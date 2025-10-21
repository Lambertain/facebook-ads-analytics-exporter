"""Debug script to find the bug in phone/email normalization logic."""
import asyncio
import sys
import os
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

load_dotenv()
sys.path.insert(0, 'app')

from services import meta_leads, alfacrm_tracking
from connectors.crm import alfacrm_list_students


async def main():
    page_id = os.getenv('FACEBOOK_PAGE_ID')
    page_token = os.getenv('META_PAGE_ACCESS_TOKEN').strip("'")

    end_date = datetime.now()
    start_date = end_date - timedelta(days=2)
    start_str = start_date.strftime('%Y-%m-%d')
    end_str = end_date.strftime('%Y-%m-%d')

    print('=' * 80)
    print('NORMALIZATION DEBUG: Find the bug in matching logic')
    print('=' * 80)

    # Step 1: Get Facebook leads and extract raw contacts
    print('\n[1/4] Getting Facebook leads...')
    campaigns_data = await meta_leads.get_leads_for_period(
        page_id=page_id,
        page_token=page_token,
        start_date=start_str,
        end_date=end_str
    )

    student_campaigns = {
        cid: cdata for cid, cdata in campaigns_data.items()
        if any(kw.lower() in cdata.get('campaign_name', '').lower()
               for kw in ['student', 'shkolnik'])
    }

    # Get raw contacts from FB
    fb_raw_contacts = []
    for campaign_data in student_campaigns.values():
        for lead in campaign_data.get('leads', []):
            field_data = lead.get('field_data', [])
            for field in field_data:
                if field['name'] in ['phone_number', 'email']:
                    fb_raw_contacts.append({
                        'type': field['name'],
                        'raw': field['values'][0]
                    })
                    if len(fb_raw_contacts) >= 10:  # Get first 10
                        break
            if len(fb_raw_contacts) >= 10:
                break
        if len(fb_raw_contacts) >= 10:
            break

    print(f'  OK Got {len(fb_raw_contacts)} raw FB contacts')

    # Step 2: Normalize FB contacts
    print('\n[2/4] Normalizing Facebook contacts...')
    fb_normalized = {}
    for contact in fb_raw_contacts:
        raw = contact['raw']
        normalized = alfacrm_tracking.normalize_contact(raw)
        fb_normalized[raw] = normalized
        print(f'  FB: {contact["type"]:15} | raw: {raw:20} -> normalized: {normalized}')

    # Step 3: Get AlfaCRM students and extract raw contacts
    print('\n[3/4] Getting AlfaCRM students...')
    all_students = []
    page = 1
    while True:
        response = alfacrm_list_students(page=page, page_size=500)
        students = response.get("items", [])
        if not students:
            break
        all_students.extend(students)
        if len(all_students) >= 500:  # Get first 500
            break
        total = response.get("total", 0)
        if len(all_students) >= total:
            break
        page += 1

    print(f'  OK Got {len(all_students)} students')

    # Get raw contacts from CRM
    crm_raw_contacts = []
    for student in all_students[:100]:  # Check first 100 students
        phones = student.get('phone', [])
        if isinstance(phones, str):
            phones = [phones]

        for phone in phones:
            crm_raw_contacts.append({
                'type': 'phone',
                'raw': phone,
                'student_id': student.get('id')
            })
            if len(crm_raw_contacts) >= 10:
                break

        email = student.get('email')
        if email:
            crm_raw_contacts.append({
                'type': 'email',
                'raw': email,
                'student_id': student.get('id')
            })

        if len(crm_raw_contacts) >= 10:
            break

    print(f'  OK Got {len(crm_raw_contacts)} raw CRM contacts')

    # Step 4: Normalize CRM contacts
    print('\n[4/4] Normalizing AlfaCRM contacts...')
    crm_normalized = {}
    for contact in crm_raw_contacts:
        raw = contact['raw']
        normalized = alfacrm_tracking.normalize_contact(raw)
        crm_normalized[raw] = normalized
        print(f'  CRM: {contact["type"]:15} | raw: {raw:20} -> normalized: {normalized}')

    # Compare normalized sets
    print('\n' + '=' * 80)
    print('COMPARISON:')
    print('=' * 80)

    fb_norm_set = set(fb_normalized.values())
    crm_norm_set = set(crm_normalized.values())

    matches = fb_norm_set & crm_norm_set

    print(f'\n  FB normalized contacts: {len(fb_norm_set)}')
    print(f'  CRM normalized contacts: {len(crm_norm_set)}')
    print(f'  Matches: {len(matches)}')

    if matches:
        print(f'\n  MATCHED CONTACTS:')
        for match in matches:
            print(f'    {match}')
    else:
        print(f'\n  NO MATCHES FOUND!')
        print(f'\n  Sample FB normalized: {list(fb_norm_set)[:5]}')
        print(f'  Sample CRM normalized: {list(crm_norm_set)[:5]}')

    print('\n' + '=' * 80)


if __name__ == '__main__':
    asyncio.run(main())
