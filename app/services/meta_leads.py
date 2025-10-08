"""
Meta Leads API Integration

Получение лидов из Meta Lead Ads Forms с группировкой по кампаниям.
"""
import os
import logging
from typing import List, Dict, Optional
from datetime import datetime
import httpx

logger = logging.getLogger(__name__)

META_API_BASE = "https://graph.facebook.com/v21.0"


async def get_leadgen_forms(page_id: str, page_token: str) -> List[Dict]:
    """
    Получить все лид-формы страницы.

    Args:
        page_id: ID Facebook Page
        page_token: Page Access Token

    Returns:
        List of leadgen forms with id, name, status, leads_count
    """
    url = f"{META_API_BASE}/{page_id}/leadgen_forms"
    params = {
        "fields": "id,name,status,leads_count",
        "access_token": page_token
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url, params=params)

        if response.status_code != 200:
            error_data = response.json() if response.text else {}
            logger.error(f"Meta API Error: {response.status_code} - {error_data}")
            response.raise_for_status()

        data = response.json()

    forms = data.get("data", [])
    logger.info(f"Найдено {len(forms)} лид-форм для страницы {page_id}")

    return forms


async def get_form_leads(
    form_id: str,
    page_token: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 1000
) -> List[Dict]:
    """
    Получить лиды из конкретной лид-формы.

    Args:
        form_id: ID лид-формы
        page_token: Page Access Token
        start_date: Фильтр по дате (YYYY-MM-DD)
        end_date: Фильтр по дате (YYYY-MM-DD)
        limit: Максимальное количество лидов

    Returns:
        List of leads with full info (id, created_time, campaign_id, field_data, etc.)
    """
    url = f"{META_API_BASE}/{form_id}/leads"
    params = {
        "fields": "id,created_time,ad_id,ad_name,adset_id,adset_name,campaign_id,campaign_name,form_id,field_data",
        "access_token": page_token,
        "limit": limit
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        data = response.json()

    leads = data.get("data", [])

    # Фильтрация по датам если указаны
    if start_date or end_date:
        filtered_leads = []
        for lead in leads:
            lead_date = lead.get("created_time", "")[:10]  # YYYY-MM-DD

            if start_date and lead_date < start_date:
                continue
            if end_date and lead_date > end_date:
                continue

            filtered_leads.append(lead)

        leads = filtered_leads

    logger.info(f"Получено {len(leads)} лидов из формы {form_id}")

    return leads


def extract_lead_contact_info(lead: Dict) -> Dict[str, Optional[str]]:
    """
    Извлечь контактную информацию из лида (email, phone, name).

    Args:
        lead: Lead object from Meta API

    Returns:
        {
            "email": "example@example.com",
            "phone": "+380123456789",
            "name": "John Doe"
        }
    """
    field_data = lead.get("field_data", [])

    contact_info = {
        "email": None,
        "phone": None,
        "name": None
    }

    for field in field_data:
        field_name = field.get("name", "").lower()
        values = field.get("values", [])
        value = values[0] if values else None

        if not value:
            continue

        # Email
        if "email" in field_name or "адрес" in field_name or "e-mail" in field_name:
            contact_info["email"] = value

        # Phone
        elif "phone" in field_name or "телефон" in field_name or "number" in field_name:
            contact_info["phone"] = value

        # Name
        elif "name" in field_name or "ім'я" in field_name or "імя" in field_name or "full_name" in field_name:
            contact_info["name"] = value

    return contact_info


async def get_leads_for_period(
    page_id: str,
    page_token: str,
    start_date: str,
    end_date: str
) -> Dict[str, List[Dict]]:
    """
    Получить все лиды за период с группировкой по кампаниям.

    Args:
        page_id: ID Facebook Page
        page_token: Page Access Token
        start_date: Начало периода (YYYY-MM-DD)
        end_date: Конец периода (YYYY-MM-DD)

    Returns:
        {
            "campaign_120226862970630609": {
                "campaign_id": "120226862970630609",
                "campaign_name": "Student/Anatoly/...",
                "leads": [
                    {
                        "id": "24905838062380228",
                        "created_time": "2025-10-08T09:09:27+0000",
                        "email": "snv88@ukr.net",
                        "phone": "+380631045546",
                        "name": "Nata Petrenko",
                        "ad_id": "...",
                        "ad_name": "...",
                        ...
                    }
                ]
            }
        }
    """
    # 1. Получить все лид-формы
    forms = await get_leadgen_forms(page_id, page_token)

    # 2. Получить лиды из всех форм
    all_leads = []
    for form in forms:
        try:
            leads = await get_form_leads(
                form["id"],
                page_token,
                start_date,
                end_date
            )
            all_leads.extend(leads)
        except Exception as e:
            logger.error(f"Ошибка получения лидов из формы {form['id']}: {e}")
            continue

    logger.info(f"Всего получено {len(all_leads)} лидов за период {start_date} - {end_date}")

    # 3. Группировать по кампаниям
    campaigns_dict = {}

    for lead in all_leads:
        campaign_id = lead.get("campaign_id")
        if not campaign_id:
            logger.warning(f"Лид {lead.get('id')} без campaign_id, пропускаем")
            continue

        # Извлечь контактную информацию
        contact_info = extract_lead_contact_info(lead)

        # Обогатить лид контактами
        lead_enriched = {
            **lead,
            **contact_info
        }

        # Добавить в группу кампании
        if campaign_id not in campaigns_dict:
            campaigns_dict[campaign_id] = {
                "campaign_id": campaign_id,
                "campaign_name": lead.get("campaign_name", f"Campaign {campaign_id}"),
                "leads": []
            }

        campaigns_dict[campaign_id]["leads"].append(lead_enriched)

    logger.info(f"Лиды сгруппированы по {len(campaigns_dict)} кампаниям")

    return campaigns_dict


async def get_campaign_statistics(
    campaign_id: str,
    user_token: str,
    start_date: str,
    end_date: str
) -> Dict:
    """
    Получить статистику кампании из Meta Insights API.

    Args:
        campaign_id: ID кампании
        user_token: User Access Token
        start_date: Начало периода (YYYY-MM-DD)
        end_date: Конец периода (YYYY-MM-DD)

    Returns:
        {
            "spend": 100.50,
            "impressions": 50000,
            "clicks": 1500,
            "ctr": 3.0,
            "cpm": 2.01
        }
    """
    url = f"{META_API_BASE}/{campaign_id}/insights"
    params = {
        "fields": "spend,impressions,clicks,ctr,cpm,reach",
        "time_range": f"{{'since':'{start_date}','until':'{end_date}'}}",
        "access_token": user_token
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        data = response.json()

    insights = data.get("data", [])
    if not insights:
        return {
            "spend": 0,
            "impressions": 0,
            "clicks": 0,
            "ctr": 0,
            "cpm": 0,
            "reach": 0
        }

    # Суммировать если несколько записей
    stats = {
        "spend": sum(float(i.get("spend", 0)) for i in insights),
        "impressions": sum(int(i.get("impressions", 0)) for i in insights),
        "clicks": sum(int(i.get("clicks", 0)) for i in insights),
        "ctr": sum(float(i.get("ctr", 0)) for i in insights) / len(insights) if insights else 0,
        "cpm": sum(float(i.get("cpm", 0)) for i in insights) / len(insights) if insights else 0,
        "reach": sum(int(i.get("reach", 0)) for i in insights)
    }

    return stats
