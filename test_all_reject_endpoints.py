"""
Тест: Все возможные варианты reject endpoints
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


def test_all_reject_endpoints():
    """Попробовать все варианты reject endpoints"""
    print("\n" + "="*80)
    print("ТЕСТ: Все варианты reject endpoints")
    print("="*80)

    token = alfacrm_auth_get_token()
    base_url = os.getenv("ALFACRM_BASE_URL").rstrip('/')

    # Все возможные комбинации
    paths = [
        # v2api варианты
        "/v2api/lead/reject",
        "/v2api/customer/reject",
        "/v2api/leadreject/index",
        "/v2api/customerreject/index",
        "/v2api/rejected-lead/index",
        "/v2api/rejected-customer/index",
        # api/v2 варианты
        "/api/v2/lead/reject",
        "/api/v2/customer/reject",
        "/api/v2/leadreject/index",
        "/api/v2/customerreject/index",
    ]

    for path in paths:
        url = f"{base_url}{path}"
        print(f"\n[{path}]:")

        # POST запрос
        try:
            resp = requests.post(
                url,
                headers={"X-ALFACRM-TOKEN": token},
                json={"page": 1, "page_size": 10},
                timeout=15
            )

            if resp.status_code == 404:
                print(f"  404")
                continue

            if resp.status_code != 200:
                print(f"  HTTP {resp.status_code}")
                continue

            data = resp.json()

            if isinstance(data, dict):
                items = data.get('items', data.get('data', []))
                count = data.get('count', data.get('total', 0))
            elif isinstance(data, list):
                items = data
                count = len(data)
            else:
                items = []
                count = 0

            print(f"  ✓ РАБОТАЕТ! items: {len(items)}, count: {count}")

            if items:
                lead = items[0]
                print(f"    ID: {lead.get('id')}")
                print(f"    lead_reject_id: {lead.get('lead_reject_id')}")
                print(f"    customer_reject_id: {lead.get('customer_reject_id')}")

                # Посчитаем с reject_id
                with_lead_reject = [l for l in items if l.get('lead_reject_id') is not None]
                with_customer_reject = [l for l in items if l.get('customer_reject_id') is not None]

                if with_lead_reject:
                    print(f"    🎯 С lead_reject_id: {len(with_lead_reject)}")
                if with_customer_reject:
                    print(f"    🎯 С customer_reject_id: {len(with_customer_reject)}")

                if with_lead_reject or with_customer_reject:
                    print(f"\n  {'='*70}")
                    print(f"  🎯🎯🎯 НАЙДЕН РАБОЧИЙ ENDPOINT: {path}")
                    print(f"  {'='*70}")
                    return url

        except Exception as e:
            print(f"  ✗ Ошибка: {e}")

    print("\n" + "="*80)
    print("❌ Ни один reject endpoint не найден")
    print("="*80)


if __name__ == "__main__":
    result = test_all_reject_endpoints()
    if result:
        print(f"\n🎯 РАБОЧИЙ ENDPOINT: {result}")
