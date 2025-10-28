"""
Тест: Почему архивные лиды не добавляются - проверка дубликатов ID
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


def test_duplicate_ids():
    """Проверить есть ли общие ID между активными и архивными лидами"""
    print("\n" + "="*80)
    print("ТЕСТ: Проверка дубликатов ID между активными и архивными лидами")
    print("="*80)

    token = alfacrm_auth_get_token()
    base_url = os.getenv("ALFACRM_BASE_URL").rstrip('/')
    company_id = int(os.getenv("ALFACRM_COMPANY_ID"))

    # 1. Получим ID активных лидов
    url = f"{base_url}/v2api/customer/index"

    print("\n[1] Получение активных лидов...")
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

    active_leads = resp.json().get('items', [])
    active_ids = {lead.get('id') for lead in active_leads}
    print(f"  Получено {len(active_leads)} активных лидов")
    print(f"  Первые 5 ID: {list(active_ids)[:5]}")

    # 2. Получим первую причину отказа
    print("\n[2] Получение причин отказа...")
    url_rejects = f"{base_url}/v2api/lead-reject/index"
    resp = requests.post(
        url_rejects,
        headers={"X-ALFACRM-TOKEN": token},
        json={},
        timeout=15
    )

    lead_rejects = resp.json().get('items', [])
    print(f"  Найдено {len(lead_rejects)} причин отказа")

    if not lead_rejects:
        print("  ✗ Нет причин отказа!")
        return

    first_reject = lead_rejects[0]
    reject_id = first_reject.get('id')
    reject_name = first_reject.get('name')

    print(f"  Первая причина: {reject_name} (ID {reject_id})")

    # 3. Получим лидов с этой причиной отказа
    print(f"\n[3] Получение архивных лидов для reject_id={reject_id}...")
    resp = requests.post(
        url,
        headers={"X-ALFACRM-TOKEN": token},
        json={
            "lead_reject_id": reject_id,
            "branch_ids": [company_id],
            "page": 1,
            "page_size": 100
        },
        timeout=15
    )

    archived_leads = resp.json().get('items', [])
    archived_ids = {lead.get('id') for lead in archived_leads}

    print(f"  Получено {len(archived_leads)} архивных лидов")
    print(f"  Первые 5 ID: {list(archived_ids)[:5]}")

    # 4. Проверим пересечения
    print(f"\n[4] Проверка пересечений...")
    common_ids = active_ids & archived_ids

    print(f"\n  Общих ID: {len(common_ids)}")

    if common_ids:
        print(f"  ❗ ПРОБЛЕМА: {len(common_ids)} лидов есть И в активных И в архивных!")
        print(f"  Первые 5 общих ID: {list(common_ids)[:5]}")

        # Проверим один общий лид
        if common_ids:
            common_id = list(common_ids)[0]
            for lead in active_leads:
                if lead.get('id') == common_id:
                    print(f"\n  Пример общего лида (ID {common_id}) из АКТИВНЫХ:")
                    print(f"    Имя: {lead.get('name')}")
                    print(f"    lead_reject_id: {lead.get('lead_reject_id')}")
                    print(f"    lead_status_id: {lead.get('lead_status_id')}")
                    break

            for lead in archived_leads:
                if lead.get('id') == common_id:
                    print(f"\n  Тот же лид (ID {common_id}) из АРХИВНЫХ:")
                    print(f"    Имя: {lead.get('name')}")
                    print(f"    lead_reject_id: {lead.get('lead_reject_id')}")
                    print(f"    lead_status_id: {lead.get('lead_status_id')}")
                    break
    else:
        print(f"  ✓ Нет общих ID между активными и архивными лидами")


if __name__ == "__main__":
    test_duplicate_ids()
