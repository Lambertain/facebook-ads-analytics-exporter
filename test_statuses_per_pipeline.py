"""
Тест получения статусов для каждой воронки
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


def test_get_statuses_by_pipeline():
    """Получить статусы для конкретной воронки"""
    print("\n" + "="*80)
    print("ТЕСТ: Получение статусов для каждой воронки")
    print("="*80)

    token = alfacrm_auth_get_token()
    base_url = os.getenv("ALFACRM_BASE_URL").rstrip('/')
    company_id = int(os.getenv("ALFACRM_COMPANY_ID"))

    # Проверяем воронки 0, 1, 2
    for pipeline_id in [0, 1, 2]:
        url = f"{base_url}/v2api/lead-status/index"
        payload = {
            "branch_id": company_id,
            "pipeline_id": pipeline_id
        }

        print(f"\n--- Воронка {pipeline_id} ---")
        print(f"Параметры: {payload}")

        resp = requests.post(
            url,
            headers={"X-ALFACRM-TOKEN": token},
            json=payload,
            timeout=15
        )

        data = resp.json()
        statuses = data.get("items", [])

        print(f"Найдено статусов: {len(statuses)}")

        for status in statuses[:5]:  # Показываем только первые 5
            print(f"  ID {status.get('id')}: {status.get('name')} (pipeline_id={status.get('pipeline_id')})")

        if len(statuses) > 5:
            print(f"  ... и еще {len(statuses) - 5} статусов")


if __name__ == "__main__":
    test_get_statuses_by_pipeline()
