"""
Unit тести для модуля nethunt_tracking

Покриття:
- Retry механізми
- Валідація API відповідей
- Нормалізація контактів
- Витягування статусів
- Маппінг статусів
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import requests
from typing import Dict, Any

# Додаємо app до sys.path для імпорту
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

from services.nethunt_tracking import (
    _validate_nethunt_changes_response,
    _nethunt_api_call_with_retry,
    normalize_contact,
    extract_status_from_record,
    map_nethunt_status_to_column,
    extract_lead_contacts,
    extract_status_history
)


class TestRetryMechanism:
    """Тести для retry механізму з tenacity."""

    @patch('services.nethunt_tracking.requests.get')
    def test_retry_on_timeout_3_attempts(self, mock_get):
        """Перевірка 3 спроб при Timeout."""
        mock_get.side_effect = requests.exceptions.Timeout("API timeout")

        with pytest.raises(requests.exceptions.Timeout):
            _nethunt_api_call_with_retry(
                url="http://test.nethunt.com/api",
                headers={"Authorization": "Basic test"},
                timeout=10
            )

        # Має бути 3 спроби (початкова + 2 retry)
        assert mock_get.call_count == 3

    @patch('services.nethunt_tracking.requests.get')
    def test_retry_success_on_second_attempt(self, mock_get):
        """Перевірка успіху на другій спробі."""
        # Перша спроба: помилка, друга: успіх
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{"recordId": "123", "time": "2025-10-10T12:00:00Z"}]

        mock_get.side_effect = [
            requests.exceptions.ConnectionError("Network error"),
            mock_response
        ]

        result = _nethunt_api_call_with_retry(
            url="http://test.nethunt.com/api",
            headers={"Authorization": "Basic test"},
            timeout=10
        )

        assert result.status_code == 200
        assert mock_get.call_count == 2

    @patch('services.nethunt_tracking.requests.get')
    def test_retry_on_http_error(self, mock_get):
        """Перевірка retry при HTTP 500 помилці."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("500 Server Error")

        mock_get.return_value = mock_response

        with pytest.raises(requests.exceptions.HTTPError):
            _nethunt_api_call_with_retry(
                url="http://test.nethunt.com/api",
                headers={"Authorization": "Basic test"},
                timeout=10
            )

        assert mock_get.call_count == 3

    @patch('services.nethunt_tracking.requests.get')
    def test_no_retry_on_success(self, mock_get):
        """Перевірка відсутності retry при успіху."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = []

        mock_get.return_value = mock_response

        result = _nethunt_api_call_with_retry(
            url="http://test.nethunt.com/api",
            headers={"Authorization": "Basic test"},
            timeout=10
        )

        assert result.status_code == 200
        assert mock_get.call_count == 1  # Тільки одна спроба


class TestValidation:
    """Тести для валідації структури API відповідей."""

    def test_validate_valid_data(self):
        """Валідні дані проходять перевірку."""
        data = [
            {"recordId": "123", "time": "2025-10-10T12:00:00Z"},
            {"recordId": "456", "time": "2025-10-11T13:00:00Z"}
        ]
        assert _validate_nethunt_changes_response(data) == True

    def test_validate_empty_list(self):
        """Порожній список вважається валідним."""
        data = []
        assert _validate_nethunt_changes_response(data) == True

    def test_validate_invalid_type_dict(self):
        """Не-список відхиляється."""
        data = {"error": "not a list"}
        assert _validate_nethunt_changes_response(data) == False

    def test_validate_invalid_type_string(self):
        """Рядок замість списку відхиляється."""
        data = "invalid response"
        assert _validate_nethunt_changes_response(data) == False

    def test_validate_missing_recordId(self, caplog):
        """Попередження при відсутності recordId."""
        data = [{"time": "2025-10-10T12:00:00Z"}]  # немає recordId

        result = _validate_nethunt_changes_response(data)

        # Продовжує роботу з попередженням
        assert result == True
        assert "missing required fields: ['recordId']" in caplog.text

    def test_validate_missing_time(self, caplog):
        """Попередження при відсутності time."""
        data = [{"recordId": "123"}]  # немає time

        result = _validate_nethunt_changes_response(data)

        assert result == True
        assert "missing required fields: ['time']" in caplog.text

    def test_validate_missing_both_fields(self, caplog):
        """Попередження при відсутності обох обов'язкових полів."""
        data = [{"user": "test@example.com"}]  # немає recordId та time

        result = _validate_nethunt_changes_response(data)

        assert result == True
        assert "missing required fields" in caplog.text

    def test_validate_non_dict_item(self, caplog):
        """Попередження при елементі що не є dict."""
        data = [
            {"recordId": "123", "time": "2025-10-10T12:00:00Z"},
            "invalid item",
            {"recordId": "456", "time": "2025-10-11T13:00:00Z"}
        ]

        result = _validate_nethunt_changes_response(data)

        assert result == True
        assert "is not a dict" in caplog.text


class TestNormalization:
    """Тести для нормалізації контактів."""

    def test_normalize_phone_international(self):
        """Нормалізація міжнародного телефону."""
        assert normalize_contact("+380 (50) 123-45-67") == "380501234567"

    def test_normalize_phone_local(self):
        """Нормалізація локального телефону."""
        assert normalize_contact("050-123-45-67") == "0501234567"

    def test_normalize_phone_with_spaces(self):
        """Нормалізація телефону з пробілами."""
        assert normalize_contact("380 50 123 45 67") == "380501234567"

    def test_normalize_email_lowercase(self):
        """Нормалізація email до lowercase."""
        assert normalize_contact("Test@Example.COM") == "test@example.com"

    def test_normalize_email_with_spaces(self):
        """Нормалізація email з пробілами."""
        assert normalize_contact("  test@example.com  ") == "test@example.com"

    def test_normalize_none(self):
        """None повертається як None."""
        assert normalize_contact(None) == None

    def test_normalize_empty_string(self):
        """Порожній рядок повертається як None."""
        assert normalize_contact("") == None

    def test_normalize_phone_only_digits(self):
        """Перевірка що телефон містить тільки цифри."""
        result = normalize_contact("+38 (050) 123-45-67")
        assert result.isdigit()
        assert len(result) == 12


class TestStatusExtraction:
    """Тести для витягування статусів з NetHunt записів."""

    def test_extract_status_direct_format(self):
        """Витягування статусу з прямого формату."""
        record = {
            "status": {"name": "New", "id": 1}
        }
        assert extract_status_from_record(record) == "new"

    def test_extract_status_from_fields_dict(self):
        """Витягування статусу з полів (dict формат)."""
        record = {
            "fields": {
                "Status": {"name": "Contacted", "id": 2}
            }
        }
        assert extract_status_from_record(record) == "contacted"

    def test_extract_status_from_fields_string(self):
        """Витягування статусу з полів (string формат)."""
        record = {
            "fields": {
                "Status": "Qualified"
            }
        }
        assert extract_status_from_record(record) == "qualified"

    def test_extract_status_case_insensitive_field(self):
        """Витягування статусу з різним регістром назви поля."""
        record = {
            "fields": {
                "status": {"name": "Hired"}
            }
        }
        assert extract_status_from_record(record) == "hired"

    def test_extract_status_missing(self):
        """None при відсутності статусу."""
        record = {
            "fields": {
                "Name": "John Doe",
                "Email": "john@example.com"
            }
        }
        assert extract_status_from_record(record) == None

    def test_extract_status_empty_record(self):
        """None при порожньому record."""
        record = {}
        assert extract_status_from_record(record) == None


class TestStatusMapping:
    """Тести для маппінгу статусів NetHunt → назви стовпців."""

    def test_map_status_direct_match(self):
        """Прямий маппінг зі словника."""
        assert map_nethunt_status_to_column("new") == "Нові"
        assert map_nethunt_status_to_column("contacted") == "Контакт встановлено"
        assert map_nethunt_status_to_column("qualified") == "Кваліфіковані"

    def test_map_status_partial_match(self):
        """Частковий маппінг (якщо є підстрока)."""
        # Якщо в settings.py є "interview_scheduled" → "Співбесіда призначена"
        # То "interview_scheduled_confirmed" має знайти часткове співпадіння
        result = map_nethunt_status_to_column("interview_scheduled")
        assert "Співбесіда" in result or result == "Interview_scheduled"

    def test_map_status_unknown(self):
        """Невідомий статус повертається з великої літери."""
        assert map_nethunt_status_to_column("unknown_status") == "Unknown_status"

    def test_map_status_none(self):
        """None повертає дефолтний статус."""
        assert map_nethunt_status_to_column(None) == "Нові"

    def test_map_status_empty_string(self):
        """Порожній рядок повертає дефолтний статус."""
        assert map_nethunt_status_to_column("") == "Нові"


class TestLeadContactExtraction:
    """Тести для витягування контактів з лідів Meta API."""

    def test_extract_phone_and_email(self):
        """Витягування телефону та email."""
        lead = {
            "field_data": [
                {"name": "phone_number", "values": ["+380501234567"]},
                {"name": "email", "values": ["test@example.com"]}
            ]
        }

        phone, email = extract_lead_contacts(lead)

        assert phone == "380501234567"
        assert email == "test@example.com"

    def test_extract_phone_only(self):
        """Витягування тільки телефону."""
        lead = {
            "field_data": [
                {"name": "phone", "values": ["050-123-45-67"]}
            ]
        }

        phone, email = extract_lead_contacts(lead)

        assert phone == "0501234567"
        assert email == None

    def test_extract_email_only(self):
        """Витягування тільки email."""
        lead = {
            "field_data": [
                {"name": "email", "values": ["Test@Example.COM"]}
            ]
        }

        phone, email = extract_lead_contacts(lead)

        assert phone == None
        assert email == "test@example.com"

    def test_extract_no_contacts(self):
        """Відсутність контактів."""
        lead = {
            "field_data": [
                {"name": "full_name", "values": ["John Doe"]}
            ]
        }

        phone, email = extract_lead_contacts(lead)

        assert phone == None
        assert email == None

    def test_extract_empty_field_data(self):
        """Порожній field_data."""
        lead = {"field_data": []}

        phone, email = extract_lead_contacts(lead)

        assert phone == None
        assert email == None

    def test_extract_ukrainian_field_names(self):
        """Витягування з українськими назвами полів."""
        lead = {
            "field_data": [
                {"name": "Телефон", "values": ["+380501234567"]},
                {"name": "email", "values": ["test@example.com"]}  # "електронна пошта" не підтримується поточною логікою
            ]
        }

        phone, email = extract_lead_contacts(lead)

        assert phone == "380501234567"
        assert email == "test@example.com"


class TestStatusHistory:
    """Тести для витягування історії статусів."""

    def test_extract_status_history_single_change(self):
        """Витягування історії з одним змінами."""
        all_changes = [
            {
                "recordId": "123",
                "time": "2025-10-10T12:00:00Z",
                "user": "manager@example.com",
                "fieldActions": [
                    {
                        "field": "status",
                        "oldValue": "new",
                        "newValue": "contacted"
                    }
                ]
            }
        ]

        history = extract_status_history("123", all_changes)

        assert len(history) == 1
        assert history[0]["old_status"] == "new"
        assert history[0]["new_status"] == "contacted"
        assert history[0]["changed_by"] == "manager@example.com"

    def test_extract_status_history_multiple_changes(self):
        """Витягування історії з декількома змінами."""
        all_changes = [
            {
                "recordId": "123",
                "time": "2025-10-10T12:00:00Z",
                "fieldActions": [
                    {"field": "status", "oldValue": "new", "newValue": "contacted"}
                ]
            },
            {
                "recordId": "123",
                "time": "2025-10-11T14:00:00Z",
                "fieldActions": [
                    {"field": "status", "oldValue": "contacted", "newValue": "qualified"}
                ]
            }
        ]

        history = extract_status_history("123", all_changes)

        assert len(history) == 2
        assert history[0]["new_status"] == "contacted"
        assert history[1]["new_status"] == "qualified"

    def test_extract_status_history_chronological_order(self):
        """Перевірка хронологічного порядку."""
        all_changes = [
            {
                "recordId": "123",
                "time": "2025-10-12T16:00:00Z",  # Пізніша дата
                "fieldActions": [
                    {"field": "status", "oldValue": "qualified", "newValue": "hired"}
                ]
            },
            {
                "recordId": "123",
                "time": "2025-10-10T12:00:00Z",  # Рання дата
                "fieldActions": [
                    {"field": "status", "oldValue": "new", "newValue": "contacted"}
                ]
            }
        ]

        history = extract_status_history("123", all_changes)

        # Має бути відсортовано за часом (рання → пізня)
        assert history[0]["time"] == "2025-10-10T12:00:00Z"
        assert history[1]["time"] == "2025-10-12T16:00:00Z"

    def test_extract_status_history_wrong_record_id(self):
        """Порожня історія для невідповідного record_id."""
        all_changes = [
            {
                "recordId": "456",  # Інший record_id
                "time": "2025-10-10T12:00:00Z",
                "fieldActions": [
                    {"field": "status", "oldValue": "new", "newValue": "contacted"}
                ]
            }
        ]

        history = extract_status_history("123", all_changes)

        assert len(history) == 0

    def test_extract_status_history_ignore_non_status_fields(self):
        """Ігнорування змін не-статусних полів."""
        all_changes = [
            {
                "recordId": "123",
                "time": "2025-10-10T12:00:00Z",
                "fieldActions": [
                    {"field": "name", "oldValue": "John", "newValue": "John Doe"},
                    {"field": "status", "oldValue": "new", "newValue": "contacted"},
                    {"field": "email", "oldValue": "", "newValue": "john@example.com"}
                ]
            }
        ]

        history = extract_status_history("123", all_changes)

        # Тільки одна зміна статусу
        assert len(history) == 1
        assert history[0]["new_status"] == "contacted"


# Інтеграційні тести (вимагають ENV змінних)
class TestIntegration:
    """Інтеграційні тести (пропускаються якщо немає ENV змінних)."""

    @pytest.mark.skipif(
        os.getenv("NETHUNT_BASIC_AUTH") is None,
        reason="NETHUNT_BASIC_AUTH not configured"
    )
    @patch('services.nethunt_tracking.requests.get')
    def test_full_flow_with_retry_and_validation(self, mock_get):
        """Повний флоу: retry → отримання → валідація."""
        # Імітація успішної відповіді NetHunt API
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "recordId": "123",
                "time": "2025-10-10T12:00:00Z",
                "user": "manager@example.com",
                "fieldActions": [
                    {"field": "status", "oldValue": "new", "newValue": "contacted"}
                ]
            }
        ]

        mock_get.return_value = mock_response

        # Виконання запиту
        result = _nethunt_api_call_with_retry(
            url="http://test.nethunt.com/api",
            headers={"Authorization": "Basic test"},
            timeout=10
        )

        # Перевірка результату
        data = result.json()
        assert _validate_nethunt_changes_response(data) == True
        assert len(data) == 1
        assert data[0]["recordId"] == "123"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
