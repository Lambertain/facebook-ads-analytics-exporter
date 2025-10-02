"""
Unit тести для CRM connector (app/connectors/crm.py).

Тестуємо enrich_leads_with_status та допоміжні функції для NetHunt та AlfaCRM.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from app.connectors import crm


class TestEnrichLeadsWithStatus:
    """Тести для головної функції enrich_leads_with_status."""

    @pytest.mark.asyncio
    async def test_enrich_leads_provider_none(self):
        """Тест з provider='none' - повертає leads без CRM даних."""
        # Arrange
        leads = [
            {"id": "lead_1", "email": "test1@example.com"},
            {"id": "lead_2", "email": "test2@example.com"}
        ]

        # Act
        result = await crm.enrich_leads_with_status(leads, "none")

        # Assert
        assert len(result) == 2
        assert result[0]["crm_status"] is None
        assert result[0]["crm_stage"] is None
        assert result[1]["crm_status"] is None

    @pytest.mark.asyncio
    @patch('app.connectors.crm._enrich_amocrm')
    async def test_enrich_leads_provider_amocrm(self, mock_enrich):
        """Тест з provider='amocrm'."""
        # Arrange
        leads = [{"id": "lead_1"}]
        mock_enrich.return_value = [{"id": "lead_1", "crm_status": "stub", "crm_stage": None}]

        # Act
        result = await crm.enrich_leads_with_status(leads, "amocrm")

        # Assert
        mock_enrich.assert_called_once_with(leads)
        assert result[0]["crm_status"] == "stub"

    @pytest.mark.asyncio
    @patch('app.connectors.crm._enrich_bitrix')
    async def test_enrich_leads_provider_bitrix24(self, mock_enrich):
        """Тест з provider='bitrix24'."""
        # Arrange
        leads = [{"id": "lead_1"}]
        mock_enrich.return_value = [{"id": "lead_1", "crm_status": "stub", "crm_stage": None}]

        # Act
        result = await crm.enrich_leads_with_status(leads, "bitrix24")

        # Assert
        mock_enrich.assert_called_once_with(leads)

    @pytest.mark.asyncio
    @patch('app.connectors.crm._enrich_nethunt')
    async def test_enrich_leads_provider_nethunt(self, mock_enrich):
        """Тест з provider='nethunt'."""
        # Arrange
        leads = [{"id": "lead_1"}]
        mock_enrich.return_value = [{"id": "lead_1", "crm_status": None, "crm_stage": None}]

        # Act
        result = await crm.enrich_leads_with_status(leads, "nethunt")

        # Assert
        mock_enrich.assert_called_once_with(leads)

    @pytest.mark.asyncio
    @patch('app.connectors.crm._enrich_alfacrm')
    async def test_enrich_leads_provider_alfacrm(self, mock_enrich):
        """Тест з provider='alfacrm'."""
        # Arrange
        leads = [{"id": "lead_1"}]
        mock_enrich.return_value = [{"id": "lead_1", "crm_status": None, "crm_stage": None}]

        # Act
        result = await crm.enrich_leads_with_status(leads, "alfacrm")

        # Assert
        mock_enrich.assert_called_once_with(leads)

    @pytest.mark.asyncio
    async def test_enrich_leads_unknown_provider(self):
        """Тест з невідомим provider - fallback."""
        # Arrange
        leads = [{"id": "lead_1"}]

        # Act
        result = await crm.enrich_leads_with_status(leads, "unknown_crm")

        # Assert
        assert result[0]["crm_status"] == "unknown_provider"
        assert result[0]["crm_stage"] is None


class TestNetHuntHelpers:
    """Тести для NetHunt допоміжних функцій."""

    @patch.dict('os.environ', {'NETHUNT_BASIC_AUTH': 'Basic test123'})
    @patch('app.connectors.crm.requests.get')
    def test_nethunt_list_folders_success(self, mock_get):
        """Тест успішного отримання списку NetHunt folders."""
        # Arrange
        mock_response = Mock()
        mock_response.json.return_value = [
            {"id": "folder_1", "name": "Teachers"},
            {"id": "folder_2", "name": "Students"}
        ]
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        # Act
        result = crm.nethunt_list_folders()

        # Assert
        assert len(result) == 2
        assert result[0]["name"] == "Teachers"
        mock_get.assert_called_once()

    @patch.dict('os.environ', {}, clear=True)
    def test_nethunt_list_folders_no_auth(self):
        """Тест помилки коли NETHUNT_BASIC_AUTH не встановлено."""
        # Act & Assert
        with pytest.raises(RuntimeError, match="NETHUNT_BASIC_AUTH is not set"):
            crm.nethunt_list_folders()

    @patch.dict('os.environ', {'NETHUNT_BASIC_AUTH': 'Basic test123'})
    @patch('app.connectors.crm.requests.get')
    def test_nethunt_folder_fields_success(self, mock_get):
        """Тест отримання полів NetHunt folder."""
        # Arrange
        mock_response = Mock()
        mock_response.json.return_value = {
            "fields": [
                {"id": "field_1", "name": "Email"},
                {"id": "field_2", "name": "Phone"}
            ]
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        # Act
        result = crm.nethunt_folder_fields("folder_123")

        # Assert
        assert "fields" in result
        assert len(result["fields"]) == 2

    @patch.dict('os.environ', {'NETHUNT_BASIC_AUTH': 'Basic test123'})
    @patch('app.connectors.crm.requests.get')
    def test_nethunt_list_records_success(self, mock_get):
        """Тест отримання записів з NetHunt folder."""
        # Arrange
        mock_response = Mock()
        mock_response.json.return_value = {
            "records": [
                {"id": "rec_1", "email": "teacher1@example.com"},
                {"id": "rec_2", "email": "teacher2@example.com"}
            ]
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        # Act
        result = crm.nethunt_list_records("folder_123")

        # Assert
        assert len(result) == 2
        assert result[0]["email"] == "teacher1@example.com"

    @patch.dict('os.environ', {'NETHUNT_BASIC_AUTH': 'Basic test123'})
    @patch('app.connectors.crm.requests.get')
    def test_nethunt_list_records_list_format(self, mock_get):
        """Тест коли API повертає список напряму."""
        # Arrange
        mock_response = Mock()
        mock_response.json.return_value = [
            {"id": "rec_1"},
            {"id": "rec_2"}
        ]
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        # Act
        result = crm.nethunt_list_records("folder_123")

        # Assert
        assert len(result) == 2


class TestAlfaCRMHelpers:
    """Тести для AlfaCRM допоміжних функцій."""

    @patch.dict('os.environ', {
        'ALFACRM_BASE_URL': 'https://test.alfacrm.pro',
        'ALFACRM_EMAIL': 'test@example.com',
        'ALFACRM_API_KEY': 'test_key_123'
    })
    @patch('app.connectors.crm.requests.post')
    def test_alfacrm_auth_get_token_success(self, mock_post):
        """Тест успішної аутентифікації AlfaCRM."""
        # Arrange
        mock_response = Mock()
        mock_response.json.return_value = {"token": "test_token_xyz"}
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        # Act
        result = crm.alfacrm_auth_get_token()

        # Assert
        assert result == "test_token_xyz"
        mock_post.assert_called_once()

    @patch.dict('os.environ', {
        'ALFACRM_BASE_URL': 'https://test.alfacrm.pro',
        'ALFACRM_EMAIL': 'test@example.com',
        'ALFACRM_API_KEY': 'test_key_123'
    })
    @patch('app.connectors.crm.requests.post')
    def test_alfacrm_auth_get_token_nested_data(self, mock_post):
        """Тест отримання токена з вкладеної структури data."""
        # Arrange
        mock_response = Mock()
        mock_response.json.return_value = {"data": {"token": "nested_token"}}
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        # Act
        result = crm.alfacrm_auth_get_token()

        # Assert
        assert result == "nested_token"

    @patch.dict('os.environ', {}, clear=True)
    def test_alfacrm_auth_get_token_no_credentials(self):
        """Тест помилки коли credentials не встановлені."""
        # Act & Assert
        with pytest.raises(RuntimeError, match="ALFACRM_BASE_URL/EMAIL/API_KEY not set"):
            crm.alfacrm_auth_get_token()

    @patch.dict('os.environ', {
        'ALFACRM_BASE_URL': 'https://test.alfacrm.pro',
        'ALFACRM_EMAIL': 'test@example.com',
        'ALFACRM_API_KEY': 'test_key_123'
    })
    @patch('app.connectors.crm.requests.post')
    def test_alfacrm_auth_no_token_in_response(self, mock_post):
        """Тест помилки коли token відсутній у відповіді."""
        # Arrange
        mock_response = Mock()
        mock_response.json.return_value = {"error": "invalid credentials"}
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        # Act & Assert
        with pytest.raises(RuntimeError, match="Failed to get AlfaCRM token"):
            crm.alfacrm_auth_get_token()

    @patch.dict('os.environ', {
        'ALFACRM_BASE_URL': 'https://test.alfacrm.pro',
        'ALFACRM_EMAIL': 'test@example.com',
        'ALFACRM_API_KEY': 'test_key_123',
        'ALFACRM_COMPANY_ID': '123'
    })
    @patch('app.connectors.crm.alfacrm_auth_get_token')
    @patch('app.connectors.crm.requests.post')
    def test_alfacrm_list_students_success(self, mock_post, mock_auth):
        """Тест успішного отримання списку студентів."""
        # Arrange
        mock_auth.return_value = "test_token"
        mock_response = Mock()
        mock_response.json.return_value = {
            "count": 2,
            "items": [
                {"id": 1, "name": "Student 1"},
                {"id": 2, "name": "Student 2"}
            ]
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        # Act
        result = crm.alfacrm_list_students()

        # Assert
        assert "items" in result
        assert len(result["items"]) == 2
        mock_auth.assert_called_once()

    @patch.dict('os.environ', {
        'ALFACRM_BASE_URL': 'https://test.alfacrm.pro',
        'ALFACRM_EMAIL': 'test@example.com',
        'ALFACRM_API_KEY': 'test_key_123'
    }, clear=True)
    @patch('app.connectors.crm.alfacrm_auth_get_token')
    def test_alfacrm_list_students_no_company_id(self, mock_auth):
        """Тест помилки коли COMPANY_ID не встановлено."""
        # Arrange
        mock_auth.return_value = "test_token"

        # Act & Assert
        with pytest.raises(RuntimeError, match="ALFACRM_COMPANY_ID is not set"):
            crm.alfacrm_list_students()

    @patch.dict('os.environ', {
        'ALFACRM_BASE_URL': 'https://test.alfacrm.pro',
        'ALFACRM_EMAIL': 'test@example.com',
        'ALFACRM_API_KEY': 'test_key_123'
    })
    @patch('app.connectors.crm.alfacrm_auth_get_token')
    @patch('app.connectors.crm.requests.get')
    def test_alfacrm_list_companies_success(self, mock_get, mock_auth):
        """Тест отримання списку компаній."""
        # Arrange
        mock_auth.return_value = "test_token"
        mock_response = Mock()
        mock_response.json.return_value = {
            "items": [
                {"id": 123, "name": "Company 1"}
            ]
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        # Act
        result = crm.alfacrm_list_companies()

        # Assert
        assert "items" in result
        mock_auth.assert_called_once()
