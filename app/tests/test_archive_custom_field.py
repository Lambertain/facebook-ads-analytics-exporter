"""
Тест для проверки Archive лидов через кастомное поле custom_ads_comp.

ЦЕЛЬ: Проверить:
1. Сколько лидов имеют custom_ads_comp = "архів"
2. Какую информацию можно извлечь из Archive лидов
3. Нужно ли их включать в агрегацию статусов
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


def test_archive_custom_field():
    """
    Перевірка Archive лідів через custom_ads_comp поле.
    """

    print("\n" + "="*80)
    print("ТЕСТ: Перевірка Archive лідів через custom_ads_comp")
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

    # Фільтрувати Archive лідів через custom_ads_comp
    print(f"\n[2/3] Пошук лідів з custom_ads_comp = 'архів'...")

    archive_leads = [
        s for s in students
        if s.get('custom_ads_comp') and s.get('custom_ads_comp').lower() == 'архів'
    ]

    print(f"  Знайдено Archive лідів: {len(archive_leads)}")

    if not archive_leads:
        print("\n  ВАЖЛИВО: Немає лідів з custom_ads_comp = 'архів'")
        print("  Можливі причини:")
        print("    1. Archive ліди дійсно відсутні в системі")
        print("    2. Використовується інше значення для архіву")
        return

    # Аналіз структури Archive лідів
    print(f"\n[3/3] Аналіз Archive лідів...")

    # Підрахувати розподіл по lead_status_id
    status_distribution = {}
    for lead in archive_leads:
        status_id = lead.get('lead_status_id')
        status_distribution[status_id] = status_distribution.get(status_id, 0) + 1

    print(f"\n  Розподіл Archive лідів по lead_status_id:")
    print(f"  {'-'*70}")
    for status_id in sorted(status_distribution.keys(), key=lambda x: (x is None, x)):
        count = status_distribution[status_id]
        percentage = count / len(archive_leads) * 100
        print(f"    lead_status_id {status_id}: {count} лідів ({percentage:.1f}%)")
    print(f"  {'-'*70}")

    # Показати перший Archive лід для аналізу
    first_archive = archive_leads[0]

    print(f"\n  Приклад Archive ліда:")
    print(f"  {'='*70}")
    print(f"    ID: {first_archive.get('id')}")
    print(f"    Name: {first_archive.get('name')}")
    print(f"    custom_ads_comp: {first_archive.get('custom_ads_comp')}")
    print(f"    lead_status_id: {first_archive.get('lead_status_id')}")
    print(f"    is_study: {first_archive.get('is_study')}")
    print(f"    study_status_id: {first_archive.get('study_status_id')}")
    print(f"    created_at: {first_archive.get('created_at')}")
    print(f"    updated_at: {first_archive.get('updated_at')}")

    # Обмежити вивід note
    note = first_archive.get('note', '')
    if note:
        print(f"    note (перші 100 символів): {note[:100]}...")
    else:
        print(f"    note: (пусто)")

    print(f"  {'='*70}")

    # Статистика по Archive лідах
    print(f"\n  Статистика Archive лідів:")
    print(f"    Всього Archive лідів: {len(archive_leads)}")
    print(f"    Відсоток від загальної кількості: {len(archive_leads) / len(students) * 100:.1f}%")

    # Перевірити чи є ліди з is_study = 1 (активні студенти)
    active_students = [
        s for s in archive_leads
        if s.get('is_study') == 1
    ]

    print(f"\n  Archive ліди що є активними студентами (is_study=1):")
    print(f"    Кількість: {len(active_students)}")
    print(f"    Відсоток: {len(active_students) / len(archive_leads) * 100:.1f}%")

    # Підсумки
    print("\n" + "="*80)
    print("РЕЗУЛЬТАТИ ДОСЛІДЖЕННЯ:")
    print("="*80)

    print(f"\n1. Archive ліди ІДЕНТИФІКУЮТЬСЯ через: custom_ads_comp = 'архів'")
    print(f"2. Кількість Archive лідів: {len(archive_leads)}")
    print(f"3. Відсоток від загальної кількості: {len(archive_leads) / len(students) * 100:.1f}%")

    print(f"\n4. ДОСТУПНА ІНФОРМАЦІЯ:")
    print(f"   - Всі стандартні поля студента (ID, name, email, phone, etc.)")
    print(f"   - lead_status_id (розподіл показано вище)")
    print(f"   - Дати створення та оновлення")
    print(f"   - Коментарі та нотатки")
    print(f"   - Статус навчання (is_study, study_status_id)")

    print(f"\n5. РЕКОМЕНДАЦІЯ:")
    if len(archive_leads) / len(students) > 0.01:  # Більше 1%
        print(f"   Archive складає {len(archive_leads) / len(students) * 100:.1f}% всіх лідів")
        print(f"   РЕКОМЕНДУЄТЬСЯ додати окрему агреговану групу 'Архів'")
        print(f"   або розподілити по існуючим групам згідно lead_status_id")
    else:
        print(f"   Archive складає менше 1% всіх лідів")
        print(f"   Можна не включати в агрегацію або додати як окрему групу")


if __name__ == "__main__":
    test_archive_custom_field()
