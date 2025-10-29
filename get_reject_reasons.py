"""
Получение всех причин отказов (reject reasons) из Alfa CRM API.

Endpoints:
- /v2api/lead-reject/index - причины отказа для лидов (44 шт)
- /v2api/customer-reject/index - причины отказа для клиентов (49 шт)
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import requests
import pandas as pd
from collections import Counter

load_dotenv()

app_dir = Path(__file__).parent / "app"
sys.path.insert(0, str(app_dir))

from connectors.crm import alfacrm_auth_get_token

base_url = os.getenv('ALFACRM_BASE_URL')
token = alfacrm_auth_get_token()

print('=' * 80)
print('[INFO] СПРАВОЧНИКИ ПРИЧИН ОТКАЗОВ')
print('=' * 80)

# 1. Получить причины отказов для лидов
print('\n[STEP 1/4] Получение причин отказа ЛИДОВ...')
print('-' * 80)

response = requests.post(
    f'{base_url}/v2api/lead-reject/index',
    headers={'X-ALFACRM-TOKEN': token},
    json={},
    timeout=10
)

lead_rejects = response.json().get('items', [])
print(f'Получено причин отказа лидов: {len(lead_rejects)}')

# Сортируем по ID
lead_rejects_sorted = sorted(lead_rejects, key=lambda x: x.get('id', 0))

print('\nПричины отказа ЛИДОВ:')
for reject in lead_rejects_sorted[:10]:
    print(f"  ID {reject.get('id')}: {reject.get('name')}")

if len(lead_rejects_sorted) > 10:
    print(f'  ... (ещё {len(lead_rejects_sorted) - 10} причин)')

# 2. Получить причины отказов для клиентов
print('\n[STEP 2/4] Получение причин отказа КЛИЕНТОВ...')
print('-' * 80)

response = requests.post(
    f'{base_url}/v2api/customer-reject/index',
    headers={'X-ALFACRM-TOKEN': token},
    json={},
    timeout=10
)

customer_rejects = response.json().get('items', [])
print(f'Получено причин отказа клиентов: {len(customer_rejects)}')

# Сортируем по ID
customer_rejects_sorted = sorted(customer_rejects, key=lambda x: x.get('id', 0))

print('\nПричины отказа КЛИЕНТОВ:')
for reject in customer_rejects_sorted[:10]:
    print(f"  ID {reject.get('id')}: {reject.get('name')}")

if len(customer_rejects_sorted) > 10:
    print(f'  ... (ещё {len(customer_rejects_sorted) - 10} причин)')

# 3. Анализ использования причин в наших данных
print('\n[STEP 3/4] Анализ использования причин в экспортированных данных...')
print('-' * 80)

# Загружаем финальный датасет
df = pd.read_csv('alfacrm_ALL_leads_merged_20251029_165012.csv')

# Только архивные записи
archived_df = df[df['lead_type'] == 'archived']

print(f'\nВсего архивных записей: {len(archived_df)}')

# Анализ lead_reject_id
lead_reject_counts = archived_df['lead_reject_id'].value_counts(dropna=True)
print(f'\nТоп-10 причин отказа ЛИДОВ (по частоте):')
for reject_id, count in lead_reject_counts.head(10).items():
    reject_id = int(reject_id)
    reject_name = next((r['name'] for r in lead_rejects if r['id'] == reject_id), 'Unknown')
    print(f"  ID {reject_id}: {reject_name} - {count} раз ({count/len(archived_df)*100:.1f}%)")

# Анализ customer_reject_id
customer_reject_counts = archived_df['customer_reject_id'].value_counts(dropna=True)
print(f'\nТоп-10 причин отказа КЛИЕНТОВ (по частоте):')
for reject_id, count in customer_reject_counts.head(10).items():
    reject_id = int(reject_id)
    reject_name = next((r['name'] for r in customer_rejects if r['id'] == reject_id), 'Unknown')
    print(f"  ID {reject_id}: {reject_name} - {count} раз ({count/len(archived_df)*100:.1f}%)")

# 4. Сохранение справочников в CSV
print('\n[STEP 4/4] Сохранение справочников в CSV...')
print('-' * 80)

# Lead rejects
lead_rejects_df = pd.DataFrame(lead_rejects_sorted)
lead_rejects_df.to_csv('alfacrm_lead_reject_reasons.csv', index=False, encoding='utf-8')
print(f'Сохранено: alfacrm_lead_reject_reasons.csv ({len(lead_rejects_df)} причин)')

# Customer rejects
customer_rejects_df = pd.DataFrame(customer_rejects_sorted)
customer_rejects_df.to_csv('alfacrm_customer_reject_reasons.csv', index=False, encoding='utf-8')
print(f'Сохранено: alfacrm_customer_reject_reasons.csv ({len(customer_rejects_df)} причин)')

print('\n' + '=' * 80)
print('[INFO] ЗАВЕРШЕНО')
print('=' * 80)
print('\nТеперь у нас есть:')
print('1. Полный справочник причин отказов лидов (44 шт)')
print('2. Полный справочник причин отказов клиентов (49 шт)')
print('3. Статистика использования причин в наших данных')
print('4. CSV файлы со справочниками для дальнейшего анализа')
