"""
Тест: Посмотреть все статусы лидов и попробовать найти "архивные"
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


def test_lead_statuses():
    """Получить все статусы лидов и проверить фильтрацию по ним"""
    print("\n" + "="*80)
    print("ТЕСТ: Статусы лидов и фильтрация по ним")
    print("="*80)

    token = alfacrm_auth_get_token()
    base_url = os.getenv("ALFACRM_BASE_URL").rstrip('/')

    # Получим все статусы лидов
    url_statuses = f"{base_url}/v2api/lead-status/index"
    resp = requests.post(
        url_statuses,
        headers={"X-ALFACRM-TOKEN": token},
        json={},
        timeout=15
    )

    statuses = resp.json().get('items', [])
    print(f"\nВсего статусов лидов: {len(statuses)}\n")

    for status in statuses:
        status_id = status.get('id')
        status_name = status.get('name')
        print(f"  ID={status_id}: {status_name}")

    print("\n" + "="*80)
    print("Проверим фильтрацию по каждому статусу")
    print("="*80)

    url_customers = f"{base_url}/v2api/customer/index"

    for status in statuses[:5]:  # Проверим первые 5 статусов
        status_id = status.get('id')
        status_name = status.get('name')

        resp = requests.post(
            url_customers,
            headers={"X-ALFACRM-TOKEN": token},
            json={
                "lead_status_id": status_id,
                "page": 1,
                "page_size": 10
            },
            timeout=15
        )

        data = resp.json()
        items = data.get('items', [])
        count = data.get('count', 0)

        print(f"\nСтатус '{status_name}' (ID={status_id}):")
        print(f"  Получено: {len(items)} лидов, count: {count}")

        if items:
            # Проверим первого лида
            lead = items[0]
            print(f"  Первый лид: ID={lead.get('id')}, lead_status_id={lead.get('lead_status_id')}, lead_reject_id={lead.get('lead_reject_id')}")

            # Посчитаем архивных
            archived = [l for l in items if l.get('lead_reject_id') is not None]
            if archived:
                print(f"  ✓✓✓ ЕСТЬ АРХИВНЫЕ: {len(archived)} из {len(items)}")
                for l in archived[:3]:
                    print(f"    ID={l.get('id')}, reject_id={l.get('lead_reject_id')}")


if __name__ == "__main__":
    test_lead_statuses()
