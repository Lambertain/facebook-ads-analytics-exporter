"""
Детальний тест API з виводом прогресу
"""
import requests
import time
from datetime import datetime, timedelta

# Параметри
endpoint = "http://127.0.0.1:8000/api/meta-data"
end_date = "2025-10-12"
start_date = "2025-10-09"

print("=" * 80)
print("ДЕТАЛЬНИЙ ТЕСТ /api/meta-data ENDPOINT")
print("=" * 80)
print(f"\nПеріод: {start_date} - {end_date}")
print(f"Endpoint: {endpoint}")
print(f"Timeout: 600 секунд (10 хвилин)")
print("\n" + "=" * 80)

start_time = time.time()
print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Викликаю API...\n")

try:
    response = requests.get(
        endpoint,
        params={"start_date": start_date, "end_date": end_date},
        timeout=600  # 10 хвилин
    )

    elapsed = time.time() - start_time

    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Отримано відповідь!")
    print(f"Час виконання: {elapsed:.1f} секунд ({elapsed/60:.1f} хвилин)")
    print(f"Статус код: {response.status_code}")

    if response.status_code == 200:
        data = response.json()

        print("\n" + "=" * 80)
        print("АНАЛІЗ РЕЗУЛЬТАТІВ")
        print("=" * 80)

        # Аналіз кампаній
        if "campaigns" in data:
            total_campaigns = len(data["campaigns"])
            print(f"\nВсього кампаній: {total_campaigns}")

            # Підрахунок кампаній з matched контактами
            campaigns_with_matches = 0
            total_matched = 0
            total_not_found = 0

            for campaign in data["campaigns"]:
                if "student_tracking" in campaign:
                    tracking = campaign["student_tracking"]
                    matched = tracking.get("matched", 0)
                    not_found = tracking.get("not_found_in_crm", 0)

                    if matched > 0:
                        campaigns_with_matches += 1

                    total_matched += matched
                    total_not_found += not_found

            print(f"\n📊 СТАТИСТИКА СПІВСТАВЛЕННЯ:")
            print(f"   Кампаній з matched контактами: {campaigns_with_matches}/{total_campaigns}")
            print(f"   Всього matched контактів: {total_matched}")
            print(f"   Всього не знайдено в CRM: {total_not_found}")

            if total_matched > 0:
                print(f"\n✅ УСПІХ! Нормалізація працює - знайдено {total_matched} співпадінь!")
            else:
                print(f"\n❌ ПРОБЛЕМА: 0 matched контактів. Нормалізація не спрацювала.")

            # Показати деталі перших 3 кампаній
            print(f"\n📋 ДЕТАЛІ ПЕРШИХ 3 КАМПАНІЙ:")
            for i, campaign in enumerate(data["campaigns"][:3], 1):
                print(f"\n   {i}. {campaign.get('campaign_name', 'N/A')}")
                if "student_tracking" in campaign:
                    tracking = campaign["student_tracking"]
                    print(f"      - Matched: {tracking.get('matched', 0)}")
                    print(f"      - Not found: {tracking.get('not_found_in_crm', 0)}")

        print("\n" + "=" * 80)
        print("✅ ТЕСТ ЗАВЕРШЕНО УСПІШНО!")
        print("=" * 80)
    else:
        print(f"\n❌ Помилка: {response.status_code}")
        print(f"Відповідь: {response.text[:500]}")

except requests.exceptions.Timeout:
    elapsed = time.time() - start_time
    print(f"\n❌ TIMEOUT після {elapsed:.1f} секунд ({elapsed/60:.1f} хвилин)")
    print("   Спробуйте збільшити timeout або перевірити продуктивність серверу")

except Exception as e:
    elapsed = time.time() - start_time
    print(f"\n❌ ПОМИЛКА після {elapsed:.1f} секунд: {str(e)}")
