import os
import logging
from typing import List, Dict, Any

import requests
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log
)

logger = logging.getLogger(__name__)


GRAPH_URL = "https://graph.facebook.com/v19.0"

DEFAULT_TIMEOUT = int(os.getenv("META_API_TIMEOUT", "30"))
MAX_RETRIES = int(os.getenv("META_API_MAX_RETRIES", "3"))


@retry(
    stop=stop_after_attempt(MAX_RETRIES),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    retry=retry_if_exception_type((requests.exceptions.Timeout, requests.exceptions.ConnectionError)),
    before_sleep=before_sleep_log(logger, logging.WARNING)
)
def _make_meta_request(url: str, params: dict, timeout: int = DEFAULT_TIMEOUT) -> dict:
    try:
        resp = requests.get(url, params=params, timeout=timeout)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 429:
            logger.warning(f"Meta API rate limit hit: {e}")
            raise
        elif e.response.status_code >= 500:
            logger.error(f"Meta API server error: {e.response.status_code} - {e.response.text}")
            raise
        else:
            logger.error(f"Meta API client error: {e.response.status_code} - {e.response.text}")
            raise
    except requests.exceptions.Timeout:
        logger.error(f"Meta API timeout after {timeout}s: {url}")
        raise
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Meta API connection error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected Meta API error: {type(e).__name__}: {e}")
        raise


def fetch_insights(ad_account_id: str, access_token: str, date_from: str, date_to: str, level: str = "campaign") -> List[Dict[str, Any]]:
    """Fetch basic insights for campaigns within a date range.

    Returns a list of dicts with campaign metrics.
    """
    url = f"{GRAPH_URL}/{ad_account_id}/insights"
    params = {
        "access_token": access_token,
        "time_range": f"{{'since':'{date_from}','until':'{date_to}'}}",
        "level": level,
        "fields": ",".join([
            "date_start",
            "date_stop",
            "campaign_id",
            "campaign_name",
            "adset_id",
            "adset_name",
            "ad_id",
            "ad_name",
            "impressions",
            "clicks",
            "spend",
            "reach",
            "cpc",
            "cpm",
            "ctr",
            "objective",
        ]),
        "limit": 500,
    }

    results: List[Dict[str, Any]] = []
    page_count = 0
    try:
        while True:
            page_count += 1
            logger.info(f"Fetching Meta insights page {page_count} for account {ad_account_id}")
            data = _make_meta_request(url, params)
            results.extend(data.get("data", []))
            paging = data.get("paging", {})
            next_url = paging.get("next")
            if not next_url:
                break
            url = next_url
            params = {}
        logger.info(f"Successfully fetched {len(results)} insights from {page_count} pages")
        return results
    except Exception as e:
        logger.error(f"Failed to fetch Meta insights after {page_count} pages: {type(e).__name__}: {e}")
        if results:
            logger.warning(f"Returning partial results: {len(results)} insights from {page_count - 1} pages")
        return results


# ФУНКЦИЯ ОТКЛЮЧЕНА: Текущий Meta токен не имеет прав для извлечения лидов (leads_retrieval permission).
# Токен позволяет только:
# - Извлечение статистики рекламных кампаний (insights)
# - Получение текстов и изображений объявлений (creatives)
# - Заполнение таблиц УЧИТЕЛЯ, СТУДЕНТЫ, РЕКЛАМА
#
# Для активации функции необходимо:
# 1. Получить новый Meta токен с правами leads_retrieval
# 2. Раскомментировать код ниже
# 3. Добавить вызов fetch_leads() в main.py

# def fetch_leads(access_token: str, date_from: str, date_to: str) -> List[Dict[str, Any]]:
#     """Fetch leads from all pages connected to the ad account.
#
#     Note: In a production setup, enumerate pages or leadgen forms relevant to your ads.
#     This is a simplified example using '/me/accounts' then '/{page_id}/leadgen_forms'.
#     """
#     results: List[Dict[str, Any]] = []
#
#     try:
#         logger.info("Starting Meta leads fetch process")
#         pages = _get_all(f"{GRAPH_URL}/me/accounts", access_token)
#         logger.info(f"Found {len(pages)} pages to process")
#     except Exception as e:
#         logger.error(f"Failed to list Meta pages: {type(e).__name__}: {e}")
#         return []
#
#     for page in pages:
#         page_id = page.get("id")
#         if not page_id:
#             continue
#         # Step 2: list leadgen forms on the page
#         forms = _get_all(f"{GRAPH_URL}/{page_id}/leadgen_forms", access_token)
#         for form in forms:
#             form_id = form.get("id")
#             if not form_id:
#                 continue
#             # Step 3: fetch leads for the form in the date range
#             url = f"{GRAPH_URL}/{form_id}/leads"
#             params = {
#                 "access_token": access_token,
#                 "filtering": f"[{{'field':'time_created','operator':'GREATER_THAN','value': '{date_from}T00:00:00+0000'}},"
#                               f"{{'field':'time_created','operator':'LESS_THAN','value': '{date_to}T23:59:59+0000'}}]",
#                 "limit": 500,
#             }
#             try:
#                 while True:
#                     data = _make_meta_request(url, params)
#                     for lead in data.get("data", []):
#                         results.append({
#                             "id": lead.get("id"),
#                             "created_time": lead.get("created_time"),
#                             "field_data": lead.get("field_data", []),
#                             "page_id": page_id,
#                             "form_id": form_id,
#                         })
#                     paging = data.get("paging", {})
#                     next_url = paging.get("next")
#                     if not next_url:
#                         break
#                     url = next_url
#                     params = {}
#             except Exception as e:
#                 logger.warning(f"Failed to fetch leads for form {form_id}: {type(e).__name__}: {e}")
#                 continue
#
#     logger.info(f"Successfully fetched {len(results)} total leads")
#     return results


def fetch_ad_creatives(ad_ids: List[str], access_token: str, ad_account_id: str = None) -> Dict[str, Dict[str, Any]]:
    """Fetch creative details (text, images, videos) for given ad IDs.

    Returns a dict mapping ad_id to creative data.
    """
    creatives = {}

    for ad_id in ad_ids:
        try:
            url = f"{GRAPH_URL}/{ad_id}"
            params = {
                "access_token": access_token,
                "fields": "creative{name,title,body,image_hash,image_url,video_id,thumbnail_url,object_story_spec}"
            }
            data = _make_meta_request(url, params)
            creative_data = data.get("creative", {})

            # Extract text from object_story_spec if available
            story_spec = creative_data.get("object_story_spec", {})
            link_data = story_spec.get("link_data", {}) or story_spec.get("video_data", {})

            # Construct image URL from hash if image_url not available
            image_url = creative_data.get("image_url", "")
            image_hash = creative_data.get("image_hash", "")

            # If no image_url but we have image_hash and ad_account_id, construct URL
            if not image_url and image_hash and ad_account_id:
                image_url = f"https://graph.facebook.com/v18.0/{ad_account_id}/adimages?hashes=[%22{image_hash}%22]&access_token={access_token}"
                logger.info(f"Constructed image URL from hash for ad {ad_id}: {image_url[:100]}...")

            creatives[ad_id] = {
                "name": creative_data.get("name", ""),
                "title": creative_data.get("title") or link_data.get("name", ""),
                "body": creative_data.get("body") or link_data.get("message", ""),
                "image_hash": image_hash,
                "image_url": image_url,
                "video_id": creative_data.get("video_id", ""),
                "thumbnail_url": creative_data.get("thumbnail_url", ""),
            }

        except Exception as e:
            logger.warning(f"Failed to fetch creative for ad {ad_id}: {e}")
            creatives[ad_id] = {
                "name": "",
                "title": "",
                "body": "",
                "image_hash": "",
                "image_url": "",
                "video_id": "",
                "thumbnail_url": "",
            }

    logger.info(f"Fetched creative details for {len(creatives)} ads")
    return creatives


def _get_all(url: str, access_token: str):
    params = {"access_token": access_token, "limit": 100}
    results = []
    page_count = 0
    while True:
        page_count += 1
        data = _make_meta_request(url, params)
        results.extend(data.get("data", []))
        next_url = data.get("paging", {}).get("next")
        if not next_url:
            break
        url = next_url
        params = {}
    logger.debug(f"Fetched {len(results)} items from {page_count} pages")
    return results
