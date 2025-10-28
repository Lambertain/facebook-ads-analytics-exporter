"""
Тестовый скрипт для проверки получения всех лидов из AlfaCRM.
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


def test_get_leads_without_filters():
    """Получить лидов БЕЗ фильтров чтобы увидеть реальное количество"""
    print("\n" + "="*80)
    print("ТЕСТ: Получение лидов БЕЗ фильтров")
    print("="*80)

    token = alfacrm_auth_get_token()
    base_url = os.getenv("ALFACRM_BASE_URL").rstrip('/')

    url = f"{base_url}/v2api/customer/index"
    payload = {
        "page": 1,
        "page_size": 10  # Только первые 10 для теста
    }

    print(f"\nЗапрос: {url}")
    print(f"Параметры: {payload}")

    resp = requests.post(
        url,
        headers={"X-ALFACRM-TOKEN": token},
        json=payload,
        timeout=15
    )

    data = resp.json()
    items = data.get("items", [])
    total = data.get("count", 0)

    print(f"\nРезультат:")
    print(f"  Получено: {len(items)} лидов")
    print(f"  Всего в системе: {total} лидов")

    if items:
        print(f"\nПример первого лида:")
        first = items[0]
        print(f"  ID: {first.get('id')}")
        print(f"  Имя: {first.get('name')}")
        print(f"  Pipeline ID: {first.get('pipeline_id')}")
        print(f"  Lead Status ID: {first.get('lead_status_id')}")
        print(f"  Branch IDs: {first.get('branch_ids')}")
        print(f"  Company ID: {first.get('company_id')}")


def test_get_leads_with_company_filter():
    """Получить лидов с фильтром по компании"""
    print("\n" + "="*80)
    print("ТЕСТ: Получение лидов С фильтром branch_ids")
    print("="*80)

    token = alfacrm_auth_get_token()
    base_url = os.getenv("ALFACRM_BASE_URL").rstrip('/')
    company_id = int(os.getenv("ALFACRM_COMPANY_ID"))

    url = f"{base_url}/v2api/customer/index"
    payload = {
        "branch_ids": [company_id],
        "page": 1,
        "page_size": 10
    }

    print(f"\nЗапрос: {url}")
    print(f"Параметры: {payload}")

    resp = requests.post(
        url,
        headers={"X-ALFACRM-TOKEN": token},
        json=payload,
        timeout=15
    )

    data = resp.json()
    items = data.get("items", [])
    total = data.get("count", 0)

    print(f"\nРезультат:")
    print(f"  Получено: {len(items)} лидов")
    print(f"  Всего в системе: {total} лидов")


def test_get_pipelines():
    """Получить список воронок"""
    print("\n" + "="*80)
    print("ТЕСТ: Получение списка воронок")
    print("="*80)

    token = alfacrm_auth_get_token()
    base_url = os.getenv("ALFACRM_BASE_URL").rstrip('/')
    company_id = int(os.getenv("ALFACRM_COMPANY_ID"))

    # Пробуем endpoint для воронок
    url = f"{base_url}/v2api/pipeline/index"
    payload = {"branch_id": company_id}

    print(f"\nЗапрос: {url}")
    print(f"Параметры: {payload}")

    try:
        resp = requests.post(
            url,
            headers={"X-ALFACRM-TOKEN": token},
            json=payload,
            timeout=15
        )

        if resp.status_code == 200:
            data = resp.json()
            pipelines = data.get("items", [])

            print(f"\nНайдено воронок: {len(pipelines)}")

            for pipeline in pipelines:
                print(f"\n  Воронка ID {pipeline.get('id')}:")
                print(f"    Название: {pipeline.get('name')}")
                print(f"    Branch ID: {pipeline.get('branch_id')}")
        else:
            print(f"\nОшибка: {resp.status_code}")
            print(f"Ответ: {resp.text}")

    except Exception as e:
        print(f"\nОшибка: {e}")


if __name__ == "__main__":
    test_get_leads_without_filters()
    test_get_leads_with_company_filter()
    test_get_pipelines()
