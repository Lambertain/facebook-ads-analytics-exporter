"""
Тестовий скрипт для перевірки /api/meta-data endpoint через HTTP.
Запускає сервер та робить реальний HTTP запит.
"""
import requests
import json
import subprocess
import time
import sys
from datetime import datetime, timedelta

def test_api_with_http():
    """Тестує API через HTTP запит."""

    print("\n" + "="*80)
    print("🧪 ТЕСТУВАННЯ /api/meta-data ENDPOINT (HTTP)")
    print("="*80)

    # Визначаємо період для тестування (останні 7 днів)
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

    print(f"\n📅 Період тестування: {start_date} - {end_date}")

    # URL endpoint
    base_url = "http://127.0.0.1:8000"
    endpoint = f"{base_url}/api/meta-data"

    print(f"\n🌐 Endpoint: {endpoint}")
    print(f"   Параметри: start_date={start_date}, end_date={end_date}")

    try:
        print("\n⏳ Викликаю API endpoint...")

        response = requests.get(
            endpoint,
            params={
                "start_date": start_date,
                "end_date": end_date
            },
            timeout=120  # 2 хвилини timeout
        )

        print(f"\n📡 HTTP Status: {response.status_code}")

        if response.status_code == 200:
            print("✅ API повернув успішну відповідь (200 OK)")

            result = response.json()

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
                            if shown < 5:
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
                    if data_type in lead_phones and lead_phones[data_type]:
                        type_phones = lead_phones[data_type]
                        print(f"\n  {data_type.upper()}:")
                        print(f"    📋 Кампаній з даними: {len(type_phones)}")

                        if type_phones:
                            # Показуємо перші 2 кампанії
                            for idx, (campaign_id, status_data) in enumerate(list(type_phones.items())[:2]):
                                print(f"\n    Кампанія {idx+1} ({campaign_id}):")
                                print(f"      Статусів: {len(status_data)}")

                                # Показуємо перші 3 статуси
                                for status_name, phones in list(status_data.items())[:3]:
                                    print(f"\n        📊 Статус: {status_name}")
                                    print(f"           Телефонів: {len(phones)}")

                                    # Підраховуємо passed/current
                                    passed = sum(1 for p in phones if p.get("status") == "passed")
                                    current = sum(1 for p in phones if p.get("status") == "current")
                                    print(f"           🔴 Passed: {passed}")
                                    print(f"           🟢 Current: {current}")

                                    # Показуємо перші 2 телефони як приклад
                                    if phones:
                                        for i, example in enumerate(phones[:2]):
                                            status_icon = "🔴" if example.get("status") == "passed" else "🟢"
                                            phone = example.get('phone', 'N/A')
                                            # Приховуємо частину телефону
                                            if len(phone) > 6:
                                                phone = phone[:3] + "****" + phone[-3:]
                                            print(f"           {i+1}. {status_icon} {phone} ({example.get('status')})")
                    else:
                        print(f"\n  {data_type.upper()}: немає даних")

            # Зберігаємо повну відповідь в файл
            output_file = "test_api_response.json"
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print(f"\n💾 Повну відповідь збережено в: {output_file}")

            # Загальна статистика
            print("\n" + "="*80)
            print("✅ ТЕСТ ЗАВЕРШЕНО УСПІШНО")
            print("="*80)

            return True

        else:
            print(f"❌ API повернув помилку: {response.status_code}")
            print(f"Відповідь: {response.text[:500]}")
            return False

    except requests.exceptions.ConnectionError:
        print("\n❌ ПОМИЛКА: Не вдалось підключитись до сервера")
        print("💡 Переконайтесь що сервер запущено:")
        print("   cd D:\\Automation\\Development\\projects\\ecademy")
        print("   uvicorn app.main:app --reload")
        return False
    except requests.exceptions.Timeout:
        print("\n❌ ПОМИЛКА: Timeout - запит зайняв більше 2 хвилин")
        return False
    except Exception as e:
        print(f"\n❌ ПОМИЛКА ПІД ЧАС ТЕСТУВАННЯ:")
        print(f"  {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n🚀 Запуск тестів...")
    print("\n⚠️  Переконайтесь що сервер запущено на http://127.0.0.1:8000")
    print("    Якщо ні, запустіть: uvicorn app.main:app --reload")

    input("\n   Натисніть Enter для продовження...")

    success = test_api_with_http()

    if success:
        print("\n🎉 Всі тести пройшли успішно!")
        sys.exit(0)
    else:
        print("\n💥 Тести провалились!")
        sys.exit(1)
