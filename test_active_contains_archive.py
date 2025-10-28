"""
Тест: Проверить содержит ли запрос "активных" лидов АРХИВНЫЕ лиды
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


def test_active_contains_archive():
    """Проверить есть ли архивные среди активных"""
    print("\n" + "="*80)
    print("ТЕСТ: Есть ли среди 'активных' лидов архивные?")
    print("="*80)

    token = alfacrm_auth_get_token()
    base_url = os.getenv("ALFACRM_BASE_URL").rstrip('/')
    company_id = int(os.getenv("ALFACRM_COMPANY_ID"))

    # Получим первые 100 "активных" лидов
    url = f"{base_url}/v2api/customer/index"

    resp = requests.post(
        url,
        headers={"X-ALFACRM-TOKEN": token},
        json={
            "branch_ids": [company_id],
            "page": 1,
            "page_size": 100
        },
        timeout=15
    )

    data = resp.json()
    items = data.get('items', [])

    print(f"\nПолучено 'активных' лидов: {len(items)}")

    # Проверим сколько из них имеют lead_reject_id
    with_reject = 0
    without_reject = 0

    for lead in items:
        if lead.get('lead_reject_id') is not None:
            with_reject += 1
        else:
            without_reject += 1

    print(f"\nРезультат:")
    print(f"  С lead_reject_id (АРХИВНЫЕ): {with_reject}")
    print(f"  Без lead_reject_id (АКТИВНЫЕ): {without_reject}")

    if with_reject > 0:
        print(f"\n❗ ВАЖНО: Запрос БЕЗ фильтра lead_reject_id возвращает АРХИВНЫЕ лиды!")
        print(f"  Это объясняет почему архивные лиды = 0 в основном скрипте")
    else:
        print(f"\n✓ Запрос без фильтра НЕ содержит архивных лидов")


if __name__ == "__main__":
    test_active_contains_archive()
