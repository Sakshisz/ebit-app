
# backend/data_access.py
from __future__ import annotations
import json
from pathlib import Path
from typing import List, Dict, Any

# Resolve project root (…/ebit-app)
ROOT = Path(__file__).resolve().parents[1]

# Data directory: …/ebit-app/data
DATA_DIR = ROOT / "data"

CONSULTANTS_FILE = DATA_DIR / "consultants.json"
PROJECTS_FILE = DATA_DIR / "projects.json"
SETTINGS_FILE = DATA_DIR / "settings.json"


def _load_json(path: Path) -> Any:
    if not path.exists():
        # Deterministic defaults (important for tests)
        if path.stem in {"consultants", "projects"}:
            return []
        return {}

    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_consultants() -> List[Dict[str, Any]]:
    data = _load_json(CONSULTANTS_FILE)
    if not isinstance(data, list):
        raise ValueError("consultants.json must contain a list")
    return data


def load_projects() -> List[Dict[str, Any]]:
    data = _load_json(PROJECTS_FILE)
    if not isinstance(data, list):
        raise ValueError("projects.json must contain a list")
    return data


def load_settings() -> Dict[str, Any]:
    data = _load_json(SETTINGS_FILE)
    if not isinstance(data, dict):
        raise ValueError("settings.json must contain an object")
    return data

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
