"""
NetHunt CRM Tracking Service для вчителів.

Inference підхід (БЕЗ історії змін):
- Рахує ліди в поточному статусі на момент аналізу
- НЕ використовує API історії змін
- Аналогічно alfacrm_tracking.py для студентів

Функціонал:
1. Отримання поточних записів з NetHunt CRM
2. Нормалізація контактів (телефони, email)
3. Індексація вчителів за нормалізованими контактами
4. Обогащення кампаній з Meta Ads статистикою воронки
"""
import logging
from typing import Dict, List, Optional, Any, Set
from collections import defaultdict

from app.connectors.crm import (
    nethunt_list_records,
    nethunt_list_folders,
    nethunt_folder_fields,
)
from app.config.settings import NETHUNT_STATUS_MAPPING

logger = logging.getLogger(__name__)


# ============================================================================
# НОРМАЛІЗАЦІЯ КОНТАКТІВ
# ============================================================================


def normalize_contact(contact: Optional[str]) -> Optional[str]:
    """
    Нормалізує контакт (телефон або email) для однозначного зіставлення.

    Логіка нормалізації телефонів (українські номери):
    - 0380XXXXXXXXX (13 цифр) → 380XXXXXXXXX (12 цифр)
    - 380XXXXXXXXX → 380XXXXXXXXX (без змін)
    - 0XXXXXXXXX (10 цифр) → 380XXXXXXXXX (12 цифр)
    - XXXXXXXXX (9 цифр) → 380XXXXXXXXX (12 цифр)

    Email: приводиться до lowercase.

    Args:
        contact: Телефон або email для нормалізації

    Returns:
        Нормалізований контакт або None якщо не вдалося нормалізувати

    Examples:
        >>> normalize_contact("0380501234567")  # 13 цифр
        "380501234567"
        >>> normalize_contact("380501234567")
        "380501234567"
        >>> normalize_contact("0501234567")  # 10 цифр
        "380501234567"
        >>> normalize_contact("501234567")  # 9 цифр
        "380501234567"
        >>> normalize_contact("user@example.com")
        "user@example.com"
    """
    if not contact:
        return None

    contact = contact.strip()

    if not contact:
        return None

    # Email: приводимо до lowercase
    if "@" in contact:
        return contact.lower()

    # Телефон: залишаємо тільки цифри
    digits = ''.join(c for c in contact if c.isdigit())

    if not digits:
        logger.warning(f"Не вдалося нормалізувати контакт (немає цифр): {contact}")
        return None

    # 0380XXXXXXXXX → 380XXXXXXXXX (видаляємо перший 0)
    if digits.startswith('0380') and len(digits) == 13:
        normalized = digits[1:13]  # 380XXXXXXXXX (12 цифр)
        logger.debug(f"Нормалізовано 0380... → {normalized}")
        return normalized

    # 380XXXXXXXXX → без змін
    if digits.startswith('380') and len(digits) == 12:
        logger.debug(f"Телефон вже нормалізований: {digits}")
        return digits

    # 0XXXXXXXXX → 380XXXXXXXXX
    if digits.startswith('0') and len(digits) == 10:
        normalized = '380' + digits[1:]  # 380XXXXXXXXX (12 цифр)
        logger.debug(f"Нормалізовано 0... → {normalized}")
        return normalized

    # XXXXXXXXX → 380XXXXXXXXX
    if len(digits) == 9:
        normalized = '380' + digits  # 380XXXXXXXXX (12 цифр)
        logger.debug(f"Нормалізовано без коду → {normalized}")
        return normalized

    # Якщо не підходить під жоден формат - повертаємо як є
    logger.warning(f"Не вдалося нормалізувати телефон (незрозумілий формат): {contact} -> {digits}")
    return digits


# ============================================================================
# ІНДЕКСАЦІЯ ВЧИТЕЛІВ З NETHUNT
# ============================================================================


def build_teacher_index(
    records: List[Dict[str, Any]]
) -> Dict[str, Dict[str, Any]]:
    """
    Будує індекс вчителів за нормалізованими контактами.

    Структура індексу:
    {
        "380501234567": {
            "id": "nethunt_record_id",
            "name": "Іван Петров",
            "email": "ivan@example.com",
            "phone": "380501234567",
            "status": "interview_target",  # ключ з NetHunt API
            "status_column": "Співбесіда (ЦА)",  # назва колонки таблиці
            "created_at": "2025-10-01T10:00:00Z",
            # ... інші поля з NetHunt
        },
        "ivan@example.com": { ... }  # той же запис, але за email
    }

    ВАЖЛИВО: Якщо у вчителя є і телефон, і email - він буде в індексі
    по обох ключах (для надійного зіставлення з Meta Ads лідами).

    Args:
        records: Список записів з NetHunt API

    Returns:
        Словник {нормалізований_контакт: дані_вчителя}
    """
    index: Dict[str, Dict[str, Any]] = {}

    for record in records:
        record_id = record.get("id")
        if not record_id:
            logger.warning("Запис без ID, пропускаємо")
            continue

        # Отримуємо статус з NetHunt
        status_key = record.get("status", "").lower().replace(" ", "_").replace("-", "_")
        status_column = NETHUNT_STATUS_MAPPING.get(status_key, "Не розібрані ліди")

        teacher_data = {
            "id": record_id,
            "name": record.get("name", ""),
            "email": record.get("email", ""),
            "phone": record.get("phone", ""),
            "status": status_key,
            "status_column": status_column,
            "created_at": record.get("created_at"),
            "updated_at": record.get("updated_at"),
            # Зберігаємо весь запис для можливих додаткових полів
            "_raw": record,
        }

        # Індексуємо по телефону
        phone = record.get("phone")
        if phone:
            normalized_phone = normalize_contact(phone)
            if normalized_phone:
                index[normalized_phone] = teacher_data
                logger.debug(f"Індексовано вчителя по телефону: {normalized_phone} -> {teacher_data['name']}")

        # Індексуємо по email
        email = record.get("email")
        if email:
            normalized_email = normalize_contact(email)
            if normalized_email:
                index[normalized_email] = teacher_data
                logger.debug(f"Індексовано вчителя по email: {normalized_email} -> {teacher_data['name']}")

    logger.info(f"Побудовано індекс вчителів: {len(index)} унікальних контактів з {len(records)} записів")
    return index


# ============================================================================
# ВІДСТЕЖЕННЯ ЛІДІВ ПО КАМПАНІЯХ
# ============================================================================


def extract_contacts_from_campaigns(
    campaigns_data: Dict[str, Dict[str, Any]]
) -> Set[str]:
    """
    Витягує всі унікальні нормалізовані контакти з лідів кампаній Meta Ads.

    Args:
        campaigns_data: Дані кампаній з Meta Ads
        {
            "campaign_id_1": {
                "name": "Campaign Name",
                "leads": [
                    {"phone": "0501234567", "email": "user@example.com"},
                    ...
                ]
            }
        }

    Returns:
        Set нормалізованих контактів (телефони та email)
    """
    contacts: Set[str] = set()

    for campaign_id, campaign_data in campaigns_data.items():
        leads = campaign_data.get("leads", [])

        for lead in leads:
            # Витягуємо телефон
            phone = lead.get("phone") or lead.get("full_phone_number")
            if phone:
                normalized_phone = normalize_contact(phone)
                if normalized_phone:
                    contacts.add(normalized_phone)

            # Витягуємо email
            email = lead.get("email")
            if email:
                normalized_email = normalize_contact(email)
                if normalized_email:
                    contacts.add(normalized_email)

    logger.info(f"Витягнуто {len(contacts)} унікальних контактів з {len(campaigns_data)} кампаній")
    return contacts


def track_campaign_leads(
    campaign_leads: List[Dict[str, Any]],
    teacher_index: Dict[str, Dict[str, Any]],
    all_status_columns: Set[str]
) -> Dict[str, Any]:
    """
    Відстежує ліди однієї кампанії в NetHunt CRM.

    Inference підхід: рахує ліди в поточному статусі на момент аналізу.

    Args:
        campaign_leads: Ліди кампанії з Meta Ads
        teacher_index: Індекс вчителів за контактами
        all_status_columns: Всі можливі колонки статусів

    Returns:
        {
            "status_counts": {"Контакт (ЦА)": 5, "Співбесіда (ЦА)": 2, ...},
            "total_matched": 10,
            "total_leads": 15
        }
    """
    # Ініціалізуємо лічильники для всіх статусів
    status_counts: Dict[str, int] = {status: 0 for status in all_status_columns}

    total_matched = 0

    for lead in campaign_leads:
        # Витягуємо контакти ліда
        phone = lead.get("phone") or lead.get("full_phone_number")
        email = lead.get("email")

        # Шукаємо вчителя в індексі
        teacher = None

        if phone:
            normalized_phone = normalize_contact(phone)
            if normalized_phone and normalized_phone in teacher_index:
                teacher = teacher_index[normalized_phone]
                logger.debug(f"Знайдено вчителя по телефону: {normalized_phone}")

        if not teacher and email:
            normalized_email = normalize_contact(email)
            if normalized_email and normalized_email in teacher_index:
                teacher = teacher_index[normalized_email]
                logger.debug(f"Знайдено вчителя по email: {normalized_email}")

        # Якщо знайшли вчителя - рахуємо його статус
        if teacher:
            total_matched += 1
            status_column = teacher.get("status_column", "Не розібрані ліди")
            status_counts[status_column] += 1
            logger.debug(f"Лід зіставлено: {phone or email} -> статус '{status_column}'")

    result = {
        "status_counts": status_counts,
        "total_matched": total_matched,
        "total_leads": len(campaign_leads),
    }

    logger.info(
        f"Відстежено кампанію: {total_matched}/{len(campaign_leads)} лідів зіставлено, "
        f"розподіл по статусах: {sum(1 for c in status_counts.values() if c > 0)} активних статусів"
    )

    return result


async def track_leads_by_campaigns(
    campaigns_data: Dict[str, Dict[str, Any]],
    folder_id: Optional[str] = None
) -> Dict[str, Dict[str, Any]]:
    """
    Обогащує дані кампаній Meta Ads статистикою воронки вчителів з NetHunt CRM.

    Inference підхід (БЕЗ історії змін):
    - Завантажує поточні записи з NetHunt
    - Рахує ліди в поточному статусі
    - Зіставляє з лідами Meta Ads за контактами

    Args:
        campaigns_data: Дані кампаній з Meta Ads
        folder_id: ID папки NetHunt (за замовчуванням з env)

    Returns:
        Збагачені дані кампаній з додатковими полями:
        {
            "campaign_id": {
                ...оригінальні дані...,
                "funnel_stats": {
                    "Не розібрані ліди": 3,
                    "Контакт (ЦА)": 5,
                    "Співбесіда (ЦА)": 2,
                    "Вчитель ЦА": 1,
                    ...
                },
                "total_matched_leads": 10,
                "match_rate": 0.67  # 10/15 лідів знайдено в NetHunt
            }
        }
    """
    logger.info(f"Початок обогащення {len(campaigns_data)} кампаній даними з NetHunt")

    # 1. Витягуємо всі унікальні контакти з лідів кампаній
    lead_contacts = extract_contacts_from_campaigns(campaigns_data)
    logger.info(f"Витягнуто {len(lead_contacts)} унікальних контактів з Meta Ads лідів")

    if not lead_contacts:
        logger.warning("Немає контактів для зіставлення з NetHunt")
        return campaigns_data

    # 2. Завантажуємо всі записи вчителів з NetHunt (поточний стан)
    try:
        all_records = nethunt_list_records(folder_id=folder_id, limit=10000)
        logger.info(f"Завантажено {len(all_records)} записів з NetHunt")
    except Exception as e:
        logger.error(f"Помилка завантаження записів з NetHunt: {e}")
        return campaigns_data

    if not all_records:
        logger.warning("NetHunt не повернув записів вчителів")
        return campaigns_data

    # 3. Будуємо індекс вчителів за нормалізованими контактами
    teacher_index = build_teacher_index(all_records)
    logger.info(f"Побудовано індекс: {len(teacher_index)} унікальних контактів")

    # Фільтруємо індекс: залишаємо тільки тих вчителів, які є в Meta Ads лідах
    filtered_index = {
        contact: teacher
        for contact, teacher in teacher_index.items()
        if contact in lead_contacts
    }
    logger.info(
        f"Відфільтровано індекс: {len(filtered_index)}/{len(teacher_index)} вчителів "
        f"знайдено в Meta Ads лідах"
    )

    if not filtered_index:
        logger.warning("Жоден вчитель з NetHunt не знайдений серед Meta Ads лідів")
        return campaigns_data

    # 4. Збираємо всі унікальні колонки статусів
    all_status_columns: Set[str] = set(NETHUNT_STATUS_MAPPING.values())
    logger.info(f"Відстежуємо {len(all_status_columns)} статусних колонок")

    # 5. Обробляємо кожну кампанію
    enriched_campaigns = {}

    for campaign_id, campaign_data in campaigns_data.items():
        campaign_leads = campaign_data.get("leads", [])

        if not campaign_leads:
            logger.debug(f"Кампанія {campaign_id} не має лідів, пропускаємо")
            enriched_campaigns[campaign_id] = campaign_data
            continue

        # Відстежуємо ліди кампанії в NetHunt
        funnel_stats = track_campaign_leads(
            campaign_leads,
            filtered_index,
            all_status_columns
        )

        # Додаємо статистику воронки до кампанії
        enriched_campaign = campaign_data.copy()
        enriched_campaign["funnel_stats"] = funnel_stats["status_counts"]
        enriched_campaign["total_matched_leads"] = funnel_stats["total_matched"]
        enriched_campaign["match_rate"] = (
            funnel_stats["total_matched"] / funnel_stats["total_leads"]
            if funnel_stats["total_leads"] > 0 else 0.0
        )

        enriched_campaigns[campaign_id] = enriched_campaign

        logger.info(
            f"Кампанія {campaign_id}: {funnel_stats['total_matched']}/{funnel_stats['total_leads']} "
            f"лідів зіставлено ({enriched_campaign['match_rate']:.1%})"
        )

    logger.info(f"Обогащення завершено: оброблено {len(enriched_campaigns)} кампаній")
    return enriched_campaigns


# ============================================================================
# ДОПОМІЖНІ ФУНКЦІЇ
# ============================================================================


async def get_nethunt_folders() -> List[Dict[str, Any]]:
    """
    Отримує список папок NetHunt.

    Returns:
        Список папок з NetHunt CRM
    """
    try:
        folders = nethunt_list_folders()
        logger.info(f"Отримано {len(folders)} папок з NetHunt")
        return folders
    except Exception as e:
        logger.error(f"Помилка отримання папок NetHunt: {e}")
        return []


async def get_nethunt_folder_fields(folder_id: str) -> Dict[str, Any]:
    """
    Отримує схему полів папки NetHunt.

    Args:
        folder_id: ID папки NetHunt

    Returns:
        Схема полів папки
    """
    try:
        fields = nethunt_folder_fields(folder_id)
        logger.info(f"Отримано схему полів для папки {folder_id}")
        return fields
    except Exception as e:
        logger.error(f"Помилка отримання схеми полів NetHunt: {e}")
        return {}
