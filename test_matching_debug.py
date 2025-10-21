"""Diagnostic script to debug matching between Facebook leads and AlfaCRM students."""
import asyncio
import sys
import os
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Setup logging BEFORE importing modules
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

load_dotenv()
sys.path.insert(0, 'app')

from services import meta_leads, alfacrm_tracking
from connectors.crm import alfacrm_list_students


async def main():
    page_id = os.getenv('FACEBOOK_PAGE_ID')
    page_token = os.getenv('META_PAGE_ACCESS_TOKEN').strip("'")

    # 2 days only
    end_date = datetime.now()
    start_date = end_date - timedelta(days=2)

    start_str = start_date.strftime('%Y-%m-%d')
    end_str = end_date.strftime('%Y-%m-%d')

    print('=' * 80)
    print(f'DIAGNOSTIC: Matching Facebook leads with AlfaCRM students')
    print(f'Period: {start_str} to {end_str}')
    print('=' * 80)

    # Step 1: Get Facebook leads
    print('\n[1/4] Getting leads from Facebook...')
    campaigns_data = await meta_leads.get_leads_for_period(
        page_id=page_id,
        page_token=page_token,
        start_date=start_str,
        end_date=end_str
    )

    # Filter student campaigns
    student_campaigns = {
        cid: cdata for cid, cdata in campaigns_data.items()
        if any(kw.lower() in cdata.get('campaign_name', '').lower()
               for kw in ['student', 'shkolnik'])
    }

    total_fb_leads = sum(len(c['leads']) for c in student_campaigns.values())
    print(f'  ✓ Found {len(student_campaigns)} student campaigns')
    print(f'  ✓ Total Facebook leads: {total_fb_leads}')

    # Step 2: Extract contacts from Facebook leads
    print('\n[2/4] Extracting contacts from Facebook leads...')
    lead_contacts = alfacrm_tracking.extract_contacts_from_campaigns(student_campaigns, debug=True)
    print(f'  ✓ Extracted {len(lead_contacts)} unique normalized contacts')

    # Show sample
    sample_fb = list(lead_contacts)[:5]
    print(f'  ✓ Sample FB contacts: {sample_fb}')

    # Step 3: Load all students from AlfaCRM
    print('\n[3/4] Loading students from AlfaCRM...')
    all_students = []
    page = 1
    while True:
        response = alfacrm_list_students(page=page, page_size=500)
        students = response.get("items", [])
        if not students:
            break
        all_students.extend(students)

        total = response.get("total", 0)
        if len(all_students) >= total:
            break
        page += 1

    print(f'  ✓ Loaded {len(all_students)} students from AlfaCRM')

    # Step 4: Build student index
    print('\n[4/4] Building student index and matching...')
    student_index = alfacrm_tracking.build_student_index(all_students, debug=True)
    print(f'  ✓ Built index with {len(student_index)} normalized contacts')

    # Show sample
    sample_crm = list(student_index.keys())[:5]
    print(f'  ✓ Sample CRM contacts: {sample_crm}')

    # Filtering
    filtered_index = {
        contact: student for contact, student in student_index.items()
        if contact in lead_contacts
    }

    print(f'\n  ⚠️  RESULT: {len(filtered_index)} matched / {len(lead_contacts)} FB contacts')
    print(f'  ⚠️  Match rate: {100 * len(filtered_index) / len(lead_contacts):.2f}%')

    # Show matched contacts
    if filtered_index:
        print(f'\n  ✓ Matched contacts:')
        for contact in list(filtered_index.keys())[:10]:
            print(f'    - {contact}')

    # Analyze mismatches
    print(f'\n  ⚠️  Sample unmatched FB contacts:')
    unmatched_fb = [c for c in lead_contacts if c not in student_index]
    for contact in unmatched_fb[:10]:
        print(f'    - {contact}')

    print('\n' + '=' * 80)
    print('DIAGNOSTIC COMPLETE')
    print('=' * 80)


if __name__ == '__main__':
    asyncio.run(main())
