"""
AlfaCRM History API Research Script

Диагностический скрипт для исследования возможных endpoints истории статусов в AlfaCRM API.
Проверяет различные варианты endpoints, которые могут содержать историю изменений.

Автор: Archon Implementation Engineer
Дата: 2025-10-10
"""
import os
import sys
import json
import requests
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Добавляем путь к app для импорта существующих функций
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.connectors.crm import alfacrm_auth_get_token

# Конфигурация
ALFACRM_BASE_URL = os.getenv("ALFACRM_BASE_URL")
ALFACRM_COMPANY_ID = os.getenv("ALFACRM_COMPANY_ID")
TIMEOUT = 15

# Список возможных endpoints для тестирования
POSSIBLE_ENDPOINTS = [
    # История клиента
    "/v2api/{branch}/customer/history?id={customer_id}",
    "/v2api/{branch}/customer/changelog?id={customer_id}",
    "/v2api/{branch}/customer/events?id={customer_id}",
    "/v2api/{branch}/customer/log?id={customer_id}",
    "/v2api/{branch}/customer/activity?id={customer_id}",

    # История по lead_status
    "/v2api/{branch}/lead-status-history/index",
    "/v2api/{branch}/customer/lead-status-history?id={customer_id}",

    # Общие history endpoints
    "/v2api/{branch}/history/index",
    "/v2api/{branch}/activity/index",
    "/v2api/{branch}/changelog/index",

    # Customer с расширенными параметрами
    "/v2api/{branch}/customer/view?id={customer_id}&expand=history",
    "/v2api/{branch}/customer/view?id={customer_id}&expand=statusHistory",

    # События (events)
    "/v2api/{branch}/event/index?customer_id={customer_id}",
    "/v2api/{branch}/customer-event/index?customer_id={customer_id}",
]


def test_endpoint(
    token: str,
    endpoint_template: str,
    customer_id: int,
    method: str = "POST"
) -> Dict[str, Any]:
    """
    Тестирование одного endpoint.

    Args:
        token: AlfaCRM токен авторизации
        endpoint_template: Шаблон endpoint (с {branch} и {customer_id})
        customer_id: ID клиента для тестирования
        method: HTTP метод (POST или GET)

    Returns:
        Результат тестирования с информацией об успешности и данными
    """
    # Заменяем плейсхолдеры
    endpoint = endpoint_template.replace("{branch}", str(ALFACRM_COMPANY_ID))
    endpoint = endpoint.replace("{customer_id}", str(customer_id))

    url = ALFACRM_BASE_URL.rstrip('/') + endpoint

    headers = {
        "X-ALFACRM-TOKEN": token,
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    result = {
        "endpoint": endpoint,
        "url": url,
        "method": method,
        "success": False,
        "status_code": None,
        "response": None,
        "error": None
    }

    try:
        if method == "POST":
            response = requests.post(
                url,
                headers=headers,
                json={"page": 0},  # Базовый payload для POST
                timeout=TIMEOUT
            )
        else:  # GET
            response = requests.get(
                url,
                headers=headers,
                timeout=TIMEOUT
            )

        result["status_code"] = response.status_code

        if response.status_code == 200:
            result["success"] = True
            try:
                result["response"] = response.json()
            except:
                result["response"] = response.text
        else:
            try:
                result["error"] = response.json()
            except:
                result["error"] = response.text

    except requests.exceptions.Timeout:
        result["error"] = "Request timeout"
    except requests.exceptions.ConnectionError:
        result["error"] = "Connection error"
    except Exception as e:
        result["error"] = f"{type(e).__name__}: {str(e)}"

    return result


def get_sample_customer_id(token: str) -> Optional[int]:
    """
    Получить ID первого клиента для тестирования.

    Args:
        token: AlfaCRM токен авторизации

    Returns:
        ID клиента или None если не удалось получить
    """
    url = f"{ALFACRM_BASE_URL.rstrip('/')}/v2api/{ALFACRM_COMPANY_ID}/customer/index"
    headers = {
        "X-ALFACRM-TOKEN": token,
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(
            url,
            headers=headers,
            json={"page": 0, "page_size": 1, "is_study": 2},  # Получить первого клиента/лида
            timeout=TIMEOUT
        )

        if response.status_code == 200:
            data = response.json()
            items = data.get("items", [])
            if items:
                customer = items[0]
                customer_id = customer.get("id")
                customer_name = customer.get("name", "Unknown")
                print(f"[OK] Используем для тестирования: Customer ID {customer_id} ({customer_name})")
                return customer_id

    except Exception as e:
        print(f"[ERROR] Не удалось получить sample customer: {e}")

    return None


def print_result(result: Dict[str, Any]):
    """Красивый вывод результата тестирования."""
    status_emoji = "✅" if result["success"] else "❌"
    print(f"\n{status_emoji} {result['method']} {result['endpoint']}")
    print(f"   Status Code: {result['status_code']}")

    if result["success"]:
        print(f"   [SUCCESS] Endpoint работает!")

        # Показываем структуру ответа
        response = result["response"]
        if isinstance(response, dict):
            keys = list(response.keys())
            print(f"   Response keys: {keys}")

            # Если есть items, показываем сколько
            if "items" in response:
                items_count = len(response["items"]) if isinstance(response["items"], list) else "?"
                print(f"   Items count: {items_count}")

                # Показываем первый item если есть
                if isinstance(response["items"], list) and response["items"]:
                    first_item = response["items"][0]
                    if isinstance(first_item, dict):
                        print(f"   First item keys: {list(first_item.keys())}")
    else:
        error_msg = result["error"]
        if isinstance(error_msg, dict):
            error_name = error_msg.get("name", "Unknown error")
            error_message = error_msg.get("message", "No message")
            print(f"   [ERROR] {error_name}: {error_message}")
        else:
            print(f"   [ERROR] {error_msg}")


def save_results_to_file(results: List[Dict[str, Any]], filename: str = "alfacrm_api_research_results.json"):
    """Сохранение результатов в JSON файл."""
    output_path = os.path.join(os.path.dirname(__file__), filename)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n[INFO] Результаты сохранены в: {output_path}")


def main():
    """Главная функция исследования."""
    print("=" * 80)
    print("AlfaCRM History API Research")
    print("=" * 80)

    # Проверка конфигурации
    if not ALFACRM_BASE_URL or not ALFACRM_COMPANY_ID:
        print("[ERROR] ALFACRM_BASE_URL или ALFACRM_COMPANY_ID не настроены в .env")
        return

    print(f"\n[INFO] Base URL: {ALFACRM_BASE_URL}")
    print(f"[INFO] Company ID: {ALFACRM_COMPANY_ID}")

    # Авторизация
    print("\n[INFO] Получаем токен авторизации...")
    try:
        token = alfacrm_auth_get_token()
        print("[OK] Токен получен успешно")
    except Exception as e:
        print(f"[ERROR] Не удалось получить токен: {e}")
        return

    # Получаем sample customer ID
    print("\n[INFO] Получаем sample customer для тестирования...")
    customer_id = get_sample_customer_id(token)

    if not customer_id:
        print("[ERROR] Не удалось получить customer ID для тестирования")
        return

    # Тестируем все endpoints
    print("\n" + "=" * 80)
    print(f"Тестирование {len(POSSIBLE_ENDPOINTS)} возможных endpoints")
    print("=" * 80)

    all_results = []
    successful_endpoints = []

    for endpoint_template in POSSIBLE_ENDPOINTS:
        # Пробуем POST
        result_post = test_endpoint(token, endpoint_template, customer_id, method="POST")
        all_results.append(result_post)
        print_result(result_post)

        if result_post["success"]:
            successful_endpoints.append(result_post)

        # Если POST не сработал, пробуем GET
        if not result_post["success"]:
            result_get = test_endpoint(token, endpoint_template, customer_id, method="GET")
            all_results.append(result_get)
            print_result(result_get)

            if result_get["success"]:
                successful_endpoints.append(result_get)

    # Итоговый отчет
    print("\n" + "=" * 80)
    print("ИТОГОВЫЙ ОТЧЕТ")
    print("=" * 80)

    print(f"\n[INFO] Протестировано endpoints: {len(all_results)}")
    print(f"[INFO] Успешных endpoints: {len(successful_endpoints)}")

    if successful_endpoints:
        print("\n✅ НАЙДЕННЫЕ РАБОЧИЕ ENDPOINTS:")
        for result in successful_endpoints:
            print(f"   • {result['method']} {result['endpoint']}")
            print(f"     URL: {result['url']}")

            # Показываем пример структуры данных
            if isinstance(result["response"], dict):
                print(f"     Response structure: {json.dumps(result['response'], indent=6, ensure_ascii=False)[:500]}...")
    else:
        print("\n❌ К сожалению, ни один из проверенных endpoints не вернул успешный ответ.")
        print("\nВОЗМОЖНЫЕ ПРИЧИНЫ:")
        print("1. AlfaCRM API не предоставляет публичный endpoint для истории статусов")
        print("2. Endpoint существует, но имеет другое название")
        print("3. История доступна только через веб-интерфейс, а не через API")

        print("\nРЕКОМЕНДАЦИИ:")
        print("1. Связаться с поддержкой AlfaCRM (dev@alfacrm.pro)")
        print("2. Проверить внутреннюю документацию AlfaCRM (если есть доступ)")
        print("3. Реализовать альтернативное решение:")
        print("   - Создать собственную таблицу для трекинга истории статусов")
        print("   - Использовать webhooks AlfaCRM для отслеживания изменений в реальном времени")
        print("   - Периодически опрашивать /customer/index и сохранять изменения статусов")

    # Сохраняем результаты
    save_results_to_file(all_results)

    print("\n" + "=" * 80)
    print("Исследование завершено")
    print("=" * 80)


if __name__ == "__main__":
    main()
