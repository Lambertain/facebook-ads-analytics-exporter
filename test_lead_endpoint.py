"""
Тест: Проверить endpoint /v2api/lead/index вместо customer/index
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


def test_lead_endpoint():
    """Проверить endpoint lead/index"""
    print("\n" + "="*80)
    print("ТЕСТ: Endpoint /v2api/lead/index")
    print("="*80)

    token = alfacrm_auth_get_token()
    base_url = os.getenv("ALFACRM_BASE_URL").rstrip('/')

    # Попробуем endpoint lead/index
    url = f"{base_url}/v2api/lead/index"

    print("\n[1] Запрос к /v2api/lead/index без фильтров:")
    try:
        resp = requests.post(
            url,
            headers={"X-ALFACRM-TOKEN": token},
            json={
                "page": 1,
                "page_size": 50
            },
            timeout=15
        )

        if resp.status_code != 200:
            print(f"  ✗ Ошибка: статус {resp.status_code}")
            print(f"  Ответ: {resp.text}")
            return

        data = resp.json()
        items = data.get('items', [])
        count = data.get('count', 0)

        print(f"  ✓ Получено: {len(items)} записей")
        print(f"  count: {count}")

        if items:
            # Посмотрим на первый элемент
            lead = items[0]
            print(f"\n  Первый элемент:")
            print(f"    Ключи: {list(lead.keys())}")
            print(f"    ID: {lead.get('id')}")
            print(f"    Имя: {lead.get('name')}")
            print(f"    lead_reject_id: {lead.get('lead_reject_id')}")
            print(f"    lead_status_id: {lead.get('lead_status_id')}")

            # Посчитаем архивных
            archived = [l for l in items if l.get('lead_reject_id') is not None]
            print(f"\n  Архивных (lead_reject_id != None): {len(archived)}")

            if archived:
                print(f"  ✓✓✓ ЕСТЬ АРХИВНЫЕ ЛИДЫ В /v2api/lead/index!")
                for l in archived[:5]:
                    print(f"    ID={l.get('id')}, reject_id={l.get('lead_reject_id')}, имя={l.get('name')}")

    except Exception as e:
        print(f"  ✗ Исключение: {e}")

    print("\n" + "="*80)
    print("[2] Запрос к /v2api/lead/index с lead_reject_id=7:")

    try:
        resp = requests.post(
            url,
            headers={"X-ALFACRM-TOKEN": token},
            json={
                "lead_reject_id": 7,
                "page": 1,
                "page_size": 50
            },
            timeout=15
        )

        data = resp.json()
        items = data.get('items', [])

        print(f"  Получено: {len(items)} записей")

        if items:
            # Проверим фактический lead_reject_id
            with_reject_7 = [l for l in items if l.get('lead_reject_id') == 7]
            print(f"  Из них с lead_reject_id=7: {len(with_reject_7)}")

            if with_reject_7:
                print(f"  ✓✓✓ ФИЛЬТР РАБОТАЕТ В /v2api/lead/index!")

    except Exception as e:
        print(f"  ✗ Исключение: {e}")


if __name__ == "__main__":
    test_lead_endpoint()
