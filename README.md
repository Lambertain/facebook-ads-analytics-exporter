# Meta Ads → Google Sheets → CRM (Skeleton)

Простой сервис для выгрузки метрик рекламных кампаний и лидов из Meta (Facebook) Ads, записи в Google Sheets и проверки статусов лидов в CRM. Включает минимальный веб‑интерфейс с выбором периода, кнопкой «Старт» и прогресс‑баром.

## Стек
- FastAPI (backend) + SSE для прогресса
- Простая HTML‑страница (без фреймворков)
- Коннекторы: Meta Marketing API, Google Sheets (gspread), CRM (заглушки)

## Быстрый старт

### Вариант 1: Docker (рекомендуется)
1) Скопируйте `.env.example` в `.env` и заполните переменные (см. инструкции в файле)

2) Соберите фронтенд:
```bash
cd web
npm install
npm run build
cd ..
```

3) Запустите через Docker Compose:
```bash
docker-compose up -d
```

4) Откройте http://localhost:8000

### Вариант 2: Локальная разработка
1) Установите зависимости:
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
- Прогресс‑бар и поток логов (SSE)
- UI вкладка «Настройки» для ввода кредов и путей; сохранение в `.env`

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
