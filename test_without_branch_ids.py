"""
Тест: Работает ли lead_reject_id фильтр БЕЗ branch_ids
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


def test_without_branch_ids():
    """Проверить работает ли фильтр lead_reject_id БЕЗ branch_ids"""
    print("\n" + "="*80)
    print("ТЕСТ: Фильтр lead_reject_id БЕЗ branch_ids")
    print("="*80)

    token = alfacrm_auth_get_token()
    base_url = os.getenv("ALFACRM_BASE_URL").rstrip('/')

    # Получим первую причину отказа
    url_rejects = f"{base_url}/v2api/lead-reject/index"
    resp = requests.post(
        url_rejects,
        headers={"X-ALFACRM-TOKEN": token},
        json={},
        timeout=15
    )

    lead_rejects = resp.json().get('items', [])

    if not lead_rejects:
        print("Нет причин отказа!")
        return

    first_reject = lead_rejects[0]
    reject_id = first_reject.get('id')
    reject_name = first_reject.get('name')

    print(f"\nПричина отказа: {reject_name} (ID {reject_id})")

    # Запрос БЕЗ branch_ids
    url = f"{base_url}/v2api/customer/index"

    print(f"\n[1] Запрос С lead_reject_id={reject_id}, БЕЗ branch_ids:")
    resp = requests.post(
        url,
        headers={"X-ALFACRM-TOKEN": token},
        json={
            "lead_reject_id": reject_id,
            "page": 1,
            "page_size": 10
        },
        timeout=15
    )

    data = resp.json()
    items = data.get('items', [])

    print(f"  Получено лидов: {len(items)}")
    print(f"  count: {data.get('count', 0)}")

    if items:
        lead = items[0]
        print(f"\n  Первый лид:")
        print(f"    ID: {lead.get('id')}")
        print(f"    Имя: {lead.get('name')}")
        print(f"    lead_reject_id: {lead.get('lead_reject_id')}")
        print(f"    customer_reject_id: {lead.get('customer_reject_id')}")
        print(f"    lead_status_id: {lead.get('lead_status_id')}")

        # Проверим все лиды
        with_reject = sum(1 for l in items if l.get('lead_reject_id') == reject_id)
        with_customer_reject = sum(1 for l in items if l.get('customer_reject_id') is not None)

        print(f"\n  Из {len(items)} лидов:")
        print(f"    С lead_reject_id={reject_id}: {with_reject}")
        print(f"    С customer_reject_id!=null: {with_customer_reject}")


if __name__ == "__main__":
    test_without_branch_ids()
