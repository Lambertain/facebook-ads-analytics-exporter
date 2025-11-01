# 🚨 HOTFIX: Исправление проблемы с META_ACCESS_TOKEN

## Диагноз проблемы

**Коммит c00787e НЕ виноват!** Проблема в том, что `META_ACCESS_TOKEN` на Railway не имеет необходимых разрешений для доступа к Ad Account.

**Ошибка Meta API:**
```
(#200) Ad account owner has NOT grant ads_management or ads_read permission
```

**Статус код:** 403 (Forbidden)
**Тип:** OAuthException

---

## 🔧 Решение (2 варианта)

### Вариант 1: Создать новый токен (РЕКОМЕНДУЕТСЯ)

#### Шаг 1: Зайти в Facebook Business Manager

1. Открыть: https://business.facebook.com/settings/system-users
2. Войти под учетной записью владельца Ad Account

#### Шаг 2: Создать System User (если еще нет)

1. Нажать **Add** → **Add System User**
2. Имя: `ecademy_analytics_bot`
3. Роль: **Admin** (для полного доступа к Ads API)
4. Нажать **Create System User**

#### Шаг 3: Сгенерировать Access Token

1. Выбрать созданного System User
2. Нажать **Generate New Token**
3. Выбрать Ad Account: `Act 1403989946628902`
4. **ОБЯЗАТЕЛЬНО** отметить permissions:
   - ✅ `ads_read` - Чтение данных рекламы
   - ✅ `ads_management` - Управление рекламой (включает ads_read)
   - ✅ `read_insights` - Чтение статистики
5. Установить срок действия: **60 days** или **Never expire** (рекомендуется для автоматизации)
6. Нажать **Generate Token**
7. **СКОПИРОВАТЬ ТОКЕН** (он показывается только один раз!)

#### Шаг 4: Обновить токен на Railway

1. Зайти в Railway: https://railway.app
2. Открыть проект: `facebook-ads-analytics-exporter-production`
3. Перейти в **Variables**
4. Найти переменную `META_ACCESS_TOKEN`
5. Нажать **Edit** → Вставить новый токен
6. Нажать **Save**
7. Railway автоматически перезапустит сервис

---

### Вариант 2: Обновить разрешения существующего токена

Если токен был создан недавно и просто не имеет разрешений:

1. Зайти в https://business.facebook.com/settings/system-users
2. Найти System User который сгенерировал токен
3. Нажать **Reassign Assets**
4. Найти Ad Account `Act 1403989946628902`
5. Убедиться что отмечены:
   - ✅ **Manage campaigns** (ads_management)
   - ✅ **View performance** (read_insights)
6. Нажать **Save Changes**
7. **Важно:** Может потребоваться перегенерация токена (Шаг 3 из Варианта 1)

---

## ✅ Проверка после исправления

### 1. Локальная проверка (если есть доступ к новому токену)

```bash
cd D:\Automation\Development\projects\ecademy

# Обновить .env с новым токеном
# META_ACCESS_TOKEN=<новый_токен>

# Запустить диагностический скрипт
python debug_meta_api.py
```

**Ожидаемый результат:**
```
✅ УСПЕХ: Insights получены!
Получено insights: <количество>
```

### 2. Проверка на Railway Production

1. Открыть UI: https://facebook-ads-analytics-exporter-production.up.railway.app
2. Перейти в **АНАЛІЗ**
3. Выбрать период: **2025-10-05 - 2025-10-11** (тот же что был на скриншоте)
4. Нажать **СТАРТ**

**Ожидаемый результат:**
```
Отримано рекламних кампаній: <число больше 0>
Отримано студентських кампаній: <число>
Отримано викладацьких кампаній: <число>
```

---

## 🔍 Дополнительная диагностика

Если проблема сохраняется после обновления токена, проверьте:

### 1. Правильность AD_ACCOUNT_ID

```bash
# В Railway Variables проверить:
META_AD_ACCOUNT_ID=act_1403989946628902
```

Формат **ОБЯЗАТЕЛЬНО** должен быть `act_<числовой_id>`, НЕ просто числовой ID!

### 2. Срок действия токена

Проверить срок действия токена:
```bash
curl -X GET "https://graph.facebook.com/v21.0/debug_token?input_token=<ваш_токен>&access_token=<ваш_токен>"
```

В ответе проверить:
```json
{
  "data": {
    "is_valid": true,  // Должно быть true
    "expires_at": 0,   // 0 = Never expire
    "scopes": [        // Должны быть ads_read или ads_management
      "ads_read",
      "read_insights"
    ]
  }
}
```

### 3. Логи Railway

Если после исправления все равно 0 кампаний:

1. Зайти в Railway → Deployments → Latest deployment
2. Открыть **Logs**
3. Искать строки:
   - `Received {N} insights from Meta API` - должно быть N > 0
   - `OAuthException` - не должно быть
   - `Fetching Meta data for period` - проверить период

---

## 📝 Коммит в репозиторий

Диагностический скрипт уже создан: `debug_meta_api.py`

Этот файл можно использовать для проверки токена в будущем.

**НЕ НУЖНО коммитить изменения в .env с настоящим токеном!** (.env уже в .gitignore)

---

## 🎯 Заключение

**Проблема НЕ в коде**, а в конфигурации токена на Railway.

После обновления `META_ACCESS_TOKEN` с правильными разрешениями (`ads_management` или `ads_read`) все должно заработать.

**Коммит c00787e безопасен** - он изменил только CRM код (AlfaCRM статусы) и никак не влияет на Meta API.
