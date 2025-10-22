"""
Скрипт для анализа Archive лидов и поиска комментариев менеджера.

Цель:
1. Извлечь всех Archive лидов (custom_ads_comp == 'архів')
2. Проанализировать ВСЕ текстовые поля на наличие комментариев
3. Найти паттерны: "Зник після контакту", "Відмова", "Не ЦА"
4. Определить, в каком поле хранятся комментарии менеджера

Использование:
    python scripts/analyze_archive_leads_comments.py
"""
import sys
import json
from pathlib import Path
from collections import Counter
from dotenv import load_dotenv

# Добавить путь к проекту
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "app"))

load_dotenv(project_root / ".env")

from connectors.crm import alfacrm_list_students


def print_separator(title: str):
    """Печать разделителя."""
    print(f"\n{'=' * 80}")
    print(f"{title:^80}")
    print(f"{'=' * 80}\n")


def analyze_archive_leads():
    """Извлечь и проанализировать все Archive лиды."""
    print("Шаг 1: Извлечение Archive лидов из AlfaCRM")
    print("-" * 80)

    try:
        # Запросить всех студентов
        print("Запрос студентов из AlfaCRM...")
        result = alfacrm_list_students(page=1, page_size=1000)

        if not result or "items" not in result:
            print("ERROR: Не удалось получить студентов")
            return None

        all_students = result["items"]
        print(f"OK Получено {len(all_students)} студентов")

        # Фильтровать Archive лиды
        archive_leads = [
            s for s in all_students
            if s.get("custom_ads_comp") == "архів"
        ]

        print(f"\nНайдено Archive лидов: {len(archive_leads)}")

        if not archive_leads:
            print("WARNING: Не найдено Archive лидов!")
            return None

        return archive_leads

    except Exception as e:
        print(f"ERROR: Не удалось извлечь студентов: {e}")
        import traceback
        traceback.print_exc()
        return None


def extract_text_fields(lead: dict) -> dict:
    """Извлечь все текстовые поля из лида."""
    text_fields = {}

    # Список всех возможных текстовых полей в AlfaCRM
    potential_text_fields = [
        "note",
        "comment",
        "comments",
        "description",
        "reject_reason",
        "status_comment",
        "manager_comment",
        "admin_comment",
        "custom_comment",
        "custom_note",
        "custom_reject_reason",
    ]

    for field in potential_text_fields:
        value = lead.get(field)
        if value and isinstance(value, str) and value.strip():
            text_fields[field] = value

    # Также проверить все custom_* поля
    for key, value in lead.items():
        if key.startswith("custom_") and isinstance(value, str) and value.strip():
            if key not in text_fields:
                text_fields[key] = value

    return text_fields


def analyze_comment_patterns(archive_leads: list):
    """Проанализировать паттерны комментариев в Archive лидах."""
    print("\nШаг 2: Анализ паттернов комментариев")
    print("-" * 80)

    # Паттерны для поиска
    patterns = [
        "зник після контакту",
        "зник",
        "відмова",
        "не ца",
        "не цільова",
        "похилий вік",
        "недозвон",
        "недодзвон",
    ]

    pattern_findings = {pattern: [] for pattern in patterns}
    all_text_fields = Counter()

    print(f"Анализирую {len(archive_leads)} Archive лидов...\n")

    for i, lead in enumerate(archive_leads, 1):
        lead_id = lead.get("id")
        lead_name = lead.get("name", "Без имени")

        # Извлечь все текстовые поля
        text_fields = extract_text_fields(lead)

        # Подсчитать, какие поля встречаются
        for field_name in text_fields.keys():
            all_text_fields[field_name] += 1

        # Искать паттерны во всех текстовых полях
        for field_name, field_value in text_fields.items():
            field_value_lower = field_value.lower()

            for pattern in patterns:
                if pattern in field_value_lower:
                    pattern_findings[pattern].append({
                        "lead_id": lead_id,
                        "lead_name": lead_name,
                        "field_name": field_name,
                        "field_value": field_value[:200],  # Первые 200 символов
                    })

        # Показывать первые 3 примера подробно
        if i <= 3:
            print(f"Пример {i}: {lead_name} (ID: {lead_id})")
            print(f"  lead_status_id: {lead.get('lead_status_id')}")
            print(f"  custom_ads_comp: {lead.get('custom_ads_comp')}")

            if text_fields:
                print("  Найденные текстовые поля:")
                for field_name, field_value in text_fields.items():
                    preview = field_value[:100] + "..." if len(field_value) > 100 else field_value
                    print(f"    - {field_name}: {preview}")
            else:
                print("  ⚠️ НЕТ текстовых полей с комментариями!")
            print()

    # Отчет по найденным полям
    print("\nШаг 3: Какие текстовые поля встречаются в Archive лидах")
    print("-" * 80)

    if all_text_fields:
        print(f"Найдено {len(all_text_fields)} уникальных текстовых полей:\n")
        for field_name, count in all_text_fields.most_common():
            pct = (count / len(archive_leads)) * 100
            print(f"  {field_name:30s} - в {count:3d} лидах ({pct:5.1f}%)")
    else:
        print("⚠️ НЕ НАЙДЕНО текстовых полей с комментариями!")

    # Отчет по паттернам
    print("\nШаг 4: Найденные паттерны комментариев")
    print("-" * 80)

    found_any = False
    for pattern, findings in pattern_findings.items():
        if findings:
            found_any = True
            print(f"\n✅ Паттерн '{pattern}': найден в {len(findings)} лидах")

            # Показать первые 3 примера
            for i, finding in enumerate(findings[:3], 1):
                print(f"   Пример {i}:")
                print(f"     Лид: {finding['lead_name']} (ID: {finding['lead_id']})")
                print(f"     Поле: {finding['field_name']}")
                print(f"     Текст: {finding['field_value']}")
                print()

    if not found_any:
        print("❌ НЕ НАЙДЕНО паттернов комментариев в Archive лидах!")
        print("\nВозможные причины:")
        print("  1. Комментарии хранятся в другом месте (не в API)")
        print("  2. Комментарии видны только в UI AlfaCRM")
        print("  3. Комментарии хранятся в отдельной таблице timeline/history")

    return {
        "pattern_findings": pattern_findings,
        "text_fields_stats": all_text_fields,
        "total_archive_leads": len(archive_leads)
    }


def main():
    """Главная функция."""
    print_separator("АНАЛИЗ ARCHIVE ЛИДОВ И КОММЕНТАРИЕВ МЕНЕДЖЕРА")

    print("Этот скрипт проанализирует все Archive лиды на наличие")
    print("комментариев менеджера ('Зник після контакту', 'Відмова', 'Не ЦА').\n")

    # Извлечь Archive лиды
    archive_leads = analyze_archive_leads()

    if not archive_leads:
        print("\nERROR: Не удалось извлечь Archive лиды")
        return

    # Проанализировать паттерны комментариев
    analysis_result = analyze_comment_patterns(archive_leads)

    print_separator("АНАЛИЗ ЗАВЕРШЕН")

    # Выводы
    print("\nВЫВОДЫ:")
    print("-" * 80)

    text_fields_count = len(analysis_result["text_fields_stats"])
    patterns_found = sum(
        1 for findings in analysis_result["pattern_findings"].values()
        if findings
    )

    if text_fields_count == 0:
        print("❌ В Archive лидах НЕ НАЙДЕНО текстовых полей с комментариями")
        print("   Комментарии менеджера НЕ доступны через AlfaCRM API")
    elif patterns_found == 0:
        print("⚠️ Текстовые поля найдены, но паттерны комментариев не обнаружены")
        print("   Возможно, нужно проверить другие ключевые слова")
    else:
        print(f"✅ Найдены комментарии менеджера!")
        print(f"   Паттернов обнаружено: {patterns_found}")
        print(f"   Текстовых полей используется: {text_fields_count}")

    print("\nРЕКОМЕНДАЦИИ:")
    if text_fields_count > 0 and patterns_found > 0:
        print("1. Использовать найденные поля для классификации Archive лидов")
        print("2. Создать функцию extract_archive_classification() в backend")
        print("3. Обновить таблицу с разделением Archive на ЦА/не ЦА")
    else:
        print("1. Комментарии НЕ доступны через API")
        print("2. Использовать альтернативное решение: создать статусы 'Архів ЦА' и 'Архів не ЦА'")
        print("3. Обучить менеджеров использовать новые статусы")


if __name__ == "__main__":
    main()
