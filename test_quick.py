"""Quick test of full flow on 2 days."""
import asyncio
import sys
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, 'app')

from services import meta_leads, alfacrm_tracking


async def main():
    page_id = os.getenv('FACEBOOK_PAGE_ID')
    page_token = os.getenv('META_PAGE_ACCESS_TOKEN').strip("'")

    # 2 days only
    end_date = datetime.now()
    start_date = end_date - timedelta(days=2)

    start_str = start_date.strftime('%Y-%m-%d')
    end_str = end_date.strftime('%Y-%m-%d')

    print('=' * 80)
    print(f'TEST: Meta Leads + AlfaCRM Tracking')
    print(f'Period: {start_str} to {end_str}')
    print('=' * 80)

    # Step 1: Get leads
    print('\n[1/2] Getting leads from Meta API...')
    try:
        campaigns_data = await meta_leads.get_leads_for_period(
            page_id=page_id,
            page_token=page_token,
            start_date=start_str,
            end_date=end_str
        )

        total_leads = sum(len(c['leads']) for c in campaigns_data.values())
        print(f'  OK {len(campaigns_data)} campaigns, {total_leads} leads')

        # Filter student campaigns
        student_campaigns = {
            cid: cdata for cid, cdata in campaigns_data.items()
            if any(kw.lower() in cdata.get('campaign_name', '').lower()
                   for kw in ['student', 'shkolnik'])
        }

        student_leads = sum(len(c['leads']) for c in student_campaigns.values())
        print(f'  Filtered: {len(student_campaigns)} student campaigns, {student_leads} leads')

    except Exception as e:
        print(f'  ERROR: {e}')
        import traceback
        traceback.print_exc()
        return

    # Step 2: Track through AlfaCRM
    print('\n[2/2] Tracking students through AlfaCRM...')
    try:
        enriched = await alfacrm_tracking.track_leads_by_campaigns(
            campaigns_data=student_campaigns,
            page_size=500
        )

        print(f'  OK Processed {len(enriched)} campaigns')

        # Aggregate funnel
        total_funnel = {}
        for campaign in enriched.values():
            for status, count in campaign['funnel_stats'].items():
                total_funnel[status] = total_funnel.get(status, 0) + count

        print('\n  Total student funnel:')
        for status, count in sorted(total_funnel.items()):
            if count > 0:
                print(f'    {status}: {count}')

        # Metrics
        conv = alfacrm_tracking.calculate_conversion_rate(total_funnel)
        target = alfacrm_tracking.calculate_target_leads_percentage(total_funnel)
        trial = alfacrm_tracking.calculate_trial_conversion(total_funnel)

        print('\n  Metrics:')
        print(f'    Target leads: {target}%')
        print(f'    Conversion to sale: {conv}%')
        print(f'    Trial to sale: {trial}%')

    except Exception as e:
        print(f'  ERROR: {e}')
        import traceback
        traceback.print_exc()
        return

    print('\n' + '=' * 80)
    print('SUCCESS! Full flow works!')
    print('=' * 80)


if __name__ == '__main__':
    asyncio.run(main())
