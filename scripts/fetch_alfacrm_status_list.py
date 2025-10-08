"""
Получить справочник статусов лидов напрямую из AlfaCRM API.

Цель:
- Запросить все возможные статусы лидов из AlfaCRM
- Получить ID и название каждого статуса
- Автоматически сгенерировать корректный ALFACRM_STATUS_MAPPING

Использование:
    python scripts/fetch_alfacrm_status_list.py
"""
import os
import sys
import requests
from pathlib import Path
from dotenv import load_dotenv

# Добавить путь к проекту
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "app"))

load_dotenv(project_root / ".env")

from connectors.crm import alfacrm_auth_get_token


def print_separator(title: str):
    """Печать разделителя."""
    print(f"\n{'=' * 80}")
    print(f"{title:^80}")
    print(f"{'=' * 80}\n")


def try_endpoint(endpoint: str, base_url: str, token: str) -> dict:
    """Попробовать запрос к endpoint."""
    url = base_url.rstrip('/') + endpoint

    print(f"Попытка: {endpoint}")

    try:
        # Попытка GET
        resp = requests.get(
            url,
            headers={"X-ALFACRM-TOKEN": token},
            timeout=15
        )

        if resp.status_code == 200:
            data = resp.json()
            print(f"  OK GET {endpoint} - {resp.status_code}")
            return {"success": True, "method": "GET", "data": data}

        # Попытка POST с пустым телом
        resp = requests.post(
            url,
            headers={"X-ALFACRM-TOKEN": token},
            json={},
            timeout=15
        )

        if resp.status_code == 200:
            data = resp.json()
            print(f"  OK POST {endpoint} - {resp.status_code}")
            return {"success": True, "method": "POST", "data": data}

        print(f"  FAIL {endpoint} - {resp.status_code}: {resp.text[:100]}")
        return {"success": False, "status": resp.status_code}

    except Exception as e:
        print(f"  ERROR: {type(e).__name__}: {e}")
        return {"success": False, "error": str(e)}


def fetch_lead_statuses():
    """Получить список статусов лидов из AlfaCRM."""
    print_separator("ПОЛУЧЕНИЕ СПРАВОЧНИКА СТАТУСОВ ALFACRM")

    # Получить credentials
    base_url = os.getenv("ALFACRM_BASE_URL")

    if not base_url:
        print("ERROR: ALFACRM_BASE_URL не найден в .env")
        return None

    print(f"AlfaCRM URL: {base_url}")

    # Получить токен
    try:
        token = alfacrm_auth_get_token()
        print(f"Token: {token[:20]}...")
    except Exception as e:
        print(f"ERROR: Не удалось получить токен: {e}")
        return None

    # Список возможных endpoints для получения статусов
    possible_endpoints = [
        "/v2api/lead-status",
        "/v2api/lead-status/index",
        "/v2api/lead_status",
        "/v2api/lead_status/index",
        "/v2api/leadstatus",
        "/v2api/leadstatus/index",
        "/v2api/customer-status",
        "/v2api/customer_status",
        "/v2api/customerstatus",
        "/v2api/status",
        "/v2api/statuses",
        "/v2api/settings/lead-status",
        "/v2api/dictionary/lead-status",
    ]

    print("\nПоиск endpoint для получения статусов...")
    print("-" * 80)

    results = []

    for endpoint in possible_endpoints:
        result = try_endpoint(endpoint, base_url, token)
        if result.get("success"):
            results.append({"endpoint": endpoint, "result": result})

    if not results:
        print("\nERROR: Ни один endpoint не вернул данные")
        print("\nВозможные причины:")
        print("  1. AlfaCRM не предоставляет публичный endpoint для справочника статусов")
        print("  2. Требуются дополнительные параметры в запросе")
        print("  3. Endpoint имеет другое название")
        return None

    print(f"\nУспешно получены данные из {len(results)} endpoint(s)")

    # Анализ результатов
    for item in results:
        endpoint = item["endpoint"]
        data = item["result"]["data"]
        method = item["result"]["method"]

        print(f"\n{endpoint} ({method}):")
        print("-" * 80)

        # Попробовать разные структуры ответа
        if isinstance(data, dict):
            if "items" in data:
                print(f"  Найдено 'items': {len(data['items'])} элементов")
                print_statuses(data["items"])
                return data["items"]
            elif "data" in data:
                print(f"  Найдено 'data': {len(data['data'])} элементов")
                print_statuses(data["data"])
                return data["data"]
            elif "statuses" in data:
                print(f"  Найдено 'statuses': {len(data['statuses'])} элементов")
                print_statuses(data["statuses"])
                return data["statuses"]
            else:
                print(f"  Структура: {list(data.keys())}")
                print(f"  Данные: {data}")
        elif isinstance(data, list):
            print(f"  Массив из {len(data)} элементов")
            print_statuses(data)
            return data

    return None


def print_statuses(statuses: list):
    """Вывести список статусов."""
    if not statuses:
        print("  Пусто")
        return

    print("\n  ID | Название")
    print("  " + "-" * 76)

    for status in statuses[:20]:  # Первые 20
        if isinstance(status, dict):
            status_id = status.get("id") or status.get("status_id") or status.get("lead_status_id")
            name = status.get("name") or status.get("title") or status.get("status_name")

            if status_id and name:
                print(f"  {status_id:3d} | {name}")
            else:
                print(f"  Структура: {status.keys()}")
        else:
            print(f"  Неожиданный тип: {type(status)}")

    if len(statuses) > 20:
        print(f"  ... еще {len(statuses) - 20} статусов")


def generate_mapping(statuses: list):
    """Сгенерировать ALFACRM_STATUS_MAPPING."""
    print_separator("ГЕНЕРАЦИЯ МАППИНГА")

    if not statuses:
        print("ERROR: Нет данных для генерации")
        return

    print("Сгенерированный ALFACRM_STATUS_MAPPING:")
    print("-" * 80)
    print("ALFACRM_STATUS_MAPPING = {")

    for status in statuses:
        if isinstance(status, dict):
            status_id = status.get("id") or status.get("status_id") or status.get("lead_status_id")
            name = status.get("name") or status.get("title") or status.get("status_name")

            if status_id and name:
                print(f'    {status_id}: "{name}",')

    print("}")

    # Сохранить в файл
    output_file = project_root / "docs" / "GENERATED_ALFACRM_MAPPING.py"

    with open(output_file, "w", encoding="utf-8") as f:
        f.write("# Автоматически сгенерированный маппинг статусов AlfaCRM\n")
        f.write("# Дата генерации: " + str(Path(__file__).stat().st_mtime) + "\n\n")
        f.write("ALFACRM_STATUS_MAPPING = {\n")

        for status in statuses:
            if isinstance(status, dict):
                status_id = status.get("id") or status.get("status_id") or status.get("lead_status_id")
                name = status.get("name") or status.get("title") or status.get("status_name")

                if status_id and name:
                    f.write(f'    {status_id}: "{name}",\n')

        f.write("}\n")

    print(f"\nСохранено в: {output_file}")


def main():
    """Главная функция."""
    statuses = fetch_lead_statuses()

    if statuses:
        generate_mapping(statuses)
        print_separator("ГОТОВО!")
        print("Следующие шаги:")
        print("1. Проверьте сгенерированный маппинг в docs/GENERATED_ALFACRM_MAPPING.py")
        print("2. Скопируйте корректный маппинг в app/services/alfacrm_tracking.py")
        print("3. Запустите повторное тестирование")
    else:
        print_separator("НЕ УДАЛОСЬ ПОЛУЧИТЬ СПРАВОЧНИК")
        print("Альтернативные варианты:")
        print("1. Запустите scripts/check_alfacrm_statuses.py для анализа реальных студентов")
        print("2. Запросите справочник напрямую у заказчика")
        print("3. Проверьте документацию AlfaCRM API")


if __name__ == "__main__":
    main()
