# Обновление Meta API Токенов

## Проблема

```
Meta API Error: 400 - {
  'error': {
    'message': 'Error validating access token: Session has expired on Wednesday, 08-Oct-25 04:00:00 PDT.',
    'type': 'OAuthException',
    'code': 190,
    'error_subcode': 463
  }
}
```

**Причина**: Page Access Token истек и требует обновления.

## Типы токенов Meta API

### 1. User Access Token
- **Срок действия**: 1-2 часа (short-lived) или 60 дней (long-lived)
- **Для чего**: Авторизация пользователя, получение Page Access Token
- **Как получить**: OAuth flow через Graph API Explorer или App

### 2. Page Access Token
- **Срок действия**: Зависит от User Access Token (может быть бессрочным)
- **Для чего**: Доступ к лид-формам страницы, leads retrieval
- **Как получить**: Через User Access Token

## Решение 1: Получить новый Page Access Token через Graph API Explorer

### Шаг 1: Получить новый User Access Token
1. Открыть https://developers.facebook.com/tools/explorer/
2. Выбрать приложение
3. Выбрать нужные permissions:
   - `pages_manage_ads`
   - `pages_read_engagement`
   - `leads_retrieval`
   - `pages_show_list`
4. Нажать "Generate Access Token"
5. Скопировать User Access Token

### Шаг 2: Продлить User Access Token (long-lived)
```bash
curl "https://graph.facebook.com/v21.0/oauth/access_token?grant_type=fb_exchange_token&client_id={APP_ID}&client_secret={APP_SECRET}&fb_exchange_token={SHORT_LIVED_TOKEN}"
```

Ответ:
```json
{
  "access_token": "LONG_LIVED_USER_TOKEN",
  "token_type": "bearer",
  "expires_in": 5183944  // ~60 дней
}
```

### Шаг 3: Получить Page Access Token
```bash
curl "https://graph.facebook.com/v21.0/me/accounts?access_token={LONG_LIVED_USER_TOKEN}"
```

Ответ:
```json
{
  "data": [
    {
      "access_token": "PAGE_ACCESS_TOKEN",
      "id": "918302931682635",
      "name": "eCademy"
    }
  ]
}
```

### Шаг 4: Обновить .env файл
```env
META_USER_ACCESS_TOKEN=<LONG_LIVED_USER_TOKEN>
META_PAGE_ACCESS_TOKEN=<PAGE_ACCESS_TOKEN>
```

## Решение 2: Бессрочный Page Access Token

Если User Access Token является **long-lived** (60 дней), то полученный из него Page Access Token **не истекает**.

### Процесс:
1. Получить short-lived User Access Token
2. Обменять на long-lived User Access Token (60 дней)
3. Получить Page Access Token через long-lived User Token
4. **Page Access Token будет бессрочным**

### Проверка срока действия токена
```bash
curl "https://graph.facebook.com/v21.0/debug_token?input_token={TOKEN_TO_CHECK}&access_token={APP_ID}|{APP_SECRET}"
```

Ответ:
```json
{
  "data": {
    "app_id": "YOUR_APP_ID",
    "type": "PAGE",
    "expires_at": 0,  // 0 = бессрочный
    "is_valid": true,
    "scopes": ["pages_manage_ads", "leads_retrieval", ...],
    "user_id": "USER_ID"
  }
}
```

## Автоматическое обновление токенов (Будущая задача)

### Вариант 1: Scheduled Token Refresh
- Cron job каждые 50 дней обновляет User Access Token
- Получает новый Page Access Token
- Обновляет .env или базу данных

### Вариант 2: Webhook для истекающих токенов
- Facebook Webhooks уведомляет о скором истечении
- Автоматически триггерит обновление токенов

### Вариант 3: System User Token (для бизнес-аккаунтов)
- Создать System User в Business Manager
- Сгенерировать бессрочный токен
- Использовать для всех API запросов

## Текущие настройки eCademy

**App ID**: Нужно уточнить у клиента
**App Secret**: Нужно уточнить у клиента
**Page ID**: `918302931682635`
**Истекший Page Token**: `EAAOzSZAGrZAjYBPptRX5SGMspkPbNnHgbKvljkzlKP6r6...`
**Дата истечения**: 2025-10-08 04:00:00 PDT

## Действия для продолжения работы

1. ✅ Создана документация по обновлению токенов
2. ⏳ **НУЖНО**: Клиент должен обновить токены через Graph API Explorer
3. ⏳ Создать тест с моковыми данными для демонстрации функционала
4. ⏳ После обновления токенов - протестировать на реальных данных

## Альтернатива: Mock тест для демонстрации

Создан `test_multiday_mock.py` который использует моковые данные для демонстрации работы модулей трекинга без необходимости в валидных токенах.
