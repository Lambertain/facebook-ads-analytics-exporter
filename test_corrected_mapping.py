"""
Тест обновленного маппинга статусов AlfaCRM - сентябрь 2025.

Проверяет что:
1. Используются правильные названия статусов из API
2. Продажи обнаруживаются как "Отримана оплата" (ID 4, 39)
3. Пробные уроки как "Проведено пробне" (ID 3, 37)
4. Новые лиды как "Не розібраний" (ID 13)
"""
import asyncio
import sys
import os
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, 'app')

from services import meta_leads, alfacrm_tracking


async def test_september_corrected():
    """Тест с корректными названиями статусов."""
    page_id = os.getenv('FACEBOOK_PAGE_ID')
    page_token = os.getenv('META_PAGE_ACCESS_TOKEN').strip("'")

    print('=' * 80)
    print('TEST: Corrected Status Mapping - September 2025')
    print('Period: 2025-09-01 to 2025-09-30')
    print('=' * 80)

    # 1. Получить лиды из Meta
    print('\n[1/2] Getting leads from Meta API...')
    try:
        campaigns_data = await meta_leads.get_leads_for_period(
            page_id=page_id,
            page_token=page_token,
            start_date='2025-09-01',
            end_date='2025-09-30'
        )

        total_leads = sum(len(c['leads']) for c in campaigns_data.values())
        print(f'  OK {len(campaigns_data)} campaigns, {total_leads} leads')

        # Фильтр student/shkolnik
        student_campaigns = {
            cid: cdata for cid, cdata in campaigns_data.items()
            if any(kw.lower() in cdata.get('campaign_name', '').lower()
                   for kw in ['student', 'shkolnik'])
        }

        student_leads = sum(len(c['leads']) for c in student_campaigns.values())
        print(f'  Student campaigns: {len(student_campaigns)}, {student_leads} leads')

    except Exception as e:
        print(f'  ERROR: {e}')
        import traceback
        traceback.print_exc()
        return

    # 2. Трекинг через AlfaCRM
    print('\n[2/2] Tracking through AlfaCRM with corrected mapping...')
    print('  (Loading all students, ~1-2 min...)')

    try:
        enriched = await alfacrm_tracking.track_leads_by_campaigns(
            campaigns_data=student_campaigns,
            page_size=500
        )

        print(f'  OK Processed {len(enriched)} campaigns')

        # Агрегированная воронка
        total_funnel = {}
        for campaign in enriched.values():
            for status, count in campaign['funnel_stats'].items():
                total_funnel[status] = total_funnel.get(status, 0) + count

        # Вывод воронки
        print('\n  FUNNEL DISTRIBUTION (corrected status names):')
        print('  ' + '-' * 76)

        sorted_statuses = sorted(
            [(s, c) for s, c in total_funnel.items() if s != 'Кількість лідів'],
            key=lambda x: x[1],
            reverse=True
        )

        total = total_funnel.get('Кількість лідів', 0)

        for status, count in sorted_statuses:
            if count > 0:
                pct = (count / total) * 100 if total > 0 else 0
                bar = '#' * int(pct / 2)
                print(f'  {status:35s} {count:4d} ({pct:5.1f}%) {bar}')

        # Метрики с ПРАВИЛЬНЫМИ названиями
        print('\n  KEY METRICS (using corrected status names):')
        print('  ' + '-' * 76)

        conv = alfacrm_tracking.calculate_conversion_rate(total_funnel)
        target = alfacrm_tracking.calculate_target_leads_percentage(total_funnel)
        trial_conv = alfacrm_tracking.calculate_trial_conversion(total_funnel)

        # Новые правильные названия
        sales = total_funnel.get("Отримана оплата", 0)
        trial_completed = total_funnel.get("Проведено пробне", 0)
        not_processed = total_funnel.get("Не розібраний", 0)

        # Все варианты недозвона
        nedozvon_total = (
            total_funnel.get("Недодзвон", 0) +
            total_funnel.get("Недозвон 2", 0) +
            total_funnel.get("Недозвон 3", 0) +
            total_funnel.get("Недозвон", 0) +
            total_funnel.get("недозвон 3", 0)
        )

        print(f'  Total leads:                    {total}')
        print(f'  Not processed (Не розібраний):  {not_processed} ({not_processed/total*100:.1f}%)')
        print(f'  No answer (all nedozvon):       {nedozvon_total} ({nedozvon_total/total*100:.1f}%)')
        print(f'  Target leads %:                 {target}%')
        print(f'  Trial completed (Проведено):    {trial_completed}')
        print(f'  Sales (Отримана оплата):        {sales}')
        print(f'  Conversion rate:                {conv}%')
        print(f'  Trial to sale conversion:       {trial_conv}%')

        # Проверка что используются правильные статусы
        print('\n  VALIDATION:')
        print('  ' + '-' * 76)

        if sales > 0:
            print(f'  OK Sales detected: {sales} (status "Отримана оплата")')
        else:
            print(f'  WARNING: 0 sales found')

        if trial_completed > 0:
            print(f'  OK Trials detected: {trial_completed} (status "Проведено пробне")')
        else:
            print(f'  INFO: 0 trials completed')

        if not_processed > 0:
            print(f'  OK Unprocessed: {not_processed} (status "Не розібраний")')

        # Проверка что старые названия НЕ используются
        old_sales = total_funnel.get("Купили (ЦА)", 0)
        old_trial = total_funnel.get("Проведений пробний", 0)
        old_unprocessed = total_funnel.get("Не розібрані", 0)

        if old_sales > 0 or old_trial > 0 or old_unprocessed > 0:
            print(f'  ERROR: Old status names still in use!')
            print(f'    Old "Купили (ЦА)": {old_sales}')
            print(f'    Old "Проведений пробний": {old_trial}')
            print(f'    Old "Не розібрані": {old_unprocessed}')
        else:
            print(f'  OK Old status names not used (correctly migrated)')

    except Exception as e:
        print(f'  ERROR: {e}')
        import traceback
        traceback.print_exc()
        return

    print('\n' + '=' * 80)
    print('SUCCESS! Corrected mapping test complete')
    print('=' * 80)


if __name__ == "__main__":
    asyncio.run(test_september_corrected())
