import os
from typing import List, Dict, Any

import gspread
from google.oauth2.service_account import Credentials


SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


def get_client():
    creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if not creds_path or not os.path.exists(creds_path):
        raise RuntimeError("GOOGLE_APPLICATION_CREDENTIALS file not found")
    credentials = Credentials.from_service_account_file(creds_path, scopes=SCOPES)
    return gspread.authorize(credentials)


def _upsert_worksheet(gc, sheet_id: str, title: str, headers: List[str]):
    sh = gc.open_by_key(sheet_id)
    try:
        ws = sh.worksheet(title)
        ws.clear()
    except gspread.WorksheetNotFound:
        ws = sh.add_worksheet(title=title, rows=1000, cols=max(10, len(headers)))
    ws.update("A1", [headers])
    return ws


def write_insights(gc, sheet_id: str, insights: List[Dict[str, Any]]):
    headers = [
        "date_start",
        "date_stop",
        "campaign_id",
        "campaign_name",
        "impressions",
        "clicks",
        "spend",
        "reach",
        "cpc",
        "cpm",
        "ctr",
        "objective",
    ]
    ws = _upsert_worksheet(gc, sheet_id, title="Insights", headers=headers)
    rows = []
    for i in insights:
        rows.append([
            i.get("date_start"),
            i.get("date_stop"),
            i.get("campaign_id"),
            i.get("campaign_name"),
            i.get("impressions"),
            i.get("clicks"),
            i.get("spend"),
            i.get("reach"),
            i.get("cpc"),
            i.get("cpm"),
            i.get("ctr"),
            i.get("objective"),
        ])
    if rows:
        ws.update(f"A2", rows)


def write_leads(gc, sheet_id: str, leads: List[Dict[str, Any]]):
    headers = [
        "id",
        "created_time",
        "page_id",
        "form_id",
        "crm_status",
        "crm_stage",
        "contact_phone",
        "contact_email",
        "raw_fields_json",
    ]
    ws = _upsert_worksheet(gc, sheet_id, title="Leads", headers=headers)
    rows = []
    for l in leads:
        # Extract common fields if present
        phone = _extract_field(l.get("field_data", []), {"phone_number", "phone", "Телефон"})
        email = _extract_field(l.get("field_data", []), {"email", "e-mail", "Эл. почта"})
        rows.append([
            l.get("id"),
            l.get("created_time"),
            l.get("page_id"),
            l.get("form_id"),
            l.get("crm_status"),
            l.get("crm_stage"),
            phone,
            email,
            str(l.get("field_data")),
        ])
    if rows:
        ws.update("A2", rows)


def _extract_field(field_data: List[Dict[str, Any]], names: set):
    for item in field_data:
        name = (item.get("name") or "").lower()
        if name in {n.lower() for n in names}:
            values = item.get("values") or []
            return values[0] if values else None
    return None

