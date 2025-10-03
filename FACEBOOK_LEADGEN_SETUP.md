# Налаштування отримання лідів з Facebook Lead Generation Forms

## Проблема
Поточний токен доступу не має необхідних прав для читання лідів з Lead Generation forms.

## Що потрібно зробити

### 1. Отримати Facebook Page ID

Ваші lead forms прив'язані до Facebook Page (сторінки), а не до окремих оголошень.

**Як знайти Page ID:**

1. Відкрийте Facebook Business Manager: https://business.facebook.com/
2. Перейдіть у розділ "Сторінки" (Pages)
3. Оберіть сторінку, до якої прив'язані ваші lead forms
4. У верхньому правому куті натисніть "Інформація про сторінку"
5. Скопіюйте "ID сторінки" (Page ID) - це число, наприклад: `123456789012345`

**Або через Graph API Explorer:**
1. Відкрийте https://developers.facebook.com/tools/explorer/
2. Виконайте запит: `GET /me/accounts`
3. Знайдіть вашу сторінку у відповіді та скопіюйте її `id`

### 2. Оновити токен доступу з правильними permissions

Поточний токен має тільки `ads_read`, але потрібні додаткові права:

**Необхідні permissions:**
- `ads_management` - читання статистики та деталей оголошень
- `leads_retrieval` - **ОБОВ'ЯЗКОВО** для читання лідів
- `pages_show_list` - список сторінок
- `pages_read_engagement` - читання взаємодій зі сторінкою
- `pages_manage_ads` - управління рекламою сторінки

**Як отримати новий токен:**

1. Відкрийте Facebook App у Developers Console: https://developers.facebook.com/apps/
2. Оберіть ваш App або створіть новий
3. У лівому меню виберіть "Tools" → "Graph API Explorer"
4. У розділі "Permissions" додайте всі зазначені вище права
5. Натисніть "Generate Access Token"
6. **ВАЖЛИВО:** Конвертуйте short-lived токен у long-lived:
   ```bash
   curl -X GET "https://graph.facebook.com/v21.0/oauth/access_token?grant_type=fb_exchange_token&client_id=YOUR_APP_ID&client_secret=YOUR_APP_SECRET&fb_exchange_token=SHORT_LIVED_TOKEN"
   ```

### 3. Оновити .env файл

Додайте новий параметр у файл `.env`:

```env
# Існуючі параметри
META_ACCESS_TOKEN=ваш_новий_токен_з_правами
META_AD_ACCOUNT_ID=act_1403989946628902

# НОВИЙ ПАРАМЕТР - додайте Page ID
FACEBOOK_PAGE_ID=ваш_page_id
```

### 4. Перевірка налаштувань

Після додавання `FACEBOOK_PAGE_ID` запустіть аналітику:

```bash
curl -X POST "http://localhost:8002/api/run" \
  -H "Content-Type: application/json" \
  -d '{"campaign_type":"teachers","date_start":"2025-09-25","date_stop":"2025-10-02"}'
```

У логах ви повинні побачити:
```
INFO - Found X leadgen forms for page YOUR_PAGE_ID
INFO - Found Y leads from form FORM_ID for period ...
INFO - Found Z leads for campaign CAMPAIGN_ID
```

## Що змінилося у коді

### Новий підхід (правильний):
1. Отримуємо всі leadgen forms зі сторінки: `GET /{page_id}/leadgen_forms`
2. Для кожної форми отримуємо ліди за період: `GET /{form_id}/leads?fields=campaign_id,field_data&filtering=...`
3. Фільтруємо ліди за `campaign_id` щоб отримати тільки ті, що належать конкретній кампанії
4. Витягуємо телефони з `field_data`

### Старий підхід (неправильний):
- ❌ Намагалися отримати форми через ad: `GET /{ad_id}?fields=leadgen_forms`
- ❌ Це поле не повертає форми після публікації оголошення

## Обмеження Meta API

- Ліди зберігаються **тільки 90 днів**
- Після 90 днів API повертає порожній список
- Переконайтеся що ваш `date_start` не старший за 90 днів

## Тестування

Якщо у формі немає реальних лідів, можна створити тестовий лід:

```bash
curl -X POST "https://graph.facebook.com/v21.0/{form_id}/test_leads" \
  -d "access_token=YOUR_TOKEN" \
  -d "field_data=[{\"name\":\"phone_number\",\"values\":[\"380501234567\"]}]"
```

## Документація Meta

- Lead Generation Forms: https://developers.facebook.com/docs/marketing-api/guides/lead-ads
- Permissions: https://developers.facebook.com/docs/permissions/reference
- Leads API: https://developers.facebook.com/docs/marketing-api/guides/lead-ads/retrieving

## Підтримка

Якщо після налаштування ліди все одно не приходять:
1. Перевірте що токен має всі необхідні права через Graph API Explorer
2. Переконайтеся що Page ID правильний
3. Перевірте що у форм є ліди за останні 90 днів
4. Подивіться логи сервера на наявність помилок 403 Forbidden
