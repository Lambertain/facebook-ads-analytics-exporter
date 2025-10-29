"""
Тест: Получить ВСЕХ лидов и отфильтровать локально по lead_reject_id
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


def test_get_all_and_filter():
    """Получить ВСЕХ лидов (без фильтра) и посмотреть сколько архивных"""
    print("\n" + "="*80)
    print("ТЕСТ: Получить ВСЕХ лидов и посмотреть архивных")
    print("="*80)

    token = alfacrm_auth_get_token()
    base_url = os.getenv("ALFACRM_BASE_URL").rstrip('/')

    url = f"{base_url}/v2api/customer/index"

    all_leads = []
    archived_leads = []

    print("\nПолучение первых 4 страниц (200 лидов):")

    for page in range(1, 5):
        resp = requests.post(
            url,
            headers={"X-ALFACRM-TOKEN": token},
            json={
                # БЕЗ ФИЛЬТРОВ - получаем ВСЕХ
                "page": page,
                "page_size": 50
            },
            timeout=15
        )

        items = resp.json().get('items', [])
        all_leads.extend(items)

        # Считаем архивных на этой странице
        page_archived = [l for l in items if l.get('lead_reject_id') is not None]
        archived_leads.extend(page_archived)

        print(f"  Страница {page}: {len(items)} лидов, архивных: {len(page_archived)}")

    print(f"\nВСЕГО лидов: {len(all_leads)}")
    print(f"Из них архивных (lead_reject_id != None): {len(archived_leads)}")

    if archived_leads:
        print(f"\n✓ ЕСТЬ АРХИВНЫЕ ЛИДЫ!")
        # Покажем первые 5
        print(f"\nПервые 5 архивных лидов:")
        for lead in archived_leads[:5]:
            print(f"  ID={lead.get('id')}, lead_reject_id={lead.get('lead_reject_id')}, имя={lead.get('name')}")
    else:
        print(f"\n✗ Нет архивных лидов среди первых {len(all_leads)}")


if __name__ == "__main__":
    test_get_all_and_filter()
