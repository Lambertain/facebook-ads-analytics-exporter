"""
Диагностический скрипт для проверки маппинга статусов лидов в AlfaCRM.

Цель:
1. Получить все возможные статусы лидов из AlfaCRM API
2. Показать примеры реальных студентов с разными lead_status_id
3. Сравнить с текущим ALFACRM_STATUS_MAPPING
4. Выявить расхождения и недостающие статусы

Использование:
    python scripts/check_alfacrm_statuses.py
"""
import asyncio
import sys
import os
from pathlib import Path
from collections import Counter
from dotenv import load_dotenv

# Добавить путь к проекту
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "app"))

load_dotenv(project_root / ".env")

from connectors.crm import alfacrm_list_students


# Текущий маппинг из alfacrm_tracking.py
CURRENT_MAPPING = {
    1: "Не розібрані",
    2: "Встанов. контакт (ЦА)",
    3: "В опрацюванні (ЦА)",
    4: "Назначений пробний",
    5: "Проведений пробний",
    6: "Купили (ЦА)",
    7: "Архів",
    8: "Недзвін",
}


def print_separator(title: str):
    """Печать разделителя."""
    print(f"\n{'=' * 80}")
    print(f"{title:^80}")
    print(f"{'=' * 80}\n")


async def get_lead_status_info():
    """Получить информацию о статусах лидов из AlfaCRM."""
    print("Шаг 1: Запрос информации о статусах лидов из AlfaCRM API")
    print("-" * 80)

    # AlfaCRM не имеет публичного endpoint для справочника статусов
    # Будем анализировать реальных студентов

    print("\nINFO: AlfaCRM не предоставляет endpoint для справочника статусов")
    print("Переходим к анализу реальных студентов")
    return None


async def analyze_real_students():
    """Анализировать реальных студентов для определения статусов."""
    print("\nШаг 2: Анализ реальных студентов из AlfaCRM")
    print("-" * 80)

    try:
        # Запросить первые 1000 студентов (все данные)
        print("Запрос студентов из AlfaCRM (первые 1000)...")

        # Используем функцию alfacrm_list_students (она НЕ async, вызываем напрямую)
        result = alfacrm_list_students(page=1, page_size=1000)

        if not result or "items" not in result:
            print("ERROR: Не удалось получить студентов")
            return None

        all_students = result["items"]
        total_count = result.get("count", len(all_students))

        print(f"OK Получено {len(all_students)} студентов из {total_count}")

        # Собрать все уникальные lead_status_id
        status_counter = Counter()
        status_examples = {}  # {status_id: [examples]}

        for student in all_students:
            status_id = student.get("lead_status_id")
            if status_id is not None:
                status_counter[status_id] += 1

                # Сохранить первые 3 примера для каждого статуса
                if status_id not in status_examples:
                    status_examples[status_id] = []

                if len(status_examples[status_id]) < 3:
                    status_examples[status_id].append({
                        "id": student.get("id"),
                        "name": student.get("name", "Без имени"),
                        "phone": student.get("phone", [""])[0] if student.get("phone") else "",
                        "created_at": student.get("assigned_at", "Неизвестно")
                    })

        print(f"\nНайдено {len(status_counter)} уникальных статусов")

        return {
            "status_counter": status_counter,
            "status_examples": status_examples,
            "total_students": len(all_students)
        }

    except Exception as e:
        print(f"ERROR: Не удалось проанализировать студентов: {e}")
        import traceback
        traceback.print_exc()
        return None


def compare_mappings(analysis_result):
    """Сравнить найденные статусы с текущим маппингом."""
    print("\nШаг 3: Сравнение с текущим ALFACRM_STATUS_MAPPING")
    print("-" * 80)

    status_counter = analysis_result["status_counter"]
    status_examples = analysis_result["status_examples"]
    total = analysis_result["total_students"]

    # Найти статусы
    found_statuses = set(status_counter.keys())
    mapped_statuses = set(CURRENT_MAPPING.keys())

    # Расхождения
    missing_in_mapping = found_statuses - mapped_statuses
    extra_in_mapping = mapped_statuses - found_statuses

    print(f"ТЕКУЩИЙ МАППИНГ:")
    print("-" * 80)
    for status_id, name in CURRENT_MAPPING.items():
        count = status_counter.get(status_id, 0)
        pct = (count / total) * 100 if total > 0 else 0

        if status_id in found_statuses:
            print(f"  {status_id}: {name:30s} [{count:4d} студентов, {pct:5.1f}%] OK")
        else:
            print(f"  {status_id}: {name:30s} [НЕ НАЙДЕНО В CRM] MISSING")

    print(f"\nРЕАЛЬНЫЕ СТАТУСЫ В CRM:")
    print("-" * 80)

    # Сортировать по количеству студентов
    sorted_statuses = sorted(status_counter.items(), key=lambda x: x[1], reverse=True)

    for status_id, count in sorted_statuses:
        pct = (count / total) * 100
        mapped_name = CURRENT_MAPPING.get(status_id, "НЕИЗВЕСТНЫЙ СТАТУС")

        marker = "OK" if status_id in mapped_statuses else "!! NEW"

        print(f"  {status_id}: {count:4d} студентов ({pct:5.1f}%) - {mapped_name:30s} {marker}")

        # Показать примеры
        if status_id in status_examples:
            examples = status_examples[status_id]
            for i, ex in enumerate(examples, 1):
                print(f"       Пример {i}: {ex['name']:20s} (ID: {ex['id']}, тел: {ex['phone']})")

    # Выводы
    print("\nВЫВОДЫ:")
    print("-" * 80)

    if missing_in_mapping:
        print(f"!! Найдены статусы, ОТСУТСТВУЮЩИЕ в маппинге: {sorted(missing_in_mapping)}")
    else:
        print("OK Все найденные статусы присутствуют в маппинге")

    if extra_in_mapping:
        print(f"!! Статусы в маппинге, НЕ найденные в CRM: {sorted(extra_in_mapping)}")
    else:
        print("OK Все статусы из маппинга найдены в CRM")

    # Проверка продаж
    sales_status_id = 6
    sales_count = status_counter.get(sales_status_id, 0)

    print(f"\nПРОВЕРКА ПРОДАЖ:")
    print("-" * 80)
    print(f"Статус 'Купили (ЦА)' (ID: {sales_status_id})")
    print(f"  Студентов в этом статусе: {sales_count}")

    if sales_count == 0:
        print("  !! ВНИМАНИЕ: Не найдено студентов со статусом 'Купили (ЦА)'")
        print("  Возможные причины:")
        print("    1. Статус продаж имеет другой ID (не 6)")
        print("    2. Продажи отслеживаются через другое поле (не lead_status_id)")
        print("    3. За сентябрь действительно не было продаж")
    else:
        pct = (sales_count / total) * 100
        print(f"  OK Найдено продаж: {sales_count} ({pct:.1f}% от всех студентов)")


async def main():
    """Главная функция."""
    print_separator("ДИАГНОСТИКА МАППИНГА СТАТУСОВ ALFACRM")

    print("Этот скрипт проверит соответствие текущего маппинга статусов")
    print("реальным данным в AlfaCRM.\n")

    # Попытка получить справочник статусов
    status_info = await get_lead_status_info()

    if status_info:
        print("\nПолучен справочник статусов из API:")
        for status in status_info:
            print(f"  {status}")

    # Анализ реальных студентов
    analysis_result = await analyze_real_students()

    if not analysis_result:
        print("\nERROR: Не удалось выполнить анализ")
        return

    # Сравнение
    compare_mappings(analysis_result)

    print_separator("ДИАГНОСТИКА ЗАВЕРШЕНА")

    print("\nРЕКОМЕНДАЦИИ:")
    print("1. Проверьте статусы с отметкой !! NEW")
    print("2. Обновите ALFACRM_STATUS_MAPPING в app/services/alfacrm_tracking.py")
    print("3. Запустите повторное тестирование после обновления")


if __name__ == "__main__":
    asyncio.run(main())
