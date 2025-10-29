"""
Тест: Работает ли пагинация БЕЗ фильтра lead_reject_id
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


def test_pagination_without_filter():
    """Проверить что пагинация возвращает РАЗНЫХ лидов даже с фильтром"""
    print("\n" + "="*80)
    print("ТЕСТ: Пагинация С фильтром lead_reject_id")
    print("="*80)

    token = alfacrm_auth_get_token()
    base_url = os.getenv("ALFACRM_BASE_URL").rstrip('/')

    url = f"{base_url}/v2api/customer/index"

    all_ids = set()

    print("\nПолучение первых 3 страниц С фильтром lead_reject_id=7:")

    for page in range(1, 4):
        resp = requests.post(
            url,
            headers={"X-ALFACRM-TOKEN": token},
            json={
                "lead_reject_id": 7,  # Фильтр который не работает
                "page": page,
                "page_size": 50
            },
            timeout=15
        )

        items = resp.json().get('items', [])
        page_ids = {lead.get('id') for lead in items}
        new_ids = page_ids - all_ids
        all_ids.update(page_ids)

        print(f"  Страница {page}: {len(items)} лидов, новых: {len(new_ids)}, всего уникальных: {len(all_ids)}")

        if len(items) > 0:
            # Проверим lead_reject_id первого лида
            lead = items[0]
            print(f"    Первый лид: ID={lead.get('id')}, lead_reject_id={lead.get('lead_reject_id')}")

    print(f"\nВСЕГО уникальных лидов: {len(all_ids)}")

    if len(all_ids) > 50:
        print(f"✓ Пагинация РАБОТАЕТ - получили {len(all_ids)} уникальных лидов")
    else:
        print(f"✗ Пагинация НЕ РАБОТАЕТ - только {len(all_ids)} уникальных лидов")


if __name__ == "__main__":
    test_pagination_without_filter()
