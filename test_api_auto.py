"""
Автоматичний тестовий скрипт для перевірки /api/meta-data endpoint через HTTP.
"""
import requests
import json
import sys
from datetime import datetime, timedelta

# Визначаємо період для тестування (останні 3 дні для швидшого тесту)
end_date = datetime.now().strftime("%Y-%m-%d")
start_date = (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")

print("\n" + "="*80)
print("🧪 ТЕСТУВАННЯ /api/meta-data ENDPOINT")
print("="*80)
print(f"\n📅 Період: {start_date} - {end_date}")

# URL endpoint
endpoint = "http://127.0.0.1:8000/api/meta-data"

try:
    print(f"\n⏳ Викликаю API... (timeout 120s)")

    response = requests.get(
        endpoint,
        params={"start_date": start_date, "end_date": end_date},
        timeout=120
    )

    print(f"📡 HTTP Status: {response.status_code}")

    if response.status_code == 200:
        result = response.json()

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
                students_campaigns = len(result[key].get("students", {}))
                teachers_campaigns = len(result[key].get("teachers", {}))
                print(f"  • {key}: students={students_campaigns} campaigns, teachers={teachers_campaigns} campaigns")
            else:
                print(f"  • {key}: {result[key]}")

        # column_metadata
        if "column_metadata" in result:
            print("\n" + "-"*80)
            print("🎨 COLUMN METADATA:")
            print("-"*80)

            for data_type in ["students", "teachers", "ads"]:
                if data_type in result["column_metadata"]:
                    meta = result["column_metadata"][data_type]
                    meta_c = sum(1 for v in meta.values() if v == "meta")
                    crm_c = sum(1 for v in meta.values() if v == "crm")
                    formula_c = sum(1 for v in meta.values() if v == "formula")

                    print(f"\n  {data_type.upper()}:")
                    print(f"    🔵 Meta: {meta_c} | 🔴 CRM: {crm_c} | 🟢 Formula: {formula_c} | Total: {len(meta)}")

        # lead_phones
        if "lead_phones" in result:
            print("\n" + "-"*80)
            print("📞 LEAD PHONES:")
            print("-"*80)

            for data_type in ["students", "teachers"]:
                if data_type in result["lead_phones"] and result["lead_phones"][data_type]:
                    phones_data = result["lead_phones"][data_type]
                    print(f"\n  {data_type.upper()}: {len(phones_data)} campaigns")

                    # Показуємо одну кампанію як приклад
                    if phones_data:
                        campaign_id, status_data = list(phones_data.items())[0]
                        print(f"    Sample campaign ({campaign_id}): {len(status_data)} statuses")

                        # Показуємо один статус
                        if status_data:
                            status_name, phones = list(status_data.items())[0]
                            passed = sum(1 for p in phones if p.get("status") == "passed")
                            current = sum(1 for p in phones if p.get("status") == "current")
                            print(f"      Sample status '{status_name}': {len(phones)} phones (🔴{passed} passed, 🟢{current} current)")

        # Зберігаємо результат
        with open("test_api_response.json", "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Результат збережено: test_api_response.json")

        print("\n" + "="*80)
        print("✅ ТЕСТ ЗАВЕРШЕНО УСПІШНО")
        print("="*80)
        sys.exit(0)
    else:
        print(f"❌ Помилка: {response.status_code}")
        print(response.text[:500])
        sys.exit(1)

except Exception as e:
    print(f"\n❌ ПОМИЛКА: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
