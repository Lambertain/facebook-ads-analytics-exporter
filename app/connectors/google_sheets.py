import os
import logging
from typing import List, Dict, Any

import gspread
from google.oauth2.service_account import Credentials
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log
)

logger = logging.getLogger(__name__)

GSHEETS_MAX_RETRIES = int(os.getenv("GSHEETS_MAX_RETRIES", "3"))


SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


def get_client():
    creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if not creds_path or not os.path.exists(creds_path):
        logger.error(f"GOOGLE_APPLICATION_CREDENTIALS not found: {creds_path}")
        raise RuntimeError("GOOGLE_APPLICATION_CREDENTIALS file not found")
    try:
        credentials = Credentials.from_service_account_file(creds_path, scopes=SCOPES)
        client = gspread.authorize(credentials)
        logger.info("Google Sheets client authorized successfully")
        return client
    except Exception as e:
        logger.error(f"Failed to authorize Google Sheets client: {type(e).__name__}: {e}")
        raise


@retry(
    stop=stop_after_attempt(GSHEETS_MAX_RETRIES),
    wait=wait_exponential(multiplier=1, min=2, max=20),
    retry=retry_if_exception_type((gspread.exceptions.APIError,)),
    before_sleep=before_sleep_log(logger, logging.WARNING)
)
def _upsert_worksheet(gc, sheet_id: str, title: str, headers: List[str]):
    try:
        sh = gc.open_by_key(sheet_id)
        logger.debug(f"Opened spreadsheet {sheet_id}")
    except Exception as e:
        logger.error(f"Failed to open spreadsheet {sheet_id}: {type(e).__name__}: {e}")
        raise

    try:
        ws = sh.worksheet(title)
        ws.clear()
        logger.info(f"Cleared existing worksheet '{title}'")
    except gspread.WorksheetNotFound:
        ws = sh.add_worksheet(title=title, rows=1000, cols=max(10, len(headers)))
        logger.info(f"Created new worksheet '{title}'")
    except Exception as e:
        logger.error(f"Failed to access worksheet '{title}': {type(e).__name__}: {e}")
        raise

    try:
        ws.update("A1", [headers])
        logger.debug(f"Updated headers in worksheet '{title}'")
        return ws
    except Exception as e:
        logger.error(f"Failed to update headers in worksheet '{title}': {type(e).__name__}: {e}")
        raise


@retry(
    stop=stop_after_attempt(GSHEETS_MAX_RETRIES),
    wait=wait_exponential(multiplier=1, min=2, max=20),
    retry=retry_if_exception_type((gspread.exceptions.APIError,)),
    before_sleep=before_sleep_log(logger, logging.WARNING)
)
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
    logger.info(f"Writing {len(insights)} insights to Google Sheets")
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
        try:
            ws.update(f"A2", rows)
            logger.info(f"Successfully wrote {len(rows)} insights rows")
        except Exception as e:
            logger.error(f"Failed to write insights data: {type(e).__name__}: {e}")
            raise
    else:
        logger.warning("No insights data to write")


@retry(
    stop=stop_after_attempt(GSHEETS_MAX_RETRIES),
    wait=wait_exponential(multiplier=1, min=2, max=20),
    retry=retry_if_exception_type((gspread.exceptions.APIError,)),
    before_sleep=before_sleep_log(logger, logging.WARNING)
)
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
    logger.info(f"Writing {len(leads)} leads to Google Sheets")
    ws = _upsert_worksheet(gc, sheet_id, title="Leads", headers=headers)
    rows = []
    for l in leads:
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
        try:
            ws.update("A2", rows)
            logger.info(f"Successfully wrote {len(rows)} leads rows")
        except Exception as e:
            logger.error(f"Failed to write leads data: {type(e).__name__}: {e}")
            raise
    else:
        logger.warning("No leads data to write")


def _extract_field(field_data: List[Dict[str, Any]], names: set):
    for item in field_data:
        name = (item.get("name") or "").lower()
        if name in {n.lower() for n in names}:
            values = item.get("values") or []
            return values[0] if values else None
    return None

