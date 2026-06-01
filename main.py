"""
Prize Distribution — PySide6 entry point.

Usage:
    python main.py
"""

import sys
import os
from pathlib import Path

# Make sure the package root is on sys.path regardless of how the script is run
ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from core.translations import TranslationManager
from core.preferences import PreferenceManager
from core.state_manager import StateManager
from ui.main_window import MainWindow


def main():
    # High-DPI
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("Prize Distribution")
    app.setOrganizationName("PrizeApp")

    if os.name == 'nt':
        base_dir = Path(os.environ.get("APPDATA", Path.home()))
    else:
        base_dir = Path.home() / ".config"
        
    data_dir = base_dir / "PrizeDistribution"
    data_dir.mkdir(parents=True, exist_ok=True)

    os.chdir(data_dir)

    if hasattr(sys, '_MEIPASS'):
        locales_path = Path(sys._MEIPASS) / "locales"
    else:
        locales_path = Path(__file__).resolve().parent / "locales"

    # Core services
    prefs     = PreferenceManager(str(data_dir / "preferences.json"))
    tr        = TranslationManager(locales_dir=str(locales_path))          # auto-discovers locales/
    state_mgr = StateManager(
        data_folder   = str(data_dir / prefs.get("data_folder",   "saved_states")),
        backup_folder = str(data_dir / prefs.get("backup_folder", "backups")),
    )

    # Apply saved language before building the window
    tr.set_language(prefs.get("language", "en"))

    window = MainWindow(tr, state_mgr, prefs)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()