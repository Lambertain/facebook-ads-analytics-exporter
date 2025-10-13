"""
NetHunt History API Research Script

Диагностический скрипт для исследования возможностей NetHunt API по получению истории статусов.
Проверяет наличие endpoints для history, changelog, activity log.

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

# Конфигурация
# ИСПРАВЛЕНИЕ: NetHunt API использует другой base URL для Zapier endpoints
NETHUNT_BASE_URL = "https://nethunt.com/api/v1/zapier"
NETHUNT_AUTH = os.getenv("NETHUNT_BASIC_AUTH")
TIMEOUT = 15


def nethunt_list_folders_debug():
    """Отладочная версия nethunt_list_folders с детальным логированием."""
    if not NETHUNT_AUTH:
        raise RuntimeError("NETHUNT_BASIC_AUTH is not set")

    # ИСПРАВЛЕНИЕ: правильный endpoint для списка папок
    url = f"{NETHUNT_BASE_URL}/triggers/readable-folder"
    headers = {"Authorization": NETHUNT_AUTH, "Accept": "application/json"}

    print(f"[DEBUG] Request URL: {url}")
    print(f"[DEBUG] Auth header present: {bool(NETHUNT_AUTH)}")
    print(f"[DEBUG] Auth header value (first 20 chars): {NETHUNT_AUTH[:20] if NETHUNT_AUTH else 'None'}")

    try:
        response = requests.get(url, headers=headers, timeout=TIMEOUT)

        print(f"[DEBUG] Response status: {response.status_code}")
        print(f"[DEBUG] Response headers: {dict(response.headers)}")
        print(f"[DEBUG] Response content-type: {response.headers.get('content-type')}")
        print(f"[DEBUG] Response text (first 500 chars): {response.text[:500]}")

        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"[ERROR] Request failed: {type(e).__name__}: {e}")
        raise

# Список endpoints для тестирования (на основе документации)
# ИСПРАВЛЕНИЕ #2: NetHunt Zapier API требует {folderId} в URL пути!
POSSIBLE_ENDPOINTS = [
    # Обновленные записи (с историей изменений полей)
    "/triggers/updated-record/{folder_id}",

    # Новые записи
    "/triggers/new-record/{folder_id}",

    # История изменений записи (КЛЮЧЕВОЙ ENDPOINT)
    "/triggers/record-change/{folder_id}",

    # Комментарии
    "/triggers/new-comment/{folder_id}",

    # Логи звонков
    "/triggers/new-call-log/{folder_id}",

    # Новый email
    "/triggers/new-email/{folder_id}",

    # Поиск записей
    "/searches/find-record/{folder_id}",
]


def test_endpoint(
    endpoint_template: str,
    folder_id: str,
    record_id: Optional[str] = None,
    method: str = "GET"
) -> Dict[str, Any]:
    """
    Тестирование одного endpoint.

    Args:
        endpoint_template: Шаблон endpoint с {folder_id} и опционально {record_id}
        folder_id: ID папки NetHunt
        record_id: ID записи (опционально)
        method: HTTP метод (POST или GET)

    Returns:
        Результат тестирования с информацией об успешности и данных
    """
    # Заменяем плейсхолдеры в URL пути
    endpoint = endpoint_template.replace("{folder_id}", folder_id)
    if record_id:
        endpoint = endpoint.replace("{record_id}", record_id)

    url = NETHUNT_BASE_URL.rstrip('/') + endpoint

    headers = {
        "Authorization": NETHUNT_AUTH,
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    # Дополнительные query параметры (если нужны)
    params = {}

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
        # NetHunt Zapier API использует GET
        if method == "GET":
            response = requests.get(
                url,
                headers=headers,
                params=params if params else None,
                timeout=TIMEOUT
            )
        else:  # POST
            response = requests.post(
                url,
                headers=headers,
                json=params if params else {},
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


def get_sample_record_id(folder_id: str) -> Optional[str]:
    """
    Получить ID первой записи из папки для тестирования.

    Args:
        folder_id: ID папки NetHunt

    Returns:
        ID записи или None если не удалось получить
    """
    url = f"{NETHUNT_BASE_URL}/folders/{folder_id}/records"
    headers = {
        "Authorization": NETHUNT_AUTH,
        "Accept": "application/json"
    }

    try:
        response = requests.get(
            url,
            headers=headers,
            params={"limit": 1},
            timeout=TIMEOUT
        )

        print(f"[DEBUG] Record request status: {response.status_code}")
        print(f"[DEBUG] Response headers: {dict(response.headers)}")
        print(f"[DEBUG] Response text (first 200 chars): {response.text[:200]}")

        if response.status_code == 200:
            data = response.json()

            # NetHunt может возвращать {records: [...]} или просто [...]
            records = data.get("records", data) if isinstance(data, dict) else data

            if records and len(records) > 0:
                record_id = records[0].get("id")
                record_name = records[0].get("name", "Unknown")
                print(f"[OK] Используем для тестирования: Record ID {record_id} ({record_name})")
                return record_id

    except Exception as e:
        print(f"[ERROR] Не удалось получить sample record: {e}")

    return None


def print_result(result: Dict[str, Any]):
    """Красивый вывод результата тестирования."""
    status_emoji = "[OK]" if result["success"] else "[FAIL]"
    print(f"\n{status_emoji} {result['method']} {result['endpoint']}")
    print(f"   Status Code: {result['status_code']}")

    if result["success"]:
        print(f"   [SUCCESS] Endpoint работает!")

        # Показываем структуру ответа
        response = result["response"]
        if isinstance(response, dict):
            keys = list(response.keys())
            print(f"   Response keys: {keys}")

            # Анализируем структуру для record-change endpoint
            if "changes" in response or "records" in response:
                items = response.get("changes", response.get("records", []))
                if isinstance(items, list):
                    items_count = len(items)
                    print(f"   Items count: {items_count}")

                    # Показываем первый item если есть
                    if items:
                        first_item = items[0]
                        if isinstance(first_item, dict):
                            print(f"   First item keys: {list(first_item.keys())}")

                            # Для record-change показываем детали изменения
                            if "fieldChanges" in first_item or "field_changes" in first_item:
                                field_changes = first_item.get("fieldChanges", first_item.get("field_changes", []))
                                print(f"   Field changes count: {len(field_changes)}")
        elif isinstance(response, list):
            print(f"   Response is array with {len(response)} items")
            if response:
                print(f"   First item keys: {list(response[0].keys()) if isinstance(response[0], dict) else 'not a dict'}")
    else:
        error_msg = result["error"]
        if isinstance(error_msg, dict):
            error_name = error_msg.get("name", "Unknown error")
            error_message = error_msg.get("message", "No message")
            print(f"   [ERROR] {error_name}: {error_message}")
        else:
            print(f"   [ERROR] {error_msg}")


def save_results_to_file(results: List[Dict[str, Any]], filename: str = "nethunt_api_research_results.json"):
    """Сохранение результатов в JSON файл."""
    output_path = os.path.join(os.path.dirname(__file__), filename)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n[INFO] Результаты сохранены в: {output_path}")


def main():
    """Главная функция исследования."""
    print("=" * 80)
    print("NetHunt History API Research")
    print("=" * 80)

    # Проверка конфигурации
    if not NETHUNT_AUTH:
        print("[ERROR] NETHUNT_BASIC_AUTH не настроен в .env")
        print("\nУстановите переменную окружения:")
        print('NETHUNT_BASIC_AUTH="Basic <base64_encoded_credentials>"')
        return

    print(f"\n[INFO] Base URL: {NETHUNT_BASE_URL}")
    print(f"[INFO] Auth configured: Yes")

    # Получаем список папок
    print("\n[INFO] Получаем список папок NetHunt...")
    try:
        folders = nethunt_list_folders_debug()
        if not folders:
            print("[ERROR] Нет доступных папок в NetHunt")
            return

        print(f"[OK] Найдено папок: {len(folders)}")

        # Используем первую папку для тестирования
        test_folder = folders[0]
        folder_id = test_folder.get("id")
        folder_name = test_folder.get("name", "Unknown")

        print(f"[INFO] Используем папку: {folder_name} (ID: {folder_id})")

    except Exception as e:
        print(f"[ERROR] Не удалось получить список папок: {e}")
        return

    # Получаем sample record ID
    print("\n[INFO] Получаем sample record для тестирования...")
    record_id = get_sample_record_id(folder_id)

    if not record_id:
        print("[WARNING] Не удалось получить record ID, будем тестировать только folder-level endpoints")

    # Тестируем все endpoints
    print("\n" + "=" * 80)
    print(f"Тестирование {len(POSSIBLE_ENDPOINTS)} возможных endpoints")
    print("=" * 80)

    all_results = []
    successful_endpoints = []

    for endpoint_template in POSSIBLE_ENDPOINTS:
        # Проверяем нужен ли record_id для этого endpoint
        needs_record_id = "{record_id}" in endpoint_template

        if needs_record_id and not record_id:
            print(f"\n[SKIP] {endpoint_template} (требуется record_id)")
            continue

        # Пробуем GET (основной метод для NetHunt API)
        result_get = test_endpoint(endpoint_template, folder_id, record_id, method="GET")
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
        print("\n[SUCCESS] НАЙДЕННЫЕ РАБОЧИЕ ENDPOINTS:")
        for result in successful_endpoints:
            print(f"   [OK] {result['method']} {result['endpoint']}")
            print(f"     URL: {result['url']}")

            # Показываем пример структуры данных
            if isinstance(result["response"], dict):
                response_preview = json.dumps(result["response"], indent=6, ensure_ascii=False)
                print(f"     Response structure: {response_preview[:500]}...")

        # Анализ найденных endpoints
        print("\n[INFO] АНАЛИЗ НАЙДЕННЫХ ENDPOINTS:")

        has_history = any("record-change" in r["endpoint"] for r in successful_endpoints)
        has_updated = any("updated-record" in r["endpoint"] for r in successful_endpoints)
        has_new = any("new-record" in r["endpoint"] for r in successful_endpoints)

        if has_history:
            print("   [OK] NetHunt API ПРЕДОСТАВЛЯЕТ историю изменений через /triggers/record-change!")
            print("   [OK] Можно реализовать РЕАЛЬНОЕ отслеживание истории статусов")
            print("\n   РЕКОМЕНДАЦИЯ:")
            print("   1. Использовать /triggers/record-change/{folder_id} для получения изменений")
            print("   2. Фильтровать изменения по полю статуса")
            print("   3. Строить полную историю пути лида через воронку")

        if has_updated:
            print("   [OK] Доступен endpoint /triggers/updated-record (для отслеживания обновлений)")

        if has_new:
            print("   [OK] Доступен endpoint /triggers/new-record (для отслеживания новых записей)")

    else:
        print("\n[FAIL] К сожалению, ни один из проверенных endpoints не вернул успешный ответ.")
        print("\nВОЗМОЖНЫЕ ПРИЧИНЫ:")
        print("1. Неправильная авторизация (проверьте NETHUNT_BASIC_AUTH)")
        print("2. Недостаточно прав доступа к API")
        print("3. Endpoint существует, но имеет другое название")

        print("\nРЕКОМЕНДАЦИИ:")
        print("1. Проверить правильность NETHUNT_BASIC_AUTH")
        print("2. Связаться с поддержкой NetHunt для уточнения API")
        print("3. Если history недоступен - реализовать inference алгоритм (как для AlfaCRM)")

    # Сохраняем результаты
    save_results_to_file(all_results)

    print("\n" + "=" * 80)
    print("Исследование завершено")
    print("=" * 80)


if __name__ == "__main__":
    main()
