"""
Тест для перевірки current-status-only логіки трекінгу лідів.

МЕТА: Перевірити що кожен лід рахується ТІЛЬКИ в одному статусі.
КРИТЕРІЙ УСПІХУ: sum(статусів) <= загальна_кількість_лідів

Тестуємо на реальних кампаніях через Meta API.
"""
import os
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Завантажити змінні середовища
load_dotenv()

# Додаємо app директорію в Python path
app_dir = Path(__file__).parent.parent
sys.path.insert(0, str(app_dir))

from services import meta_leads
from services import alfacrm_tracking


async def test_current_status_only_no_duplication():
    """
    Тест перевіряє що лід рахується ТІЛЬКИ в поточному статусі.

    Логіка:
    1. Отримуємо кампанії з Meta API за період
    2. Обогачуємо через AlfaCRM
    3. Перевіряємо: sum(funnel_stats.values()) <= leads_count
    4. Якщо є дублювання - тест падає з деталями
    """

    print("\n" + "="*80)
    print("ТЕСТ: Current-Status-Only (без дублювання лідів)")
    print("="*80)

    # Параметри
    page_id = os.getenv('FACEBOOK_PAGE_ID')
    page_token = os.getenv('META_PAGE_ACCESS_TOKEN')
    start_date = '2025-09-21'
    end_date = '2025-09-23'

    print(f"\nПараметри:")
    print(f"  Page ID: {page_id}")
    print(f"  Період: {start_date} - {end_date}")

    # Крок 1: Отримати кампанії з Meta
    print(f"\n[1/2] Отримання лідів з Meta API...")
    try:
        campaigns_data = await meta_leads.get_leads_for_period(
            page_id=page_id,
            page_token=page_token,
            start_date=start_date,
            end_date=end_date
        )

        total_leads = sum(len(c['leads']) for c in campaigns_data.values())
        print(f"  ✓ Отримано {len(campaigns_data)} кампаній, {total_leads} лідів")

        if len(campaigns_data) < 5:
            print(f"  ⚠️  УВАГА: Знайдено тільки {len(campaigns_data)} кампаній. Рекомендовано мінімум 5.")

    except Exception as e:
        print(f"  ✗ ПОМИЛКА: {e}")
        return

    # Крок 2: Обогатити через AlfaCRM
    print(f"\n[2/2] Обогачення через AlfaCRM (CURRENT-STATUS-ONLY ЛОГІКА)...")
    try:
        enriched = await alfacrm_tracking.track_leads_by_campaigns(
            campaigns_data=campaigns_data,
            page_size=500
        )

        print(f"  ✓ Оброблено {len(enriched)} кампаній")

    except Exception as e:
        print(f"  ✗ ПОМИЛКА: {e}")
        import traceback
        traceback.print_exc()
        return

    # Крок 3: Перевірка на дублювання
    print(f"\n📊 Тестуємо {len(enriched)} кампаній:")
    print("-" * 80)

    failed_campaigns = []

    for idx, (campaign_id, campaign) in enumerate(enriched.items(), 1):
        campaign_name = campaign.get('campaign_name', 'Без назви')
        leads_count = campaign['leads_count']
        funnel_stats = campaign['funnel_stats']

        print(f"\n{idx}. Кампанія: {campaign_name[:50]}")
        print(f"   ID: {campaign_id}")
        print(f"   Очікувана кількість лідів: {leads_count}")

        # Рахуємо суму лідів по статусам (виключаючи ключ 'Кількість лідів')
        sum_in_statuses = sum(
            count for status, count in funnel_stats.items()
            if status != 'Кількість лідів'
        )

        print(f"   Сума по статусам: {sum_in_statuses}")
        print(f"   Різниця: {sum_in_statuses - leads_count}")

        # КРИТЕРІЙ УСПІХУ: sum_in_statuses <= leads_count
        if sum_in_statuses > leads_count:
            print(f"   ❌ ПРОВАЛ: Дублювання лідів! {sum_in_statuses} > {leads_count}")

            # Виводимо детальну статистику
            print(f"   Деталі по статусам:")
            for status, count in sorted(funnel_stats.items()):
                if count > 0 and status != 'Кількість лідів':
                    print(f"      - {status}: {count}")

            failed_campaigns.append({
                'campaign_id': campaign_id,
                'campaign_name': campaign_name,
                'expected': leads_count,
                'actual': sum_in_statuses,
                'difference': sum_in_statuses - leads_count,
                'funnel_stats': {k: v for k, v in funnel_stats.items() if v > 0}
            })
        else:
            print(f"   ✅ УСПІХ: Немає дублювання")

    # Підсумки
    print("\n" + "="*80)
    print("РЕЗУЛЬТАТИ ТЕСТУВАННЯ:")
    print("="*80)

    if failed_campaigns:
        print(f"\n❌ ПРОВАЛ: {len(failed_campaigns)} з {len(enriched)} кампаній мають дублювання лідів\n")

        for idx, failed in enumerate(failed_campaigns, 1):
            print(f"{idx}. {failed['campaign_name'][:50]}")
            print(f"   Очікувано: {failed['expected']}")
            print(f"   Фактично: {failed['actual']}")
            print(f"   Дублювання: +{failed['difference']} лідів")
            print()

        raise AssertionError(f"Виявлено дублювання лідів в {len(failed_campaigns)} кампаніях")
    else:
        print(f"\n✅ УСПІХ: Всі {len(enriched)} кампаній пройшли перевірку")
        print("   Немає дублювання лідів - кожен лід рахується тільки в одному статусі")


if __name__ == "__main__":
    asyncio.run(test_current_status_only_no_duplication())
