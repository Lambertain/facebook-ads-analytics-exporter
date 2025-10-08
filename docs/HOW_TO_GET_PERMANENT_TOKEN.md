# Как получить БЕССРОЧНЫЙ Page Access Token для Meta API

## Почему токен истекает?

Meta API использует иерархию токенов:
1. **Short-lived User Token** (1-2 часа) → Page Token тоже короткий
2. **Long-lived User Token** (60 дней) → **Page Token БЕССРОЧНЫЙ** ✅

## Решение: Получить Long-lived User Token

### Способ 1: Автоматический скрипт (РЕКОМЕНДУЕТСЯ)

Создан скрипт `scripts/refresh_meta_tokens.py` который автоматически:
- Берет short-lived token
- Обменивает на long-lived (60 дней)
- Получает бессрочный Page Access Token
- Обновляет .env файл

**Использование**:
```bash
cd D:\Automation\Development\projects\ecademy
python scripts/refresh_meta_tokens.py
```

### Способ 2: Ручной через Meta Graph API Explorer

#### Шаг 1: Получить Short-lived User Access Token
1. Открыть https://developers.facebook.com/tools/explorer/
2. Выбрать ваше приложение (или создать новое)
3. Нажать "Get Token" → "Get User Access Token"
4. Выбрать permissions:
   - ✅ `pages_manage_ads`
   - ✅ `pages_read_engagement`
   - ✅ `leads_retrieval`
   - ✅ `pages_show_list`
5. Нажать "Generate Access Token"
6. Скопировать токен (это short-lived, живет 1-2 часа)

#### Шаг 2: Обменять на Long-lived User Token (60 дней)

**Через curl**:
```bash
curl "https://graph.facebook.com/v21.0/oauth/access_token?grant_type=fb_exchange_token&client_id=YOUR_APP_ID&client_secret=YOUR_APP_SECRET&fb_exchange_token=SHORT_LIVED_TOKEN"
```

**Ответ**:
```json
{
  "access_token": "LONG_LIVED_USER_TOKEN_HERE",
  "token_type": "bearer",
  "expires_in": 5183944  // ~60 дней
}
```

#### Шаг 3: Получить БЕССРОЧНЫЙ Page Access Token

**Через curl**:
```bash
curl "https://graph.facebook.com/v21.0/me/accounts?access_token=LONG_LIVED_USER_TOKEN_HERE"
```

**Ответ**:
```json
{
  "data": [
    {
      "access_token": "PERMANENT_PAGE_TOKEN_HERE",
      "id": "918302931682635",
      "name": "eCademy"
    }
  ]
}
```

⚠️ **ВАЖНО**: Этот Page Access Token будет БЕССРОЧНЫМ, потому что получен из long-lived User Token!

#### Шаг 4: Проверить что токен бессрочный

```bash
curl "https://graph.facebook.com/v21.0/debug_token?input_token=PAGE_TOKEN_HERE&access_token=YOUR_APP_ID|YOUR_APP_SECRET"
```

**Ответ**:
```json
{
  "data": {
    "app_id": "YOUR_APP_ID",
    "type": "PAGE",
    "expires_at": 0,  // ← 0 означает БЕССРОЧНЫЙ!
    "is_valid": true,
    "scopes": ["pages_manage_ads", "leads_retrieval", ...],
    "user_id": "USER_ID"
  }
}
```

Если `expires_at: 0` — токен **бессрочный** ✅

#### Шаг 5: Обновить .env файл

```env
# Long-lived User Token (60 дней, нужно обновлять раз в 2 месяца)
META_USER_ACCESS_TOKEN=LONG_LIVED_USER_TOKEN_HERE

# БЕССРОЧНЫЙ Page Token (не истекает!)
META_PAGE_ACCESS_TOKEN=PERMANENT_PAGE_TOKEN_HERE
```

## Способ 3: System User Token (для Business Manager)

### Преимущества:
- ✅ Токен не привязан к конкретному пользователю
- ✅ Бессрочный по умолчанию
- ✅ Не нужно обновлять каждые 60 дней

### Как получить:
1. Открыть Business Manager: https://business.facebook.com/
2. Settings → System Users → Add
3. Создать System User с ролью Admin
4. Generate New Token
5. Выбрать permissions:
   - pages_manage_ads
   - leads_retrieval
   - pages_read_engagement
6. Скопировать токен — он БЕССРОЧНЫЙ

### Использовать System User Token:
```env
# System User Token (бессрочный)
META_PAGE_ACCESS_TOKEN=SYSTEM_USER_TOKEN_HERE
```

## FAQ

### Q: Как часто нужно обновлять токены?

**Short-lived User Token**: Каждые 1-2 часа (не используем)
**Long-lived User Token**: Каждые 60 дней
**Page Token from Long-lived User**: БЕССРОЧНЫЙ, обновлять не нужно
**System User Token**: БЕССРОЧНЫЙ, обновлять не нужно

### Q: Что делать если забыл обновить Long-lived User Token?

Если Long-lived User Token истек (прошло 60 дней):
1. Получить новый short-lived через Graph API Explorer
2. Обменять на новый long-lived
3. Получить новый бессрочный Page Token
4. Обновить .env

### Q: Можно ли автоматизировать обновление?

Да! Скрипт `scripts/refresh_meta_tokens.py` делает это автоматически.

Можно настроить cron job (каждые 50 дней):
```bash
# Linux/Mac
0 0 */50 * * cd /path/to/project && python scripts/refresh_meta_tokens.py

# Windows Task Scheduler
schtasks /create /tn "Meta Token Refresh" /tr "python D:\Automation\Development\projects\ecademy\scripts\refresh_meta_tokens.py" /sc daily /mo 50
```

### Q: В чем разница между User Token и Page Token?

- **User Token**: Авторизует пользователя, дает доступ к списку страниц
- **Page Token**: Авторизует страницу, дает доступ к лид-формам

Нужны ОБА:
- User Token → чтобы получить Page Token
- Page Token → чтобы работать с Lead Ads API

## Текущая ситуация eCademy

**Проблема**: Использовался short-lived Page Token
**Решение**: Получить long-lived User Token → бессрочный Page Token

**Где найти App ID и App Secret?**
1. https://developers.facebook.com/apps/
2. Выбрать ваше приложение
3. Settings → Basic
4. App ID и App Secret будут там

Если приложения нет — создать новое:
1. Create App
2. Type: Business
3. Add Product: Facebook Login
4. Add permissions: leads_retrieval, pages_manage_ads

## Следующие шаги

1. ✅ Получить App ID и App Secret
2. ✅ Запустить `scripts/refresh_meta_tokens.py`
3. ✅ Проверить что токен бессрочный (`expires_at: 0`)
4. ✅ Протестировать на реальных данных
