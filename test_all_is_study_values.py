"""
Test script to find all possible is_study values in AlfaCRM API.
This script tests values from -5 to 10 to find missing records.
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import requests

# Load environment variables
load_dotenv()

# Add app directory to path
app_dir = Path(__file__).parent / "app"
sys.path.insert(0, str(app_dir))

from connectors.crm import alfacrm_auth_get_token

# AlfaCRM API configuration
base_url = os.getenv('ALFACRM_BASE_URL')
token = alfacrm_auth_get_token()

print('[INFO] SEARCH FOR ALL is_study VALUES')
print('=' * 70)

results = {}

# Test values from -5 to 10
for val in range(-5, 11):
    print(f'\n[TEST] is_study={val}...', flush=True)

    # Get total count first with larger page_size
    payload = {
        'is_study': val,
        'page': 1,
        'page_size': 500  # Increased from 50 to 500
    }

    try:
        response = requests.post(
            f'{base_url}/v2api/customer/index',
            headers={'X-ALFACRM-TOKEN': token},
            json=payload,
            timeout=10
        )
        data = response.json()
        items = data.get('items', [])

        if items:
            all_records = []
            page = 1

            # Fetch all pages until we get empty response
            while True:
                payload['page'] = page
                response = requests.post(
                    f'{base_url}/v2api/customer/index',
                    headers={'X-ALFACRM-TOKEN': token},
                    json=payload,
                    timeout=10
                )
                data = response.json()
                items = data.get('items', [])

                if not items:
                    break

                all_records.extend(items)

                # Progress every 5 pages
                if page % 5 == 0:
                    print(f'  [PROGRESS] Page {page}, collected {len(all_records)} records', flush=True)

                page += 1

                # Safety limit - reduced to 50 pages × 500 = 25000 records max per is_study
                if page > 50:
                    print(f'  [WARNING] Reached page limit of 50 pages', flush=True)
                    break

            # Check for archived leads
            archived_count = sum(1 for r in all_records if r.get('lead_reject_id') is not None)

            results[val] = {
                'count': len(all_records),
                'pages': page - 1,
                'archived': archived_count
            }
            print(f'[OK] is_study={val:2d}: {len(all_records):5d} records ({archived_count} archived)', flush=True)
        else:
            print(f'[--] is_study={val:2d}: 0 records', flush=True)

    except Exception as e:
        print(f'[ERROR] is_study={val}: {e}')

print('\n' + '=' * 70)
print('[SUMMARY] RESULTS:')
print('=' * 70)

total_records = 0
total_archived = 0

for val, info in sorted(results.items()):
    count = info['count']
    archived = info['archived']
    pages = info['pages']
    total_records += count
    total_archived += archived
    print(f'  is_study={val}: {count:5d} records ({pages:3d} pages, {archived} archived)')

print('\n' + '=' * 70)
print(f'[TOTAL] Sum of all is_study values: {total_records} records')
print(f'[ARCHIVED] Total archived leads found: {total_archived}')
print(f'[TARGET] Expected: 7000+ records')

if total_records >= 7000:
    print(f'[SUCCESS] FOUND ALL! Delta: +{total_records - 7000}')
else:
    print(f'[WARNING] Missing: {7000 - total_records} records')
