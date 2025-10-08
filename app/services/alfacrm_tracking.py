"""
AlfaCRM Lead Tracking Service

Трекинг прогресса лидов из Meta Ads через статусы AlfaCRM.
Подсчет количества лидов на каждом этапе воронки для студентов.
"""
import os
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime
import sys

# Добавляем путь к app для импорта connectors
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from connectors.crm import alfacrm_list_students

logger = logging.getLogger(__name__)


# Маппинг lead_status_id из AlfaCRM в названия столбцов таблицы
# Получено из /v2api/lead-status endpoint (38 статусов)
ALFACRM_STATUS_MAPPING = {
    11: "Недодзвон",
    10: "Недозвон 2",
    27: "Недозвон 3",
    1: "Вст контакт невідомо",
    32: "Вст контакт зацікавлений",
    26: "Зник після контакту",
    12: "Розмовляли, чекаємо відповідь",
    6: "Чекає пробного",
    2: "Призначено пробне",
    3: "Проведено пробне",
    5: "Не відвідав пробне",
    9: "Чекаємо оплату",
    4: "Отримана оплата",                   # Продажа (основная воронка)
    29: "Сплатить через 2 тижні >",
    25: "Передзвонити через 2 тижні",
    30: "Передзвон через місяць",
    31: "Передзвон 2 місяці і більше",
    8: "Опрацювати заперечення",
    13: "Не розібраний",                    # Новые необработанные лиды
    50: "Старі клієнти",
    # Дубликаты для второй воронки
    18: "Недозвон",
    40: "Недозвон 2",
    42: "недозвон 3",
    43: "Встан коннт невідомо",
    22: "Встан контакт зацікавлений",
    44: "Зник після контакту",
    24: "Розмовляли чекаємо відповіді",
    34: "Чекає пробного",
    35: "Призначено пробне",
    37: "Проведено пробне",
    36: "Не відвідав пробне",
    38: "Чекає оплату",
    39: "Отримана оплата",                  # Продажа (вторая воронка)
    45: "Сплатить через 2 тижні",
    46: "Передзвонити через 2 тижні",
    47: "Передз через місяць",
    48: "Передзвон 2 місяці і більше",
    49: "Опрацювати заперечення",
}


def normalize_contact(contact: Optional[str]) -> Optional[str]:
    """
    Нормализовать контакт (телефон или email) для поиска.

    Args:
        contact: Телефон или email

    Returns:
        Нормализованный контакт
    """
    if not contact:
        return None

    contact = str(contact).strip()

    # Если это email
    if "@" in contact:
        return contact.lower()

    # Если это телефон - убираем все кроме цифр
    return ''.join(c for c in contact if c.isdigit())


def extract_lead_contacts(lead: Dict[str, Any]) -> tuple[Optional[str], Optional[str]]:
    """
    Извлечь телефон и email из field_data лида.

    Args:
        lead: Лид из Meta API с field_data

    Returns:
        (phone, email) tuple
    """
    field_data = lead.get("field_data", [])
    phone = None
    email = None

    for field in field_data:
        field_name = field.get("name", "").lower()
        values = field.get("values", [])
        value = values[0] if values else None

        if not value:
            continue

        # Поиск телефона
        if any(keyword in field_name for keyword in ["phone", "телефон", "number"]):
            phone = normalize_contact(value)

        # Поиск email
        elif any(keyword in field_name for keyword in ["email", "e-mail", "адрес", "почта"]):
            email = normalize_contact(value)

    return phone, email


def build_student_index(students: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """
    Создать индекс студентов по телефону и email для быстрого поиска.

    Args:
        students: Список студентов из AlfaCRM

    Returns:
        Словарь {normalized_contact: student_data}
    """
    index = {}

    for student in students:
        # Индексируем по телефонам (массив)
        phones = student.get("phone", [])
        if isinstance(phones, str):
            phones = [phones]

        for phone in phones:
            normalized = normalize_contact(phone)
            if normalized:
                index[normalized] = student

        # Индексируем по email (массив)
        emails = student.get("email", [])
        if isinstance(emails, str):
            emails = [emails]

        for email in emails:
            normalized = normalize_contact(email)
            if normalized:
                index[normalized] = student

        # Также индексируем по custom_email если есть
        custom_email = student.get("custom_email")
        if custom_email:
            normalized = normalize_contact(custom_email)
            if normalized:
                index[normalized] = student

    return index


def track_campaign_leads(
    campaign_leads: List[Dict[str, Any]],
    student_index: Dict[str, Dict[str, Any]]
) -> Dict[str, int]:
    """
    Подсчитать количество лидов кампании на каждом этапе воронки.

    Args:
        campaign_leads: Список лидов одной кампании из Meta API
        student_index: Индекс студентов {normalized_contact: student}

    Returns:
        {
            "Кількість лідів": 150,
            "Не розібрані": 20,
            "Встанов. контакт (ЦА)": 80,
            "В опрацюванні (ЦА)": 30,
            "Назначений пробний": 40,
            "Проведений пробний": 35,
            "Купили (ЦА)": 25,
            ...
        }
    """
    # Инициализируем счетчики
    status_counts = {status_name: 0 for status_name in ALFACRM_STATUS_MAPPING.values()}
    status_counts["Кількість лідів"] = len(campaign_leads)

    matched_count = 0
    not_found_count = 0

    for lead in campaign_leads:
        # Извлекаем контакты лида
        phone, email = extract_lead_contacts(lead)

        # Ищем студента в индексе
        student = None
        if phone and phone in student_index:
            student = student_index[phone]
        elif email and email in student_index:
            student = student_index[email]

        if student:
            matched_count += 1

            # Получаем текущий статус студента
            lead_status_id = student.get("lead_status_id")

            if lead_status_id in ALFACRM_STATUS_MAPPING:
                status_name = ALFACRM_STATUS_MAPPING[lead_status_id]
                status_counts[status_name] += 1

            # ВАЖНО: Если лид прошел несколько статусов, нужно +1 в каждом
            # Для этого нужна история статусов, которой пока нет в AlfaCRM API
            # Пока считаем только текущий статус

        else:
            not_found_count += 1
            # Лиды которые не найдены в CRM считаем как "Не розібраний"
            status_counts["Не розібраний"] += 1

    logger.info(
        f"Campaign tracking: {matched_count} matched, {not_found_count} not found in CRM"
    )

    return status_counts


async def track_leads_by_campaigns(
    campaigns_data: Dict[str, Dict[str, Any]],
    page_size: int = 500
) -> Dict[str, Dict[str, Any]]:
    """
    Обогатить данные кампаний статистикой по воронке из AlfaCRM.

    Args:
        campaigns_data: Данные от get_leads_for_period() из meta_leads.py
            {
                "campaign_123": {
                    "campaign_id": "123",
                    "campaign_name": "Student/...",
                    "leads": [...]
                }
            }
        page_size: Размер страницы для загрузки студентов

    Returns:
        {
            "campaign_123": {
                "campaign_id": "123",
                "campaign_name": "Student/...",
                "leads_count": 150,
                "funnel_stats": {
                    "Кількість лідів": 150,
                    "Не розібрані": 20,
                    "Встанов. контакт (ЦА)": 80,
                    ...
                }
            }
        }
    """
    # 1. Загрузить всех студентов из AlfaCRM
    logger.info("Loading students from AlfaCRM...")

    all_students = []
    page = 1

    while True:
        try:
            response = alfacrm_list_students(page=page, page_size=page_size)
            students = response.get("items", [])

            if not students:
                break

            all_students.extend(students)

            # Проверяем есть ли еще страницы
            total = response.get("total", 0)
            if len(all_students) >= total:
                break

            page += 1

        except Exception as e:
            logger.error(f"Failed to load students page {page}: {e}")
            break

    logger.info(f"Loaded {len(all_students)} students from AlfaCRM")

    # 2. Построить индекс студентов
    student_index = build_student_index(all_students)
    logger.info(f"Built student index with {len(student_index)} contact entries")

    # 3. Обработать каждую кампанию
    enriched_campaigns = {}

    for campaign_id, campaign_data in campaigns_data.items():
        campaign_leads = campaign_data.get("leads", [])

        # Подсчитать статусы для этой кампании
        funnel_stats = track_campaign_leads(campaign_leads, student_index)

        enriched_campaigns[campaign_id] = {
            "campaign_id": campaign_data.get("campaign_id"),
            "campaign_name": campaign_data.get("campaign_name"),
            "leads_count": len(campaign_leads),
            "funnel_stats": funnel_stats
        }

    logger.info(f"Enriched {len(enriched_campaigns)} campaigns with AlfaCRM funnel stats")

    return enriched_campaigns


# Дополнительные утилиты для вычисляемых полей

def calculate_conversion_rate(funnel_stats: Dict[str, int]) -> float:
    """
    Вычислить процент конверсии в продажу.

    Returns:
        Процент конверсии (0-100)
    """
    total = funnel_stats.get("Кількість лідів", 0)

    # Продажи - "Отримана оплата" (ID 4 и 39 - обе воронки)
    converted = funnel_stats.get("Отримана оплата", 0)

    if total == 0:
        return 0.0

    return round((converted / total) * 100, 2)


def calculate_target_leads_percentage(funnel_stats: Dict[str, int]) -> float:
    """
    Вычислить процент целевых лидов (те кто прошел дальше первого контакта).

    Returns:
        Процент целевых лидов (0-100)
    """
    total = funnel_stats.get("Кількість лідів", 0)

    # Целевые = все кроме "Не розібраний" и всех вариантов недозвона
    not_processed = funnel_stats.get("Не розібраний", 0)
    no_answer = (
        funnel_stats.get("Недодзвон", 0) +
        funnel_stats.get("Недозвон 2", 0) +
        funnel_stats.get("Недозвон 3", 0) +
        funnel_stats.get("Недозвон", 0) +
        funnel_stats.get("недозвон 3", 0)
    )

    target = total - not_processed - no_answer

    if total == 0:
        return 0.0

    return round((target / total) * 100, 2)


def calculate_trial_conversion(funnel_stats: Dict[str, int]) -> float:
    """
    Вычислить конверсию из проведенного пробного в продажу.

    Returns:
        Процент конверсии (0-100)
    """
    # "Проведено пробне" (ID 3 и 37 - обе воронки)
    trial_completed = funnel_stats.get("Проведено пробне", 0)

    # Продажи - "Отримана оплата" (ID 4 и 39 - обе воронки)
    converted = funnel_stats.get("Отримана оплата", 0)

    if trial_completed == 0:
        return 0.0

    return round((converted / trial_completed) * 100, 2)
