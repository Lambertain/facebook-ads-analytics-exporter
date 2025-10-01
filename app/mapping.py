import json
import os
from typing import Dict, Any


def load_mapping() -> Dict[str, Any]:
    """Загружает mapping из config/mapping.json"""
    mapping_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "config",
        "mapping.json"
    )

    if not os.path.exists(mapping_path):
        return {}

    try:
        with open(mapping_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading mapping: {e}")
        return {}