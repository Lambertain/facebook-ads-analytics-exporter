"""
Тест для анализа ВСЕХ status_id в AlfaCRM системе.

ЦЕЛЬ: Выяснить какие status_id реально используются и есть ли среди них Archive (7).
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from collections import Counter

# Завантажити змінні середовища
load_dotenv()

# Додати app директорію в Python path
app_dir = Path(__file__).parent.parent
sys.path.insert(0, str(app_dir))

from connectors.crm import alfacrm_list_students


def test_all_status_ids():
    """
    Анализ всех status_id в AlfaCRM.
    """

    print("\n" + "="*80)
    print("АНАЛИЗ: Все status_id в AlfaCRM системе")
    print("="*80)

    # Получить студентов
    print(f"\n[1/2] Получение студентов из AlfaCRM...")
    try:
        response = alfacrm_list_students(page=1, page_size=500)
        students = response.get('items', [])
        total_count = response.get('count', 0)

        print(f"  Получено студентов: {len(students)}")
        print(f"  Общее количество в системе: {total_count}")

    except Exception as e:
        print(f"  ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
        return

    # Анализ status_id
    print(f"\n[2/2] Анализ всех status_id...")

    # Счетчик status_id
    status_counter = Counter()

    for student in students:
        status_id = student.get('status_id')
        if status_id is not None:
            status_counter[status_id] += 1

    # Вывод результатов
    print(f"\n  Найдено уникальных status_id: {len(status_counter)}")
    print(f"\n  Распределение по status_id:")
    print(f"  {'-'*70}")

    # Сортировка по ID для удобства
    for status_id in sorted(status_counter.keys()):
        count = status_counter[status_id]
        percentage = count / len(students) * 100
        print(f"    status_id {status_id:2d}: {count:3d} лидов ({percentage:5.1f}%)")

    print(f"  {'-'*70}")

    # Проверка на Archive (status_id = 7)
    print(f"\n  ПРОВЕРКА на Archive (status_id = 7):")
    if 7 in status_counter:
        print(f"    ✓ status_id = 7 НАЙДЕН: {status_counter[7]} лидов")
    else:
        print(f"    ✗ status_id = 7 НЕ НАЙДЕН в системе")

    # Показать примеры для каждого status_id
    print(f"\n  Примеры лидов для каждого status_id:")
    print(f"  {'-'*70}")

    status_examples = {}
    for student in students:
        status_id = student.get('status_id')
        if status_id not in status_examples:
            status_examples[status_id] = student

    for status_id in sorted(status_examples.keys()):
        example = status_examples[status_id]
        print(f"\n    status_id {status_id}:")
        print(f"      ID: {example.get('id')}")
        print(f"      Name: {example.get('name', 'N/A')}")
        print(f"      Comment (первые 50 символов):")
        comment = example.get('comment', '')
        if comment:
            print(f"        {str(comment)[:50]}...")
        else:
            print(f"        (пусто)")

    # Итоги
    print("\n" + "="*80)
    print("ВЫВОДЫ:")
    print("="*80)

    print(f"\n1. Всего уникальных status_id: {len(status_counter)}")
    print(f"2. Все найденные status_id: {sorted(status_counter.keys())}")

    if 7 not in status_counter:
        print(f"\n3. Archive status (ID=7) НЕ ИСПОЛЬЗУЕТСЯ в текущих данных")
        print(f"   Возможные причины:")
        print(f"   - Нет лидов с таким статусом")
        print(f"   - Archive лиды перемещаются в другую таблицу")
        print(f"   - Archive имеет другой ID")
        print(f"\n4. РЕКОМЕНДАЦИЯ:")
        print(f"   Пока Archive лидов нет - добавлять status_id=7 в ALFACRM_STATUS_TO_GROUP")
        print(f"   НЕ ОБЯЗАТЕЛЬНО. Но можно добавить для будущего использования.")
    else:
        print(f"\n3. Archive status (ID=7) НАЙДЕН: {status_counter[7]} лидов")
        print(f"\n4. РЕКОМЕНДАЦИЯ:")
        print(f"   НЕОБХОДИМО добавить status_id=7 в ALFACRM_STATUS_TO_GROUP mapping")
        print(f"   как отдельную группу 'Архів' или включить в существующую группу")


if __name__ == "__main__":
    test_all_status_ids()
