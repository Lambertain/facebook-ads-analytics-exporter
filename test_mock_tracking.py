"""
Тест модулей трекинга с моковыми данными (без необходимости в валидных Meta токенах).
Демонстрирует работу alfacrm_tracking и nethunt_tracking на реалистичных данных.
"""
import sys
import asyncio
from datetime import datetime

# Добавить app в путь
sys.path.insert(0, 'app')

from services import alfacrm_tracking
from services import nethunt_tracking


def print_separator(title: str, char: str = "="):
    """Печать разделителя с заголовком."""
    width = 80
    print(f"\n{char * width}")
    print(f"{title:^{width}}")
    print(f"{char * width}\n")


# Моковые данные студентов из AlfaCRM (симулируем реальную структуру)
MOCK_STUDENTS = [
    {
        "id": 1001,
        "name": "Иванов Иван",
        "phone": ["+380501234567"],
        "email": ["ivan@example.com"],
        "lead_status_id": 6,  # Купили (ЦА)
        "is_study": 1
    },
    {
        "id": 1002,
        "name": "Петров Петр",
        "phone": ["+380502345678"],
        "email": ["petr@example.com"],
        "lead_status_id": 5,  # Проведений пробний
        "is_study": 0
    },
    {
        "id": 1003,
        "name": "Сидорова Анна",
        "phone": ["+380503456789"],
        "email": ["anna@example.com"],
        "lead_status_id": 4,  # Назначений пробний
        "is_study": 0
    },
    {
        "id": 1004,
        "name": "Коваленко Ольга",
        "phone": ["+380504567890"],
        "email": ["olga@example.com"],
        "lead_status_id": 3,  # В опрацюванні (ЦА)
        "is_study": 0
    },
    {
        "id": 1005,
        "name": "Шевченко Тарас",
        "phone": ["+380505678901"],
        "email": ["taras@example.com"],
        "lead_status_id": 2,  # Встанов. контакт (ЦА)
        "is_study": 0
    },
    {
        "id": 1006,
        "name": "Мельник Владимир",
        "phone": ["+380506789012"],
        "email": [],
        "lead_status_id": 1,  # Не розібрані
        "is_study": 0
    },
    {
        "id": 1007,
        "name": "Левченко Дмитрий",
        "phone": ["+380507890123"],
        "email": ["dmitry@example.com"],
        "lead_status_id": 8,  # Недзвін
        "is_study": 0
    },
    {
        "id": 1008,
        "name": "Гончарук Елена",
        "phone": ["+380508901234"],
        "email": ["elena@example.com"],
        "lead_status_id": 6,  # Купили (ЦА)
        "is_study": 1
    },
    {
        "id": 1009,
        "name": "Бондаренко Сергей",
        "phone": ["+380509012345"],
        "email": ["sergey@example.com"],
        "lead_status_id": 7,  # Архів
        "is_study": 0
    },
    {
        "id": 1010,
        "name": "Захарова Наталья",
        "phone": ["+380500123456"],
        "email": ["natalia@example.com"],
        "lead_status_id": 5,  # Проведений пробний
        "is_study": 0
    }
]


# Моковые данные учителей из NetHunt
MOCK_TEACHERS = [
    {
        "id": "rec_2001",
        "fields": {
            "Name": "Марченко Виктория",
            "Phone": "+380671234567",
            "Email": "victoria@teacher.com"
        },
        "status": {"name": "Hired"}  # Найнято
    },
    {
        "id": "rec_2002",
        "fields": {
            "Phone": "+380672345678",
            "Email": "alexander@teacher.com"
        },
        "status": {"name": "Interview_Completed"}  # Співбесіда проведена
    },
    {
        "id": "rec_2003",
        "fields": {
            "Phone": "+380673456789",
            "Email": "maria@teacher.com"
        },
        "status": {"name": "Interview_Scheduled"}  # Співбесіда призначена
    },
    {
        "id": "rec_2004",
        "fields": {
            "Phone": "+380674567890"
        },
        "status": {"name": "Qualified"}  # Кваліфіковані
    },
    {
        "id": "rec_2005",
        "fields": {
            "Email": "andrey@teacher.com"
        },
        "status": {"name": "Contacted"}  # Контакт встановлено
    },
    {
        "id": "rec_2006",
        "fields": {
            "Phone": "+380676789012"
        },
        "status": {"name": "New"}  # Нові
    },
    {
        "id": "rec_2007",
        "fields": {
            "Email": "svetlana@teacher.com"
        },
        "status": {"name": "No_Answer"}  # Недзвін
    },
    {
        "id": "rec_2008",
        "fields": {
            "Phone": "+380678901234",
            "Email": "igor@teacher.com"
        },
        "status": {"name": "Rejected"}  # Відмова
    }
]


# Моковые лиды из Meta API
MOCK_META_LEADS_STUDENTS = [
    {
        "id": "lead_10001",
        "created_time": "2025-10-05T10:30:00+0000",
        "campaign_id": "camp_student_001",
        "campaign_name": "Student Campaign - German A1",
        "field_data": [
            {"name": "phone_number", "values": ["+380501234567"]},
            {"name": "email", "values": ["ivan@example.com"]}
        ]
    },
    {
        "id": "lead_10002",
        "created_time": "2025-10-05T11:15:00+0000",
        "campaign_id": "camp_student_001",
        "campaign_name": "Student Campaign - German A1",
        "field_data": [
            {"name": "phone_number", "values": ["+380502345678"]},
            {"name": "email", "values": ["petr@example.com"]}
        ]
    },
    {
        "id": "lead_10003",
        "created_time": "2025-10-05T14:20:00+0000",
        "campaign_id": "camp_student_001",
        "campaign_name": "Student Campaign - German A1",
        "field_data": [
            {"name": "phone_number", "values": ["+380503456789"]},
            {"name": "email", "values": ["anna@example.com"]}
        ]
    },
    {
        "id": "lead_10004",
        "created_time": "2025-10-06T09:00:00+0000",
        "campaign_id": "camp_student_002",
        "campaign_name": "Student Campaign - German B1",
        "field_data": [
            {"name": "phone_number", "values": ["+380504567890"]},
            {"name": "email", "values": ["olga@example.com"]}
        ]
    },
    {
        "id": "lead_10005",
        "created_time": "2025-10-06T12:45:00+0000",
        "campaign_id": "camp_student_002",
        "campaign_name": "Student Campaign - German B1",
        "field_data": [
            {"name": "phone_number", "values": ["+380505678901"]},
            {"name": "email", "values": ["taras@example.com"]}
        ]
    },
    {
        "id": "lead_10006",
        "created_time": "2025-10-07T10:00:00+0000",
        "campaign_id": "camp_student_001",
        "campaign_name": "Student Campaign - German A1",
        "field_data": [
            {"name": "phone_number", "values": ["+380506789012"]}
        ]
    },
    {
        "id": "lead_10007",
        "created_time": "2025-10-07T15:30:00+0000",
        "campaign_id": "camp_student_002",
        "campaign_name": "Student Campaign - German B1",
        "field_data": [
            {"name": "phone_number", "values": ["+380508901234"]},
            {"name": "email", "values": ["elena@example.com"]}
        ]
    }
]


MOCK_META_LEADS_TEACHERS = [
    {
        "id": "lead_20001",
        "created_time": "2025-10-05T09:00:00+0000",
        "campaign_id": "camp_teacher_001",
        "campaign_name": "Teacher Campaign - German Teachers",
        "field_data": [
            {"name": "phone_number", "values": ["+380671234567"]},
            {"name": "email", "values": ["victoria@teacher.com"]}
        ]
    },
    {
        "id": "lead_20002",
        "created_time": "2025-10-05T11:30:00+0000",
        "campaign_id": "camp_teacher_001",
        "campaign_name": "Teacher Campaign - German Teachers",
        "field_data": [
            {"name": "phone_number", "values": ["+380672345678"]},
            {"name": "email", "values": ["alexander@teacher.com"]}
        ]
    },
    {
        "id": "lead_20003",
        "created_time": "2025-10-06T10:15:00+0000",
        "campaign_id": "camp_teacher_001",
        "campaign_name": "Teacher Campaign - German Teachers",
        "field_data": [
            {"name": "phone_number", "values": ["+380673456789"]},
            {"name": "email", "values": ["maria@teacher.com"]}
        ]
    },
    {
        "id": "lead_20004",
        "created_time": "2025-10-06T14:00:00+0000",
        "campaign_id": "camp_teacher_002",
        "campaign_name": "Teacher Campaign - English Teachers",
        "field_data": [
            {"name": "phone_number", "values": ["+380674567890"]}
        ]
    },
    {
        "id": "lead_20005",
        "created_time": "2025-10-07T11:00:00+0000",
        "campaign_id": "camp_teacher_002",
        "campaign_name": "Teacher Campaign - English Teachers",
        "field_data": [
            {"name": "email", "values": ["andrey@teacher.com"]}
        ]
    }
]


def test_students_tracking():
    """Тест трекинга студентов с моковыми данными."""

    print_separator("ТЕСТ СТУДЕНТОВ: AlfaCRM Tracking (Mock Data)", "=")

    # Группируем моковые лиды по кампаниям
    campaigns_data = {}
    for lead in MOCK_META_LEADS_STUDENTS:
        campaign_id = lead["campaign_id"]
        if campaign_id not in campaigns_data:
            campaigns_data[campaign_id] = {
                "campaign_id": campaign_id,
                "campaign_name": lead["campaign_name"],
                "leads": []
            }
        campaigns_data[campaign_id]["leads"].append(lead)

    print(f"Моковые данные:")
    print(f"  Кампаний: {len(campaigns_data)}")
    print(f"  Лидов: {len(MOCK_META_LEADS_STUDENTS)}")
    print(f"  Студентов в CRM: {len(MOCK_STUDENTS)}")

    # Строим индекс студентов
    print(f"\n[1/3] Построение индекса студентов...")
    student_index = alfacrm_tracking.build_student_index(MOCK_STUDENTS)
    print(f"  OK Индекс построен ({len(student_index)} контактов)")

    # Трекинг по каждой кампании
    print(f"\n[2/3] Трекинг лидов по статусам...")

    enriched_campaigns = {}
    for campaign_id, campaign_data in campaigns_data.items():
        funnel_stats = alfacrm_tracking.track_campaign_leads(
            campaign_data["leads"],
            student_index
        )

        enriched_campaigns[campaign_id] = {
            "campaign_id": campaign_id,
            "campaign_name": campaign_data["campaign_name"],
            "leads_count": len(campaign_data["leads"]),
            "funnel_stats": funnel_stats
        }

        print(f"\n  Кампания: {campaign_data['campaign_name']}")
        print(f"    Лидов: {len(campaign_data['leads'])}")
        for status, count in funnel_stats.items():
            if count > 0 and status != "Кількість лідів":
                print(f"    {status}: {count}")

    # Вычисляем метрики
    print(f"\n[3/3] Вычисление метрик...")

    for campaign in enriched_campaigns.values():
        funnel = campaign["funnel_stats"]
        conv = alfacrm_tracking.calculate_conversion_rate(funnel)
        target = alfacrm_tracking.calculate_target_leads_percentage(funnel)
        trial = alfacrm_tracking.calculate_trial_conversion(funnel)

        print(f"\n  {campaign['campaign_name']}:")
        print(f"    % целевых: {target}%")
        print(f"    % конверсия: {conv}%")
        print(f"    % пробний->продажа: {trial}%")

    print_separator("ТЕСТ СТУДЕНТОВ ЗАВЕРШЕН", "=")


def test_teachers_tracking():
    """Тест трекинга учителей с моковыми данными."""

    print_separator("ТЕСТ УЧИТЕЛЕЙ: NetHunt Tracking (Mock Data)", "=")

    # Группируем моковые лиды по кампаниям
    campaigns_data = {}
    for lead in MOCK_META_LEADS_TEACHERS:
        campaign_id = lead["campaign_id"]
        if campaign_id not in campaigns_data:
            campaigns_data[campaign_id] = {
                "campaign_id": campaign_id,
                "campaign_name": lead["campaign_name"],
                "leads": []
            }
        campaigns_data[campaign_id]["leads"].append(lead)

    print(f"Моковые данные:")
    print(f"  Кампаний: {len(campaigns_data)}")
    print(f"  Лидов: {len(MOCK_META_LEADS_TEACHERS)}")
    print(f"  Учителей в CRM: {len(MOCK_TEACHERS)}")

    # Строим индекс учителей
    print(f"\n[1/3] Построение индекса учителей...")
    teacher_index = nethunt_tracking.build_teacher_index(MOCK_TEACHERS)
    print(f"  OK Индекс построен ({len(teacher_index)} контактов)")

    # Собираем уникальные статусы
    all_status_columns = set(nethunt_tracking.NETHUNT_STATUS_MAPPING.values())
    for record in MOCK_TEACHERS:
        status_name = nethunt_tracking.extract_status_from_record(record)
        if status_name:
            column_name = nethunt_tracking.map_nethunt_status_to_column(status_name)
            all_status_columns.add(column_name)

    # Трекинг по каждой кампании
    print(f"\n[2/3] Трекинг лидов по статусам...")

    enriched_campaigns = {}
    for campaign_id, campaign_data in campaigns_data.items():
        funnel_stats = nethunt_tracking.track_campaign_leads(
            campaign_data["leads"],
            teacher_index,
            all_status_columns
        )

        enriched_campaigns[campaign_id] = {
            "campaign_id": campaign_id,
            "campaign_name": campaign_data["campaign_name"],
            "leads_count": len(campaign_data["leads"]),
            "funnel_stats": funnel_stats
        }

        print(f"\n  Кампания: {campaign_data['campaign_name']}")
        print(f"    Лидов: {len(campaign_data['leads'])}")
        for status, count in funnel_stats.items():
            if count > 0 and status != "Кількість лідів":
                print(f"    {status}: {count}")

    # Вычисляем метрики
    print(f"\n[3/3] Вычисление метрик...")

    for campaign in enriched_campaigns.values():
        funnel = campaign["funnel_stats"]
        conv = nethunt_tracking.calculate_conversion_rate(funnel)
        qual = nethunt_tracking.calculate_qualified_percentage(funnel)
        interview = nethunt_tracking.calculate_interview_conversion(funnel)

        print(f"\n  {campaign['campaign_name']}:")
        print(f"    % квалифицированных: {qual}%")
        print(f"    % конверсия в найм: {conv}%")
        print(f"    % собеседование->найм: {interview}%")

    print_separator("ТЕСТ УЧИТЕЛЕЙ ЗАВЕРШЕН", "=")


def main():
    """Запуск всех mock тестов."""

    print_separator("DEMO: ТРЕКИНГ ЛИДОВ С МОКОВЫМИ ДАННЫМИ", "#")
    print(f"Дата запуска: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    print("Этот тест демонстрирует работу модулей трекинга без необходимости")
    print("в валидных Meta API токенах, используя реалистичные моковые данные.")

    # Тест 1: Студенты
    test_students_tracking()

    print("\n" + "-" * 80)

    # Тест 2: Учителя
    test_teachers_tracking()

    print_separator("ВСЕ ТЕСТЫ ЗАВЕРШЕНЫ УСПЕШНО", "#")
    print("\nСледующий шаг: Обновить Meta API токены для тестирования на реальных данных")
    print("См. docs/META_TOKEN_REFRESH.md для инструкций")


if __name__ == "__main__":
    main()
