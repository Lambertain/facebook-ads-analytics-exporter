"""
Analytics Processor - основний модуль для обробки даних кампаній.

Логіка роботи:
1. Фільтрує РК за ключовими словами (Teacher/Vchitel або Student/Shkolnik)
2. Забирає метрики РК з Facebook Ads API
3. Забирає ліди (телефони) з Facebook Ads Leads API
4. Матчить телефони з контактами в NetHunt
5. Підраховує статистику по воронці
6. Обчислює метрики
"""

import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import requests

logger = logging.getLogger(__name__)


class AnalyticsProcessor:
    """Процесор для аналізу рекламних кампаній."""

    def __init__(self, campaign_type: str, date_start: str, date_stop: str):
        """
        Args:
            campaign_type: 'teachers' або 'students'
            date_start: Дата початку періоду (YYYY-MM-DD)
            date_stop: Дата кінця періоду (YYYY-MM-DD)
        """
        self.campaign_type = campaign_type
        self.date_start = date_start
        self.date_stop = date_stop

        # Credentials
        self.meta_token = os.getenv("META_ACCESS_TOKEN")
        self.ad_account_id = os.getenv("META_AD_ACCOUNT_ID")
        self.nethunt_auth = os.getenv("NETHUNT_BASIC_AUTH")

        # Keywords
        if campaign_type == "teachers":
            keywords_str = os.getenv("CAMPAIGN_KEYWORDS_TEACHERS", "Teacher,Vchitel")
        else:
            keywords_str = os.getenv("CAMPAIGN_KEYWORDS_STUDENTS", "Student,Shkolnik")

        self.keywords = [k.strip() for k in keywords_str.split(",")]
        logger.info(f"Initialized processor for {campaign_type} with keywords: {self.keywords}")

    def filter_campaigns_by_keywords(self, campaigns: List[Dict]) -> List[Dict]:
        """Фільтрує кампанії за ключовими словами в назві.

        Args:
            campaigns: Список всіх кампаній з Facebook Ads

        Returns:
            Список відфільтрованих кампаній
        """
        filtered = []
        for campaign in campaigns:
            name = campaign.get("name", "")
            if any(keyword.lower() in name.lower() for keyword in self.keywords):
                filtered.append(campaign)
                logger.debug(f"Matched campaign: {name}")

        logger.info(f"Filtered {len(filtered)} campaigns from {len(campaigns)} total")
        return filtered

    def get_campaigns_from_fb(self) -> List[Dict]:
        """Забирає всі кампанії з Facebook Ads за період.

        Returns:
            Список кампаній з метриками
        """
        if not self.meta_token or not self.ad_account_id:
            raise RuntimeError("META_ACCESS_TOKEN or META_AD_ACCOUNT_ID not configured")

        url = f"https://graph.facebook.com/v21.0/{self.ad_account_id}/campaigns"
        params = {
            "access_token": self.meta_token,
            "fields": "name,id,status",
            "limit": 100,
            "time_range": f"{{'since':'{self.date_start}','until':'{self.date_stop}'}}"
        }

        try:
            resp = requests.get(url, params=params, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            campaigns = data.get("data", [])
            logger.info(f"Fetched {len(campaigns)} campaigns from Facebook Ads")
            return campaigns
        except Exception as e:
            logger.error(f"Failed to fetch campaigns: {e}")
            raise

    def get_campaign_insights(self, campaign_id: str) -> Dict[str, Any]:
        """Забирає метрики для конкретної кампанії.

        Args:
            campaign_id: ID кампанії

        Returns:
            Словник з метриками
        """
        url = f"https://graph.facebook.com/v21.0/{campaign_id}/insights"
        params = {
            "access_token": self.meta_token,
            "fields": "spend,impressions,clicks,ctr,cpm,reach,campaign_name",
            "time_range": f"{{'since':'{self.date_start}','until':'{self.date_stop}'}}",
            "time_increment": "all_days"
        }

        try:
            resp = requests.get(url, params=params, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            insights = data.get("data", [])

            if insights:
                return insights[0]  # Повертаємо перший результат
            else:
                logger.warning(f"No insights for campaign {campaign_id}")
                return {}
        except Exception as e:
            logger.error(f"Failed to fetch insights for {campaign_id}: {e}")
            return {}

    def get_campaign_leads(self, campaign_id: str) -> List[str]:
        """Забирає телефони всіх лідів з кампанії.

        Args:
            campaign_id: ID кампанії

        Returns:
            Список унікальних номерів телефонів
        """
        phones = []

        try:
            # 1. Отримуємо всі ads для кампанії
            ads_url = f"https://graph.facebook.com/v21.0/{campaign_id}/ads"
            ads_params = {
                "access_token": self.meta_token,
                "fields": "id,name",
                "limit": 100
            }
            ads_resp = requests.get(ads_url, params=ads_params, timeout=30)
            ads_resp.raise_for_status()
            ads = ads_resp.json().get("data", [])

            logger.debug(f"Found {len(ads)} ads for campaign {campaign_id}")

            # 2. Для кожного ad отримуємо leadgen forms
            for ad in ads:
                ad_id = ad["id"]

                # Отримуємо форми для ad
                forms_url = f"https://graph.facebook.com/v21.0/{ad_id}"
                forms_params = {
                    "access_token": self.meta_token,
                    "fields": "leadgen_forms{id,name}"
                }
                forms_resp = requests.get(forms_url, params=forms_params, timeout=30)
                forms_resp.raise_for_status()
                forms_data = forms_resp.json().get("leadgen_forms", {}).get("data", [])

                # 3. Для кожної форми отримуємо ліди
                for form in forms_data:
                    form_id = form["id"]

                    leads_url = f"https://graph.facebook.com/v21.0/{form_id}/leads"
                    leads_params = {
                        "access_token": self.meta_token,
                        "fields": "field_data",
                        "filtering": f"[{{'field':'time_created','operator':'GREATER_THAN','value':{int(datetime.strptime(self.date_start, '%Y-%m-%d').timestamp())}}}]",
                        "limit": 500
                    }
                    leads_resp = requests.get(leads_url, params=leads_params, timeout=30)
                    leads_resp.raise_for_status()
                    leads = leads_resp.json().get("data", [])

                    # Витягуємо телефони
                    for lead in leads:
                        field_data = lead.get("field_data", [])
                        for field in field_data:
                            if field.get("name") in ["phone_number", "PHONE", "phone"]:
                                phone = field.get("values", [None])[0]
                                if phone:
                                    phones.append(phone.strip())

            logger.info(f"Found {len(phones)} leads for campaign {campaign_id}")
            return list(set(phones))  # Унікальні телефони

        except Exception as e:
            logger.error(f"Failed to fetch leads for campaign {campaign_id}: {e}")
            return []

    def search_contact_in_nethunt(self, phone: str) -> Optional[Dict]:
        """Шукає контакт в NetHunt за номером телефону.

        Args:
            phone: Номер телефону

        Returns:
            Дані контакту або None якщо не знайдено
        """
        if not self.nethunt_auth:
            logger.warning("NetHunt auth not configured")
            return None

        try:
            url = "https://api.nethunt.com/api/v1/zapier/contacts/search"
            headers = {"Authorization": self.nethunt_auth}
            params = {"phone": phone}

            resp = requests.get(url, headers=headers, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()

            if data and len(data) > 0:
                return data[0]  # Повертаємо перший знайдений контакт
            return None

        except Exception as e:
            logger.error(f"Failed to search contact {phone} in NetHunt: {e}")
            return None

    def get_contact_status_history(self, contact_id: str) -> List[str]:
        """Отримує історію статусів контакту з NetHunt.

        Args:
            contact_id: ID контакту в NetHunt

        Returns:
            Список всіх статусів через які пройшов контакт
        """
        if not self.nethunt_auth:
            return []

        try:
            url = f"https://api.nethunt.com/api/v1/zapier/contacts/{contact_id}/history"
            headers = {"Authorization": self.nethunt_auth}

            resp = requests.get(url, headers=headers, timeout=10)
            resp.raise_for_status()
            history = resp.json()

            # Витягуємо всі унікальні статуси з історії
            statuses = []
            for event in history:
                if event.get("type") == "status_change":
                    status = event.get("new_status")
                    if status and status not in statuses:
                        statuses.append(status)

            # Додаємо поточний статус
            contact_url = f"https://api.nethunt.com/api/v1/zapier/contacts/{contact_id}"
            contact_resp = requests.get(contact_url, headers=headers, timeout=10)
            contact_resp.raise_for_status()
            contact_data = contact_resp.json()
            current_status = contact_data.get("status")
            if current_status and current_status not in statuses:
                statuses.append(current_status)

            return statuses

        except Exception as e:
            logger.error(f"Failed to get status history for contact {contact_id}: {e}")
            return []

    def calculate_funnel_stats(self, phones: List[str]) -> Dict[str, int]:
        """Підраховує статистику по воронці для списку телефонів.

        Логіка: якщо лід пройшов через 3 статуси, він враховується в 3 колонках.
        Загальна кількість лідів = len(phones) (унікальні номери).

        Args:
            phones: Список номерів телефонів

        Returns:
            Словник з підрахунками по кожному статусу
        """
        stats = {}
        total_found_in_nethunt = 0

        for phone in phones:
            # Шукаємо контакт
            contact = self.search_contact_in_nethunt(phone)

            if not contact:
                continue  # Контакт не знайдено в NetHunt

            total_found_in_nethunt += 1
            contact_id = contact.get("id")

            # Отримуємо історію статусів
            statuses = self.get_contact_status_history(contact_id)

            # Рахуємо кожен статус окремо
            for status in statuses:
                if status not in stats:
                    stats[status] = 0
                stats[status] += 1

        logger.info(f"Found {total_found_in_nethunt} contacts in NetHunt from {len(phones)} phones")
        logger.info(f"Funnel stats: {stats}")

        return stats

    def process(self) -> List[Dict[str, Any]]:
        """Основна функція обробки.

        Returns:
            Список рядків для таблиці з усіма метриками
        """
        logger.info(f"Starting analytics processing for {self.campaign_type}")

        # 1. Забираємо всі кампанії
        all_campaigns = self.get_campaigns_from_fb()

        # 2. Фільтруємо за ключовими словами
        filtered_campaigns = self.filter_campaigns_by_keywords(all_campaigns)

        # 3. Для кожної кампанії збираємо дані
        results = []
        for campaign in filtered_campaigns:
            campaign_id = campaign["id"]
            campaign_name = campaign["name"]

            logger.info(f"Processing campaign: {campaign_name}")

            # Метрики з Facebook
            insights = self.get_campaign_insights(campaign_id)

            # Ліди з Facebook
            phones = self.get_campaign_leads(campaign_id)
            total_leads = len(phones)

            # Статистика з NetHunt
            funnel_stats = self.calculate_funnel_stats(phones)

            # Обчислюємо метрики
            spend = float(insights.get("spend", 0) or 0)
            cpl = spend / total_leads if total_leads > 0 else 0  # Cost Per Lead

            # Формуємо результат
            row = {
                "Назва реклами": campaign_name,
                "Посилання на рекламну компанію": f"https://facebook.com/campaign/{campaign_id}",
                "Дата аналізу": datetime.now().strftime("%Y-%m-%d"),
                "Період аналізу запущеної компанії": f"{self.date_start} - {self.date_stop}",
                "Витрачений бюджет в $": spend,
                "Кількість лідів": total_leads,
                "Кількість показів": int(insights.get("impressions", 0) or 0),
                "Кількість кліків": int(insights.get("clicks", 0) or 0),
                "CTR (%)": insights.get("ctr", "0"),
                "CPM ($)": insights.get("cpm", "0"),
                "Охоплення": int(insights.get("reach", 0) or 0),
                "Ціна в $ за ліда": round(cpl, 2),
            }

            # Додаємо статистику воронки
            row.update(funnel_stats)

            results.append(row)

        logger.info(f"Processed {len(results)} campaigns")
        return results
