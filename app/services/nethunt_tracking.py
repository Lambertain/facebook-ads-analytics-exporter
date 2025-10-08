"""
NetHunt Lead Tracking Service

Трекинг прогресса лидов из Meta Ads через статусы NetHunt CRM.
Подсчет количества лидов на каждом этапе воронки для учителей.
"""
import os
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime
import sys

# Добавляем путь к app для импорта connectors
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from connectors.crm import nethunt_list_folders, nethunt_list_records

logger = logging.getLogger(__name__)


# Маппинг статусов NetHunt в названия столбцов таблицы
# ВАЖНО: Эти статусы нужно уточнить у клиента после получения реальных данных
NETHUNT_STATUS_MAPPING = {
    "new": "Нові",
    "contacted": "Контакт встановлено",
    "qualified": "Кваліфіковані",
    "interview_scheduled": "Співбесіда призначена",
    "interview_completed": "Співбесіда проведена",
    "offer_sent": "Офер відправлено",
    "hired": "Найнято",
    "rejected": "Відмова",
    "no_answer": "Недзвін",
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


def extract_status_from_record(record: Dict[str, Any]) -> Optional[str]:
    """
    Извлечь статус из записи NetHunt.

    NetHunt хранит статусы в разных местах:
    - record.get("status") - объект статуса
    - record.get("fields", {}).get("Status") - поле статуса

    Args:
        record: Запись из NetHunt

    Returns:
        Название статуса или None
    """
    # Попытка 1: Прямой статус
    status_obj = record.get("status", {})
    if isinstance(status_obj, dict):
        status_name = status_obj.get("name", "").lower()
        if status_name:
            return status_name

    # Попытка 2: Статус в полях
    fields = record.get("fields", {})
    for field_name, field_value in fields.items():
        if "status" in field_name.lower():
            if isinstance(field_value, dict):
                return field_value.get("name", "").lower()
            elif isinstance(field_value, str):
                return field_value.lower()

    return None


def map_nethunt_status_to_column(status_name: Optional[str]) -> str:
    """
    Преобразовать статус NetHunt в название столбца таблицы.

    Args:
        status_name: Название статуса из NetHunt (lowercase)

    Returns:
        Название столбца таблицы
    """
    if not status_name:
        return "Нові"

    # Прямое сопоставление
    if status_name in NETHUNT_STATUS_MAPPING:
        return NETHUNT_STATUS_MAPPING[status_name]

    # Поиск по частичному совпадению
    for key, value in NETHUNT_STATUS_MAPPING.items():
        if key in status_name or status_name in key:
            return value

    # Если не найдено - возвращаем как есть (заглавная буква)
    return status_name.capitalize()


def build_teacher_index(records: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """
    Создать индекс учителей (записей NetHunt) по телефону и email для быстрого поиска.

    Args:
        records: Список записей из NetHunt

    Returns:
        Словарь {normalized_contact: record}
    """
    index = {}

    for record in records:
        fields = record.get("fields", {})

        # Индексируем по всем полям, которые могут содержать контакты
        for field_name, field_value in fields.items():
            field_name_lower = field_name.lower()

            # Индексируем по телефону
            if any(keyword in field_name_lower for keyword in ["phone", "телефон", "tel", "mobile"]):
                if field_value:
                    normalized = normalize_contact(str(field_value))
                    if normalized:
                        index[normalized] = record

            # Индексируем по email
            if any(keyword in field_name_lower for keyword in ["email", "почта", "mail"]):
                if field_value:
                    normalized = normalize_contact(str(field_value))
                    if normalized:
                        index[normalized] = record

    return index


def track_campaign_leads(
    campaign_leads: List[Dict[str, Any]],
    teacher_index: Dict[str, Dict[str, Any]],
    all_status_columns: set
) -> Dict[str, int]:
    """
    Подсчитать количество лидов кампании на каждом этапе воронки.

    Args:
        campaign_leads: Список лидов одной кампании из Meta API
        teacher_index: Индекс учителей {normalized_contact: record}
        all_status_columns: Множество всех возможных названий столбцов статусов

    Returns:
        {
            "Кількість лідів": 50,
            "Нові": 10,
            "Контакт встановлено": 20,
            "Кваліфіковані": 15,
            ...
        }
    """
    # Инициализируем счетчики
    status_counts = {status_col: 0 for status_col in all_status_columns}
    status_counts["Кількість лідів"] = len(campaign_leads)

    matched_count = 0
    not_found_count = 0

    for lead in campaign_leads:
        # Извлекаем контакты лида
        phone, email = extract_lead_contacts(lead)

        # Ищем учителя в индексе
        teacher_record = None
        if phone and phone in teacher_index:
            teacher_record = teacher_index[phone]
        elif email and email in teacher_index:
            teacher_record = teacher_index[email]

        if teacher_record:
            matched_count += 1

            # Извлекаем статус учителя
            status_name = extract_status_from_record(teacher_record)

            # Преобразуем в название столбца
            column_name = map_nethunt_status_to_column(status_name)

            # Добавляем столбец если его еще нет
            if column_name not in status_counts:
                status_counts[column_name] = 0

            status_counts[column_name] += 1

        else:
            not_found_count += 1
            # Лиды которые не найдены в CRM считаем как "Нові"
            status_counts["Нові"] += 1

    logger.info(
        f"Campaign tracking: {matched_count} matched, {not_found_count} not found in NetHunt"
    )

    return status_counts


async def track_leads_by_campaigns(
    campaigns_data: Dict[str, Dict[str, Any]],
    folder_id: Optional[str] = None
) -> Dict[str, Dict[str, Any]]:
    """
    Обогатить данные кампаний статистикой по воронке из NetHunt.

    Args:
        campaigns_data: Данные от get_leads_for_period() из meta_leads.py
            {
                "campaign_123": {
                    "campaign_id": "123",
                    "campaign_name": "Teacher/...",
                    "leads": [...]
                }
            }
        folder_id: ID папки в NetHunt (если не указан - берется из env или первая доступная)

    Returns:
        {
            "campaign_123": {
                "campaign_id": "123",
                "campaign_name": "Teacher/...",
                "leads_count": 50,
                "funnel_stats": {
                    "Кількість лідів": 50,
                    "Нові": 10,
                    "Контакт встановлено": 20,
                    ...
                }
            }
        }
    """
    # 1. Определить folder_id
    if not folder_id:
        folder_id = os.getenv("NETHUNT_FOLDER_ID")

    if not folder_id or folder_id == "default":
        # Получить первую доступную папку
        try:
            folders = nethunt_list_folders()
            if folders:
                folder_id = folders[0].get("id")
                logger.info(f"Using NetHunt folder: {folders[0].get('name')} ({folder_id})")
            else:
                logger.error("No NetHunt folders found")
                return {}
        except Exception as e:
            logger.error(f"Failed to get NetHunt folders: {e}")
            return {}

    # 2. Загрузить все записи учителей из NetHunt
    logger.info(f"Loading teachers from NetHunt folder {folder_id}...")

    try:
        all_records = nethunt_list_records(folder_id, limit=1000)
        logger.info(f"Loaded {len(all_records)} teacher records from NetHunt")
    except Exception as e:
        logger.error(f"Failed to load NetHunt records: {e}")
        return {}

    # 3. Построить индекс учителей
    teacher_index = build_teacher_index(all_records)
    logger.info(f"Built teacher index with {len(teacher_index)} contact entries")

    # 4. Собрать все уникальные статусы для создания столбцов
    all_status_columns = set(NETHUNT_STATUS_MAPPING.values())

    # Добавить реальные статусы из данных
    for record in all_records:
        status_name = extract_status_from_record(record)
        if status_name:
            column_name = map_nethunt_status_to_column(status_name)
            all_status_columns.add(column_name)

    logger.info(f"Found {len(all_status_columns)} unique status columns")

    # 5. Обработать каждую кампанию
    enriched_campaigns = {}

    for campaign_id, campaign_data in campaigns_data.items():
        campaign_leads = campaign_data.get("leads", [])

        # Подсчитать статусы для этой кампании
        funnel_stats = track_campaign_leads(
            campaign_leads,
            teacher_index,
            all_status_columns
        )

        enriched_campaigns[campaign_id] = {
            "campaign_id": campaign_data.get("campaign_id"),
            "campaign_name": campaign_data.get("campaign_name"),
            "leads_count": len(campaign_leads),
            "funnel_stats": funnel_stats
        }

    logger.info(f"Enriched {len(enriched_campaigns)} campaigns with NetHunt funnel stats")

    return enriched_campaigns


# Дополнительные утилиты для вычисляемых полей

def calculate_conversion_rate(funnel_stats: Dict[str, int]) -> float:
    """
    Вычислить процент конверсии в найм.

    Returns:
        Процент конверсии (0-100)
    """
    total = funnel_stats.get("Кількість лідів", 0)
    hired = funnel_stats.get("Найнято", 0)

    if total == 0:
        return 0.0

    return round((hired / total) * 100, 2)


def calculate_qualified_percentage(funnel_stats: Dict[str, int]) -> float:
    """
    Вычислить процент квалифицированных лидов.

    Returns:
        Процент квалифицированных (0-100)
    """
    total = funnel_stats.get("Кількість лідів", 0)
    new = funnel_stats.get("Нові", 0)
    no_answer = funnel_stats.get("Недзвін", 0)

    if total == 0:
        return 0.0

    qualified = total - new - no_answer
    return round((qualified / total) * 100, 2)


def calculate_interview_conversion(funnel_stats: Dict[str, int]) -> float:
    """
    Вычислить конверсию из проведенной собеседования в найм.

    Returns:
        Процент конверсии (0-100)
    """
    interview_completed = funnel_stats.get("Співбесіда проведена", 0)
    hired = funnel_stats.get("Найнято", 0)

    if interview_completed == 0:
        return 0.0

    return round((hired / interview_completed) * 100, 2)
