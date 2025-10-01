import asyncio
import os
import uuid
import json
from datetime import datetime
from typing import Dict, Any, List
import openpyxl

from fastapi import FastAPI, BackgroundTasks, Request, Depends
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from dotenv import load_dotenv

from .progress import ProgressStore
from .connectors import meta as meta_conn
from .connectors import google_sheets as gs_conn
from .connectors import excel as excel_conn
from .mapping import load_mapping
from .connectors import crm as crm_tools
from .config_store import get_config_masked, set_config
from .connectors import crm as crm_conn
from .middleware.auth import verify_api_key
from .database import init_db, get_db
from .models import PipelineRun, RunLog


load_dotenv()

app = FastAPI(title="Ads → Sheets → CRM")

# Initialize database on startup
@app.on_event("startup")
def startup_event():
    init_db()

# Security: Rate limiting
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Security: CORS protection
# TODO: Replace with your actual frontend domain in production
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:8000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
)

# Security: Trusted host protection
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
app.add_middleware(TrustedHostMiddleware, allowed_hosts=ALLOWED_HOSTS)

# Security: Add security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
    return response

progress = ProgressStore()

# Define paths for static files
WEB_DIST = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "dist")
STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")


@app.post("/api/start-job")
@limiter.limit("5/minute")
async def start_job(
    request: Request,
    payload: Dict[str, Any],
    background_tasks: BackgroundTasks,
    api_key: str = Depends(verify_api_key),
):
    # payload expects: start_date, end_date (YYYY-MM-DD), sheet_id (optional)
    start_date = payload.get("start_date")
    end_date = payload.get("end_date")
    sheet_id = payload.get("sheet_id") or os.getenv("GOOGLE_SHEET_ID")

    # Basic validation
    for key, val in {"start_date": start_date, "end_date": end_date}.items():
        if not val:
            return JSONResponse({"error": f"Відсутнє поле {key}"}, status_code=400)
    try:
        _ = datetime.strptime(start_date, "%Y-%m-%d")
        _ = datetime.strptime(end_date, "%Y-%m-%d")
    except ValueError:
        return JSONResponse({"error": "Невірний формат дати, використовуйте YYYY-MM-DD"}, status_code=400)
    backend = os.getenv("STORAGE_BACKEND", "sheets").lower()
    if backend == "sheets" and not sheet_id:
        return JSONResponse({"error": "Відсутній Google Sheet ID"}, status_code=400)

    job_id = str(uuid.uuid4())
    progress.init(job_id, title="Pipeline run")

    params = {
        "start_date": start_date,
        "end_date": end_date,
        "sheet_id": sheet_id,
    }
    background_tasks.add_task(run_pipeline, job_id, params)
    return {"job_id": job_id}


@app.get("/api/events/{job_id}")
async def events(job_id: str):
    async def event_stream():
        last_index = 0
        while True:
            await asyncio.sleep(0.5)
            state = progress.get(job_id)
            if not state:
                # job unknown → end stream
                break
            logs = state["logs"]
            # Send incremental logs and current progress as SSE
            while last_index < len(logs):
                msg = logs[last_index]
                last_index += 1
                yield f"event: log\ndata: {msg}\n\n"
            yield (
                "event: progress\n"
                f"data: {{\"percent\": {state['percent']}, \"status\": \"{state['status']}\"}}\n\n"
            )
            if state["status"] in ("done", "error"):
                break

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.get("/api/inspect/excel-headers")
async def inspect_excel_headers():
    from .connectors import excel as ex
    # Just probe existing headers by reading first row; we won’t modify files here
    files = {
        "creatives": os.getenv("EXCEL_CREATIVES_PATH"),
        "students": os.getenv("EXCEL_STUDENTS_PATH"),
        "teachers": os.getenv("EXCEL_TEACHERS_PATH"),
    }
    result = {}
    for key, path in files.items():
        if not path or not os.path.exists(path):
            result[key] = {"error": "file_not_found", "path": path}
            continue
        try:
            # reuse openpyxl through helpers
            from openpyxl import load_workbook
            wb = load_workbook(path, read_only=True, data_only=True)
            sheets = {}
            for name in wb.sheetnames:
                ws = wb[name]
                row1 = next(ws.iter_rows(min_row=1, max_row=1, values_only=True), None) or []
                headers = [str(c) if c is not None else '' for c in row1]
                sheets[name] = headers
            result[key] = {"path": path, "sheets": sheets}
        except Exception as e:
            result[key] = {"path": path, "error": str(e)}
    return result


@app.get("/api/inspect/nethunt/folders")
async def inspect_nethunt_folders():
    data = crm_tools.nethunt_list_folders()
    return data


@app.get("/api/inspect/nethunt/fields")
async def inspect_nethunt_fields(folder_id: str):
    data = crm_tools.nethunt_folder_fields(folder_id)
    return data


@app.get("/api/inspect/alfacrm/companies")
async def inspect_alfacrm_companies():
    data = crm_tools.alfacrm_list_companies()
    return data


@app.get("/api/config")
@limiter.limit("10/minute")
async def get_config(request: Request):
    return get_config_masked()


@app.post("/api/config")
@limiter.limit("5/minute")
async def update_config(
    request: Request, payload: Dict[str, Any], api_key: str = Depends(verify_api_key)
):
    # Never echo secrets back
    set_config(payload or {})
    return {"status": "ok"}


@app.get("/api/runs")
@limiter.limit("30/minute")
async def get_runs(
    request: Request,
    status: str = None,
    limit: int = 50,
    offset: int = 0
):
    """
    Get pipeline run history with optional filtering.

    Query params:
    - status: Filter by status (success, error, running)
    - limit: Maximum number of results (default: 50, max: 100)
    - offset: Pagination offset (default: 0)
    """
    try:
        # Limit maximum results
        limit = min(limit, 100)

        with get_db() as db:
            query = db.query(PipelineRun)

            # Apply status filter if provided
            if status:
                query = query.filter(PipelineRun.status == status)

            # Order by most recent first
            query = query.order_by(PipelineRun.start_time.desc())

            # Apply pagination
            runs = query.offset(offset).limit(limit).all()

            # Convert to dict
            result = []
            for run in runs:
                result.append({
                    "id": run.id,
                    "job_id": run.job_id,
                    "start_time": run.start_time.isoformat() if run.start_time else None,
                    "end_time": run.end_time.isoformat() if run.end_time else None,
                    "status": run.status,
                    "start_date": run.start_date,
                    "end_date": run.end_date,
                    "sheet_id": run.sheet_id,
                    "storage_backend": run.storage_backend,
                    "insights_count": run.insights_count,
                    "students_count": run.students_count,
                    "teachers_count": run.teachers_count,
                    "error_message": run.error_message
                })

            return {"runs": result, "count": len(result)}
    except Exception as e:
        return JSONResponse({"error": f"Помилка бази даних: {str(e)}"}, status_code=500)


@app.get("/api/runs/{run_id}")
@limiter.limit("30/minute")
async def get_run_details(request: Request, run_id: int):
    """Get detailed information about a specific run including logs."""
    try:
        with get_db() as db:
            run = db.query(PipelineRun).filter(PipelineRun.id == run_id).first()

            if not run:
                return JSONResponse({"error": "Запуск не знайдено"}, status_code=404)

            # Get logs for this run
            logs = db.query(RunLog).filter(RunLog.run_id == run_id).order_by(RunLog.timestamp).all()

            return {
                "run": {
                    "id": run.id,
                    "job_id": run.job_id,
                    "start_time": run.start_time.isoformat() if run.start_time else None,
                    "end_time": run.end_time.isoformat() if run.end_time else None,
                    "status": run.status,
                    "start_date": run.start_date,
                    "end_date": run.end_date,
                    "sheet_id": run.sheet_id,
                    "storage_backend": run.storage_backend,
                    "insights_count": run.insights_count,
                    "students_count": run.students_count,
                    "teachers_count": run.teachers_count,
                    "error_message": run.error_message
                },
                "logs": [
                    {
                        "id": log.id,
                        "timestamp": log.timestamp.isoformat() if log.timestamp else None,
                        "level": log.level,
                        "message": log.message
                    }
                    for log in logs
                ]
            }
    except Exception as e:
        return JSONResponse({"error": f"Помилка бази даних: {str(e)}"}, status_code=500)


async def enrich_students_with_alfacrm(students_from_excel: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Обогащает данные студентов из Excel свежими данными из AlfaCRM.

    Args:
        students_from_excel: Список студентов из Excel файла

    Returns:
        Обогащенный список студентов
    """
    if not (os.getenv("ALFACRM_BASE_URL") and os.getenv("ALFACRM_EMAIL")
            and os.getenv("ALFACRM_API_KEY") and os.getenv("ALFACRM_COMPANY_ID")):
        return students_from_excel

    try:
        alfacrm_students = []
        page = 1
        while True:
            data = crm_tools.alfacrm_list_students(page=page, page_size=200)
            items = data.get("items") or data.get("data") or data.get("list") or []
            if not isinstance(items, list):
                break

            for s in items:
                flat = {}
                if isinstance(s, dict):
                    for k, v in s.items():
                        if isinstance(v, (dict, list)):
                            try:
                                flat[k] = json.dumps(v, ensure_ascii=False)
                            except Exception:
                                flat[k] = str(v)
                        else:
                            flat[k] = v
                alfacrm_students.append(flat)

            if len(items) < 200:
                break
            page += 1

        alfacrm_lookup = {}
        for student in alfacrm_students:
            student_id = student.get("id") or student.get("student_id")
            email = student.get("email")
            if student_id:
                alfacrm_lookup[str(student_id)] = student
            if email:
                alfacrm_lookup[email] = student

        enriched = []
        for excel_student in students_from_excel:
            student_id = excel_student.get("id") or excel_student.get("student_id")
            email = excel_student.get("email") or excel_student.get("Email")

            crm_data = None
            if student_id and str(student_id) in alfacrm_lookup:
                crm_data = alfacrm_lookup[str(student_id)]
            elif email and email in alfacrm_lookup:
                crm_data = alfacrm_lookup[email]

            if crm_data:
                merged = {**excel_student, **crm_data}
            else:
                merged = excel_student

            enriched.append(merged)

        return enriched

    except Exception as e:
        print(f"Попередження: збагачення даних з AlfaCRM не вдалося: {e}")
        return students_from_excel


@app.get("/api/students")
@limiter.limit("30/minute")
async def get_students(request: Request, start_date: str = None, end_date: str = None, enrich: bool = True):
    """
    Get students data with all 33 fields from Students Analysis structure.

    Query params:
    - start_date: Filter by analysis date (YYYY-MM-DD)
    - end_date: Filter by analysis date (YYYY-MM-DD)
    - enrich: Enrich with fresh AlfaCRM data (default: True)
    """
    try:
        backend = os.getenv("STORAGE_BACKEND", "excel").lower()

        if backend == "excel":
            excel_path = os.getenv("EXCEL_STUDENTS_PATH")
            if not excel_path or not os.path.exists(excel_path):
                return JSONResponse({"error": "Файл студентів не знайдено"}, status_code=404)

            # Read from Excel
            from openpyxl import load_workbook
            mapping = load_mapping()
            sheet_name = mapping.get("students", {}).get("sheet_name", "Students")

            wb = load_workbook(excel_path, read_only=True, data_only=True)
            if sheet_name not in wb.sheetnames:
                return JSONResponse({"error": f"Аркуш '{sheet_name}' не знайдено"}, status_code=404)

            ws = wb[sheet_name]

            # Get headers from first row
            headers_row = next(ws.iter_rows(min_row=1, max_row=1, values_only=True), None)
            if not headers_row:
                return JSONResponse({"error": "Заголовки не знайдено"}, status_code=404)

            headers = [str(h) if h is not None else '' for h in headers_row]

            # Read all data rows
            students = []
            for row in ws.iter_rows(min_row=2, values_only=True):
                if not any(row):  # Skip empty rows
                    continue

                student_dict = {}
                for idx, header in enumerate(headers):
                    value = row[idx] if idx < len(row) else None
                    # Convert datetime to string
                    if hasattr(value, 'isoformat'):
                        value = value.isoformat()
                    student_dict[header] = value

                students.append(student_dict)

            wb.close()

            # Filter by date if provided
            if start_date or end_date:
                filtered = []
                for s in students:
                    date_str = s.get("Дата аналізу", "")
                    if date_str:
                        # Simple date comparison
                        if start_date and str(date_str) < start_date:
                            continue
                        if end_date and str(date_str) > end_date:
                            continue
                    filtered.append(s)
                students = filtered

            # Enrich with AlfaCRM data if requested
            if enrich:
                students = await enrich_students_with_alfacrm(students)

            return {"students": students, "count": len(students)}
        else:
            # Google Sheets backend - to be implemented
            return JSONResponse({"error": "Google Sheets backend поки не підтримується"}, status_code=501)

    except Exception as e:
        return JSONResponse({"error": f"Помилка читання даних: {str(e)}"}, status_code=500)


@app.post("/api/download-excel")
async def download_excel(payload: Dict[str, Any]):
    """
    Експорт даних у Excel з підтримкою різних типів даних.

    Args:
        data_type: "ads" | "students" | "teachers"
        start_date: YYYY-MM-DD
        end_date: YYYY-MM-DD
    """
    from fastapi.responses import FileResponse
    import tempfile
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment
    from openpyxl.utils import get_column_letter

    data_type = payload.get("data_type", "ads")
    start_date = payload.get("start_date")
    end_date = payload.get("end_date")

    try:
        wb = Workbook()
        ws = wb.active

        if data_type == "students":
            ws.title = "Students"

            # Отримуємо дані студентів через існуючий endpoint
            excel_path = os.getenv("EXCEL_STUDENTS_PATH")
            if not excel_path or not os.path.exists(excel_path):
                return JSONResponse({"error": "Файл студентів не знайдено"}, status_code=404)

            # Читаємо з Excel
            mapping = load_mapping()
            sheet_name = mapping.get("students", {}).get("sheet_name", "Students")

            source_wb = openpyxl.load_workbook(excel_path, read_only=True, data_only=True)
            if sheet_name not in source_wb.sheetnames:
                return JSONResponse({"error": f"Аркуш '{sheet_name}' не знайдено"}, status_code=404)

            source_ws = source_wb[sheet_name]

            # Копіюємо всі дані з форматуванням
            for row_idx, row in enumerate(source_ws.iter_rows(values_only=False), 1):
                for col_idx, cell in enumerate(row, 1):
                    target_cell = ws.cell(row=row_idx, column=col_idx)
                    target_cell.value = cell.value

                    # Форматування заголовків
                    if row_idx == 1:
                        target_cell.font = Font(bold=True, size=11)
                        target_cell.fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
                        target_cell.font = Font(bold=True, color="FFFFFF", size=11)
                        target_cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

            # Автоширина столбцов
            for column in ws.columns:
                max_length = 0
                column_letter = get_column_letter(column[0].column)
                for cell in column:
                    try:
                        if cell.value:
                            max_length = max(max_length, len(str(cell.value)))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                ws.column_dimensions[column_letter].width = adjusted_width

            # Применяем числовые форматы для процентов и валюты
            percent_columns = ["% цільових лідів", "% не цільових лідів", "% Встан. контакт",
                             "% В опрацюванні (ЦА)", "% конверсія", "% архів", "% недозвон",
                             "% Назначений пробний", "%\nПроведений пробний від загальних лідів\n(ЦА)",
                             "%\nПроведений пробний від назначених пробних", "Конверсія з проведеного пробного в продаж"]

            currency_columns = ["Витрачений бюджет в $", "Ціна / ліда", "Ціна / цільового ліда"]

            # Находим индексы колонок
            headers = [cell.value for cell in ws[1]]
            for col_idx, header in enumerate(headers, 1):
                if header in percent_columns:
                    for row_idx in range(2, ws.max_row + 1):
                        ws.cell(row=row_idx, column=col_idx).number_format = '0.00%'
                elif header in currency_columns:
                    for row_idx in range(2, ws.max_row + 1):
                        ws.cell(row=row_idx, column=col_idx).number_format = '$#,##0.00'

            source_wb.close()
            filename = f"students_export_{start_date}_{end_date}.xlsx"

        else:  # ads (creatives)
            ws.title = "Creatives"

            meta_token = os.getenv("META_ACCESS_TOKEN")
            ad_account_id = os.getenv("META_AD_ACCOUNT_ID")

            if not meta_token or not ad_account_id:
                return JSONResponse({"error": "META credentials не налаштовані"}, status_code=400)

            insights = meta_conn.fetch_insights(
                ad_account_id=ad_account_id,
                access_token=meta_token,
                date_from=start_date,
                date_to=end_date,
                level="ad"
            )

            headers = ["date_start", "date_stop", "campaign_id", "campaign_name",
                       "adset_id", "adset_name", "ad_id", "ad_name",
                       "impressions", "clicks", "spend", "cpc", "cpm", "ctr"]
            ws.append(headers)

            for insight in insights:
                row = [
                    insight.get("date_start", ""),
                    insight.get("date_stop", ""),
                    insight.get("campaign_id", ""),
                    insight.get("campaign_name", ""),
                    insight.get("adset_id", ""),
                    insight.get("adset_name", ""),
                    insight.get("ad_id", ""),
                    insight.get("ad_name", ""),
                    insight.get("impressions", 0),
                    insight.get("clicks", 0),
                    insight.get("spend", 0),
                    insight.get("cpc", 0),
                    insight.get("cpm", 0),
                    insight.get("ctr", 0),
                ]
                ws.append(row)

            filename = f"ads_export_{start_date}_{end_date}.xlsx"

        # Save to temp file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
        wb.save(temp_file.name)
        temp_file.close()

        return FileResponse(
            temp_file.name,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename=filename
        )
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


async def run_pipeline(job_id: str, params: Dict[str, Any]):
    # Create database record for this run
    with get_db() as db:
        db_run = PipelineRun(
            job_id=job_id,
            start_date=params["start_date"],
            end_date=params["end_date"],
            sheet_id=params.get("sheet_id"),
            storage_backend=os.getenv("STORAGE_BACKEND", "sheets"),
            status="running"
        )
        db.add(db_run)
        db.commit()
        db.refresh(db_run)
        run_id = db_run.id

    def log_to_db(message: str, level: str = "info"):
        """Helper to save log messages to database."""
        try:
            with get_db() as db:
                log_entry = RunLog(run_id=run_id, message=message, level=level)
                db.add(log_entry)
                db.commit()
        except Exception as e:
            print(f"Помилка запису логу в БД: {e}")

    try:
        progress.update(job_id, 2, "Перевірка облікових даних")
        log_to_db("Початок виконання pipeline")

        # Meta credentials
        meta_token = os.getenv("META_ACCESS_TOKEN")
        ad_account_id = os.getenv("META_AD_ACCOUNT_ID")
        if not meta_token or not ad_account_id:
            raise RuntimeError("META_ACCESS_TOKEN або META_AD_ACCOUNT_ID не налаштовані")

        backend = os.getenv("STORAGE_BACKEND", "sheets").lower()
        gs_client = None
        sheet_id = params.get("sheet_id")
        if backend == "sheets":
            gs_client = gs_conn.get_client()
            if not sheet_id:
                raise RuntimeError("GOOGLE_SHEET_ID обов'язковий коли STORAGE_BACKEND=sheets")

        # 1) Fetch Ads insights
        progress.update(job_id, 10, "Отримання статистики Meta Ads (рівень оголошень)")
        insights = meta_conn.fetch_insights(
            ad_account_id=ad_account_id,
            access_token=meta_token,
            date_from=params["start_date"],
            date_to=params["end_date"],
            level="ad",
        )

        # 2) Fetch Leads
        progress.update(job_id, 30, "Підготовка даних CRM (студенти: AlfaCRM, викладачі: NetHunt)")
        # Fetch teachers from NetHunt
        teachers: list[dict] = []
        nh_folder = os.getenv("NETHUNT_FOLDER_ID")
        if nh_folder:
            try:
                raw_records = crm_tools.nethunt_list_records(nh_folder, limit=1000)
                # Flatten NetHunt records: keep id, createdAt, updatedAt and fields
                for r in raw_records:
                    flat = {}
                    if isinstance(r, dict):
                        flat["id"] = r.get("id") or r.get("_id")
                        flat["createdAt"] = r.get("createdAt")
                        flat["updatedAt"] = r.get("updatedAt")
                        fields = r.get("fields") or {}
                        if isinstance(fields, dict):
                            for k, v in fields.items():
                                # Basic normalization
                                if isinstance(v, (dict, list)):
                                    try:
                                        import json as _json
                                        flat[k] = _json.dumps(v, ensure_ascii=False)
                                    except Exception:
                                        flat[k] = str(v)
                                else:
                                    flat[k] = v
                    teachers.append(flat)
                progress.log(job_id, f"Отримано викладачів з NetHunt: {len(teachers)}")
            except Exception as e:
                progress.log(job_id, f"Помилка отримання з NetHunt: {e}")
        else:
            progress.log(job_id, "NETHUNT_FOLDER_ID не встановлено; викладачі пропущені")

        # Fetch students from AlfaCRM
        students: list[dict] = []
        if os.getenv("ALFACRM_BASE_URL") and os.getenv("ALFACRM_EMAIL") and os.getenv("ALFACRM_API_KEY") and os.getenv("ALFACRM_COMPANY_ID"):
            try:
                page = 1
                total = 0
                while True:
                    data = crm_tools.alfacrm_list_students(page=page, page_size=200)
                    # Expect data like {items:[...], total: N} or similar
                    items = data.get("items") or data.get("data") or data.get("list") or []
                    if not isinstance(items, list):
                        break
                    for s in items:
                        # Flatten student
                        flat = {}
                        if isinstance(s, dict):
                            for k, v in s.items():
                                if isinstance(v, (dict, list)):
                                    try:
                                        import json as _json
                                        flat[k] = _json.dumps(v, ensure_ascii=False)
                                    except Exception:
                                        flat[k] = str(v)
                                else:
                                    flat[k] = v
                        students.append(flat)
                    total += len(items)
                    if len(items) < 200:
                        break
                    page += 1
                progress.log(job_id, f"Отримано студентів з AlfaCRM: {len(students)}")
            except Exception as e:
                progress.log(job_id, f"Помилка отримання з AlfaCRM: {e}")
        else:
            progress.log(job_id, "AlfaCRM credentials неповні; студенти пропущені")

        # 3) Check CRM statuses
        progress.update(job_id, 45, "Отримано дані CRM")

        # 4) Write to Google Sheets
        progress.update(job_id, 70, "Запис даних у цільове сховище")
        mapping = load_mapping()
        if backend == "sheets" and gs_client:
            gs_conn.write_insights(gs_client, sheet_id, insights)
            # If needed, write students/teachers to different tabs/sheets in Sheets (not configured yet)
        else:
            excel_creatives = os.getenv("EXCEL_CREATIVES_PATH")
            excel_students = os.getenv("EXCEL_STUDENTS_PATH")
            excel_teachers = os.getenv("EXCEL_TEACHERS_PATH")
            if excel_creatives:
                cr_map = mapping.get("creatives", {})
                excel_conn.write_creatives(
                    excel_creatives,
                    insights,
                    mapping=cr_map.get("fields"),
                    sheet_name=cr_map.get("sheet_name", "Creatives"),
                )
                progress.log(job_id, f"Записано креативів: {len(insights)} рядків")
            else:
                progress.log(job_id, "EXCEL_CREATIVES_PATH не встановлено; креативи пропущені")
            if excel_students:
                st_map = mapping.get("students", {})
                excel_conn.write_students(
                    excel_students,
                    students,
                    mapping=st_map.get("fields"),
                    sheet_name=st_map.get("sheet_name", "Students"),
                )
                progress.log(job_id, f"Записано студентів: {len(students)} рядків")
            if excel_teachers:
                tc_map = mapping.get("teachers", {})
                excel_conn.write_teachers(
                    excel_teachers,
                    teachers,
                    mapping=tc_map.get("fields"),
                    sheet_name=tc_map.get("sheet_name", "Teachers"),
                )
                progress.log(job_id, f"Записано викладачів: {len(teachers)} рядків")

        progress.update(job_id, 100, "done")
        log_to_db("Pipeline завершено успішно")

        # Update database record with results
        with get_db() as db:
            db_run = db.query(PipelineRun).filter(PipelineRun.id == run_id).first()
            if db_run:
                db_run.status = "success"
                db_run.end_time = datetime.utcnow()
                db_run.insights_count = len(insights)
                db_run.students_count = len(students)
                db_run.teachers_count = len(teachers)
                db.commit()

    except Exception as e:
        progress.log(job_id, f"ERROR: {e}")
        progress.set_status(job_id, "error")
        log_to_db(f"ERROR: {e}", level="error")

        # Update database record with error
        with get_db() as db:
            db_run = db.query(PipelineRun).filter(PipelineRun.id == run_id).first()
            if db_run:
                db_run.status = "error"
                db_run.end_time = datetime.utcnow()
                db_run.error_message = str(e)
                db.commit()


# Serve index.html for root path
@app.get("/", response_class=HTMLResponse)
async def index():
    dist_index = os.path.join(WEB_DIST, "index.html")
    if os.path.exists(dist_index):
        with open(dist_index, "r", encoding="utf-8") as f:
            return HTMLResponse(f.read())
    static_index = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(static_index):
        with open(static_index, "r", encoding="utf-8") as f:
            return HTMLResponse(f.read())
    return HTMLResponse("<h1>UI not found</h1>")


# Mount static files AFTER all API routes to avoid conflicts
if os.path.exists(WEB_DIST):
    app.mount("/assets", StaticFiles(directory=os.path.join(WEB_DIST, "assets")), name="assets")
