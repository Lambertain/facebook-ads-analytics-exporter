"""
Показать 10 архивных лидов с полной информацией о доступных полях.
"""
import os
import sys
import json
import requests
from pathlib import Path
from dotenv import load_dotenv

# Загрузить переменные окружения
load_dotenv()

# Добавить app директорию в Python path
app_dir = Path(__file__).parent / "app"
sys.path.insert(0, str(app_dir))

from connectors.crm import alfacrm_auth_get_token


def show_archive_leads_details():
    """
    Показать 10 архивных лидов с подробной информацией.
    """

    print("\n" + "="*80)
    print("АРХИВНЫЕ ЛИДЫ ИЗ АЛЬФА СРМ - ДЕТАЛЬНАЯ ИНФОРМАЦИЯ")
    print("="*80)

    # Получить токен
    print("\n[1/2] Получение архивных лидов...")
    try:
        token = alfacrm_auth_get_token()
        base_url = os.getenv("ALFACRM_BASE_URL").rstrip('/')
        company_id = int(os.getenv("ALFACRM_COMPANY_ID"))

        url = f"{base_url}/v2api/customer/index"
        payload = {
            "branch_ids": [company_id],
            "page": 1,
            "page_size": 10,  # Получаем только 10 лидов
            "lead_status_id": 39  # Архивные лиды
        }

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

        print(f"  ✓ Получено: {len(items)} лидов")
        print(f"  ✓ Всего архивных в системе: {total}")

    except Exception as e:
        print(f"  ✗ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return

    # Показать детальную информацию о каждом лиде
    print("\n[2/2] Детальная информация о лидах:")
    print("="*80)

    for i, lead in enumerate(items, 1):
        print(f"\n{'='*80}")
        print(f"АРХИВНЫЙ ЛИД #{i}")
        print(f"{'='*80}")

        # Основная информация
        print(f"\n📋 ОСНОВНАЯ ИНФОРМАЦИЯ:")
        print(f"  ID: {lead.get('id')}")
        print(f"  Имя: {lead.get('name')}")
        print(f"  Дата создания: {lead.get('created_at')}")
        print(f"  Дата обновления: {lead.get('updated_at')}")

        # Статусы
        print(f"\n📊 СТАТУСЫ:")
        print(f"  lead_status_id: {lead.get('lead_status_id')}")
        print(f"  study_status_id: {lead.get('study_status_id')}")
        print(f"  is_study: {lead.get('is_study')}")
        print(f"  color: {lead.get('color')}")

        # Контакты
        print(f"\n📞 КОНТАКТНАЯ ИНФОРМАЦИЯ:")
        phones = lead.get('phone', [])
        emails = lead.get('email', [])
        print(f"  Телефоны ({len(phones)}): {phones}")
        print(f"  Email ({len(emails)}): {emails}")
        print(f"  Адрес: {lead.get('addr', 'N/A')}")

        # Custom поля
        print(f"\n🔧 CUSTOM ПОЛЯ (связанные с кампаниями):")
        custom_fields = {k: v for k, v in lead.items() if k.startswith('custom_')}

        # Важные custom поля
        important_custom = [
            'custom_ads_comp',
            'custom_id_srm',
            'custom_gorodstvaniya',
            'custom_age_',
            'custom_email',
            'custom_yazik',
            'custom_urovenvladenwoo',
            'custom_schedule',
            'custom_try_lessons'
        ]

        for field in important_custom:
            if field in custom_fields:
                value = custom_fields[field]
                # Обрезаем длинные значения
                if isinstance(value, str) and len(value) > 60:
                    value = value[:60] + "..."
                print(f"  {field}: {value}")

        # Остальные custom поля
        other_custom = {k: v for k, v in custom_fields.items() if k not in important_custom}
        if other_custom:
            print(f"\n  Другие custom поля ({len(other_custom)}):")
            for k, v in list(other_custom.items())[:3]:
                if isinstance(v, str) and len(v) > 40:
                    v = v[:40] + "..."
                print(f"    {k}: {v}")
            if len(other_custom) > 3:
                print(f"    ... еще {len(other_custom) - 3} полей")

        # Финансовая информация
        print(f"\n💰 ФИНАНСЫ:")
        print(f"  balance: {lead.get('balance', 0)}")
        print(f"  balance_base: {lead.get('balance_base', 0)}")
        print(f"  balance_bonus: {lead.get('balance_bonus', 0)}")
        print(f"  paid_count: {lead.get('paid_count', 0)}")
        print(f"  paid_lesson_count: {lead.get('paid_lesson_count', 0)}")

        # Назначения
        print(f"\n👤 НАЗНАЧЕНИЯ:")
        print(f"  assigned_id: {lead.get('assigned_id')}")
        print(f"  branch_ids: {lead.get('branch_ids', [])}")
        print(f"  company_id: {lead.get('company_id')}")

        # Дополнительная информация
        print(f"\n📝 ДОПОЛНИТЕЛЬНО:")
        print(f"  Дата рождения: {lead.get('b_date', 'N/A')}")
        print(f"  Пол: {lead.get('sex', 'N/A')}")
        print(f"  Barcode: {lead.get('barcode', 'N/A')}")
        print(f"  Комментарий: {lead.get('comment', 'N/A')[:100]}...")

        # Количество уроков
        print(f"\n📚 УРОКИ:")
        print(f"  legal_type: {lead.get('legal_type')}")
        print(f"  Количество записей: {lead.get('paid_count', 0)}")

    # Итоговая статистика по всем полям
    print(f"\n{'='*80}")
    print("СТАТИСТИКА ПО ДОСТУПНЫМ ПОЛЯМ")
    print(f"{'='*80}")

    # Собираем все уникальные ключи
    all_keys = set()
    for lead in items:
        all_keys.update(lead.keys())

    print(f"\nВсего уникальных полей: {len(all_keys)}")
    print(f"\nПолный список полей:")

    # Группируем поля
    custom_keys = sorted([k for k in all_keys if k.startswith('custom_')])
    standard_keys = sorted([k for k in all_keys if not k.startswith('custom_')])

    print(f"\n1. Стандартные поля ({len(standard_keys)}):")
    for i in range(0, len(standard_keys), 5):
        print(f"   {', '.join(standard_keys[i:i+5])}")

    print(f"\n2. Custom поля ({len(custom_keys)}):")
    for i in range(0, len(custom_keys), 3):
        print(f"   {', '.join(custom_keys[i:i+3])}")

    # Проверяем наличие важных полей для связи с Facebook
    print(f"\n{'='*80}")
    print("АНАЛИЗ СВЯЗИ С FACEBOOK КАМПАНИЯМИ")
    print(f"{'='*80}")

    # Проверяем custom_ads_comp
    ads_comp_values = [lead.get('custom_ads_comp') for lead in items if lead.get('custom_ads_comp')]
    print(f"\nПоле custom_ads_comp (название кампании):")
    print(f"  Заполнено у {len(ads_comp_values)} из {len(items)} лидов")
    if ads_comp_values:
        print(f"\n  Примеры значений:")
        for val in ads_comp_values[:5]:
            if len(val) > 70:
                val = val[:70] + "..."
            print(f"    - {val}")

    # Проверяем custom_id_srm
    srm_ids = [lead.get('custom_id_srm') for lead in items if lead.get('custom_id_srm')]
    print(f"\nПоле custom_id_srm (ID из Facebook):")
    print(f"  Заполнено у {len(srm_ids)} из {len(items)} лидов")
    if srm_ids:
        print(f"  Примеры: {srm_ids[:3]}")

    print(f"\n{'='*80}")
    print("ВЫВОД:")
    print(f"{'='*80}")
    print(f"""
✅ ПОЛУЧАЕМ ПОЛНУЮ ИНФОРМАЦИЮ ОБ АРХИВНЫХ ЛИДАХ:
  • Основные данные (ID, имя, даты)
  • Контакты (телефоны, email)
  • Статусы (lead_status_id, study_status_id)
  • Связь с кампаниями Facebook (custom_ads_comp, custom_id_srm)
  • Финансовую информацию (балансы, оплаты)
  • Custom поля (язык, уровень, город, возраст и т.д.)

🔗 МОЖЕМ СВЯЗАТЬ С FACEBOOK КАМПАНИЯМИ:
  • custom_ads_comp содержит название кампании из Facebook
  • custom_id_srm содержит ID лида из Facebook
  • Это позволяет отслеживать путь лида от Facebook до архива

📊 ВСЕГО ПОЛЕЙ: {len(all_keys)}
  • Стандартных: {len(standard_keys)}
  • Custom: {len(custom_keys)}
    """)


if __name__ == "__main__":
    show_archive_leads_details()
