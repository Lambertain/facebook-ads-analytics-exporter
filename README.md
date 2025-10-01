# Meta Ads → Google Sheets → CRM

Простий сервіс для вивантаження метрик рекламних кампаній та лідів з Meta (Facebook) Ads, запису в Google Sheets та перевірки статусів лідів у CRM. Включає мінімальний веб-інтерфейс з вибором періоду, кнопкою «Старт» та прогрес-баром.

## Стек
- FastAPI (backend) + SSE для прогресу
- React + Material UI (фронтенд)
- Коннектори: Meta Marketing API, Google Sheets (gspread), CRM (NetHunt, AlfaCRM)

## Швидкий старт

### Варіант 1: Docker (рекомендується)
1) Скопіюйте `.env.example` в `.env` та заповніть змінні (див. інструкції в файлі)

2) Зберіть фронтенд:
```bash
cd web
npm install
npm run build
cd ..
```

3) Запустіть через Docker Compose:
```bash
docker-compose up -d
```

4) Відкрийте http://localhost:8000

### Варіант 2: Локальна розробка
1) Встановіть залежності:
```bash
python -m venv .venv
# Windows:
.\.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

pip install -r requirements.txt
# Для разработки:
pip install -r requirements-dev.txt
pre-commit install
```

2) Скопируйте `.env.example` в `.env` и заполните:
- `META_ACCESS_TOKEN` — токен Meta Marketing API (с правами ads_read, leads_retrieval)
- `META_AD_ACCOUNT_ID` — формат `act_XXXXXXXX`
- `GOOGLE_APPLICATION_CREDENTIALS` — путь к JSON ключу сервисного аккаунта Google
- `GOOGLE_SHEET_ID` — ID таблицы (опционально, можно ввести через UI)
- `NETHUNT_BASIC_AUTH` и `NETHUNT_FOLDER_ID` — для интеграции с NetHunt CRM (преподаватели)
- `ALFACRM_*` — для интеграции с AlfaCRM (студенты)

3) Дайте сервисному аккаунту доступ к таблице (Share → редактор).

4) Запуск dev‑сервера:
```bash
uvicorn app.main:app --reload
```
Откройте http://localhost:8000

## Новый UI (React + MUI)
- Фронтенд лежит в `web/` (Vite + React + MUI).
- Dev-запуск UI с прокси на backend:
```
cd web
npm install
npm run dev
```
Открыть http://localhost:5173 (или сборка):
```
npm run build
```
Собранные файлы попадут в `web/dist`, FastAPI начнёт раздавать их по `http://localhost:8000`.

## Что уже работает
- Поле для периода, Sheet ID, кнопка «Старт».
- Фоновая задача, которая:
  - Получает инсайты кампаний Meta (уровень campaign, day)
  - Получает лиды с ваших страниц/форм в указанном периоде
  - (Заглушка) обогащает лиды статусами из выбранной CRM
  - Записывает «Insights» и «Leads» в указанный Google Sheet
  - **НОВОЕ**: Сохраняет историю запусков в базу данных (SQLite)
- Прогресс‑бар и поток логов (SSE)
- UI вкладка «Настройки» для ввода кредов и путей; сохранение в `.env`
- **НОВОЕ**: UI вкладка «История» для просмотра всех запусков:
  - Фильтрация по статусу (успешные/ошибки/все)
  - Просмотр детальной информации о каждом запуске
  - Просмотр логов выполнения
  - Количество обработанных записей (creatives, студенты, учителя)

## API Authentication (Security)

**ВАЖНО:** В production режиме API защищен authentication через API keys.

### Генерация API ключа:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### Настройка:
1. Добавьте сгенерированный ключ в `.env`:
```
API_KEYS=ваш_сгенерированный_ключ_здесь
```

2. Для нескольких ключей используйте запятую без пробелов:
```
API_KEYS=key1,key2,key3
```

### Использование API:
Добавьте `Authorization` header ко всем защищенным запросам:
```bash
curl -X POST http://localhost:8000/api/start-job \
  -H "Authorization: Bearer ваш_api_ключ" \
  -H "Content-Type: application/json" \
  -d '{"start_date": "2025-01-01", "end_date": "2025-01-31"}'
```

### Защищенные endpoints:
- `POST /api/start-job` - запуск pipeline
- `POST /api/config` - изменение конфигурации

**Development режим:** Если `API_KEYS` пустой, authentication отключен для удобства разработки.

## Настройка Meta
- Получите `META_ACCESS_TOKEN` с правами: ads_read, leads_retrieval и доступом к нужным страницам/аккаунту.
- Укажите `META_AD_ACCOUNT_ID` (например, `act_1234567890`).

## Настройка Google Sheets
- Создайте сервисный аккаунт в Google Cloud, скачайте JSON ключ.
- Укажите путь к файлу в `GOOGLE_APPLICATION_CREDENTIALS` (в `.env`).
- Поделитесь целевой таблицей с email сервисного аккаунта (роль: редактор).

## CRM
Сейчас зашиты заглушки. Для продакшена:
- amoCRM: искать лид/контакт по телефону/email, вернуть статус/этап воронки
- Bitrix24: `crm.lead.list`/`crm.deal.list` с фильтром по полям телефона/email
- HubSpot: поиск контакта, связка с сделками и стадиями
- Pipedrive: поиск person и сделок

Вносите вызовы в `app/connectors/crm.py` и добавляйте нужные поля на запись в таблицу.

## Структура таблиц
- Лист `Insights`: date_start, date_stop, campaign_id, campaign_name, impressions, clicks, spend, reach, cpc, cpm, ctr, objective
- Лист `Leads`: id, created_time, page_id, form_id, crm_status, crm_stage, contact_phone, contact_email, raw_fields_json

## Расширение
- Добавьте фильтры по кампаниям/площадкам.
- Добавьте планировщик (cron) для авто‑запуска.
- Храните историю запусков в БД (SQLite/Postgres) и показывайте её в UI.
- Замените SSE на WebSocket, если нужны двусторонние события.

## Замечания
- В `meta.fetch_leads` используется пример «все страницы → все формы». Уточните список страниц/форм для ускорения и контроля прав.
- Для больших объёмов добавьте ретраи/лимиты/экспоненциальную задержку.
