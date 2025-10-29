"""
Тест: Получить МНОГО лидов без фильтров и посмотреть где начинаются архивные
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


def test_get_many_without_filter():
    """Получить первые 1000 лидов без фильтров"""
    print("\n" + "="*80)
    print("ТЕСТ: Получить первые 1000 лидов БЕЗ ФИЛЬТРОВ")
    print("="*80)

    token = alfacrm_auth_get_token()
    base_url = os.getenv("ALFACRM_BASE_URL").rstrip('/')

    url = f"{base_url}/v2api/customer/index"

    all_leads = []
    archived_count = 0

    print("\nПолучение первых 20 страниц (1000 лидов):")

    for page in range(1, 21):
        resp = requests.post(
            url,
            headers={"X-ALFACRM-TOKEN": token},
            json={
                # БЕЗ ФИЛЬТРОВ ВООБЩЕ
                "page": page,
                "page_size": 50
            },
            timeout=15
        )

        data = resp.json()
        items = data.get('items', [])

        if not items:
            print(f"  Страница {page}: пусто, останавливаемся")
            break

        all_leads.extend(items)

        # Считаем архивных на этой странице
        page_archived = [l for l in items if l.get('lead_reject_id') is not None]
        archived_count += len(page_archived)

        if page_archived:
            print(f"  Страница {page}: {len(items)} лидов, архивных: {len(page_archived)} ✓✓✓")
            # Покажем первого архивного
            lead = page_archived[0]
            print(f"    Первый архивный: ID={lead.get('id')}, reject_id={lead.get('lead_reject_id')}, имя={lead.get('name')}")
        else:
            print(f"  Страница {page}: {len(items)} лидов, архивных: 0")

    print(f"\n{'='*80}")
    print(f"ИТОГО лидов получено: {len(all_leads)}")
    print(f"Из них архивных (lead_reject_id != None): {archived_count}")
    print(f"{'='*80}")

    if archived_count > 0:
        print(f"\n✓✓✓ НАЙДЕНЫ АРХИВНЫЕ ЛИДЫ!")
        # Покажем всех архивных
        archived_leads = [l for l in all_leads if l.get('lead_reject_id') is not None]
        print(f"\nВсе архивные лиды:")
        for lead in archived_leads:
            print(f"  ID={lead.get('id')}, reject_id={lead.get('lead_reject_id')}, статус={lead.get('lead_status_id')}, имя={lead.get('name')}")
    else:
        print(f"\n✗ Архивных лидов НЕ НАЙДЕНО среди первых {len(all_leads)}")


if __name__ == "__main__":
    test_get_many_without_filter()
