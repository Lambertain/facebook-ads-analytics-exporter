"""
Скрипт для експорту ВСЕХ лидов из AlfaCRM с дедупликацией по ID.

Стратегия:
1. Собрать is_study=0 (уникальные лиды - 2,100 записей)
2. Собрать is_study=1 (студенты - 1,429 записей)
3. Собрать is_study=2 (комбинированные - 2,500+ записей)
4. Дедуплицировать по ID
5. Экспорт в CSV

Примечание: is_study=3-10 НЕ используем, т.к. они полные дубликаты is_study=2
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
print('[INFO] ЭКСПОРТ ВСЕХ ЛИДОВ ИЗ ALFACRM')
print('=' * 80)


def fetch_all_records(is_study_val, max_pages=100):
    """Получить ВСЕ записи для заданного is_study значения"""
    all_records = []
    page = 1

    print(f'\n[FETCH] Загрузка is_study={is_study_val}...', flush=True)

    while page <= max_pages:
        try:
            response = requests.post(
                f'{base_url}/v2api/customer/index',
                headers={'X-ALFACRM-TOKEN': token},
                json={
                    'is_study': is_study_val,
                    'page': page,
                    'page_size': 500
                },
                timeout=15
            )
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

    print(f'[OK] is_study={is_study_val}: получено {len(all_records)} записей за {page-1} страниц', flush=True)
    return all_records


print('\n[STEP 1/5] Загрузка записей...')
print('-' * 80)

records_by_is_study = {}

records_by_is_study[0] = fetch_all_records(0, max_pages=50)
records_by_is_study[1] = fetch_all_records(1, max_pages=50)
records_by_is_study[2] = fetch_all_records(2, max_pages=100)

print('\n[STEP 2/5] Дедупликация по ID...')
print('-' * 80)

unique_records = {}

for is_study_val, records in records_by_is_study.items():
    for record in records:
        record_id = record.get('id')
        if record_id not in unique_records:
            unique_records[record_id] = record

total_before = sum(len(records) for records in records_by_is_study.values())
total_after = len(unique_records)
duplicates_removed = total_before - total_after

print(f'Всего записей до дедупликации: {total_before}')
print(f'Уникальных записей после: {total_after}')
print(f'Дубликатов удалено: {duplicates_removed} ({duplicates_removed/total_before*100:.1f}%)')

print('\n[STEP 3/5] Разбивка по категориям...')
print('-' * 80)

leads = [r for r in unique_records.values() if r.get('is_study') == 0]
students = [r for r in unique_records.values() if r.get('is_study') == 1]
combined = [r for r in unique_records.values() if r.get('is_study') not in [0, 1]]

print(f'Лиды (is_study=0): {len(leads)}')
print(f'Студенты (is_study=1): {len(students)}')
print(f'Комбинированные (is_study=2+): {len(combined)}')

print('\n[STEP 4/5] Проверка архивных записей...')
print('-' * 80)

archived_leads = [r for r in unique_records.values()
                  if r.get('lead_reject_id') is not None or r.get('customer_reject_id') is not None]
print(f'Архивных записей: {len(archived_leads)}')

print('\n[STEP 5/5] Экспорт в CSV...')
print('-' * 80)

timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
output_file = f'alfacrm_leads_export_{timestamp}.csv'

if unique_records:
    sample_record = list(unique_records.values())[0]
    fieldnames = list(sample_record.keys())

    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for record in unique_records.values():
            writer.writerow(record)

    file_size = os.path.getsize(output_file) / 1024 / 1024

    print(f'\n[SUCCESS] Экспорт завершен!')
    print(f'Файл: {output_file}')
    print(f'Размер: {file_size:.2f} MB')
    print(f'Всего уникальных записей: {len(unique_records)}')
    print(f'Полей в каждой записи: {len(fieldnames)}')

else:
    print('[ERROR] Нет записей для экспорта!')

print('\n' + '=' * 80)
print('[INFO] ЗАВЕРШЕНО')
print('=' * 80)
