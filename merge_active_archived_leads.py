"""
Объединение активных и архивных лидов с проверкой пересечений.

Проверяем:
1. Есть ли общие ID между активными и архивными?
2. Создаем ФИНАЛЬНЫЙ объединенный CSV со всеми лидами
3. Добавляем колонку lead_type: 'active' или 'archived'
"""
import pandas as pd
import os
from datetime import datetime

print('=' * 80)
print('[INFO] ОБЪЕДИНЕНИЕ АКТИВНЫХ И АРХИВНЫХ ЛИДОВ')
print('=' * 80)

# Загрузка CSV файлов
print('\n[STEP 1/5] Загрузка CSV файлов...')
print('-' * 80)

active_df = pd.read_csv('alfacrm_leads_export_20251029_144642.csv')
archived_df = pd.read_csv('alfacrm_archived_leads_export_20251029_154818.csv')

print(f'Активные лиды: {len(active_df)} записей')
print(f'Архивные лиды: {len(archived_df)} записей')

print('\n[STEP 2/5] Проверка пересечений по ID...')
print('-' * 80)

active_ids = set(active_df['id'])
archived_ids = set(archived_df['id'])

common_ids = active_ids.intersection(archived_ids)

print(f'Уникальных ID в активных: {len(active_ids)}')
print(f'Уникальных ID в архивных: {len(archived_ids)}')
print(f'Общих ID (пересечения): {len(common_ids)}')

if common_ids:
    print(f'\n⚠️ ВНИМАНИЕ: Найдено {len(common_ids)} записей, которые есть И в активных И в архивных!')
    print(f'Примеры ID: {list(common_ids)[:5]}')

    # Анализ пересечений
    common_active = active_df[active_df['id'].isin(common_ids)]
    common_archived = archived_df[archived_df['id'].isin(common_ids)]

    print(f'\nАнализ пересечений:')
    for idx, row_active in common_active.head(3).iterrows():
        row_archived = common_archived[common_archived['id'] == row_active['id']].iloc[0]
        print(f'\nID: {row_active["id"]}')
        print(f'  Активный: is_study={row_active["is_study"]}, lead_reject_id={row_active["lead_reject_id"]}')
        print(f'  Архивный: is_study={row_archived["is_study"]}, lead_reject_id={row_archived["lead_reject_id"]}')
else:
    print('✅ Пересечений НЕТ - все ID уникальны!')

print('\n[STEP 3/5] Добавление метки типа записи...')
print('-' * 80)

# Добавляем колонку lead_type
active_df['lead_type'] = 'active'
archived_df['lead_type'] = 'archived'

print('✅ Добавлена колонка lead_type')

print('\n[STEP 4/5] Объединение датасетов...')
print('-' * 80)

# Стратегия объединения
if common_ids:
    print(f'Стратегия: Приоритет АРХИВНЫМ записям для {len(common_ids)} пересечений')

    # Удаляем активные записи, которые есть в архивных
    active_df_cleaned = active_df[~active_df['id'].isin(common_ids)]

    print(f'Активных после очистки: {len(active_df_cleaned)}')
    print(f'Архивных (приоритет): {len(archived_df)}')

    # Объединяем
    merged_df = pd.concat([active_df_cleaned, archived_df], ignore_index=True)
else:
    print('Стратегия: Простое объединение (пересечений нет)')
    merged_df = pd.concat([active_df, archived_df], ignore_index=True)

print(f'\n✅ Объединено записей: {len(merged_df)}')

# Проверка финальной уникальности
unique_ids = merged_df['id'].nunique()
print(f'Уникальных ID в финальном датасете: {unique_ids}')

if unique_ids == len(merged_df):
    print('✅ Все ID уникальны в финальном датасете!')
else:
    print(f'⚠️ Найдены дубли: {len(merged_df) - unique_ids} дублей')

print('\n[STEP 5/5] Статистика и экспорт...')
print('-' * 80)

# Статистика по типам
print('\nРаспределение по типам:')
print(merged_df['lead_type'].value_counts())

# Статистика по is_study
print('\nРаспределение по is_study:')
print(merged_df['is_study'].value_counts())

# Статистика по архивным причинам
archived_with_reject = merged_df[
    (merged_df['lead_type'] == 'archived') &
    (merged_df['lead_reject_id'].notna() | merged_df['customer_reject_id'].notna())
]
print(f'\nАрхивных с заполненными reject_id: {len(archived_with_reject)}')

# Экспорт
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
output_file = f'alfacrm_ALL_leads_merged_{timestamp}.csv'

merged_df.to_csv(output_file, index=False, encoding='utf-8')

file_size = os.path.getsize(output_file) / 1024 / 1024

print(f'\n[SUCCESS] Финальный объединенный экспорт!')
print(f'Файл: {output_file}')
print(f'Размер: {file_size:.2f} MB')
print(f'Всего записей: {len(merged_df)}')
print(f'Уникальных ID: {unique_ids}')
print(f'Полей: {len(merged_df.columns)}')

print('\n' + '=' * 80)
print('[INFO] ЗАВЕРШЕНО')
print('=' * 80)
