"""
Знайти справжні архівні ліди.

Перевірити різні варіанти:
1. custom_ads_comp == 'архів' (як було в старій документації)
2. Інші можливі ознаки архіву
"""
import os
import sys
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

app_dir = Path(__file__).parent / "app"
sys.path.insert(0, str(app_dir))

from connectors.crm import alfacrm_auth_get_token


def find_real_archive():
    """
    Знайти справжні архівні ліди різними способами.
    """

    print("\n" + "="*80)
    print("ПОШУК СПРАВЖНІХ АРХІВНИХ ЛІДІВ")
    print("="*80)

    token = alfacrm_auth_get_token()
    base_url = os.getenv("ALFACRM_BASE_URL").rstrip('/')
    company_id = int(os.getenv("ALFACRM_COMPANY_ID"))

    # Отримати ВСІХ студентів (без фільтрації)
    print("\n[1/2] Завантаження всіх студентів без фільтрів...")

    all_students = []
    page = 1

    while True:
        url = f"{base_url}/v2api/customer/index"
        payload = {
            "branch_ids": [company_id],
            "page": page,
            "page_size": 500
        }

        try:
            resp = requests.post(
                url,
                headers={"X-ALFACRM-TOKEN": token},
                json=payload,
                timeout=15
            )
            resp.raise_for_status()
            data = resp.json()

            items = data.get("items", [])
            total = data.get("count", 0)

            print(f"  Сторінка {page}: {len(items)} студентів")

            if not items:
                break

            all_students.extend(items)

            if len(all_students) >= total:
                break

            page += 1

        except Exception as e:
            print(f"  ✗ Помилка: {e}")
            break

    print(f"\n  ✓ Всього завантажено: {len(all_students)} студентів")

    # Аналізуємо різні варіанти архіву
    print("\n[2/2] Аналіз різних ознак архіву...")
    print("="*80)

    # Варіант 1: custom_ads_comp == 'архів'
    archive_by_custom_field = [
        s for s in all_students
        if s.get("custom_ads_comp") == "архів"
    ]

    print(f"\n1. За custom_ads_comp == 'архів':")
    print(f"   Знайдено: {len(archive_by_custom_field)} лідів")

    if archive_by_custom_field:
        print(f"\n   Приклади архівних лідів:")
        for i, lead in enumerate(archive_by_custom_field[:5], 1):
            print(f"\n   Лід #{i}:")
            print(f"     ID: {lead.get('id')}")
            print(f"     Ім'я: {lead.get('name')}")
            print(f"     lead_status_id: {lead.get('lead_status_id')}")
            print(f"     study_status_id: {lead.get('study_status_id')}")
            print(f"     custom_ads_comp: {lead.get('custom_ads_comp')}")
            print(f"     Телефон: {lead.get('phone', [])}")
            print(f"     Дата створення: {lead.get('created_at')}")

    # Варіант 2: lead_status_id == 39
    archive_by_status_39 = [
        s for s in all_students
        if s.get("lead_status_id") == 39
    ]

    print(f"\n2. За lead_status_id == 39:")
    print(f"   Знайдено: {len(archive_by_status_39)} лідів")

    # Варіант 3: study_status_id
    unique_study_statuses = set(s.get("study_status_id") for s in all_students)
    print(f"\n3. Унікальні study_status_id:")
    print(f"   {sorted(unique_study_statuses)}")

    # Варіант 4: is_study == False
    not_studying = [
        s for s in all_students
        if s.get("is_study") == 0 or s.get("is_study") == False
    ]

    print(f"\n4. За is_study == False/0:")
    print(f"   Знайдено: {len(not_studying)} лідів")

    # Перевіряємо унікальні значення custom_ads_comp
    print(f"\n5. Аналіз поля custom_ads_comp:")
    custom_ads_values = {}
    for s in all_students:
        val = s.get("custom_ads_comp", "")
        if val:
            custom_ads_values[val] = custom_ads_values.get(val, 0) + 1

    print(f"   Всього унікальних значень: {len(custom_ads_values)}")
    print(f"\n   Топ-10 значень custom_ads_comp:")
    sorted_values = sorted(custom_ads_values.items(), key=lambda x: x[1], reverse=True)
    for val, count in sorted_values[:10]:
        display_val = val if len(val) <= 50 else val[:47] + "..."
        print(f"     {count:4} лідів: {display_val}")

    # Перевіряємо чи є значення 'архів'
    if 'архів' in custom_ads_values:
        print(f"\n   ✅ Знайдено 'архів': {custom_ads_values['архів']} лідів")
    else:
        print(f"\n   ❌ Значення 'архів' НЕ знайдено!")
        # Шукаємо схожі значення
        similar = [k for k in custom_ads_values.keys() if 'арх' in k.lower()]
        if similar:
            print(f"   Схожі значення: {similar}")

    # Перевіряємо всі унікальні lead_status_id
    print(f"\n6. Унікальні lead_status_id:")
    unique_lead_statuses = {}
    for s in all_students:
        status = s.get("lead_status_id")
        if status:
            unique_lead_statuses[status] = unique_lead_statuses.get(status, 0) + 1

    for status, count in sorted(unique_lead_statuses.items()):
        print(f"   status_id {status}: {count} лідів")

    # ВИСНОВОК
    print("\n" + "="*80)
    print("ВИСНОВОК:")
    print("="*80)

    if len(archive_by_custom_field) > 0:
        print(f"\n✅ АРХІВ визначається за: custom_ads_comp == 'архів'")
        print(f"   Всього архівних лідів: {len(archive_by_custom_field)}")
    elif len(archive_by_status_39) > 0:
        print(f"\n✅ АРХІВ визначається за: lead_status_id == 39")
        print(f"   Всього архівних лідів: {len(archive_by_status_39)}")
    else:
        print(f"\n❌ НЕ ЗНАЙДЕНО жодного архівного ліда!")
        print(f"   Можливо потрібен інший спосіб визначення архіву")

    print("\n" + "="*80 + "\n")

    return archive_by_custom_field if archive_by_custom_field else archive_by_status_39


if __name__ == "__main__":
    find_real_archive()
