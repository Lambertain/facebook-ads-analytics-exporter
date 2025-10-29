"""
Тест: Проверить фильтр is_study=0 (только лиды, не студенты)
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


def test_is_study_filter():
    """Проверить получение только лидов с is_study=0"""
    print("\n" + "="*80)
    print("ТЕСТ: Фильтр is_study=0 (только лиды)")
    print("="*80)

    token = alfacrm_auth_get_token()
    base_url = os.getenv("ALFACRM_BASE_URL").rstrip('/')

    url = f"{base_url}/v2api/customer/index"

    print("\n[1] Запрос с is_study=0:")
    resp = requests.post(
        url,
        headers={"X-ALFACRM-TOKEN": token},
        json={
            "is_study": 0,
            "page": 1,
            "page_size": 50
        },
        timeout=15
    )

    data = resp.json()
    items = data.get('items', [])
    count = data.get('count', 0)

    print(f"  Получено: {len(items)} записей")
    print(f"  count: {count}")

    if items:
        # Посчитаем архивных
        archived = [l for l in items if l.get('lead_reject_id') is not None]
        print(f"\n  Из {len(items)} лидов:")
        print(f"    С lead_reject_id != None (архивных): {len(archived)}")
        print(f"    С lead_reject_id == None (активных): {len(items) - len(archived)}")

        if archived:
            print(f"\n  ✓✓✓ ЕСТЬ АРХИВНЫЕ ЛИДЫ!")
            for lead in archived[:5]:
                print(f"    ID={lead.get('id')}, reject_id={lead.get('lead_reject_id')}, статус={lead.get('lead_status_id')}, имя={lead.get('name')}")
        else:
            print(f"\n  ✗ Архивных нет среди первых {len(items)}")

    print("\n" + "="*80)
    print("[2] Запрос с is_study=0 И lead_reject_id != null:")

    # Попробуем совместить is_study=0 с фильтром lead_reject_id
    resp = requests.post(
        url,
        headers={"X-ALFACRM-TOKEN": token},
        json={
            "is_study": 0,
            "lead_reject_id": 7,  # Проверим с конкретным reject_id
            "page": 1,
            "page_size": 50
        },
        timeout=15
    )

    data = resp.json()
    items = data.get('items', [])

    print(f"  Получено: {len(items)} записей")

    if items:
        # Проверим фактический lead_reject_id
        with_reject_7 = [l for l in items if l.get('lead_reject_id') == 7]
        print(f"  Из них с lead_reject_id=7: {len(with_reject_7)}")

        if with_reject_7:
            print(f"  ✓✓✓ ФИЛЬТР РАБОТАЕТ!")
        else:
            print(f"  ✗ Фильтр НЕ работает - все с другим reject_id")

            # Покажем что реально вернулось
            lead = items[0]
            print(f"  Первый лид: ID={lead.get('id')}, lead_reject_id={lead.get('lead_reject_id')}")


if __name__ == "__main__":
    test_is_study_filter()
