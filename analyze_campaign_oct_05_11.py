"""Анализ данных кампании Shkolnik_EVR_10.09_newform за период 2025-10-05 - 2025-10-11."""
import asyncio
from datetime import datetime
from services.meta_leads import get_student_campaigns_with_leads
from services.alfacrm_tracking import track_campaign_leads, build_student_index
from connectors.crm import alfacrm_get_all_students


async def main():
    print("=" * 80)
    print("АНАЛИЗ КАМПАНИИ: Shkolnik_EVR_10.09_newform")
    print("Период: 2025-10-05 - 2025-10-11")
    print("=" * 80)

    # Параметры периода
    start_date = "2025-10-05"
    end_date = "2025-10-11"

    print("\n[1/4] Получение лидов Facebook...")
    campaigns = await get_student_campaigns_with_leads(start_date, end_date)

    # Находим кампанию Shkolnik_EVR_10.09_newform
    target_campaign = None
    for campaign in campaigns:
        if "Shkolnik_EVR_10.09_newform" in campaign["campaign_name"]:
            target_campaign = campaign
            break

    if not target_campaign:
        print("  [ERROR] Кампания Shkolnik_EVR_10.09_newform не найдена!")
        print(f"  Доступные кампании: {[c['campaign_name'] for c in campaigns[:5]]}")
        return

    print(f"  [OK] Найдена кампания: {target_campaign['campaign_name']}")
    print(f"  [OK] Лидов в кампании: {len(target_campaign['leads'])}")

    # Показываем первые 3 лида
    print("\n  Примеры лидов:")
    for i, lead in enumerate(target_campaign['leads'][:3], 1):
        phone = email = None
        for field in lead.get('field_data', []):
            if field['name'] == 'phone_number':
                phone = field['values'][0]
            elif field['name'] == 'email':
                email = field['values'][0]
        print(f"    {i}. Phone: {phone}, Email: {email}")

    print("\n[2/4] Загрузка студентов из AlfaCRM...")
    students = await alfacrm_get_all_students()
    print(f"  [OK] Загружено студентов: {len(students)}")

    print("\n[3/4] Построение индекса студентов...")
    student_index = build_student_index(students)
    print(f"  [OK] Индекс содержит {len(student_index)} контактов")

    print("\n[4/4] Трекинг кампании...")
    status_counts = track_campaign_leads(target_campaign['leads'], student_index)

    print("\n" + "=" * 80)
    print("РЕЗУЛЬТАТЫ ТРЕКИНГА:")
    print("=" * 80)

    # Выводим все статусы с ненулевыми значениями
    print("\nОсновные метрики:")
    key_metrics = [
        "Кількість лідів",
        "Не розібраний",
        "Недодзвон",
        "Вст контакт невідомо",
        "Вст контакт зацікавлений",
        "Призначено пробне",
        "Проведено пробне",
        "Чекаємо оплату",
        "Отримана оплата",
        "Отримана оплата (вторинна)",
    ]

    for metric in key_metrics:
        value = status_counts.get(metric, 0)
        if value > 0:
            print(f"  {metric}: {value}")

    print("\nВсе статусы с ненулевыми значениями:")
    for status_name, count in sorted(status_counts.items()):
        if count > 0:
            print(f"  {status_name}: {count}")

    print("\n" + "=" * 80)
    print("ПРОБЛЕМЫ:")
    print("=" * 80)

    total_leads = status_counts.get("Кількість лідів", 0)
    not_processed = status_counts.get("Не розібраний", 0)
    purchased = status_counts.get("Отримана оплата", 0)
    purchased_sec = status_counts.get("Отримана оплата (вторинна)", 0)
    total_purchased = purchased + purchased_sec

    if total_leads > 0:
        print(f"\n  Всего лидов: {total_leads}")
        print(f"  'Не розібраний': {not_processed} ({not_processed/total_leads*100:.1f}%)")
        print(f"  Купили (всего): {total_purchased}")

        if not_processed == total_leads - 1:
            print("\n  [ПРОБЛЕМА] Почти все лиды в статусе 'Не розібраний'!")
            print("  [ПРИЧИНА] Возможно, баг в lines 300-303 alfacrm_tracking.py")
            print("             'not found in CRM' лиды добавляются к status_13")

if __name__ == "__main__":
    asyncio.run(main())
