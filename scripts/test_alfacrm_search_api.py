"""
Тестовый скрипт для исследования API поиска AlfaCRM.
Цель: Найти endpoint который использует Web UI для поиска по телефону.
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

from connectors.crm import alfacrm_auth_get_token, alfacrm_list_students


def test_customer_search_by_phone(phone: str):
    """
    Тест поиска клиента по телефону через различные endpoints.

    Args:
        phone: Телефон для поиска
    """
    print("=" * 80)
    print(f"ПОИСК КЛИЕНТА ПО ТЕЛЕФОНУ: {phone}")
    print("=" * 80)

    try:
        token = alfacrm_auth_get_token()
        print(f"\nОК Получен токен: {token[:20]}...")
    except Exception as e:
        print(f"\nERROR: Не удалось получить токен: {e}")
        return

    base_url = os.getenv("ALFACRM_BASE_URL")
    company_id = os.getenv("ALFACRM_COMPANY_ID")

    # Возможные endpoints для поиска
    search_endpoints = [
        # Поиск через customer/index с фильтрацией
        {
            "name": "customer/index с фильтром phone",
            "method": "POST",
            "url": f"{base_url.rstrip('/')}/v2api/customer/index",
            "payload": {
                "branch_ids": [int(company_id)],
                "phone": phone,
                "page": 1,
                "page_size": 10
            }
        },
        # Поиск через search endpoint
        {
            "name": "customer/search",
            "method": "POST",
            "url": f"{base_url.rstrip('/')}/v2api/customer/search",
            "payload": {
                "query": phone,
                "branch_id": int(company_id)
            }
        },
        # Автокомплит (может использовать Web UI)
        {
            "name": "customer/autocomplete",
            "method": "GET",
            "url": f"{base_url.rstrip('/')}/v2api/customer/autocomplete",
            "params": {
                "term": phone,
                "branch_id": company_id
            }
        },
        # Поиск через lead endpoints
        {
            "name": "lead/search",
            "method": "POST",
            "url": f"{base_url.rstrip('/')}/v2api/lead/search",
            "payload": {
                "phone": phone,
                "branch_id": int(company_id)
            }
        },
    ]

    for endpoint_config in search_endpoints:
        print("\n" + "-" * 80)
        print(f"ТЕСТ: {endpoint_config['name']}")
        print("-" * 80)

        try:
            if endpoint_config["method"] == "POST":
                response = requests.post(
                    endpoint_config["url"],
                    headers={"X-ALFACRM-TOKEN": token},
                    json=endpoint_config.get("payload", {}),
                    timeout=15
                )
            else:  # GET
                response = requests.get(
                    endpoint_config["url"],
                    headers={"X-ALFACRM-TOKEN": token},
                    params=endpoint_config.get("params", {}),
                    timeout=15
                )

            print(f"Status Code: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                print("\nOK НАЙДЕН!")
                print(json.dumps(data, indent=2, ensure_ascii=False)[:2000])

                # Проверяем есть ли информация о статусах
                if isinstance(data, dict):
                    items = data.get("items", data.get("data", []))
                    if items and len(items) > 0:
                        first_item = items[0]
                        print("\n" + "=" * 80)
                        print("АНАЛИЗ ПЕРВОГО РЕЗУЛЬТАТА:")
                        print("=" * 80)

                        # Ищем поля связанные со статусами
                        status_related_keys = [k for k in first_item.keys()
                                              if any(word in k.lower() for word in
                                                   ['status', 'history', 'timeline', 'lead'])]

                        if status_related_keys:
                            print("\nНайдены поля связанные со статусами:")
                            for key in status_related_keys:
                                print(f"  - {key}: {first_item[key]}")
                        else:
                            print("\nНЕТ полей связанных с историей статусов")
                            print(f"Доступные поля: {list(first_item.keys())}")

            elif response.status_code == 404:
                print("NOT FOUND (404)")
            else:
                print(f"ERROR: {response.status_code}")
                print(f"Response: {response.text[:500]}")

        except Exception as e:
            print(f"ERROR: {type(e).__name__}: {e}")


def analyze_customer_full_data(customer_id: int):
    """
    Получить полные данные о клиенте через customer/index и проанализировать.
    """
    print("\n" + "=" * 80)
    print(f"АНАЛИЗ ПОЛНЫХ ДАННЫХ КЛИЕНТА ID={customer_id}")
    print("=" * 80)

    try:
        students_data = alfacrm_list_students(page=1, page_size=1000)
        students = students_data.get("items", []) if isinstance(students_data, dict) else students_data

        # Найти нужного клиента
        target_student = None
        for student in students:
            if student.get("id") == customer_id:
                target_student = student
                break

        if not target_student:
            print(f"ERROR: Клиент с ID {customer_id} не найден")
            return

        print("\nПОЛНЫЕ ДАННЫЕ КЛИЕНТА:")
        print(json.dumps(target_student, indent=2, ensure_ascii=False))

        print("\n" + "=" * 80)
        print("ПОИСК ИСТОРИИ СТАТУСОВ:")
        print("=" * 80)

        # Проверяем все поля
        all_keys = list(target_student.keys())
        print(f"\nВсего полей: {len(all_keys)}")
        print(f"Поля: {all_keys}")

        # Ищем поля со статусами
        status_keys = [k for k in all_keys if any(word in k.lower() for word in
                                                  ['status', 'history', 'lead', 'stage', 'timeline'])]

        if status_keys:
            print(f"\nНайдены поля связанные со статусами: {status_keys}")
            for key in status_keys:
                print(f"\n{key}:")
                print(f"  {target_student[key]}")
        else:
            print("\nНЕТ полей с историей статусов в customer/index")

    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("Получаем тестового клиента...")

    try:
        students_data = alfacrm_list_students(page=1, page_size=5)
        students = students_data.get("items", []) if isinstance(students_data, dict) else students_data

        if not students:
            print("ERROR: Не удалось получить клиентов")
            sys.exit(1)

        # Берем первого клиента с телефоном
        test_student = None
        for student in students:
            phones = student.get("phone", [])
            if phones:
                test_student = student
                break

        if not test_student:
            print("ERROR: Не найден клиент с телефоном")
            sys.exit(1)

        customer_id = test_student.get("id")
        customer_name = test_student.get("name", "Unknown")
        customer_phone = test_student.get("phone", [""])[0]
        current_status = test_student.get("lead_status_id")

        print(f"\nТЕСТОВЫЙ КЛИЕНТ:")
        print(f"  ID: {customer_id}")
        print(f"  Имя: {customer_name}")
        print(f"  Телефон: {customer_phone}")
        print(f"  Текущий статус: {current_status}")
        print("")

        # Тест 1: Поиск по телефону через разные endpoints
        test_customer_search_by_phone(customer_phone)

        # Тест 2: Анализ полных данных клиента
        analyze_customer_full_data(customer_id)

    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
