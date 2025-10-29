"""
Тест: Попробовать разные параметры для получения архивных лидов
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
    """Попробовать разные комбинации параметров"""
    print("\n" + "="*80)
    print("ТЕСТ: Поиск правильного параметра для архивных лидов")
    print("="*80)

    token = alfacrm_auth_get_token()
    base_url = os.getenv("ALFACRM_BASE_URL").rstrip('/')
    company_id = int(os.getenv("ALFACRM_COMPANY_ID"))

    url = f"{base_url}/v2api/customer/index"

    # Список параметров для тестирования
    test_cases = [
        {"name": "archived=1", "params": {"archived": 1, "page": 1, "page_size": 50}},
        {"name": "archived=true", "params": {"archived": True, "page": 1, "page_size": 50}},
        {"name": "is_archived=1", "params": {"is_archived": 1, "page": 1, "page_size": 50}},
        {"name": "is_archive=1", "params": {"is_archive": 1, "page": 1, "page_size": 50}},
        {"name": "archive=1", "params": {"archive": 1, "page": 1, "page_size": 50}},
        {"name": "status=archived", "params": {"status": "archived", "page": 1, "page_size": 50}},
        {"name": "is_study=0 + archived=1", "params": {"is_study": 0, "archived": 1, "page": 1, "page_size": 50}},
        {"name": "branch_ids + archived=1", "params": {"branch_ids": [company_id], "archived": 1, "page": 1, "page_size": 50}},
        {"name": "rejected=1", "params": {"rejected": 1, "page": 1, "page_size": 50}},
        {"name": "is_rejected=1", "params": {"is_rejected": 1, "page": 1, "page_size": 50}},
    ]

    for test_case in test_cases:
        name = test_case["name"]
        params = test_case["params"]

        print(f"\n[{name}]:")

        try:
            resp = requests.post(
                url,
                headers={"X-ALFACRM-TOKEN": token},
                json=params,
                timeout=15
            )

            if resp.status_code != 200:
                print(f"  ✗ Ошибка HTTP {resp.status_code}")
                continue

            data = resp.json()
            items = data.get('items', [])
            count = data.get('count', 0)

            print(f"  Получено: {len(items)} лидов, count: {count}")

            if items:
                # Проверим первого лида
                lead = items[0]
                lead_reject_id = lead.get('lead_reject_id')
                is_study = lead.get('is_study')

                print(f"  Первый лид: ID={lead.get('id')}, lead_reject_id={lead_reject_id}, is_study={is_study}")

                # Посчитаем архивных
                archived = [l for l in items if l.get('lead_reject_id') is not None]
                if archived:
                    print(f"  ✓✓✓ ЕСТЬ АРХИВНЫЕ: {len(archived)} из {len(items)}")
                    for l in archived[:3]:
                        print(f"    ID={l.get('id')}, reject_id={l.get('lead_reject_id')}, имя={l.get('name')}")

                    # НАШЛИ!
                    print(f"\n  {'='*70}")
                    print(f"  🎯 НАШЛИ РАБОЧИЙ ПАРАМЕТР: {name}")
                    print(f"  {'='*70}")
                    return
                else:
                    print(f"  ✗ Все с lead_reject_id=None")

        except Exception as e:
            print(f"  ✗ Исключение: {e}")

    print("\n" + "="*80)
    print("❌ НИ ОДИН параметр не сработал")
    print("="*80)


if __name__ == "__main__":
    test_archive_params()
