"""
NetHunt Lead Tracking Service

Трекинг прогресса лидов (учителей) из Meta Ads через РЕАЛЬНУЮ историю изменений NetHunt API.
Использует endpoint /triggers/record-change/ для получения полной истории статусов.

ОТЛИЧИЕ ОТ ALFACRM:
- AlfaCRM: Inference подход (восстановление пути из текущего статуса)
- NetHunt: Real history (полная история изменений из API)

Преимущества NetHunt подхода:
- Точные временные метки изменений
- Информация о том, кто изменил статус
- История всех полей, не только статус
"""
import os
import logging
import requests
from typing import List, Dict, Optional, Any
from datetime import datetime
import sys
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log
)

# Добавляем путь к app для импорта connectors и config
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from connectors.crm import nethunt_list_folders, nethunt_list_records
from config.settings import (
    NETHUNT_BASE_URL,
    NETHUNT_AUTH,
    NETHUNT_TIMEOUT,
    NETHUNT_STATUS_MAPPING,
    NETHUNT_FOLDER_ID,
    NETHUNT_STRICT_VALIDATION
)

logger = logging.getLogger(__name__)


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


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((
        requests.exceptions.Timeout,
        requests.exceptions.ConnectionError,
        requests.exceptions.HTTPError
    )),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True
)
def _nethunt_api_call_with_retry(url: str, headers: Dict[str, str], timeout: int) -> requests.Response:
    """
    Выполнить HTTP запрос к NetHunt API с retry механизмом.

    Args:
        url: URL endpoint
        headers: HTTP заголовки
        timeout: Timeout в секундах

    Returns:
        Response объект

    Raises:
        requests.exceptions.HTTPError: При ошибках HTTP
        requests.exceptions.Timeout: При timeout
        requests.exceptions.ConnectionError: При проблемах с соединением
    """
    response = requests.get(url, headers=headers, timeout=timeout)
    response.raise_for_status()
    return response


def _validate_nethunt_changes_response(data: Any) -> bool:
    """
    Валидировать структуру ответа NetHunt API для record changes.

    Args:
        data: Данные из response.json()

    Returns:
        True если структура валидна, False иначе
    """
    # Проверка что это список
    if not isinstance(data, list):
        logger.error(f"Invalid NetHunt response: expected list, got {type(data).__name__}")
        return False

    # Проверка структуры каждого изменения
    for idx, change in enumerate(data):
        if not isinstance(change, dict):
            logger.warning(f"Change #{idx} is not a dict: {type(change).__name__}")
            continue

        # Обязательные поля
        required_fields = ["recordId", "time"]
        missing_fields = [f for f in required_fields if f not in change]

        if missing_fields:
            logger.warning(f"Change #{idx} missing required fields: {missing_fields}")

    return True


def nethunt_get_record_changes(
    folder_id: str,
    since_date: Optional[str] = None,
    limit: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Получить историю изменений записей из папки NetHunt.

    Использует endpoint /triggers/record-change/{folder_id} для получения
    полной истории всех изменений полей.

    Включает:
    - Retry механизм с exponential backoff (3 попытки)
    - Валидацию структуры API ответа
    - Детальное логирование ошибок
    - Опциональную фильтрацию по дате (для уменьшения объема данных)
    - Опциональный лимит результатов

    Args:
        folder_id: ID папки NetHunt
        since_date: Получить изменения начиная с этой даты (ISO 8601 формат)
                   Например: "2025-01-01T00:00:00Z"
        limit: Максимальное количество изменений для возврата
              (фильтрация после получения от API)

    Returns:
        Список изменений с структурой:
        [{
            "id": "...",
            "recordId": "ID записи",
            "time": "2025-10-10T12:00:00Z",
            "user": "email пользователя",
            "recordAction": "updated|created|deleted",
            "fieldActions": [
                {"field": "status", "oldValue": "new", "newValue": "contacted"}
            ]
        }]
    """
    if not NETHUNT_AUTH:
        logger.error("NETHUNT_BASIC_AUTH not configured")
        return []

    url = f"{NETHUNT_BASE_URL}/triggers/record-change/{folder_id}"
    headers = {
        "Authorization": NETHUNT_AUTH,
        "Accept": "application/json"
    }

    try:
        # Вызов API с retry механизмом
        response = _nethunt_api_call_with_retry(url, headers, NETHUNT_TIMEOUT)

        # Парсинг JSON
        try:
            changes = response.json()
        except ValueError as e:
            logger.error(f"Failed to parse NetHunt API response as JSON: {e}")
            logger.error(f"Response content (first 500 chars): {response.text[:500]}")
            return []

        # Валидация структуры ответа
        if not _validate_nethunt_changes_response(changes):
            logger.error("NetHunt API response validation failed")

            if NETHUNT_STRICT_VALIDATION:
                # Production режим: зупиняємо виконання
                logger.critical(
                    "NETHUNT_STRICT_VALIDATION=true - aborting execution due to invalid response"
                )
                return []
            else:
                # Development режим: продовжуємо з попередженням
                logger.warning(
                    "Continuing with potentially invalid data (NETHUNT_STRICT_VALIDATION=false). "
                    "Set NETHUNT_STRICT_VALIDATION=true for production."
                )

        # Фильтрация по дате (если указана)
        if since_date:
            original_count = len(changes)
            changes = [
                change for change in changes
                if change.get("time", "") >= since_date
            ]
            logger.info(
                f"Filtered changes by date (since {since_date}): "
                f"{original_count} -> {len(changes)}"
            )

        # Ограничение результатов (если указано)
        if limit and limit > 0:
            original_count = len(changes)
            changes = changes[:limit]
            if original_count > limit:
                logger.info(f"Limited results from {original_count} to {limit}")

        logger.info(f"Loaded {len(changes)} record changes from NetHunt folder {folder_id}")
        return changes

    except requests.exceptions.HTTPError as e:
        logger.error(
            f"NetHunt API HTTP error: {e.response.status_code}, "
            f"URL: {url}, "
            f"Response: {e.response.text[:200] if hasattr(e.response, 'text') else 'N/A'}"
        )
        return []
    except requests.exceptions.Timeout:
        logger.error(f"NetHunt API timeout after {NETHUNT_TIMEOUT}s, URL: {url}")
        return []
    except requests.exceptions.ConnectionError as e:
        logger.error(f"NetHunt API connection error: {e}, URL: {url}")
        return []
    except Exception as e:
        logger.error(
            f"Unexpected error in nethunt_get_record_changes: {type(e).__name__}: {e}, "
            f"URL: {url}",
            exc_info=True
        )
        return []


def extract_status_history(record_id: str, all_changes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Извлечь историю изменений статуса для одной записи.

    Args:
        record_id: ID записи (учителя) в NetHunt
        all_changes: Все изменения из nethunt_get_record_changes()

    Returns:
        История статусов в хронологическом порядке:
        [{
            "time": "2025-10-01T10:00:00Z",
            "old_status": "new",
            "new_status": "contacted",
            "changed_by": "manager@ecademy.com"
        }]
    """
    status_history = []

    for change in all_changes:
        if change.get("recordId") != record_id:
            continue

        field_actions = change.get("fieldActions", [])

        for field_action in field_actions:
            field_name = field_action.get("field", "").lower()

            # Ищем изменения поля статуса
            if any(keyword in field_name for keyword in ["status", "статус", "stage", "этап"]):
                status_history.append({
                    "time": change.get("time"),
                    "old_status": field_action.get("oldValue"),
                    "new_status": field_action.get("newValue"),
                    "changed_by": change.get("user")
                })

    # Сортируем по времени
    status_history.sort(key=lambda x: x.get("time", ""))
    return status_history


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
    status_histories: Dict[str, List[Dict[str, Any]]],
    all_status_columns: set
) -> Dict[str, int]:
    """
    Подсчитать количество лидов кампании на каждом этапе воронки.

    ИСПОЛЬЗУЕТ РЕАЛЬНУЮ ИСТОРИЮ СТАТУСОВ из NetHunt API!

    Args:
        campaign_leads: Список лидов одной кампании из Meta API
        teacher_index: Индекс учителей {normalized_contact: record}
        status_histories: Истории статусов {record_id: [status_changes]}
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
            record_id = teacher_record.get("id")

            # Получаем историю статусов для этого учителя
            history = status_histories.get(record_id, [])

            if history:
                # КЛЮЧОВА РІЗНИЦЯ ВІД ALFACRM INFERENCE ПІДХОДУ:
                #
                # AlfaCRM (студенти):
                # - Inference підхід: відновлюємо шлях з поточного статусу
                # - Приклад: якщо статус = "Оплата" → інферуємо [Новий, Контакт, Пробний, Оплата]
                #
                # NetHunt (вчителі):
                # - Real history: використовуємо реальну історію змін з API
                # - Приклад: якщо історія = [New → Contacted → Qualified → Hired]
                #   то засчитуємо +1 в КОЖЕН стовпець: ["Нові", "Контакт", "Кваліфіковані", "Найнято"]
                #
                # Це дає НАКОПИЧУВАЛЬНУ статистику воронки:
                # - Кожен наступний статус є підмножиною попереднього (Найнято ⊆ Кваліфіковані ⊆ Контакт ⊆ Нові)
                # - Дозволяє аналізувати конверсію між етапами: (Найнято / Кваліфіковані) * 100%

                unique_statuses = set()
                for change in history:
                    new_status = change.get("new_status", "").lower() if change.get("new_status") else None

                    if new_status:
                        # Перетворюємо статус NetHunt → назва стовпця таблиці
                        # Використовуємо NETHUNT_STATUS_MAPPING з settings.py
                        column_name = map_nethunt_status_to_column(new_status)
                        unique_statuses.add(column_name)

                # Засчитуємо вчителя в КОЖЕН статус через який він пройшов
                # (це накопичувальна метрика для аналізу конверсії по етапах)
                for status_col in unique_statuses:
                    if status_col not in status_counts:
                        status_counts[status_col] = 0
                    status_counts[status_col] += 1
            else:
                # Fallback: если нет истории, используем текущий статус
                status_name = extract_status_from_record(teacher_record)
                column_name = map_nethunt_status_to_column(status_name)

                if column_name not in status_counts:
                    status_counts[column_name] = 0
                status_counts[column_name] += 1

        else:
            not_found_count += 1
            # Лиды которые не найдены в CRM считаем как "Нові"
            status_counts["Нові"] += 1

    logger.info(
        f"Teacher campaign tracking: {matched_count} matched, {not_found_count} not found in NetHunt"
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

    # 2. Загрузить ИСТОРИЮ изменений записей из NetHunt
    logger.info(f"Loading record change history from NetHunt folder {folder_id}...")

    # Опциональная фильтрация: загрузить изменения только за последние 90 дней
    # (можно настроить через ENV переменную для уменьшения нагрузки)
    since_date = None
    days_back = os.getenv("NETHUNT_HISTORY_DAYS", None)
    if days_back:
        try:
            from datetime import timedelta
            since_dt = datetime.now() - timedelta(days=int(days_back))
            since_date = since_dt.isoformat() + "Z"
            logger.info(f"Filtering history to last {days_back} days (since {since_date})")
        except (ValueError, TypeError) as e:
            logger.warning(f"Invalid NETHUNT_HISTORY_DAYS value: {days_back}, error: {e}")

    all_changes = nethunt_get_record_changes(folder_id, since_date=since_date)

    if not all_changes:
        logger.warning("No record changes found, falling back to current status only")

    # 3. Построить истории статусов для каждой записи
    record_ids = set(change.get("recordId") for change in all_changes if change.get("recordId"))
    status_histories = {}

    for record_id in record_ids:
        history = extract_status_history(record_id, all_changes)
        if history:
            status_histories[record_id] = history

    logger.info(f"Built status history for {len(status_histories)} teachers")

    # 4. Загрузить текущие записи учителей для индексации по контактам
    logger.info(f"Loading current teacher records from NetHunt folder {folder_id}...")

    try:
        all_records = nethunt_list_records(folder_id, limit=1000)
        logger.info(f"Loaded {len(all_records)} teacher records from NetHunt")
    except Exception as e:
        logger.error(f"Failed to load NetHunt records: {e}")
        return {}

    # 5. Построить индекс учителей
    teacher_index = build_teacher_index(all_records)
    logger.info(f"Built teacher index with {len(teacher_index)} contact entries")

    # 6. Собрать все уникальные статусы для создания столбцов
    all_status_columns = set(NETHUNT_STATUS_MAPPING.values())

    # Добавить реальные статусы из истории
    for history in status_histories.values():
        for change in history:
            new_status = change.get("new_status", "").lower() if change.get("new_status") else None
            if new_status:
                column_name = map_nethunt_status_to_column(new_status)
                all_status_columns.add(column_name)

    # Добавить текущие статусы из данных
    for record in all_records:
        status_name = extract_status_from_record(record)
        if status_name:
            column_name = map_nethunt_status_to_column(status_name)
            all_status_columns.add(column_name)

    logger.info(f"Found {len(all_status_columns)} unique status columns")

    # 7. Обработать каждую кампанию
    enriched_campaigns = {}

    for campaign_id, campaign_data in campaigns_data.items():
        campaign_leads = campaign_data.get("leads", [])

        # Подсчитать статусы для этой кампании ИСПОЛЬЗУЯ ИСТОРИЮ
        funnel_stats = track_campaign_leads(
            campaign_leads,
            teacher_index,
            status_histories,
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
