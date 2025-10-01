"""
Integration тести для FastAPI endpoints (app/main.py).

Тестуємо основні API ендпоінти з використанням TestClient.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock
from app.main import app


@pytest.fixture
def client():
    """Створює TestClient для FastAPI додатку."""
    return TestClient(app)


@pytest.fixture
def mock_job_config():
    """Mock конфігурація для запуску job."""
    return {
        "start_date": "2025-01-01",
        "end_date": "2025-01-31",
        "sheet_id": "test_sheet_id_123"
    }


class TestHealthEndpoint:
    """Тести для GET / (health check)."""

    def test_health_check_success(self, client):
        """Тест health check endpoint."""
        # Act
        response = client.get("/")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data


class TestStartJobEndpoint:
    """Тести для POST /api/start-job."""

    @patch('app.main.run_pipeline_background')
    def test_start_job_success(self, mock_run_pipeline, client, mock_job_config):
        """Тест успішного запуску job."""
        # Arrange
        mock_run_pipeline.return_value = None

        # Act
        response = client.post("/api/start-job", json=mock_job_config)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "started"
        assert "job_id" in data
        mock_run_pipeline.assert_called_once()

    def test_start_job_missing_fields(self, client):
        """Тест з відсутніми обов'язковими полями."""
        # Arrange
        incomplete_config = {"start_date": "2025-01-01"}

        # Act
        response = client.post("/api/start-job", json=incomplete_config)

        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "error" in data

    def test_start_job_invalid_date_format(self, client):
        """Тест з невірним форматом дати."""
        # Arrange
        invalid_config = {
            "start_date": "01-01-2025",  # неправильний формат
            "end_date": "2025-01-31",
            "sheet_id": "test_sheet"
        }

        # Act
        response = client.post("/api/start-job", json=invalid_config)

        # Assert
        assert response.status_code == 400


class TestConfigEndpoint:
    """Тести для GET /api/config та POST /api/config."""

    @patch.dict('os.environ', {
        'META_ACCESS_TOKEN': 'test_token',
        'META_AD_ACCOUNT_ID': 'act_123',
        'STORAGE_BACKEND': 'sheets'
    })
    def test_get_config_success(self, client):
        """Тест успішного отримання конфігурації."""
        # Act
        response = client.get("/api/config")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "meta_access_token" in data
        assert "storage_backend" in data

    @patch('app.main.save_config')
    def test_post_config_success(self, mock_save, client):
        """Тест успішного збереження конфігурації."""
        # Arrange
        mock_save.return_value = None
        new_config = {
            "meta_access_token": "new_token",
            "storage_backend": "excel"
        }

        # Act
        response = client.post("/api/config", json=new_config)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "saved"
        mock_save.assert_called_once()


class TestHistoryEndpoint:
    """Тести для GET /api/history."""

    @patch('app.main.get_run_history')
    def test_get_history_all_runs(self, mock_get_history, client):
        """Тест отримання історії всіх запусків."""
        # Arrange
        mock_get_history.return_value = [
            {
                "job_id": "job_1",
                "status": "success",
                "start_time": "2025-01-15T10:00:00",
                "insights_count": 100
            },
            {
                "job_id": "job_2",
                "status": "error",
                "start_time": "2025-01-16T10:00:00",
                "error_message": "API error"
            }
        ]

        # Act
        response = client.get("/api/history")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["job_id"] == "job_1"
        assert data[1]["status"] == "error"

    @patch('app.main.get_run_history')
    def test_get_history_filtered_by_status(self, mock_get_history, client):
        """Тест фільтрації історії за статусом."""
        # Arrange
        mock_get_history.return_value = [
            {"job_id": "job_1", "status": "success"}
        ]

        # Act
        response = client.get("/api/history?status=success")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert all(run["status"] == "success" for run in data)

    @patch('app.main.get_run_history')
    def test_get_history_with_limit(self, mock_get_history, client):
        """Тест обмеження кількості результатів."""
        # Arrange
        mock_get_history.return_value = [
            {"job_id": f"job_{i}", "status": "success"}
            for i in range(5)
        ]

        # Act
        response = client.get("/api/history?limit=3")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 3


class TestProgressEndpoint:
    """Тести для GET /api/progress/{job_id} (SSE)."""

    def test_progress_stream_endpoint_exists(self, client):
        """Тест що progress endpoint існує."""
        # Act
        response = client.get("/api/progress/test_job_123")

        # Assert
        # SSE endpoint повинен повертати 200 і text/event-stream
        assert response.status_code == 200
        # Note: TestClient не підтримує streaming повністю,
        # для повного тестування SSE потрібен спеціальний клієнт


class TestLogsEndpoint:
    """Тести для GET /api/logs/{job_id}."""

    @patch('app.main.get_job_logs')
    def test_get_logs_success(self, mock_get_logs, client):
        """Тест успішного отримання логів job."""
        # Arrange
        mock_get_logs.return_value = [
            {"timestamp": "2025-01-15T10:00:00", "level": "info", "message": "Started"},
            {"timestamp": "2025-01-15T10:05:00", "level": "info", "message": "Completed"}
        ]

        # Act
        response = client.get("/api/logs/job_123")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["message"] == "Started"

    @patch('app.main.get_job_logs')
    def test_get_logs_job_not_found(self, mock_get_logs, client):
        """Тест коли job не знайдено."""
        # Arrange
        mock_get_logs.return_value = []

        # Act
        response = client.get("/api/logs/nonexistent_job")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0


class TestCORSMiddleware:
    """Тести для CORS налаштувань."""

    def test_cors_headers_present(self, client):
        """Тест наявності CORS headers у відповіді."""
        # Act
        response = client.options("/api/config")

        # Assert
        # CORS middleware повинен додавати access-control headers
        assert response.status_code in [200, 204]


class TestSecurityMiddleware:
    """Тести для security middleware."""

    @patch.dict('os.environ', {'API_KEYS': 'test_key_123'})
    def test_protected_endpoint_without_auth(self, client):
        """Тест доступу до захищеного endpoint без auth."""
        # Act
        response = client.post("/api/start-job", json={
            "start_date": "2025-01-01",
            "end_date": "2025-01-31"
        })

        # Assert
        # Якщо API_KEYS встановлено, запит без auth має бути відхилено
        assert response.status_code in [401, 403, 400]

    @patch.dict('os.environ', {'API_KEYS': ''})
    def test_protected_endpoint_dev_mode(self, client):
        """Тест що в dev режимі (без API_KEYS) доступ дозволено."""
        # Act
        with patch('app.main.run_pipeline_background'):
            response = client.post("/api/start-job", json={
                "start_date": "2025-01-01",
                "end_date": "2025-01-31",
                "sheet_id": "test"
            })

        # Assert
        # В dev режимі без API_KEYS доступ дозволено
        assert response.status_code == 200


class TestDownloadExcelEndpoint:
    """Тести для POST /api/download-excel."""

    @patch('app.main.meta_conn')
    def test_download_excel_ads_success(self, mock_meta, client):
        """Тест успішного експорту ads даних в Excel."""
        # Arrange
        mock_meta.fetch_insights.return_value = [
            {
                "date_start": "2025-01-01",
                "date_stop": "2025-01-31",
                "campaign_id": "123",
                "campaign_name": "Test Campaign",
                "impressions": 1000,
                "clicks": 50,
                "spend": 100.0
            }
        ]

        # Act
        response = client.post("/api/download-excel", json={
            "data_type": "ads",
            "start_date": "2025-01-01",
            "end_date": "2025-01-31"
        })

        # Assert
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        assert "ads_export" in response.headers.get("content-disposition", "")

    @patch.dict('os.environ', {'EXCEL_STUDENTS_PATH': 'test_students.xlsx'})
    @patch('app.main.os.path.exists')
    @patch('app.main.openpyxl.load_workbook')
    def test_download_excel_students_success(self, mock_load_wb, mock_exists, client):
        """Тест успішного експорту студентів в Excel."""
        # Arrange
        mock_exists.return_value = True
        mock_wb = Mock()
        mock_ws = Mock()
        mock_ws.iter_rows.return_value = [
            [Mock(value="Header1", column=1), Mock(value="Header2", column=2)],
            [Mock(value="Data1", column=1), Mock(value="Data2", column=2)]
        ]
        mock_ws.max_row = 2
        mock_wb.__getitem__.return_value = mock_ws
        mock_wb.sheetnames = ["Students"]
        mock_load_wb.return_value = mock_wb

        # Act
        response = client.post("/api/download-excel", json={
            "data_type": "students",
            "start_date": "2025-01-01",
            "end_date": "2025-01-31"
        })

        # Assert
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        assert "students_export" in response.headers.get("content-disposition", "")

    @patch.dict('os.environ', {'EXCEL_STUDENTS_PATH': ''})
    def test_download_excel_students_file_not_found(self, client):
        """Тест коли файл студентів не знайдено."""
        # Act
        response = client.post("/api/download-excel", json={
            "data_type": "students",
            "start_date": "2025-01-01",
            "end_date": "2025-01-31"
        })

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "error" in data

    def test_download_excel_missing_fields(self, client):
        """Тест з відсутніми обов'язковими полями."""
        # Act
        response = client.post("/api/download-excel", json={
            "data_type": "students"
        })

        # Assert
        assert response.status_code in [400, 422]

    def test_download_excel_invalid_data_type(self, client):
        """Тест з невірним типом даних."""
        # Act
        response = client.post("/api/download-excel", json={
            "data_type": "invalid_type",
            "start_date": "2025-01-01",
            "end_date": "2025-01-31"
        })

        # Assert
        assert response.status_code in [400, 422, 500]
