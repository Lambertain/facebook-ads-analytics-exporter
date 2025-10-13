"""
AlfaCRM Lead Tracking Service

Трекинг прогресса лидов из Meta Ads через статусы AlfaCRM.
Подсчет количества лидов на каждом этапе воронки для студентов.

ПОДХОД: Inference - восстановление пути из текущего статуса.
Использует lead_journey_recovery.py для определения всех статусов через которые прошел лид.
"""
import os
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime
import sys

# Добавляем путь к app для импорта connectors
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from connectors.crm import alfacrm_list_students
from services.lead_journey_recovery import recover_lead_journey, ALFACRM_STATUS_NAMES

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

    Для телефонов использует умную нормализацию:
    - Убирает все кроме цифр
    - Приводит украинские номера к единому формату с кодом страны 380
    - Возвращает последние 12 цифр (380 + 9 цифр номера)

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
    digits = ''.join(c for c in contact if c.isdigit())

    if not digits:
        return None

    # Умная нормализация украинских номеров
    # Варианты: 380501234567, 0501234567, 501234567

    # Если номер начинается с 380 (код Украины)
    if digits.startswith('380'):
        # Берем 380 + 9 цифр (стандартный формат)
        if len(digits) >= 12:
            return digits[:12]  # 380501234567
        return digits

    # Если номер начинается с 0 (местный формат)
    elif digits.startswith('0') and len(digits) == 10:
        # Конвертируем 0501234567 → 380501234567
        return '380' + digits[1:]

    # Если номер без кода страны и без 0 (9 цифр)
    elif len(digits) == 9:
        # Конвертируем 501234567 → 380501234567
        return '380' + digits

    # Если длина нестандартная - возвращаем как есть
    return digits


def extract_lead_contacts(lead: Dict[str, Any], debug: bool = False) -> tuple[Optional[str], Optional[str]]:
    """
    Извлечь телефон и email из field_data лида.

    Args:
        lead: Лид из Meta API с field_data
        debug: Включить отладочное логирование

    Returns:
        (phone, email) tuple
    """
    field_data = lead.get("field_data", [])
    phone = None
    email = None

    if debug and field_data:
        logger.info(f"[DEBUG] Lead ID: {lead.get('id')}, field_data: {field_data}")

    for field in field_data:
        field_name = field.get("name", "").lower()
        values = field.get("values", [])
        value = values[0] if values else None

        if debug:
            logger.info(f"[DEBUG] field_name: '{field_name}', value: '{value}'")

        if not value:
            continue

        # Поиск телефона
        if any(keyword in field_name for keyword in ["phone", "телефон", "number"]):
            raw_phone = value
            phone = normalize_contact(value)
            if debug:
                logger.info(f"[DEBUG] Found phone - raw: '{raw_phone}' -> normalized: '{phone}'")

        # Поиск email
        elif any(keyword in field_name for keyword in ["email", "e-mail", "адрес", "почта"]):
            raw_email = value
            email = normalize_contact(value)
            if debug:
                logger.info(f"[DEBUG] Found email - raw: '{raw_email}' -> normalized: '{email}'")

    return phone, email


def build_student_index(students: List[Dict[str, Any]], debug: bool = False) -> Dict[str, Dict[str, Any]]:
    """
    Создать индекс студентов по телефону и email для быстрого поиска.

    Args:
        students: Список студентов из AlfaCRM
        debug: Включить отладочное логирование

    Returns:
        Словарь {normalized_contact: student_data}
    """
    index = {}
    debug_samples = 0

    for student in students:
        # Индексируем по телефонам (массив)
        phones = student.get("phone", [])
        if isinstance(phones, str):
            phones = [phones]

        if debug and debug_samples < 3 and phones:
            logger.info(f"[DEBUG] Student ID: {student.get('id')}, raw phones: {phones}")

        for phone in phones:
            raw = phone
            normalized = normalize_contact(phone)
            if normalized:
                index[normalized] = student
                if debug and debug_samples < 3:
                    logger.info(f"[DEBUG] Phone - raw: '{raw}' -> normalized: '{normalized}'")

        # Индексируем по email (массив)
        emails = student.get("email", [])
        if isinstance(emails, str):
            emails = [emails]

        if debug and debug_samples < 3 and emails:
            logger.info(f"[DEBUG] Student ID: {student.get('id')}, raw emails: {emails}")

        for email in emails:
            raw = email
            normalized = normalize_contact(email)
            if normalized:
                index[normalized] = student
                if debug and debug_samples < 3:
                    logger.info(f"[DEBUG] Email - raw: '{raw}' -> normalized: '{normalized}'")

        # Также индексируем по custom_email если есть
        custom_email = student.get("custom_email")
        if custom_email:
            raw = custom_email
            normalized = normalize_contact(custom_email)
            if normalized:
                index[normalized] = student
                if debug and debug_samples < 3:
                    logger.info(f"[DEBUG] Custom email - raw: '{raw}' -> normalized: '{normalized}'")

        if debug and (phones or emails or custom_email):
            debug_samples += 1

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

            if lead_status_id:
                # INFERENCE ПОДХОД: Восстанавливаем путь лида через воронку
                # на основе текущего статуса
                journey = recover_lead_journey(lead_status_id)

                # Засчитываем лида в КАЖДОМ статусе через который он прошел
                # Это создает КУМУЛЯТИВНУЮ воронку как в NetHunt
                for status_id in journey:
                    status_name = ALFACRM_STATUS_NAMES.get(status_id)
                    if status_name and status_name in status_counts:
                        status_counts[status_name] += 1
            else:
                # Если нет lead_status_id - считаем как необработанный
                status_counts["Не розібраний"] += 1

        else:
            not_found_count += 1
            # Лиды которые не найдены в CRM считаем как "Не розібраний"
            status_counts["Не розібраний"] += 1

    logger.info(
        f"Campaign tracking: {matched_count} matched, {not_found_count} not found in CRM"
    )

    return status_counts


def extract_contacts_from_campaigns(campaigns_data: Dict[str, Dict[str, Any]], debug: bool = False) -> set:
    """
    Извлечь все уникальные контакты (телефоны и email) из лидов кампаний.

    Args:
        campaigns_data: Данные от get_leads_for_period() из meta_leads.py
        debug: Включить отладочное логирование

    Returns:
        Множество нормализованных контактов
    """
    contacts = set()
    debug_samples = 0

    for campaign_data in campaigns_data.values():
        leads = campaign_data.get("leads", [])

        for lead in leads:
            phone, email = extract_lead_contacts(lead, debug=(debug and debug_samples < 3))
            if phone:
                contacts.add(phone)
            if email:
                contacts.add(email)

            if debug and (phone or email):
                debug_samples += 1

    logger.info(f"Extracted {len(contacts)} unique contacts from {sum(len(c.get('leads', [])) for c in campaigns_data.values())} leads")

    if debug:
        sample_contacts = list(contacts)[:5]
        logger.info(f"[DEBUG] Sample extracted contacts: {sample_contacts}")

    return contacts


async def track_leads_by_campaigns(
    campaigns_data: Dict[str, Dict[str, Any]],
    page_size: int = 500
) -> Dict[str, Dict[str, Any]]:
    """
    Обогатить данные кампаний статистикой по воронке из AlfaCRM.

    ОПТИМИЗАЦИЯ: Загружает только тех студентов, которые есть в лидах кампаний за период.

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
    # ВРЕМЕННО: Включаем DEBUG режим для диагностики
    DEBUG_MODE = True

    # 1. Извлечь контакты из лидов Meta за указанный период
    lead_contacts = extract_contacts_from_campaigns(campaigns_data, debug=DEBUG_MODE)

    if not lead_contacts:
        logger.warning("No contacts found in Meta leads - skipping AlfaCRM loading")
        return {}

    # 2. Загрузить ВСЕХ студентов из AlfaCRM (требуется для сопоставления)
    # Примечание: AlfaCRM API не поддерживает фильтрацию по телефону/email
    # поэтому мы загружаем всех студентов но затем используем только релевантных
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

    # 3. Построить индекс ТОЛЬКО для студентов с контактами из лидов
    student_index = build_student_index(all_students, debug=DEBUG_MODE)

    # Фильтруем индекс - оставляем только контакты которые есть в лидах
    filtered_index = {
        contact: student for contact, student in student_index.items()
        if contact in lead_contacts
    }

    logger.info(f"Filtered student index: {len(filtered_index)} matched contacts from {len(student_index)} total")

    if DEBUG_MODE and len(filtered_index) == 0:
        # Если нет совпадений - показываем примеры для анализа
        sample_lead_contacts = list(lead_contacts)[:5]
        sample_index_contacts = list(student_index.keys())[:5]
        logger.info(f"[DEBUG] Sample lead contacts: {sample_lead_contacts}")
        logger.info(f"[DEBUG] Sample index contacts: {sample_index_contacts}")

    # 4. Обработать каждую кампанию
    enriched_campaigns = {}

    for campaign_id, campaign_data in campaigns_data.items():
        campaign_leads = campaign_data.get("leads", [])

        # Подсчитать статусы для этой кампании используя отфильтрованный индекс
        funnel_stats = track_campaign_leads(campaign_leads, filtered_index)

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
