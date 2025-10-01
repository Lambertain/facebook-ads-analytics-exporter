import os
from typing import List, Dict, Any

import requests


GRAPH_URL = "https://graph.facebook.com/v19.0"


def fetch_insights(ad_account_id: str, access_token: str, date_from: str, date_to: str, level: str = "campaign") -> List[Dict[str, Any]]:
    """Fetch basic insights for campaigns within a date range.

    Returns a list of dicts with campaign metrics.
    """
    url = f"{GRAPH_URL}/{ad_account_id}/insights"
    params = {
        "access_token": access_token,
        "time_range": f"{{'since':'{date_from}','until':'{date_to}'}}",
        "level": level,
        "time_increment": 1,
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
    while True:
        resp = requests.get(url, params=params, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        results.extend(data.get("data", []))
        paging = data.get("paging", {})
        next_url = paging.get("next")
        if not next_url:
            break
        url = next_url
        params = {}  # next contains full URL
    return results


def fetch_leads(access_token: str, date_from: str, date_to: str) -> List[Dict[str, Any]]:
    """Fetch leads from all pages connected to the ad account.

    Note: In a production setup, enumerate pages or leadgen forms relevant to your ads.
    This is a simplified example using '/me/accounts' then '/{page_id}/leadgen_forms'.
    """
    results: List[Dict[str, Any]] = []

    # Step 1: list pages the token can access
    pages = _get_all(f"{GRAPH_URL}/me/accounts", access_token)
    for page in pages:
        page_id = page.get("id")
        if not page_id:
            continue
        # Step 2: list leadgen forms on the page
        forms = _get_all(f"{GRAPH_URL}/{page_id}/leadgen_forms", access_token)
        for form in forms:
            form_id = form.get("id")
            if not form_id:
                continue
            # Step 3: fetch leads for the form in the date range
            url = f"{GRAPH_URL}/{form_id}/leads"
            params = {
                "access_token": access_token,
                "filtering": f"[{{'field':'time_created','operator':'GREATER_THAN','value': '{date_from}T00:00:00+0000'}},"
                              f"{{'field':'time_created','operator':'LESS_THAN','value': '{date_to}T23:59:59+0000'}}]",
                "limit": 500,
            }
            while True:
                resp = requests.get(url, params=params, timeout=60)
                resp.raise_for_status()
                data = resp.json()
                for lead in data.get("data", []):
                    results.append({
                        "id": lead.get("id"),
                        "created_time": lead.get("created_time"),
                        "field_data": lead.get("field_data", []),
                        "page_id": page_id,
                        "form_id": form_id,
                    })
                paging = data.get("paging", {})
                next_url = paging.get("next")
                if not next_url:
                    break
                url = next_url
                params = {}

    return results


def _get_all(url: str, access_token: str):
    params = {"access_token": access_token, "limit": 100}
    results = []
    while True:
        resp = requests.get(url, params=params, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        results.extend(data.get("data", []))
        next_url = data.get("paging", {}).get("next")
        if not next_url:
            break
        url = next_url
        params = {}
    return results
