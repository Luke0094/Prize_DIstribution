import json
import os

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QLabel, QComboBox, QSpinBox, QCheckBox, QPushButton,
    QGroupBox, QMessageBox, QFileDialog, QListWidget, QListWidgetItem,
    QSlider, QTextEdit,
)
from PySide6.QtCore import Qt, Signal

from core.translations import TranslationManager
from core.preferences import PreferenceManager
from core.state_manager import StateManager
from ui.widgets import hsep


class SettingsDialog(QDialog):
    theme_changed    = Signal(str)
    language_changed = Signal(str)
    font_size_changed = Signal(int)

    def __init__(self, tr: TranslationManager, prefs: PreferenceManager,
                 state_mgr: StateManager, parent=None):
        super().__init__(parent)
        self.tr        = tr
        self.prefs     = prefs
        self.state_mgr = state_mgr
        self.setWindowTitle(self.tr.get("settings"))
        self.setMinimumSize(540, 480)
        self._build_ui()

    # ── Build ─────────────────────────────────────────────────────────────────

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setSpacing(10)

        tabs = QTabWidget()

        # ── General ──────────────────────────────────────────────────────────
        gen = QWidget()
        gl  = QVBoxLayout(gen)
        gl.setSpacing(12)

        # Import settings from JSON
        import_grp = QGroupBox(self.tr.get("import_settings"))
        il = QVBoxLayout(import_grp)
        import_btn = QPushButton("⬇  " + self.tr.get("select_settings_file"))
        import_btn.clicked.connect(self._import_settings)
        il.addWidget(import_btn)
        gl.addWidget(import_grp)

        # Language
        lang_grp = QGroupBox(self.tr.get("default_language"))
        ll = QVBoxLayout(lang_grp)
        self._lang_combo = QComboBox()
        lang_map = {"it":"🇮🇹 Italiano","en":"🇬🇧 English","fr":"🇫🇷 Français","ru":"🇷🇺 Русский"}
        cur_lang = self.prefs.get("language","it")
        for code in self.tr.available_languages:
            self._lang_combo.addItem(lang_map.get(code, code.upper()), code)
        for i in range(self._lang_combo.count()):
            if self._lang_combo.itemData(i) == cur_lang:
                self._lang_combo.setCurrentIndex(i); break
        ll.addWidget(self._lang_combo)
        gl.addWidget(lang_grp)

        gl.addStretch()
        tabs.addTab(gen, self.tr.get("general"))

        # ── Theme & Font ──────────────────────────────────────────────────────
        theme_tab = QWidget()
        tl = QVBoxLayout(theme_tab)
        tl.setSpacing(12)

        theme_grp = QGroupBox(self.tr.get("theme"))
        tgl = QHBoxLayout(theme_grp)
        self._btn_dark  = QPushButton("🌙  " + self.tr.get("theme_dark"))
        self._btn_light = QPushButton("☀  " + self.tr.get("theme_light"))
        for btn in (self._btn_dark, self._btn_light):
            btn.setCheckable(True)
            btn.setMinimumHeight(38)
        cur_theme = self.prefs.get("theme","dark")
        self._btn_dark.setChecked(cur_theme == "dark")
        self._btn_light.setChecked(cur_theme == "light")
        # setChecked alone updates the style, but we also ensure mutual exclusion
        self._btn_dark.clicked.connect(lambda: self._select_theme("dark"))
        self._btn_light.clicked.connect(lambda: self._select_theme("light"))
        tgl.addWidget(self._btn_dark)
        tgl.addWidget(self._btn_light)
        tl.addWidget(theme_grp)

        # Font size with live preview
        font_grp = QGroupBox(self.tr.get("font_size"))
        fl = QVBoxLayout(font_grp)

        self._preview_lbl = QLabel("Anteprima testo — Sample text — Exemple")
        self._preview_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        fl.addWidget(self._preview_lbl)
        fl.addWidget(hsep())

        slider_row = QHBoxLayout()
        slider_row.addWidget(QLabel("8"))
        self._font_slider = QSlider(Qt.Orientation.Horizontal)
        self._font_slider.setRange(8, 16)
        self._font_slider.setSingleStep(1)
        self._font_slider.setTickInterval(1)
        self._font_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self._font_slider.setValue(self.prefs.get("font_size", 10))
        slider_row.addWidget(self._font_slider)
        slider_row.addWidget(QLabel("16"))
        fl.addLayout(slider_row)

        self._font_val_lbl = QLabel(str(self._font_slider.value()) + " pt")
        self._font_val_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        fl.addWidget(self._font_val_lbl)

        self._font_slider.valueChanged.connect(self._on_font_changed)
        self._on_font_changed(self._font_slider.value())  # init preview

        reset_font_btn = QPushButton(self.tr.get("reset"))
        reset_font_btn.setFixedWidth(90)
        reset_font_btn.clicked.connect(lambda: self._font_slider.setValue(10))
        fl.addWidget(reset_font_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        tl.addWidget(font_grp)
        tl.addStretch()
        tabs.addTab(theme_tab, self.tr.get("theme") + " / " + self.tr.get("display"))

        # ── Backup ────────────────────────────────────────────────────────────
        bk = QWidget()
        bk.setAutoFillBackground(True)   # inherit theme bg_window properly
        bl = QVBoxLayout(bk)
        bl.setSpacing(8)

        auto_grp = QGroupBox(self.tr.get("backup_settings"))
        al = QVBoxLayout(auto_grp)
        self._auto_cb = QCheckBox(self.tr.get("enable_auto_backup"))
        self._auto_cb.setChecked(self.prefs.get("auto_backup",False))
        al.addWidget(self._auto_cb)

        row1 = QHBoxLayout()
        row1.addWidget(QLabel(self.tr.get("backup_interval")+":"))
        self._interval_spin = QSpinBox(); self._interval_spin.setRange(1,60)
        self._interval_spin.setValue(self.prefs.get("backup_interval",3))
        row1.addWidget(self._interval_spin)
        row1.addWidget(QLabel(self.tr.get("minutes"))); row1.addStretch()
        al.addLayout(row1)

        row2 = QHBoxLayout()
        row2.addWidget(QLabel(self.tr.get("backup_retention")+":"))
        self._retention_spin = QSpinBox(); self._retention_spin.setRange(1,100)
        self._retention_spin.setValue(self.prefs.get("backup_retention",10))
        row2.addWidget(self._retention_spin); row2.addStretch()
        al.addLayout(row2)
        bl.addWidget(auto_grp)

        btn_row = QHBoxLayout()
        backup_now_btn = QPushButton(self.tr.get("backup_now"))
        backup_now_btn.clicked.connect(self._do_backup)
        restore_btn = QPushButton(self.tr.get("restore"))
        restore_btn.clicked.connect(self._do_restore)
        btn_row.addWidget(backup_now_btn); btn_row.addWidget(restore_btn)
        bl.addLayout(btn_row)

        bl.addWidget(QLabel(self.tr.get("select_backup")+":"))

        # Backup list + preview side by side
        backup_split = QHBoxLayout()
        self._backup_list = QListWidget()
        self._backup_list.currentItemChanged.connect(self._show_backup_preview)
        backup_split.addWidget(self._backup_list, 1)

        preview_frame = QGroupBox(self.tr.get("preview"))
        pfl = QVBoxLayout(preview_frame)
        self._backup_preview = QTextEdit()
        self._backup_preview.setReadOnly(True)
        self._backup_preview.setMaximumHeight(120)
        pfl.addWidget(self._backup_preview)
        backup_split.addWidget(preview_frame, 1)
        bl.addLayout(backup_split)

        self._refresh_backup_list()
        bl.addStretch()
        tabs.addTab(bk, self.tr.get("backup"))

        # ── Import/Export ─────────────────────────────────────────────────────
        io = QWidget()
        il2 = QVBoxLayout(io)
        il2.setSpacing(10)
        export_btn = QPushButton("⬆  " + self.tr.get("export_json"))
        export_btn.clicked.connect(self._do_export)
        import_data_btn = QPushButton("⬇  " + self.tr.get("import_json"))
        import_data_btn.clicked.connect(self._do_import_data)
        il2.addWidget(export_btn); il2.addWidget(import_data_btn); il2.addStretch()
        tabs.addTab(io, self.tr.get("import")+"/"+self.tr.get("export"))

        root.addWidget(tabs)

        # Dialog buttons
        dlg_row = QHBoxLayout()
        reset_btn2 = QPushButton(self.tr.get("reset"))
        reset_btn2.clicked.connect(self._do_reset)
        cancel_btn = QPushButton(self.tr.get("cancel"))
        cancel_btn.clicked.connect(self.reject)
        save_btn = QPushButton(self.tr.get("save"))
        save_btn.setObjectName("primary")
        save_btn.clicked.connect(self._do_save)
        dlg_row.addWidget(reset_btn2); dlg_row.addStretch()
        dlg_row.addWidget(cancel_btn); dlg_row.addWidget(save_btn)
        root.addLayout(dlg_row)

    # ── Font preview ──────────────────────────────────────────────────────────

    def _on_font_changed(self, size: int):
        from PySide6.QtGui import QFont
        f = QFont(); f.setPointSize(size)
        self._preview_lbl.setFont(f)
        self._font_val_lbl.setText(f"{size} pt")

    # ── Theme ─────────────────────────────────────────────────────────────────

    def _select_theme(self, name: str):
        self._btn_dark.setChecked(name == "dark")
        self._btn_light.setChecked(name == "light")

    def _current_theme(self) -> str:
        return "dark" if self._btn_dark.isChecked() else "light"

    # ── Backup ────────────────────────────────────────────────────────────────

    def _refresh_backup_list(self):
        self._backup_list.clear()
        for fname in self.state_mgr.list_backups():
            self._backup_list.addItem(QListWidgetItem(fname))

    def _show_backup_preview(self, item):
        if not item:
            return
        path = os.path.join(self.state_mgr.backup_folder, item.text())
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, list):
                data = [data]
            prizes_total       = sum(len(s.get("prizes",[]))       for s in data)
            participants_total = sum(len(s.get("participants",[])) for s in data)
            lines = [
                f"{self.tr.get('prizes')}: {prizes_total}",
                f"{self.tr.get('participants')}: {participants_total}",
                "",
            ]
            # Show first 3 prizes from first state
            first_prizes = (data[0].get("prizes",[]) if data else [])[:3]
            if first_prizes:
                lines.append(f"{self.tr.get('prizes')} (primi 3):")
                for p in first_prizes:
                    lines.append(f"  {p.get('name','?')}: {p.get('quantity','?')}")
            # Show first 3 participants from first state
            first_parts = (data[0].get("participants",[]) if data else [])[:3]
            if first_parts:
                lines.append(f"\n{self.tr.get('participants')} (primi 3):")
                for p in first_parts:
                    lines.append(f"  {p.get('name','?')}: {p.get('damage','?')}")
            self._backup_preview.setPlainText("\n".join(lines))
        except Exception as e:
            self._backup_preview.setPlainText(f"Errore: {e}")

    def _do_backup(self):
        try:
            retention = self.prefs.get("backup_retention", 10)
            fname = self.state_mgr.create_backup(retention)
            self.tr.log_info("log_backup_created", filename=fname)
            QMessageBox.information(self, self.tr.get("info"),
                                    f"{self.tr.get('backup_created')}\n{fname}")
            self._refresh_backup_list()
        except Exception as e:
            self.tr.log_error("log_error_backup", error=str(e))
            QMessageBox.critical(self, self.tr.get("error"), str(e))

    def _do_restore(self):
        item = self._backup_list.currentItem()
        if not item:
            QMessageBox.warning(self, self.tr.get("error"), self.tr.get("no_backup_selected"))
            return
        path = os.path.join(self.state_mgr.backup_folder, item.text())
        reply = QMessageBox.question(
            self, self.tr.get("confirm"), self.tr.get("confirm_restore"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        try:
            self.state_mgr.restore_backup(path)
            self.tr.log_info("log_restore_completed", filename=item.text())
            QMessageBox.information(self, self.tr.get("info"), self.tr.get("restore_completed"))
        except Exception as e:
            self.tr.log_error("log_error_restore", error=str(e))
            QMessageBox.critical(self, self.tr.get("error"), str(e))

    # ── Import/Export ─────────────────────────────────────────────────────────

    def _do_export(self):
        path, _ = QFileDialog.getSaveFileName(self, self.tr.get("export_json"), "", "JSON (*.json)")
        if path:
            try:
                self.state_mgr.export_json(path)
                QMessageBox.information(self, self.tr.get("info"), self.tr.get("export_completed"))
            except Exception as e:
                QMessageBox.critical(self, self.tr.get("error"), str(e))

    def _do_import_data(self):
        path, _ = QFileDialog.getOpenFileName(self, self.tr.get("import_json"), "", "JSON (*.json)")
        if path:
            try:
                imported = self.state_mgr.import_json(path)
                QMessageBox.information(self, self.tr.get("info"),
                                        f"{self.tr.get('restore_completed')}: {len(imported)} stati")
            except Exception as e:
                QMessageBox.critical(self, self.tr.get("error"), str(e))

    def _import_settings(self):
        """Import preferences from a JSON file (with rollback on error)."""
        path, _ = QFileDialog.getOpenFileName(
            self, self.tr.get("select_settings_file"), "", "JSON (*.json)"
        )
        if not path:
            return
        backup = dict(self.prefs._prefs)
        try:
            with open(path, encoding="utf-8") as f:
                new_prefs = json.load(f)
            if not isinstance(new_prefs, dict):
                raise ValueError(self.tr.get("invalid_settings_file"))
            for k, v in new_prefs.items():
                self.prefs.set(k, v)
            QMessageBox.information(self, self.tr.get("info"), self.tr.get("settings_imported"))
            self.reject()  # close and let main window reload
        except json.JSONDecodeError:
            self.prefs._prefs = backup
            self.prefs._save()
            QMessageBox.critical(self, self.tr.get("error"), self.tr.get("invalid_settings_file"))
        except Exception as e:
            self.prefs._prefs = backup
            self.prefs._save()
            self.tr.log_error("log_error_preferences", error=str(e))
            QMessageBox.critical(self, self.tr.get("error"), self.tr.get("settings_import_error"))

    # ── Save / Reset ──────────────────────────────────────────────────────────

    def _do_save(self):
        theme    = self._current_theme()
        lang     = self._lang_combo.currentData()
        font_sz  = self._font_slider.value()
        self.prefs.set("theme",            theme)
        self.prefs.set("language",         lang)
        self.prefs.set("font_size",        font_sz)
        self.prefs.set("auto_backup",      self._auto_cb.isChecked())
        self.prefs.set("backup_interval",  self._interval_spin.value())
        self.prefs.set("backup_retention", self._retention_spin.value())
        self.tr.log_info("log_settings_saved")
        self.theme_changed.emit(theme)
        self.language_changed.emit(lang)
        self.font_size_changed.emit(font_sz)
        self.accept()

    def _do_reset(self):
        reply = QMessageBox.question(
            self, self.tr.get("confirm"), self.tr.get("confirm_reset_preferences"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.prefs.reset()
            QMessageBox.information(self, self.tr.get("info"), self.tr.get("preferences_reset"))
            self.reject()
