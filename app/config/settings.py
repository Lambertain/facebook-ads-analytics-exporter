"""
eCademy Application Settings

Центральна конфігурація для всіх сервісів та модулів проекту.
"""
import os
from typing import Dict

# ============================================================================
# NetHunt CRM Configuration
# ============================================================================

# NetHunt Status Mapping - маппінг статусів NetHunt в назви стовпців таблиці
# ВАЖЛИВО: Ці статуси потрібно уточнити у клієнта після отримання реальних даних
NETHUNT_STATUS_MAPPING: Dict[str, str] = {
    "new": "Нові",
    "contacted": "Контакт встановлено",
    "qualified": "Кваліфіковані",
    "interview_scheduled": "Співбесіда призначена",
    "interview_completed": "Співбесіда проведена",
    "offer_sent": "Офер відправлено",
    "hired": "Найнято",
    "rejected": "Відмова",
    "no_answer": "Недзвін",
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
