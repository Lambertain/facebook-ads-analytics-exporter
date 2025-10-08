import os
import logging
from typing import List, Dict, Any
import asyncio
import requests
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log
)

logger = logging.getLogger(__name__)

CRM_TIMEOUT = int(os.getenv("CRM_API_TIMEOUT", "15"))
CRM_MAX_RETRIES = int(os.getenv("CRM_API_MAX_RETRIES", "2"))


async def enrich_leads_with_status(leads: List[Dict[str, Any]], provider: str) -> List[Dict[str, Any]]:
    """Attach CRM status to each lead with graceful degradation.

    provider: none|amocrm|bitrix24|hubspot|pipedrive|nethunt|alfacrm

    Graceful degradation: If CRM is unavailable, returns leads without enrichment
    instead of failing the entire pipeline.
    """
    if provider == "none":
        logger.info("CRM enrichment disabled (provider=none)")
        return [
            {**l, "crm_status": None, "crm_stage": None}
            for l in leads
        ]

    logger.info(f"Starting CRM enrichment with provider: {provider} for {len(leads)} leads")

    try:
        if provider == "amocrm":
            result = await _enrich_amocrm(leads)
        elif provider == "bitrix24":
            result = await _enrich_bitrix(leads)
        elif provider == "hubspot":
            result = await _enrich_hubspot(leads)
        elif provider == "pipedrive":
            result = await _enrich_pipedrive(leads)
        elif provider == "nethunt":
            result = await _enrich_nethunt(leads)
        elif provider == "alfacrm":
            result = await _enrich_alfacrm(leads)
        else:
            logger.warning(f"Unknown CRM provider: {provider}")
            return [
                {**l, "crm_status": "unknown_provider", "crm_stage": None}
                for l in leads
            ]

        logger.info(f"Successfully enriched {len(result)} leads with {provider}")
        return result

    except Exception as e:
        logger.error(f"CRM enrichment failed for provider {provider}: {type(e).__name__}: {e}")
        logger.warning(f"Graceful degradation: returning {len(leads)} leads without CRM enrichment")
        return [
            {**l, "crm_status": "enrichment_failed", "crm_stage": None}
            for l in leads
        ]


# The following are minimal placeholders. Replace with real API calls and matching logic.

async def _enrich_amocrm(leads: List[Dict[str, Any]]):
    base_url = os.getenv("AMO_BASE_URL")
    token = os.getenv("AMO_ACCESS_TOKEN")
    # TODO: Find leads by phone/email, then map status/stage.
    return [{**l, "crm_status": "stub", "crm_stage": None} for l in leads]


async def _enrich_bitrix(leads: List[Dict[str, Any]]):
    base_url = os.getenv("BITRIX_BASE_URL")
    wh = os.getenv("BITRIX_WEBHOOK_TOKEN")
    # TODO: Use crm.lead.list or crm.deal.list with filter by phone/email
    return [{**l, "crm_status": "stub", "crm_stage": None} for l in leads]


async def _enrich_hubspot(leads: List[Dict[str, Any]]):
    token = os.getenv("HUBSPOT_ACCESS_TOKEN")
    # TODO: Search contacts by email/phone, then get deal/pipeline stage
    return [{**l, "crm_status": "stub", "crm_stage": None} for l in leads]


async def _enrich_pipedrive(leads: List[Dict[str, Any]]):
    token = os.getenv("PIPEDRIVE_API_TOKEN")
    # TODO: Search persons by email/phone, then get deals and stages
    return [{**l, "crm_status": "stub", "crm_stage": None} for l in leads]


async def _enrich_nethunt(leads: List[Dict[str, Any]]):
    """Обогащение лидов данными из NetHunt с поиском по phone/email."""
    auth = os.getenv("NETHUNT_BASIC_AUTH")
    folder_id = os.getenv("NETHUNT_FOLDER_ID", "default")

    if not auth:
        logger.warning("NETHUNT_BASIC_AUTH not configured, skipping enrichment")
        return [{**l, "crm_status": "not_configured", "crm_stage": None} for l in leads]

    try:
        # Получаем список записей из NetHunt
        # Если folder_id не указан, пытаемся получить первую папку
        if folder_id == "default":
            folders = nethunt_list_folders()
            if not folders:
                logger.error("No NetHunt folders found")
                return [{**l, "crm_status": "api_error", "crm_stage": None} for l in leads]
            folder_id = folders[0].get("id")
            logger.info(f"Using NetHunt folder: {folders[0].get('name')} ({folder_id})")

        records = nethunt_list_records(folder_id, limit=1000)
        logger.info(f"Loaded {len(records)} records from NetHunt folder {folder_id}")

        # Создаем индекс для быстрого поиска
        record_index = {}
        for record in records:
            # NetHunt хранит данные в полях (fields)
            fields = record.get("fields", {})

            # Ищем телефон и email в полях записи
            for field_name, field_value in fields.items():
                field_name_lower = field_name.lower()

                # Индексируем по телефону
                if any(keyword in field_name_lower for keyword in ["phone", "телефон", "tel"]):
                    phone_value = str(field_value).strip().replace("+", "").replace("-", "").replace(" ", "")
                    if phone_value:
                        record_index[phone_value] = record

                # Индексируем по email
                if any(keyword in field_name_lower for keyword in ["email", "почта", "mail"]):
                    email_value = str(field_value).strip().lower()
                    if email_value:
                        record_index[email_value] = record

        # Обогащаем каждый лид
        enriched_leads = []
        for lead in leads:
            # Извлекаем контакты лида
            lead_phone = _extract_field(lead.get("field_data", []), {"phone_number", "phone", "Телефон"})
            lead_email = _extract_field(lead.get("field_data", []), {"email", "e-mail", "Эл. почта"})

            # Нормализуем для поиска
            normalized_phone = lead_phone.strip().replace("+", "").replace("-", "").replace(" ", "") if lead_phone else None
            normalized_email = lead_email.strip().lower() if lead_email else None

            # Ищем запись в индексе
            crm_record = None
            matched_by = None
            if normalized_phone and normalized_phone in record_index:
                crm_record = record_index[normalized_phone]
                matched_by = "phone"
            elif normalized_email and normalized_email in record_index:
                crm_record = record_index[normalized_email]
                matched_by = "email"

            if crm_record:
                # Маппинг статусов NetHunt
                crm_status, crm_stage = _map_nethunt_status(crm_record)

                enriched_leads.append({
                    **lead,
                    "crm_status": crm_status,
                    "crm_stage": crm_stage,
                    "crm_id": crm_record.get("id"),
                    "crm_matched_by": matched_by
                })
                logger.debug(f"Matched lead {lead.get('id')} with NetHunt record {crm_record.get('id')}")
            else:
                # Лид не найден в CRM
                enriched_leads.append({
                    **lead,
                    "crm_status": "not_found",
                    "crm_stage": None,
                    "crm_id": None
                })

        logger.info(f"NetHunt enrichment: {len([l for l in enriched_leads if l.get('crm_id')])} matched, {len([l for l in enriched_leads if l.get('crm_status') == 'not_found'])} not found")
        return enriched_leads

    except Exception as e:
        logger.error(f"NetHunt enrichment failed: {type(e).__name__}: {e}")
        return [{**l, "crm_status": "enrichment_error", "crm_stage": None} for l in leads]


async def _enrich_alfacrm(leads: List[Dict[str, Any]]):
    """Обогащение лидов данными из AlfaCRM с поиском по phone/email.

    AlfaCRM API: /api/v2/student/index
    Структура ответа: {"items": [...], "total": N, "page": N}
    Student поля: id, name, phone (array), email (array), study_status_id, is_study, balance, paid_lesson_count
    """
    if not os.getenv("ALFACRM_BASE_URL") or not os.getenv("ALFACRM_COMPANY_ID"):
        logger.warning("AlfaCRM credentials not configured, skipping enrichment")
        return [{**l, "crm_status": "not_configured", "crm_stage": None} for l in leads]

    try:
        # Используем существующий helper для получения студентов
        students_data = alfacrm_list_students(page=1, page_size=1000)

        # AlfaCRM возвращает items напрямую или в структуре {items: [], total: N}
        students = students_data if isinstance(students_data, list) else students_data.get("items", [])
        logger.info(f"Loaded {len(students)} students from AlfaCRM")

        # Создаем индекс для быстрого поиска по phone/email
        # ВАЖНО: phone и email в AlfaCRM это МАССИВЫ
        student_index = {}
        for student in students:
            # Индексируем по всем телефонам студента (массив)
            phones = student.get("phone", [])
            if isinstance(phones, str):  # Если вдруг строка, конвертируем в массив
                phones = [phones]
            for phone in phones:
                normalized = str(phone).strip().replace("+", "").replace("-", "").replace(" ", "").replace("(", "").replace(")", "")
                if normalized:
                    student_index[normalized] = student

            # Индексируем по всем email студента (массив)
            emails = student.get("email", [])
            if isinstance(emails, str):  # Если вдруг строка, конвертируем в массив
                emails = [emails]
            for email in emails:
                normalized = str(email).strip().lower()
                if normalized:
                    student_index[normalized] = student

        # Обогащаем каждый лид
        enriched_leads = []
        for lead in leads:
            # Извлекаем контакты лида
            lead_phone = _extract_field(lead.get("field_data", []), {"phone_number", "phone", "Телефон"})
            lead_email = _extract_field(lead.get("field_data", []), {"email", "e-mail", "Эл. почта"})

            # Нормализуем телефон для поиска
            normalized_phone = lead_phone.strip().replace("+", "").replace("-", "").replace(" ", "").replace("(", "").replace(")", "") if lead_phone else None
            normalized_email = lead_email.strip().lower() if lead_email else None

            # Ищем студента в индексе
            crm_student = None
            matched_by = None
            if normalized_phone and normalized_phone in student_index:
                crm_student = student_index[normalized_phone]
                matched_by = "phone"
            elif normalized_email and normalized_email in student_index:
                crm_student = student_index[normalized_email]
                matched_by = "email"

            if crm_student:
                # Маппинг статусов AlfaCRM в универсальные
                # Используем study_status_id согласно документации
                status_id = crm_student.get("study_status_id")
                crm_status = _map_alfacrm_status(status_id)
                crm_stage = _map_alfacrm_stage(crm_student)

                enriched_leads.append({
                    **lead,
                    "crm_status": crm_status,
                    "crm_stage": crm_stage,
                    "crm_id": crm_student.get("id"),
                    "crm_matched_by": matched_by
                })
                logger.debug(f"Matched lead {lead.get('id')} with AlfaCRM student {crm_student.get('id')}")
            else:
                # Лид не найден в CRM
                enriched_leads.append({
                    **lead,
                    "crm_status": "not_found",
                    "crm_stage": None,
                    "crm_id": None
                })

        logger.info(f"AlfaCRM enrichment: {len([l for l in enriched_leads if l.get('crm_id')])} matched, {len([l for l in enriched_leads if l.get('crm_status') == 'not_found'])} not found")
        return enriched_leads

    except Exception as e:
        logger.error(f"AlfaCRM enrichment failed: {type(e).__name__}: {e}")
        return [{**l, "crm_status": "enrichment_error", "crm_stage": None} for l in leads]


# Mapping functions for CRM statuses to universal format

def _map_alfacrm_status(status_id: int) -> str:
    """
    Маппинг статусов AlfaCRM в универсальные статусы воронки.

    AlfaCRM статусы (типичные):
    1 - Новый лид
    2 - Установлен контакт
    3 - В обработке
    4 - Назначен пробный урок
    5 - Проведен пробный
    6 - Продажа (студент)
    7 - Архив (отказ)
    """
    status_map = {
        1: "new",                  # Новый лид
        2: "contacted",            # Установлен контакт
        3: "in_progress",          # В обработке
        4: "trial_scheduled",      # Назначен пробный
        5: "trial_completed",      # Проведен пробный
        6: "converted",            # Продажа
        7: "archived",             # Архив/Отказ
        8: "no_answer"             # Недозвон
    }
    return status_map.get(status_id, "unknown")


def _map_alfacrm_stage(student: Dict[str, Any]) -> str:
    """
    Определение стадии воронки на основе данных студента.

    Возвращает текущую стадию: lead, trial, active, paused, archived
    """
    status_id = student.get("status_id")
    is_active = student.get("is_active", False)
    has_lessons = student.get("lessons_count", 0) > 0

    if status_id in [1, 2, 3]:  # Новый, контакт, обработка
        return "lead"
    elif status_id in [4, 5]:  # Пробный урок
        return "trial"
    elif status_id == 6:  # Продажа
        if is_active and has_lessons:
            return "active"
        elif not is_active:
            return "paused"
    elif status_id == 7:  # Архив
        return "archived"

    return "unknown"


def _map_nethunt_status(record: Dict[str, Any]) -> tuple[str, str]:
    """
    Маппинг статусов NetHunt в универсальные.

    Returns:
        (crm_status, crm_stage)
    """
    # NetHunt использует кастомные поля и статусы
    # Извлекаем status из record
    record_status = record.get("status", {})
    status_name = record_status.get("name", "").lower()

    # Типичные статусы NetHunt
    status_mapping = {
        "new": ("new", "lead"),
        "contacted": ("contacted", "lead"),
        "qualified": ("in_progress", "lead"),
        "proposal": ("in_progress", "trial"),
        "negotiation": ("trial_scheduled", "trial"),
        "closed won": ("converted", "active"),
        "closed lost": ("archived", "archived")
    }

    # Если статус не найден, пытаемся определить по keywords
    for key, (status, stage) in status_mapping.items():
        if key in status_name:
            return (status, stage)

    return ("unknown", "unknown")


# Helper calls for inspection endpoints
@retry(
    stop=stop_after_attempt(CRM_MAX_RETRIES),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type((requests.exceptions.Timeout, requests.exceptions.ConnectionError)),
    before_sleep=before_sleep_log(logger, logging.WARNING)
)
def nethunt_list_folders() -> List[Dict[str, Any]]:
    auth = os.getenv("NETHUNT_BASIC_AUTH")
    if not auth:
        raise RuntimeError("NETHUNT_BASIC_AUTH is not set")
    try:
        resp = requests.get("https://api.nethunt.com/api/v1/folders", headers={"Authorization": auth}, timeout=CRM_TIMEOUT)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.HTTPError as e:
        logger.error(f"NetHunt API error: {e.response.status_code} - {e.response.text}")
        raise
    except Exception as e:
        logger.error(f"NetHunt request failed: {type(e).__name__}: {e}")
        raise


@retry(
    stop=stop_after_attempt(CRM_MAX_RETRIES),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type((requests.exceptions.Timeout, requests.exceptions.ConnectionError)),
    before_sleep=before_sleep_log(logger, logging.WARNING)
)
def nethunt_folder_fields(folder_id: str) -> Dict[str, Any]:
    auth = os.getenv("NETHUNT_BASIC_AUTH")
    if not auth:
        raise RuntimeError("NETHUNT_BASIC_AUTH is not set")
    url = f"https://api.nethunt.com/api/v1/folders/{folder_id}/fields"
    try:
        resp = requests.get(url, headers={"Authorization": auth}, timeout=CRM_TIMEOUT)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.error(f"NetHunt folder fields request failed: {type(e).__name__}: {e}")
        raise


@retry(
    stop=stop_after_attempt(CRM_MAX_RETRIES),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type((requests.exceptions.Timeout, requests.exceptions.ConnectionError)),
    before_sleep=before_sleep_log(logger, logging.WARNING)
)
def nethunt_list_records(folder_id: str, limit: int = 500) -> List[Dict[str, Any]]:
    """List records from a NetHunt folder (simple pagination)."""
    auth = os.getenv("NETHUNT_BASIC_AUTH")
    if not auth:
        raise RuntimeError("NETHUNT_BASIC_AUTH is not set")
    url = f"https://api.nethunt.com/api/v1/folders/{folder_id}/records"
    params = {"limit": min(max(limit, 1), 1000)}
    try:
        resp = requests.get(url, headers={"Authorization": auth}, params=params, timeout=CRM_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        if isinstance(data, dict) and "records" in data:
            return data["records"]
        if isinstance(data, list):
            return data
        return []
    except Exception as e:
        logger.error(f"NetHunt list records failed: {type(e).__name__}: {e}")
        raise


@retry(
    stop=stop_after_attempt(CRM_MAX_RETRIES),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type((requests.exceptions.Timeout, requests.exceptions.ConnectionError)),
    before_sleep=before_sleep_log(logger, logging.WARNING)
)
def alfacrm_auth_get_token() -> str:
    base_url = os.getenv("ALFACRM_BASE_URL")
    email = os.getenv("ALFACRM_EMAIL")
    api_key = os.getenv("ALFACRM_API_KEY")
    if not base_url or not email or not api_key:
        raise RuntimeError("ALFACRM_BASE_URL/EMAIL/API_KEY not set")
    url = base_url.rstrip('/') + "/v2api/auth/login"
    try:
        resp = requests.post(url, json={"email": email, "api_key": api_key}, timeout=CRM_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        token = data.get("token") or data.get("data", {}).get("token")
        if not token:
            raise RuntimeError("Failed to get AlfaCRM token")
        return token
    except Exception as e:
        logger.error(f"AlfaCRM auth failed: {type(e).__name__}: {e}")
        raise


@retry(
    stop=stop_after_attempt(CRM_MAX_RETRIES),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type((requests.exceptions.Timeout, requests.exceptions.ConnectionError)),
    before_sleep=before_sleep_log(logger, logging.WARNING)
)
def alfacrm_list_companies() -> Dict[str, Any]:
    token = alfacrm_auth_get_token()
    base_url = os.getenv("ALFACRM_BASE_URL")
    url = base_url.rstrip('/') + "/v2api/company/index"
    try:
        resp = requests.get(url, headers={"X-ALFACRM-TOKEN": token}, timeout=CRM_TIMEOUT)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.error(f"AlfaCRM list companies failed: {type(e).__name__}: {e}")
        raise


@retry(
    stop=stop_after_attempt(CRM_MAX_RETRIES),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type((requests.exceptions.Timeout, requests.exceptions.ConnectionError)),
    before_sleep=before_sleep_log(logger, logging.WARNING)
)
def alfacrm_list_students(page: int = 1, page_size: int = 200) -> Dict[str, Any]:
    """Fetch students list from AlfaCRM. Uses customer/index with branch_ids filter."""
    token = alfacrm_auth_get_token()
    base_url = os.getenv("ALFACRM_BASE_URL")
    company_id = os.getenv("ALFACRM_COMPANY_ID")
    if not company_id:
        raise RuntimeError("ALFACRM_COMPANY_ID is not set")
    url = base_url.rstrip('/') + "/v2api/customer/index"
    payload = {
        "branch_ids": [int(company_id)],
        "page": page,
        "page_size": page_size,
    }
    try:
        resp = requests.post(url, headers={"X-ALFACRM-TOKEN": token}, json=payload, timeout=CRM_TIMEOUT)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.error(f"AlfaCRM list students failed: {type(e).__name__}: {e}")
        raise
