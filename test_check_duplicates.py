"""
Тест: Перевірити чи є дублікати між різними is_study значеннями.
Порівняємо ID записів з is_study=0, 1, 2, 3 для початку.
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

print('[INFO] CHECKING FOR DUPLICATES BETWEEN is_study VALUES')
print('=' * 70)

# Збираємо ID з перших 2 сторінок кожного is_study (достатньо для перевірки)
def get_ids(is_study_val, max_pages=2):
    """Отримати перші max_pages сторінок і зібрати всі ID"""
    all_ids = set()

    for page in range(1, max_pages + 1):
        try:
            response = requests.post(
                f'{base_url}/v2api/customer/index',
                headers={'X-ALFACRM-TOKEN': token},
                json={
                    'is_study': is_study_val,
                    'page': page,
                    'page_size': 100
                },
                timeout=10
            )
            data = response.json()
            items = data.get('items', [])

            if not items:
                break

            for record in items:
                all_ids.add(record.get('id'))

        except Exception as e:
            print(f'[ERROR] is_study={is_study_val}, page={page}: {e}')
            break

    return all_ids

# Збираємо ID з кількох is_study значень
print('\n[1] Збираємо ID записів з різних is_study...')
ids_by_is_study = {}

for val in [0, 1, 2, 3, 4]:
    print(f'  Збираємо is_study={val}...', flush=True)
    ids_by_is_study[val] = get_ids(val, max_pages=2)
    print(f'    Знайдено {len(ids_by_is_study[val])} унікальних ID', flush=True)

print('\n' + '=' * 70)
print('[2] АНАЛІЗ ДУБЛІКАТІВ:')
print('=' * 70)

# Перевіряємо чи є спільні ID між різними is_study
for i in [0, 1, 2, 3, 4]:
    for j in [0, 1, 2, 3, 4]:
        if i >= j:
            continue

        common = ids_by_is_study[i] & ids_by_is_study[j]
        if common:
            print(f'\n  is_study={i} і is_study={j}:')
            print(f'    Спільних ID: {len(common)}')
            print(f'    Приклад спільних ID: {list(common)[:5]}')
        else:
            print(f'\n  is_study={i} і is_study={j}: НЕ МАЮТЬ спільних ID')

# Загальна кількість унікальних ID
all_ids_combined = set()
for ids in ids_by_is_study.values():
    all_ids_combined.update(ids)

print('\n' + '=' * 70)
print('[3] ПІДСУМОК:')
print('=' * 70)

total_if_no_duplicates = sum(len(ids) for ids in ids_by_is_study.values())
actual_unique = len(all_ids_combined)

print(f'\n  Загалом ID якщо БЕЗ дублікатів: {total_if_no_duplicates}')
print(f'  Фактично унікальних ID: {actual_unique}')
print(f'  Дублікатів: {total_if_no_duplicates - actual_unique}')

if actual_unique == total_if_no_duplicates:
    print(f'\n  ✅ ДУБЛІКАТІВ НЕМАЄ! Кожен is_study має унікальні записи.')
else:
    print(f'\n  ⚠️ ДУБЛІКАТИ ЗНАЙДЕНО! Ті самі записи є в різних is_study.')
    print(f'  Коефіцієнт дублікатів: {(total_if_no_duplicates - actual_unique) / total_if_no_duplicates * 100:.1f}%')
