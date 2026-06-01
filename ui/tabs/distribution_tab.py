from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame,
    QComboBox, QCheckBox, QLabel, QSplitter,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from models import Prize, Participant
from core.translations import TranslationManager
from core.distribution import DistributionEngine
from ui.widgets import (
    primary_btn, SortableTable, center_item, mono_item,
    section_label, stat_value_label,
)


class DistributionTab(QWidget):
    def __init__(self, tr: TranslationManager):
        super().__init__()
        self.tr = tr
        self._integer_only = True
        self._prizes: list[Prize] = []
        self._participants: list[Participant] = []
        self._received: set[tuple] = set()
        self._build_ui()

    # ── Build ─────────────────────────────────────────────────────────────────

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setSpacing(10); root.setContentsMargins(4, 4, 4, 4)

        # Toolbar
        toolbar = QHBoxLayout()
        self._lbl_select_prize = QLabel(self.tr.get("select_prize") + ":")
        toolbar.addWidget(self._lbl_select_prize)
        self._prize_combo = QComboBox(); self._prize_combo.setMinimumWidth(220)
        self._prize_combo.currentIndexChanged.connect(self._refresh)
        toolbar.addWidget(self._prize_combo)
        toolbar.addSpacing(16)
        self._int_cb = QCheckBox(self.tr.get("integer_only"))
        self._int_cb.setChecked(True)
        self._int_cb.toggled.connect(self._on_int_toggled)
        toolbar.addWidget(self._int_cb)
        toolbar.addStretch()
        self._refresh_btn = primary_btn("⟳  " + self.tr.get("refresh"))
        self._refresh_btn.setFixedWidth(140)
        self._refresh_btn.clicked.connect(self._refresh)
        toolbar.addWidget(self._refresh_btn)
        root.addLayout(toolbar)

        # Splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Distribution table frame
        dist_frame = QFrame(); dist_frame.setObjectName("panel")
        dl = QVBoxLayout(dist_frame); dl.setContentsMargins(10, 10, 10, 10)
        self._lbl_dist_section = section_label(self.tr.get("distribution"))
        dl.addWidget(self._lbl_dist_section)
        self._table = SortableTable([
            (self.tr.get("id"), 48), (self.tr.get("participant"), 0),
            (self.tr.get("quantity"), 110), (self.tr.get("percentage"), 90),
            (self.tr.get("received"), 80),
        ], action_cols={4})
        self._table.cellClicked.connect(self._toggle_received)
        dl.addWidget(self._table)
        splitter.addWidget(dist_frame)

        # Stats panel
        stats_frame = QFrame(); stats_frame.setObjectName("panel")
        stats_frame.setFixedWidth(210)
        sl = QVBoxLayout(stats_frame); sl.setContentsMargins(12, 12, 12, 12); sl.setSpacing(8)
        self._lbl_summary_section = section_label(self.tr.get("summary"))
        sl.addWidget(self._lbl_summary_section)

        def _stat(label: str):
            lbl = QLabel(label); sl.addWidget(lbl)
            v = stat_value_label(); sl.addWidget(v)
            return lbl, v

        self._lbl_dmg,      self._stat_dmg      = _stat(self.tr.get("total_damage"))
        self._lbl_parts,    self._stat_parts     = _stat(self.tr.get("participants"))
        self._lbl_qty,      self._stat_qty       = _stat(self.tr.get("quantity"))
        self._lbl_received, self._stat_received  = _stat(self.tr.get("received"))
        sl.addStretch()
        splitter.addWidget(stats_frame)
        splitter.setStretchFactor(0, 1); splitter.setStretchFactor(1, 0)
        root.addWidget(splitter)

    # ── Public API ────────────────────────────────────────────────────────────

    def update_prizes(self, prizes: list[Prize]):
        self._prizes = prizes
        current_id = self._prize_combo.currentData()
        self._prize_combo.blockSignals(True)
        self._prize_combo.clear()
        for p in prizes:
            prefix = "★ " if p.is_special else ""
            self._prize_combo.addItem(
                f"{prefix}{p.name}  [{DistributionEngine.format_number(p.quantity)}]",
                userData=p.id)
        for i in range(self._prize_combo.count()):
            if self._prize_combo.itemData(i) == current_id:
                self._prize_combo.setCurrentIndex(i); break
        self._prize_combo.blockSignals(False)
        self._refresh()

    def update_participants(self, participants: list[Participant]):
        self._participants = participants
        self._refresh()

    def refresh_now(self):
        self._refresh()

    def set_integer_only(self, value: bool):
        self._int_cb.blockSignals(True); self._int_cb.setChecked(value)
        self._integer_only = value; self._int_cb.blockSignals(False)
        self._refresh()

    # ── Internal ─────────────────────────────────────────────────────────────

    def _on_int_toggled(self, checked: bool):
        self._integer_only = checked; self._refresh()

    def _refresh(self):
        self._table.setRowCount(0); self._table.reset_sort()
        for sv in (self._stat_dmg, self._stat_parts, self._stat_qty, self._stat_received):
            sv.setText("—")

        prize = self._current_prize()
        if not prize: return
        active = [p for p in self._participants if p.enabled]
        if not active: return

        if prize.is_special:
            pool      = sorted(active, key=lambda p: p.damage, reverse=True)[:prize.top_winners]
            total_dmg = sum(p.damage for p in pool)
        else:
            pool = active; total_dmg = sum(p.damage for p in active)
        if total_dmg == 0: return

        dist = DistributionEngine.calculate(pool, total_dmg, prize.quantity, self._integer_only)
        total_assigned = sum(qty for _, _, qty in dist)
        received_count = 0

        for pid, name, qty in dist:
            pct = qty / prize.quantity * 100 if prize.quantity > 0 else 0
            key = (prize.name, name)
            is_recv = key in self._received
            if is_recv: received_count += 1

            r = self._table.rowCount(); self._table.insertRow(r)
            self._table.setItem(r, 0, mono_item(pid))
            self._table.setItem(r, 1, center_item(name))
            self._table.setItem(r, 2, mono_item(DistributionEngine.format_number(qty, self._integer_only)))
            self._table.setItem(r, 3, mono_item(f"{pct:.3f}%"))
            recv_item = center_item("☑" if is_recv else "☐")
            if is_recv:
                recv_item.setForeground(QColor("#2dd284"))
                for c in range(self._table.columnCount()):
                    it = self._table.item(r, c)
                    if it: it.setForeground(QColor("#2dd284"))
            self._table.setItem(r, 4, recv_item)
            self._table.setRowHeight(r, 36)

        self._stat_dmg.setText(DistributionEngine.format_number(total_dmg))
        self._stat_parts.setText(str(len(dist)))
        self._stat_qty.setText(DistributionEngine.format_number(total_assigned, self._integer_only))
        self._stat_received.setText(f"{received_count}/{len(dist)}")

    def _toggle_received(self, row: int, col: int):
        if col != 4: return
        prize = self._current_prize()
        if not prize: return
        name_item = self._table.item(row, 1)
        if not name_item: return
        key = (prize.name, name_item.text())
        self._received.discard(key) if key in self._received else self._received.add(key)
        self._refresh()

    def _current_prize(self) -> Prize | None:
        pid = self._prize_combo.currentData()
        return next((p for p in self._prizes if p.id == pid), None)

    def get_distributions(self) -> dict:
        result = {}
        active = [p for p in self._participants if p.enabled]
        if not active: return result
        for prize in self._prizes:
            if prize.is_special:
                pool      = sorted(active, key=lambda p: p.damage, reverse=True)[:prize.top_winners]
                total_dmg = sum(p.damage for p in pool)
            else:
                pool = active; total_dmg = sum(p.damage for p in active)
            if total_dmg == 0: continue
            dist = DistributionEngine.calculate(pool, total_dmg, prize.quantity, self._integer_only)
            result[prize.id] = [(pid, name, qty) for pid, name, qty in dist]
        return result

    # ── Retranslation ─────────────────────────────────────────────────────────

    def retranslate_ui(self):
        tr = self.tr
        self._lbl_select_prize.setText(tr.get("select_prize") + ":")
        self._int_cb.setText(tr.get("integer_only"))
        self._refresh_btn.setText("⟳  " + tr.get("refresh"))
        self._lbl_dist_section.setText(tr.get("distribution").upper())
        self._lbl_summary_section.setText(tr.get("summary").upper())
        self._lbl_dmg.setText(tr.get("total_damage"))
        self._lbl_parts.setText(tr.get("participants"))
        self._lbl_qty.setText(tr.get("quantity"))
        self._lbl_received.setText(tr.get("received"))
        self._table.update_headers([
            tr.get("id"), tr.get("participant"), tr.get("quantity"),
            tr.get("percentage"), tr.get("received"),
        ])
        self.update_prizes(self._prizes)
