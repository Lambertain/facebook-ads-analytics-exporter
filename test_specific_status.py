"""
Тест: Получить лидов по конкретным статусам из архивной вкладки
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


def test_specific_statuses():
    """Получить лидов по статусам из архивной вкладки"""
    print("\n" + "="*80)
    print("ТЕСТ: Получение лидов по статусам из архивной вкладки")
    print("="*80)

    token = alfacrm_auth_get_token()
    base_url = os.getenv("ALFACRM_BASE_URL").rstrip('/')
    company_id = int(os.getenv("ALFACRM_COMPANY_ID"))

    url = f"{base_url}/v2api/customer/index"

    # Статусы из архивной вкладки на скриншоте:
    # ID=13: "Не розібраний" (Не разобрано)
    # ID=11: "Недодзвон"
    # ID=10: "Недозвон 2"
    # ID=27: "Недозвон 3"

    test_statuses = [
        (13, "Не розібраний"),
        (11, "Недодзвон"),
        (10, "Недозвон 2"),
        (27, "Недозвон 3"),
    ]

    for status_id, status_name in test_statuses:
        print(f"\n[Статус: {status_name} (ID={status_id})]:")

        resp = requests.post(
            url,
            headers={"X-ALFACRM-TOKEN": token},
            json={
                "is_study": 0,  # Только лиды
                "lead_status_id": status_id,
                "branch_ids": [company_id],
                "page": 1,
                "page_size": 100
            },
            timeout=15
        )

        data = resp.json()
        items = data.get('items', [])
        count = data.get('count', 0)

        print(f"  Получено: {len(items)} лидов, count: {count}")

        if items:
            # Посмотрим на первого лида
            lead = items[0]
            print(f"  Первый лид: ID={lead.get('id')}, lead_reject_id={lead.get('lead_reject_id')}")

            # Посчитаем архивных
            archived = [l for l in items if l.get('lead_reject_id') is not None]
            if archived:
                print(f"  ✓✓✓ ЕСТЬ АРХИВНЫЕ: {len(archived)} из {len(items)}")
                for l in archived[:3]:
                    print(f"    ID={l.get('id')}, reject_id={l.get('lead_reject_id')}, имя={l.get('name')}")
            else:
                print(f"  ✗ Все с lead_reject_id=None")

    print("\n" + "="*80)
    print("Попробуем получить ВСЕХ лидов с is_study=0 БЕЗ фильтра по статусу:")
    print("="*80)

    # Получим ВСЕ лиды без фильтра по статусу
    all_count = 0
    page = 1
    while page <= 100:
        resp = requests.post(
            url,
            headers={"X-ALFACRM-TOKEN": token},
            json={
                "is_study": 0,
                "branch_ids": [company_id],
                "page": page,
                "page_size": 500
            },
            timeout=15
        )

        data = resp.json()
        items = data.get('items', [])

        if not items:
            break

        all_count += len(items)
        page += 1

        # Посчитаем архивных
        archived = [l for l in items if l.get('lead_reject_id') is not None]
        if archived:
            print(f"  Страница {page-1}: ЕСТЬ {len(archived)} АРХИВНЫХ!")
            for l in archived[:3]:
                print(f"    ID={l.get('id')}, reject_id={l.get('lead_reject_id')}")
            break

    print(f"\nВсего лидов (is_study=0): {all_count}")


if __name__ == "__main__":
    test_specific_statuses()
