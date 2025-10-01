# 📊 eCademy Marketing Analytics Platform

> Автоматизація вивантаження метрик Meta (Facebook) Ads, інтеграція з CRM системами та експорт даних у Google Sheets/Excel

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18+-61DAFB.svg)](https://reactjs.org/)

## 🎯 Основні можливості

- ✅ **Збір даних з Meta Ads**: Автоматичне вивантаження метрик кампаній, лідів та форм
- ✅ **Інтеграція з CRM**: Підтримка NetHunt (викладачі) та AlfaCRM (студенти)
- ✅ **Експорт даних**: Google Sheets або локальні Excel файли з форматуванням
- ✅ **Історія запусків**: Повна база даних SQLite з логами та статистикою
- ✅ **Real-time прогрес**: Server-Sent Events для моніторингу виконання
- ✅ **Безпечний API**: JWT authentication для production використання
- ✅ **Сучасний UI**: React + Material-UI з темною темою

## 📸 Демонстрація

### Головний екран з прогресом
![Main Interface](screenshots/main.png)

### Історія запусків
![History View](screenshots/history.png)

### Налаштування
![Configuration](screenshots/settings.png)

## 🏗️ Архітектура

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  React UI   │────▶│  FastAPI     │────▶│  Meta Ads   │
│  (frontend) │     │  (backend)   │     │     API     │
└─────────────┘     └──────────────┘     └─────────────┘
                           │
                           ├──────▶┌──────────────┐
                           │       │ Google       │
                           │       │ Sheets API   │
                           │       └──────────────┘
                           │
                           ├──────▶┌──────────────┐
                           │       │  NetHunt     │
                           │       │  CRM         │
                           │       └──────────────┘
                           │
                           ├──────▶┌──────────────┐
                           │       │  AlfaCRM     │
                           │       │              │
                           │       └──────────────┘
                           │
                           └──────▶┌──────────────┐
                                   │  SQLite DB   │
                                   │  (History)   │
                                   └──────────────┘
```

## 🚀 Швидкий старт

### Вимоги

- Python 3.11+
- Node.js 18+ (для frontend)
- Docker (опціонально)

### Варіант 1: Docker (рекомендується)

```bash
# 1. Клонуйте репозиторій
git clone https://github.com/your-username/ecademy.git
cd ecademy

# 2. Скопіюйте .env.example в .env та заповніть змінні
cp .env.example .env
# Відредагуйте .env у вашому редакторі

# 3. Зберіть frontend
cd web
npm install
npm run build
cd ..

# 4. Запустіть через Docker Compose
docker-compose up -d

# 5. Відкрийте браузер
open http://localhost:8000
```

### Варіант 2: Локальна розробка

```bash
# 1. Створіть віртуальне середовище
python -m venv .venv

# Windows:
.\.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# 2. Встановіть залежності
pip install -r requirements.txt

# Для розробки:
pip install -r requirements-dev.txt
pre-commit install

# 3. Налаштуйте змінні середовища
cp .env.example .env
# Відредагуйте .env

# 4. Запустіть backend
uvicorn app.main:app --reload

# 5. У окремому терміналі запустіть frontend
cd web
npm install
npm run dev
```

## ⚙️ Конфігурація

### Meta (Facebook) Marketing API

1. Отримайте access token з правами: `ads_read`, `leads_retrieval`
   - Перейдіть на https://developers.facebook.com/tools/explorer/
   - Виберіть потрібні дозволи
   - Згенеруйте довгостроковий токен

2. Знайдіть ваш Ad Account ID (формат: `act_XXXXXXXXXX`)
   - https://business.facebook.com/settings/ad-accounts/

3. Додайте у `.env`:
```bash
META_ACCESS_TOKEN=your_long_lived_token_here
META_AD_ACCOUNT_ID=act_1234567890
```

### Google Sheets API

1. Створіть проект у Google Cloud Console
2. Увімкніть Google Sheets API
3. Створіть Service Account та завантажте JSON ключ
4. Додайте у `.env`:
```bash
GOOGLE_APPLICATION_CREDENTIALS=/path/to/your/service-account.json
GOOGLE_SHEET_ID=1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t
```
5. Дайте доступ Service Account email до вашої таблиці (Share → Editor)

### CRM Інтеграції

#### NetHunt CRM (для викладачів)
```bash
NETHUNT_BASIC_AUTH=Basic base64(email:api_key)
NETHUNT_FOLDER_ID=your_folder_id
```

#### AlfaCRM (для студентів)
```bash
ALFACRM_BASE_URL=https://yoursubdomain.alfacrm.pro
ALFACRM_EMAIL=your@email.com
ALFACRM_API_KEY=your_api_key
ALFACRM_COMPANY_ID=123
```

### API Security (Production)

Для production обов'язково згенеруйте API ключ:

```bash
# Генерація безпечного ключа
python -c "import secrets; print(secrets.token_hex(32))"
```

Додайте у `.env`:
```bash
API_KEYS=your_generated_key_here
```

Для множинних ключів:
```bash
API_KEYS=key1,key2,key3
```

Використання:
```bash
curl -X POST http://localhost:8000/api/start-job \
  -H "Authorization: Bearer your_api_key" \
  -H "Content-Type: application/json" \
  -d '{"start_date": "2025-01-01", "end_date": "2025-01-31"}'
```

## 📋 API Документація

### Основні endpoints

#### `POST /api/start-job`
Запустити процес збору даних

**Request:**
```json
{
  "start_date": "2025-01-01",
  "end_date": "2025-01-31",
  "sheet_id": "optional_sheet_id"
}
```

**Response:**
```json
{
  "job_id": "uuid-here",
  "status": "running"
}
```

#### `GET /api/events/{job_id}`
Server-Sent Events stream для реального часу прогресу

**Events:**
- `log`: Текстові повідомлення прогресу
- `progress`: JSON об'єкти з метриками

#### `GET /api/config`
Отримати поточну конфігурацію

#### `POST /api/config`
Оновити конфігурацію (змінні .env)

#### `GET /api/students`
Отримати дані студентів з базою знань

**Query params:**
- `start_date`: Дата початку (YYYY-MM-DD)
- `end_date`: Дата кінця (YYYY-MM-DD)
- `enrich`: Збагачення даними з AlfaCRM (true/false)

**Response:**
```json
{
  "students": [...],
  "count": 42
}
```

#### `POST /api/download-excel`
Експорт даних у Excel

**Request:**
```json
{
  "data_type": "students",
  "start_date": "2025-01-01",
  "end_date": "2025-01-31"
}
```

Повна документація доступна на `/docs` (Swagger UI)

## 🧪 Тестування

```bash
# Запуск всіх тестів
pytest

# З покриттям коду
pytest --cov=app --cov-report=html

# Тільки unit тести
pytest tests/unit/

# Інтеграційні тести
pytest tests/integration/
```

## 📊 Структура даних

### Google Sheets

**Аркуш "Insights":**
- `date_start`, `date_stop`: Період метрик
- `campaign_id`, `campaign_name`: Інформація про кампанію
- `impressions`, `clicks`, `spend`: Основні метрики
- `reach`, `cpc`, `cpm`, `ctr`: Ефективність
- `objective`: Мета кампанії

**Аркуш "Leads":**
- `id`, `created_time`: Ідентифікація ліда
- `page_id`, `form_id`: Джерело ліда
- `crm_status`, `crm_stage`: Статус в CRM
- `contact_phone`, `contact_email`: Контактні дані
- `raw_fields_json`: Повні дані форми

**Аркуш "Students" (33 поля):**
- Посилання на рекламну кампанію
- Дата та період аналізу
- Витрачений бюджет
- Кількість лідів та їх розподіл
- Конверсійні метрики
- Фінансові показники

### База даних (SQLite)

**Таблиця `runs`:**
- `id`: UUID запуску
- `start_date`, `end_date`: Період даних
- `status`: running/completed/failed
- `creatives_count`, `students_count`, `teachers_count`: Статистика
- `created_at`, `completed_at`: Часові мітки
- `error_message`: Опис помилки (якщо є)
- `logs`: JSON масив логів виконання

## 🔧 Troubleshooting

### Помилка: "Meta API rate limit exceeded"
**Рішення:** Додайте затримки між запитами або збільште затримку в `app/connectors/meta.py`

### Помилка: "Google Sheets API permission denied"
**Рішення:** Перевірте що Service Account має доступ до таблиці (Editor role)

### Помилка: "CRM connection timeout"
**Рішення:** Перевірте CORS налаштування та API ключі CRM систем

### Frontend не завантажується
**Рішення:**
1. Перевірте що зібрали frontend: `cd web && npm run build`
2. Перевірте що FastAPI знаходить файли у `web/dist/`
3. Очистіть кеш браузера (Ctrl+Shift+R)

### База даних locked
**Рішення:** SQLite не підтримує конкурентний запис. Для production використовуйте PostgreSQL

## 🛠️ Development

### Структура проекту

```
ecademy/
├── app/                    # Backend (FastAPI)
│   ├── connectors/         # API коннектори
│   │   ├── meta.py         # Meta Marketing API
│   │   ├── sheets.py       # Google Sheets
│   │   ├── crm.py          # CRM інтеграції
│   │   └── excel.py        # Excel експорт
│   ├── database.py         # SQLite база даних
│   ├── mapping.py          # Mapping конфігурація
│   └── main.py             # FastAPI додаток
├── web/                    # Frontend (React)
│   ├── src/
│   │   ├── App.tsx         # Головний компонент
│   │   ├── StudentsTable.tsx  # Таблиця студентів
│   │   └── api.ts          # API клієнт
│   └── package.json
├── config/
│   └── mapping.json        # Field mapping конфігурація
├── tests/                  # Тести
├── .env.example            # Шаблон змінних середовища
├── requirements.txt        # Python залежності
├── requirements-dev.txt    # Dev залежності
└── docker-compose.yml      # Docker конфігурація
```

### Code Style

Python:
```bash
# Форматування
black app/ tests/

# Лінтинг
flake8 app/ tests/

# Type checking
mypy app/
```

TypeScript/React:
```bash
cd web

# Форматування
npm run format

# Лінтинг
npm run lint
```

### Pre-commit Hooks

```bash
pre-commit install
```

Автоматично виконується перед кожним commit:
- Форматування коду (black, prettier)
- Лінтинг (flake8, eslint)
- Type checking
- Тестування

## 🚢 Deployment

### Docker Production

```bash
# Build
docker-compose -f docker-compose.prod.yml build

# Deploy
docker-compose -f docker-compose.prod.yml up -d

# Logs
docker-compose logs -f app
```

### Kubernetes

Див. `k8s/` директорію для Kubernetes manifests

### Environment Variables (Production)

Обов'язково встановіть у production:
- `API_KEYS`: Безпечні API ключі
- `ALLOWED_ORIGINS`: Домени фронтенду
- `ALLOWED_HOSTS`: Довірені хости
- `DATABASE_URL`: PostgreSQL (замість SQLite)

## 📝 Changelog

### v1.0.0 (2025-10-01)
- ✅ Експорт студентів у Excel з 33 полями
- ✅ Форматування Excel (заголовки, відсотки, валюта)
- ✅ Історія запусків з базою даних
- ✅ API authentication через ключі
- ✅ React UI з Material-UI
- ✅ Real-time прогрес через SSE

### v0.9.0 (2025-09-15)
- Початкова версія з базовою функціональністю

## 🤝 Contributing

Дякуємо за інтерес до проекту! Див. [CONTRIBUTING.md](CONTRIBUTING.md) для деталей.

### Основні правила:
1. Fork репозиторій
2. Створіть feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit зміни (`git commit -m 'Add some AmazingFeature'`)
4. Push до branch (`git push origin feature/AmazingFeature`)
5. Створіть Pull Request

## 📄 License

Цей проект ліцензовано під MIT License - див. [LICENSE](LICENSE) файл для деталей.

## 👥 Authors

- **eCademy Team** - *Initial work*

## 🙏 Acknowledgments

- FastAPI за чудовий фреймворк
- Meta Marketing API за доступ до даних
- Material-UI за UI компоненти
- Всім контрибюторам проекту

## 📞 Support

Якщо у вас є питання або проблеми:
- Відкрийте [Issue](https://github.com/your-username/ecademy/issues)
- Створіть Pull Request для покращень

---

**Зроблено з ❤️ для автоматизації маркетингу**
