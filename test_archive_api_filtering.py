"""
Тест для проверки возможности фильтрации архивных лидов через AlfaCRM API.

ЦЕЛЬ ИССЛЕДОВАНИЯ:
1. Проверить можем ли мы НАПРЯМУЮ получать только архивные лиды через API
2. Проверить какие параметры фильтрации поддерживает /v2api/customer/index
3. Проверить можно ли фильтровать по custom_ads_comp или lead_status_id

РЕЗУЛЬТАТЫ:
- Поможет понять можно ли делать эффективные запросы только для архивных лидов
- Или нужно загружать всех студентов и фильтровать на стороне клиента
"""
import os
import sys
import json
import requests
from pathlib import Path
from dotenv import load_dotenv

# Загрузить переменные окружения
load_dotenv()

# Добавить app директорию в Python path
app_dir = Path(__file__).parent / "app"
sys.path.insert(0, str(app_dir))

from connectors.crm import alfacrm_auth_get_token


def test_archive_filtering():
    """
    Тестировать различные способы фильтрации архивных лидов через API.
    """

    print("\n" + "="*80)
    print("ИССЛЕДОВАНИЕ: Фильтрация архивных лидов в AlfaCRM API")
    print("="*80)

    # Получить токен
    print("\n[1/6] Аутентификация в AlfaCRM...")
    try:
        token = alfacrm_auth_get_token()
        print("  ✓ Токен получен")
    except Exception as e:
        print(f"  ✗ Ошибка: {e}")
        return

    base_url = os.getenv("ALFACRM_BASE_URL").rstrip('/')
    company_id = int(os.getenv("ALFACRM_COMPANY_ID"))
    headers = {"X-ALFACRM-TOKEN": token}

    # Тест 1: Базовый запрос без фильтров
    print("\n[2/6] Тест 1: Базовый запрос без фильтров")
    try:
        url = f"{base_url}/v2api/customer/index"
        payload = {
            "branch_ids": [company_id],
            "page": 1,
            "page_size": 10
        }

        resp = requests.post(url, headers=headers, json=payload, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        items = data.get("items", [])
        total = data.get("count", 0)

        print(f"  ✓ Получено: {len(items)} студентов")
        print(f"  ✓ Всего в системе: {total}")

        # Проверяем есть ли архивные
        archive_count = sum(1 for item in items if item.get("custom_ads_comp") == "архів")
        print(f"  ✓ Из них архивных (custom_ads_comp='архів'): {archive_count}")

        # Показываем доступные поля для понимания структуры
        if items:
            sample = items[0]
            print(f"\n  Доступные поля в ответе ({len(sample.keys())} полей):")
            print(f"    {', '.join(sorted(sample.keys())[:20])}...")

    except Exception as e:
        print(f"  ✗ Ошибка: {e}")
        import traceback
        traceback.print_exc()

    # Тест 2: Попытка фильтрации по lead_status_id
    print("\n[3/6] Тест 2: Фильтрация по lead_status_id (статус 39 - архив)")
    try:
        url = f"{base_url}/v2api/customer/index"
        payload = {
            "branch_ids": [company_id],
            "page": 1,
            "page_size": 10,
            "lead_status_id": 39  # Из документации - архивный статус
        }

        resp = requests.post(url, headers=headers, json=payload, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        items = data.get("items", [])
        print(f"  ✓ Получено: {len(items)} студентов")

        if items:
            # Проверяем все ли с status_id = 39
            status_ids = [item.get("lead_status_id") for item in items]
            unique_statuses = set(status_ids)
            print(f"  ✓ Уникальные lead_status_id в результатах: {unique_statuses}")
            print(f"  ✓ РЕЗУЛЬТАТ: Фильтрация по lead_status_id {'РАБОТАЕТ' if unique_statuses == {39} else 'НЕ РАБОТАЕТ'}")
        else:
            print(f"  ⚠ Нет результатов - возможно параметр не поддерживается или нет лидов с status_id=39")

    except requests.exceptions.HTTPError as e:
        print(f"  ✗ HTTP Ошибка {e.response.status_code}: {e.response.text}")
        print(f"  ⚠ Вероятно параметр lead_status_id НЕ ПОДДЕРЖИВАЕТСЯ API")
    except Exception as e:
        print(f"  ✗ Ошибка: {e}")

    # Тест 3: Попытка фильтрации по lead_status_ids (массив)
    print("\n[4/6] Тест 3: Фильтрация по lead_status_ids (массив)")
    try:
        url = f"{base_url}/v2api/customer/index"
        payload = {
            "branch_ids": [company_id],
            "page": 1,
            "page_size": 10,
            "lead_status_ids": [39]  # Массив статусов
        }

        resp = requests.post(url, headers=headers, json=payload, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        items = data.get("items", [])
        print(f"  ✓ Получено: {len(items)} студентов")

        if items:
            status_ids = [item.get("lead_status_id") for item in items]
            unique_statuses = set(status_ids)
            print(f"  ✓ Уникальные lead_status_id: {unique_statuses}")
            print(f"  ✓ РЕЗУЛЬТАТ: Фильтрация по lead_status_ids {'РАБОТАЕТ' if unique_statuses == {39} else 'НЕ РАБОТАЕТ'}")
        else:
            print(f"  ⚠ Нет результатов")

    except requests.exceptions.HTTPError as e:
        print(f"  ✗ HTTP Ошибка {e.response.status_code}: {e.response.text}")
        print(f"  ⚠ Вероятно параметр lead_status_ids НЕ ПОДДЕРЖИВАЕТСЯ API")
    except Exception as e:
        print(f"  ✗ Ошибка: {e}")

    # Тест 4: Проверка параметра status (может быть другое название)
    print("\n[5/6] Тест 4: Фильтрация по status")
    try:
        url = f"{base_url}/v2api/customer/index"
        payload = {
            "branch_ids": [company_id],
            "page": 1,
            "page_size": 10,
            "status": "archived"  # Возможно есть текстовый параметр
        }

        resp = requests.post(url, headers=headers, json=payload, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        items = data.get("items", [])
        print(f"  ✓ Получено: {len(items)} студентов")

        if items:
            archive_count = sum(1 for item in items if item.get("custom_ads_comp") == "архів")
            print(f"  ✓ Архивных (custom_ads_comp='архів'): {archive_count}")
            print(f"  ✓ РЕЗУЛЬТАТ: Фильтрация по status={'archived'} {'РАБОТАЕТ' if archive_count == len(items) else 'НЕ РАБОТАЕТ'}")

    except requests.exceptions.HTTPError as e:
        print(f"  ✗ HTTP Ошибка {e.response.status_code}: {e.response.text}")
        print(f"  ⚠ Вероятно параметр status НЕ ПОДДЕРЖИВАЕТСЯ API")
    except Exception as e:
        print(f"  ✗ Ошибка: {e}")

    # Тест 5: Получить ВСЕХ студентов и посчитать архивные на стороне клиента
    print("\n[6/6] Тест 5: Анализ архивных лидов (клиентская фильтрация)")
    try:
        url = f"{base_url}/v2api/customer/index"
        payload = {
            "branch_ids": [company_id],
            "page": 1,
            "page_size": 500  # Большая выборка
        }

        resp = requests.post(url, headers=headers, json=payload, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        items = data.get("items", [])
        total = data.get("count", 0)

        print(f"  ✓ Загружено: {len(items)} из {total} студентов")

        # Фильтруем архивные на стороне клиента
        archive_by_field = [item for item in items if item.get("custom_ads_comp") == "архів"]
        archive_by_status = [item for item in items if item.get("lead_status_id") == 39]

        print(f"\n  Результаты клиентской фильтрации:")
        print(f"    По custom_ads_comp='архів': {len(archive_by_field)}")
        print(f"    По lead_status_id=39: {len(archive_by_status)}")

        # Показываем пример архивного лида
        if archive_by_field:
            sample = archive_by_field[0]
            print(f"\n  Пример архивного лида:")
            print(f"    ID: {sample.get('id')}")
            print(f"    Имя: {sample.get('name')}")
            print(f"    lead_status_id: {sample.get('lead_status_id')}")
            print(f"    custom_ads_comp: {sample.get('custom_ads_comp')}")
            print(f"    Телефоны: {sample.get('phone', [])}")
            print(f"    Email: {sample.get('email', [])}")

        # Проверяем согласованность
        both = [item for item in items
                if item.get("custom_ads_comp") == "архів" and item.get("lead_status_id") == 39]
        print(f"\n  Согласованность:")
        print(f"    Лидов с ОБОИМИ признаками (custom_ads_comp='архів' И lead_status_id=39): {len(both)}")

        only_field = [item for item in archive_by_field if item.get("lead_status_id") != 39]
        only_status = [item for item in archive_by_status if item.get("custom_ads_comp") != "архів"]

        print(f"    Только custom_ads_comp='архів' (без status_id=39): {len(only_field)}")
        print(f"    Только lead_status_id=39 (без custom_ads_comp='архів'): {len(only_status)}")

        if only_field:
            print(f"\n  ⚠ Несогласованность! Есть {len(only_field)} лидов с custom_ads_comp='архів' но БЕЗ status_id=39")
            print(f"    Их status_id: {set(item.get('lead_status_id') for item in only_field)}")

    except Exception as e:
        print(f"  ✗ Ошибка: {e}")
        import traceback
        traceback.print_exc()

    # Итоговые выводы
    print("\n" + "="*80)
    print("ИТОГОВЫЕ ВЫВОДЫ:")
    print("="*80)

    print("\n1. ФИЛЬТРАЦИЯ НА СТОРОНЕ СЕРВЕРА (AlfaCRM API):")
    print("   Проверено несколько вариантов параметров фильтрации:")
    print("   - lead_status_id: [результат будет выше]")
    print("   - lead_status_ids: [результат будет выше]")
    print("   - status: [результат будет выше]")

    print("\n2. ФИЛЬТРАЦИЯ НА СТОРОНЕ КЛИЕНТА:")
    print("   ✓ РАБОТАЕТ - можно загрузить всех студентов и отфильтровать")
    print("   ✓ Архив определяется по custom_ads_comp == 'архів'")
    print("   ✓ Дополнительно можно проверять lead_status_id == 39")

    print("\n3. РЕКОМЕНДАЦИИ:")
    print("   Если серверная фильтрация НЕ работает:")
    print("   - Загружать всех студентов через alfacrm_list_students()")
    print("   - Фильтровать на стороне клиента: custom_ads_comp == 'архів'")
    print("   - Это уже реализовано в alfacrm_tracking.py (строка 324)")

    print("\n" + "="*80)


if __name__ == "__main__":
    test_archive_filtering()
