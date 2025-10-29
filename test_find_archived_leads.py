"""
Тест: Знайти параметр для отримання архівних лідів (7,788 записів).

Стратегія:
1. Спробувати БЕЗ is_study параметра
2. Додати різні варіанти archived параметрів
3. Перевірити is_study=-1, NULL, 99
4. Комбінувати з lead_reject_id фільтрами
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

base_url = os.getenv('ALFACRM_BASE_URL')
token = alfacrm_auth_get_token()

print('=' * 80)
print('[INFO] ПОШУК ПАРАМЕТРА ДЛЯ АРХІВНИХ ЛІДІВ')
print('=' * 80)


def test_request(test_name, payload, max_pages=3):
    """Протестувати запит і показати результати"""
    print(f'\n[TEST] {test_name}')
    print(f'  Payload: {payload}')

    try:
        response = requests.post(
            f'{base_url}/v2api/customer/index',
            headers={'X-ALFACRM-TOKEN': token},
            json=payload,
            timeout=10
        )

        if response.status_code != 200:
            print(f'  ❌ HTTP {response.status_code}: {response.text[:100]}')
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
                timeout=10
            )

            page_items = resp.json().get('items', [])
            if not page_items:
                break

            all_records.extend(page_items)
            page += 1

        # Аналіз архівних
        archived = [r for r in all_records
                   if r.get('lead_reject_id') or r.get('customer_reject_id')]

        print(f'  ✅ Знайдено {len(all_records)} записів ({page-1} сторінок)')
        print(f'     Архівних (reject_id != null): {len(archived)}')
        print(f'     Не архівних: {len(all_records) - len(archived)}')

        # Показати is_study розподіл
        is_study_counts = {}
        for r in all_records:
            val = r.get('is_study', 'NULL')
            is_study_counts[val] = is_study_counts.get(val, 0) + 1

        print(f'     is_study розподіл: {is_study_counts}')

        # Якщо багато архівних - це успіх!
        if len(archived) > 100:
            print(f'  🎯 МОЖЛИВО ЗНАЙШЛИ! {len(archived)} архівних записів!')

            # Показати приклад архівного запису
            sample = archived[0]
            print(f'\n  Приклад архівного запису:')
            print(f'    ID: {sample.get("id")}')
            print(f'    ПІБ: {sample.get("name")}')
            print(f'    is_study: {sample.get("is_study")}')
            print(f'    lead_reject_id: {sample.get("lead_reject_id")}')
            print(f'    customer_reject_id: {sample.get("customer_reject_id")}')

    except Exception as e:
        print(f'  ❌ ERROR: {e}')


print('\n[ГРУПА 1] БЕЗ is_study фільтра')
print('-' * 80)

# Тест 1: Зовсім без фільтрів
test_request('Без фільтрів (тільки page, page_size)', {
    'page': 1,
    'page_size': 100
})

# Тест 2: З різними archived параметрами
test_request('archived=1', {
    'archived': 1,
    'page': 1,
    'page_size': 100
})

test_request('archived=true', {
    'archived': True,
    'page': 1,
    'page_size': 100
})

test_request('is_archive=1', {
    'is_archive': 1,
    'page': 1,
    'page_size': 100
})

test_request('archive=1', {
    'archive': 1,
    'page': 1,
    'page_size': 100
})

test_request('only_archived=1', {
    'only_archived': 1,
    'page': 1,
    'page_size': 100
})

print('\n[ГРУПА 2] is_study=NULL або спеціальні значення')
print('-' * 80)

test_request('is_study=None (NULL)', {
    'is_study': None,
    'page': 1,
    'page_size': 100
})

test_request('is_study=-1', {
    'is_study': -1,
    'page': 1,
    'page_size': 100
})

test_request('is_study=99', {
    'is_study': 99,
    'page': 1,
    'page_size': 100
})

print('\n[ГРУПА 3] Комбінації lead_reject_id')
print('-' * 80)

test_request('БЕЗ is_study + lead_reject_id != null', {
    'page': 1,
    'page_size': 100
    # На жаль API може не підтримувати $ne, але спробуємо
})

test_request('lead_reject_id існує (спроба 1)', {
    'lead_reject_id': {'$exists': True},
    'page': 1,
    'page_size': 100
})

test_request('lead_reject_id не null (спроба 2)', {
    'lead_reject_id': {'$ne': None},
    'page': 1,
    'page_size': 100
})

print('\n[ГРУПА 4] Фільтри по статусах')
print('-' * 80)

# З UI відомо що є статуси: Не розібрано, Недодзвон, Недозвон 2, Недозвон 3
# Їх ID були: 13, 11, 10, 27 (з попередніх тестів)

test_request('lead_status_id=13 (Не розібрано)', {
    'lead_status_id': 13,
    'page': 1,
    'page_size': 100
})

test_request('lead_status_id=11 (Недодзвон)', {
    'lead_status_id': 11,
    'page': 1,
    'page_size': 100
})

print('\n' + '=' * 80)
print('[INFO] ТЕСТИ ЗАВЕРШЕНО')
print('=' * 80)
