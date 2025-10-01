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
    auth = os.getenv("NETHUNT_BASIC_AUTH")
    # Placeholder passthrough unless later matched by phone/email against records we fetch by folder
    await asyncio.sleep(0)
    return [{**l, "crm_status": None, "crm_stage": None} for l in leads]


async def _enrich_alfacrm(leads: List[Dict[str, Any]]):
    base_url = os.getenv("ALFACRM_BASE_URL")
    email = os.getenv("ALFACRM_EMAIL")
    api_key = os.getenv("ALFACRM_API_KEY")
    company_id = os.getenv("ALFACRM_COMPANY_ID")
    # Placeholder passthrough; real matching to be implemented with provided base_url/company_id
    await asyncio.sleep(0)
    return [{**l, "crm_status": None, "crm_stage": None} for l in leads]


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
    url = base_url.rstrip('/') + "/api/v2/auth/login"
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
    url = base_url.rstrip('/') + "/api/v2/company/index"
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
    """Fetch students list from AlfaCRM. Adjust endpoint if your account uses different path."""
    token = alfacrm_auth_get_token()
    base_url = os.getenv("ALFACRM_BASE_URL")
    company_id = os.getenv("ALFACRM_COMPANY_ID")
    if not company_id:
        raise RuntimeError("ALFACRM_COMPANY_ID is not set")
    url = base_url.rstrip('/') + "/api/v2/student/index"
    payload = {
        "company_id": int(company_id),
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
