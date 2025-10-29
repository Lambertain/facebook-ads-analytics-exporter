"""
Тест: Глубокая пагинация - может архивные идут дальше?
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


def test_deep_pagination():
    """Получить МНОГО лидов с is_study=0 и посмотреть где начинаются архивные"""
    print("\n" + "="*80)
    print("ТЕСТ: Глубокая пагинация is_study=0 (только лиды)")
    print("="*80)

    token = alfacrm_auth_get_token()
    base_url = os.getenv("ALFACRM_BASE_URL").rstrip('/')
    company_id = int(os.getenv("ALFACRM_COMPANY_ID"))

    url = f"{base_url}/v2api/customer/index"

    all_leads = []
    archived_count = 0
    first_archived_page = None

    print("\nПолучение с is_study=0, page_size=500:")

    for page in range(1, 50):  # До 50 страниц (25000 лидов)
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
            print(f"  Страница {page}: пусто, останавливаемся")
            break

        all_leads.extend(items)

        # Посчитаем архивных на этой странице
        page_archived = [l for l in items if l.get('lead_reject_id') is not None]

        if page_archived:
            archived_count += len(page_archived)
            if first_archived_page is None:
                first_archived_page = page
            print(f"  Страница {page}: {len(items)} лидов, архивных: {len(page_archived)} ✓✓✓")

            # Покажем первого архивного
            lead = page_archived[0]
            print(f"    Первый архивный: ID={lead.get('id')}, reject_id={lead.get('lead_reject_id')}, имя={lead.get('name')}")
        else:
            print(f"  Страница {page}: {len(items)} лидов, архивных: 0")

        # Если нашли архивных, получим еще несколько страниц для подтверждения
        if archived_count > 0 and page >= first_archived_page + 5:
            break

    print(f"\n{'='*80}")
    print(f"ИТОГО лидов получено: {len(all_leads)}")
    print(f"Из них архивных (lead_reject_id != None): {archived_count}")

    if first_archived_page:
        print(f"Первая страница с архивными: {first_archived_page}")
        print(f"Активных до архивных: {(first_archived_page - 1) * 500 + len([l for l in all_leads[:first_archived_page*500] if l.get('lead_reject_id') is None])}")
    print(f"{'='*80}")

    if archived_count > 0:
        print(f"\n✓✓✓ НАЙДЕНЫ АРХИВНЫЕ ЛИДЫ! Они начинаются со страницы {first_archived_page}")
    else:
        print(f"\n✗ Архивных лидов НЕ НАЙДЕНО среди первых {len(all_leads)}")


if __name__ == "__main__":
    test_deep_pagination()
