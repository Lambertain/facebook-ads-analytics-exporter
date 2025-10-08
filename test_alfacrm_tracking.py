"""
Тест модуля alfacrm_tracking.py с реальными данными.
"""
import os
import sys
import asyncio
import json
from dotenv import load_dotenv

# Загрузить переменные окружения
load_dotenv()

# Добавить app в путь
sys.path.insert(0, 'app')

from services import meta_leads
from services import alfacrm_tracking


async def test_full_flow():
    """Тест полного flow: Meta Leads -> AlfaCRM Tracking."""

    print("=" * 80)
    print("ТЕСТ: Получение лидов из Meta API + трекинг через AlfaCRM")
    print("=" * 80)

    # Параметры
    page_id = os.getenv("FACEBOOK_PAGE_ID")
    page_token = os.getenv("META_PAGE_ACCESS_TOKEN")
    start_date = "2025-10-01"  # Начало октября
    end_date = "2025-10-08"    # Неделя данных

    print(f"\nПараметры:")
    print(f"  Page ID: {page_id}")
    print(f"  Период: {start_date} - {end_date}")

    # 1. Получить лиды из Meta API
    print(f"\n[1/3] Получение лидов из Meta API...")

    try:
        campaigns_data = await meta_leads.get_leads_for_period(
            page_id=page_id,
            page_token=page_token,
            start_date=start_date,
            end_date=end_date
        )

        total_leads = sum(len(c["leads"]) for c in campaigns_data.values())
        print(f"  OK Получено {len(campaigns_data)} кампаний, {total_leads} лидов")

        # Показать первую кампанию
        if campaigns_data:
            first_campaign = list(campaigns_data.values())[0]
            print(f"\n  Пример кампании:")
            print(f"    ID: {first_campaign['campaign_id']}")
            print(f"    Название: {first_campaign['campaign_name']}")
            print(f"    Лидов: {len(first_campaign['leads'])}")

    except Exception as e:
        print(f"  ERROR: {e}")
        return

    # 2. Обогатить данными из AlfaCRM
    print(f"\n[2/3] Трекинг лидов через AlfaCRM...")

    try:
        enriched_campaigns = await alfacrm_tracking.track_leads_by_campaigns(
            campaigns_data=campaigns_data,
            page_size=500
        )

        print(f"  OK Обработано {len(enriched_campaigns)} кампаний")

        # Показать статистику первой кампании
        if enriched_campaigns:
            first_campaign = list(enriched_campaigns.values())[0]
            print(f"\n  Пример обогащенной кампании:")
            print(f"    Название: {first_campaign['campaign_name']}")
            print(f"    Всего лидов: {first_campaign['leads_count']}")
            print(f"\n    Воронка:")

            funnel_stats = first_campaign['funnel_stats']
            for status_name, count in funnel_stats.items():
                if count > 0:
                    print(f"      {status_name}: {count}")

    except Exception as e:
        print(f"  ERROR: {e}")
        import traceback
        traceback.print_exc()
        return

    # 3. Вычислить метрики
    print(f"\n[3/3] Вычисление метрик...")

    try:
        for campaign_id, campaign in enriched_campaigns.items():
            funnel_stats = campaign['funnel_stats']

            # Вычислить проценты
            conversion = alfacrm_tracking.calculate_conversion_rate(funnel_stats)
            target_pct = alfacrm_tracking.calculate_target_leads_percentage(funnel_stats)
            trial_conv = alfacrm_tracking.calculate_trial_conversion(funnel_stats)

            print(f"\n  Кампания: {campaign['campaign_name'][:60]}...")
            print(f"    % целевых лидов: {target_pct}%")
            print(f"    % конверсия в продажу: {conversion}%")
            print(f"    % конверсия пробный->продажа: {trial_conv}%")

    except Exception as e:
        print(f"  ERROR: {e}")
        import traceback
        traceback.print_exc()
        return

    print(f"\n" + "=" * 80)
    print("ТЕСТ ЗАВЕРШЕН УСПЕШНО")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_full_flow())
