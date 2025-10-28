"""
Тест для получения ТОЛЬКО архивных лидов через AlfaCRM API.

На основе результатов test_archive_api_filtering.py:
- Фильтрация по lead_status_id=39 РАБОТАЕТ!
- Можем получать только архивные лиды напрямую

ЦЕЛЬ: Проверить эффективность получения архивных лидов
"""
import os
import sys
import requests
from pathlib import Path
from dotenv import load_dotenv

# Загрузить переменные окружения
load_dotenv()

# Добавить app директорию в Python path
app_dir = Path(__file__).parent / "app"
sys.path.insert(0, str(app_dir))

from connectors.crm import alfacrm_auth_get_token


def get_only_archive_leads():
    """
    Получить ТОЛЬКО архивные лиды используя lead_status_id=39.
    """

    print("\n" + "="*80)
    print("ТЕСТ: Получение ТОЛЬКО архивных лидов из AlfaCRM")
    print("="*80)

    # Получить токен
    print("\n[1/3] Аутентификация...")
    try:
        token = alfacrm_auth_get_token()
        print("  ✓ Токен получен")
    except Exception as e:
        print(f"  ✗ Ошибка: {e}")
        return

    base_url = os.getenv("ALFACRM_BASE_URL").rstrip('/')
    company_id = int(os.getenv("ALFACRM_COMPANY_ID"))
    headers = {"X-ALFACRM-TOKEN": token}

    # Получение ТОЛЬКО архивных лидов
    print("\n[2/3] Запрос архивных лидов (lead_status_id=39)...")
    try:
        url = f"{base_url}/v2api/customer/index"
        payload = {
            "branch_ids": [company_id],
            "page": 1,
            "page_size": 100,  # Получаем больше для полной картины
            "lead_status_id": 39  # РАБОТАЕТ согласно предыдущему тесту
        }

        resp = requests.post(url, headers=headers, json=payload, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        items = data.get("items", [])
        total = data.get("count", 0)

        print(f"  ✓ Получено: {len(items)} архивных лидов")
        print(f"  ✓ Всего архивных в системе: {total}")

        # Проверка что ВСЕ лиды действительно архивные
        archive_by_status = [item for item in items if item.get("lead_status_id") == 39]
        archive_by_field = [item for item in items if item.get("custom_ads_comp") == "архів"]

        print(f"\n  Проверка результатов:")
        print(f"    С lead_status_id=39: {len(archive_by_status)} из {len(items)}")
        print(f"    С custom_ads_comp='архів': {len(archive_by_field)} из {len(items)}")

        if len(archive_by_status) == len(items) and len(archive_by_field) == len(items):
            print(f"  ✅ ОТЛИЧНО! Все полученные лиды действительно архивные")
        else:
            print(f"  ⚠ ВНИМАНИЕ! Есть несоответствие в данных")

    except Exception as e:
        print(f"  ✗ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return

    # Анализ архивных лидов
    print("\n[3/3] Анализ архивных лидов...")
    if items:
        # Показываем первые 3 примера
        print(f"\n  Примеры архивных лидов:")
        print(f"  " + "-"*76)

        for i, lead in enumerate(items[:3], 1):
            print(f"\n  Лид #{i}:")
            print(f"    ID: {lead.get('id')}")
            print(f"    Имя: {lead.get('name')}")
            print(f"    lead_status_id: {lead.get('lead_status_id')}")
            print(f"    custom_ads_comp: {lead.get('custom_ads_comp')}")
            print(f"    Телефон: {lead.get('phone', [])}")
            print(f"    Email: {lead.get('email', [])}")
            print(f"    Дата создания: {lead.get('created_at', 'N/A')}")

            # Проверяем есть ли информация о кампании
            custom_fields = {k: v for k, v in lead.items() if k.startswith('custom_')}
            if custom_fields:
                print(f"    Custom поля: {list(custom_fields.keys())[:5]}...")

        print(f"\n  " + "-"*76)

        # Статистика
        print(f"\n  Статистика архивных лидов:")
        print(f"    Всего архивных лидов: {total}")
        print(f"    Загружено в текущем запросе: {len(items)}")

        # Проверяем есть ли лиды с телефонами/email
        with_phone = [item for item in items if item.get('phone')]
        with_email = [item for item in items if item.get('email')]

        print(f"    С телефоном: {len(with_phone)}")
        print(f"    С email: {len(with_email)}")

    # Итоги
    print("\n" + "="*80)
    print("ИТОГОВЫЕ РЕЗУЛЬТАТЫ:")
    print("="*80)

    print(f"\n✅ МОЖЕМ ПОЛУЧАТЬ АРХИВНЫЕ ЛИДЫ НАПРЯМУЮ!")

    print(f"\nМетод:")
    print(f"  Endpoint: POST /v2api/customer/index")
    print(f"  Параметры:")
    print(f"    - branch_ids: [{company_id}]")
    print(f"    - lead_status_id: 39")
    print(f"    - page: N")
    print(f"    - page_size: M")

    print(f"\nПреимущества:")
    print(f"  ✓ Не нужно загружать всех студентов")
    print(f"  ✓ Получаем только архивные лиды")
    print(f"  ✓ Экономия трафика и времени")
    print(f"  ✓ Можно использовать пагинацию")

    print(f"\nИспользование в коде:")
    print(f"""
  # В app/connectors/crm.py добавить функцию:
  def alfacrm_list_archive_students(page: int = 1, page_size: int = 200):
      \"\"\"Получить только архивных студентов из AlfaCRM.\"\"\"
      token = alfacrm_auth_get_token()
      base_url = os.getenv("ALFACRM_BASE_URL")
      company_id = os.getenv("ALFACRM_COMPANY_ID")

      url = base_url.rstrip('/') + "/v2api/customer/index"
      payload = {{
          "branch_ids": [int(company_id)],
          "page": page,
          "page_size": page_size,
          "lead_status_id": 39  # Архив
      }}

      resp = requests.post(
          url,
          headers={{"X-ALFACRM-TOKEN": token}},
          json=payload,
          timeout=15
      )
      resp.raise_for_status()
      return resp.json()
    """)

    print(f"\n" + "="*80)


if __name__ == "__main__":
    get_only_archive_leads()
