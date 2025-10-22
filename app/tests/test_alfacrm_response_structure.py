"""
Тест для детального анализа структуры ответа AlfaCRM API.

ЦЕЛЬ: Выяснить где хранится статус студента и как его правильно читать.
"""
import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

# Завантажити змінні середовища
load_dotenv()

# Додати app директорію в Python path
app_dir = Path(__file__).parent.parent
sys.path.insert(0, str(app_dir))

from connectors.crm import alfacrm_list_students


def test_alfacrm_response_structure():
    """
    Детальний аналіз структури відповіді AlfaCRM API.
    """

    print("\n" + "="*80)
    print("АНАЛІЗ: Структура відповіді AlfaCRM API")
    print("="*80)

    # Отримати студентів
    print(f"\n[1/2] Отримання студентів з AlfaCRM...")
    try:
        response = alfacrm_list_students(page=1, page_size=500)

        print(f"  Отримано відповідь від API")
        print(f"\n  Ключі верхнього рівня відповіді:")
        for key in response.keys():
            print(f"    - {key}: {type(response[key])}")

        students = response.get('items', [])
        total_count = response.get('count', 0)

        print(f"\n  Кількість студентів: {len(students)}")
        print(f"  Загальна кількість в системі: {total_count}")

    except Exception as e:
        print(f"  ПОМИЛКА: {e}")
        import traceback
        traceback.print_exc()
        return

    # Детальний аналіз структури студента
    if not students:
        print("\n  ПОМИЛКА: Немає студентів для аналізу")
        return

    print(f"\n[2/2] Аналіз структури об'єкта студента...")

    first_student = students[0]

    print(f"\n  Всі поля першого студента:")
    print(f"  {'-'*70}")

    # Сортуємо ключі для зручності
    for key in sorted(first_student.keys()):
        value = first_student[key]
        value_type = type(value).__name__

        # Обмежуємо вивід для великих значень
        if isinstance(value, (list, dict)):
            value_repr = f"{value_type} (довжина: {len(value)})"
        elif isinstance(value, str) and len(value) > 50:
            value_repr = f"'{value[:50]}...'"
        else:
            value_repr = repr(value)

        print(f"    {key:25s} : {value_repr}")

    print(f"  {'-'*70}")

    # Пошук можливих полів статусу
    print(f"\n  ПОШУК ПОЛІВ СТАТУСУ:")
    print(f"  {'-'*70}")

    status_fields = [
        'status_id', 'status', 'lead_status_id', 'lead_status',
        'customer_status_id', 'customer_status', 'student_status_id'
    ]

    found_status_fields = []

    for field in status_fields:
        if field in first_student:
            value = first_student[field]
            found_status_fields.append((field, value))
            print(f"    ✓ {field}: {value}")
        else:
            print(f"    ✗ {field}: не знайдено")

    print(f"  {'-'*70}")

    # Якщо є вкладені об'єкти - проаналізувати їх
    print(f"\n  АНАЛІЗ ВКЛАДЕНИХ ОБ'ЄКТІВ:")
    print(f"  {'-'*70}")

    for key, value in first_student.items():
        if isinstance(value, dict):
            print(f"\n    Об'єкт '{key}':")
            for nested_key in sorted(value.keys()):
                nested_value = value[nested_key]
                print(f"      {nested_key}: {repr(nested_value)[:60]}")

    print(f"  {'-'*70}")

    # Показати приклади для кількох студентів
    print(f"\n  ПРИКЛАДИ ДЛЯ 3 СТУДЕНТІВ:")
    print(f"  {'-'*70}")

    for i, student in enumerate(students[:3], 1):
        print(f"\n    Студент {i}:")
        print(f"      ID: {student.get('id')}")
        print(f"      Name: {student.get('name', 'N/A')}")

        # Показати всі знайдені поля статусу
        for field, _ in found_status_fields:
            value = student.get(field)
            print(f"      {field}: {value}")

    # ВИСНОВКИ
    print("\n" + "="*80)
    print("ВИСНОВКИ:")
    print("="*80)

    if found_status_fields:
        print(f"\n1. Знайдено {len(found_status_fields)} полів статусу:")
        for field, value in found_status_fields:
            print(f"   - {field}: {value}")

        print(f"\n2. ПРАВИЛЬНЕ ПОЛЕ СТАТУСУ:")
        # Пріоритет: status_id > lead_status_id > status
        if 'status_id' in dict(found_status_fields):
            print(f"   Використовувати: status_id")
        elif 'lead_status_id' in dict(found_status_fields):
            print(f"   Використовувати: lead_status_id")
        else:
            print(f"   Використовувати: {found_status_fields[0][0]}")
    else:
        print(f"\n1. КРИТИЧНА ПРОБЛЕМА: Не знайдено жодного поля статусу!")
        print(f"   Можливі причини:")
        print(f"   - AlfaCRM не повертає статус через цей endpoint")
        print(f"   - Статус зберігається під іншою назвою поля")
        print(f"   - Потрібен інший API endpoint")

        print(f"\n2. НАСТУПНИЙ КРОК:")
        print(f"   Перевірити документацію AlfaCRM API")
        print(f"   або зв'язатися з підтримкою для з'ясування")

    # Показати повний JSON першого студента
    print(f"\n3. ПОВНИЙ JSON ПЕРШОГО СТУДЕНТА:")
    print(f"   (для детального аналізу)")
    print(f"\n{json.dumps(first_student, indent=2, ensure_ascii=False)}")


if __name__ == "__main__":
    test_alfacrm_response_structure()
