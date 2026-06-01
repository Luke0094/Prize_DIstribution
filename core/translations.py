"""
TranslationManager
==================
Loads locale data from JSON files in a ``locales/`` directory.
Auto-detects any extra *.json file added by the user (e.g. de.json).
Falls back through the fallback chain for missing keys.

Log format: %(asctime)s - [%(language)s] - %(levelname)s - %(message)s
"""

import json
import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Dict, List, Optional


class _LanguageFilter(logging.Filter):
    """Injects the current language code into every LogRecord."""
    def __init__(self, manager):
        super().__init__()
        self._mgr = manager

    def filter(self, record):
        record.language = self._mgr.current_language
        return True


def _setup_root_logger(manager) -> logging.Logger:
    logger = logging.getLogger("PrizeDistribution")
    if logger.handlers:
        return logger
    logger.setLevel(logging.DEBUG)
    try:
        handler = RotatingFileHandler(
            "prize_distribution.log",
            maxBytes=1_048_576,
            backupCount=5,
            encoding="utf-8",
        )
        handler.setLevel(logging.DEBUG)
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s - [%(language)s] - %(levelname)s - %(message)s"
            )
        )
        handler.addFilter(_LanguageFilter(manager))
        logger.addHandler(handler)
    except OSError as exc:
        logging.basicConfig(level=logging.DEBUG)
        logging.warning("Could not open log file: %s", exc)
    return logger


class TranslationManager:
    _BUILTIN_LANGS = {"it", "en", "fr", "ru"}
    _FALLBACK      = ("it",)

    def __init__(self, locales_dir: Optional[str] = None):
        self._current: str = "it"
        self._data: Dict[str, Dict[str, str]] = {}

        script_dir = Path(__file__).resolve().parent.parent / "locales"
        cwd_dir    = Path.cwd() / "locales"
        self._search_paths = (
            [Path(locales_dir), script_dir, cwd_dir] if locales_dir
            else [script_dir, cwd_dir]
        )

        # Logger must be created AFTER _current is set (filter needs it)
        self.logger = _setup_root_logger(self)
        self._load_all()

    # ── Loading ───────────────────────────────────────────────────────────────

    def _load_all(self):
        found: Dict[str, Path] = {}
        for d in self._search_paths:
            if not Path(d).is_dir():
                continue
            for f in sorted(Path(d).glob("*.json")):
                lang = f.stem.lower()
                if lang not in found:
                    found[lang] = f

        if not found:
            self.logger.warning("No locale files found.")
            return

        for priority in list(self._FALLBACK) + sorted(found.keys()):
            if priority not in self._data and priority in found:
                self._load_file(priority, found[priority])

        for lang, path in found.items():
            if lang not in self._BUILTIN_LANGS:
                self.logger.info(
                    self.get("log_locale_autodetected", lang=lang, path=str(path))
                )

    def _load_file(self, lang: str, path: Path):
        try:
            with open(path, encoding="utf-8") as fh:
                raw = json.load(fh)
            if not isinstance(raw, dict):
                raise ValueError("Top-level must be a JSON object")
            self._data[lang] = raw
            self.logger.debug(
                self.get("log_locale_loaded", path=str(path))
            )
        except Exception as exc:
            self.logger.error(
                self.get("log_locale_load_error", path=str(path), error=str(exc))
            )

    # ── Public API ────────────────────────────────────────────────────────────

    @property
    def available_languages(self) -> List[str]:
        return sorted(self._data.keys())

    @property
    def current_language(self) -> str:
        return self._current

    def set_language(self, lang: str) -> bool:
        lang = lang.lower()
        if lang in self._data:
            self._current = lang
            self.logger.info(self.get("log_language_changed", language=lang))
            return True
        self.logger.warning("Language '%s' not available; keeping '%s'", lang, self._current)
        return False

    def get(self, key: str, **kwargs: Any) -> str:
        text: Optional[str] = self._data.get(self._current, {}).get(key)
        if text is None:
            for fb in self._FALLBACK:
                if fb != self._current:
                    text = self._data.get(fb, {}).get(key)
                    if text is not None:
                        break
        if text is None:
            text = key
        if kwargs:
            try:
                text = text.format(**kwargs)
            except (KeyError, IndexError):
                pass
        return text

    # ── Logging helpers ───────────────────────────────────────────────────────

    def log(self, level: str, key: str, **kwargs: Any):
        msg = self.get(key, **kwargs)
        getattr(self.logger, level, self.logger.info)(msg)

    def log_debug(self, key: str, **kwargs):   self.log("debug",   key, **kwargs)
    def log_info(self, key: str, **kwargs):    self.log("info",    key, **kwargs)
    def log_warning(self, key: str, **kwargs): self.log("warning", key, **kwargs)
    def log_error(self, key: str, **kwargs):   self.log("error",   key, **kwargs)
