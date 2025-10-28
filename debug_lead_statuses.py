"""
Debug: Перевірка статусів лідів та воронок.
"""
import os
import sys
import requests
from pathlib import Path
from dotenv import load_dotenv
from collections import Counter

load_dotenv()

app_dir = Path(__file__).parent / "app"
sys.path.insert(0, str(app_dir))

from connectors.crm import alfacrm_auth_get_token


def debug_statuses():
    print("\n" + "="*80)
    print("DEBUG: СТАТУСИ ЛІДІВ ТА ВОРОНОК")
    print("="*80)

    token = alfacrm_auth_get_token()
    base_url = os.getenv("ALFACRM_BASE_URL").rstrip('/')
    company_id = int(os.getenv("ALFACRM_COMPANY_ID"))

    # 1. Получаем статусы из API
    print("\n[1/3] Отримання статусів з API...")
    try:
        url = f"{base_url}/v2api/lead-status/index"
        payload = {"branch_id": company_id}

        resp = requests.post(
            url,
            headers={"X-ALFACRM-TOKEN": token},
            json=payload,
            timeout=15
        )
        resp.raise_for_status()
        data = resp.json()

        statuses = data.get("items", [])
        print(f"  ✓ Отримано {len(statuses)} статусів")

        print("\n  Статуси:")
        for status in statuses[:10]:
            print(f"    ID: {status.get('id'):3} | Pipeline: {status.get('pipeline_id', 'N/A'):3} | Назва: {status.get('name')}")

        if len(statuses) > 10:
            print(f"    ... та ще {len(statuses) - 10} статусів")

    except Exception as e:
        print(f"  ✗ Помилка: {e}")
        statuses = []

    # 2. Получаем всех лидов
    print("\n[2/3] Отримання лідів...")
    url = f"{base_url}/v2api/customer/index"
    payload = {
        "branch_ids": [company_id],
        "page": 1,
        "page_size": 100
    }

    try:
        resp = requests.post(
            url,
            headers={"X-ALFACRM-TOKEN": token},
            json=payload,
            timeout=15
        )
        resp.raise_for_status()
        data = resp.json()

        leads = data.get("items", [])
        print(f"  ✓ Отримано {len(leads)} лідів")

    except Exception as e:
        print(f"  ✗ Помилка: {e}")
        leads = []

    # 3. Анализируем статусы лидов
    print("\n[3/3] Аналіз статусів лідів...")

    # Считаем lead_status_id
    lead_status_counter = Counter(lead.get("lead_status_id") for lead in leads)
    print(f"\n  Розподіл по lead_status_id:")
    for status_id, count in lead_status_counter.most_common():
        # Находим название статуса
        status_name = "Невідомий"
        for s in statuses:
            if s.get("id") == status_id:
                status_name = s.get("name", "Невідомий")
                break
        print(f"    Status ID {status_id:3}: {count:3} лідів - {status_name}")

    # Считаем pipeline_id
    pipeline_counter = Counter(lead.get("pipeline_id") for lead in leads)
    print(f"\n  Розподіл по pipeline_id:")
    for pipeline_id, count in pipeline_counter.most_common():
        print(f"    Pipeline ID {pipeline_id}: {count} лідів")

    # Показываем примеры
    print(f"\n  Приклади лідів:")
    for i, lead in enumerate(leads[:3], 1):
        print(f"\n  Лід #{i}:")
        print(f"    ID: {lead.get('id')}")
        print(f"    Ім'я: {lead.get('name')}")
        print(f"    lead_status_id: {lead.get('lead_status_id')}")
        print(f"    pipeline_id: {lead.get('pipeline_id')}")
        print(f"    study_status_id: {lead.get('study_status_id')}")

    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    debug_statuses()
