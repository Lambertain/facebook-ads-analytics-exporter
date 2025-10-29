"""
Тест: Получить список филиалов (branches) и попробовать разные branch_ids
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


def test_branches():
    """Получить филиалы и попробовать разные комбинации с lead_reject_id"""
    print("\n" + "="*80)
    print("ТЕСТ: Филиалы и их влияние на фильтр lead_reject_id")
    print("="*80)

    token = alfacrm_auth_get_token()
    base_url = os.getenv("ALFACRM_BASE_URL").rstrip('/')
    company_id = int(os.getenv("ALFACRM_COMPANY_ID"))

    # Получим список филиалов
    url_branches = f"{base_url}/v2api/branch/index"

    print("\n[1] Получение списка филиалов:")
    try:
        resp = requests.post(
            url_branches,
            headers={"X-ALFACRM-TOKEN": token},
            json={},
            timeout=15
        )

        branches = resp.json().get('items', [])
        print(f"  Найдено филиалов: {len(branches)}")

        for branch in branches:
            print(f"    ID={branch.get('id')}, name={branch.get('name')}")

    except Exception as e:
        print(f"  ✗ Ошибка: {e}")
        branches = []

    print("\n" + "="*80)
    print("[2] Попробуем запросы БЕЗ branch_ids:")

    url_customers = f"{base_url}/v2api/customer/index"

    # Без branch_ids, без фильтров
    print("\n  [2.1] БЕЗ branch_ids, БЕЗ фильтров:")
    resp = requests.post(
        url_customers,
        headers={"X-ALFACRM-TOKEN": token},
        json={
            "page": 1,
            "page_size": 50
        },
        timeout=15
    )

    data = resp.json()
    items = data.get('items', [])
    count = data.get('count', 0)

    print(f"    Получено: {len(items)} лидов, count: {count}")

    # Посчитаем архивных
    archived = [l for l in items if l.get('lead_reject_id') is not None]
    print(f"    Архивных: {len(archived)}")

    if archived:
        print(f"    ✓✓✓ ЕСТЬ АРХИВНЫЕ БЕЗ branch_ids!")
        for l in archived[:3]:
            print(f"      ID={l.get('id')}, reject_id={l.get('lead_reject_id')}, branch_ids={l.get('branch_ids')}")

    # Без branch_ids, с lead_reject_id
    print("\n  [2.2] БЕЗ branch_ids, С lead_reject_id=7:")
    resp = requests.post(
        url_customers,
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

    print(f"    Получено: {len(items)} лидов")

    if items:
        # Проверим фактический reject_id
        with_reject_7 = [l for l in items if l.get('lead_reject_id') == 7]
        print(f"    С lead_reject_id=7: {len(with_reject_7)}")

        if with_reject_7:
            print(f"    ✓✓✓ ФИЛЬТР РАБОТАЕТ БЕЗ branch_ids!")
        else:
            print(f"    ✗ Фильтр не работает, первый лид:")
            lead = items[0]
            print(f"      ID={lead.get('id')}, lead_reject_id={lead.get('lead_reject_id')}")

    print("\n" + "="*80)
    print("[3] С branch_ids=[]  (пустой массив):")

    resp = requests.post(
        url_customers,
        headers={"X-ALFACRM-TOKEN": token},
        json={
            "branch_ids": [],  # ПУСТОЙ массив
            "page": 1,
            "page_size": 50
        },
        timeout=15
    )

    data = resp.json()
    items = data.get('items', [])

    print(f"  Получено: {len(items)} лидов")
    archived = [l for l in items if l.get('lead_reject_id') is not None]
    print(f"  Архивных: {len(archived)}")


if __name__ == "__main__":
    test_branches()
