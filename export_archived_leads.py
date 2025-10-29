"""
ФИНАЛЬНЫЙ ЭКСПОРТ АРХИВНЫХ ЛИДОВ через параметр removed=2

РЕШЕНИЕ НАЙДЕНО! ChatGPT предложил параметр 'removed':
- removed=0: только активные
- removed=1: активные + архивные
- removed=2: ТОЛЬКО архивные (ЭТО РЕШЕНИЕ!)

Экспортируем:
1. Архивные лиды (is_study=0, removed=2)
2. Архивные студенты (is_study=1, removed=2)
3. Архивные комбинированные (is_study=2, removed=2)

Ожидаемый результат: ~7,788 архивных записей из Web UI
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import requests
import csv
from datetime import datetime

load_dotenv()

app_dir = Path(__file__).parent / "app"
sys.path.insert(0, str(app_dir))

from connectors.crm import alfacrm_auth_get_token

base_url = os.getenv('ALFACRM_BASE_URL')
token = alfacrm_auth_get_token()

print('=' * 80)
print('[INFO] ЭКСПОРТ АРХИВНЫХ ЛИДОВ (removed=2)')
print('=' * 80)


def fetch_archived_records(is_study_val, category_name, max_pages=200):
    """Получить ВСЕ архивные записи для заданного is_study значения"""
    all_records = []
    page = 1

    print(f'\n[FETCH] Загрузка архивных {category_name} (is_study={is_study_val})...', flush=True)

    while page <= max_pages:
        try:
            response = requests.post(
                f'{base_url}/v2api/customer/index',
                headers={'X-ALFACRM-TOKEN': token},
                json={
                    'is_study': is_study_val,
                    'removed': 2,  # КЛЮЧЕВОЙ ПАРАМЕТР!
                    'page': page,
                    'page_size': 500
                },
                timeout=15
            )

            if response.status_code != 200:
                print(f'  ❌ HTTP {response.status_code} на странице {page}', flush=True)
                break

            data = response.json()
            items = data.get('items', [])

            if not items:
                print(f'  Страница {page}: пусто, завершено', flush=True)
                break

            all_records.extend(items)

            if page % 10 == 0:
                print(f'  Страница {page}: собрано {len(all_records)} записей...', flush=True)

            page += 1

        except Exception as e:
            print(f'[ERROR] is_study={is_study_val}, page={page}: {e}')
            break

    print(f'[OK] {category_name}: получено {len(all_records)} архивных записей за {page-1} страниц', flush=True)
    return all_records


print('\n[STEP 1/5] Загрузка архивных записей...')
print('-' * 80)

archived_records = {}

# Архивные лиды (lead_reject_id)
archived_records[0] = fetch_archived_records(0, 'лиды', max_pages=200)

# Архивные студенты (customer_reject_id)
archived_records[1] = fetch_archived_records(1, 'студенты', max_pages=200)

# Архивные комбинированные
archived_records[2] = fetch_archived_records(2, 'комбинированные', max_pages=100)

print('\n[STEP 2/5] Дедупликация по ID...')
print('-' * 80)

unique_archived = {}

for is_study_val, records in archived_records.items():
    for record in records:
        record_id = record.get('id')
        if record_id not in unique_archived:
            unique_archived[record_id] = record

total_before = sum(len(records) for records in archived_records.values())
total_after = len(unique_archived)
duplicates_removed = total_before - total_after

print(f'Всего архивных записей до дедупликации: {total_before}')
print(f'Уникальных архивных записей после: {total_after}')
print(f'Дубликатов удалено: {duplicates_removed} ({duplicates_removed/total_before*100 if total_before > 0 else 0:.1f}%)')

print('\n[STEP 3/5] Анализ типов архивных записей...')
print('-' * 80)

with_lead_reject = [r for r in unique_archived.values() if r.get('lead_reject_id')]
with_customer_reject = [r for r in unique_archived.values() if r.get('customer_reject_id')]

print(f'Архивные лиды (lead_reject_id): {len(with_lead_reject)}')
print(f'Архивные студенты (customer_reject_id): {len(with_customer_reject)}')

# Проверка is_study разбивки
is_study_counts = {}
for r in unique_archived.values():
    val = r.get('is_study', 'NULL')
    is_study_counts[val] = is_study_counts.get(val, 0) + 1

print(f'is_study распределение: {is_study_counts}')

print('\n[STEP 4/5] Примеры архивных записей...')
print('-' * 80)

if with_lead_reject:
    sample = with_lead_reject[0]
    print(f'\nПример архивного лида:')
    print(f'  ID: {sample.get("id")}')
    print(f'  ПІБ: {sample.get("name")}')
    print(f'  is_study: {sample.get("is_study")}')
    print(f'  lead_reject_id: {sample.get("lead_reject_id")}')
    print(f'  lead_status_id: {sample.get("lead_status_id")}')

if with_customer_reject:
    sample = with_customer_reject[0]
    print(f'\nПример архивного студента:')
    print(f'  ID: {sample.get("id")}')
    print(f'  ПІБ: {sample.get("name")}')
    print(f'  is_study: {sample.get("is_study")}')
    print(f'  customer_reject_id: {sample.get("customer_reject_id")}')

print('\n[STEP 5/5] Экспорт в CSV...')
print('-' * 80)

timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
output_file = f'alfacrm_archived_leads_export_{timestamp}.csv'

if unique_archived:
    sample_record = list(unique_archived.values())[0]
    fieldnames = list(sample_record.keys())

    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for record in unique_archived.values():
            writer.writerow(record)

    file_size = os.path.getsize(output_file) / 1024 / 1024

    print(f'\n[SUCCESS] Экспорт архивных записей завершен!')
    print(f'Файл: {output_file}')
    print(f'Размер: {file_size:.2f} MB')
    print(f'Всего уникальных архивных записей: {len(unique_archived)}')
    print(f'Полей в каждой записи: {len(fieldnames)}')
    print(f'\nРаспределение:')
    print(f'  Архивные лиды: {len(with_lead_reject)}')
    print(f'  Архивные студенты: {len(with_customer_reject)}')

else:
    print('[ERROR] Нет архивных записей для экспорта!')

print('\n' + '=' * 80)
print('[INFO] ЗАВЕРШЕНО')
print('=' * 80)
print('\n🎯 РЕШЕНИЕ: параметр removed=2 дает доступ к ВСЕМ архивным записям!')
print('💡 Благодарность ChatGPT за подсказку параметра removed!')
print('=' * 80)
