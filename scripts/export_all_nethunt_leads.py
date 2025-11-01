"""
Скрипт для экспорта ВСЕХ лидов из NetHunt CRM (активные + архивные).

Использует NetHunt API с пагинацией по времени (since параметр).
Экспортирует все данные в Excel файл с полной информацией о каждом лиде.

Автор: Archon Implementation Engineer
Дата: 2025-11-01
"""
import os
import sys
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from dotenv import load_dotenv
import requests
import pandas as pd
from pathlib import Path

# Добавляем путь к app для импорта
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

# Конфигурация
NETHUNT_AUTH = os.getenv("NETHUNT_BASIC_AUTH")
NETHUNT_FOLDER_ID = os.getenv("NETHUNT_FOLDER_ID")
TIMEOUT = 30
MAX_RETRIES = 3


def nethunt_get_all_records(
    folder_id: str,
    since_date: Optional[str] = None,
    limit_per_request: int = 1000
) -> List[Dict[str, Any]]:
    """
    Получить ВСЕ записи из NetHunt папки включая архивные.

    Использует пагинацию по времени через параметр 'since'.
    Итерирует пока не получит все записи с самой ранней даты.

    Args:
        folder_id: ID папки NetHunt
        since_date: Начальная дата в ISO формате (по умолчанию 2015-01-01)
        limit_per_request: Макс записей за один запрос (макс 1000)

    Returns:
        Список всех записей из NetHunt
    """
    if not NETHUNT_AUTH:
        raise RuntimeError("NETHUNT_BASIC_AUTH не настроен в .env")

    # Устанавливаем начальную дату для получения ВСЕХ исторических записей
    if not since_date:
        since_date = "2015-01-01T00:00:00Z"

    logger.info(f"Начинаю получение всех записей с {since_date}")
    logger.info(f"Folder ID: {folder_id}")
    logger.info(f"Limit per request: {limit_per_request}")

    all_records = []
    current_since = since_date
    page = 1

    while True:
        logger.info(f"Страница {page}: получаю записи с since={current_since}")

        # Запрос к NetHunt API
        url = f"https://nethunt.com/api/v1/zapier/triggers/updated-record/{folder_id}"
        headers = {
            "Authorization": NETHUNT_AUTH,
            "Accept": "application/json"
        }
        params = {
            "since": current_since,
            "limit": min(limit_per_request, 1000)  # Макс 1000 по документации
        }

        try:
            response = requests.get(
                url,
                headers=headers,
                params=params,
                timeout=TIMEOUT
            )

            logger.info(f"Response status: {response.status_code}")

            if response.status_code != 200:
                logger.error(f"API error: {response.status_code} - {response.text}")
                break

            data = response.json()

            # NetHunt может возвращать массив напрямую или {records: [...]}
            if isinstance(data, dict):
                records = data.get("records", [])
            elif isinstance(data, list):
                records = data
            else:
                logger.warning(f"Неожиданный формат ответа: {type(data)}")
                break

            records_count = len(records)
            logger.info(f"Получено записей: {records_count}")

            if records_count == 0:
                logger.info("Больше нет записей, завершаю")
                break

            # Добавляем записи в общий список
            all_records.extend(records)

            # Если получили меньше чем limit - это последняя страница
            if records_count < limit_per_request:
                logger.info(f"Получено {records_count} < {limit_per_request}, это последняя страница")
                break

            # Обновляем since для следующего запроса
            # Используем updated_at последней записи
            last_record = records[-1]
            last_updated = last_record.get("updated_at") or last_record.get("updatedAt")

            if not last_updated:
                logger.warning("У последней записи нет поля updated_at, останавливаю пагинацию")
                break

            # Добавляем 1 миллисекунду чтобы не получить ту же запись снова
            try:
                last_dt = datetime.fromisoformat(last_updated.replace('Z', '+00:00'))
                next_dt = last_dt + timedelta(milliseconds=1)
                current_since = next_dt.isoformat().replace('+00:00', 'Z')
            except Exception as e:
                logger.error(f"Не удалось парсить дату {last_updated}: {e}")
                break

            page += 1

            # Безопасность: макс 100 страниц
            if page > 100:
                logger.warning("Достигнут лимит 100 страниц, останавливаю")
                break

        except requests.exceptions.Timeout:
            logger.error(f"Timeout при запросе страницы {page}")
            break
        except Exception as e:
            logger.error(f"Ошибка при получении страницы {page}: {type(e).__name__}: {e}")
            break

    logger.info(f"Всего получено записей: {len(all_records)}")
    return all_records


def export_to_excel(
    records: List[Dict[str, Any]],
    output_path: str
) -> None:
    """
    Экспорт записей NetHunt в Excel файл.

    Args:
        records: Список записей из NetHunt
        output_path: Путь к выходному Excel файлу
    """
    if not records:
        logger.warning("Нет записей для экспорта")
        return

    logger.info(f"Начинаю экспорт {len(records)} записей в Excel")

    # Преобразуем вложенные структуры в плоский формат
    flat_records = []

    for record in records:
        flat_record = {
            "id": record.get("id"),
            "name": record.get("name"),
            "email": record.get("email"),
            "phone": record.get("phone"),
            "status": record.get("status", ""),
            "created_at": record.get("created_at") or record.get("createdAt"),
            "updated_at": record.get("updated_at") or record.get("updatedAt"),
        }

        # Добавляем кастомные поля из fields
        fields = record.get("fields", {})
        if isinstance(fields, dict):
            for field_name, field_value in fields.items():
                # Преобразуем field_name в безопасное название колонки
                safe_name = field_name.replace(" ", "_").lower()
                flat_record[f"field_{safe_name}"] = field_value

        # Добавляем полную запись как JSON для справки
        flat_record["raw_json"] = json.dumps(record, ensure_ascii=False)

        flat_records.append(flat_record)

    # Создаем DataFrame
    df = pd.DataFrame(flat_records)

    # Сортируем по дате создания
    if "created_at" in df.columns:
        df = df.sort_values("created_at")

    # Создаем директорию если не существует
    output_dir = os.path.dirname(output_path)
    if output_dir:
        Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Экспортируем в Excel
    df.to_excel(output_path, index=False, engine='openpyxl')

    logger.info(f"Экспорт завершен: {output_path}")
    logger.info(f"Записей: {len(df)}")
    logger.info(f"Колонок: {len(df.columns)}")

    # Показываем первые колонки
    logger.info(f"Колонки: {list(df.columns[:10])}...")


def main():
    """Главная функция скрипта."""
    logger.info("=" * 80)
    logger.info("NetHunt CRM - Full Export (Active + Archived)")
    logger.info("=" * 80)

    # Проверяем конфигурацию
    if not NETHUNT_AUTH:
        logger.error("NETHUNT_BASIC_AUTH не настроен в .env")
        return

    if not NETHUNT_FOLDER_ID:
        logger.error("NETHUNT_FOLDER_ID не настроен в .env")
        logger.info("Получите folder_id из NetHunt CRM Settings > API")
        return

    logger.info(f"Auth configured: Yes")
    logger.info(f"Folder ID: {NETHUNT_FOLDER_ID}")

    # Получаем все записи
    try:
        all_records = nethunt_get_all_records(
            folder_id=NETHUNT_FOLDER_ID,
            since_date="2015-01-01T00:00:00Z"
        )

        if not all_records:
            logger.warning("Не получено ни одной записи из NetHunt")
            return

        # Экспортируем в Excel
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"exports/nethunt_all_leads_{timestamp}.xlsx"

        export_to_excel(all_records, output_path)

        logger.info("=" * 80)
        logger.info("Экспорт завершен успешно!")
        logger.info("=" * 80)

    except Exception as e:
        logger.error(f"Ошибка при экспорте: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
