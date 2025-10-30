"""
eCademy Application Settings

Центральна конфігурація для всіх сервісів та модулів проекту.
"""
import os
from typing import Dict

# ============================================================================
# NetHunt CRM Configuration
# ============================================================================

# NetHunt Status Mapping для вчителів - маппінг статусів NetHunt в назви стовпців таблиці
# Базується на 49-колонковій специфікації (колонки I-AG)
# ВАЖЛИВО: Ці статуси потрібно уточнити у клієнта після отримання реальних даних NetHunt
NETHUNT_STATUS_MAPPING: Dict[str, str] = {
    # === ЛІДИ В ПРОЦЕСІ ОПРАЦЮВАННЯ (Колонки I-U) ===

    # Початкові статуси
    "unprocessed": "Не розібрані ліди",  # Column I
    "in_work": "Взяті в роботу",  # Column J

    # Контакт та дзвони
    "contact_target": "Контакт (ЦА)",  # Column K
    "no_answer_non_target": "НЕ дозвон (не ЦА)",  # Column L

    # Співбесіди
    "interview_target": "Співбесіда (ЦА)",  # Column M
    "interview_done_target": "СП проведено (ЦА)",  # Column N
    "interview_no_show": "Не з'явився на СП",  # Column O

    # Затвердження завучем
    "zavuch_approved": "Завуч затвердив кандидата (в процесі опрацювання) ЦА",  # Column P
    "zavuch_rejected": "Завуч не затвердив кандидата (відмовився) ЦА",  # Column Q

    # Переговори та стажування
    "negotiation": "Переговори (в процесі опрацювання) ЦА",  # Column R
    "internship": "Стажування ЦА",  # Column S
    "no_students": "Не має учнів ЦА",  # Column T

    # Фінальний успішний статус
    "teacher": "Вчитель ЦА",  # Column U - FINAL SUCCESS

    # === КАТЕГОРІЇ ВТРАТ ТА ВІДМОВ (Колонки V-AG) ===

    # Втрати цільової аудиторії
    "lost_rejected_target": "Втрачений (відмовився) ЦА",  # Column V
    "reserve_internship": "Резерв стажування (в процесі опрацювання) ЦА",  # Column W
    "reserve_call": "Резерв дзвінок (в процесі опрацювання) ЦА",  # Column X
    "offboarding_rejected": "Офбординг (відмовився) ЦА",  # Column Y
    "quit_rejected": "Звільнився (відмовився) ЦА",  # Column Z

    # Втрати нецільової аудиторії
    "lost_non_target": "Втрачений не цільовий (не цільовий) НЕ ЦА",  # Column AA
    "lost_no_answer_non_target": "Втрачений недозвон (не цільовий) НЕ ЦА",  # Column AB
    "lost_not_relevant": "Втрачений не актуально (не цільовий) НЕ ЦА",  # Column AC

    # Специфічні причини втрат
    "lost_low_salary": "Втрачений мала зп (відмовився) ЦА",  # Column AD
    "lost_forever": "Втрачений назавжди (не цільовий) НЕ ЦА",  # Column AE
    "lost_check_viber": "Втрачений перевірити Вайбер (не цільовий) НЕ ЦА",  # Column AF
    "lost_ignores": "Втрачений ігнорує (відмовився) ЦА",  # Column AG
}

# NetHunt API Configuration
NETHUNT_BASE_URL = "https://nethunt.com/api/v1/zapier"
NETHUNT_AUTH = os.getenv("NETHUNT_BASIC_AUTH")
NETHUNT_TIMEOUT = int(os.getenv("NETHUNT_TIMEOUT", "15"))
NETHUNT_FOLDER_ID = os.getenv("NETHUNT_FOLDER_ID", "default")

# ============================================================================
# AlfaCRM Configuration
# ============================================================================

# AlfaCRM Status Mapping - маппінг статусів AlfaCRM в назви стовпців таблиці
ALFACRM_STATUS_MAPPING: Dict[int, str] = {
    11: "Недодзвон",
    10: "Недозвон 2",
    27: "Недозвон 3",
    1: "Вст контакт невідомо",
    32: "Вст контакт зацікавлений",
    26: "Зник після контакту",
    12: "Розмовляли, чекаємо відповідь",
    6: "Чекає пробного",
    2: "Призначено пробне",
    3: "Проведено пробне",
    5: "Не відвідав пробне",
    9: "Чекаємо оплату",
    4: "Отримана оплата",
    29: "Сплатить через 2 тижні >",
    25: "Передзвонити через 2 тижні",
    30: "Передзвон через місяць",
    31: "Передзвон 2 місяці і більше",
    8: "Опрацювати заперечення",
    # ... (інші статуси)
}

# ============================================================================
# Application Configuration
# ============================================================================

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = os.getenv(
    "LOG_FORMAT",
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Performance
DEFAULT_PAGE_SIZE = int(os.getenv("DEFAULT_PAGE_SIZE", "100"))
MAX_PAGE_SIZE = int(os.getenv("MAX_PAGE_SIZE", "1000"))

# Retry Configuration
RETRY_MAX_ATTEMPTS = int(os.getenv("RETRY_MAX_ATTEMPTS", "3"))
RETRY_EXPONENTIAL_BASE = int(os.getenv("RETRY_EXPONENTIAL_BASE", "2"))
RETRY_MIN_WAIT = int(os.getenv("RETRY_MIN_WAIT", "2"))
RETRY_MAX_WAIT = int(os.getenv("RETRY_MAX_WAIT", "10"))

# Validation Configuration
# Строга валідація: якщо True, невалідні дані зупиняють виконання
# Development режим: false (продовжує з попередженням)
# Production режим: true (зупиняє виконання)
NETHUNT_STRICT_VALIDATION = os.getenv("NETHUNT_STRICT_VALIDATION", "false").lower() == "true"
