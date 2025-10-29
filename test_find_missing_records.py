"""
Тест: Знайти де решта записів (~7000 замість 3544)
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import requests
import json

load_dotenv()

app_dir = Path(__file__).parent / "app"
sys.path.insert(0, str(app_dir))

from connectors.crm import alfacrm_auth_get_token


def test_page_size_variants():
    """Перевірити чи page_size впливає на результати"""
    print("\n" + "="*80)
    print("ТЕСТ 1: Різні page_size")
    print("="*80)

    token = alfacrm_auth_get_token()
    base_url = os.getenv("ALFACRM_BASE_URL").rstrip('/')

    for page_size in [10, 50, 100, 500]:
        url = f"{base_url}/v2api/customer/index"

        resp = requests.post(
            url,
            headers={"X-ALFACRM-TOKEN": token},
            json={
                "is_study": 2,
                "page": 1,
                "page_size": page_size
            },
            timeout=15
        )

        data = resp.json()
        count = data.get('count', 0)
        items_len = len(data.get('items', []))

        print(f"  page_size={page_size:3d}: count={count:5d}, items={items_len:3d}")


def test_without_pagination():
    """Спробувати без page взагалі"""
    print("\n" + "="*80)
    print("ТЕСТ 2: БЕЗ параметра page")
    print("="*80)

    token = alfacrm_auth_get_token()
    base_url = os.getenv("ALFACRM_BASE_URL").rstrip('/')
    url = f"{base_url}/v2api/customer/index"

    # Спробуємо різні варіанти
    tests = [
        ("БЕЗ page і page_size", {"is_study": 2}),
        ("page=0", {"is_study": 2, "page": 0}),
        ("page=-1", {"is_study": 2, "page": -1}),
        ("page_size=10000", {"is_study": 2, "page_size": 10000}),
    ]

    for test_name, params in tests:
        try:
            resp = requests.post(
                url,
                headers={"X-ALFACRM-TOKEN": token},
                json=params,
                timeout=15
            )

            if resp.status_code == 200:
                data = resp.json()
                count = data.get('count', 0)
                items_len = len(data.get('items', []))
                print(f"  [{test_name}]: count={count}, items={items_len}")
            else:
                print(f"  [{test_name}]: HTTP {resp.status_code}")

        except Exception as e:
            print(f"  [{test_name}]: ERROR - {e}")


def test_deep_count():
    """Перевірити поле count в відповіді на різних сторінках"""
    print("\n" + "="*80)
    print("ТЕСТ 3: Значення поля 'count' на різних сторінках")
    print("="*80)

    token = alfacrm_auth_get_token()
    base_url = os.getenv("ALFACRM_BASE_URL").rstrip('/')
    url = f"{base_url}/v2api/customer/index"

    for page in [1, 10, 50, 70, 100]:
        resp = requests.post(
            url,
            headers={"X-ALFACRM-TOKEN": token},
            json={
                "is_study": 2,
                "page": page,
                "page_size": 50
            },
            timeout=15
        )

        data = resp.json()
        count = data.get('count', 0)
        items_len = len(data.get('items', []))

        if items_len == 0:
            print(f"  Сторінка {page:3d}: ПУСТО (count={count})")
            break
        else:
            print(f"  Сторінка {page:3d}: count={count:5d}, items={items_len:2d}")


def test_total_with_bigger_page_size():
    """Спробувати отримати ВСІ з більшим page_size"""
    print("\n" + "="*80)
    print("ТЕСТ 4: Повна пагінація з page_size=500")
    print("="*80)

    token = alfacrm_auth_get_token()
    base_url = os.getenv("ALFACRM_BASE_URL").rstrip('/')
    url = f"{base_url}/v2api/customer/index"

    all_records = {}
    page = 1

    print("\nЗавантаження всіх записів з page_size=500...")

    while page <= 50:  # Макс 50 сторінок × 500 = 25000 записів
        resp = requests.post(
            url,
            headers={"X-ALFACRM-TOKEN": token},
            json={
                "is_study": 2,
                "page": page,
                "page_size": 500
            },
            timeout=15
        )

        data = resp.json()
        items = data.get('items', [])
        count = data.get('count', 0)

        if not items:
            print(f"  Сторінка {page}: пусто (count={count}), зупиняємось")
            break

        for record in items:
            record_id = record.get('id')
            if record_id not in all_records:
                all_records[record_id] = record

        if page % 5 == 0:
            print(f"  Сторінка {page}: завантажено {len(all_records)} унікальних (count={count})")

        page += 1

    print(f"\n  ВСЬОГО унікальних записів: {len(all_records)}")

    # Архівні
    archived = [r for r in all_records.values()
                if r.get('lead_reject_id') or r.get('customer_reject_id')]
    print(f"  Архівних: {len(archived)}")


def test_api_response_structure():
    """Подивитися на структуру відповіді API"""
    print("\n" + "="*80)
    print("ТЕСТ 5: Структура відповіді API")
    print("="*80)

    token = alfacrm_auth_get_token()
    base_url = os.getenv("ALFACRM_BASE_URL").rstrip('/')
    url = f"{base_url}/v2api/customer/index"

    resp = requests.post(
        url,
        headers={"X-ALFACRM-TOKEN": token},
        json={
            "is_study": 2,
            "page": 1,
            "page_size": 1
        },
        timeout=15
    )

    data = resp.json()

    print("\n  Ключі верхнього рівня:")
    for key, value in data.items():
        if key != 'items':
            print(f"    {key}: {value}")

    print(f"\n  Кількість полів в items[0]: {len(data.get('items', [{}])[0])}")


if __name__ == "__main__":
    test_page_size_variants()
    test_without_pagination()
    test_deep_count()
    test_total_with_bigger_page_size()
    test_api_response_structure()

    print("\n" + "="*80)
    print("ВСІ ТЕСТИ ЗАВЕРШЕНО")
    print("="*80)
