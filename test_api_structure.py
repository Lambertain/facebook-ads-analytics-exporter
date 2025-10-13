"""
Аналіз структури відповіді API
"""
import requests
import json

endpoint = "http://127.0.0.1:8000/api/meta-data"
end_date = "2025-10-12"
start_date = "2025-10-09"

print("Викликаю API...\n")

try:
    response = requests.get(
        endpoint,
        params={"start_date": start_date, "end_date": end_date},
        timeout=600
    )

    if response.status_code == 200:
        data = response.json()

        # Виводимо структуру відповіді
        print("=" * 80)
        print("СТРУКТУРА ВІДПОВІДІ:")
        print("=" * 80)
        print(f"\nКлючі верхнього рівня: {list(data.keys())}\n")

        # Якщо є data, подивимося що всередині
        if "data" in data:
            print(f"Ключі в data: {list(data['data'].keys())}\n")

            if "campaigns" in data["data"]:
                campaigns = data["data"]["campaigns"]
                print(f"Кількість кампаній: {len(campaigns)}\n")

                if len(campaigns) > 0:
                    print("Структура першої кампанії:")
                    first = campaigns[0]
                    print(f"Ключі: {list(first.keys())}\n")

                    # Перевіримо student_tracking
                    if "student_tracking" in first:
                        print("student_tracking:")
                        print(json.dumps(first["student_tracking"], indent=2, ensure_ascii=False))

                    # Виведемо деталі декількох кампаній
                    print("\n" + "=" * 80)
                    print("ДЕТАЛЬНА СТАТИСТИКА ПО КАМПАНІЯМ:")
                    print("=" * 80)

                    total_matched = 0
                    total_not_found = 0
                    campaigns_with_matches = 0

                    for campaign in campaigns:
                        if "student_tracking" in campaign:
                            tracking = campaign["student_tracking"]
                            matched = tracking.get("matched", 0)
                            not_found = tracking.get("not_found_in_crm", 0)

                            total_matched += matched
                            total_not_found += not_found

                            if matched > 0:
                                campaigns_with_matches += 1

                    print(f"\n📊 ЗАГАЛЬНА СТАТИСТИКА:")
                    print(f"   Всього кампаній: {len(campaigns)}")
                    print(f"   Кампаній з matched > 0: {campaigns_with_matches}")
                    print(f"   Всього matched контактів: {total_matched}")
                    print(f"   Всього not_found_in_crm: {total_not_found}")

                    if total_matched > 0:
                        print(f"\n✅ УСПІХ! Нормалізація ПРАЦЮЄ - знайдено {total_matched} співпадінь!")
                    else:
                        print(f"\n❌ ПРОБЛЕМА: 0 matched контактів")

                    # Деталі по кампаніям
                    print(f"\n📋 ДЕТАЛІ ПО КАМПАНІЯМ (перші 5):")
                    for i, campaign in enumerate(campaigns[:5], 1):
                        name = campaign.get("campaign_name", "N/A")
                        if "student_tracking" in campaign:
                            tracking = campaign["student_tracking"]
                            matched = tracking.get("matched", 0)
                            not_found = tracking.get("not_found_in_crm", 0)
                            print(f"\n   {i}. {name}")
                            print(f"      matched: {matched}, not_found: {not_found}")

        elif "campaigns" in data:
            # Інша структура - campaigns на верхньому рівні
            print("campaigns знаходиться на верхньому рівні")

        # Збережемо відповідь у файл для детального аналізу
        with open("api_response.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"\n\nПовна відповідь збережена у api_response.json")

    else:
        print(f"Помилка: {response.status_code}")

except Exception as e:
    print(f"Помилка: {e}")
