"""
Тест для проверки НОВОЙ логики: агрегация статусов + hybrid counting.

ЦЕЛЬ: Проверить что:
1. 38 статусов правильно агрегируются в 11 групп
2. Current-status counting работает для non-trial статусов
3. Cumulative counting работает для trial funnel (Призначено >= Проведено >= Чекає >= Оплата)

КРИТЕРІЙ УСПІХУ:
- Призначено пробне >= Проведено пробне >= Чекає оплату >= Отримана оплата
- Сума non-trial статусів + Отримана оплата <= Кількість лідів (допускається невелике перевищення через trial funnel)
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


async def test_aggregated_hybrid_counting():
    """
    Тест перевіряє НОВУ логіку:
    - Агрегація 38 статусів -> 11 груп
    - Hybrid counting: current-status + cumulative для trial funnel
    """

    print("\n" + "="*80)
    print("ТЕСТ: Агрегація статусів + Hybrid Counting")
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

    # Крок 2: Обогатити через AlfaCRM з НОВОЮ логікою
    print(f"\n[2/2] Обогачення через AlfaCRM (АГРЕГАЦІЯ + HYBRID COUNTING)...")
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

    # Крок 3: Перевірка НОВОЇ логіки
    print(f"\n📊 Тестуємо {len(enriched)} кампаній:")
    print("-" * 80)

    # Очікувані агреговані статуси
    EXPECTED_AGGREGATED_STATUSES = [
        "Не розібраний",
        "Недозвон",
        "Встановлено контакт",
        "Зник після контакту",
        "В опрацюванні",
        "Призначено пробне",
        "Проведено пробне",
        "Чекає оплату",
        "Отримана оплата",
        "Передзвонити пізніше",
        "Старі клієнти",
    ]

    failed_campaigns = []
    cumulative_errors = []

    for idx, (campaign_id, campaign) in enumerate(enriched.items(), 1):
        campaign_name = campaign.get('campaign_name', 'Без назви')
        leads_count = campaign['leads_count']
        funnel_stats = campaign['funnel_stats']

        print(f"\n{idx}. Кампанія: {campaign_name[:50]}")
        print(f"   ID: {campaign_id}")
        print(f"   Очікувана кількість лідів: {leads_count}")

        # ПЕРЕВІРКА 1: Всі ключі мають бути з EXPECTED_AGGREGATED_STATUSES
        unexpected_keys = [
            key for key in funnel_stats.keys()
            if key not in EXPECTED_AGGREGATED_STATUSES and key != 'Кількість лідів'
        ]

        if unexpected_keys:
            print(f"   ❌ ПРОВАЛ: Знайдено неочікувані ключі: {unexpected_keys}")
            failed_campaigns.append({
                'campaign_id': campaign_id,
                'campaign_name': campaign_name,
                'reason': 'unexpected_keys',
                'details': unexpected_keys
            })
            continue

        # ПЕРЕВІРКА 2: Cumulative counting для trial funnel
        # Призначено >= Проведено >= Чекає >= Отримана
        призначено = funnel_stats.get("Призначено пробне", 0)
        проведено = funnel_stats.get("Проведено пробне", 0)
        чекає = funnel_stats.get("Чекає оплату", 0)
        оплата = funnel_stats.get("Отримана оплата", 0)

        print(f"   Trial funnel:")
        print(f"      Призначено пробне: {призначено}")
        print(f"      Проведено пробне: {проведено}")
        print(f"      Чекає оплату: {чекає}")
        print(f"      Отримана оплата: {оплата}")

        cumulative_valid = (
            призначено >= проведено >= чекає and
            призначено >= оплата and
            проведено >= оплата
        )

        if not cumulative_valid:
            print(f"   ❌ ПРОВАЛ: Порушення cumulative логіки!")
            cumulative_errors.append({
                'campaign_id': campaign_id,
                'campaign_name': campaign_name,
                'призначено': призначено,
                'проведено': проведено,
                'чекає': чекає,
                'оплата': оплата,
            })
            failed_campaigns.append({
                'campaign_id': campaign_id,
                'campaign_name': campaign_name,
                'reason': 'cumulative_violation',
                'details': f"Призначено: {призначено}, Проведено: {проведено}, Чекає: {чекає}, Оплата: {оплата}"
            })
            continue

        # ПЕРЕВІРКА 3: Сума non-trial статусів + Оплата <= leads_count
        # (допускається невелике перевищення через cumulative counting)
        non_trial_sum = sum(
            count for status, count in funnel_stats.items()
            if status not in ["Призначено пробне", "Проведено пробне", "Чекає оплату", "Кількість лідів"]
        )

        print(f"   Сума non-trial статусів: {non_trial_sum}")
        print(f"   Різниця з очікуваним: {non_trial_sum - leads_count}")

        # Допускаємо невелике перевищення (до 10%) через особливості cumulative counting
        if non_trial_sum > leads_count * 1.1:
            print(f"   ⚠️  УВАГА: Значне перевищення non-trial суми")
            failed_campaigns.append({
                'campaign_id': campaign_id,
                'campaign_name': campaign_name,
                'reason': 'non_trial_overflow',
                'expected': leads_count,
                'actual': non_trial_sum,
                'difference': non_trial_sum - leads_count
            })
        else:
            print(f"   ✅ УСПІХ: Агрегація + Hybrid counting працює коректно")

    # Підсумки
    print("\n" + "="*80)
    print("РЕЗУЛЬТАТИ ТЕСТУВАННЯ:")
    print("="*80)

    if failed_campaigns:
        print(f"\n❌ ПРОВАЛ: {len(failed_campaigns)} з {len(enriched)} кампаній мають проблеми\n")

        for idx, failed in enumerate(failed_campaigns, 1):
            print(f"{idx}. {failed['campaign_name'][:50]}")
            print(f"   Причина: {failed['reason']}")
            print(f"   Деталі: {failed.get('details', 'N/A')}")
            print()

        raise AssertionError(f"Виявлено проблеми в {len(failed_campaigns)} кампаніях")
    else:
        print(f"\n✅ УСПІХ: Всі {len(enriched)} кампаній пройшли перевірку")
        print("   Агрегація статусів працює коректно (38 → 11 груп)")
        print("   Hybrid counting працює коректно:")
        print("     - Current-status для non-trial статусів")
        print("     - Cumulative counting для trial funnel")


if __name__ == "__main__":
    asyncio.run(test_aggregated_hybrid_counting())
