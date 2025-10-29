"""
Тест: Проверить сколько лидов имеют заполненное поле note
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


def test_note_field():
    """Проверить лидов с заполненным полем note"""
    print("\n" + "="*80)
    print("ТЕСТ: Лиды с заполненным полем note (примітка/коментар)")
    print("="*80)

    token = alfacrm_auth_get_token()
    base_url = os.getenv("ALFACRM_BASE_URL").rstrip('/')
    company_id = int(os.getenv("ALFACRM_COMPANY_ID"))

    url = f"{base_url}/v2api/customer/index"

    all_leads = []
    with_note = 0
    with_note_and_reject = 0

    print("\nПолучение первых 10 страниц (5000 лидов):")

    for page in range(1, 11):
        resp = requests.post(
            url,
            headers={"X-ALFACRM-TOKEN": token},
            json={
                "is_study": 0,  # Только лиды
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

        all_leads.extend(items)

        # Посчитаем лидов с заполненным note
        page_with_note = [l for l in items if l.get('note')]
        with_note += len(page_with_note)

        # Посчитаем лидов с note И с lead_reject_id
        page_with_both = [l for l in items if l.get('note') and l.get('lead_reject_id')]
        with_note_and_reject += len(page_with_both)

        print(f"  Страница {page}: {len(items)} лидов")
        print(f"    С note: {len(page_with_note)}")
        print(f"    С note И reject_id: {len(page_with_both)}")

        if page_with_note:
            # Покажем первого с note
            lead = page_with_note[0]
            note = lead.get('note', '')
            note_preview = (note[:50] + '...') if len(note) > 50 else note
            print(f"    Пример note: '{note_preview}'")
            print(f"    У этого лида reject_id={lead.get('lead_reject_id')}")

    print(f"\n{'='*80}")
    print(f"ИТОГО лидов получено: {len(all_leads)}")
    print(f"С заполненным note: {with_note}")
    print(f"С note И lead_reject_id: {with_note_and_reject}")
    print(f"{'='*80}")

    # Посмотрим на всех с note
    if with_note > 0:
        leads_with_note = [l for l in all_leads if l.get('note')]
        print(f"\nВсе лиды с заполненным note:")
        for lead in leads_with_note[:10]:  # Первые 10
            note = lead.get('note', '')
            note_preview = (note[:50] + '...') if len(note) > 50 else note
            print(f"  ID={lead.get('id')}, reject_id={lead.get('lead_reject_id')}, note='{note_preview}'")

    # Проверим корреляцию
    if with_note > 0:
        percent_archived = (with_note_and_reject / with_note * 100) if with_note > 0 else 0
        print(f"\nКорреляция:")
        print(f"  {percent_archived:.1f}% лидов с note имеют lead_reject_id")

        if percent_archived > 50:
            print(f"  ✓✓✓ СИЛЬНАЯ КОРРЕЛЯЦИЯ! Лиды с note часто архивные")
        elif percent_archived > 0:
            print(f"  ~ Есть корреляция но не полная")


if __name__ == "__main__":
    test_note_field()
