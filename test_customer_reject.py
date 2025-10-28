"""
Тест: Проверить customer_reject_id вместо lead_reject_id
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


def test_customer_reject():
    """Проверить фильтр по customer_reject_id"""
    print("\n" + "="*80)
    print("ТЕСТ: Фильтр по customer_reject_id")
    print("="*80)

    token = alfacrm_auth_get_token()
    base_url = os.getenv("ALFACRM_BASE_URL").rstrip('/')
    company_id = int(os.getenv("ALFACRM_COMPANY_ID"))

    # Получим причины отказа для клиентов
    url_rejects = f"{base_url}/v2api/customer-reject/index"
    resp = requests.post(
        url_rejects,
        headers={"X-ALFACRM-TOKEN": token},
        json={},
        timeout=15
    )

    customer_rejects = resp.json().get('items', [])
    print(f"\nНайдено причин отказа клиентов: {len(customer_rejects)}")

    if not customer_rejects:
        print("Нет причин отказа клиентов!")
        return

    # Возьмем первую причину
    first_reject = customer_rejects[0]
    reject_id = first_reject.get('id')
    reject_name = first_reject.get('name')

    print(f"Первая причина: {reject_name} (ID {reject_id})")

    # Попробуем получить лидов с этой причиной
    url = f"{base_url}/v2api/customer/index"

    print(f"\n[1] Запрос С customer_reject_id={reject_id}:")
    resp = requests.post(
        url,
        headers={"X-ALFACRM-TOKEN": token},
        json={
            "customer_reject_id": reject_id,
            "page": 1,
            "page_size": 10
        },
        timeout=15
    )

    data = resp.json()
    items = data.get('items', [])

    print(f"  Получено: {len(items)} лидов")
    print(f"  count: {data.get('count', 0)}")

    if items:
        # Проверим фактическое содержимое
        with_correct_reject = 0
        for lead in items:
            if lead.get('customer_reject_id') == reject_id:
                with_correct_reject += 1

        print(f"\n  Из {len(items)} лидов:")
        print(f"    С customer_reject_id={reject_id}: {with_correct_reject}")

        # Покажем первого лида
        lead = items[0]
        print(f"\n  Первый лид:")
        print(f"    ID: {lead.get('id')}")
        print(f"    Имя: {lead.get('name')}")
        print(f"    customer_reject_id: {lead.get('customer_reject_id')}")
        print(f"    lead_reject_id: {lead.get('lead_reject_id')}")
        print(f"    is_study: {lead.get('is_study')}")


if __name__ == "__main__":
    test_customer_reject()
