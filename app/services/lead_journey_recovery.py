"""
Lead Journey Recovery Service

Восстановление истории лида через воронку на основе текущего статуса AlfaCRM.
Интеллектуальное восстановление пути лида через 38 статусов.
"""
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


# Определяем логическую последовательность воронки
# Основная воронка (первая колонка статусов)
MAIN_FUNNEL_ORDER = [
    13,  # Не розібраний (новый лид)
    11,  # Недодзвон
    10,  # Недозвон 2
    27,  # Недозвон 3
    1,   # Вст контакт невідомо
    32,  # Вст контакт зацікавлений
    26,  # Зник після контакту
    12,  # Розмовляли, чекаємо відповідь
    6,   # Чекає пробного
    2,   # Призначено пробне
    3,   # Проведено пробне
    5,   # Не відвідав пробне
    9,   # Чекаємо оплату
    4,   # Отримана оплата (конверсия)
    29,  # Сплатить через 2 тижні >
    25,  # Передзвонити через 2 тижні
    30,  # Передзвон через місяць
    31,  # Передзвон 2 місяці і більше
    8,   # Опрацювати заперечення
    50,  # Старі клієнти
]

# Вторая воронка (дубликаты для второй ветки)
SECONDARY_FUNNEL_ORDER = [
    18,  # Недозвон
    40,  # Недозвон 2
    42,  # недозвон 3
    43,  # Встан коннт невідомо
    22,  # Встан контакт зацікавлений
    44,  # Зник після контакту
    24,  # Розмовляли чекаємо відповіді
    34,  # Чекає пробного
    35,  # Призначено пробне
    37,  # Проведено пробне
    36,  # Не відвідав пробне
    38,  # Чекає оплату
    39,  # Отримана оплата (конверсия)
    45,  # Сплатить через 2 тижні
    46,  # Передзвонити через 2 тижні
    47,  # Передз через місяць
    48,  # Передзвон 2 місяці і більше
    49,  # Опрацювати заперечення
]

# Объединенная воронка для поиска
COMBINED_FUNNEL_ORDER = MAIN_FUNNEL_ORDER + SECONDARY_FUNNEL_ORDER

# Маппинг статусов для отображения (из alfacrm_tracking.py)
ALFACRM_STATUS_NAMES = {
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
    4: "Отримана оплата",
    29: "Сплатить через 2 тижні >",
    25: "Передзвонити через 2 тижні",
    30: "Передзвон через місяць",
    31: "Передзвон 2 місяці і більше",
    8: "Опрацювати заперечення",
    13: "Не розібраний",
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
    39: "Отримана оплата",
    45: "Сплатить через 2 тижні",
    46: "Передзвонити через 2 тижні",
    47: "Передз через місяць",
    48: "Передзвон 2 місяці і більше",
    49: "Опрацювати заперечення",
}


def recover_lead_journey(current_status_id: int) -> List[int]:
    """
    Восстановить путь лида через воронку на основе текущего статуса.

    Логика восстановления:
    1. Определяем в какой воронке находится текущий статус (основная/вторая)
    2. Восстанавливаем линейный путь от начала воронки до текущего статуса
    3. Возвращаем список ID статусов, через которые прошел лид

    Args:
        current_status_id: Текущий lead_status_id из AlfaCRM

    Returns:
        Список status_id, через которые прошел лид (от начала до текущего)

    Examples:
        >>> recover_lead_journey(4)  # Отримана оплата
        [13, 11, 1, 32, 12, 6, 2, 3, 9, 4]

        >>> recover_lead_journey(39)  # Отримана оплата (вторая воронка)
        [18, 43, 22, 24, 34, 35, 37, 38, 39]
    """
    if current_status_id not in ALFACRM_STATUS_NAMES:
        logger.warning(f"Unknown status_id: {current_status_id}")
        return [current_status_id]

    # Определяем, в какой воронке находится статус
    if current_status_id in MAIN_FUNNEL_ORDER:
        funnel_order = MAIN_FUNNEL_ORDER
        logger.debug(f"Status {current_status_id} found in main funnel")
    elif current_status_id in SECONDARY_FUNNEL_ORDER:
        funnel_order = SECONDARY_FUNNEL_ORDER
        logger.debug(f"Status {current_status_id} found in secondary funnel")
    else:
        # Если статус не найден ни в одной воронке, возвращаем только его
        logger.warning(f"Status {current_status_id} not found in any funnel")
        return [current_status_id]

    try:
        # Находим индекс текущего статуса
        current_index = funnel_order.index(current_status_id)

        # Восстанавливаем путь от начала до текущего статуса (включительно)
        journey = funnel_order[:current_index + 1]

        logger.debug(
            f"Recovered journey for status {current_status_id} ({ALFACRM_STATUS_NAMES[current_status_id]}): "
            f"{len(journey)} steps"
        )

        return journey

    except ValueError:
        # Если индекс не найден (не должно происходить после проверки выше)
        logger.error(f"Failed to find index for status_id {current_status_id} in funnel")
        return [current_status_id]


def get_journey_statistics(journey: List[int]) -> Dict[str, Any]:
    """
    Получить статистику по пути лида.

    Args:
        journey: Список status_id, через которые прошел лид

    Returns:
        Словарь со статистикой:
        - total_steps: Общее количество шагов
        - conversion_reached: Достиг ли лид конверсии (статус 4 или 39)
        - current_status: Текущий статус
        - funnel_type: Тип воронки (main/secondary)
    """
    if not journey:
        return {
            "total_steps": 0,
            "conversion_reached": False,
            "current_status": None,
            "funnel_type": "unknown"
        }

    current_status_id = journey[-1]
    conversion_statuses = {4, 39}  # Отримана оплата в обеих воронках

    # Определяем тип воронки
    funnel_type = "main" if current_status_id in MAIN_FUNNEL_ORDER else "secondary"

    return {
        "total_steps": len(journey),
        "conversion_reached": current_status_id in conversion_statuses,
        "current_status": current_status_id,
        "current_status_name": ALFACRM_STATUS_NAMES.get(current_status_id, "Unknown"),
        "funnel_type": funnel_type
    }


def build_journey_path_names(journey: List[int]) -> List[str]:
    """
    Преобразовать список status_id в список названий статусов.

    Args:
        journey: Список status_id

    Returns:
        Список названий статусов

    Example:
        >>> build_journey_path_names([13, 11, 1, 32, 4])
        ["Не розібраний", "Недодзвон", "Вст контакт невідомо", "Вст контакт зацікавлений", "Отримана оплата"]
    """
    return [ALFACRM_STATUS_NAMES.get(status_id, f"Unknown ({status_id})") for status_id in journey]


def enrich_student_with_journey(student: Dict[str, Any]) -> Dict[str, Any]:
    """
    Обогатить данные студента информацией о пути через воронку.

    Args:
        student: Словарь с данными студента из AlfaCRM (должен содержать lead_status_id)

    Returns:
        Обогащенный словарь с дополнительными полями:
        - journey_status_ids: Список ID статусов, через которые прошел лид
        - journey_status_names: Список названий статусов
        - journey_stats: Статистика по пути лида
    """
    lead_status_id = student.get("lead_status_id")

    if not lead_status_id:
        logger.warning(f"Student {student.get('id')} has no lead_status_id")
        return {
            **student,
            "journey_status_ids": [],
            "journey_status_names": [],
            "journey_stats": get_journey_statistics([])
        }

    # Восстанавливаем путь лида
    journey = recover_lead_journey(lead_status_id)

    # Получаем названия статусов
    journey_names = build_journey_path_names(journey)

    # Получаем статистику
    stats = get_journey_statistics(journey)

    return {
        **student,
        "journey_status_ids": journey,
        "journey_status_names": journey_names,
        "journey_stats": stats
    }


def batch_enrich_students(students: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Пакетное обогащение студентов информацией о пути через воронку.

    Args:
        students: Список студентов из AlfaCRM

    Returns:
        Список обогащенных студентов
    """
    enriched_students = []

    for student in students:
        enriched_student = enrich_student_with_journey(student)
        enriched_students.append(enriched_student)

    logger.info(f"Enriched {len(enriched_students)} students with journey data")

    return enriched_students


# Утилиты для анализа воронки

def calculate_funnel_conversion_rate(students: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Вычислить процент конверсии для каждого этапа воронки.

    Args:
        students: Список студентов с journey_stats

    Returns:
        Словарь {status_name: conversion_rate_percent}
    """
    if not students:
        return {}

    # Подсчитываем количество лидов на каждом статусе
    status_counts = {}
    for student in students:
        journey = student.get("journey_status_ids", [])
        for status_id in journey:
            status_name = ALFACRM_STATUS_NAMES.get(status_id, f"Unknown ({status_id})")
            status_counts[status_name] = status_counts.get(status_name, 0) + 1

    # Вычисляем процент конверсии относительно начала воронки
    total_leads = len(students)
    conversion_rates = {}

    for status_name, count in status_counts.items():
        conversion_rate = (count / total_leads) * 100 if total_leads > 0 else 0
        conversion_rates[status_name] = round(conversion_rate, 2)

    return conversion_rates


def get_funnel_drop_off_points(students: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Определить точки наибольшего отсева в воронке.

    Args:
        students: Список студентов с journey_stats

    Returns:
        Список словарей с информацией о точках отсева:
        - from_status: Статус, с которого происходит отсев
        - to_status: Следующий статус в воронке
        - drop_count: Количество лидов, не дошедших до следующего статуса
        - drop_rate: Процент отсева
    """
    # TODO: Реализовать анализ точек отсева
    # Требует данных о предыдущих статусах лидов (история изменений)
    logger.warning("get_funnel_drop_off_points not yet implemented")
    return []
