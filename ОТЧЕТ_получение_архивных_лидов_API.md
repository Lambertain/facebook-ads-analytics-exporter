# Отчет: Получение архивных лидов из Альфа СРМ через API

**Дата:** 2025-10-28
**Исследование:** Возможность получения лидов из архива через AlfaCRM API
**Статус:** ✅ РЕШЕНИЕ НАЙДЕНО

---

## 🎯 Вопрос клиента

> "Постучи через апи в Альфа СРМ и посмотри мы можем забирать всех лидов именно из архива?"

---

## ✅ КРАТКИЙ ОТВЕТ

**ДА, МЫ МОЖЕМ ПОЛУЧАТЬ АРХИВНЫЕ ЛИДЫ НАПРЯМУЮ ЧЕРЕЗ API!**

Метод: Использовать параметр `lead_status_id: 39` в запросе к `/v2api/customer/index`

---

## 📊 Результаты тестирования

### Тест 1: Проверка параметров фильтрации

| Параметр | Работает? | Результат |
|----------|-----------|-----------|
| `lead_status_id: 39` | ✅ ДА | Возвращает ТОЛЬКО архивные лиды |
| `lead_status_ids: [39]` | ❌ НЕТ | Игнорируется, возвращает всех |
| `status: "archived"` | ❌ НЕТ | Игнорируется, возвращает всех |
| Клиентская фильтрация | ✅ ДА | Всегда работает как fallback |

### Тест 2: Получение только архивных лидов

```
Результат запроса с lead_status_id=39:
✓ Получено: 50 архивных лидов
✓ Всего архивных в системе: 50
✓ Все лиды имеют lead_status_id=39
```

**Примеры архивных лидов:**
- ID: 23813, Имя: Жилiна Галина, Телефон: +380(93)744-56-52
- ID: 25552, Имя: Жмуренко Еліна, Телефон: +380(99)238-03-61
- ID: 28371, Имя: Заяць Володимир, Телефон: +380(97)413-78-43

---

## 🔍 ВАЖНОЕ ОТКРЫТИЕ: custom_ads_comp

### Что обнаружили:

1. **custom_ads_comp НЕ является индикатором архива!**
   - В старом исследовании (ИССЛЕДОВАНИЕ_Archive_ЦА_классификация.md) было сказано что архив определяется через `custom_ads_comp == 'архів'`
   - НО в реальности из 50 архивных лидов (lead_status_id=39):
     - 0 лидов имеют custom_ads_comp='архів'
     - 50 лидов имеют custom_ads_comp с названием кампании

2. **custom_ads_comp хранит название кампании Facebook:**
   ```
   Примеры значений:
   - "Shkolnik_GERM_30.07_2"
   - "Shkolnik_UKR_23.07"
   - "Student/Анатолій/ЛФ/Україна,30-55,Ж,Advantage+/23.09.2025"
   ```

3. **Правильный способ определения архива:**
   ```python
   # ✅ ПРАВИЛЬНО - по lead_status_id
   is_archived = (lead.get("lead_status_id") == 39)

   # ❌ НЕПРАВИЛЬНО - по custom_ads_comp (не работает!)
   is_archived = (lead.get("custom_ads_comp") == "архів")
   ```

---

## 💡 Рекомендуемое решение

### Вариант 1: Серверная фильтрация (РЕКОМЕНДУЕТСЯ)

**Преимущества:**
- ✅ Получаем только архивные лиды
- ✅ Экономия трафика (не загружаем всех студентов)
- ✅ Быстрее работает
- ✅ Поддержка пагинации

**Код для реализации:**

```python
# app/connectors/crm.py

@retry(
    stop=stop_after_attempt(CRM_MAX_RETRIES),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type((requests.exceptions.Timeout, requests.exceptions.ConnectionError)),
    before_sleep=before_sleep_log(logger, logging.WARNING)
)
def alfacrm_list_archive_students(page: int = 1, page_size: int = 200) -> Dict[str, Any]:
    """
    Получить ТОЛЬКО архивные студенты из AlfaCRM.

    Использует фильтр lead_status_id=39 для получения только архивных лидов.

    Args:
        page: Номер страницы (начиная с 1)
        page_size: Количество записей на страницу (макс 200)

    Returns:
        {
            "items": [...],  # Список архивных студентов
            "count": N       # Общее количество архивных студентов
        }
    """
    token = alfacrm_auth_get_token()
    base_url = os.getenv("ALFACRM_BASE_URL")
    company_id = os.getenv("ALFACRM_COMPANY_ID")

    if not company_id:
        raise RuntimeError("ALFACRM_COMPANY_ID is not set")

    url = base_url.rstrip('/') + "/v2api/customer/index"
    payload = {
        "branch_ids": [int(company_id)],
        "page": page,
        "page_size": page_size,
        "lead_status_id": 39  # Фильтр для архивных лидов
    }

    try:
        resp = requests.post(
            url,
            headers={"X-ALFACRM-TOKEN": token},
            json=payload,
            timeout=CRM_TIMEOUT
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.error(f"AlfaCRM list archive students failed: {type(e).__name__}: {e}")
        raise
```

**Использование:**

```python
# Получить все архивные лиды
all_archive_leads = []
page = 1

while True:
    response = alfacrm_list_archive_students(page=page, page_size=200)
    items = response.get("items", [])

    if not items:
        break

    all_archive_leads.extend(items)

    # Проверяем есть ли еще страницы
    total = response.get("count", 0)
    if len(all_archive_leads) >= total:
        break

    page += 1

print(f"Загружено {len(all_archive_leads)} архивных лидов")
```

### Вариант 2: Клиентская фильтрация (текущий подход)

**Когда использовать:**
- Если нужны ВСЕ студенты для других целей
- Как fallback если серверная фильтрация не работает

**Код (уже реализован):**

```python
# app/services/alfacrm_tracking.py (строка 324)

# Получить всех студентов
all_students = alfacrm_list_students(page=1, page_size=500)
students = all_students.get("items", [])

# Отфильтровать архивные на стороне клиента
archive_leads = [
    student for student in students
    if student.get("lead_status_id") == 39  # ✅ Правильно!
]

# НЕ ИСПОЛЬЗУЙТЕ custom_ads_comp для фильтрации архива!
# archive_leads = [s for s in students if s.get("custom_ads_comp") == "архів"]  # ❌ НЕ РАБОТАЕТ
```

---

## 🔧 Необходимые изменения в коде

### 1. Исправить проверку архива в alfacrm_tracking.py

**Текущий код (строка 324):**
```python
# ПРОВЕРКА НА АРХИВ: Сначала проверяем custom_ads_comp
custom_ads_comp = student.get("custom_ads_comp", "")
if custom_ads_comp == "архів":
    archived_count += 1
    # ...
```

**Исправленный код:**
```python
# ПРОВЕРКА НА АРХИВ: По lead_status_id
lead_status_id = student.get("lead_status_id")
if lead_status_id == 39:  # Архивный статус
    archived_count += 1
    # ...
```

### 2. Добавить новую функцию в crm.py

Добавить функцию `alfacrm_list_archive_students()` как показано выше.

### 3. Обновить документацию

Обновить ИССЛЕДОВАНИЕ_Archive_ЦА_классификация.md с новыми данными:
- custom_ads_comp хранит название кампании, а НЕ статус архива
- Правильный способ определения архива - по lead_status_id=39

---

## 📋 Сравнение методов

| Критерий | Серверная фильтрация | Клиентская фильтрация |
|----------|---------------------|----------------------|
| **Скорость** | ⚡ Быстро (только архив) | 🐌 Медленно (все студенты) |
| **Трафик** | 💚 Минимальный | 🔴 Весь список студентов |
| **Простота** | 😊 Простая | 😊 Простая |
| **Надежность** | ✅ Работает | ✅ Всегда работает |
| **Пагинация** | ✅ Поддерживается | ⚠️ Нужна для всех |

---

## 🎓 Выводы и рекомендации

### Что узнали:

1. ✅ **Можем получать архивные лиды напрямую** через параметр `lead_status_id: 39`
2. ✅ **API поддерживает фильтрацию** по lead_status_id
3. ⚠️ **custom_ads_comp НЕ для архива** - это поле для названия кампании Facebook
4. ✅ **Правильный способ** - использовать `lead_status_id == 39`

### Рекомендации:

1. **Внедрить серверную фильтрацию** - добавить функцию `alfacrm_list_archive_students()`
2. **Исправить текущий код** - заменить проверку `custom_ads_comp == "архів"` на `lead_status_id == 39`
3. **Обновить документацию** - исправить информацию о custom_ads_comp
4. **Использовать пагинацию** - для больших объемов архивных лидов

### Приоритет:

**🔴 ВЫСОКИЙ** - Текущая логика в alfacrm_tracking.py:324 использует НЕПРАВИЛЬНЫЙ метод фильтрации (custom_ads_comp). Это может привести к тому что архивные лиды не учитываются!

---

## 📂 Созданные тестовые скрипты

1. **test_archive_api_filtering.py** - Проверка различных методов фильтрации
2. **test_get_only_archive_leads.py** - Получение только архивных лидов
3. **test_archive_status.py** - Уже существующий тест (устаревший подход)

**Запуск тестов:**
```bash
cd D:\Automation\Development\projects\ecademy
python test_archive_api_filtering.py
python test_get_only_archive_leads.py
```

---

## 🔗 Связанные документы

- `ИССЛЕДОВАНИЕ_Archive_ЦА_классификация.md` - Предыдущее исследование (требует обновления)
- `BUSINESS_LOGIC.md` - Бизнес-логика проекта
- `app/services/alfacrm_tracking.py` - Основной файл трекинга (требует исправления)
- `app/connectors/crm.py` - Коннектор AlfaCRM (добавить новую функцию)

---

**Автор отчета:** Claude Code Assistant
**Дата:** 2025-10-28
