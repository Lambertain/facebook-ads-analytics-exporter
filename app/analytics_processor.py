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
        self.facebook_page_id = os.getenv("FACEBOOK_PAGE_ID")  # Потрібен для leadgen forms!

        # CRM setup based on campaign type
        if campaign_type == "teachers":
            self.crm_provider = os.getenv("CRM_PROVIDER_TEACHERS", "nethunt")
            keywords_str = os.getenv("CAMPAIGN_KEYWORDS_TEACHERS", "Teacher,Vchitel")
        else:
            self.crm_provider = os.getenv("CRM_PROVIDER_STUDENTS", "alfacrm")
            keywords_str = os.getenv("CAMPAIGN_KEYWORDS_STUDENTS", "Student,Shkolnik")

        self.nethunt_auth = os.getenv("NETHUNT_BASIC_AUTH")

        self.keywords = [k.strip() for k in keywords_str.split(",")]
        logger.info(f"Initialized processor for {campaign_type} with keywords: {self.keywords}, CRM: {self.crm_provider}")

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
                logger.info(f"Matched campaign: {name}")
            else:
                logger.info(f"Skipped campaign: {name} (keywords: {self.keywords})")

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
            "limit": 100
        }

        try:
            resp = requests.get(url, params=params, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            campaigns = data.get("data", [])
            logger.info(f"Fetched {len(campaigns)} campaigns from Facebook Ads")
            logger.info(f"Campaign names: {[c.get('name') for c in campaigns]}")
            return campaigns
        except Exception as e:
            logger.error(f"Failed to fetch campaigns: {e}")
            logger.error(f"Response: {resp.text if 'resp' in locals() else 'No response'}")
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
            "date_preset": "last_30d"
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

    # ВРЕМЕННО ОТКЛЮЧЕНО - ожидаем получение прав доступа от клиента
    # Необходимые permissions: leads_retrieval, pages_manage_ads
    # После получения нового токена - раскомментировать
    #
    # def get_page_leadgen_forms(self, page_id: str) -> List[Dict]:
    #     """Отримує всі leadgen forms для Facebook Page.
    #
    #     Args:
    #         page_id: ID Facebook Page
    #
    #     Returns:
    #         Список форм з id, name, created_time
    #     """
    #     try:
    #         forms_url = f"https://graph.facebook.com/v21.0/{page_id}/leadgen_forms"
    #         forms_params = {
    #             "access_token": self.meta_token,
    #             "fields": "id,name,created_time",
    #             "limit": 200
    #         }
    #         forms_resp = requests.get(forms_url, params=forms_params, timeout=30)
    #         forms_resp.raise_for_status()
    #         forms = forms_resp.json().get("data", [])
    #         logger.info(f"Found {len(forms)} leadgen forms for page {page_id}")
    #         return forms
    #     except Exception as e:
    #         logger.error(f"Failed to get leadgen forms for page {page_id}: {e}")
    #         return []

    # ВРЕМЕННО ОТКЛЮЧЕНО - ожидаем получение прав доступа от клиента
    # Необходимые permissions: leads_retrieval
    # После получения нового токена - раскомментировать
    #
    # def get_leads_from_form(self, form_id: str) -> List[Dict]:
    #     """Отримує всі ліди з конкретної форми за період.
    #
    #     Args:
    #         form_id: ID leadgen форми
    #
    #     Returns:
    #         Список лідів з field_data, campaign_id, ad_id тощо
    #     """
    #     try:
    #         # Конвертуємо дати у UNIX timestamp
    #         start_ts = int(datetime.strptime(self.date_start, '%Y-%m-%d').timestamp())
    #         end_ts = int(datetime.strptime(self.date_stop, '%Y-%m-%d').timestamp())
    #
    #         leads_url = f"https://graph.facebook.com/v21.0/{form_id}/leads"
    #         leads_params = {
    #             "access_token": self.meta_token,
    #             "fields": "created_time,id,ad_id,ad_name,adset_id,adset_name,campaign_id,campaign_name,field_data",
    #             "limit": 500,
    #             "filtering": f"[{{'field':'time_created','operator':'GREATER_THAN','value':{start_ts}}},{{'field':'time_created','operator':'LESS_THAN','value':{end_ts}}}]"
    #         }
    #         leads_resp = requests.get(leads_url, params=leads_params, timeout=30)
    #         leads_resp.raise_for_status()
    #         leads = leads_resp.json().get("data", [])
    #         logger.info(f"Found {len(leads)} leads from form {form_id} for period {self.date_start} - {self.date_stop}")
    #         return leads
    #     except Exception as e:
    #         logger.warning(f"Failed to get leads for form {form_id}: {e}")
    #         return []

    # ВРЕМЕННО ОТКЛЮЧЕНО - ожидаем получение прав доступа от клиента
    # Необходимые permissions: leads_retrieval, pages_manage_ads
    # После получения нового токена - раскомментировать
    #
    # def get_campaign_leads(self, campaign_id: str, page_id: str) -> List[str]:
    #     """Забирає телефони всіх лідів з кампанії через Page leadgen forms.
    #
    #     Args:
    #         campaign_id: ID кампанії
    #         page_id: ID Facebook Page (обов'язково!)
    #
    #     Returns:
    #         Список унікальних номерів телефонів
    #     """
    #     logger.info(f"START get_campaign_leads for campaign {campaign_id}, page {page_id}")
    #     phones = []
    #
    #     try:
    #         # 1. Отримуємо всі форми зі сторінки
    #         forms = self.get_page_leadgen_forms(page_id)
    #
    #         if not forms:
    #             logger.warning(f"No leadgen forms found for page {page_id}")
    #             return []
    #
    #         # 2. Для кожної форми отримуємо ліди
    #         for form in forms:
    #             form_id = form["id"]
    #             leads = self.get_leads_from_form(form_id)
    #
    #             # 3. Фільтруємо ліди за campaign_id і витягуємо телефони
    #             for lead in leads:
    #                 if lead.get("campaign_id") == campaign_id:
    #                     field_data = lead.get("field_data", [])
    #                     for field in field_data:
    #                         if field.get("name") in ["phone_number", "PHONE", "phone"]:
    #                             phone = field.get("values", [None])[0]
    #                             if phone:
    #                                 phones.append(phone.strip())
    #
    #         logger.info(f"Found {len(phones)} leads for campaign {campaign_id}")
    #         return list(set(phones))  # Унікальні телефони
    #
    #     except Exception as e:
    #         logger.error(f"EXCEPTION in get_campaign_leads for {campaign_id}: {type(e).__name__}: {e}")
    #         return []

    # ВРЕМЕННО ОТКЛЮЧЕНО - ожидаем получение прав доступа от клиента для Facebook Leads
    # После получения лидов через Facebook API - раскомментировать
    #
    # def search_contact_in_nethunt(self, phone: str) -> Optional[Dict]:
    #     """Шукає контакт в NetHunt за номером телефону.
    #
    #     Args:
    #         phone: Номер телефону
    #
    #     Returns:
    #         Дані контакту або None якщо не знайдено
    #     """
    #     if not self.nethunt_auth:
    #         logger.warning("NetHunt auth not configured")
    #         return None
    #
    #     try:
    #         url = "https://api.nethunt.com/api/v1/zapier/contacts/search"
    #         headers = {"Authorization": self.nethunt_auth}
    #         params = {"phone": phone}
    #
    #         resp = requests.get(url, headers=headers, params=params, timeout=10)
    #         resp.raise_for_status()
    #         data = resp.json()
    #
    #         if data and len(data) > 0:
    #             return data[0]  # Повертаємо перший знайдений контакт
    #         return None
    #
    #     except Exception as e:
    #         logger.error(f"Failed to search contact {phone} in NetHunt: {e}")
    #         return None

    # ВРЕМЕННО ОТКЛЮЧЕНО - ожидаем получение прав доступа от клиента для Facebook Leads
    # После получения лидов через Facebook API - раскомментировать
    #
    # def get_contact_status_history(self, contact_id: str) -> List[str]:
    #     """Отримує історію статусів контакту з NetHunt.
    #
    #     Args:
    #         contact_id: ID контакту в NetHunt
    #
    #     Returns:
    #         Список всіх статусів через які пройшов контакт
    #     """
    #     if not self.nethunt_auth:
    #         return []
    #
    #     try:
    #         url = f"https://api.nethunt.com/api/v1/zapier/contacts/{contact_id}/history"
    #         headers = {"Authorization": self.nethunt_auth}
    #
    #         resp = requests.get(url, headers=headers, timeout=10)
    #         resp.raise_for_status()
    #         history = resp.json()
    #
    #         # Витягуємо всі унікальні статуси з історії
    #         statuses = []
    #         for event in history:
    #             if event.get("type") == "status_change":
    #                 status = event.get("new_status")
    #                 if status and status not in statuses:
    #                     statuses.append(status)
    #
    #         # Додаємо поточний статус
    #         contact_url = f"https://api.nethunt.com/api/v1/zapier/contacts/{contact_id}"
    #         contact_resp = requests.get(contact_url, headers=headers, timeout=10)
    #         contact_resp.raise_for_status()
    #         contact_data = contact_resp.json()
    #         current_status = contact_data.get("status")
    #         if current_status and current_status not in statuses:
    #             statuses.append(current_status)
    #
    #         return statuses
    #
    #     except Exception as e:
    #         logger.error(f"Failed to get status history for contact {contact_id}: {e}")
    #         return []
    #
    # def calculate_funnel_stats(self, phones: List[str]) -> Dict[str, int]:
    #     """Підраховує статистику по воронці для списку телефонів.
    #
    #     Логіка: якщо лід пройшов через 3 статуси, він враховується в 3 колонках.
    #     Загальна кількість лідів = len(phones) (унікальні номери).
    #
    #     Args:
    #         phones: Список номерів телефонів
    #
    #     Returns:
    #         Словник з підрахунками по кожному статусу
    #     """
    #     stats = {}
    #     total_found_in_nethunt = 0
    #
    #     for phone in phones:
    #         # Шукаємо контакт
    #         contact = self.search_contact_in_nethunt(phone)
    #
    #         if not contact:
    #             continue  # Контакт не знайдено в NetHunt
    #
    #         total_found_in_nethunt += 1
    #         contact_id = contact.get("id")
    #
    #         # Отримуємо історію статусів
    #         statuses = self.get_contact_status_history(contact_id)
    #
    #         # Рахуємо кожен статус окремо
    #         for status in statuses:
    #             if status not in stats:
    #                 stats[status] = 0
    #             stats[status] += 1
    #
    #     logger.info(f"Found {total_found_in_nethunt} contacts in NetHunt from {len(phones)} phones")
    #     logger.info(f"Funnel stats: {stats}")
    #
    #     return stats

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

            # === MVP VERSION - ВРЕМЕННО ОТКЛЮЧЕНЫ ФУНКЦИИ ПОЛУЧЕНИЯ ЛИДОВ ===
            # Ожидаем получение прав доступа от клиента:
            # - leads_retrieval
            # - pages_manage_ads
            # - pages_read_engagement
            # После получения нового токена - раскомментировать блок ниже
            #
            # if not self.facebook_page_id:
            #     logger.warning("FACEBOOK_PAGE_ID not configured, skipping leads")
            #     phones = []
            # else:
            #     phones = self.get_campaign_leads(campaign_id, self.facebook_page_id)
            # total_leads = len(phones)
            # funnel_stats = self.calculate_funnel_stats(phones)

            # MVP: показываем только метрики РК без лидов
            total_leads = 0
            funnel_stats = {}
            logger.info("MVP MODE: leads collection disabled, waiting for new access token")

            # Обчислюємо метрики
            spend = float(insights.get("spend", 0) or 0)
            cpl = spend / total_leads if total_leads > 0 else 0  # Cost Per Lead

            # Формуємо результат (MVP - только статистика РК)
            row = {
                "Назва реклами": campaign_name,
                "Посилання на рекламну компанію": f"https://facebook.com/campaign/{campaign_id}",
                "Дата аналізу": datetime.now().strftime("%Y-%m-%d"),
                "Період аналізу запущеної компанії": f"{self.date_start} - {self.date_stop}",
                "Витрачений бюджет в $": spend,
                "Кількість показів": int(insights.get("impressions", 0) or 0),
                "Кількість кліків": int(insights.get("clicks", 0) or 0),
                "CTR (%)": insights.get("ctr", "0"),
                "CPM ($)": insights.get("cpm", "0"),
                "Охоплення": int(insights.get("reach", 0) or 0),
                # MVP: ліди тимчасово відключені
                # "Кількість лідів": total_leads,
                # "Ціна в $ за ліда": round(cpl, 2),
            }

            # MVP: воронка тимчасово відключена
            # row.update(funnel_stats)

            results.append(row)

        logger.info(f"Processed {len(results)} campaigns")
        return results
