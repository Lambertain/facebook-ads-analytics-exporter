#!/usr/bin/env python3
"""Тестовый скрипт для проверки форматирования массивов телефонов в Excel."""
from openpyxl import Workbook
from openpyxl.styles import Alignment
from datetime import datetime

# Тестовые данные с массивами телефонов (как в production)
students_data = [
    {
        "campaign_name": "Test Campaign 1",
        "budget": 1000.0,
        "location": "Київ",
        "leads_count": ["+380501234567", "+380631234568", "+380931234569"],
        "target_leads": 8,
        "non_target_leads": 2,
        "Не розібраний": ["+380501234567"],
        "Недозвон (не ЦА)": ["+380631234568"],
        "Встановлено контакт (ЦА)": ["+380931234569", "+380671234570"],
        "В опрацюванні (ЦА)": ["+380501234571", "+380631234572"],
        "Призначено пробне (ЦА)": ["+380931234573"],
        "Проведено пробне (ЦА)": ["+380671234574"],
        "Чекає оплату": [],
        "Отримана оплата (ЦА)": ["+380501234575"],
        "Архів (ЦА)": ["+380631234576"],
        "Архів (не ЦА)": ["+380931234577"]
    },
    {
        "campaign_name": "Test Campaign 2",
        "budget": 1500.0,
        "location": "Львів",
        "leads_count": ["+380501111111", "+380632222222"],
        "target_leads": 5,
        "non_target_leads": 1,
        "Не розібраний": [],
        "Недозвон (не ЦА)": ["+380501111111"],
        "Встановлено контакт (ЦА)": ["+380632222222"],
        "В опрацюванні (ЦА)": [],
        "Призначено пробне (ЦА)": [],
        "Проведено пробне (ЦА)": [],
        "Чекає оплату": [],
        "Отримана оплата (ЦА)": [],
        "Архів (ЦА)": [],
        "Архів (не ЦА)": []
    }
]

# Список полей с массивами телефонов (как в main.py)
phone_array_fields = {
    "leads_count",
    "Не розібраний",
    "Недозвон (не ЦА)",
    "Встановлено контакт (ЦА)",
    "В опрацюванні (ЦА)",
    "Призначено пробне (ЦА)",
    "Проведено пробне (ЦА)",
    "Чекає оплату",
    "Отримана оплата (ЦА)",
    "Архів (ЦА)",
    "Архів (не ЦА)"
}

print("=" * 80)
print("ТЕСТ: Форматирование массивов телефонов в Excel")
print("=" * 80)

# Создаем Excel файл
wb = Workbook()
ws = wb.active
ws.title = "Студенти"

# Заголовки
headers = list(students_data[0].keys())
ws.append(headers)

print(f"\nКоличество записей: {len(students_data)}")
print(f"Количество колонок: {len(headers)}")
print(f"\nКолонки с массивами телефонов:")
for h in headers:
    if h in phone_array_fields:
        print(f"  - {h}")

# Данные с форматированием (как в main.py)
for row_idx, row_data in enumerate(students_data, start=2):  # start=2 т.к. row 1 = заголовки
    # Преобразуем значения: массивы телефонов → строки с переносами
    formatted_row = []
    for key, value in row_data.items():
        if key in phone_array_fields and isinstance(value, list):
            # Форматируем массив телефонов как строку с переносами
            formatted_value = "\n".join(value) if value else ""
            formatted_row.append(formatted_value)
        else:
            formatted_row.append(value)

    ws.append(formatted_row)

    # Применяем wrap_text к ячейкам с телефонами
    for col_idx, key in enumerate(headers, start=1):
        if key in phone_array_fields:
            cell = ws.cell(row=row_idx, column=col_idx)
            cell.alignment = Alignment(wrap_text=True, vertical="top")

# Сохраняем
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
filename = f"test_phone_arrays_{timestamp}.xlsx"
wb.save(filename)

print(f"\n✓ Excel файл создан: {filename}")
print("\nПроверьте файл:")
print(f"  1. Откройте {filename} в Excel")
print("  2. Проверьте что телефоны в колонках leads_count и статусах")
print("  3. Проверьте что телефоны разделены переносами строк")
print("  4. Проверьте что ячейки имеют wrap_text (автоперенос)")
print("\n" + "=" * 80)
