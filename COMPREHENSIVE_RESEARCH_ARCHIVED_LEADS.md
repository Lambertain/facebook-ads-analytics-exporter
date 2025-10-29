# COMPREHENSIVE RESEARCH: Получение архивных лидов из Alfa CRM API

**Дата**: 2025-10-29
**Проект**: eCademy
**Статус**: Завершено

## 1. ПРОБЛЕМА

Найдено: 3,592 активных лидов через API `/v2api/customer/index`
Требуется: Получить 7,788 архивных лидов
Статус: **АРХИВНЫЕ ЛИДЫ НЕ ДОСТУПНЫ ЧЕРЕЗ ПУБЛИЧНЫЙ API**

## 2. ОСНОВНЫЕ ENDPOINTS ALFA CRM V2 API

| Endpoint | Метод | Параметры | Статус |
|----------|-------|-----------|--------|
| `/v2api/auth/login` | POST | email, api_key | ✅ РАБОТАЕТ |
| `/v2api/customer/index` | POST | branch_ids, page, page_size, is_study | ✅ РАБОТАЕТ |
| `/v2api/company/index` | GET | X-ALFACRM-TOKEN | ✅ РАБОТАЕТ |
| `/v2api/lead-status/index` | POST | branch_id | ✅ РАБОТАЕТ |
| `/v2api/lead-reject/index` | POST | branch_id | ✅ РАБОТАЕТ |
| `/v2api/customer-reject/index` | POST | branch_id | ✅ РАБОТАЕТ |

## 3. КЛЮЧЕВЫЕ ПОЛЯ ОТВЕТА API

- `lead_reject_id` - ID причины отклонения лида
- `customer_reject_id` - ID причины отклонения клиента
- **КРИТИЧНО**: Оба поля ВСЕГДА `null` в полученных записях!

## 4. ПРОТЕСТИРОВАННЫЕ ПАРАМЕТРЫ

### Параметры которые РАБОТАЮТ:
- `branch_ids: [1]` ✅
- `is_study: 0|1|2` ✅
- `page` ✅
- `page_size` ✅

### Параметры которые НЕ РАБОТАЮТ:
- `archived: True/1` ❌
- `is_archive: True/1` ❌
- `lead_reject_id: значение` ❌
- `customer_reject_id: значение` ❌
- Все варианты фильтрации архива ❌

## 5. РЕЗУЛЬТАТЫ ЭКСПОРТА

```
Файл: alfacrm_leads_export_20251029_144642.csv
Статистика:
- Всего записей: 6,171
- Уникальных: 6,171
- Лидов (is_study=0): 2,100
- Студентов (is_study=1): 1,429
- Комбинированные (is_study=2+): 2,642

Архивных найдено: 0
```

## 6. ВЕРСИЯ API

- Используется: **/v2api/** (v2)
- v1api и v3api не поддерживаются

## 7. РЕКОМЕНДАЦИИ

1. Экспортировать доступные 3,592 активных лидов
2. Обратиться в техподдержку AlfaCRM
3. Если не поможет - использовать reverse engineering UI
4. Рассмотреть альтернативные методы доступа (DB, webhooks)

