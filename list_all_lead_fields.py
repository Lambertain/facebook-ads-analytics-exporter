"""
Получить список ВСЕХ полей лида из AlfaCRM API
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import requests
import json

load_dotenv()

app_dir = Path(__file__).parent / "app"
sys.path.insert(0, str(app_dir))

from connectors.crm import alfacrm_auth_get_token


def get_lead_fields():
    """Получить все поля из реального лида"""
    print("\n" + "="*80)
    print("ПОЛУЧЕНИЕ ВСЕХ ПОЛЕЙ ЛИДА ИЗ API")
    print("="*80)

    token = alfacrm_auth_get_token()
    base_url = os.getenv("ALFACRM_BASE_URL").rstrip('/')

    # Получаем первого лида
    url = f"{base_url}/v2api/customer/index"
    payload = {
        "page": 1,
        "page_size": 1
    }

    print(f"\nЗапрос: {url}")

    resp = requests.post(
        url,
        headers={"X-ALFACRM-TOKEN": token},
        json=payload,
        timeout=15
    )

    data = resp.json()
    items = data.get("items", [])

    if not items:
        print("Лиды не найдены!")
        return

    lead = items[0]

    print(f"\nПолучен лид ID: {lead.get('id')}")
    print(f"Всего полей в ответе: {len(lead)}")

    # Сохраняем в JSON для анализа
    output_file = Path(__file__).parent / "lead_fields_sample.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(lead, f, ensure_ascii=False, indent=2)

    print(f"\nПолный ответ сохранен в: {output_file}")

    # Разделяем на системные и кастомные
    system_fields = {}
    custom_fields = {}

    for key, value in lead.items():
        if key.startswith("custom_"):
            custom_fields[key] = value
        else:
            system_fields[key] = value

    print(f"\n{'='*80}")
    print(f"СИСТЕМНЫЕ ПОЛЯ (С): {len(system_fields)}")
    print(f"{'='*80}")

    for key in sorted(system_fields.keys()):
        value = system_fields[key]
        value_type = type(value).__name__

        # Показываем примерное значение
        if value is None:
            display_value = "None"
        elif isinstance(value, (list, dict)):
            display_value = f"{value_type} с {len(value)} элементами" if value else "пусто"
        elif isinstance(value, str) and len(value) > 50:
            display_value = value[:47] + "..."
        else:
            display_value = str(value)

        print(f"  {key:30} │ {value_type:10} │ {display_value}")

    print(f"\n{'='*80}")
    print(f"КАСТОМНЫЕ ПОЛЯ (К): {len(custom_fields)}")
    print(f"{'='*80}")

    for key in sorted(custom_fields.keys()):
        value = custom_fields[key]
        value_type = type(value).__name__

        # Показываем примерное значение
        if value is None:
            display_value = "None"
        elif isinstance(value, (list, dict)):
            display_value = f"{value_type} с {len(value)} элементами" if value else "пусто"
        elif isinstance(value, str) and len(value) > 50:
            display_value = value[:47] + "..."
        else:
            display_value = str(value)

        print(f"  {key:30} │ {value_type:10} │ {display_value}")

    print(f"\n{'='*80}")
    print(f"ВСЕГО ПОЛЕЙ: {len(lead)}")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    get_lead_fields()
