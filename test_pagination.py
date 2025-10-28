"""
Тест пагинации AlfaCRM API
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import requests

load_dotenv()

app_dir = Path(__file__).parent / "app"
sys.path.insert(0, str(app_dir))

from connectors.crm import alfacrm_auth_get_token


def test_pagination():
    """Проверить работает ли пагинация"""
    print("\n" + "="*80)
    print("ТЕСТ ПАГИНАЦИИ")
    print("="*80)

    token = alfacrm_auth_get_token()
    base_url = os.getenv("ALFACRM_BASE_URL").rstrip('/')

    # Получаем несколько страниц
    for page in range(1, 5):
        url = f"{base_url}/v2api/customer/index"
        payload = {
            "page": page,
            "page_size": 20
        }

        print(f"\n--- Страница {page} ---")
        print(f"Параметры: {payload}")

        resp = requests.post(
            url,
            headers={"X-ALFACRM-TOKEN": token},
            json=payload,
            timeout=15
        )

        data = resp.json()
        items = data.get("items", [])
        total = data.get("count", 0)

        print(f"Результат:")
        print(f"  Получено: {len(items)} лидов")
        print(f"  Всего в системе: {total}")

        if items:
            print(f"  Первый ID: {items[0].get('id')}")
            print(f"  Последний ID: {items[-1].get('id')}")

        if not items:
            print(f"  → Страница пустая, останавливаемся")
            break


def test_max_page_size():
    """Проверить максимальный page_size"""
    print("\n" + "="*80)
    print("ТЕСТ МАКСИМАЛЬНОГО PAGE_SIZE")
    print("="*80)

    token = alfacrm_auth_get_token()
    base_url = os.getenv("ALFACRM_BASE_URL").rstrip('/')

    # Пробуем разные размеры страницы
    for page_size in [50, 100, 500, 1000]:
        url = f"{base_url}/v2api/customer/index"
        payload = {
            "page": 1,
            "page_size": page_size
        }

        print(f"\n--- page_size = {page_size} ---")

        resp = requests.post(
            url,
            headers={"X-ALFACRM-TOKEN": token},
            json=payload,
            timeout=30
        )

        data = resp.json()
        items = data.get("items", [])
        total = data.get("count", 0)

        print(f"  Получено: {len(items)} лидов")
        print(f"  Всего в системе: {total}")


if __name__ == "__main__":
    test_pagination()
    test_max_page_size()
