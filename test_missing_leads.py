"""
Тест: Почему не были получены ліди из статусов "Не розібраний", "Недодзвон" и т.д.
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


def test_leads_by_status():
    """Проверить сколько лидов в каждом статусе"""
    print("\n" + "="*80)
    print("ТЕСТ: Количество лідів по статусам")
    print("="*80)

    token = alfacrm_auth_get_token()
    base_url = os.getenv("ALFACRM_BASE_URL").rstrip('/')

    # Сначала получим все статусы
    url_statuses = f"{base_url}/v2api/lead-status/index"
    resp = requests.post(
        url_statuses,
        headers={"X-ALFACRM-TOKEN": token},
        json={},
        timeout=15
    )

    statuses_data = resp.json()
    statuses = {s['id']: s['name'] for s in statuses_data.get('items', [])}

    print(f"\nВсего статусов в API: {len(statuses)}")

    # Статусы из скриншота
    target_statuses = [
        "Не розібраний",
        "Недодзвон",
        "Недозвон 2",
        "Недозвон 3"
    ]

    # Найдем ID этих статусов
    status_ids = {}
    for sid, sname in statuses.items():
        if sname in target_statuses:
            status_ids[sid] = sname

    print(f"\nНайдено целевых статусов: {len(status_ids)}")
    for sid, sname in status_ids.items():
        print(f"  ID {sid}: {sname}")

    # Теперь попробуем получить лидов БЕЗ фильтров
    print("\n" + "="*80)
    print("ПОЛУЧЕНИЕ ЛІДІВ БЕЗ ФИЛЬТРОВ")
    print("="*80)

    url_leads = f"{base_url}/v2api/customer/index"

    resp = requests.post(
        url_leads,
        headers={"X-ALFACRM-TOKEN": token},
        json={"page": 1, "page_size": 10},
        timeout=15
    )

    data = resp.json()
    total = data.get("count", 0)
    items = data.get("items", [])

    print(f"Всего лідів (по API): {total}")
    print(f"Получено в первой странице: {len(items)}")

    # Проверим статусы первых лидов
    status_counts = {}
    for lead in items:
        status_id = lead.get("lead_status_id")
        status_name = statuses.get(status_id, f"Unknown ({status_id})")
        status_counts[status_name] = status_counts.get(status_name, 0) + 1

    print(f"\nСтатусы первых {len(items)} лідів:")
    for sname, count in sorted(status_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {sname}: {count}")

    # Теперь попробуем с фильтром по конкретному статусу
    print("\n" + "="*80)
    print("ПОЛУЧЕНИЕ ЛІДІВ С ФИЛЬТРОМ ПО СТАТУСУ")
    print("="*80)

    for sid, sname in status_ids.items():
        resp = requests.post(
            url_leads,
            headers={"X-ALFACRM-TOKEN": token},
            json={
                "lead_status_id": sid,
                "page": 1,
                "page_size": 10
            },
            timeout=15
        )

        data = resp.json()
        total = data.get("count", 0)
        items = data.get("items", [])

        print(f"\n{sname} (ID {sid}):")
        print(f"  Всего по API: {total}")
        print(f"  Получено: {len(items)}")

        if items:
            print(f"  Первый лід: {items[0].get('name')}")


def test_with_filters():
    """Попробовать разные фильтры"""
    print("\n" + "="*80)
    print("ТЕСТ РАЗЛИЧНЫХ ФИЛЬТРОВ")
    print("="*80)

    token = alfacrm_auth_get_token()
    base_url = os.getenv("ALFACRM_BASE_URL").rstrip('/')
    company_id = int(os.getenv("ALFACRM_COMPANY_ID"))

    url = f"{base_url}/v2api/customer/index"

    # Тест 1: Без фильтров
    print("\n--- Без фильтров ---")
    resp = requests.post(
        url,
        headers={"X-ALFACRM-TOKEN": token},
        json={"page": 1, "page_size": 1},
        timeout=15
    )
    print(f"Всего: {resp.json().get('count', 0)}")

    # Тест 2: С branch_ids
    print("\n--- С фильтром branch_ids ---")
    resp = requests.post(
        url,
        headers={"X-ALFACRM-TOKEN": token},
        json={"branch_ids": [company_id], "page": 1, "page_size": 1},
        timeout=15
    )
    print(f"Всего: {resp.json().get('count', 0)}")

    # Тест 3: Только студенты (is_study=1)
    print("\n--- Только студенты (is_study=1) ---")
    resp = requests.post(
        url,
        headers={"X-ALFACRM-TOKEN": token},
        json={"is_study": 1, "page": 1, "page_size": 1},
        timeout=15
    )
    print(f"Всего: {resp.json().get('count', 0)}")

    # Тест 4: Только ліди (is_study=0)
    print("\n--- Только ліди (is_study=0) ---")
    resp = requests.post(
        url,
        headers={"X-ALFACRM-TOKEN": token},
        json={"is_study": 0, "page": 1, "page_size": 1},
        timeout=15
    )
    print(f"Всего: {resp.json().get('count', 0)}")


if __name__ == "__main__":
    test_leads_by_status()
    test_with_filters()
