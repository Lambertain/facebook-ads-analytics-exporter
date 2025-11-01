# NetHunt CRM - Full Export Script

Скрипт для экспорта **ВСЕХ** лидов из NetHunt CRM включая архивные записи за все время существования аккаунта.

## Возможности

- ✅ Получение ВСЕХ записей из NetHunt (активные + архивные)
- ✅ Пагинация по времени через `since` параметр
- ✅ Экспорт в Excel (.xlsx) с полной информацией
- ✅ Обработка всех кастомных полей NetHunt
- ✅ Сохранение raw JSON для каждой записи
- ✅ Логирование процесса получения данных

## Требования

### Зависимости Python

```bash
pip install -r requirements.txt
```

Основные зависимости:
- `requests` - HTTP запросы к NetHunt API
- `pandas` - обработка данных
- `openpyxl` - экспорт в Excel
- `python-dotenv` - загрузка переменных окружения

### Настройка .env файла

Создайте файл `.env` в корне проекта и добавьте:

```env
# NetHunt CRM Configuration
NETHUNT_BASIC_AUTH=Basic <your_base64_encoded_credentials>
NETHUNT_FOLDER_ID=<your_folder_id>
```

**Как получить NETHUNT_BASIC_AUTH:**
1. Зайдите в NetHunt CRM Settings > API
2. Создайте API ключ
3. Закодируйте `email:api_key` в base64
4. Добавьте `Basic ` перед закодированным значением

**Пример:**
```
echo -n "user@example.com:api_key_12345" | base64
# Результат: dXNlckBleGFtcGxlLmNvbTphcGlfa2V5XzEyMzQ1
# NETHUNT_BASIC_AUTH=Basic dXNlckBleGFtcGxlLmNvbTphcGlfa2V5XzEyMzQ1
```

**Как получить NETHUNT_FOLDER_ID:**
1. Зайдите в NetHunt CRM
2. Откройте нужную папку (folder)
3. Скопируйте ID из URL: `https://nethunt.com/folder/{folder_id}`

## Использование

### Запуск скрипта

```bash
cd D:\Automation\Development\projects\ecademy
python scripts\export_all_nethunt_leads.py
```

### Что происходит

1. **Валидация конфигурации** - проверка NETHUNT_BASIC_AUTH и NETHUNT_FOLDER_ID
2. **Получение записей** - пагинация через NetHunt API начиная с 2015-01-01
3. **Экспорт в Excel** - сохранение в `exports/nethunt_all_leads_{timestamp}.xlsx`

### Процесс работы

Скрипт использует пагинацию по времени:

```
Страница 1: since=2015-01-01T00:00:00Z → получено 1000 записей
Страница 2: since=2023-05-15T10:30:45Z → получено 1000 записей
Страница 3: since=2024-08-20T14:22:10Z → получено 534 записи
Завершено: всего 2534 записи
```

## Структура экспортированного Excel файла

### Основные колонки

- `id` - ID записи в NetHunt
- `name` - Имя контакта
- `email` - Email
- `phone` - Телефон
- `status` - Текущий статус
- `created_at` - Дата создания
- `updated_at` - Дата последнего обновления

### Кастомные поля

Все кастомные поля из NetHunt добавляются с префиксом `field_`:
- `field_company` - Компания
- `field_notes` - Заметки
- `field_source` - Источник лида
- и т.д.

### Дополнительно

- `raw_json` - Полная JSON запись для reference

## Примеры использования

### Экспорт за конкретный период

Откройте скрипт и измените `since_date`:

```python
all_records = nethunt_get_all_records(
    folder_id=NETHUNT_FOLDER_ID,
    since_date="2024-01-01T00:00:00Z"  # С 1 января 2024
)
```

### Изменение лимита записей за запрос

```python
all_records = nethunt_get_all_records(
    folder_id=NETHUNT_FOLDER_ID,
    limit_per_request=500  # По 500 записей за раз
)
```

## Ограничения NetHunt API

Согласно официальной документации NetHunt API:

- **Максимум записей за запрос:** 1000
- **Пагинация:** только по времени через `since` параметр
- **Нет offset/cursor:** невозможна классическая пагинация
- **Архивные записи:** получаются автоматически при использовании раннего `since`

## Troubleshooting

### Ошибка: "NETHUNT_BASIC_AUTH не настроен"

Проверьте:
1. Файл `.env` существует в корне проекта
2. Переменная `NETHUNT_BASIC_AUTH` правильно записана
3. Формат: `Basic <base64_encoded_credentials>`

### Ошибка: "API error: 401"

Причины:
- Неправильный NETHUNT_BASIC_AUTH
- Истек API ключ
- Email:API_key неправильно закодированы в base64

Решение: пересоздайте API ключ в NetHunt Settings

### Ошибка: "API error: 404"

Причина: неправильный NETHUNT_FOLDER_ID

Решение: проверьте ID папки в URL NetHunt CRM

### Получено 0 записей

Причины:
- Папка пустая
- Неправильный folder_id
- `since_date` позже всех записей

## Логи

Скрипт выводит подробные логи:

```
[INFO] ========================================
[INFO] NetHunt CRM - Full Export (Active + Archived)
[INFO] ========================================
[INFO] Auth configured: Yes
[INFO] Folder ID: abc123def456
[INFO] Начинаю получение всех записей с 2015-01-01T00:00:00Z
[INFO] Folder ID: abc123def456
[INFO] Limit per request: 1000
[INFO] Страница 1: получаю записи с since=2015-01-01T00:00:00Z
[INFO] Response status: 200
[INFO] Получено записей: 1000
...
[INFO] Всего получено записей: 2534
[INFO] Начинаю экспорт 2534 записей в Excel
[INFO] Экспорт завершен: exports/nethunt_all_leads_20251101_170530.xlsx
[INFO] Записей: 2534
[INFO] Колонок: 25
[INFO] ========================================
[INFO] Экспорт завершен успешно!
[INFO] ========================================
```

## Автор

Archon Implementation Engineer
Дата: 2025-11-01
Проект: eCademy - Facebook Ads Analytics
