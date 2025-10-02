"""
Unit тести для Meta Ads connector (app/connectors/meta.py).

Тестуємо fetch_insights та fetch_leads функції з mock HTTP запитами.
"""

import pytest
from unittest.mock import Mock, patch, call
from app.connectors import meta


class TestFetchInsights:
    """Тести для функції fetch_insights."""

    @patch('app.connectors.meta.requests.get')
    def test_fetch_insights_success(self, mock_get, mock_meta_token, mock_ad_account_id,
                                     date_range, mock_meta_insights_response):
        """Тест успішного отримання insights."""
        # Arrange
        mock_response = Mock()
        mock_response.json.return_value = mock_meta_insights_response
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        # Act
        result = meta.fetch_insights(
            ad_account_id=mock_ad_account_id,
            access_token=mock_meta_token,
            date_from=date_range["date_from"],
            date_to=date_range["date_to"],
            level="campaign"
        )

        # Assert
        assert len(result) == 1
        assert result[0]["campaign_id"] == "123"
        assert result[0]["campaign_name"] == "Test Campaign"
        assert result[0]["impressions"] == "1000"
        assert result[0]["clicks"] == "50"
        assert result[0]["spend"] == "100.50"
        mock_get.assert_called_once()

    @patch('app.connectors.meta.requests.get')
    def test_fetch_insights_with_pagination(self, mock_get, mock_meta_token,
                                            mock_ad_account_id, date_range):
        """Тест отримання insights з пагінацією."""
        # Arrange: дві сторінки результатів
        first_response = Mock()
        first_response.json.return_value = {
            "data": [{"campaign_id": "123", "impressions": "1000"}],
            "paging": {"next": "https://graph.facebook.com/v19.0/next_page"}
        }
        first_response.raise_for_status = Mock()

        second_response = Mock()
        second_response.json.return_value = {
            "data": [{"campaign_id": "456", "impressions": "2000"}],
            "paging": {}
        }
        second_response.raise_for_status = Mock()

        mock_get.side_effect = [first_response, second_response]

        # Act
        result = meta.fetch_insights(
            ad_account_id=mock_ad_account_id,
            access_token=mock_meta_token,
            date_from=date_range["date_from"],
            date_to=date_range["date_to"]
        )

        # Assert
        assert len(result) == 2
        assert result[0]["campaign_id"] == "123"
        assert result[1]["campaign_id"] == "456"
        assert mock_get.call_count == 2

    @patch('app.connectors.meta.requests.get')
    def test_fetch_insights_api_error(self, mock_get, mock_meta_token,
                                      mock_ad_account_id, date_range):
        """Тест обробки помилки API."""
        # Arrange
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = Exception("API Error")
        mock_get.return_value = mock_response

        # Act & Assert
        with pytest.raises(Exception, match="API Error"):
            meta.fetch_insights(
                ad_account_id=mock_ad_account_id,
                access_token=mock_meta_token,
                date_from=date_range["date_from"],
                date_to=date_range["date_to"]
            )

    @patch('app.connectors.meta.requests.get')
    def test_fetch_insights_empty_response(self, mock_get, mock_meta_token,
                                           mock_ad_account_id, date_range):
        """Тест порожньої відповіді від API."""
        # Arrange
        mock_response = Mock()
        mock_response.json.return_value = {"data": [], "paging": {}}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        # Act
        result = meta.fetch_insights(
            ad_account_id=mock_ad_account_id,
            access_token=mock_meta_token,
            date_from=date_range["date_from"],
            date_to=date_range["date_to"]
        )

        # Assert
        assert result == []


class TestFetchLeads:
    """Тести для функції fetch_leads."""

    @patch('app.connectors.meta._get_all')
    @patch('app.connectors.meta.requests.get')
    def test_fetch_leads_success(self, mock_get, mock_get_all, mock_meta_token,
                                  date_range, mock_pages_response, mock_forms_response,
                                  mock_meta_leads_response):
        """Тест успішного отримання лідів."""
        # Arrange
        mock_get_all.side_effect = [
            mock_pages_response["data"],  # pages
            mock_forms_response["data"]   # forms
        ]

        mock_response = Mock()
        mock_response.json.return_value = mock_meta_leads_response
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        # Act
        result = meta.fetch_leads(
            access_token=mock_meta_token,
            date_from=date_range["date_from"],
            date_to=date_range["date_to"]
        )

        # Assert
        assert len(result) == 1
        assert result[0]["id"] == "lead_123"
        assert result[0]["page_id"] == "page_123"
        assert result[0]["form_id"] == "form_123"
        assert "field_data" in result[0]

    @patch('app.connectors.meta._get_all')
    def test_fetch_leads_no_pages(self, mock_get_all, mock_meta_token, date_range):
        """Тест коли немає доступних сторінок."""
        # Arrange
        mock_get_all.return_value = []

        # Act
        result = meta.fetch_leads(
            access_token=mock_meta_token,
            date_from=date_range["date_from"],
            date_to=date_range["date_to"]
        )

        # Assert
        assert result == []

    @patch('app.connectors.meta._get_all')
    @patch('app.connectors.meta.requests.get')
    def test_fetch_leads_with_pagination(self, mock_get, mock_get_all, mock_meta_token,
                                         date_range, mock_pages_response, mock_forms_response):
        """Тест отримання лідів з пагінацією."""
        # Arrange
        mock_get_all.side_effect = [
            mock_pages_response["data"],
            mock_forms_response["data"]
        ]

        first_response = Mock()
        first_response.json.return_value = {
            "data": [{"id": "lead_1", "created_time": "2025-01-01T10:00:00+0000", "field_data": []}],
            "paging": {"next": "https://graph.facebook.com/v19.0/next_page"}
        }
        first_response.raise_for_status = Mock()

        second_response = Mock()
        second_response.json.return_value = {
            "data": [{"id": "lead_2", "created_time": "2025-01-02T10:00:00+0000", "field_data": []}],
            "paging": {}
        }
        second_response.raise_for_status = Mock()

        mock_get.side_effect = [first_response, second_response]

        # Act
        result = meta.fetch_leads(
            access_token=mock_meta_token,
            date_from=date_range["date_from"],
            date_to=date_range["date_to"]
        )

        # Assert
        assert len(result) == 2
        assert result[0]["id"] == "lead_1"
        assert result[1]["id"] == "lead_2"


class TestGetAll:
    """Тести для допоміжної функції _get_all."""

    @patch('app.connectors.meta.requests.get')
    def test_get_all_single_page(self, mock_get, mock_meta_token):
        """Тест _get_all з однією сторінкою."""
        # Arrange
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": [{"id": "1"}, {"id": "2"}],
            "paging": {}
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        # Act
        result = meta._get_all("https://test.com", mock_meta_token)

        # Assert
        assert len(result) == 2
        assert result[0]["id"] == "1"
        assert result[1]["id"] == "2"

    @patch('app.connectors.meta.requests.get')
    def test_get_all_multiple_pages(self, mock_get, mock_meta_token):
        """Тест _get_all з декількома сторінками."""
        # Arrange
        first_response = Mock()
        first_response.json.return_value = {
            "data": [{"id": "1"}],
            "paging": {"next": "https://test.com/page2"}
        }
        first_response.raise_for_status = Mock()

        second_response = Mock()
        second_response.json.return_value = {
            "data": [{"id": "2"}],
            "paging": {}
        }
        second_response.raise_for_status = Mock()

        mock_get.side_effect = [first_response, second_response]

        # Act
        result = meta._get_all("https://test.com", mock_meta_token)

        # Assert
        assert len(result) == 2
        assert mock_get.call_count == 2
