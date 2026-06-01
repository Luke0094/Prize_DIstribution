"""
MainWindow — PySide6 Prize Distribution
Full retranslation on language change, synced language combos,
two-row state bar, template section, font-size propagation.
"""

from calendar import monthrange
from datetime import datetime

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QFrame, QLabel, QLineEdit, QComboBox, QCheckBox,
    QPushButton, QTabWidget, QStatusBar, QMessageBox,
    QSpinBox, QApplication, QSizePolicy,
)
from PySide6.QtCore import QTimer
from PySide6.QtGui import QFont

from models import SavedState, DateRange
from core.translations import TranslationManager
from core.state_manager import StateManager
from core.preferences import PreferenceManager

from ui.theme import THEMES, get_stylesheet
from ui.widgets import primary_btn, icon_btn, section_label
from ui.tabs import PrizesTab, ParticipantsTab, DistributionTab, HistoryTab
from ui.dialogs import SettingsDialog, CreditsDialog

TAB_PRIZES  = 0
TAB_PARTS   = 1
TAB_DIST    = 2
TAB_HISTORY = 3


class MainWindow(QMainWindow):
    def __init__(self, tr: TranslationManager, state_mgr: StateManager,
                 prefs: PreferenceManager):
        super().__init__()
        self.tr        = tr
        self.state_mgr = state_mgr
        self.prefs     = prefs
        self.current_state: SavedState | None = None
        self._backup_timer: QTimer | None = None

        self._setup_window()
        self._build_header()
        self._build_state_bar()
        self._build_tabs()
        self._build_statusbar()
        self._connect_signals()

        self._apply_theme(prefs.get("theme", "dark"))
        self._apply_font_size(prefs.get("font_size", 10))
        # set language silently — combo is already synced in _build_header
        self.tr.set_language(prefs.get("language", "it"))

        if prefs.get("auto_backup", False):
            self._start_auto_backup()

        self.tr.log_info("log_app_initialized")
        self._status(self.tr.get("ready"), 3000)

    # ── Window ────────────────────────────────────────────────────────────────

    def _setup_window(self):
        self.setWindowTitle(self.tr.get("title"))
        self.resize(1440, 940)
        screen = QApplication.primaryScreen().availableGeometry()
        self.move((screen.width()-1440)//2, (screen.height()-940)//2)

    # ── Header ────────────────────────────────────────────────────────────────

    def _build_header(self):
        central = QWidget()
        self.setCentralWidget(central)
        self._root = QVBoxLayout(central)
        self._root.setContentsMargins(0, 0, 0, 0)
        self._root.setSpacing(0)

        hdr = QFrame(); hdr.setObjectName("header"); hdr.setFixedHeight(62)
        hl = QHBoxLayout(hdr); hl.setContentsMargins(20, 0, 16, 0); hl.setSpacing(8)

        self._title_lbl = QLabel("⚔  PRIZE DISTRIBUTION")
        self._title_lbl.setObjectName("title_label")
        hl.addWidget(self._title_lbl)
        hl.addStretch()

        self._credits_btn = QPushButton("ℹ  " + self.tr.get("credits"))
        self._credits_btn.clicked.connect(self._show_credits)
        hl.addWidget(self._credits_btn)

        self._theme_btn = icon_btn("☀", self.tr.get("theme"), size=36)
        self._theme_btn.clicked.connect(self._toggle_theme)
        hl.addWidget(self._theme_btn)

        # Language combo — single source of truth (also drives settings dialog)
        lang_labels = {"it":"🇮🇹 IT","en":"🇬🇧 EN","fr":"🇫🇷 FR","ru":"🇷🇺 RU"}
        self._lang_combo = QComboBox(); self._lang_combo.setFixedWidth(95)
        for code in self.tr.available_languages:
            self._lang_combo.addItem(lang_labels.get(code, code.upper()), code)
        cur = self.prefs.get("language", "it")
        self._sync_lang_combo(self._lang_combo, cur)
        self._lang_combo.currentIndexChanged.connect(self._on_lang_changed)
        hl.addWidget(self._lang_combo)

        self._settings_btn = QPushButton("⚙  " + self.tr.get("settings"))
        self._settings_btn.clicked.connect(self._show_settings)
        hl.addWidget(self._settings_btn)

        self._root.addWidget(hdr)

    # ── State bar (3 rows: start · template · end-date) ─────────────────────

    def _build_state_bar(self):
        outer = QFrame(); outer.setObjectName("panel")
        ol = QVBoxLayout(outer); ol.setSpacing(4); ol.setContentsMargins(14, 8, 14, 8)

        months = self.tr.get("months").split(",")

        # ══ Row 1: event · start date · checkbox · save ═══════════════════════
        row1 = QHBoxLayout(); row1.setSpacing(8)

        self._lbl_event = QLabel(self.tr.get("event") + ":")
        row1.addWidget(self._lbl_event)
        self._event_input = QLineEdit()
        self._event_input.setPlaceholderText(self.tr.get("event_placeholder"))
        self._event_input.setMinimumWidth(130)
        self._event_input.setMaximumWidth(190)
        row1.addWidget(self._event_input)

        self._lbl_year = QLabel(self.tr.get("year") + ":")
        row1.addWidget(self._lbl_year)
        self._year_spin = QSpinBox()
        self._year_spin.setRange(2000, 2100)
        self._year_spin.setValue(datetime.now().year)
        self._year_spin.setFixedWidth(84)
        self._year_spin.valueChanged.connect(lambda _: self._update_day_combos())
        row1.addWidget(self._year_spin)

        self._lbl_month = QLabel(self.tr.get("month") + ":")
        row1.addWidget(self._lbl_month)
        self._month_combo = QComboBox(); self._month_combo.setFixedWidth(100)
        for i, m in enumerate(months, 1):
            self._month_combo.addItem(m, i)
        self._month_combo.setCurrentIndex(datetime.now().month - 1)
        self._month_combo.currentIndexChanged.connect(lambda _: self._update_day_combos())
        row1.addWidget(self._month_combo)

        self._lbl_sday = QLabel(self.tr.get("start_day") + ":")
        row1.addWidget(self._lbl_sday)
        self._start_day_combo = QComboBox(); self._start_day_combo.setFixedWidth(62)
        row1.addWidget(self._start_day_combo)

        self._range_cb = QCheckBox(self.tr.get("use_date_range"))
        self._range_cb.toggled.connect(self._toggle_range)
        row1.addWidget(self._range_cb)

        row1.addStretch()

        self._save_btn = primary_btn("💾  " + self.tr.get("save_state"))
        self._save_btn.clicked.connect(self._save_state)
        row1.addWidget(self._save_btn)

        self._update_btn = QPushButton("↻  " + self.tr.get("update_state"))
        self._update_btn.setEnabled(False)
        self._update_btn.clicked.connect(self._update_state)
        row1.addWidget(self._update_btn)

        ol.addLayout(row1)

        # ══ Row 2: template (fixed left) · end-date (appears to its right) ═══
        row2 = QHBoxLayout(); row2.setSpacing(8)

        # Template — always at the start of row 2, never moves
        self._tmpl_lbl = QLabel("📋 " + self.tr.get("load_template") + ":")
        self._tmpl_lbl.setObjectName("subtitle")
        row2.addWidget(self._tmpl_lbl)

        self._tmpl_state_combo = QComboBox()
        self._tmpl_state_combo.setMinimumWidth(180)
        self._tmpl_state_combo.setMaximumWidth(260)
        self._tmpl_state_combo.setPlaceholderText("— " + self.tr.get("history") + " —")
        row2.addWidget(self._tmpl_state_combo)

        self._tmpl_prizes_btn = QPushButton("🏆 " + self.tr.get("load_prizes"))
        self._tmpl_prizes_btn.clicked.connect(self._load_prizes_from_template)
        row2.addWidget(self._tmpl_prizes_btn)

        self._tmpl_parts_btn = QPushButton("👥 " + self.tr.get("load_participants"))
        self._tmpl_parts_btn.clicked.connect(self._load_parts_from_template)
        row2.addWidget(self._tmpl_parts_btn)

        # End-date — hidden by default, appears inline to the right of template
        self._end_frame = QFrame()
        self._end_frame.setVisible(False)
        ef = QHBoxLayout(self._end_frame)
        ef.setContentsMargins(8, 0, 0, 0); ef.setSpacing(8)

        ef.addWidget(QLabel("→"))
        self._lbl_end_year = QLabel(self.tr.get("year") + ":")
        ef.addWidget(self._lbl_end_year)
        self._end_year = QSpinBox(); self._end_year.setRange(2000, 2100)
        self._end_year.setValue(datetime.now().year); self._end_year.setFixedWidth(84)
        self._end_year.valueChanged.connect(lambda _: self._update_day_combos())
        ef.addWidget(self._end_year)

        self._lbl_end_month = QLabel(self.tr.get("month") + ":")
        ef.addWidget(self._lbl_end_month)
        self._end_month = QComboBox(); self._end_month.setFixedWidth(100)
        for i, m in enumerate(months, 1):
            self._end_month.addItem(m, i)
        self._end_month.setCurrentIndex(datetime.now().month - 1)
        self._end_month.currentIndexChanged.connect(lambda _: self._update_day_combos())
        ef.addWidget(self._end_month)

        self._lbl_end_day = QLabel(self.tr.get("end_day") + ":")
        ef.addWidget(self._lbl_end_day)
        self._end_day_combo = QComboBox(); self._end_day_combo.setFixedWidth(62)
        ef.addWidget(self._end_day_combo)

        row2.addWidget(self._end_frame)
        row2.addStretch()
        ol.addLayout(row2)

        wrapper = QWidget()
        wl = QVBoxLayout(wrapper); wl.setContentsMargins(8, 4, 8, 0)
        wl.addWidget(outer)
        self._root.addWidget(wrapper)

        self._update_day_combos()

    def _toggle_range(self, checked: bool):
        self._end_frame.setVisible(checked)

    def _update_day_combos(self):
        self._populate_day_combo(self._start_day_combo,
                                 self._year_spin.value(),
                                 self._month_combo.currentData() or 1)
        self._populate_day_combo(self._end_day_combo,
                                 self._end_year.value(),
                                 self._end_month.currentData() or 1)

    @staticmethod
    def _populate_day_combo(combo: QComboBox, year: int, month: int):
        current = combo.currentData()
        combo.blockSignals(True)
        combo.clear()
        combo.addItem("—", None)
        n = monthrange(year, month)[1]
        for d in range(1, n + 1):
            combo.addItem(str(d), d)
        idx = combo.findData(current) if current else 0
        combo.setCurrentIndex(max(idx, 0))
        combo.blockSignals(False)

    def _refresh_template_combo(self):
        self._tmpl_state_combo.blockSignals(True)
        self._tmpl_state_combo.clear()
        for s in sorted(self.state_mgr.states,
                        key=lambda x: (x.date_range.start_year,
                                       x.date_range.start_month), reverse=True):
            label = f"{s.event}  ({s.date_range})"
            self._tmpl_state_combo.addItem(label, userData=s)
        self._tmpl_state_combo.blockSignals(False)

    # ── Tabs ──────────────────────────────────────────────────────────────────

    def _build_tabs(self):
        self._tabs = QTabWidget()
        self._prizes_tab = PrizesTab(self.tr, self.state_mgr)
        self._parts_tab  = ParticipantsTab(self.tr, self.state_mgr)
        self._dist_tab   = DistributionTab(self.tr)
        self._hist_tab   = HistoryTab(self.tr, self.state_mgr)

        self._tabs.addTab(self._prizes_tab, "🏆  " + self.tr.get("prizes"))
        self._tabs.addTab(self._parts_tab,  "👥  " + self.tr.get("participants"))
        self._tabs.addTab(self._dist_tab,   "📊  " + self.tr.get("distribution"))
        self._tabs.addTab(self._hist_tab,   "📋  " + self.tr.get("history"))
        self._tabs.currentChanged.connect(self._on_tab_changed)

        wrapper = QWidget()
        wl = QVBoxLayout(wrapper); wl.setContentsMargins(8, 4, 8, 4)
        wl.addWidget(self._tabs)
        self._root.addWidget(wrapper)
        self.tr.log_info("log_ui_setup_completed")

    def _on_tab_changed(self, index: int):
        if index == TAB_DIST:
            self._dist_tab.update_prizes(self._prizes_tab.prizes)
            self._dist_tab.update_participants(self._parts_tab.participants)
            self._dist_tab.refresh_now()
        elif index == TAB_HISTORY:
            self._hist_tab.refresh()
            self._refresh_template_combo()

    # ── Status bar ────────────────────────────────────────────────────────────

    def _build_statusbar(self):
        self._sb = QStatusBar(); self.setStatusBar(self._sb)
        self._state_lbl = QLabel(""); self._state_lbl.setObjectName("subtitle")
        self._sb.addPermanentWidget(self._state_lbl)

    def _status(self, msg: str, ms: int = 0):
        self._sb.showMessage(msg, ms) if ms else self._sb.showMessage(msg)

    # ── Signals ───────────────────────────────────────────────────────────────

    def _connect_signals(self):
        self._prizes_tab.prizes_changed.connect(self._on_prizes_changed)
        self._parts_tab.participants_changed.connect(self._on_parts_changed)
        self._hist_tab.state_loaded.connect(self._restore_state)
        # History tab template signals (kept for history-tab workflow too)
        self._hist_tab.prizes_as_template.connect(self._do_load_prizes_template)
        self._hist_tab.parts_as_template.connect(self._do_load_parts_template)

    def _on_prizes_changed(self):
        self._dist_tab.update_prizes(self._prizes_tab.prizes)

    def _on_parts_changed(self):
        self._dist_tab.update_participants(self._parts_tab.participants)

    # ── Template loading (state bar) ──────────────────────────────────────────

    def _load_prizes_from_template(self):
        state: SavedState | None = self._tmpl_state_combo.currentData()
        if state:
            self._do_load_prizes_template(state)

    def _load_parts_from_template(self):
        state: SavedState | None = self._tmpl_state_combo.currentData()
        if state:
            self._do_load_parts_template(state)

    def _do_load_prizes_template(self, state: SavedState):
        if not state.prizes:
            return
        reply = QMessageBox.question(
            self, self.tr.get("confirm"),
            f"{self.tr.get('load_prizes')} da «{state.event}»?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            mid = max((p.id for p in state.prizes), default=0) + 1
            self._prizes_tab.load_prizes(state.prizes, mid)
            self._dist_tab.update_prizes(self._prizes_tab.prizes)
            self._tabs.setCurrentIndex(TAB_PRIZES)
            self._status(f"{self.tr.get('load_prizes')}: {state.event}", 3000)

    def _do_load_parts_template(self, state: SavedState):
        if not state.participants:
            return
        reply = QMessageBox.question(
            self, self.tr.get("confirm"),
            f"{self.tr.get('load_participants')} da «{state.event}»?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            mid = max((p.id for p in state.participants), default=0) + 1
            self._parts_tab.load_participants(state.participants, mid)
            self._dist_tab.update_participants(self._parts_tab.participants)
            self._tabs.setCurrentIndex(TAB_PARTS)
            self._status(f"{self.tr.get('load_participants')}: {state.event}", 3000)

    # ── State management ──────────────────────────────────────────────────────

    def _get_date_range(self) -> DateRange | None:
        year  = self._year_spin.value()
        month = self._month_combo.currentData()
        if not month:
            QMessageBox.warning(self, self.tr.get("error"), self.tr.get("start_month_required"))
            return None
        sday = self._start_day_combo.currentData()
        if self._range_cb.isChecked():
            dr = DateRange(year, month, start_day=sday,
                           end_year=self._end_year.value(),
                           end_month=self._end_month.currentData(),
                           end_day=self._end_day_combo.currentData())
        else:
            dr = DateRange(year, month, start_day=sday)
        if not dr.is_valid():
            QMessageBox.warning(self, self.tr.get("error"), self.tr.get("invalid_date_range"))
            return None
        return dr

    def _save_state(self):
        event = self._event_input.text().strip()
        if not event:
            QMessageBox.warning(self, self.tr.get("error"), self.tr.get("event_required")); return
        if not self._prizes_tab.prizes or not self._parts_tab.participants:
            QMessageBox.warning(self, self.tr.get("error"),
                                self.tr.get("prizes_and_participants_required")); return
        dr = self._get_date_range()
        if not dr: return
        for s in self.state_mgr.states:
            if s is self.current_state: continue
            if s.event == event and dr.overlaps(s.date_range):
                if QMessageBox.question(self, self.tr.get("confirm"),
                        self.tr.get("date_collision"),
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                        ) != QMessageBox.StandardButton.Yes:
                    return
                break
        active = [p for p in self._parts_tab.participants if p.enabled]
        state  = SavedState(dr, event,
                            list(self._prizes_tab.prizes),
                            list(self._parts_tab.participants),
                            self._dist_tab.get_distributions(),
                            sum(p.damage for p in active))
        try:
            fname = self.state_mgr.save(state)
            self.current_state = state
            self._update_btn.setEnabled(True)
            self._state_lbl.setText(f"  {event}  |  {dr}")
            self.tr.log_info("log_state_saved", event=event)
            self.tr.log_info("log_state_file_saved", filename=fname)
            self._status(self.tr.get("state_saved"), 4000)
            self._after_state_change()
        except Exception as e:
            self.tr.log_error("log_error_saving_state", error=str(e))
            QMessageBox.critical(self, self.tr.get("error"), str(e))

    def _update_state(self):
        if not self.current_state: return
        if QMessageBox.question(self, self.tr.get("confirm"), self.tr.get("confirm_update"),
                                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                                ) != QMessageBox.StandardButton.Yes:
            return
        active = [p for p in self._parts_tab.participants if p.enabled]
        self.current_state.prizes        = list(self._prizes_tab.prizes)
        self.current_state.participants  = list(self._parts_tab.participants)
        self.current_state.distributions = self._dist_tab.get_distributions()
        self.current_state.total_damage  = sum(p.damage for p in active)
        try:
            self.state_mgr.save(self.current_state)
            self.tr.log_info("log_state_saved", event=self.current_state.event)
            self._status(self.tr.get("state_updated"), 4000)
            self._after_state_change()
        except Exception as e:
            self.tr.log_error("log_error_update_state", error=str(e))
            QMessageBox.critical(self, self.tr.get("error"), str(e))

    def _after_state_change(self):
        self._hist_tab.refresh()
        self._refresh_template_combo()
        self._prizes_tab.refresh_completer_from_states()
        self._parts_tab.refresh_completer_from_states()

    def _restore_state(self, state: SavedState):
        self.current_state = state
        self._event_input.setText(state.event)
        self._year_spin.setValue(state.date_range.start_year)
        for i in range(self._month_combo.count()):
            if self._month_combo.itemData(i) == state.date_range.start_month:
                self._month_combo.setCurrentIndex(i); break
        self._update_day_combos()
        if state.date_range.start_day:
            idx = self._start_day_combo.findData(state.date_range.start_day)
            if idx >= 0: self._start_day_combo.setCurrentIndex(idx)
        mid_p = max((p.id for p in state.prizes),        default=0) + 1
        mid_a = max((p.id for p in state.participants),   default=0) + 1
        self._prizes_tab.load_prizes(state.prizes, mid_p)
        self._parts_tab.load_participants(state.participants, mid_a)
        self._dist_tab.update_prizes(state.prizes)
        self._dist_tab.update_participants(state.participants)
        self._update_btn.setEnabled(True)
        self._state_lbl.setText(f"  {state.event}  |  {state.date_range}")
        self._status(f"{self.tr.get('state_updated')}: {state.event}", 4000)
        self._tabs.setCurrentIndex(TAB_PRIZES)
        self._after_state_change()

    # ── Theme ─────────────────────────────────────────────────────────────────

    def _toggle_theme(self):
        self._apply_theme("light" if self.prefs.get("theme","dark") == "dark" else "dark")

    def _apply_theme(self, name: str):
        theme = THEMES.get(name, THEMES["dark"])
        fsize = self.prefs.get("font_size", 10)
        ss    = get_stylesheet(theme).replace("font-size: 10pt;", f"font-size: {fsize}pt;", 1)
        app   = QApplication.instance()
        app.setStyleSheet(ss)
        # Force all top-level widgets to repaint so theme propagates to viewports
        for w in app.topLevelWidgets():
            w.update()
        self._theme_btn.setText("☀" if name == "dark" else "🌙")
        self.prefs.set("theme", name)
        self.tr.log_info("log_theme_applied", theme=name)

    def _apply_font_size(self, size: int):
        f = QFont(); f.setPointSize(size)
        QApplication.instance().setFont(f)
        self.prefs.set("font_size", size)
        self._apply_theme(self.prefs.get("theme", "dark"))

    # ── Language ──────────────────────────────────────────────────────────────

    @staticmethod
    def _sync_lang_combo(combo: QComboBox, lang: str):
        for i in range(combo.count()):
            if combo.itemData(i) == lang:
                combo.setCurrentIndex(i); return

    def _on_lang_changed(self):
        lang = self._lang_combo.currentData()
        if not lang: return
        self.tr.set_language(lang)
        self.prefs.set("language", lang)
        self._retranslate_ui()

    def _apply_language_from_settings(self, lang: str):
        """Called by SettingsDialog.language_changed signal."""
        self.tr.set_language(lang)
        self.prefs.set("language", lang)
        # Sync the header combo without re-triggering _on_lang_changed
        self._lang_combo.blockSignals(True)
        self._sync_lang_combo(self._lang_combo, lang)
        self._lang_combo.blockSignals(False)
        self._retranslate_ui()

    def _retranslate_ui(self):
        """Update all translatable text in the main window and tabs immediately."""
        tr = self.tr
        # Window title
        self.setWindowTitle(tr.get("title"))
        # Header
        self._credits_btn.setText("ℹ  " + tr.get("credits"))
        self._settings_btn.setText("⚙  " + tr.get("settings"))
        # State bar row 1
        self._lbl_event.setText(tr.get("event") + ":")
        self._event_input.setPlaceholderText(tr.get("event_placeholder"))
        self._lbl_year.setText(tr.get("year") + ":")
        self._lbl_month.setText(tr.get("month") + ":")
        self._lbl_sday.setText(tr.get("start_day") + ":")
        self._range_cb.setText(tr.get("use_date_range"))
        self._save_btn.setText("💾  " + tr.get("save_state"))
        self._update_btn.setText("↻  " + tr.get("update_state"))
        # State bar row 2 — template
        self._tmpl_lbl.setText("📋 " + tr.get("load_template") + ":")
        self._tmpl_state_combo.setPlaceholderText("— " + tr.get("history") + " —")
        self._tmpl_prizes_btn.setText("🏆 " + tr.get("load_prizes"))
        self._tmpl_parts_btn.setText("👥 " + tr.get("load_participants"))
        # State bar row 3 — end date labels
        self._lbl_end_year.setText(tr.get("year") + ":")
        self._lbl_end_month.setText(tr.get("month") + ":")
        self._lbl_end_day.setText(tr.get("end_day") + ":")
        # Month combos — rebuild with new locale
        months = tr.get("months").split(",")
        for combo in (self._month_combo, self._end_month):
            cur = combo.currentData()
            combo.blockSignals(True)
            combo.clear()
            for i, m in enumerate(months, 1):
                combo.addItem(m, i)
            self._sync_lang_combo(combo, cur)
            combo.blockSignals(False)
        # Tabs
        self._tabs.setTabText(TAB_PRIZES,   "🏆  " + tr.get("prizes"))
        self._tabs.setTabText(TAB_PARTS,    "👥  " + tr.get("participants"))
        self._tabs.setTabText(TAB_DIST,     "📊  " + tr.get("distribution"))
        self._tabs.setTabText(TAB_HISTORY,  "📋  " + tr.get("history"))
        # Delegate to each tab
        self._prizes_tab.retranslate_ui()
        self._parts_tab.retranslate_ui()
        self._dist_tab.retranslate_ui()
        self._hist_tab.retranslate_ui()

    # ── Dialogs ───────────────────────────────────────────────────────────────

    def _show_credits(self):
        try:
            CreditsDialog(self.tr, self).exec()
        except Exception as e:
            self.tr.log_error("log_error_credits", error=str(e))

    def _show_settings(self):
        dlg = SettingsDialog(self.tr, self.prefs, self.state_mgr, self)
        dlg.theme_changed.connect(self._apply_theme)
        dlg.font_size_changed.connect(self._apply_font_size)
        # Sync language from settings: also updates header combo
        dlg.language_changed.connect(self._apply_language_from_settings)
        dlg.exec()

    # ── Auto-backup ───────────────────────────────────────────────────────────

    def _start_auto_backup(self):
        iv = self.prefs.get("backup_interval", 3)
        rt = self.prefs.get("backup_retention", 10)
        self._backup_timer = QTimer(self)
        self._backup_timer.timeout.connect(lambda: self._auto_backup(rt))
        self._backup_timer.start(iv * 60 * 1000)
        self.tr.log_info("log_auto_backup_setup", interval=iv, retention=rt)

    def _auto_backup(self, retention: int = 10):
        try:
            fname = self.state_mgr.create_backup(retention)
            self.tr.log_info("log_backup_created", filename=fname)
            self._status(f"Auto-backup: {fname}", 2000)
        except Exception as e:
            self.tr.log_error("log_error_auto_backup", error=str(e))
