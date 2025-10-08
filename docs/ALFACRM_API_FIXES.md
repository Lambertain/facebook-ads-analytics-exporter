# AlfaCRM API - Исправления и актуальная документация

## Проблема и Решение

**Проблема:** Исходный код использовал неверные пути API:
- `/api/v2/auth/login` (неверно)
- `/api/v2/student/index` (неверно)

**Решение:** Правильные пути API:
- `/v2api/auth/login` ✅
- `/v2api/customer/index` ✅

## Исправленная Аутентификация

```python
def alfacrm_auth_get_token() -> str:
    base_url = os.getenv("ALFACRM_BASE_URL")
    email = os.getenv("ALFACRM_EMAIL")
    api_key = os.getenv("ALFACRM_API_KEY")
    url = base_url.rstrip('/') + "/v2api/auth/login"  # ИСПРАВЛЕНО

    resp = requests.post(url, json={"email": email, "api_key": api_key})
    data = resp.json()
    return data.get("token")
```

## Получение Студентов (Customers)

**Важно:** В AlfaCRM студенты называются "customers", а не "students".

```python
def alfacrm_list_students(page: int = 1, page_size: int = 200) -> Dict[str, Any]:
    token = alfacrm_auth_get_token()
    base_url = os.getenv("ALFACRM_BASE_URL")
    url = base_url.rstrip('/') + "/v2api/customer/index"  # ИСПРАВЛЕНО

    payload = {
        "branch_ids": [1],  # ИСПРАВЛЕНО: используем branch_ids вместо company_id
        "page": page,
        "page_size": page_size,
    }

    resp = requests.post(url, headers={"X-ALFACRM-TOKEN": token}, json=payload)
    return resp.json()
```

## Структура Данных Студента

Каждый студент содержит:

| Поле | Тип | Описание |
|------|-----|----------|
| `id` | int | Уникальный ID студента |
| `name` | str | ФИО студента |
| `phone` | list[str] | Массив телефонов |
| `email` | list[str] | Массив email адресов |
| `lead_status_id` | int | ID статуса лида (1-7+) |
| `study_status_id` | int | ID статуса обучения |
| `branch_ids` | list[int] | ID филиалов |
| `teacher_ids` | list[int] | ID преподавателей |
| `is_study` | int | 0 или 1 - учится ли |
| `balance` | str | Баланс счета |
| `custom_*` | any | Кастомные поля |

## Пример Ответа API

```json
{
  "total": 1365,
  "count": 50,
  "page": 1,
  "items": [
    {
      "id": 23219,
      "branch_ids": [1],
      "teacher_ids": [1727],
      "name": "*Дядюрко Анфія (Іщенко Регіна)",
      "is_study": 1,
      "study_status_id": 1,
      "lead_status_id": 4,
      "phone": ["+380(97)047-32-99"],
      "email": [],
      "custom_email": "",
      "custom_yazik": "НМК",
      "custom_urovenvladenwoo": "A21",
      "created_at": "2025-07-31 09:44:10"
    }
  ]
}
```

## Статусы Лидов (lead_status_id)

На основе существующих данных выявлены следующие статусы:

| ID | Вероятное Значение |
|----|-------------------|
| 1  | Новый лид |
| 2  | Установлен контакт |
| 3  | В обработке |
| 4  | Назначен пробный урок |
| 5  | Проведен пробный |
| 6  | Продажа / Купили |
| 7  | Отказ / Архив |

**Примечание:** Точное соответствие ID и названий нужно уточнить у клиента или через интерфейс AlfaCRM.

## Кастомные Поля eCademy

Специфичные поля для проекта eCademy:

- `custom_email` - альтернативный email
- `custom_yazik` - язык обучения (НМК = немецкий)
- `custom_urovenvladenwoo` - уровень владения (A21, B1, и т.д.)
- `custom_ads_comp` - рекламная кампания
- `custom_try_lessons` - дата пробного урока
- `custom_schedule` - расписание занятий
- `custom_gorodstvaniya` - место проживания
- `custom_age_` - возрастная категория (Підліток, Дорослий и т.д.)

## Тестирование API

```bash
# 1. Получить токен
curl -X POST "https://ecademyua.alfacrm.com/v2api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "ruslan9699@icloud.com", "api_key": "21ad68a5-8d2c-11ed-83fb-3cecef7ebd64"}'

# Ответ: {"token":"6b55c93f8c36aa57709f8a7160ef1731"}

# 2. Получить студентов
curl -X POST "https://ecademyua.alfacrm.com/v2api/customer/index" \
  -H "Content-Type: application/json" \
  -H "X-ALFACRM-TOKEN: 6b55c93f8c36aa57709f8a7160ef1731" \
  -d '{"branch_ids": [1], "page": 1, "page_size": 3}'
```

## Изменения в Коде

Файл: `app/connectors/crm.py`

**Строка 452:** `/api/v2/auth/login` → `/v2api/auth/login`
**Строка 475:** `/api/v2/company/index` → `/v2api/company/index`
**Строка 498:** `/api/v2/student/index` → `/v2api/customer/index`
**Строка 500:** `"company_id": int(company_id)` → `"branch_ids": [int(company_id)]`

## Следующие Шаги

1. ✅ Исправлены пути API
2. ✅ Протестирована аутентификация
3. ✅ Получены реальные данные студентов
4. ⏳ Создать модуль для трекинга статусов лидов
5. ⏳ Интегрировать с Meta Leads API
6. ⏳ Реализовать подсчет +1 для каждого статуса
