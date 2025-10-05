"""Простий інтеграційний тест для /api/meta-data endpoint"""
from fastapi.testclient import TestClient
from app.main import app
import os

# Set test env vars
os.environ['META_ACCESS_TOKEN'] = 'test_token'
os.environ['META_AD_ACCOUNT_ID'] = 'act_123'

client = TestClient(app)

# Test endpoint
response = client.get('/api/meta-data?start_date=2025-01-01&end_date=2025-01-31')
print(f'Status: {response.status_code}')

if response.status_code != 200:
    print(f'Error: {response.text}')
else:
    data = response.json()
    print(f'Response keys: {list(data.keys())}')
    print(f'Ads count: {len(data.get("ads", []))}')
    print(f'Students count: {len(data.get("students", []))}')
    print(f'Teachers count: {len(data.get("teachers", []))}')
    print(f'Fetched at: {data.get("fetched_at")}')
    print(f'Period: {data.get("period")}')

    # Check structure of first ad if available
    if data.get("ads"):
        ad = data["ads"][0]
        print(f'\nFirst ad keys: {list(ad.keys())[:5]}...')
        print(f'Campaign name: {ad.get("campaign_name")}')
        print(f'Leads count: {ad.get("leads_count")}')
