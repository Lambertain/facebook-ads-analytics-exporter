"""
Подробный отчет по всем статусам лидов за сентябрь 2025.

Показывает:
1. Все 38 статусов из маппинга
2. Сколько лидов в каждом статусе
3. Какие статусы используются, какие нет
4. Распределение по воронке
"""
import asyncio
import sys
import os
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, 'app')

from services import meta_leads, alfacrm_tracking


async def detailed_status_report():
    """Подробный отчет по всем статусам."""
    page_id = os.getenv('FACEBOOK_PAGE_ID')
    page_token = os.getenv('META_PAGE_ACCESS_TOKEN').strip("'")

    print('=' * 80)
    print('DETAILED STATUS REPORT - September 2025')
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
    print('\n[2/2] Tracking through AlfaCRM...')
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

        total = total_funnel.get('Кількість лідів', 0)

        # Вывод ВСЕХ 38 статусов из маппинга
        print('\n' + '=' * 80)
        print('ALL 38 STATUSES FROM ALFACRM_STATUS_MAPPING')
        print('=' * 80)

        # Группируем статусы
        main_funnel = {}
        second_funnel = {}

        # ID статусов основной воронки
        main_ids = [11, 10, 27, 1, 32, 26, 12, 6, 2, 3, 5, 9, 4, 29, 25, 30, 31, 8, 13, 50]

        for status_id, status_name in alfacrm_tracking.ALFACRM_STATUS_MAPPING.items():
            count = total_funnel.get(status_name, 0)

            if status_id in main_ids:
                main_funnel[status_id] = (status_name, count)
            else:
                second_funnel[status_id] = (status_name, count)

        # Основная воронка
        print('\nMAIN FUNNEL (IDs 1-50):')
        print('-' * 80)
        print(f'{"ID":<5} {"Status Name":<40} {"Count":<8} {"Percent":<8} {"Bar":<20}')
        print('-' * 80)

        for status_id in main_ids:
            if status_id in main_funnel:
                status_name, count = main_funnel[status_id]
                pct = (count / total * 100) if total > 0 else 0
                bar = '#' * int(pct / 2) if count > 0 else ''
                marker = 'OK' if count > 0 else ''
                print(f'{status_id:<5} {status_name:<40} {count:<8} {pct:>6.1f}%  {bar:<20} {marker}')

        # Вторая воронка
        print('\nSECOND FUNNEL (IDs 18-49):')
        print('-' * 80)
        print(f'{"ID":<5} {"Status Name":<40} {"Count":<8} {"Percent":<8} {"Bar":<20}')
        print('-' * 80)

        second_ids = [18, 40, 42, 43, 22, 44, 24, 34, 35, 37, 36, 38, 39, 45, 46, 47, 48, 49]

        for status_id in second_ids:
            if status_id in second_funnel:
                status_name, count = second_funnel[status_id]
                pct = (count / total * 100) if total > 0 else 0
                bar = '#' * int(pct / 2) if count > 0 else ''
                marker = 'OK' if count > 0 else ''
                print(f'{status_id:<5} {status_name:<40} {count:<8} {pct:>6.1f}%  {bar:<20} {marker}')

        # Статистика использования
        print('\n' + '=' * 80)
        print('USAGE STATISTICS')
        print('=' * 80)

        used_statuses = [s for s, c in total_funnel.items() if c > 0 and s != 'Кількість лідів']
        unused_count = len(alfacrm_tracking.ALFACRM_STATUS_MAPPING) - len(used_statuses)

        print(f'\nTotal statuses in mapping:  {len(alfacrm_tracking.ALFACRM_STATUS_MAPPING)}')
        print(f'Statuses with leads:        {len(used_statuses)}')
        print(f'Unused statuses:            {unused_count}')

        print('\nUsed statuses (September 2025):')
        for status in sorted(used_statuses):
            count = total_funnel[status]
            pct = (count / total * 100) if total > 0 else 0
            # Найти ID статуса
            status_id = None
            for sid, sname in alfacrm_tracking.ALFACRM_STATUS_MAPPING.items():
                if sname == status:
                    status_id = sid
                    break
            print(f'  ID {status_id:>2}: {status:<40} {count:>4} leads ({pct:>5.1f}%)')

        print('\nUnused statuses (0 leads):')
        all_status_names = set(alfacrm_tracking.ALFACRM_STATUS_MAPPING.values())
        unused_statuses = all_status_names - set(used_statuses)

        for status in sorted(unused_statuses):
            # Найти ID статуса
            status_id = None
            for sid, sname in alfacrm_tracking.ALFACRM_STATUS_MAPPING.items():
                if sname == status:
                    status_id = sid
                    break
            print(f'  ID {status_id:>2}: {status}')

        # Ключевые метрики
        print('\n' + '=' * 80)
        print('KEY METRICS')
        print('=' * 80)

        sales = total_funnel.get("Отримана оплата", 0)
        trial_completed = total_funnel.get("Проведено пробне", 0)
        not_processed = total_funnel.get("Не розібраний", 0)

        conv = alfacrm_tracking.calculate_conversion_rate(total_funnel)
        target = alfacrm_tracking.calculate_target_leads_percentage(total_funnel)
        trial_conv = alfacrm_tracking.calculate_trial_conversion(total_funnel)

        print(f'\nTotal leads:                {total}')
        print(f'Sales (Отримана оплата):    {sales} ({conv}%)')
        print(f'Trial (Проведено пробне):   {trial_completed}')
        print(f'Trial to sale conversion:   {trial_conv}%')
        print(f'Not processed:              {not_processed} ({not_processed/total*100:.1f}%)')
        print(f'Target leads %:             {target}%')

    except Exception as e:
        print(f'  ERROR: {e}')
        import traceback
        traceback.print_exc()
        return

    print('\n' + '=' * 80)
    print('REPORT COMPLETE')
    print('=' * 80)


if __name__ == "__main__":
    asyncio.run(detailed_status_report())
