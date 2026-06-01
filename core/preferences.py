import json
import os
from typing import Any


class PreferenceManager:
    DEFAULTS: dict = {
        "theme": "dark",
        "language": "it",
        "font_size": 10,
        "auto_backup": False,
        "backup_interval": 3,
        "backup_retention": 10,
        "integer_only": True,
        "data_folder": "saved_states",
        "backup_folder": "backups",
    }

    def __init__(self, path: str = "preferences.json"):
        self._path = path
        self._prefs: dict = {}
        self._load()

    def _load(self):
        if os.path.exists(self._path):
            try:
                with open(self._path, encoding="utf-8") as f:
                    loaded = json.load(f)
                if isinstance(loaded, dict):
                    self._prefs = loaded
            except Exception:
                self._prefs = {}

    def _save(self):
        try:
            with open(self._path, "w", encoding="utf-8") as f:
                json.dump(self._prefs, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def get(self, key: str, default: Any = None) -> Any:
        if key in self._prefs:
            return self._prefs[key]
        if key in self.DEFAULTS:
            return self.DEFAULTS[key]
        return default

    def set(self, key: str, value: Any):
        self._prefs[key] = value
        self._save()

    def reset(self):
        self._prefs = {}
        if os.path.exists(self._path):
            try:
                os.remove(self._path)
            except OSError:
                pass
