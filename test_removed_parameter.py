"""
КРИТИЧЕСКАЯ НАХОДКА от ChatGPT: параметр 'removed' для архивных лидов!

Тестируем:
- removed=0 (только активные)
- removed=1 (активные + архивные)
- removed=2 (только архивные)

Plus дополнительные параметры:
- removed_from, removed_to (диапазон дат)
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import requests
from datetime import datetime, timedelta

load_dotenv()

app_dir = Path(__file__).parent / "app"
sys.path.insert(0, str(app_dir))

from connectors.crm import alfacrm_auth_get_token

base_url = os.getenv('ALFACRM_BASE_URL')
token = alfacrm_auth_get_token()

print('=' * 80)
print('[КРИТИЧЕСКИЙ ТЕСТ] ПАРАМЕТР removed ДЛЯ АРХИВНЫХ ЛИДОВ')
print('=' * 80)


def test_removed(test_name, payload, max_pages=5):
    """Протестувати запит з параметром removed"""
    print(f'\n[TEST] {test_name}')
    print(f'  Payload: {payload}')

    try:
        response = requests.post(
            f'{base_url}/v2api/customer/index',
            headers={'X-ALFACRM-TOKEN': token},
            json=payload,
            timeout=15
        )

        if response.status_code != 200:
            print(f'  ❌ HTTP {response.status_code}: {response.text[:200]}')
            return

        data = response.json()
        items = data.get('items', [])

        if not items:
            print(f'  ❌ 0 записів')
            return

        # Збираємо кілька сторінок для аналізу
        all_records = items[:]
        page = 2

        while page <= max_pages:
            payload_copy = payload.copy()
            payload_copy['page'] = page

            resp = requests.post(
                f'{base_url}/v2api/customer/index',
                headers={'X-ALFACRM-TOKEN': token},
                json=payload_copy,
                timeout=15
            )

            page_items = resp.json().get('items', [])
            if not page_items:
                break

            all_records.extend(page_items)
            page += 1

        # Аналіз архівних
        with_lead_reject = [r for r in all_records if r.get('lead_reject_id')]
        with_customer_reject = [r for r in all_records if r.get('customer_reject_id')]
        archived_total = len(set([r['id'] for r in with_lead_reject + with_customer_reject]))

        print(f'  ✅ Знайдено {len(all_records)} записів ({page-1} сторінок)')
        print(f'     З lead_reject_id: {len(with_lead_reject)}')
        print(f'     З customer_reject_id: {len(with_customer_reject)}')
        print(f'     Унікальних архівних: {archived_total}')

        # is_study розподіл
        is_study_counts = {}
        for r in all_records:
            val = r.get('is_study', 'NULL')
            is_study_counts[val] = is_study_counts.get(val, 0) + 1

        print(f'     is_study розподіл: {is_study_counts}')

        # Якщо БАГАТО архівних - це SUCCESS!
        if archived_total > 100:
            print(f'\n  🎯🎯🎯 ЗНАЙДЕНО РІШЕННЯ! {archived_total} архівних записів! 🎯🎯🎯')

            # Показати приклади
            if with_lead_reject:
                sample = with_lead_reject[0]
                print(f'\n  Приклад архівного ліда:')
                print(f'    ID: {sample.get("id")}')
                print(f'    ПІБ: {sample.get("name")}')
                print(f'    is_study: {sample.get("is_study")}')
                print(f'    lead_reject_id: {sample.get("lead_reject_id")}')
                print(f'    lead_status_id: {sample.get("lead_status_id")}')

    except Exception as e:
        print(f'  ❌ ERROR: {e}')


print('\n[ГРУПА 1] Тестування параметра removed')
print('-' * 80)

# Тест 1: removed=0 (тільки активні)
test_removed('removed=0 (тільки активні)', {
    'is_study': 0,
    'removed': 0,
    'page': 1,
    'page_size': 100
})

# Тест 2: removed=1 (активні + архівні)
test_removed('removed=1 (активні + архівні)', {
    'is_study': 0,
    'removed': 1,
    'page': 1,
    'page_size': 100
})

# Тест 3: removed=2 (ТІЛЬКИ АРХІВНІ) - ЦЕ КЛЮЧОВИЙ ТЕСТ!
test_removed('removed=2 (ТІЛЬКИ АРХІВНІ) 🎯', {
    'is_study': 0,
    'removed': 2,
    'page': 1,
    'page_size': 100
}, max_pages=20)  # Більше сторінок для архіву

print('\n[ГРУПА 2] Тестування з діапазоном дат')
print('-' * 80)

# Тест 4: removed=2 + date range (останній рік)
one_year_ago = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
today = datetime.now().strftime('%Y-%m-%d')

test_removed(f'removed=2 + date range ({one_year_ago} to {today})', {
    'is_study': 0,
    'removed': 2,
    'removed_from': one_year_ago,
    'removed_to': today,
    'page': 1,
    'page_size': 100
}, max_pages=20)

print('\n[ГРУПА 3] Різні is_study з removed=2')
print('-' * 80)

# Тест 5: is_study=1 (студенти архівні)
test_removed('is_study=1 + removed=2 (архівні студенти)', {
    'is_study': 1,
    'removed': 2,
    'page': 1,
    'page_size': 100
}, max_pages=10)

# Тест 6: is_study=2 (комбіновані архівні)
test_removed('is_study=2 + removed=2 (архівні комбіновані)', {
    'is_study': 2,
    'removed': 2,
    'page': 1,
    'page_size': 100
}, max_pages=10)

print('\n' + '=' * 80)
print('[РЕЗУЛЬТАТИ]')
print('=' * 80)
print('\n⏳ Очікуємо результати тестування параметра removed...')
print('📊 Якщо знайдено >100 архівних - ЦЕ РІШЕННЯ!')
print('\n' + '=' * 80)
