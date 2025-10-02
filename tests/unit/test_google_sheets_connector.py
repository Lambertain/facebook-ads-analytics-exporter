"""
Unit тести для Google Sheets connector (app/connectors/google_sheets.py).

Тестуємо get_client, write_insights, write_leads та допоміжні функції з мокуванням gspread.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from app.connectors import google_sheets


class TestGetClient:
    """Тести для функції get_client."""

    @patch.dict('os.environ', {'GOOGLE_APPLICATION_CREDENTIALS': '/path/to/creds.json'})
    @patch('app.connectors.google_sheets.os.path.exists')
    @patch('app.connectors.google_sheets.Credentials.from_service_account_file')
    @patch('app.connectors.google_sheets.gspread.authorize')
    def test_get_client_success(self, mock_authorize, mock_creds, mock_exists):
        """Тест успішного створення Google Sheets клієнта."""
        # Arrange
        mock_exists.return_value = True
        mock_credentials = Mock()
        mock_creds.return_value = mock_credentials
        mock_client = Mock()
        mock_authorize.return_value = mock_client

        # Act
        result = google_sheets.get_client()

        # Assert
        assert result == mock_client
        mock_creds.assert_called_once_with('/path/to/creds.json', scopes=google_sheets.SCOPES)
        mock_authorize.assert_called_once_with(mock_credentials)

    @patch.dict('os.environ', {}, clear=True)
    def test_get_client_no_credentials(self):
        """Тест помилки коли GOOGLE_APPLICATION_CREDENTIALS не встановлено."""
        # Act & Assert
        with pytest.raises(RuntimeError, match="GOOGLE_APPLICATION_CREDENTIALS file not found"):
            google_sheets.get_client()

    @patch.dict('os.environ', {'GOOGLE_APPLICATION_CREDENTIALS': '/nonexistent/path.json'})
    @patch('app.connectors.google_sheets.os.path.exists')
    def test_get_client_file_not_exists(self, mock_exists):
        """Тест помилки коли файл credentials не існує."""
        # Arrange
        mock_exists.return_value = False

        # Act & Assert
        with pytest.raises(RuntimeError, match="GOOGLE_APPLICATION_CREDENTIALS file not found"):
            google_sheets.get_client()


class TestUpsertWorksheet:
    """Тести для допоміжної функції _upsert_worksheet."""

    def test_upsert_worksheet_exists(self):
        """Тест оновлення існуючого worksheet."""
        # Arrange
        mock_gc = Mock()
        mock_sheet = Mock()
        mock_worksheet = Mock()
        mock_gc.open_by_key.return_value = mock_sheet
        mock_sheet.worksheet.return_value = mock_worksheet
        headers = ["col1", "col2", "col3"]

        # Act
        result = google_sheets._upsert_worksheet(mock_gc, "sheet_123", "TestSheet", headers)

        # Assert
        assert result == mock_worksheet
        mock_sheet.worksheet.assert_called_once_with("TestSheet")
        mock_worksheet.clear.assert_called_once()
        mock_worksheet.update.assert_called_once_with("A1", [headers])

    def test_upsert_worksheet_not_exists(self):
        """Тест створення нового worksheet."""
        # Arrange
        from gspread.exceptions import WorksheetNotFound
        mock_gc = Mock()
        mock_sheet = Mock()
        mock_worksheet = Mock()
        mock_gc.open_by_key.return_value = mock_sheet
        mock_sheet.worksheet.side_effect = WorksheetNotFound("not found")
        mock_sheet.add_worksheet.return_value = mock_worksheet
        headers = ["col1", "col2"]

        # Act
        result = google_sheets._upsert_worksheet(mock_gc, "sheet_123", "NewSheet", headers)

        # Assert
        assert result == mock_worksheet
        mock_sheet.add_worksheet.assert_called_once()
        mock_worksheet.update.assert_called_once_with("A1", [headers])


class TestWriteInsights:
    """Тести для функції write_insights."""

    @patch('app.connectors.google_sheets._upsert_worksheet')
    def test_write_insights_success(self, mock_upsert):
        """Тест успішного запису insights в Google Sheet."""
        # Arrange
        mock_gc = Mock()
        mock_worksheet = Mock()
        mock_upsert.return_value = mock_worksheet

        insights = [
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
        ]

        # Act
        google_sheets.write_insights(mock_gc, "sheet_123", insights)

        # Assert
        mock_upsert.assert_called_once()
        mock_worksheet.update.assert_called_once()
        call_args = mock_worksheet.update.call_args
        assert call_args[0][0] == "A2"
        assert len(call_args[0][1]) == 1  # один рядок даних

    @patch('app.connectors.google_sheets._upsert_worksheet')
    def test_write_insights_empty_list(self, mock_upsert):
        """Тест запису порожнього списку insights."""
        # Arrange
        mock_gc = Mock()
        mock_worksheet = Mock()
        mock_upsert.return_value = mock_worksheet

        # Act
        google_sheets.write_insights(mock_gc, "sheet_123", [])

        # Assert
        mock_upsert.assert_called_once()
        mock_worksheet.update.assert_not_called()  # не викликається для порожнього списку

    @patch('app.connectors.google_sheets._upsert_worksheet')
    def test_write_insights_multiple_records(self, mock_upsert):
        """Тест запису декількох insights."""
        # Arrange
        mock_gc = Mock()
        mock_worksheet = Mock()
        mock_upsert.return_value = mock_worksheet

        insights = [
            {"campaign_id": "1", "impressions": "100"},
            {"campaign_id": "2", "impressions": "200"},
            {"campaign_id": "3", "impressions": "300"}
        ]

        # Act
        google_sheets.write_insights(mock_gc, "sheet_123", insights)

        # Assert
        call_args = mock_worksheet.update.call_args
        assert len(call_args[0][1]) == 3  # три рядки даних


class TestWriteLeads:
    """Тести для функції write_leads."""

    @patch('app.connectors.google_sheets._upsert_worksheet')
    @patch('app.connectors.google_sheets._extract_field')
    def test_write_leads_success(self, mock_extract, mock_upsert):
        """Тест успішного запису leads в Google Sheet."""
        # Arrange
        mock_gc = Mock()
        mock_worksheet = Mock()
        mock_upsert.return_value = mock_worksheet
        mock_extract.side_effect = ["+380501234567", "test@example.com"]

        leads = [
            {
                "id": "lead_123",
                "created_time": "2025-01-15T10:30:00+0000",
                "page_id": "page_123",
                "form_id": "form_123",
                "crm_status": "new",
                "crm_stage": "contact",
                "field_data": [
                    {"name": "phone_number", "values": ["+380501234567"]},
                    {"name": "email", "values": ["test@example.com"]}
                ]
            }
        ]

        # Act
        google_sheets.write_leads(mock_gc, "sheet_123", leads)

        # Assert
        mock_upsert.assert_called_once()
        mock_worksheet.update.assert_called_once()
        call_args = mock_worksheet.update.call_args
        assert call_args[0][0] == "A2"
        assert len(call_args[0][1]) == 1

    @patch('app.connectors.google_sheets._upsert_worksheet')
    def test_write_leads_empty_list(self, mock_upsert):
        """Тест запису порожнього списку leads."""
        # Arrange
        mock_gc = Mock()
        mock_worksheet = Mock()
        mock_upsert.return_value = mock_worksheet

        # Act
        google_sheets.write_leads(mock_gc, "sheet_123", [])

        # Assert
        mock_upsert.assert_called_once()
        mock_worksheet.update.assert_not_called()


class TestExtractField:
    """Тести для допоміжної функції _extract_field."""

    def test_extract_field_found(self):
        """Тест успішного знаходження поля."""
        # Arrange
        field_data = [
            {"name": "phone_number", "values": ["+380501234567"]},
            {"name": "email", "values": ["test@example.com"]}
        ]

        # Act
        result = google_sheets._extract_field(field_data, {"phone_number", "phone"})

        # Assert
        assert result == "+380501234567"

    def test_extract_field_not_found(self):
        """Тест коли поле не знайдено."""
        # Arrange
        field_data = [
            {"name": "other_field", "values": ["value"]}
        ]

        # Act
        result = google_sheets._extract_field(field_data, {"phone_number", "phone"})

        # Assert
        assert result is None

    def test_extract_field_case_insensitive(self):
        """Тест пошуку поля без урахування регістру."""
        # Arrange
        field_data = [
            {"name": "Phone_Number", "values": ["+380501234567"]}
        ]

        # Act
        result = google_sheets._extract_field(field_data, {"phone_number"})

        # Assert
        assert result == "+380501234567"

    def test_extract_field_empty_values(self):
        """Тест коли поле знайдено але values порожній."""
        # Arrange
        field_data = [
            {"name": "phone_number", "values": []}
        ]

        # Act
        result = google_sheets._extract_field(field_data, {"phone_number"})

        # Assert
        assert result is None

    def test_extract_field_no_values_key(self):
        """Тест коли поле знайдено але немає ключа values."""
        # Arrange
        field_data = [
            {"name": "phone_number"}
        ]

        # Act
        result = google_sheets._extract_field(field_data, {"phone_number"})

        # Assert
        assert result is None
