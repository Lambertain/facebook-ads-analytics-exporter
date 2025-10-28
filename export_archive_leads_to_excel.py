"""
Експорт всіх архівних лідів з AlfaCRM в Excel таблицю.

Створює Excel файл з:
- Українськими назвами полів
- Позначками "С" для стандартних полів
- Позначками "К" для кастомних полів
- Повною інформацією про всіх архівних лідів
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import pandas as pd
from datetime import datetime
import requests

# Загрузка переменных окружения
load_dotenv()

# Добавить app директорию в Python path
app_dir = Path(__file__).parent / "app"
sys.path.insert(0, str(app_dir))

from connectors.crm import alfacrm_auth_get_token


# Словарь переводов названий полей на украинский
FIELD_TRANSLATIONS = {
    # Основные поля
    "id": "ID",
    "name": "Ім'я",
    "created_at": "Дата створення",
    "updated_at": "Дата оновлення",

    # Статусы
    "lead_status_id": "ID статусу ліда",
    "study_status_id": "ID статусу навчання",
    "is_study": "Навчається",
    "color": "Колір",

    # Контакты
    "phone": "Телефони",
    "email": "Email адреси",
    "addr": "Адреса",

    # Финансы
    "balance": "Баланс",
    "balance_base": "Базовий баланс",
    "balance_bonus": "Бонусний баланс",
    "paid_count": "Кількість оплат",
    "paid_lesson_count": "Кількість оплачених уроків",

    # Назначения
    "assigned_id": "ID відповідального",
    "branch_ids": "ID філій",
    "company_id": "ID компанії",

    # Дополнительная информация
    "b_date": "Дата народження",
    "sex": "Стать",
    "barcode": "Штрих-код",
    "comment": "Коментар",
    "legal_type": "Тип особи",

    # Custom поля (основные известные)
    "custom_ads_comp": "Назва кампанії",
    "custom_id_srm": "ID з Facebook",
    "custom_gorodstvaniya": "Громадянство",
    "custom_age_": "Вік",
    "custom_email": "Email (custom)",
    "custom_yazik": "Мова",
    "custom_urovenvladenwoo": "Рівень володіння",
    "custom_schedule": "Розклад",
    "custom_try_lessons": "Пробні уроки",
}


def get_all_archive_leads():
    """
    Получить ВСЕХ архивных лидов из AlfaCRM.

    ВАЖНО: Архів визначається за custom_ads_comp == 'архів', а НЕ за lead_status_id!
    Тому завантажуємо всіх студентів і фільтруємо на стороні клієнта.

    Returns:
        List[dict]: Список всех архивных лидов
    """
    print("\n" + "="*80)
    print("ЗБІР АРХІВНИХ ЛІДІВ З ALFACRM")
    print("="*80)

    token = alfacrm_auth_get_token()
    base_url = os.getenv("ALFACRM_BASE_URL").rstrip('/')
    company_id = int(os.getenv("ALFACRM_COMPANY_ID"))

    all_students = []
    page = 1
    page_size = 500  # Максимальный размер страницы

    # Завантажуємо всіх студентів
    print(f"\n[1/2] Завантаження всіх студентів...")

    while True:
        url = f"{base_url}/v2api/customer/index"
        payload = {
            "branch_ids": [company_id],
            "page": page,
            "page_size": page_size
        }

        try:
            resp = requests.post(
                url,
                headers={"X-ALFACRM-TOKEN": token},
                json=payload,
                timeout=15
            )
            resp.raise_for_status()
            data = resp.json()

            items = data.get("items", [])
            total = data.get("count", 0)

            print(f"  Сторінка {page}: {len(items)} студентів")

            if not items:
                break

            all_students.extend(items)

            # Проверяем загрузили ли мы всех
            if len(all_students) >= total:
                break

            page += 1

        except Exception as e:
            print(f"  ✗ Помилка: {e}")
            import traceback
            traceback.print_exc()
            break

    print(f"  ✓ Всього завантажено: {len(all_students)} студентів")

    # Фільтруємо архівні ліди (custom_ads_comp == 'архів')
    print(f"\n[2/2] Фільтрація архівних лідів...")
    archive_leads = [
        student for student in all_students
        if student.get("custom_ads_comp") == "архів"
    ]

    print(f"  ✓ Знайдено архівних лідів: {len(archive_leads)}")

    print(f"\n{'='*80}")
    print(f"Всього архівних лідів: {len(archive_leads)}")
    print(f"{'='*80}\n")

    return archive_leads


def get_ukrainian_column_name(field_name: str, all_fields: set) -> str:
    """
    Получить украинское название поля с маркером (С) или (К).

    Args:
        field_name: Название поля на английском
        all_fields: Множество всех полей для контекста

    Returns:
        str: Украинское название с маркером
    """
    # Определяем тип поля
    is_custom = field_name.startswith("custom_")
    marker = "К" if is_custom else "С"

    # Получаем перевод
    if field_name in FIELD_TRANSLATIONS:
        ukr_name = FIELD_TRANSLATIONS[field_name]
    else:
        # Для неизвестных custom полей берем название без префикса
        if is_custom:
            ukr_name = field_name.replace("custom_", "").replace("_", " ").title()
        else:
            ukr_name = field_name.replace("_", " ").title()

    return f"{ukr_name} ({marker})"


def format_cell_value(value):
    """
    Форматировать значение ячейки для удобного отображения в Excel.

    Args:
        value: Значение любого типа

    Returns:
        Отформатированное значение для Excel
    """
    if value is None or value == "":
        return ""

    # Списки и массивы преобразуем в строку
    if isinstance(value, list):
        if not value:
            return ""
        # Если список телефонов/email
        return ", ".join(str(v) for v in value)

    # Словари преобразуем в JSON-подобную строку
    if isinstance(value, dict):
        return str(value)

    # Булевы значения
    if isinstance(value, bool):
        return "Так" if value else "Ні"

    # Длинные строки обрезаем для удобства
    if isinstance(value, str) and len(value) > 500:
        return value[:500] + "..."

    return value


def export_to_excel(leads: list, output_file: str):
    """
    Экспортировать лиды в Excel файл.

    Args:
        leads: Список лидов
        output_file: Путь к выходному файлу
    """
    if not leads:
        print("❌ Немає лідів для експорту!")
        return

    print(f"\n[1/3] Підготовка даних для експорту...")

    # Собираем все уникальные поля из всех лидов
    all_fields = set()
    for lead in leads:
        all_fields.update(lead.keys())

    print(f"  ✓ Знайдено {len(all_fields)} унікальних полів")

    # Сортируем поля: сначала стандартные, потом custom
    standard_fields = sorted([f for f in all_fields if not f.startswith("custom_")])
    custom_fields = sorted([f for f in all_fields if f.startswith("custom_")])
    sorted_fields = standard_fields + custom_fields

    print(f"  ✓ Стандартних полів: {len(standard_fields)}")
    print(f"  ✓ Кастомних полів: {len(custom_fields)}")

    # Создаем DataFrame
    print(f"\n[2/3] Створення таблиці...")

    # Подготавливаем данные для DataFrame
    data = []
    for lead in leads:
        row = {}
        for field in sorted_fields:
            ukr_col_name = get_ukrainian_column_name(field, all_fields)
            row[ukr_col_name] = format_cell_value(lead.get(field))
        data.append(row)

    df = pd.DataFrame(data)

    print(f"  ✓ Створено таблицю: {len(df)} рядків × {len(df.columns)} стовпців")

    # Экспортируем в Excel
    print(f"\n[3/3] Експорт в Excel файл...")

    try:
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Архівні ліди', index=False)

            # Получаем workbook для форматирования
            workbook = writer.book
            worksheet = writer.sheets['Архівні ліди']

            # Автоматически подбираем ширину столбцов
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter

                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass

                # Ограничиваем максимальную ширину
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width

            # Замораживаем первую строку (заголовки)
            worksheet.freeze_panes = 'A2'

        print(f"  ✓ Файл збережено: {output_file}")

    except Exception as e:
        print(f"  ✗ Помилка при експорті: {e}")
        import traceback
        traceback.print_exc()
        return

    # Статистика по заполненности полей
    print(f"\n{'='*80}")
    print("СТАТИСТИКА ЗАПОВНЕНОСТІ ПОЛІВ")
    print(f"{'='*80}\n")

    # Анализируем заполненность
    print("Топ-20 найбільш заповнених полів:")
    print("-" * 80)

    field_stats = []
    for col in df.columns:
        non_empty = df[col].astype(str).str.strip().replace('', None).notna().sum()
        percentage = (non_empty / len(df)) * 100
        field_stats.append((col, non_empty, percentage))

    # Сортируем по заполненности
    field_stats.sort(key=lambda x: x[1], reverse=True)

    for i, (field, count, pct) in enumerate(field_stats[:20], 1):
        # Сокращаем длинные названия для красивого вывода
        display_name = field if len(field) <= 40 else field[:37] + "..."
        bar_length = int(pct / 2)  # Масштаб для визуализации
        bar = "█" * bar_length
        print(f"{i:2}. {display_name:42} │ {count:3}/{len(df)} │ {pct:5.1f}% │{bar}")

    # Показываем пустые поля
    empty_fields = [f for f, c, p in field_stats if c == 0]
    if empty_fields:
        print(f"\n⚠ Повністю порожні поля ({len(empty_fields)}):")
        for field in empty_fields[:10]:
            print(f"  - {field}")
        if len(empty_fields) > 10:
            print(f"  ... та ще {len(empty_fields) - 10} полів")

    print(f"\n{'='*80}\n")


def main():
    """
    Основная функция для экспорта архивных лидов.
    """
    # Проверяем наличие pandas
    try:
        import pandas as pd
        import openpyxl
    except ImportError:
        print("❌ Помилка: Необхідні бібліотеки pandas та openpyxl")
        print("\nВстановіть їх командою:")
        print("  pip install pandas openpyxl")
        return

    # Получаем всех архивных лидов
    leads = get_all_archive_leads()

    if not leads:
        print("❌ Не вдалося отримати архівних лідів")
        return

    # Формируем имя выходного файла с датой
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    output_file = f"Архівні_ліди_{timestamp}.xlsx"

    # Экспортируем в Excel
    export_to_excel(leads, output_file)

    print(f"✅ ГОТОВО! Архівні ліди експортовано в файл: {output_file}")
    print(f"📊 Всього лідів: {len(leads)}\n")


if __name__ == "__main__":
    main()
