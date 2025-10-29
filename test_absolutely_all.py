"""
Тест: Получить ВООБЩЕ ВСЕ записи без фильтров
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import requests

load_dotenv()

app_dir = Path(__file__).parent / "app"
sys.path.insert(0, str(app_dir))

from connectors.crm import alfacrm_auth_get_token


def test_absolutely_all():
    """Получить ВСЕ записи без ВООБЩЕ НИКАКИХ фильтров"""
    print("\n" + "="*80)
    print("ТЕСТ: ВСЕ записи БЕЗ ФИЛЬТРОВ (is_study=2, без branch_ids)")
    print("="*80)

    token = alfacrm_auth_get_token()
    base_url = os.getenv("ALFACRM_BASE_URL").rstrip('/')

    url = f"{base_url}/v2api/customer/index"

    all_records = []
    archived_count = 0

    print("\nПолучение ВСЕХ записей (лиды + студенты):")

    for page in range(1, 100):
        resp = requests.post(
            url,
            headers={"X-ALFACRM-TOKEN": token},
            json={
                "is_study": 2,  # И лиды И студенты
                # НЕТ branch_ids!
                # НЕТ ВООБЩЕ НИКАКИХ фильтров!
                "page": page,
                "page_size": 500
            },
            timeout=15
        )

        data = resp.json()
        items = data.get('items', [])

        if not items:
            print(f"  Страница {page}: пусто, останавливаемся")
            break

        all_records.extend(items)

        # Проверим архивных
        page_with_lead_reject = [l for l in items if l.get('lead_reject_id') is not None]
        page_with_customer_reject = [l for l in items if l.get('customer_reject_id') is not None]

        archived_this_page = len(page_with_lead_reject) + len(page_with_customer_reject)
        archived_count += archived_this_page

        if archived_this_page > 0:
            print(f"  Страница {page}: {len(items)} записей, АРХИВНЫХ: {archived_this_page} 🎯")
            if page_with_lead_reject:
                print(f"    С lead_reject_id: {len(page_with_lead_reject)}")
                for l in page_with_lead_reject[:2]:
                    print(f"      ID={l.get('id')}, reject_id={l.get('lead_reject_id')}, is_study={l.get('is_study')}")
            if page_with_customer_reject:
                print(f"    С customer_reject_id: {len(page_with_customer_reject)}")
                for l in page_with_customer_reject[:2]:
                    print(f"      ID={l.get('id')}, reject_id={l.get('customer_reject_id')}, is_study={l.get('is_study')}")
        else:
            if page % 5 == 0:  # Выводим каждую 5-ю страницу
                print(f"  Страница {page}: {len(items)} записей, архивных: 0")

    print(f"\n{'='*80}")
    print(f"ИТОГО записей получено: {len(all_records)}")
    print(f"Из них архивных: {archived_count}")
    print(f"{'='*80}")

    # Разбивка по is_study
    leads = [r for r in all_records if r.get('is_study') == 0]
    students = [r for r in all_records if r.get('is_study') == 1]

    print(f"\nРазбивка:")
    print(f"  Лиды (is_study=0): {len(leads)}")
    print(f"  Студенты (is_study=1): {len(students)}")

    # Архивные среди лидов и студентов
    archived_leads = [r for r in leads if r.get('lead_reject_id') is not None or r.get('customer_reject_id') is not None]
    archived_students = [r for r in students if r.get('lead_reject_id') is not None or r.get('customer_reject_id') is not None]

    print(f"\n  Архивных среди лидов: {len(archived_leads)}")
    print(f"  Архивных среди студентов: {len(archived_students)}")

    if archived_count > 0:
        print(f"\n🎯🎯🎯 НАШЛИ {archived_count} АРХИВНЫХ!")
    else:
        print(f"\n❌ Архивных НЕ НАЙДЕНО среди {len(all_records)} записей")


if __name__ == "__main__":
    test_absolutely_all()
