"""
Скрипт для получения бессрочного Page Access Token от Meta API.

Процесс:
1. Берет short-lived User Access Token (из ввода пользователя)
2. Обменивает на long-lived User Token (60 дней)
3. Получает бессрочный Page Access Token
4. Обновляет .env файл

Использование:
    python scripts/refresh_meta_tokens.py
"""
import os
import sys
import requests
from pathlib import Path
from datetime import datetime

# Добавить путь к проекту
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv, set_key

# Загрузить текущие переменные
env_path = project_root / ".env"
load_dotenv(env_path)

META_API_BASE = "https://graph.facebook.com/v21.0"


def print_separator(title: str):
    """Печать разделителя."""
    print(f"\n{'=' * 80}")
    print(f"{title:^80}")
    print(f"{'=' * 80}\n")


def get_app_credentials():
    """Получить App ID и App Secret."""
    app_id = os.getenv("META_APP_ID")
    app_secret = os.getenv("META_APP_SECRET")

    if not app_id:
        print("META_APP_ID не найден в .env файле")
        app_id = input("Введите Meta App ID: ").strip()

    if not app_secret:
        print("META_APP_SECRET не найден в .env файле")
        app_secret = input("Введите Meta App Secret: ").strip()

    return app_id, app_secret


def get_short_lived_token():
    """Получить short-lived User Access Token от пользователя."""
    print("\nШаг 1: Получение short-lived User Access Token")
    print("-" * 80)
    print("\n1. Откройте: https://developers.facebook.com/tools/explorer/")
    print("2. Выберите ваше приложение")
    print("3. Нажмите 'Get Token' -> 'Get User Access Token'")
    print("4. Выберите permissions:")
    print("   - pages_manage_ads")
    print("   - pages_read_engagement")
    print("   - leads_retrieval")
    print("   - pages_show_list")
    print("5. Нажмите 'Generate Access Token'")
    print("6. Скопируйте токен\n")

    token = input("Вставьте short-lived User Access Token: ").strip()
    return token


def exchange_for_long_lived(app_id: str, app_secret: str, short_token: str) -> str:
    """Обменять short-lived на long-lived User Token."""
    print("\nШаг 2: Обмен на long-lived User Token (60 дней)")
    print("-" * 80)

    url = f"{META_API_BASE}/oauth/access_token"
    params = {
        "grant_type": "fb_exchange_token",
        "client_id": app_id,
        "client_secret": app_secret,
        "fb_exchange_token": short_token
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        long_lived_token = data.get("access_token")
        expires_in = data.get("expires_in", 0)

        days = expires_in // 86400  # Перевести секунды в дни

        print(f"OK Long-lived User Token получен")
        print(f"   Срок действия: {days} дней")

        return long_lived_token

    except requests.exceptions.RequestException as e:
        print(f"ERROR: Не удалось обменять токен: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"Детали: {e.response.text}")
        sys.exit(1)


def get_page_token(long_lived_token: str, page_id: str) -> str:
    """Получить бессрочный Page Access Token."""
    print("\nШаг 3: Получение бессрочного Page Access Token")
    print("-" * 80)

    url = f"{META_API_BASE}/me/accounts"
    params = {
        "access_token": long_lived_token
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        pages = data.get("data", [])

        if not pages:
            print("ERROR: Не найдено страниц, доступных этому пользователю")
            sys.exit(1)

        # Найти нужную страницу
        target_page = None
        for page in pages:
            if page.get("id") == page_id:
                target_page = page
                break

        if not target_page:
            print(f"\nНе найдена страница с ID: {page_id}")
            print("\nДоступные страницы:")
            for i, page in enumerate(pages, 1):
                print(f"  {i}. {page.get('name')} (ID: {page.get('id')})")

            choice = input("\nВыберите номер страницы: ").strip()
            target_page = pages[int(choice) - 1]

        page_token = target_page.get("access_token")
        page_name = target_page.get("name")
        page_id = target_page.get("id")

        print(f"OK Page Token получен")
        print(f"   Страница: {page_name}")
        print(f"   ID: {page_id}")

        return page_token, page_id

    except requests.exceptions.RequestException as e:
        print(f"ERROR: Не удалось получить Page Token: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"Детали: {e.response.text}")
        sys.exit(1)


def verify_token_permanence(app_id: str, app_secret: str, page_token: str):
    """Проверить что Page Token бессрочный."""
    print("\nШаг 4: Проверка что токен бессрочный")
    print("-" * 80)

    url = f"{META_API_BASE}/debug_token"
    params = {
        "input_token": page_token,
        "access_token": f"{app_id}|{app_secret}"
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        token_data = data.get("data", {})
        expires_at = token_data.get("expires_at", None)
        is_valid = token_data.get("is_valid", False)
        token_type = token_data.get("type", "")

        print(f"Тип токена: {token_type}")
        print(f"Валидный: {is_valid}")

        if expires_at == 0:
            print(f"Срок действия: БЕССРОЧНЫЙ (expires_at: 0)")
            print("\nОТЛИЧНО! Токен бессрочный.")
            return True
        elif expires_at:
            expiry_date = datetime.fromtimestamp(expires_at)
            print(f"Срок действия: {expiry_date}")
            print(f"\nВНИМАНИЕ: Токен НЕ бессрочный. Истечет: {expiry_date}")
            return False
        else:
            print(f"Срок действия: Неизвестно")
            return None

    except requests.exceptions.RequestException as e:
        print(f"WARNING: Не удалось проверить токен: {e}")
        return None


def update_env_file(long_lived_user_token: str, page_token: str, page_id: str,
                    app_id: str, app_secret: str):
    """Обновить .env файл с новыми токенами."""
    print("\nШаг 5: Обновление .env файла")
    print("-" * 80)

    try:
        # Обновить токены
        set_key(env_path, "META_USER_ACCESS_TOKEN", long_lived_user_token)
        set_key(env_path, "META_PAGE_ACCESS_TOKEN", page_token)
        set_key(env_path, "FACEBOOK_PAGE_ID", page_id)
        set_key(env_path, "META_APP_ID", app_id)
        set_key(env_path, "META_APP_SECRET", app_secret)

        print(f"OK .env файл обновлен")
        print(f"   Path: {env_path}")
        print(f"\nОбновленные переменные:")
        print(f"   META_USER_ACCESS_TOKEN: {long_lived_user_token[:20]}...")
        print(f"   META_PAGE_ACCESS_TOKEN: {page_token[:20]}...")
        print(f"   FACEBOOK_PAGE_ID: {page_id}")
        print(f"   META_APP_ID: {app_id}")

    except Exception as e:
        print(f"ERROR: Не удалось обновить .env: {e}")
        print(f"\nСкопируйте вручную:")
        print(f'META_USER_ACCESS_TOKEN="{long_lived_user_token}"')
        print(f'META_PAGE_ACCESS_TOKEN="{page_token}"')
        print(f'FACEBOOK_PAGE_ID="{page_id}"')
        print(f'META_APP_ID="{app_id}"')
        print(f'META_APP_SECRET="{app_secret}"')


def main():
    """Главная функция."""
    print_separator("META API: ПОЛУЧЕНИЕ БЕССРОЧНОГО PAGE ACCESS TOKEN")

    print("Этот скрипт поможет получить бессрочный Page Access Token.")
    print("Вам понадобится:")
    print("  1. Meta App ID и App Secret")
    print("  2. Доступ к Graph API Explorer")
    print("  3. Admin права на Facebook Page\n")

    # Получить credentials
    app_id, app_secret = get_app_credentials()
    page_id = os.getenv("FACEBOOK_PAGE_ID", "")

    if not page_id:
        page_id = input("Введите Facebook Page ID: ").strip()

    # Шаг 1: Short-lived token
    short_token = get_short_lived_token()

    # Шаг 2: Обменять на long-lived
    long_lived_token = exchange_for_long_lived(app_id, app_secret, short_token)

    # Шаг 3: Получить Page Token
    page_token, page_id = get_page_token(long_lived_token, page_id)

    # Шаг 4: Проверить что бессрочный
    is_permanent = verify_token_permanence(app_id, app_secret, page_token)

    # Шаг 5: Обновить .env
    update_env_file(long_lived_token, page_token, page_id, app_id, app_secret)

    print_separator("ГОТОВО!")

    if is_permanent:
        print("Бессрочный Page Access Token успешно получен и сохранен в .env")
        print("\nСледующие шаги:")
        print("  1. Перезапустите приложение для загрузки новых токенов")
        print("  2. Запустите тесты: python test_multiday_tracking.py")
    else:
        print("Page Access Token получен, но он НЕ бессрочный.")
        print("Возможные причины:")
        print("  - User Token был short-lived, а не long-lived")
        print("  - Ошибка в процессе обмена токенов")
        print("\nПопробуйте запустить скрипт снова.")


if __name__ == "__main__":
    main()
