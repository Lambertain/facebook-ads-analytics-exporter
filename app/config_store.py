import os
from typing import Dict, Tuple


ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ENV_PATH = os.path.join(ROOT_DIR, ".env")


ALLOWED_KEYS = [
    "META_ACCESS_TOKEN",
    "META_AD_ACCOUNT_ID",
    "GOOGLE_APPLICATION_CREDENTIALS",
    "GOOGLE_SHEET_ID",
    "STORAGE_BACKEND",
    "EXCEL_CREATIVES_PATH",
    "EXCEL_STUDENTS_PATH",
    "EXCEL_TEACHERS_PATH",
    "NETHUNT_BASIC_AUTH",
    "NETHUNT_FOLDER_ID",
    "ALFACRM_BASE_URL",
    "ALFACRM_EMAIL",
    "ALFACRM_API_KEY",
    "ALFACRM_COMPANY_ID",
]

SECRET_KEYS = {
    "META_ACCESS_TOKEN",
    "NETHUNT_BASIC_AUTH",
    "ALFACRM_API_KEY",
}


def _mask(value: str) -> Tuple[bool, str]:
    if not value:
        return False, ""
    return True, "••••••••"


def get_config_masked() -> Dict[str, Dict[str, str]]:
    out: Dict[str, Dict[str, str]] = {}
    for key in ALLOWED_KEYS:
        val = os.getenv(key, "")
        if key in SECRET_KEYS:
            has, masked = _mask(val)
            out[key] = {"value": masked, "has_value": has, "secret": True}
        else:
            out[key] = {"value": val, "has_value": bool(val), "secret": False}
    return out


def set_config(values: Dict[str, str]):
    # Filter only allowed keys
    updates = {k: v for k, v in values.items() if k in ALLOWED_KEYS and v is not None}
    if not updates:
        return
    # Update in-memory env
    for k, v in updates.items():
        os.environ[k] = str(v)
    # Update .env file (upsert)
    lines = []
    if os.path.exists(ENV_PATH):
        with open(ENV_PATH, "r", encoding="utf-8") as f:
            lines = f.read().splitlines()
    # Build map of existing keys -> idx
    idx_map = {}
    for idx, line in enumerate(lines):
        if not line or line.strip().startswith("#"):
            continue
        if "=" in line:
            k = line.split("=", 1)[0].strip()
            if k in ALLOWED_KEYS and k not in idx_map:
                idx_map[k] = idx
    # Apply updates
    for k, v in updates.items():
        entry = f"{k}={v}"
        if k in idx_map:
            lines[idx_map[k]] = entry
        else:
            lines.append(entry)
    with open(ENV_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + ("\n" if lines else ""))
