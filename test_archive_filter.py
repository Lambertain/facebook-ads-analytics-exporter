"""
Тест: Найти параметр для получения АРХИВНЫХ лідів
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


def test_archive_params():
    """Попробовать разные параметры для архива"""
    print("\n" + "="*80)
    print("ПОИСК ПАРАМЕТРА ДЛЯ ПОЛУЧЕНИЯ АРХИВНЫХ ЛІДІВ")
    print("="*80)

    token = alfacrm_auth_get_token()
    base_url = os.getenv("ALFACRM_BASE_URL").rstrip('/')

    url = f"{base_url}/v2api/customer/index"

    # Базовый запрос
    print("\n--- Без параметров архива ---")
    resp = requests.post(
        url,
        headers={"X-ALFACRM-TOKEN": token},
        json={"page": 1, "page_size": 1},
        timeout=15
    )
    data = resp.json()
    print(f"Всего: {data.get('count', 0)}")
    if data.get('items'):
        lead = data['items'][0]
        print(f"Пример: {lead.get('name')}, lead_reject_id={lead.get('lead_reject_id')}, customer_reject_id={lead.get('customer_reject_id')}")

    # Попробуем разные параметры
    test_params = [
        {"archived": True},
        {"archived": 1},
        {"is_archive": True},
        {"is_archive": 1},
        {"archive": True},
        {"archive": 1},
        {"lead_reject_id": {"$ne": None}},  # Not null
        {"customer_reject_id": {"$ne": None}},  # Not null
        {"status": "archive"},
        {"state": "archive"},
    ]

    for params in test_params:
        params_copy = {"page": 1, "page_size": 1, **params}

        print(f"\n--- С параметром {params} ---")

        try:
            resp = requests.post(
                url,
                headers={"X-ALFACRM-TOKEN": token},
                json=params_copy,
                timeout=15
            )

            if resp.status_code == 200:
                data = resp.json()
                print(f"Всего: {data.get('count', 0)}")

                if data.get('items'):
                    lead = data['items'][0]
                    print(f"Пример: {lead.get('name')}")
                    print(f"  lead_reject_id: {lead.get('lead_reject_id')}")
                    print(f"  customer_reject_id: {lead.get('customer_reject_id')}")
                    print(f"  lead_status_id: {lead.get('lead_status_id')}")
            else:
                print(f"Ошибка: {resp.status_code}")
                print(f"Ответ: {resp.text[:200]}")
        except Exception as e:
            print(f"Исключение: {e}")


def test_reject_filters():
    """Попробовать фильтровать по причинам отказа"""
    print("\n" + "="*80)
    print("ФИЛЬТР ПО ПРИЧИНАМ ОТКАЗА (reject)")
    print("="*80)

    token = alfacrm_auth_get_token()
    base_url = os.getenv("ALFACRM_BASE_URL").rstrip('/')

    # Получим список причин отказа
    try:
        url_rejects = f"{base_url}/v2api/customer-reject/index"
        resp = requests.post(
            url_rejects,
            headers={"X-ALFACRM-TOKEN": token},
            json={},
            timeout=15
        )

        if resp.status_code == 200:
            rejects = resp.json().get('items', [])
            print(f"\nНайдено причин отказа клиентов: {len(rejects)}")
            for reject in rejects[:5]:
                print(f"  ID {reject.get('id')}: {reject.get('name')}")
        else:
            print(f"Endpoint customer-reject недоступен: {resp.status_code}")
    except Exception as e:
        print(f"Ошибка при получении причин отказа: {e}")

    # Попробуем аналогично для лидов
    try:
        url_lead_rejects = f"{base_url}/v2api/lead-reject/index"
        resp = requests.post(
            url_lead_rejects,
            headers={"X-ALFACRM-TOKEN": token},
            json={},
            timeout=15
        )

        if resp.status_code == 200:
            rejects = resp.json().get('items', [])
            print(f"\nНайдено причин отказа лидов: {len(rejects)}")
            for reject in rejects[:5]:
                print(f"  ID {reject.get('id')}: {reject.get('name')}")

            # Теперь попробуем получить лидов с этими причинами отказа
            if rejects:
                first_reject_id = rejects[0].get('id')
                print(f"\n--- Ліди с lead_reject_id={first_reject_id} ---")

                url_leads = f"{base_url}/v2api/customer/index"
                resp = requests.post(
                    url_leads,
                    headers={"X-ALFACRM-TOKEN": token},
                    json={
                        "lead_reject_id": first_reject_id,
                        "page": 1,
                        "page_size": 10
                    },
                    timeout=15
                )

                data = resp.json()
                print(f"Всего лідів: {data.get('count', 0)}")
                print(f"Получено: {len(data.get('items', []))}")
        else:
            print(f"Endpoint lead-reject недоступен: {resp.status_code}")
    except Exception as e:
        print(f"Ошибка при получении причин отказа лидов: {e}")


if __name__ == "__main__":
    test_archive_params()
    test_reject_filters()
