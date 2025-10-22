"""
Тест для проверки Archive лидов в AlfaCRM.

ЦЕЛЬ: Проверить:
1. Видны ли ліди зі статусом Archive (status_id = 7) через API
2. Яку інформацію можна отримати з Archive лідів
3. Скільки таких лідів у системі
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Завантажити змінні середовища
load_dotenv()

# Додати app директорію в Python path
app_dir = Path(__file__).parent.parent
sys.path.insert(0, str(app_dir))

from connectors.crm import alfacrm_list_students


def test_archive_status():
    """
    Перевірка Archive лідів в AlfaCRM.
    """

    print("\n" + "="*80)
    print("ТЕСТ: Перевірка Archive лідів в AlfaCRM")
    print("="*80)

    # Отримати студентів з AlfaCRM
    print(f"\n[1/3] Отримання студентів з AlfaCRM...")
    try:
        response = alfacrm_list_students(page=1, page_size=500)

        students = response.get('items', [])
        total_count = response.get('count', 0)

        print(f"  Отримано студентів: {len(students)}")
        print(f"  Загальна кількість в системі: {total_count}")

    except Exception as e:
        print(f"  ПОМИЛКА: {e}")
        import traceback
        traceback.print_exc()
        return

    # Фільтрувати Archive лідів (status_id = 7)
    print(f"\n[2/3] Пошук лідів зі статусом Archive (status_id = 7)...")

    archive_leads = [s for s in students if s.get('status_id') == 7]

    print(f"  Знайдено Archive лідів: {len(archive_leads)}")

    if not archive_leads:
        print("\n  ВАЖЛИВО: Немає лідів зі статусом Archive")
        print("  Можливі причини:")
        print("    1. Archive ліди дійсно відсутні в системі")
        print("    2. API не повертає Archive ліди (фільтрує їх)")
        print("    3. Archive статус має інший ID")
        return

    # Аналіз структури Archive лідів
    print(f"\n[3/3] Аналіз структури Archive лідів...")

    # Показати перший Archive лід для аналізу
    first_archive = archive_leads[0]

    print(f"\n  Приклад Archive ліда:")
    print(f"  {'='*70}")

    # Показати всі доступні поля
    for key, value in first_archive.items():
        # Обмежити довжину виводу для великих полів
        value_str = str(value)
        if len(value_str) > 100:
            value_str = value_str[:100] + "..."
        print(f"    {key}: {value_str}")

    print(f"  {'='*70}")

    # Статистика по Archive лідах
    print(f"\n  Статистика Archive лідів:")
    print(f"    Всього Archive лідів: {len(archive_leads)}")
    print(f"    Відсоток від загальної кількості: {len(archive_leads) / len(students) * 100:.1f}%")

    # Перевірити які ще поля є
    print(f"\n  Доступні поля в Archive лідах:")
    all_keys = set()
    for lead in archive_leads[:10]:  # Перші 10 Archive лідів
        all_keys.update(lead.keys())

    print(f"    Всього унікальних полів: {len(all_keys)}")
    print(f"    Поля: {', '.join(sorted(all_keys))}")

    # Перевірити чи є Meta lead_id
    archive_with_meta = [
        s for s in archive_leads
        if s.get('lead_id') or s.get('comment')
    ]

    print(f"\n  Archive ліди з Meta інформацією:")
    print(f"    Archive лідів з lead_id або comment: {len(archive_with_meta)}")

    if archive_with_meta:
        print(f"\n  Приклад Archive ліда з Meta інформацією:")
        example = archive_with_meta[0]
        print(f"    ID: {example.get('id')}")
        print(f"    Status ID: {example.get('status_id')}")
        print(f"    Lead ID: {example.get('lead_id', 'Немає')}")
        print(f"    Comment: {example.get('comment', 'Немає')[:100]}...")
        print(f"    Created: {example.get('created_at', 'Немає')}")

    # Підсумки
    print("\n" + "="*80)
    print("РЕЗУЛЬТАТИ ДОСЛІДЖЕННЯ:")
    print("="*80)

    print(f"\n1. Archive ліди ВИДНІ через API: {'ТАК' if archive_leads else 'НІ'}")

    if archive_leads:
        print(f"2. Кількість Archive лідів: {len(archive_leads)}")
        print(f"3. Доступна інформація:")
        print(f"   - Всього полів: {len(all_keys)}")
        print(f"   - Є Meta lead_id: {'ТАК' if any(s.get('lead_id') for s in archive_leads) else 'НІ'}")
        print(f"   - Є коментарі: {'ТАК' if any(s.get('comment') for s in archive_leads) else 'НІ'}")
        print(f"\n4. РЕКОМЕНДАЦІЯ:")
        print(f"   Archive статус ПОТРІБНО додати в ALFACRM_STATUS_TO_GROUP mapping")
        print(f"   як окрему агреговану групу для коректного обліку всіх лідів.")
    else:
        print(f"2. РЕКОМЕНДАЦІЯ:")
        print(f"   Перевірити чи Archive статус має ID = 7")
        print(f"   або чи API не фільтрує Archive ліди")


if __name__ == "__main__":
    test_archive_status()
