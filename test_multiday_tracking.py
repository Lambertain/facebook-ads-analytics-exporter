"""
Тест полного flow Meta Leads + AlfaCRM + NetHunt на периоде в несколько дней.
"""
import os
import sys
import asyncio
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Загрузить переменные окружения
load_dotenv()

# Добавить app в путь
sys.path.insert(0, 'app')

from services import meta_leads
from services import alfacrm_tracking
from services import nethunt_tracking


def print_separator(title: str, char: str = "="):
    """Печать разделителя с заголовком."""
    width = 80
    print(f"\n{char * width}")
    print(f"{title:^{width}}")
    print(f"{char * width}\n")


async def test_multiday_students():
    """Тест flow студентов на периоде в несколько дней."""

    print_separator("ТЕСТ СТУДЕНТОВ: Meta Leads + AlfaCRM (5 дней)", "=")

    # Параметры
    page_id = os.getenv("FACEBOOK_PAGE_ID")
    page_token = os.getenv("META_PAGE_ACCESS_TOKEN")

    # Период: последние 5 дней
    end_date = datetime.now()
    start_date = end_date - timedelta(days=5)

    start_str = start_date.strftime("%Y-%m-%d")
    end_str = end_date.strftime("%Y-%m-%d")

    print(f"Параметры:")
    print(f"  Page ID: {page_id}")
    print(f"  Период: {start_str} - {end_str} (5 дней)")

    # 1. Получить лиды из Meta API
    print(f"\n[1/3] Получение лидов из Meta API...")

    try:
        campaigns_data = await meta_leads.get_leads_for_period(
            page_id=page_id,
            page_token=page_token,
            start_date=start_str,
            end_date=end_str
        )

        total_leads = sum(len(c["leads"]) for c in campaigns_data.values())
        print(f"  OK Получено {len(campaigns_data)} кампаний, {total_leads} лидов")

        # Показать топ-3 кампании по количеству лидов
        if campaigns_data:
            sorted_campaigns = sorted(
                campaigns_data.values(),
                key=lambda x: len(x["leads"]),
                reverse=True
            )[:3]

            print(f"\n  Топ-3 кампании по лидам:")
            for i, camp in enumerate(sorted_campaigns, 1):
                leads_count = len(camp["leads"])
                name = camp["campaign_name"][:50]
                print(f"    {i}. {name}... ({leads_count} лидов)")

        # Фильтруем только кампании студентов (название содержит "Student")
        student_campaigns = {
            cid: cdata for cid, cdata in campaigns_data.items()
            if "student" in cdata.get("campaign_name", "").lower()
        }

        if not student_campaigns:
            print("\n  ВНИМАНИЕ: Не найдено кампаний студентов (с 'Student' в названии)")
            print("  Используем все кампании для демонстрации")
            student_campaigns = campaigns_data
        else:
            student_leads = sum(len(c["leads"]) for c in student_campaigns.values())
            print(f"\n  Отфильтровано {len(student_campaigns)} кампаний студентов ({student_leads} лидов)")

    except Exception as e:
        print(f"  ERROR: {e}")
        import traceback
        traceback.print_exc()
        return

    # 2. Трекинг через AlfaCRM
    print(f"\n[2/3] Трекинг лидов студентов через AlfaCRM...")

    try:
        enriched_campaigns = await alfacrm_tracking.track_leads_by_campaigns(
            campaigns_data=student_campaigns,
            page_size=500
        )

        print(f"  OK Обработано {len(enriched_campaigns)} кампаний")

        # Показать статистику по всем кампаниям
        total_funnel = {}
        for campaign in enriched_campaigns.values():
            for status, count in campaign["funnel_stats"].items():
                total_funnel[status] = total_funnel.get(status, 0) + count

        print(f"\n  Общая воронка студентов за период:")
        for status_name, count in total_funnel.items():
            if count > 0:
                print(f"    {status_name}: {count}")

    except Exception as e:
        print(f"  ERROR: {e}")
        import traceback
        traceback.print_exc()
        return

    # 3. Вычислить метрики
    print(f"\n[3/3] Вычисление метрик...")

    try:
        total_conversion = alfacrm_tracking.calculate_conversion_rate(total_funnel)
        total_target = alfacrm_tracking.calculate_target_leads_percentage(total_funnel)
        total_trial = alfacrm_tracking.calculate_trial_conversion(total_funnel)

        print(f"\n  Общие метрики за период:")
        print(f"    % целевых лидов: {total_target}%")
        print(f"    % конверсия в продажу: {total_conversion}%")
        print(f"    % конверсия пробный->продажа: {total_trial}%")

        # Детали по топ-3 кампаниям
        top_campaigns = sorted(
            enriched_campaigns.values(),
            key=lambda x: x["leads_count"],
            reverse=True
        )[:3]

        if top_campaigns:
            print(f"\n  Детали по топ-3 кампаниям:")
            for i, campaign in enumerate(top_campaigns, 1):
                funnel = campaign["funnel_stats"]
                conv = alfacrm_tracking.calculate_conversion_rate(funnel)
                target = alfacrm_tracking.calculate_target_leads_percentage(funnel)

                name = campaign["campaign_name"][:60]
                leads = campaign["leads_count"]

                print(f"\n    {i}. {name}...")
                print(f"       Лидов: {leads}")
                print(f"       Целевые: {target}%")
                print(f"       Конверсия: {conv}%")

    except Exception as e:
        print(f"  ERROR: {e}")
        import traceback
        traceback.print_exc()
        return

    print_separator("ТЕСТ СТУДЕНТОВ ЗАВЕРШЕН УСПЕШНО", "=")


async def test_multiday_teachers():
    """Тест flow учителей на периоде в несколько дней."""

    print_separator("ТЕСТ УЧИТЕЛЕЙ: Meta Leads + NetHunt (5 дней)", "=")

    # Параметры
    page_id = os.getenv("FACEBOOK_PAGE_ID")
    page_token = os.getenv("META_PAGE_ACCESS_TOKEN")

    # Период: последние 5 дней
    end_date = datetime.now()
    start_date = end_date - timedelta(days=5)

    start_str = start_date.strftime("%Y-%m-%d")
    end_str = end_date.strftime("%Y-%m-%d")

    print(f"Параметры:")
    print(f"  Page ID: {page_id}")
    print(f"  Период: {start_str} - {end_str} (5 дней)")

    # 1. Получить лиды из Meta API
    print(f"\n[1/3] Получение лидов из Meta API...")

    try:
        campaigns_data = await meta_leads.get_leads_for_period(
            page_id=page_id,
            page_token=page_token,
            start_date=start_str,
            end_date=end_str
        )

        total_leads = sum(len(c["leads"]) for c in campaigns_data.values())
        print(f"  OK Получено {len(campaigns_data)} кампаний, {total_leads} лидов")

        # Фильтруем только кампании учителей (название содержит "Teacher")
        teacher_campaigns = {
            cid: cdata for cid, cdata in campaigns_data.items()
            if "teacher" in cdata.get("campaign_name", "").lower()
        }

        if not teacher_campaigns:
            print("\n  ВНИМАНИЕ: Не найдено кампаний учителей (с 'Teacher' в названии)")
            print("  Тест учителей пропущен")
            return

        teacher_leads = sum(len(c["leads"]) for c in teacher_campaigns.values())
        print(f"\n  Отфильтровано {len(teacher_campaigns)} кампаний учителей ({teacher_leads} лидов)")

    except Exception as e:
        print(f"  ERROR: {e}")
        import traceback
        traceback.print_exc()
        return

    # 2. Трекинг через NetHunt
    print(f"\n[2/3] Трекинг лидов учителей через NetHunt...")

    try:
        # Используем folder_id из .env или первую доступную папку
        enriched_campaigns = await nethunt_tracking.track_leads_by_campaigns(
            campaigns_data=teacher_campaigns,
            folder_id=None  # Автоматически определит из env или первую
        )

        print(f"  OK Обработано {len(enriched_campaigns)} кампаний")

        # Показать статистику по всем кампаниям
        total_funnel = {}
        for campaign in enriched_campaigns.values():
            for status, count in campaign["funnel_stats"].items():
                total_funnel[status] = total_funnel.get(status, 0) + count

        print(f"\n  Общая воронка учителей за период:")
        for status_name, count in total_funnel.items():
            if count > 0:
                print(f"    {status_name}: {count}")

    except Exception as e:
        print(f"  ERROR: {e}")
        import traceback
        traceback.print_exc()
        return

    # 3. Вычислить метрики
    print(f"\n[3/3] Вычисление метрик...")

    try:
        total_conversion = nethunt_tracking.calculate_conversion_rate(total_funnel)
        total_qualified = nethunt_tracking.calculate_qualified_percentage(total_funnel)
        total_interview = nethunt_tracking.calculate_interview_conversion(total_funnel)

        print(f"\n  Общие метрики за период:")
        print(f"    % квалифицированных: {total_qualified}%")
        print(f"    % конверсия в найм: {total_conversion}%")
        print(f"    % конверсия собеседование->найм: {total_interview}%")

        # Детали по кампаниям
        for i, campaign in enumerate(enriched_campaigns.values(), 1):
            funnel = campaign["funnel_stats"]
            conv = nethunt_tracking.calculate_conversion_rate(funnel)
            qual = nethunt_tracking.calculate_qualified_percentage(funnel)

            name = campaign["campaign_name"][:60]
            leads = campaign["leads_count"]

            print(f"\n    {i}. {name}...")
            print(f"       Лидов: {leads}")
            print(f"       Квалифицированные: {qual}%")
            print(f"       Конверсия: {conv}%")

    except Exception as e:
        print(f"  ERROR: {e}")
        import traceback
        traceback.print_exc()
        return

    print_separator("ТЕСТ УЧИТЕЛЕЙ ЗАВЕРШЕН УСПЕШНО", "=")


async def main():
    """Запуск всех тестов."""

    print_separator("ТЕСТЫ НА ПЕРИОДЕ В НЕСКОЛЬКО ДНЕЙ", "#")
    print(f"Дата запуска: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Тест 1: Студенты (Meta + AlfaCRM)
    await test_multiday_students()

    # Пауза между тестами
    print("\n" + "-" * 80)
    await asyncio.sleep(2)

    # Тест 2: Учителя (Meta + NetHunt)
    await test_multiday_teachers()

    print_separator("ВСЕ ТЕСТЫ ЗАВЕРШЕНЫ", "#")


if __name__ == "__main__":
    asyncio.run(main())
