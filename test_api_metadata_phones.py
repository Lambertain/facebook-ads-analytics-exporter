"""
Тестовий скрипт для перевірки /api/meta-data endpoint
з новими полями column_metadata та lead_phones.
"""
import asyncio
import sys
import os
from datetime import datetime, timedelta

# Додаємо шлях до app
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from dotenv import load_dotenv
load_dotenv()

async def test_meta_data_api():
    """Тестує /api/meta-data endpoint з реальними даними."""
    from main import get_meta_data
    from fastapi import Request

    print("\n" + "="*80)
    print("🧪 ТЕСТУВАННЯ /api/meta-data ENDPOINT")
    print("="*80)

    # Визначаємо період для тестування (останні 7 днів)
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

    print(f"\n📅 Період тестування: {start_date} - {end_date}")
    print(f"🔑 META_PAGE_ID: {os.getenv('META_PAGE_ID')}")
    print(f"🔑 NETHUNT_FOLDER_ID: {os.getenv('NETHUNT_FOLDER_ID')}")
    print(f"🔑 ALFACRM_COMPANY_ID: {os.getenv('ALFACRM_COMPANY_ID')}")

    # Створюємо фейковий Request об'єкт
    class FakeRequest:
        def __init__(self):
            self.client = type('obj', (object,), {'host': '127.0.0.1'})()

    request = FakeRequest()

    try:
        print("\n⏳ Викликаю API endpoint...")
        result = await get_meta_data(request, start_date=start_date, end_date=end_date)

        if isinstance(result, dict):
            print("\n✅ API повернув успішну відповідь")

            # Перевірка основних секцій
            print("\n" + "-"*80)
            print("📊 СТРУКТУРА ВІДПОВІДІ:")
            print("-"*80)

            for key in result.keys():
                if key in ["ads", "students", "teachers"]:
                    count = len(result[key]) if isinstance(result[key], list) else 0
                    print(f"  • {key}: {count} записів")
                elif key == "column_metadata":
                    print(f"  • {key}: {len(result[key])} категорій")
                elif key == "lead_phones":
                    print(f"  • {key}: присутній")
                else:
                    print(f"  • {key}: {result[key]}")

            # Детальна перевірка column_metadata
            if "column_metadata" in result:
                print("\n" + "-"*80)
                print("🎨 COLUMN METADATA (КОЛЬОРОВА МАРКІРОВКА):")
                print("-"*80)

                metadata = result["column_metadata"]

                for data_type in ["students", "teachers", "ads"]:
                    if data_type in metadata:
                        type_metadata = metadata[data_type]

                        # Підраховуємо по категоріях
                        meta_count = sum(1 for v in type_metadata.values() if v == "meta")
                        crm_count = sum(1 for v in type_metadata.values() if v == "crm")
                        formula_count = sum(1 for v in type_metadata.values() if v == "formula")

                        print(f"\n  {data_type.upper()}:")
                        print(f"    🔵 Meta (голубі): {meta_count} полів")
                        print(f"    🔴 CRM (рожеві): {crm_count} полів")
                        print(f"    🟢 Formula (зелені): {formula_count} полів")
                        print(f"    📊 Всього: {len(type_metadata)} полів")

                        # Показуємо приклади
                        print(f"\n    Приклади полів:")
                        shown = 0
                        for field, category in type_metadata.items():
                            if shown < 3:
                                color_icon = "🔵" if category == "meta" else "🔴" if category == "crm" else "🟢"
                                print(f"      {color_icon} {field}: {category}")
                                shown += 1

            # Детальна перевірка lead_phones
            if "lead_phones" in result:
                print("\n" + "-"*80)
                print("📞 LEAD PHONES (ТЕЛЕФОНИ З СТАТУСАМИ):")
                print("-"*80)

                lead_phones = result["lead_phones"]

                for data_type in ["students", "teachers"]:
                    if data_type in lead_phones:
                        type_phones = lead_phones[data_type]
                        print(f"\n  {data_type.upper()}:")
                        print(f"    📋 Кампаній з даними: {len(type_phones)}")

                        if type_phones:
                            # Показуємо перші 2 кампанії
                            for idx, (campaign_id, status_data) in enumerate(list(type_phones.items())[:2]):
                                print(f"\n    Кампанія {idx+1} ({campaign_id}):")
                                print(f"      Статусів: {len(status_data)}")

                                # Показуємо перші 2 статуси
                                for status_name, phones in list(status_data.items())[:2]:
                                    print(f"\n        Статус: {status_name}")
                                    print(f"        Телефонів: {len(phones)}")

                                    # Підраховуємо passed/current
                                    passed = sum(1 for p in phones if p.get("status") == "passed")
                                    current = sum(1 for p in phones if p.get("status") == "current")
                                    print(f"          🔴 Passed: {passed}")
                                    print(f"          🟢 Current: {current}")

                                    # Показуємо перший телефон як приклад
                                    if phones:
                                        example = phones[0]
                                        status_icon = "🔴" if example.get("status") == "passed" else "🟢"
                                        print(f"          Приклад: {status_icon} {example.get('phone', 'N/A')} ({example.get('status')})")

            # Загальна статистика
            print("\n" + "="*80)
            print("✅ ТЕСТ ЗАВЕРШЕНО УСПІШНО")
            print("="*80)

            return True

        else:
            print("\n❌ API повернув не словник")
            print(f"Тип відповіді: {type(result)}")
            print(f"Відповідь: {result}")
            return False

    except Exception as e:
        print(f"\n❌ ПОМИЛКА ПІД ЧАС ТЕСТУВАННЯ:")
        print(f"  {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n🚀 Запуск тестів...")
    success = asyncio.run(test_meta_data_api())

    if success:
        print("\n🎉 Всі тести пройшли успішно!")
        sys.exit(0)
    else:
        print("\n💥 Тести провалились!")
        sys.exit(1)
