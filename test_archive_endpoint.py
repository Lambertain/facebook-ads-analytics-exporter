"""
Тест: Поиск альтернативных endpoint для архивных лидов
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


def test_archive_endpoints():
    """Попробовать разные endpoints для архивных лидов"""
    print("\n" + "="*80)
    print("ТЕСТ: Поиск endpoint для архивных лидов")
    print("="*80)

    token = alfacrm_auth_get_token()
    base_url = os.getenv("ALFACRM_BASE_URL").rstrip('/')
    company_id = int(os.getenv("ALFACRM_COMPANY_ID"))

    # Список возможных endpoints
    endpoints = [
        "/v2api/archive/index",
        "/v2api/lead-archive/index",
        "/v2api/customer-archive/index",
        "/v2api/archived-customer/index",
        "/v2api/rejected-customer/index",
        "/v2api/customer/archive",
        "/v2api/customer/rejected",
        "/v2api/customer/deleted",
    ]

    for endpoint in endpoints:
        url = f"{base_url}{endpoint}"
        print(f"\n[{endpoint}]:")

        try:
            resp = requests.post(
                url,
                headers={"X-ALFACRM-TOKEN": token},
                json={
                    "page": 1,
                    "page_size": 10
                },
                timeout=15
            )

            if resp.status_code == 404:
                print(f"  ✗ 404 Not Found")
                continue

            if resp.status_code != 200:
                print(f"  ✗ HTTP {resp.status_code}")
                continue

            data = resp.json()

            # Проверим есть ли items
            if 'items' in data:
                items = data.get('items', [])
                count = data.get('count', 0)

                print(f"  ✓ ENDPOINT СУЩЕСТВУЕТ!")
                print(f"    items: {len(items)}, count: {count}")

                if items:
                    # Посмотрим на первый элемент
                    lead = items[0]
                    print(f"    Ключи: {list(lead.keys())[:10]}")
                    print(f"    ID: {lead.get('id')}")
                    print(f"    lead_reject_id: {lead.get('lead_reject_id')}")

                    # Посчитаем архивных
                    archived = [l for l in items if l.get('lead_reject_id') is not None]
                    if archived:
                        print(f"    ✓✓✓ ЕСТЬ АРХИВНЫЕ: {len(archived)} из {len(items)}")
                        return endpoint

        except requests.exceptions.RequestException as e:
            print(f"  ✗ Ошибка запроса: {e}")
        except Exception as e:
            print(f"  ✗ Исключение: {e}")

    print("\n" + "="*80)
    print("❌ НИ ОДИН альтернативный endpoint не найден")
    print("="*80)

    # Попробуем еще вариант - может есть специальный параметр type или filter
    print("\n" + "="*80)
    print("Попробуем параметры type/filter в customer/index:")
    print("="*80)

    url = f"{base_url}/v2api/customer/index"

    test_params = [
        {"name": "type=archive", "params": {"type": "archive"}},
        {"name": "type=archived", "params": {"type": "archived"}},
        {"name": "type=rejected", "params": {"type": "rejected"}},
        {"name": "filter=archive", "params": {"filter": "archive"}},
        {"name": "filter=archived", "params": {"filter": "archived"}},
    ]

    for test in test_params:
        print(f"\n[{test['name']}]:")

        try:
            params = test['params'].copy()
            params.update({"page": 1, "page_size": 10})

            resp = requests.post(
                url,
                headers={"X-ALFACRM-TOKEN": token},
                json=params,
                timeout=15
            )

            data = resp.json()
            items = data.get('items', [])

            print(f"  items: {len(items)}")

            if items:
                lead = items[0]
                lead_reject_id = lead.get('lead_reject_id')
                print(f"  Первый лид: ID={lead.get('id')}, reject_id={lead_reject_id}")

                archived = [l for l in items if l.get('lead_reject_id') is not None]
                if archived:
                    print(f"  ✓✓✓ ЕСТЬ АРХИВНЫЕ: {len(archived)}")

        except Exception as e:
            print(f"  ✗ Ошибка: {e}")


if __name__ == "__main__":
    test_archive_endpoints()
