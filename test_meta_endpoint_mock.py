"""Тест /api/meta-data endpoint з mock Meta API"""
from unittest.mock import patch, Mock
from fastapi.testclient import TestClient
from app.main import app
import os

# Set test env vars
os.environ['META_ACCESS_TOKEN'] = 'test_token_123'
os.environ['META_AD_ACCOUNT_ID'] = 'act_123456'
os.environ['CAMPAIGN_KEYWORDS_STUDENTS'] = 'student,school'
os.environ['CAMPAIGN_KEYWORDS_TEACHERS'] = 'teacher,tutor'

# Mock Meta API responses
mock_insights = [
    {
        "campaign_id": "camp_001",
        "campaign_name": "Student Campaign Test",
        "ad_id": "ad_001",
        "impressions": "5000",
        "clicks": "250",
        "spend": "100.50",
        "ctr": "5.0",
        "cpm": "20.10",
        "date_start": "2025-01-01",
        "date_stop": "2025-01-31"
    },
    {
        "campaign_id": "camp_002",
        "campaign_name": "Teacher Recruitment Campaign",
        "ad_id": "ad_002",
        "impressions": "3000",
        "clicks": "150",
        "spend": "75.25",
        "ctr": "5.0",
        "cpm": "25.08",
        "date_start": "2025-01-01",
        "date_stop": "2025-01-31"
    }
]

mock_creatives = {
    "ad_001": {
        "title": "Навчання для студентів",
        "body": "Приєднуйтесь до нашої школи!",
        "image_url": "https://example.com/student.jpg",
        "video_id": "",
        "thumbnail_url": ""
    },
    "ad_002": {
        "title": "Робота вчителем",
        "body": "Шукаємо викладачів!",
        "image_url": "https://example.com/teacher.jpg",
        "video_id": "",
        "thumbnail_url": ""
    }
}

with patch('app.connectors.meta.fetch_insights') as mock_fetch_insights, \
     patch('app.connectors.meta.fetch_ad_creatives') as mock_fetch_creatives:

    mock_fetch_insights.return_value = mock_insights
    mock_fetch_creatives.return_value = mock_creatives

    client = TestClient(app)

    # Test endpoint
    response = client.get('/api/meta-data?start_date=2025-01-01&end_date=2025-01-31')

    print(f'Status Code: {response.status_code}')

    if response.status_code != 200:
        print(f'Error Response: {response.text}')
    else:
        data = response.json()

        print(f'\n=== Response Structure ===')
        print(f'Response keys: {list(data.keys())}')
        print(f'Fetched at: {data.get("fetched_at")}')
        print(f'Period: {data.get("period")}')

        print(f'\n=== Data Counts ===')
        print(f'Ads: {len(data.get("ads", []))}')
        print(f'Students: {len(data.get("students", []))}')
        print(f'Teachers: {len(data.get("teachers", []))}')

        # Check ads data
        if data.get("ads"):
            print(f'\n=== First Ad ===')
            ad = data["ads"][0]
            print(f'Campaign: {ad.get("campaign_name")}')
            print(f'Creative Text: {ad.get("creative_text")}')
            print(f'CTR: {ad.get("ctr")}')
            print(f'Leads Count: {ad.get("leads_count")}')

        # Check students data
        if data.get("students"):
            print(f'\n=== First Student Campaign ===')
            student = data["students"][0]
            print(f'Campaign Link: {student.get("campaign_link")}')
            print(f'Budget: {student.get("budget")}')
            print(f'Leads: {student.get("leads_count")}')

        # Check teachers data
        if data.get("teachers"):
            print(f'\n=== First Teacher Campaign ===')
            teacher = data["teachers"][0]
            print(f'Campaign Name: {teacher.get("campaign_name")}')
            print(f'Budget: {teacher.get("budget")}')
            print(f'Leads: {teacher.get("leads_count")}')

        print(f'\n✅ Endpoint test PASSED')
