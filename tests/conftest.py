"""
Pytest configuration та загальні fixtures для тестів eCademy.
"""

import os
import pytest
from unittest.mock import Mock


@pytest.fixture
def mock_meta_token():
    """Повертає тестовий Meta API токен."""
    return "test_meta_access_token_12345"


@pytest.fixture
def mock_ad_account_id():
    """Повертає тестовий Meta Ad Account ID."""
    return "act_1234567890"


@pytest.fixture
def date_range():
    """Повертає тестовий діапазон дат."""
    return {
        "date_from": "2025-01-01",
        "date_to": "2025-01-31"
    }


@pytest.fixture
def mock_meta_insights_response():
    """Повертає mock відповідь Meta Insights API."""
    return {
        "data": [
            {
                "date_start": "2025-01-01",
                "date_stop": "2025-01-01",
                "campaign_id": "123",
                "campaign_name": "Test Campaign",
                "impressions": "1000",
                "clicks": "50",
                "spend": "100.50",
                "reach": "800",
                "cpc": "2.01",
                "cpm": "100.50",
                "ctr": "5.0",
                "objective": "OUTCOME_LEADS"
            }
        ],
        "paging": {}
    }


@pytest.fixture
def mock_meta_leads_response():
    """Повертає mock відповідь Meta Leads API."""
    return {
        "data": [
            {
                "id": "lead_123",
                "created_time": "2025-01-15T10:30:00+0000",
                "field_data": [
                    {"name": "email", "values": ["test@example.com"]},
                    {"name": "phone_number", "values": ["+380501234567"]}
                ]
            }
        ],
        "paging": {}
    }


@pytest.fixture
def mock_pages_response():
    """Повертає mock відповідь Meta Pages API."""
    return {
        "data": [
            {"id": "page_123", "name": "Test Page"}
        ],
        "paging": {}
    }


@pytest.fixture
def mock_forms_response():
    """Повертає mock відповідь Meta Leadgen Forms API."""
    return {
        "data": [
            {"id": "form_123", "name": "Test Lead Form"}
        ],
        "paging": {}
    }
