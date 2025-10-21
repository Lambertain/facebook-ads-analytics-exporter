"""Export FB and AlfaCRM contacts to text files for manual comparison."""
import asyncio
import sys
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, 'app')

from services import meta_leads, alfacrm_tracking
from connectors.crm import alfacrm_list_students


async def main():
    page_id = os.getenv('FACEBOOK_PAGE_ID')
    page_token = os.getenv('META_PAGE_ACCESS_TOKEN').strip("'")

    # Конкретный период: 7-14 октября 2025
    start_date = datetime(2025, 10, 7)
    end_date = datetime(2025, 10, 14)
    start_str = start_date.strftime('%Y-%m-%d')
    end_str = end_date.strftime('%Y-%m-%d')

    print('Exporting contacts to text files...')

    # Step 1: Get Facebook leads
    print('\n[1/2] Getting Facebook leads...')
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

    # Extract and normalize FB contacts
    fb_contacts = {}  # raw -> normalized
    for campaign_data in student_campaigns.values():
        for lead in campaign_data.get('leads', []):
            field_data = lead.get('field_data', [])
            for field in field_data:
                if field['name'] in ['phone_number', 'email']:
                    raw = field['values'][0]
                    normalized = alfacrm_tracking.normalize_contact(raw)
                    if normalized:
                        fb_contacts[raw] = normalized

    print(f'  OK Collected {len(fb_contacts)} unique FB contacts')

    # Step 2: Get AlfaCRM students
    print('\n[2/2] Getting AlfaCRM students...')
    all_students = []
    page_num = 1
    while True:
        response = alfacrm_list_students(page=page_num, page_size=500)
        students = response.get("items", [])
        if not students:
            break
        all_students.extend(students)

        total = response.get("total", 0)
        if len(all_students) >= total:
            break
        page_num += 1

    print(f'  OK Got {len(all_students)} students from AlfaCRM')

    # Extract and normalize CRM contacts
    crm_contacts = {}  # raw -> normalized
    for student in all_students:
        # Phones
        phones = student.get('phone', [])
        if isinstance(phones, str):
            phones = [phones]

        for phone in phones:
            normalized = alfacrm_tracking.normalize_contact(phone)
            if normalized:
                crm_contacts[phone] = normalized

        # Email
        email = student.get('email')
        if email:
            normalized = alfacrm_tracking.normalize_contact(email)
            if normalized:
                crm_contacts[email] = normalized

    print(f'  OK Collected {len(crm_contacts)} unique CRM contacts')

    # Write to files
    print('\nWriting to files...')

    with open('fb_contacts.txt', 'w', encoding='utf-8') as f:
        f.write('=' * 80 + '\n')
        f.write(f'FACEBOOK CONTACTS ({len(fb_contacts)} total)\n')
        f.write(f'Period: {start_str} to {end_str}\n')
        f.write('=' * 80 + '\n\n')

        f.write('RAW CONTACT                 | NORMALIZED\n')
        f.write('-' * 80 + '\n')

        for raw, normalized in sorted(fb_contacts.items()):
            f.write(f'{raw:30} | {normalized}\n')

    with open('crm_contacts.txt', 'w', encoding='utf-8') as f:
        f.write('=' * 80 + '\n')
        f.write(f'ALFACRM CONTACTS ({len(crm_contacts)} total)\n')
        f.write(f'Total students: {len(all_students)}\n')
        f.write('=' * 80 + '\n\n')

        f.write('RAW CONTACT                 | NORMALIZED\n')
        f.write('-' * 80 + '\n')

        for raw, normalized in sorted(crm_contacts.items()):
            f.write(f'{raw:30} | {normalized}\n')

    print('\nDone!')
    print(f'  fb_contacts.txt  - {len(fb_contacts)} contacts')
    print(f'  crm_contacts.txt - {len(crm_contacts)} contacts')

    # Quick comparison
    fb_norm_set = set(fb_contacts.values())
    crm_norm_set = set(crm_contacts.values())
    matches = fb_norm_set & crm_norm_set

    print(f'\nQuick check:')
    print(f'  Matches found: {len(matches)}')
    if matches:
        print(f'  Matched contacts: {list(matches)[:5]}')


if __name__ == '__main__':
    asyncio.run(main())
