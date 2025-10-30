"""
Campaign Formatter Service

Преобразование обогащенных данных кампаний из alfacrm_tracking
в формат строк для экспорта в Excel согласно спецификации.
"""
from typing import List, Dict, Any
from datetime import datetime


def transform_enriched_campaigns_to_excel_rows(
    enriched_campaigns: Dict[str, Dict[str, Any]],
    analysis_date: str,
    date_range: str,
    facebook_ads_url: str
) -> List[Dict[str, Any]]:
    """
    Преобразовать enriched_campaigns в формат строк для Excel.

    Args:
        enriched_campaigns: Результат от alfacrm_tracking.track_leads_by_campaigns()
        analysis_date: Дата анализа (формат: ДД.ММ.РРРР)
        date_range: Период анализа (формат: ДД.ММ.РРРР - ДД.ММ.РРРР)
        facebook_ads_url: URL ссылка на рекламный аккаунт

    Returns:
        Список словарей, где каждый словарь = 1 строка таблицы с 36 колонками
    """
    rows = []

    for campaign_id, campaign_data in enriched_campaigns.items():
        funnel = campaign_data.get("funnel_stats", {})

        # Основные данные кампании
        row = {
            # Колонка 1: Название РК
            "Название Рекламной компании": campaign_data.get("campaign_name", ""),

            # Колонка 2: Ссылка на РК
            "Посилання на рекламну компанію": facebook_ads_url,

            # Колонка 3: Дата анализа
            "Дата аналізу": analysis_date,

            # Колонка 4: Период анализа
            "Період аналізу запущеної компанії": date_range,

            # Колонка 5: Бюджет
            "Витрачений бюджет в $": campaign_data.get("budget", 0.0),

            # Колонка 6: Местоположение
            "Місце знаходження (країни чи міста)": campaign_data.get("location", ""),

            # Колонка 7: Количество лидов
            "Кількість лідів": funnel.get("Кількість лідів", 0),
        }

        # Колонки 8-18: Данные по лидам (из funnel_stats)
        # Колонка 8: Проверка лидов автоматический (ФОРМУЛА)
        row["Перевірка лідів автоматичний"] = _calculate_verification_total(funnel)

        # Колонка 9: Не разобранные
        row["Не розібраний"] = funnel.get("Не розібраний", 0)

        # Колонка 10: Вст контакт неизвестно (НОВАЯ)
        row["Вст контакт невідомо"] = funnel.get("Вст контакт невідомо", 0)

        # Колонка 11: Установлен контакт заинтересованный (ЦА)
        row["Вст контакт зацікавлений (ЦА)"] = funnel.get("Встановлено контакт (ЦА)", 0)

        # Колонка 12: В обработке (ЦА)
        row["В опрацюванні (ЦА)"] = funnel.get("В опрацюванні (ЦА)", 0)

        # Колонка 13: Назначен пробный (ЦА)
        row["Призначено пробне (ЦА)"] = funnel.get("Призначено пробне (ЦА)", 0)

        # Колонка 14: Проведен пробный (ЦА)
        row["Проведено пробне (ЦА)"] = funnel.get("Проведено пробне (ЦА)", 0)

        # Колонка 15: Ожидание оплаты
        row["Чекаємо оплату"] = funnel.get("Чекає оплату", 0)

        # Колонка 16: Получена оплата (ЦА)
        row["Отримана оплата (ЦА)"] = funnel.get("Отримана оплата (ЦА)", 0)

        # Колонка 17: Архив (ЦА) ( В )
        row["Архів (ЦА) ( В )"] = funnel.get("Архів (ЦА)", 0)

        # Колонка 18: Недозвон (не ЦА)
        row["Недозвон (не ЦА)"] = funnel.get("Недозвон (не ЦА)", 0)

        # Колонка 19: Архив (не ЦА)
        row["Архів (не ЦА)"] = funnel.get("Архів (не ЦА)", 0)

        # Колонки 19-20: Количество целевых/нецелевых лидов (ФОРМУЛЫ)
        row["Кількість цільових лідів"] = _calculate_target_leads(funnel, row)
        row["Кількість не цільових лідів"] = _calculate_non_target_leads(funnel, row)

        # Колонки 21-27: Проценты (ФОРМУЛЫ)
        total_leads = row["Кількість лідів"]

        row["% цільових лідів"] = _safe_percent(row["Кількість цільових лідів"], total_leads)
        row["% не цільових лідів"] = _safe_percent(row["Кількість не цільових лідів"], total_leads)
        row["% Встан. контакт"] = _safe_percent(row["Вст контакт зацікавлений (ЦА)"], total_leads)
        row["% В опрацюванні (ЦА)"] = _safe_percent(row["В опрацюванні (ЦА)"], total_leads)
        row["% конверсія"] = _safe_percent(row["Отримана оплата (ЦА)"], total_leads)
        row["% архів"] = _safe_percent(
            row["Архів (ЦА) ( В )"] + row["Архів (не ЦА)"],
            total_leads
        )
        row["% недозвон"] = _safe_percent(row["Недозвон (не ЦА)"], total_leads)

        # Колонки 28-29: Финансовые показатели (ФОРМУЛЫ)
        budget = row["Витрачений бюджет в $"]
        row["Ціна / ліда"] = _safe_division(budget, total_leads)
        row["Ціна / цільового ліда"] = _safe_division(budget, row["Кількість цільових лідів"])

        # Колонка 30: Заметки (пусто)
        row["Нотатки"] = ""

        # Колонки 31-34: Дополнительные проценты (ФОРМУЛЫ)
        row["% Призначених пробних"] = _safe_percent(row["Призначено пробне (ЦА)"], total_leads)
        row["% Проведених пробних від загальних лідів(ЦА)"] = _safe_percent(
            row["Проведено пробне (ЦА)"],
            total_leads
        )
        row["% Проведених пробних від призначених пробних"] = _safe_percent(
            row["Проведено пробне (ЦА)"],
            row["Призначено пробне (ЦА)"]
        )
        row["Конверсія з проведеного пробного в продаж"] = _safe_percent(
            row["Отримана оплата (ЦА)"],
            row["Проведено пробне (ЦА)"]
        )

        # Колонка 35: CPC (из Facebook, если есть)
        row["CPC"] = campaign_data.get("cpc", 0.0)

        rows.append(row)

    return rows


def _calculate_verification_total(funnel: Dict[str, int]) -> int:
    """
    Колонка 8: Перевірка лідів автоматичний
    Формула: сумма колонок 9-18
    """
    return (
        funnel.get("Не розібраний", 0) +
        funnel.get("Вст контакт невідомо", 0) +
        funnel.get("Встановлено контакт (ЦА)", 0) +
        funnel.get("В опрацюванні (ЦА)", 0) +
        funnel.get("Чекає оплату", 0) +
        funnel.get("Отримана оплата (ЦА)", 0) +
        funnel.get("Архів (ЦА)", 0) +
        funnel.get("Недозвон (не ЦА)", 0) +
        funnel.get("Архів (не ЦА)", 0)
    )


def _calculate_target_leads(funnel: Dict[str, int], row: Dict[str, Any]) -> int:
    """
    Колонка 19: Кількість цільових лідів
    Формула: колонка 11 + 12 + 15 + 16 + 17
    """
    return (
        row["Вст контакт зацікавлений (ЦА)"] +
        row["В опрацюванні (ЦА)"] +
        row["Чекаємо оплату"] +
        row["Отримана оплата (ЦА)"] +
        row["Архів (ЦА) ( В )"]
    )


def _calculate_non_target_leads(funnel: Dict[str, int], row: Dict[str, Any]) -> int:
    """
    Колонка 20: Кількість не цільових лідів
    Формула: колонка 18 + 19
    """
    return row["Недозвон (не ЦА)"] + row["Архів (не ЦА)"]


def _safe_percent(value: float, total: float) -> float:
    """
    Безопасное вычисление процента с округлением до 2 знаков.
    """
    if total == 0:
        return 0.0
    return round((value / total) * 100, 2)


def _safe_division(numerator: float, denominator: float) -> float:
    """
    Безопасное деление с округлением до 2 знаков.
    """
    if denominator == 0:
        return 0.0
    return round(numerator / denominator, 2)
