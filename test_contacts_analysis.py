"""Analyze types of contacts in Facebook leads vs AlfaCRM students."""
import asyncio
import sys
import os
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv
from collections import Counter

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

load_dotenv()
sys.path.insert(0, 'app')

from services import meta_leads, alfacrm_tracking
from connectors.crm import alfacrm_list_students


def analyze_contact_type(contact: str) -> str:
    """Determine contact type: UA phone, international phone, or email."""
    if '@' in contact:
        return 'email'
    elif contact.startswith('380') and len(contact) == 12:
        return 'ua_phone'
    elif contact.isdigit():
        return 'intl_phone'
    else:
        return 'unknown'


async def main():
    page_id = os.getenv('FACEBOOK_PAGE_ID')
    page_token = os.getenv('META_PAGE_ACCESS_TOKEN').strip("'")

    end_date = datetime.now()
    start_date = end_date - timedelta(days=2)
    start_str = start_date.strftime('%Y-%m-%d')
    end_str = end_date.strftime('%Y-%m-%d')

    print('=' * 80)
    print('CONTACT TYPE ANALYSIS: Facebook vs AlfaCRM')
    print('=' * 80)

    # Get Facebook leads
    print('\n[1/3] Getting Facebook leads...')
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

    lead_contacts = alfacrm_tracking.extract_contacts_from_campaigns(student_campaigns, debug=False)

    # Analyze FB contacts
    print(f'\n[2/3] Analyzing {len(lead_contacts)} Facebook contacts...')
    fb_types = Counter(analyze_contact_type(c) for c in lead_contacts)

    print(f'  ✓ Emails: {fb_types["email"]}')
    print(f'  ✓ UA phones (380...): {fb_types["ua_phone"]}')
    print(f'  ✓ International phones: {fb_types["intl_phone"]}')
    print(f'  ✓ Unknown format: {fb_types["unknown"]}')

    # Get AlfaCRM students
    print('\n[3/3] Loading AlfaCRM students...')
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

    student_index = alfacrm_tracking.build_student_index(all_students, debug=False)

    # Analyze CRM contacts
    print(f'\nAnalyzing {len(student_index)} AlfaCRM contacts...')
    crm_types = Counter(analyze_contact_type(c) for c in student_index.keys())

    print(f'  ✓ Emails: {crm_types["email"]}')
    print(f'  ✓ UA phones (380...): {crm_types["ua_phone"]}')
    print(f'  ✓ International phones: {crm_types["intl_phone"]}')
    print(f'  ✓ Unknown format: {crm_types["unknown"]}')

    # Comparison
    print('\n' + '=' * 80)
    print('COMPARISON:')
    print('=' * 80)
    print(f'\n  Facebook leads are {fb_types["intl_phone"] / len(lead_contacts) * 100:.1f}% international')
    print(f'  AlfaCRM students are {crm_types["ua_phone"] / len(student_index) * 100:.1f}% Ukrainian')

    print(f'\n  ⚠️  THIS IS THE PROBLEM!')
    print(f'  Facebook collects INTERNATIONAL audience')
    print(f'  AlfaCRM contains mostly UKRAINIAN students')
    print(f'  → Very low match rate expected!')

    # Calculate potential matches
    fb_ua_phones = {c for c in lead_contacts if analyze_contact_type(c) == 'ua_phone'}
    crm_ua_phones = {c for c in student_index.keys() if analyze_contact_type(c) == 'ua_phone'}
    ua_matches = fb_ua_phones & crm_ua_phones

    fb_emails = {c for c in lead_contacts if analyze_contact_type(c) == 'email'}
    crm_emails = {c for c in student_index.keys() if analyze_contact_type(c) == 'email'}
    email_matches = fb_emails & crm_emails

    print(f'\n  Potential matches:')
    print(f'    UA phones matched: {len(ua_matches)} / {len(fb_ua_phones)} FB UA phones')
    print(f'    Emails matched: {len(email_matches)} / {len(fb_emails)} FB emails')

    print('\n' + '=' * 80)


if __name__ == '__main__':
    asyncio.run(main())
