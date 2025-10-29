"""
Тест: ПРАВИЛЬНЫЙ endpoint для архивных лидов из документации
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


def test_correct_endpoint():
    """Использовать правильный endpoint из документации"""
    print("\n" + "="*80)
    print("ТЕСТ: ПРАВИЛЬНЫЙ endpoint /api/v2/{branch}/lead/reject")
    print("="*80)

    token = alfacrm_auth_get_token()
    base_url = os.getenv("ALFACRM_BASE_URL").rstrip('/')
    company_id = int(os.getenv("ALFACRM_COMPANY_ID"))

    # Согласно документации: GET /api/v2/{учебный_центр}/lead/reject
    # Попробуем разные варианты

    endpoints = [
        f"{base_url}/api/v2/{company_id}/lead/reject",
        f"{base_url}/api/v2/lead/reject",
        f"{base_url}/v2api/{company_id}/lead/reject",
        f"{base_url}/v2api/lead/reject",
    ]

    for endpoint in endpoints:
        print(f"\n[Тестируем: {endpoint}]")

        try:
            # Попробуем GET как в документации
            resp = requests.get(
                endpoint,
                headers={"X-ALFACRM-TOKEN": token},
                params={"limit": 50, "page": 1},
                timeout=15
            )

            print(f"  GET статус: {resp.status_code}")

            if resp.status_code == 200:
                data = resp.json()

                # Проверим структуру ответа
                if isinstance(data, dict):
                    items = data.get('items', data.get('data', []))
                    count = data.get('count', data.get('total', 0))
                elif isinstance(data, list):
                    items = data
                    count = len(data)
                else:
                    items = []
                    count = 0

                print(f"  ✓ РАБОТАЕТ! items: {len(items)}, count/total: {count}")

                if items:
                    # Посмотрим на первый элемент
                    lead = items[0]
                    print(f"  Первый лид:")
                    print(f"    ID: {lead.get('id')}")
                    print(f"    lead_reject_id: {lead.get('lead_reject_id')}")
                    print(f"    Имя: {lead.get('name')}")

                    # Посчитаем сколько с lead_reject_id
                    with_reject = [l for l in items if l.get('lead_reject_id') is not None]
                    print(f"  С lead_reject_id != None: {len(with_reject)}")

                    if with_reject:
                        print(f"  🎯🎯🎯 НАШЛИ АРХИВНЫЕ ЛИДЫ!")
                        return endpoint

            elif resp.status_code == 404:
                print(f"  ✗ 404 Not Found")

            else:
                print(f"  ✗ Статус {resp.status_code}")

        except Exception as e:
            print(f"  ✗ GET ошибка: {e}")

        # Попробуем POST
        try:
            resp = requests.post(
                endpoint,
                headers={"X-ALFACRM-TOKEN": token},
                json={"limit": 50, "page": 1},
                timeout=15
            )

            print(f"  POST статус: {resp.status_code}")

            if resp.status_code == 200:
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

                print(f"  ✓ POST РАБОТАЕТ! items: {len(items)}, count: {count}")

                if items:
                    lead = items[0]
                    print(f"  Первый лид: ID={lead.get('id')}, reject_id={lead.get('lead_reject_id')}")

                    with_reject = [l for l in items if l.get('lead_reject_id') is not None]
                    print(f"  С lead_reject_id != None: {len(with_reject)}")

                    if with_reject:
                        print(f"  🎯🎯🎯 НАШЛИ АРХИВНЫЕ ЛИДЫ ЧЕРЕЗ POST!")
                        return endpoint

        except Exception as e:
            print(f"  ✗ POST ошибка: {e}")

    print("\n" + "="*80)
    print("❌ Ни один endpoint не сработал")
    print("="*80)


if __name__ == "__main__":
    result = test_correct_endpoint()
    if result:
        print(f"\n{'='*80}")
        print(f"🎯 НАЙДЕН РАБОЧИЙ ENDPOINT: {result}")
        print(f"{'='*80}")
