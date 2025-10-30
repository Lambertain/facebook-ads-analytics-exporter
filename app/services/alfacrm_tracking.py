"""
AlfaCRM Lead Tracking Service

Трекинг прогресса лидов из Meta Ads через статусы AlfaCRM.
Подсчет количества лидов на каждом этапе воронки для студентов.

ПОДХОД: Current-Status-Only - каждый лид учитывается ТОЛЬКО в текущем статусе.
Это исключает дублирование лидов в нескольких колонках статусов.
Гарантирует что сума лидов по статусам = общее количество лидов.
"""
import os
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime
import sys

# Добавляем путь к app для импорта connectors
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from connectors.crm import alfacrm_list_students, alfacrm_list_all_leads

logger = logging.getLogger(__name__)


# Маппинг lead_status_id из AlfaCRM в названия столбцов таблицы
# Получено из /v2api/lead-status endpoint (38 статусов)
# НОВА АРХІТЕКТУРА: Агрегація статусів + hybrid counting
# Маппінг AlfaCRM status_id → агрегована група
ALFACRM_STATUS_TO_GROUP = {
    # Недозвон (не ЦА) - об'єднання всіх варіантів недозвону
    11: "Недозвон (не ЦА)",
    10: "Недозвон (не ЦА)",
    27: "Недозвон (не ЦА)",
    18: "Недозвон (не ЦА)",
    40: "Недозвон (не ЦА)",
    42: "Недозвон (не ЦА)",

    # Не розібраний
    13: "Не розібраний",

    # Вст контакт невідомо
    1: "Вст контакт невідомо",

    # Встановлено контакт (ЦА)
    32: "Встановлено контакт (ЦА)",
    43: "Встановлено контакт (ЦА)",
    22: "Встановлено контакт (ЦА)",

    # В ОПРАЦЮВАННІ (ЦА) (агрегована група)
    12: "В опрацюванні (ЦА)",  # Розмовляли, чекаємо відповідь
    6: "В опрацюванні (ЦА)",   # Чекає пробного
    24: "В опрацюванні (ЦА)",  # Розмовляли чекаємо відповіді (втор.)
    34: "В опрацюванні (ЦА)",  # Чекає пробного (втор.)
    5: "В опрацюванні (ЦА)",   # Не відвідав пробне
    36: "В опрацюванні (ЦА)",  # Не відвідав пробне (втор.)
    8: "В опрацюванні (ЦА)",   # Опрацювати заперечення
    49: "В опрацюванні (ЦА)",  # Опрацювати заперечення (втор.)

    # Trial funnel (cumulative counting)
    2: "Призначено пробне (ЦА)",
    35: "Призначено пробне (ЦА)",
    3: "Проведено пробне (ЦА)",
    37: "Проведено пробне (ЦА)",
    9: "Чекає оплату",
    38: "Чекає оплату",

    # Продаж (фінальна конверсія)
    4: "Отримана оплата (ЦА)",
    39: "Отримана оплата (ЦА)",

    # Відкладені (передзвонити пізніше)
    29: "Передзвонити пізніше",
    25: "Передзвонити пізніше",
    30: "Передзвонити пізніше",
    31: "Передзвонити пізніше",
    45: "Передзвонити пізніше",
    46: "Передзвонити пізніше",
    47: "Передзвонити пізніше",
    48: "Передзвонити пізніше",

    # Старі клієнти
    50: "Старі клієнти",
}

# Список всіх агрегованих статусів (замість 38 → 12 колонок)
AGGREGATED_STATUSES = [
    "Не розібраний",
    "Вст контакт невідомо",         # Новий статус - встановлено контакт, але невідомо чи ЦА
    "Недозвон (не ЦА)",
    "Встановлено контакт (ЦА)",
    "В опрацюванні (ЦА)",
    "Призначено пробне (ЦА)",      # Cumulative: всі хто >= цього етапу
    "Проведено пробне (ЦА)",        # Cumulative: всі хто >= цього етапу
    "Чекає оплату",            # Cumulative: всі хто >= цього етапу
    "Отримана оплата (ЦА)",         # Тільки фактичні продажі
    "Передзвонити пізніше",
    "Старі клієнти",
]

# Для cumulative counting: визначити ієрархію trial funnel
TRIAL_FUNNEL_HIERARCHY = {
    "Призначено пробне (ЦА)": 1,
    "Проведено пробне (ЦА)": 2,
    "Чекає оплату": 3,
    "Отримана оплата (ЦА)": 4,
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

    # ВАЖНО: Обрабатываем ошибочный формат +0380... (13 цифр)
    # Пример: +0380683957264 -> 0380683957264 -> 380683957264
    if digits.startswith('0380') and len(digits) == 13:
        return digits[1:13]  # Убираем первый 0, берем 380 + 9 цифр

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
    # НОВАЯ АРХИТЕКТУРА: Инициализируем счетчики для агрегированных статусов
    status_counts = {status_name: 0 for status_name in AGGREGATED_STATUSES}
    status_counts["Кількість лідів"] = len(campaign_leads)

    matched_count = 0
    not_found_count = 0
    archived_count = 0  # Лиды с custom_ads_comp == 'архів'

    # Для cumulative counting: сохраняем всех лидов по trial funnel уровням
    trial_funnel_levels = {level: [] for level in TRIAL_FUNNEL_HIERARCHY.keys()}

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

            # ПРОВЕРКА НА АРХИВ: Сначала проверяем custom_ads_comp
            custom_ads_comp = student.get("custom_ads_comp", "")
            if custom_ads_comp == "архів":
                archived_count += 1
                # ВИМОГА КОРИСТУВАЧА (2025-10-22): архівні ліди вважаються ЦА
                # Додаємо їх до "Призначено пробне (ЦА)" для cumulative counting
                trial_funnel_levels["Призначено пробне (ЦА)"].append(student)
                continue  # Пропускаем normal status counting для archived leads

            # Получаем текущий статус студента
            lead_status_id = student.get("lead_status_id")

            if lead_status_id:
                # НОВАЯ АРХИТЕКТУРА 2025-10-22: Агрегация + hybrid counting
                # 1. Маппим status_id -> агрегированная группа
                aggregated_group = ALFACRM_STATUS_TO_GROUP.get(lead_status_id)

                if aggregated_group:
                    # 2. Проверяем - это trial funnel статус или нет
                    if aggregated_group in TRIAL_FUNNEL_HIERARCHY:
                        # Trial funnel: сохраняем для cumulative counting
                        trial_funnel_levels[aggregated_group].append(student)
                        # ДОДАНО 2025-10-23: trial funnel статуси ТАКОЖ рахуються в "В опрацюванні (ЦА)"
                        # Подвійна логіка: вони попадають І в trial funnel cumulative І в "В опрацюванні"
                        if "В опрацюванні (ЦА)" in status_counts:
                            status_counts["В опрацюванні (ЦА)"] += 1
                    else:
                        # Не trial funnel: simple counting (current-status-only)
                        if aggregated_group in status_counts:
                            status_counts[aggregated_group] += 1

        else:
            not_found_count += 1

    # CUMULATIVE COUNTING для trial funnel - ПРАВИЛЬНАЯ ЛОГИКА 2025-10-22
    # Лид в Призначено → +1 только в Призначено
    # Лид в Проведено → +1 в Проведено И +1 в Призначено
    # Лід в Чекає → +1 в Чекає І +1 в Проведено І +1 в Призначено
    # Лід в Оплата → +1 в Оплата І +1 в Проведено І +1 в Призначено (ПРОПУСКАЄМО Чекає!)

    # Ініціалізація лічильників для trial funnel
    status_counts["Призначено пробне (ЦА)"] = 0
    status_counts["Проведено пробне (ЦА)"] = 0
    status_counts["Чекає оплату"] = 0
    status_counts["Отримана оплата (ЦА)"] = 0

    # Ліди в статусі "Призначено пробне (ЦА)"
    prizn_count = len(trial_funnel_levels["Призначено пробне (ЦА)"])
    status_counts["Призначено пробне (ЦА)"] += prizn_count

    # Ліди в статусі "Проведено пробне (ЦА)"
    prov_count = len(trial_funnel_levels["Проведено пробне (ЦА)"])
    status_counts["Проведено пробне (ЦА)"] += prov_count
    status_counts["Призначено пробне (ЦА)"] += prov_count  # +1 на попередній етап

    # Ліди в статусі "Чекає оплату"
    chek_count = len(trial_funnel_levels["Чекає оплату"])
    status_counts["Чекає оплату"] += chek_count
    status_counts["Проведено пробне (ЦА)"] += chek_count  # +1 на попередній етап
    status_counts["Призначено пробне (ЦА)"] += chek_count  # +1 на попередній етап

    # Ліди в статусі "Отримана оплата (ЦА)"
    opl_count = len(trial_funnel_levels["Отримана оплата (ЦА)"])
    status_counts["Отримана оплата (ЦА)"] += opl_count
    # ПРОПУСКАЄМО "Чекає оплату"! (як вказав користувач)
    status_counts["Проведено пробне (ЦА)"] += opl_count  # +1 на попередній етап
    status_counts["Призначено пробне (ЦА)"] += opl_count  # +1 на попередній етап

    # ЛОГИКА Archive статусов (2025-10-22):
    # Всі архівні ліди (custom_ads_comp == 'архів') вважаються ЦА
    # Вони додаються до "Призначено пробне (ЦА)" (рядок 328) та враховуються окремо
    status_counts["Архів (ЦА)"] = archived_count  # Всі архівні ліди за період
    # "Архів (не ЦА)" = 0 до рішення замовника про класифікацію Archive лідів
    # Можливі варіанти: 1) створити нові статуси в AlfaCRM, 2) custom field, 3) API
    status_counts["Архів (не ЦА)"] = 0  # До рішення замовника

    logger.info(
        f"Campaign tracking: {matched_count} matched, {not_found_count} not found in CRM, {archived_count} archived"
    )

    return status_counts


def get_lead_phones_by_status(
    campaign_leads: List[Dict[str, Any]],
    student_index: Dict[str, Dict[str, Any]]
) -> Dict[str, List[str]]:
    """
    Получить массивы номеров телефонов лидов, сгруппированные по статусам.

    Args:
        campaign_leads: Список лидов одной кампании из Meta API
        student_index: Индекс студентов {normalized_contact: student}

    Returns:
        {
            "leads_count": ["+380501234567", "+380631234567", ...],
            "Не розібраний": ["+380509876543", ...],
            "Встановлено контакт (ЦА)": ["+380661234567", ...],
            ...
        }
    """
    # Инициализируем массивы для каждого агрегированного статуса
    status_phones = {status_name: [] for status_name in AGGREGATED_STATUSES}
    all_lead_phones = []

    # Для cumulative counting: сохраняем всех лидов по trial funnel уровням
    trial_funnel_phones = {level: [] for level in TRIAL_FUNNEL_HIERARCHY.keys()}

    for lead in campaign_leads:
        # Извлекаем контакты лида
        phone, email = extract_lead_contacts(lead)

        # Ищем студента в индексе
        student = None
        if phone and phone in student_index:
            student = student_index[phone]
        elif email and email in student_index:
            student = student_index[email]

        # Используем телефон из лида (не из студента)
        # Форматируем для вывода: +380501234567
        display_phone = None
        if phone:
            # Добавляем + в начало если это 12-значный номер с 380
            if phone.startswith('380') and len(phone) == 12:
                display_phone = '+' + phone
            else:
                display_phone = phone

        # Добавляем в общий список всех лидов
        if display_phone:
            all_lead_phones.append(display_phone)

        if student and display_phone:
            # ПРОВЕРКА НА АРХИВ: Сначала проверяем custom_ads_comp
            custom_ads_comp = student.get("custom_ads_comp", "")
            if custom_ads_comp == "архів":
                # Архивные лиды добавляются в "Призначено пробне (ЦА)" для cumulative
                trial_funnel_phones["Призначено пробне (ЦА)"].append(display_phone)
                continue

            # Получаем текущий статус студента
            lead_status_id = student.get("lead_status_id")

            if lead_status_id:
                # Маппим status_id -> агрегированная группа
                aggregated_group = ALFACRM_STATUS_TO_GROUP.get(lead_status_id)

                if aggregated_group:
                    # Проверяем - это trial funnel статус или нет
                    if aggregated_group in TRIAL_FUNNEL_HIERARCHY:
                        # Trial funnel: сохраняем для cumulative counting
                        trial_funnel_phones[aggregated_group].append(display_phone)
                        # ТАКОЖ додаємо в "В опрацюванні (ЦА)" (подвійна логіка)
                        if "В опрацюванні (ЦА)" in status_phones:
                            status_phones["В опрацюванні (ЦА)"].append(display_phone)
                    else:
                        # Не trial funnel: simple counting (current-status-only)
                        if aggregated_group in status_phones:
                            status_phones[aggregated_group].append(display_phone)

    # CUMULATIVE COUNTING для trial funnel - аналогично track_campaign_leads
    # Инициализация
    status_phones["Призначено пробне (ЦА)"] = []
    status_phones["Проведено пробне (ЦА)"] = []
    status_phones["Чекає оплату"] = []
    status_phones["Отримана оплата (ЦА)"] = []

    # Ліди в статусі "Призначено пробне (ЦА)"
    prizn_phones = trial_funnel_phones["Призначено пробне (ЦА)"]
    status_phones["Призначено пробне (ЦА)"].extend(prizn_phones)

    # Ліди в статусі "Проведено пробне (ЦА)"
    prov_phones = trial_funnel_phones["Проведено пробне (ЦА)"]
    status_phones["Проведено пробне (ЦА)"].extend(prov_phones)
    status_phones["Призначено пробне (ЦА)"].extend(prov_phones)  # +1 на попередній етап

    # Ліди в статусі "Чекає оплату"
    chek_phones = trial_funnel_phones["Чекає оплату"]
    status_phones["Чекає оплату"].extend(chek_phones)
    status_phones["Проведено пробне (ЦА)"].extend(chek_phones)  # +1 на попередній етап
    status_phones["Призначено пробне (ЦА)"].extend(chek_phones)  # +1 на попередній етап

    # Ліди в статусі "Отримана оплата (ЦА)"
    opl_phones = trial_funnel_phones["Отримана оплата (ЦА)"]
    status_phones["Отримана оплата (ЦА)"].extend(opl_phones)
    # ПРОПУСКАЄМО "Чекає оплату"!
    status_phones["Проведено пробне (ЦА)"].extend(opl_phones)  # +1 на попередній етап
    status_phones["Призначено пробне (ЦА)"].extend(opl_phones)  # +1 на попередній етап

    # Добавляем все телефоны лидов в ключ "leads_count"
    result = {"leads_count": all_lead_phones}
    result.update(status_phones)

    return result


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
            response = alfacrm_list_all_leads(page=page, page_size=page_size)
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

        # НОВОЕ 2025-10-24: Получить массивы телефонов вместо счетчиков
        phone_arrays = get_lead_phones_by_status(campaign_leads, filtered_index)

        enriched_campaigns[campaign_id] = {
            "campaign_id": campaign_data.get("campaign_id"),
            "campaign_name": campaign_data.get("campaign_name"),
            "budget": campaign_data.get("budget"),  # ИСПРАВЛЕНО 2025-10-21: Добавлено поле budget из Facebook
            "location": campaign_data.get("location"),  # ИСПРАВЛЕНО 2025-10-21: Добавлено поле location из Facebook
            "leads_count": len(campaign_leads),
            "funnel_stats": funnel_stats,
            "phone_arrays": phone_arrays  # НОВОЕ 2025-10-24: Массивы телефонов по статусам
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
