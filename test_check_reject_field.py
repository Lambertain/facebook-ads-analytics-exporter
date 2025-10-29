"""
Тест: Проверить РЕАЛЬНО ли лиды с lead_reject_id фильтром имеют этот reject_id
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


def test_check_reject_field():
    """Проверить имеют ли полученные лиды правильный lead_reject_id"""
    print("\n" + "="*80)
    print("ТЕСТ: Проверка поля lead_reject_id у полученных лидов")
    print("="*80)

    token = alfacrm_auth_get_token()
    base_url = os.getenv("ALFACRM_BASE_URL").rstrip('/')

    # Получим первую причину отказа
    url_rejects = f"{base_url}/v2api/lead-reject/index"
    resp = requests.post(
        url_rejects,
        headers={"X-ALFACRM-TOKEN": token},
        json={},
        timeout=15
    )

    lead_rejects = resp.json().get('items', [])

    if not lead_rejects:
        print("Нет причин отказа!")
        return

    # Возьмем последнюю причину (как в оригинальном тесте)
    test_reject = lead_rejects[-1]
    reject_id = test_reject.get('id')
    reject_name = test_reject.get('name')

    print(f"\nТестируем причину отказа: {reject_name} (ID {reject_id})")

    # Получим лидов с этим reject_id БЕЗ branch_ids
    url = f"{base_url}/v2api/customer/index"

    resp = requests.post(
        url,
        headers={"X-ALFACRM-TOKEN": token},
        json={
            "lead_reject_id": reject_id,
            "page": 1,
            "page_size": 50
        },
        timeout=15
    )

    data = resp.json()
    items = data.get('items', [])
    count = data.get('count', 0)

    print(f"\nПолучено: {len(items)} лидов")
    print(f"count: {count}")

    if items:
        # Проверим РЕАЛЬНО ли у них lead_reject_id = reject_id
        correct_reject = 0
        null_reject = 0
        other_reject = 0

        for lead in items:
            lead_reject = lead.get('lead_reject_id')
            if lead_reject == reject_id:
                correct_reject += 1
            elif lead_reject is None:
                null_reject += 1
            else:
                other_reject += 1

        print(f"\nИз {len(items)} лидов:")
        print(f"  С lead_reject_id={reject_id}: {correct_reject}")
        print(f"  С lead_reject_id=None: {null_reject}")
        print(f"  С другим lead_reject_id: {other_reject}")

        # Покажем первого лида
        lead = items[0]
        print(f"\nПервый лид:")
        print(f"  ID: {lead.get('id')}")
        print(f"  Имя: {lead.get('name')}")
        print(f"  lead_reject_id: {lead.get('lead_reject_id')}")
        print(f"  lead_status_id: {lead.get('lead_status_id')}")
        print(f"  is_study: {lead.get('is_study')}")


if __name__ == "__main__":
    test_check_reject_field()
