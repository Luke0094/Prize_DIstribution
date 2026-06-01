from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame,
    QLabel, QComboBox, QTreeWidget, QTreeWidgetItem,
    QPushButton, QMessageBox, QSplitter,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor

from models import SavedState
from core.translations import TranslationManager
from core.state_manager import StateManager
from core.distribution import DistributionEngine
from ui.widgets import (
    primary_btn, danger_btn, SortableTable,
    center_item, mono_item, section_label,
)


class HistoryTab(QWidget):
    state_loaded         = Signal(object)   # emits SavedState → full restore
    prizes_as_template   = Signal(object)   # emits SavedState → load prizes only
    parts_as_template    = Signal(object)   # emits SavedState → load participants only

    def __init__(self, tr: TranslationManager, state_mgr: StateManager):
        super().__init__()
        self.tr = tr
        self.state_mgr = state_mgr
        self._selected: SavedState | None = None
        self._build_ui()

    # ── Build ─────────────────────────────────────────────────────────────────

    def _build_ui(self):
        root = QHBoxLayout(self)
        root.setSpacing(12)
        root.setContentsMargins(4, 4, 4, 4)

        # ── Left: tree ─────────────────────────────────────────────────────
        left = QFrame()
        left.setObjectName("panel")
        left.setFixedWidth(280)
        ll = QVBoxLayout(left)
        ll.setContentsMargins(10, 10, 10, 10)
        ll.setSpacing(8)
        self._lbl_history_section = section_label(self.tr.get("history"))
        ll.addWidget(self._lbl_history_section)

        # Filters
        filter_row = QHBoxLayout()
        self._lbl_year_filter = QLabel(self.tr.get("year") + ":")
        filter_row.addWidget(self._lbl_year_filter)
        self._year_combo = QComboBox()
        self._year_combo.setFixedWidth(72)
        self._year_combo.addItem(self.tr.get("all"), None)
        self._year_combo.currentIndexChanged.connect(self._refresh_tree)
        filter_row.addWidget(self._year_combo)
        self._lbl_month_filter = QLabel(self.tr.get("month") + ":")
        filter_row.addWidget(self._lbl_month_filter)
        self._month_combo = QComboBox()
        self._month_combo.setFixedWidth(86)
        months = self.tr.get("months").split(",")
        self._month_combo.addItem(self.tr.get("all"), None)
        for i, m in enumerate(months, 1):
            self._month_combo.addItem(m, i)
        self._month_combo.currentIndexChanged.connect(self._refresh_tree)
        filter_row.addWidget(self._month_combo)
        ll.addLayout(filter_row)

        self._tree = QTreeWidget()
        self._tree.setHeaderHidden(True)
        self._tree.setRootIsDecorated(True)
        self._tree.itemClicked.connect(self._on_item_click)
        ll.addWidget(self._tree)

        btn_row = QHBoxLayout()
        refresh_btn = QPushButton("⟳")
        refresh_btn.setFixedWidth(36)
        refresh_btn.clicked.connect(self.refresh)
        self._load_btn = primary_btn(self.tr.get("load"))
        self._load_btn.clicked.connect(self._load_selected)
        self._del_btn = danger_btn(self.tr.get("delete"))
        self._del_btn.clicked.connect(self._delete_selected)
        btn_row.addWidget(refresh_btn)
        btn_row.addWidget(self._load_btn)
        btn_row.addWidget(self._del_btn)
        ll.addLayout(btn_row)

        root.addWidget(left)

        # ── Right: detail ───────────────────────────────────────────────────
        right = QVBoxLayout()
        self._detail_lbl = section_label(self.tr.get("detail"))
        right.addWidget(self._detail_lbl)
        self._event_lbl = QLabel("—")
        self._event_lbl.setObjectName("stat_value")
        right.addWidget(self._event_lbl)
        self._date_lbl = QLabel("")
        self._date_lbl.setObjectName("subtitle")
        right.addWidget(self._date_lbl)

        splitter = QSplitter(Qt.Orientation.Vertical)

        prizes_frame = QFrame()
        prizes_frame.setObjectName("panel")
        pl = QVBoxLayout(prizes_frame)
        pl.setContentsMargins(8, 8, 8, 8)
        self._lbl_prizes_section = section_label(self.tr.get("prizes"))
        pl.addWidget(self._lbl_prizes_section)
        self._prizes_tbl = SortableTable([
            (self.tr.get("id"),          48),
            (self.tr.get("prize_name"),   0),
            (self.tr.get("quantity"),   100),
            ("★",                        44),
        ])
        pl.addWidget(self._prizes_tbl)
        splitter.addWidget(prizes_frame)

        parts_frame = QFrame()
        parts_frame.setObjectName("panel")
        ptl = QVBoxLayout(parts_frame)
        ptl.setContentsMargins(8, 8, 8, 8)
        self._lbl_parts_section = section_label(self.tr.get("participants"))
        ptl.addWidget(self._lbl_parts_section)
        self._parts_tbl = SortableTable([
            (self.tr.get("id"),           48),
            (self.tr.get("participant"),   0),
            (self.tr.get("damage"),      110),
            (self.tr.get("percentage"),   80),
        ])
        ptl.addWidget(self._parts_tbl)
        splitter.addWidget(parts_frame)

        right.addWidget(splitter)
        root.addLayout(right)

    # ── Refresh ───────────────────────────────────────────────────────────────

    def refresh(self):
        self.state_mgr.load_all()
        self._repopulate_filters()
        self._refresh_tree()

    def _repopulate_filters(self):
        years = sorted({s.date_range.start_year for s in self.state_mgr.states}, reverse=True)
        self._year_combo.blockSignals(True)
        self._year_combo.clear()
        self._year_combo.addItem(self.tr.get("all"), None)
        for y in years:
            self._year_combo.addItem(str(y), y)
        self._year_combo.blockSignals(False)

    def _refresh_tree(self):
        self._tree.clear()
        year_f  = self._year_combo.currentData()
        month_f = self._month_combo.currentData()

        states = self.state_mgr.states
        if year_f  is not None:
            states = [s for s in states if s.date_range.start_year  == year_f]
        if month_f is not None:
            states = [s for s in states if s.date_range.start_month == month_f]

        grouped: dict[int, dict[int, list]] = {}
        for s in states:
            grouped.setdefault(s.date_range.start_year, {}).setdefault(
                s.date_range.start_month, []
            ).append(s)

        months_list = self.tr.get("months").split(",")
        for year in sorted(grouped.keys(), reverse=True):
            y_item = QTreeWidgetItem([str(year)])
            y_item.setForeground(0, QColor("#f0a500"))
            for month in sorted(grouped[year].keys()):
                m_name = months_list[month - 1] if month <= 12 else str(month)
                m_item = QTreeWidgetItem([m_name])
                m_item.setForeground(0, QColor("#8b92a8"))
                for state in grouped[year][month]:
                    s_item = QTreeWidgetItem([state.event or "—"])
                    s_item.setData(0, Qt.ItemDataRole.UserRole, state)
                    m_item.addChild(s_item)
                y_item.addChild(m_item)
            self._tree.addTopLevelItem(y_item)
        self._tree.expandAll()

    def _on_item_click(self, item: QTreeWidgetItem, _col: int):
        state: SavedState | None = item.data(0, Qt.ItemDataRole.UserRole)
        if state is None:
            return
        self._selected = state
        self._show_detail(state)

    def _show_detail(self, state: SavedState):
        self._event_lbl.setText(state.event or "—")
        self._date_lbl.setText(str(state.date_range))

        self._prizes_tbl.setRowCount(0)
        self._prizes_tbl.reset_sort()
        for p in state.prizes:
            r = self._prizes_tbl.rowCount()
            self._prizes_tbl.insertRow(r)
            self._prizes_tbl.setItem(r, 0, mono_item(p.id))
            self._prizes_tbl.setItem(r, 1, center_item(p.name))
            self._prizes_tbl.setItem(r, 2, mono_item(DistributionEngine.format_number(p.quantity)))
            st = center_item("★" if p.is_special else "")
            if p.is_special:
                st.setForeground(QColor("#f0a500"))
            self._prizes_tbl.setItem(r, 3, st)
            self._prizes_tbl.setRowHeight(r, 32)

        self._parts_tbl.setRowCount(0)
        self._parts_tbl.reset_sort()
        total_dmg = sum(p.damage for p in state.participants)
        for p in state.participants:
            r = self._parts_tbl.rowCount()
            self._parts_tbl.insertRow(r)
            pct = p.damage / total_dmg * 100 if total_dmg > 0 else 0
            self._parts_tbl.setItem(r, 0, mono_item(p.id))
            self._parts_tbl.setItem(r, 1, center_item(p.name))
            self._parts_tbl.setItem(r, 2, mono_item(DistributionEngine.format_number(p.damage)))
            self._parts_tbl.setItem(r, 3, mono_item(f"{pct:.3f}%"))
            self._parts_tbl.setRowHeight(r, 32)

    # ── Actions ───────────────────────────────────────────────────────────────

    def _load_selected(self):
        if not self._selected:
            return
        reply = QMessageBox.question(
            self, self.tr.get("confirm"), self.tr.get("confirm_new_state"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.tr.log_info("log_state_loaded", event=self._selected.event)
            self.state_loaded.emit(self._selected)

    def _delete_selected(self):
        if not self._selected:
            return
        reply = QMessageBox.question(
            self, self.tr.get("confirm"), self.tr.get("confirm_delete"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.state_mgr.delete(self._selected)
            self._selected = None
            self.refresh()

    def retranslate_ui(self):
        """Called by MainWindow when the language changes."""
        tr = self.tr
        # Table headers
        self._prizes_tbl.update_headers([
            tr.get("id"), tr.get("prize_name"), tr.get("quantity"), "★",
        ])
        self._parts_tbl.update_headers([
            tr.get("id"), tr.get("participant"), tr.get("damage"), tr.get("percentage"),
        ])
        # Section labels
        self._lbl_history_section.setText(tr.get("history").upper())
        self._detail_lbl.setText(tr.get("detail").upper())
        self._lbl_prizes_section.setText(tr.get("prizes").upper())
        self._lbl_parts_section.setText(tr.get("participants").upper())
        # Filter labels
        self._lbl_year_filter.setText(tr.get("year") + ":")
        self._lbl_month_filter.setText(tr.get("month") + ":")
        # Buttons
        self._load_btn.setText(tr.get("load"))
        self._del_btn.setText(tr.get("delete"))
        # Year combo: rebuild "All" item text
        cur_year = self._year_combo.currentData()
        self._year_combo.blockSignals(True)
        for i in range(self._year_combo.count()):
            if self._year_combo.itemData(i) is None:
                self._year_combo.setItemText(i, tr.get("all"))
                break
        self._year_combo.blockSignals(False)
        # Month combo: rebuild with new locale names
        months = tr.get("months").split(",")
        self._month_combo.blockSignals(True)
        cur_month = self._month_combo.currentData()
        self._month_combo.clear()
        self._month_combo.addItem(tr.get("all"), None)
        for i, m in enumerate(months, 1):
            self._month_combo.addItem(m, i)
        if cur_month is not None:
            for j in range(self._month_combo.count()):
                if self._month_combo.itemData(j) == cur_month:
                    self._month_combo.setCurrentIndex(j)
                    break
        self._month_combo.blockSignals(False)
        self._refresh_tree()
