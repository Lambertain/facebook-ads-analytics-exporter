"""
Диагностический скрипт для проверки Meta API Insights.

Проверяет:
1. Валидность токена META_ACCESS_TOKEN
2. Правильность META_AD_ACCOUNT_ID
3. Наличие insights за указанный период
4. Детальный лог ответа Meta API
"""
import os
import sys
import requests
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

def check_meta_insights(date_from: str, date_to: str):
    """
    Проверка получения insights из Meta API за период.

    Args:
        date_from: Начало периода (YYYY-MM-DD)
        date_to: Конец периода (YYYY-MM-DD)
    """
    print("=" * 80)
    print("ДИАГНОСТИКА META API INSIGHTS")
    print("=" * 80)

    # Проверка переменных окружения
    meta_token = os.getenv("META_ACCESS_TOKEN")
    ad_account_id = os.getenv("META_AD_ACCOUNT_ID")

    print(f"\n1. Проверка переменных окружения:")
    print(f"   META_ACCESS_TOKEN: {'✅ Установлен' if meta_token else '❌ НЕ установлен'}")
    print(f"   META_AD_ACCOUNT_ID: {'✅ Установлен' if ad_account_id else '❌ НЕ установлен'}")

    if not meta_token or not ad_account_id:
        print("\n❌ ОШИБКА: Переменные окружения не установлены!")
        print("   Убедитесь что .env файл содержит:")
        print("   META_ACCESS_TOKEN=<ваш_токен>")
        print("   META_AD_ACCOUNT_ID=<ваш_ad_account_id>")
        sys.exit(1)

    # Формируем запрос к Meta API
    url = f"https://graph.facebook.com/v21.0/{ad_account_id}/insights"

    params = {
        "access_token": meta_token,
        "time_range": f"{{'since':'{date_from}','until':'{date_to}'}}",
        "fields": "campaign_id,campaign_name,ad_id,ad_name,adset_id,adset_name,spend,impressions,clicks,ctr,cpm,actions",
        "level": "ad",
        "limit": 100
    }

    print(f"\n2. Запрос к Meta API:")
    print(f"   URL: {url}")
    print(f"   Период: {date_from} - {date_to}")
    print(f"   Level: ad")

    try:
        print(f"\n3. Отправка запроса...")
        response = requests.get(url, params=params, timeout=30)

        print(f"   Статус код: {response.status_code}")

        if response.status_code != 200:
            print(f"\n❌ ОШИБКА Meta API!")
            print(f"   Ответ: {response.text}")

            # Попытка распарсить JSON с ошибкой
            try:
                error_data = response.json()
                if "error" in error_data:
                    error_info = error_data["error"]
                    print(f"\n   Код ошибки: {error_info.get('code')}")
                    print(f"   Тип ошибки: {error_info.get('type')}")
                    print(f"   Сообщение: {error_info.get('message')}")
                    print(f"   Подтип: {error_info.get('error_subcode', 'N/A')}")
            except Exception:
                pass

            sys.exit(1)

        # Парсим ответ
        data = response.json()
        insights = data.get("data", [])

        print(f"\n4. Результат:")
        print(f"   Получено insights: {len(insights)}")

        if not insights:
            print(f"\n⚠️  ПРОБЛЕМА НАЙДЕНА: Meta API вернул 0 insights за период {date_from} - {date_to}")
            print(f"\n   Возможные причины:")
            print(f"   1. За этот период не было активных кампаний")
            print(f"   2. Период слишком старый (Meta API хранит данные ~90 дней)")
            print(f"   3. Период в будущем")
            print(f"   4. Неправильный AD_ACCOUNT_ID (не тот аккаунт)")
            print(f"\n   Рекомендации:")
            print(f"   - Проверьте что кампании были активны в этот период")
            print(f"   - Попробуйте период за последние 7 дней")
            print(f"   - Проверьте AD_ACCOUNT_ID в Meta Ads Manager")
        else:
            print(f"\n✅ УСПЕХ: Insights получены!")
            print(f"\n   Примеры кампаний:")
            for i, insight in enumerate(insights[:5], 1):
                campaign_name = insight.get("campaign_name", "N/A")
                campaign_id = insight.get("campaign_id", "N/A")
                spend = insight.get("spend", "0")
                print(f"   {i}. {campaign_name[:50]}... (ID: {campaign_id}, Spend: ${spend})")

            # Проверка на actions (лиды)
            print(f"\n   Проверка лидов:")
            total_leads = 0
            for insight in insights:
                actions = insight.get("actions", [])
                for action in actions:
                    if action.get("action_type") == "lead":
                        total_leads += int(action.get("value", 0))

            print(f"   Всего лидов (из actions): {total_leads}")

            if total_leads == 0:
                print(f"\n   ⚠️  У insights нет лидов (actions.lead)")
                print(f"   Это нормально если кампании не используют Lead Ads формы")

    except requests.exceptions.Timeout:
        print(f"\n❌ TIMEOUT: Meta API не ответил за 30 секунд")
        sys.exit(1)
    except requests.exceptions.RequestException as e:
        print(f"\n❌ ОШИБКА СЕТИ: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ НЕОЖИДАННАЯ ОШИБКА: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    print("\n" + "=" * 80)
    print("ДИАГНОСТИКА ЗАВЕРШЕНА")
    print("=" * 80)


if __name__ == "__main__":
    # Период из скриншота пользователя
    DATE_FROM = "2025-10-05"
    DATE_TO = "2025-10-11"

    print(f"\n🔍 Тестируем период: {DATE_FROM} - {DATE_TO}")
    print(f"   (Тот же период что был на скриншоте)\n")

    check_meta_insights(DATE_FROM, DATE_TO)
