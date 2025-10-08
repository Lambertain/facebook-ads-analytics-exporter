# План реализации: Meta Leads + CRM Tracking

## 🎯 Цель

Автоматический сбор и анализ лидов из Meta Ads с трекингом их продвижения по воронке в CRM системах (AlfaCRM для студентов, NetHunt для учителей).

## 📊 Архитектура данных

### 1. Источники данных

**Meta API (Лиды):**
- Эндпоинт: `/{PAGE_ID}/leadgen_forms` → `/{FORM_ID}/leads`
- Данные по каждому лиду:
  - `id` - уникальный ID лида
  - `created_time` - дата создания
  - `campaign_id`, `campaign_name` - кампания
  - `ad_id`, `ad_name` - объявление
  - `field_data` - поля формы (email, phone, name, etc.)

**AlfaCRM API (Студенты):**
- Эндпоинт: `/v2api/{COMPANY_ID}/student/index`
- Статусы воронки:
  1. "Не розібрані" - новый лид
  2. "Встанов. контакт (ЦА)" - установлен контакт
  3. "В опрацюванні (ЦА)" - в обработке
  4. "Назначений пробний (ЦА)" - назначен пробный урок
  5. "Проведений пробний (ЦА)" - проведен пробный урок
  6. "Чекаємо оплату" - ожидание оплаты
  7. "Купили (ЦА)" - оплатил (конверсия)
  8. "Архів (ЦА)" - архив целевой
  9. "Недозвон (не ЦА)" - не дозвонились
  10. "Архів (не ЦА)" - архив нецелевой

**NetHunt API (Учителя):**
- Эндпоинт: `/api/records/folder/{FOLDER_ID}`
- Статусы воронки учителей (50+ статусов согласно UI)

### 2. Логика подсчета лидов

```python
# Псевдокод логики
def count_leads_by_status(campaign_id, start_date, end_date):
    # 1. Получить все лиды из Meta API для кампании
    leads = get_meta_leads(campaign_id, start_date, end_date)

    # 2. Для каждого лида проверить статус в CRM
    status_counts = {
        "contacted": 0,
        "in_progress": 0,
        "trial_scheduled": 0,
        # ... все статусы
    }

    for lead in leads:
        # Поиск лида в CRM по email или phone
        crm_record = find_in_crm(lead.email, lead.phone)

        if crm_record:
            # Проверяем через какие статусы прошел лид
            for status in crm_record.status_history:
                if status == "Встанов. контакт (ЦА)":
                    status_counts["contacted"] += 1
                elif status == "Назначений пробний (ЦА)":
                    status_counts["trial_scheduled"] += 1
                # ... для каждого статуса

    return status_counts
```

## 🛠️ План реализации

### Шаг 1: Создать модуль получения лидов из Meta API

**Файл:** `app/services/meta_leads.py`

```python
async def get_leads_for_period(
    page_id: str,
    page_token: str,
    start_date: str,
    end_date: str
) -> List[Dict]:
    """
    Получить все лиды за период с группировкой по кампаниям.

    Returns:
        [
            {
                "campaign_id": "120226862970630609",
                "campaign_name": "Student/Anatoly/...",
                "leads": [
                    {
                        "id": "24905838062380228",
                        "created_time": "2025-10-08T09:09:27+0000",
                        "email": "snv88@ukr.net",
                        "phone": "+380631045546",
                        "name": "Nata Petrenko",
                        ...
                    }
                ]
            }
        ]
    """
    # 1. Получить все leadgen_forms
    forms = await get_leadgen_forms(page_id, page_token)

    # 2. Для каждой формы получить лиды за период
    all_leads = []
    for form in forms:
        leads = await get_form_leads(
            form["id"],
            page_token,
            start_date,
            end_date
        )
        all_leads.extend(leads)

    # 3. Группировать лиды по кампаниям
    grouped = group_by_campaign(all_leads)

    return grouped
```

### Шаг 2: Создать модуль трекинга в AlfaCRM

**Файл:** `app/services/alfacrm_tracking.py`

```python
async def track_lead_in_alfacrm(
    email: str,
    phone: str
) -> Dict[str, int]:
    """
    Найти лида в AlfaCRM и вернуть статусы через которые он прошел.

    Returns:
        {
            "found": True,
            "student_id": "12345",
            "statuses": {
                "contacted": True,
                "in_progress": True,
                "trial_scheduled": True,
                "trial_completed": False,
                "purchased": False,
                ...
            }
        }
    """
    # Поиск студента в AlfaCRM
    students = await search_alfacrm_students(email, phone)

    if not students:
        return {"found": False}

    student = students[0]

    # Маппинг статусов AlfaCRM на колонки таблицы
    STATUS_MAPPING = {
        "Встанов. контакт (ЦА)": "contacted",
        "В опрацюванні (ЦА)": "in_progress",
        "Назначений пробний (ЦА)": "trial_scheduled",
        "Проведений пробний (ЦА)": "trial_completed",
        "Купили (ЦА)": "purchased",
        "Недозвон (не ЦА)": "not_reached",
        ...
    }

    # Проверяем статусы
    statuses = {}
    for alfa_status, table_field in STATUS_MAPPING.items():
        statuses[table_field] = check_status(student, alfa_status)

    return {
        "found": True,
        "student_id": student["id"],
        "statuses": statuses
    }
```

### Шаг 3: Создать модуль трекинга в NetHunt

**Файл:** `app/services/nethunt_tracking.py`

```python
async def track_lead_in_nethunt(
    email: str,
    phone: str
) -> Dict[str, bool]:
    """
    Найти лида в NetHunt и вернуть статусы (для учителей).

    Returns:
        {
            "found": True,
            "record_id": "67890",
            "statuses": {
                "contacted": True,
                "interview_scheduled": True,
                ...
            }
        }
    """
    # Аналогично AlfaCRM, но для учителей
    pass
```

### Шаг 4: Интегрировать в endpoint /api/meta-data

**Файл:** `app/main.py` (обновить существующий endpoint)

```python
@app.post("/api/meta-data")
async def get_meta_data(payload: dict):
    """
    Получить данные из Meta API + CRM трекинг за период.

    Request:
        {
            "start_date": "2025-10-01",
            "end_date": "2025-10-07"
        }

    Response:
        {
            "ads": [...],  # реклама
            "students": [  # студенты с CRM статусами
                {
                    "campaign_name": "...",
                    "budget": 100,
                    "leads_count": 50,
                    "contacted": 30,  # +1 за каждый лид прошедший статус
                    "in_progress": 25,
                    "trial_scheduled": 15,
                    "trial_completed": 10,
                    "purchased": 5,
                    ...
                }
            ],
            "teachers": [...]  # учителя с CRM статусами
        }
    """
    start_date = payload.get("start_date")
    end_date = payload.get("end_date")

    # 1. Получить все кампании из Meta API
    campaigns = await get_campaigns(start_date, end_date)

    # 2. Разделить на студентов и учителей
    student_campaigns = filter_student_campaigns(campaigns)
    teacher_campaigns = filter_teacher_campaigns(campaigns)

    # 3. Для каждой студенческой кампании
    students_data = []
    for campaign in student_campaigns:
        # 3.1 Получить лиды из Meta
        leads = await get_campaign_leads(campaign["id"], start_date, end_date)

        # 3.2 Трекинг каждого лида в AlfaCRM
        status_counts = {
            "contacted": 0,
            "in_progress": 0,
            "trial_scheduled": 0,
            ...
        }

        for lead in leads:
            crm_data = await track_lead_in_alfacrm(lead["email"], lead["phone"])
            if crm_data["found"]:
                # +1 для каждого статуса через который прошел лид
                for status_key, passed in crm_data["statuses"].items():
                    if passed:
                        status_counts[status_key] += 1

        # 3.3 Формируем данные для таблицы
        students_data.append({
            "campaign_name": campaign["name"],
            "campaign_link": f"https://facebook.com/campaign/{campaign['id']}",
            "budget": campaign["spend"],
            "leads_count": len(leads),
            **status_counts,  # все счетчики статусов
            # Вычисляемые поля НЕ заполняем - их считают Excel формулы
        })

    # 4. Аналогично для учителей
    teachers_data = []
    # ...

    # 5. Реклама (креативы)
    ads_data = []
    # ...

    return {
        "ads": ads_data,
        "students": students_data,
        "teachers": teachers_data,
        "fetched_at": datetime.now().isoformat()
    }
```

### Шаг 5: Добавить Excel формулы

**Файл:** `app/excel_export.py` (обновить функцию экспорта)

```python
def add_excel_formulas(ws, sheet_type: str):
    """
    Добавить формулы для вычисляемых полей.

    sheet_type: "students" | "teachers" | "ads"
    """
    if sheet_type == "students":
        # Найти индексы колонок
        headers = [cell.value for cell in ws[1]]

        leads_col = headers.index("Кількість лідів") + 1
        target_leads_col = headers.index("Кількість цільових лідів") + 1
        purchased_col = headers.index("Купили (ЦА)") + 1
        trial_completed_col = headers.index("Проведений пробний (ЦА)") + 1

        # Для каждой строки данных
        for row_idx in range(2, ws.max_row + 1):
            # % цільових лідів = (target_leads / leads) * 100
            target_percent_col = headers.index("% цільових лідів") + 1
            ws.cell(row_idx, target_percent_col).value = f"=IF({get_col_letter(leads_col)}{row_idx}=0,0,{get_col_letter(target_leads_col)}{row_idx}/{get_col_letter(leads_col)}{row_idx}*100)"
            ws.cell(row_idx, target_percent_col).number_format = "0.00%"

            # Конверсія з проведеного пробного в продаж
            conversion_col = headers.index("Конверсія з проведеного пробного в продаж") + 1
            ws.cell(row_idx, conversion_col).value = f"=IF({get_col_letter(trial_completed_col)}{row_idx}=0,0,{get_col_letter(purchased_col)}{row_idx}/{get_col_letter(trial_completed_col)}{row_idx}*100)"
            ws.cell(row_idx, conversion_col).number_format = "0.00%"

            # Ціна / ліда
            cost_per_lead_col = headers.index("Ціна / ліда") + 1
            budget_col = headers.index("Витрачений бюджет в $") + 1
            ws.cell(row_idx, cost_per_lead_col).value = f"=IF({get_col_letter(leads_col)}{row_idx}=0,0,{get_col_letter(budget_col)}{row_idx}/{get_col_letter(leads_col)}{row_idx})"
            ws.cell(row_idx, cost_per_lead_col).number_format = "$#,##0.00"

            # ... все остальные вычисляемые поля
```

## 📝 Маппинг статусов

### Студенты (AlfaCRM)

| Статус в AlfaCRM | Поле в таблице |
|------------------|----------------|
| Не розібрані | `not_processed` |
| Встанов. контакт (ЦА) | `contacted` |
| В опрацюванні (ЦА) | `in_progress` |
| Назначений пробний (ЦА) | `trial_scheduled` |
| Проведений пробний (ЦА) | `trial_completed` |
| Чекаємо оплату | `awaiting_payment` |
| Купили (ЦА) | `purchased` |
| Архів (ЦА) | `archived` |
| Недозвон (не ЦА) | `not_reached` |
| Архів (не ЦА) | `archived_non_target` |

### Учителя (NetHunt)

| Статус в NetHunt | Поле в таблице |
|------------------|----------------|
| Не розібрані ліди | `not_processed` |
| Взяті в роботу | `contacted` |
| Контакт (ЦА) | `contacted` |
| НЕ дозвон (НЕ ЦА) | `not_reached` |
| Співбесіда (ЦА) | `trial_scheduled` |
| СП проведено (ЦА) | `trial_completed` |
| Стажування (ЦА) | `internship` |
| Вчитель (ЦА) | `teacher_active` |
| ... (50+ статусов) | ... |

## 🔢 Вычисляемые поля (Excel формулы)

### Студенты

```excel
% цільових лідів = (Кількість цільових лідів / Кількість лідів) * 100
% не цільових лідів = (Кількість не цільових лідів / Кількість лідів) * 100
% Встан. контакт = (Встанов. контакт (ЦА) / Кількість цільових лідів) * 100
% В опрацюванні (ЦА) = (В опрацюванні (ЦА) / Кількість цільових лідів) * 100
% конверсія = (Купили (ЦА) / Кількість цільових лідів) * 100
% архів = (Архів (ЦА) / Кількість цільових лідів) * 100
% недозвон = (Недозвон (не ЦА) / Кількість лідів) * 100
Ціна / ліда = Витрачений бюджет в $ / Кількість лідів
Ціна / цільового ліда = Витрачений бюджет в $ / Кількість цільових лідів
% Назначений пробний = (Назначений пробний (ЦА) / Кількість цільових лідів) * 100
% Проведений пробний від загальних лідів (ЦА) = (Проведений пробний (ЦА) / Кількість лідів) * 100
% Проведений пробний від назначених пробних = (Проведений пробний (ЦА) / Назначений пробний (ЦА)) * 100
Конверсія з проведеного пробного в продаж = (Купили (ЦА) / Проведений пробний (ЦА)) * 100
```

### Реклама

```excel
CPL = Витрачено ($) / Кількість лідів
Ціна в $ за цільового ліда = Витрачено ($) / Кількість цільових лідів
% цільових лідів = (Кількість цільових лідів / Кількість лідів) * 100
% Не цільових лідів = (Кількість не цільових лідів / Кількість лідів) * 100
% Не дозвонів = (Кількість не дозвонів / Кількість лідів) * 100
% В опрацюванні = (Кількість в опрацюванні / Кількість лідів) * 100
```

## ⚠️ Важные детали

1. **НЕ изменять UI таблиц** - поля остаются как есть
2. **Только счетчики из CRM** - все данные из Meta API + CRM трекинг
3. **Формулы в Excel** - вычисляемые поля считаются формулами, НЕ в Python
4. **+1 за статус** - если лид прошел статус, добавляем 1 к счетчику
5. **Поиск в CRM** - по email или phone из Meta lead
6. **История статусов** - важно учитывать что лид может пройти несколько статусов

## 🚀 Следующие шаги

1. ✅ Изучить структуру Excel и маппинг
2. ⏳ Создать `app/services/meta_leads.py`
3. ⏳ Создать `app/services/alfacrm_tracking.py`
4. ⏳ Создать `app/services/nethunt_tracking.py`
5. ⏳ Обновить `/api/meta-data` endpoint
6. ⏳ Добавить Excel формулы в экспорт
7. ⏳ Протестировать на реальных данных
