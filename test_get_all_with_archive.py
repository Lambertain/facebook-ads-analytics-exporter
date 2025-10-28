"""
Тест: Получить ВСЕХ лідів включая архивных
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


def test_all_leads_with_rejects():
    """Попробовать получить архивных лідів"""
    print("\n" + "="*80)
    print("ПОЛУЧЕНИЕ АРХИВНЫХ ЛІДІВ ЧЕРЕЗ lead_reject_id")
    print("="*80)

    token = alfacrm_auth_get_token()
    base_url = os.getenv("ALFACRM_BASE_URL").rstrip('/')

    # Получим все причины отказа лидов
    url_rejects = f"{base_url}/v2api/lead-reject/index"
    resp = requests.post(
        url_rejects,
        headers={"X-ALFACRM-TOKEN": token},
        json={},
        timeout=15
    )

    lead_rejects = resp.json().get('items', [])
    print(f"\nВсего причин отказа лидов: {len(lead_rejects)}")

    # Попробуем получить количество лидов для каждой причины
    url_leads = f"{base_url}/v2api/customer/index"

    total_archived_leads = 0
    reject_stats = {}

    print("\nПроверка количества лідів по каждой причине отказа:")

    for reject in lead_rejects[:10]:  # Только первые 10 для теста
        reject_id = reject.get('id')
        reject_name = reject.get('name')

        resp = requests.post(
            url_leads,
            headers={"X-ALFACRM-TOKEN": token},
            json={
                "lead_reject_id": reject_id,
                "page": 1,
                "page_size": 1
            },
            timeout=15
        )

        data = resp.json()
        count = data.get('count', 0)
        reject_stats[reject_name] = count

        if count > 0:
            print(f"  {reject_name}: {count} лідів")

    print(f"\n{'='*80}")
    print("ПОПЫТКА ПОЛУЧИТЬ ВСЕХ ЛІДІВ БЕЗ ФИЛЬТРА ПО СТАТУСУ")
    print("="*80)

    # Попробуем без lead_status_id фильтра
    resp = requests.post(
        url_leads,
        headers={"X-ALFACRM-TOKEN": token},
        json={
            "page": 1,
            "page_size": 50
        },
        timeout=15
    )

    data = resp.json()
    items = data.get('items', [])

    print(f"\nВсего по API: {data.get('count', 0)}")
    print(f"Получено: {len(items)}")

    # Проверим есть ли среди них архивные
    archived_count = 0
    active_count = 0

    for lead in items:
        if lead.get('lead_reject_id') is not None or lead.get('customer_reject_id') is not None:
            archived_count += 1
        else:
            active_count += 1

    print(f"\nИз первых {len(items)} лідів:")
    print(f"  Активных: {active_count}")
    print(f"  Архивных: {archived_count}")

    # Попробуем исключить активных (без статуса ліда)
    print(f"\n{'='*80}")
    print("ПОПЫТКА: Только с заполненным lead_status_id")
    print("="*80)

    resp = requests.post(
        url_leads,
        headers={"X-ALFACRM-TOKEN": token},
        json={
            "page": 1,
            "page_size": 10
        },
        timeout=15
    )

    items = resp.json().get('items', [])

    for lead in items:
        print(f"\nЛід ID {lead.get('id')}:")
        print(f"  Имя: {lead.get('name')}")
        print(f"  lead_status_id: {lead.get('lead_status_id')}")
        print(f"  lead_reject_id: {lead.get('lead_reject_id')}")
        print(f"  customer_reject_id: {lead.get('customer_reject_id')}")
        print(f"  is_study: {lead.get('is_study')}")


if __name__ == "__main__":
    test_all_leads_with_rejects()
