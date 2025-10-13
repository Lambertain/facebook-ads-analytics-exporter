"""
Тестовый скрипт для проверки endpoint /v2api/customer/view
Цель: Получить детальную информацию о клиенте включая историю статусов.
"""
import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv
import requests

# Добавить путь к проекту
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "app"))

load_dotenv(project_root / ".env")

from connectors.crm import alfacrm_auth_get_token


def test_customer_view(customer_id: int):
    """
    Тестирование endpoint /v2api/customer/view для получения детальной информации.

    Args:
        customer_id: ID клиента в AlfaCRM
    """
    print("=" * 80)
    print(f"ТЕСТ: /v2api/customer/view для customer_id={customer_id}")
    print("=" * 80)

    # Получаем токен
    try:
        token = alfacrm_auth_get_token()
        print(f"\nОК Получен токен: {token[:20]}...")
    except Exception as e:
        print(f"\nERROR: Не удалось получить токен: {e}")
        return

    base_url = os.getenv("ALFACRM_BASE_URL")
    company_id = os.getenv("ALFACRM_COMPANY_ID")

    # Тестируем endpoint /v2api/customer/view
    url = base_url.rstrip('/') + f"/v2api/customer/view"

    # Пробуем разные варианты параметров
    print("\n" + "-" * 80)
    print("ВАРИАНТ 1: GET запрос с id в query params")
    print("-" * 80)

    try:
        response = requests.get(
            url,
            headers={"X-ALFACRM-TOKEN": token},
            params={"id": customer_id, "branch_id": company_id},
            timeout=15
        )
        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print("\nOK Получен ответ:")
            print(json.dumps(data, indent=2, ensure_ascii=False))

            # Ищем поля связанные с историей статусов
            print("\n" + "=" * 80)
            print("ПОИСК ИСТОРИИ СТАТУСОВ В ОТВЕТЕ:")
            print("=" * 80)

            # Проверяем возможные поля
            status_fields = [
                "lead_status_id", "lead_status", "status_id", "status",
                "history", "status_history", "timeline", "changes",
                "lead_history", "statuses"
            ]

            for field in status_fields:
                if field in data:
                    print(f"\nНАЙДЕНО ПОЛЕ '{field}':")
                    print(json.dumps(data[field], indent=2, ensure_ascii=False))

            # Проверяем вложенные объекты
            if "data" in data and isinstance(data["data"], dict):
                print("\nПроверка вложенного объекта 'data':")
                for field in status_fields:
                    if field in data["data"]:
                        print(f"\nНАЙДЕНО ПОЛЕ 'data.{field}':")
                        print(json.dumps(data["data"][field], indent=2, ensure_ascii=False))
        else:
            print(f"ERROR: {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}")

    # Пробуем POST запрос
    print("\n" + "-" * 80)
    print("ВАРИАНТ 2: POST запрос с id в body")
    print("-" * 80)

    try:
        response = requests.post(
            url,
            headers={"X-ALFACRM-TOKEN": token},
            json={"id": customer_id, "branch_id": int(company_id)},
            timeout=15
        )
        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print("\nOK Получен ответ:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
        else:
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}")


def test_customer_timeline(customer_id: int):
    """
    Проверка возможного endpoint для timeline/истории клиента.
    """
    print("\n" + "=" * 80)
    print(f"ТЕСТ: Поиск endpoint для timeline customer_id={customer_id}")
    print("=" * 80)

    try:
        token = alfacrm_auth_get_token()
    except Exception as e:
        print(f"ERROR: Не удалось получить токен: {e}")
        return

    base_url = os.getenv("ALFACRM_BASE_URL")

    # Возможные endpoints для истории
    possible_endpoints = [
        f"/v2api/customer/timeline",
        f"/v2api/customer/history",
        f"/v2api/customer/status-history",
        f"/v2api/customer/changes",
        f"/v2api/lead/history",
        f"/v2api/lead/timeline",
    ]

    for endpoint in possible_endpoints:
        url = base_url.rstrip('/') + endpoint
        print(f"\nПроверка: {endpoint}")

        try:
            # Пробуем GET
            response = requests.get(
                url,
                headers={"X-ALFACRM-TOKEN": token},
                params={"customer_id": customer_id},
                timeout=10
            )

            if response.status_code == 200:
                print(f"  OK НАЙДЕН! Status: {response.status_code}")
                data = response.json()
                print(f"  Response: {json.dumps(data, indent=2, ensure_ascii=False)[:500]}...")
            elif response.status_code == 404:
                print(f"  NOT FOUND (404)")
            else:
                print(f"  Status: {response.status_code}")
        except Exception as e:
            print(f"  ERROR: {type(e).__name__}: {e}")


if __name__ == "__main__":
    # Тестируем на первом доступном клиенте
    print("Получаем список клиентов для тестирования...")

    from connectors.crm import alfacrm_list_students

    try:
        students_data = alfacrm_list_students(page=1, page_size=5)
        students = students_data.get("items", []) if isinstance(students_data, dict) else students_data

        if not students:
            print("ERROR: Не удалось получить клиентов для теста")
            sys.exit(1)

        # Берем первого клиента
        first_student = students[0]
        customer_id = first_student.get("id")
        customer_name = first_student.get("name", "Unknown")
        current_status = first_student.get("lead_status_id")

        print(f"\nТЕСТОВЫЙ КЛИЕНТ:")
        print(f"  ID: {customer_id}")
        print(f"  Имя: {customer_name}")
        print(f"  Текущий статус: {current_status}")
        print("")

        # Тест 1: customer/view
        test_customer_view(customer_id)

        # Тест 2: поиск timeline endpoints
        test_customer_timeline(customer_id)

    except Exception as e:
        print(f"ERROR при получении клиентов: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
