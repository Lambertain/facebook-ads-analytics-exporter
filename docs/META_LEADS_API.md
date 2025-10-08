# Meta Leads API - Документация

## 📋 Обзор

Проект eCademy использует Meta Graph API для получения лидов из Lead Ads форм Facebook.

## 🔑 Настройка токенов

### Требуемые разрешения (Permissions)

При создании User Access Token через Graph API Explorer нужно добавить:

- ✅ `leads_retrieval` - **главное разрешение** для получения лидов
- ✅ `pages_manage_ads` - доступ к страницам с лид-формами
- ✅ `pages_show_list` - список страниц
- ✅ `ads_read` - чтение рекламных данных
- ✅ `read_insights` - статистика рекламы

### Два типа токенов

**1. User Access Token** - для работы с Ad Account и кампаниями:
```
META_USER_ACCESS_TOKEN=EAAOzSZ...
```

**2. Page Access Token** - для получения лидов из форм:
```
META_PAGE_ACCESS_TOKEN=EAAOzSZ...
```

### Как получить Page Access Token

```bash
curl "https://graph.facebook.com/v21.0/{PAGE_ID}?fields=access_token&access_token={USER_ACCESS_TOKEN}"
```

## 📊 Структура данных

### Получение лид-форм

**Эндпоинт:** `/{PAGE_ID}/leadgen_forms`

**Пример запроса:**
```bash
curl "https://graph.facebook.com/v21.0/918302931682635/leadgen_forms?fields=id,name,status,leads_count&access_token={PAGE_ACCESS_TOKEN}"
```

**Пример ответа:**
```json
{
  "data": [
    {
      "id": "914125173480823",
      "name": "Форма Pasha-new-nemec_04,01",
      "status": "ACTIVE",
      "leads_count": 4098
    }
  ]
}
```

### Получение лидов

**Эндпоинт:** `/{FORM_ID}/leads`

**Пример запроса:**
```bash
curl "https://graph.facebook.com/v21.0/914125173480823/leads?fields=id,created_time,ad_id,ad_name,adset_id,adset_name,campaign_id,campaign_name,form_id,field_data&access_token={PAGE_ACCESS_TOKEN}"
```

**Пример ответа:**
```json
{
  "data": [
    {
      "id": "24905838062380228",
      "created_time": "2025-10-08T09:09:27+0000",
      "ad_id": "120226863088130609",
      "ad_name": "3/статика/Індивідуальні уроки німецької від 299 грн",
      "adset_id": "120226862970650609",
      "adset_name": "Україна/30-55/Ж/Advantage+",
      "campaign_id": "120226862970630609",
      "campaign_name": "Student/Анатолій/ЛФ/Україна,30-55,Ж,Advantage+/24.07.2025",
      "form_id": "914125173480823",
      "field_data": [
        {"name": "full_name", "values": ["Nata Petrenko"]},
        {"name": "phone_number", "values": ["+380631045546"]},
        {"name": "эл._адрес", "values": ["snv88@ukr.net"]},
        {"name": "country", "values": ["UA"]},
        {"name": "куди_відправити_інформацію?", "values": ["viber"]},
        {"name": "коли_б_хотіли_спробувати_пробне_заняття?", "values": ["цього тижня"]},
        {"name": "яку_мову_хочете_вивчати?", "values": ["німецьку"]},
        {"name": "який_рівень_у_вас_зараз?", "values": ["початковий_рівень"]}
      ]
    }
  ]
}
```

## 🎯 Данные по каждому лиду

Каждый лид содержит полную информацию об источнике:

| Поле | Описание |
|------|----------|
| `id` | Уникальный ID лида |
| `created_time` | Дата и время создания лида |
| `campaign_id` | ID рекламной кампании |
| `campaign_name` | Название кампании |
| `adset_id` | ID набора объявлений |
| `adset_name` | Название adset (таргетинг) |
| `ad_id` | ID конкретного объявления |
| `ad_name` | Название объявления (креатив) |
| `form_id` | ID лид-формы |
| `field_data` | Массив заполненных полей формы |

## 📝 Поля форм eCademy

Стандартные поля в лид-формах:

1. `full_name` - ФИО лида
2. `phone_number` - телефон
3. `эл._адрес` - email
4. `country` - страна (UA, DE и т.д.)
5. `куди_відправити_інформацію?` - канал связи (viber, telegram, whatsapp)
6. `коли_б_хотіли_спробувати_пробне_заняття?` - когда хотят пробное занятие
7. `яку_мову_хочете_вивчати?` - какой язык хотят изучать
8. `який_рівень_у_вас_зараз?` - текущий уровень владения языком

## 🔄 Интеграция с AlfaCRM

После получения лидов из Meta API, данные обогащаются через AlfaCRM:

1. Получить лид из Meta API (email, phone, name)
2. Найти студента в AlfaCRM по email или phone
3. Обогатить данные: статус обучения, оплаты, посещаемость
4. Связать с рекламной кампанией для аналитики ROI

## 📍 Конфигурация проекта

**Основные переменные окружения:**

```env
# Meta API
META_USER_ACCESS_TOKEN=...
META_PAGE_ACCESS_TOKEN=...
META_AD_ACCOUNT_ID=act_1403989946628902
FACEBOOK_PAGE_ID=918302931682635

# AlfaCRM
ALFACRM_BASE_URL=https://ecademyua.alfacrm.com
ALFACRM_EMAIL=ruslan9699@icloud.com
ALFACRM_API_KEY=21ad68a5-8d2c-11ed-83fb-3cecef7ebd64
ALFACRM_COMPANY_ID=1
```

## 🚀 Примеры использования в коде

### Python FastAPI

```python
import os
import requests

def get_leads_from_form(form_id: str, limit: int = 100):
    """Получить лиды из конкретной лид-формы."""
    page_token = os.getenv("META_PAGE_ACCESS_TOKEN")
    url = f"https://graph.facebook.com/v21.0/{form_id}/leads"

    params = {
        "fields": "id,created_time,ad_id,ad_name,campaign_id,campaign_name,field_data",
        "access_token": page_token,
        "limit": limit
    }

    response = requests.get(url, params=params)
    return response.json()

def get_all_leadgen_forms():
    """Получить все лид-формы страницы."""
    page_id = os.getenv("FACEBOOK_PAGE_ID")
    page_token = os.getenv("META_PAGE_ACCESS_TOKEN")
    url = f"https://graph.facebook.com/v21.0/{page_id}/leadgen_forms"

    params = {
        "fields": "id,name,status,leads_count",
        "access_token": page_token
    }

    response = requests.get(url, params=params)
    return response.json()
```

## ⚠️ Важные замечания

1. **Срок жизни токенов:**
   - Short-lived token: 1-2 часа
   - Long-lived token: 60 дней
   - Для production использовать System User Token (не истекает)

2. **Rate Limits:**
   - Meta API имеет лимиты запросов
   - Используйте пагинацию для больших объёмов данных
   - Кешируйте данные где возможно

3. **Разрешения:**
   - `leads_retrieval` требует App Review для публичных приложений
   - В Development Mode работает только для админов/тестеров приложения

4. **Webhooks:**
   - Рекомендуется настроить Webhooks для real-time получения лидов
   - Подписка на событие `leadgen` для мгновенного уведомления о новых лидах

## 🔗 Полезные ссылки

- [Meta Graph API Explorer](https://developers.facebook.com/tools/explorer/)
- [Lead Ads API Documentation](https://developers.facebook.com/docs/marketing-api/guides/lead-ads)
- [Permissions Reference](https://developers.facebook.com/docs/permissions/reference)
- [Webhooks for Lead Ads](https://developers.facebook.com/docs/marketing-api/guides/lead-ads/retrieving)
