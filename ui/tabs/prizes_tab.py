from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLineEdit, QDoubleSpinBox, QSpinBox, QCheckBox,
    QPushButton, QLabel, QMessageBox, QPlainTextEdit, QFrame,
    QCompleter,
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QColor, QStandardItemModel, QStandardItem

from models import Prize
from core.translations import TranslationManager
from core.distribution import DistributionEngine
from core.state_manager import StateManager
from ui.widgets import (
    primary_btn, danger_btn, SortableTable,
    center_item, mono_item, section_label,
)


class PrizesTab(QWidget):
    prizes_changed = Signal()

    def __init__(self, tr: TranslationManager, state_mgr: StateManager | None = None):
        super().__init__()
        self.tr         = tr
        self._state_mgr = state_mgr
        self.prizes: list[Prize] = []
        self._next_id   = 1
        self._editing_id: int | None = None
        self._build_ui()
        self._setup_completer()

    # ── Build ─────────────────────────────────────────────────────────────────

    def _build_ui(self):
        root = QHBoxLayout(self)
        root.setSpacing(12)
        root.setContentsMargins(4, 4, 4, 4)

        left = QFrame(); left.setObjectName("panel"); left.setFixedWidth(290)
        ll = QVBoxLayout(left); ll.setSpacing(10); ll.setContentsMargins(12, 12, 12, 12)

        self._lbl_add_section = section_label(self.tr.get("add"))
        ll.addWidget(self._lbl_add_section)

        self._lbl_prize_name = QLabel(self.tr.get("prize_name") + ":")
        ll.addWidget(self._lbl_prize_name)
        self._name_input = QLineEdit()
        self._name_input.setPlaceholderText(self.tr.get("prize_name") + "…")
        ll.addWidget(self._name_input)

        self._lbl_quantity = QLabel(self.tr.get("quantity") + ":")
        ll.addWidget(self._lbl_quantity)
        self._qty_spin = QDoubleSpinBox()
        self._qty_spin.setRange(1, 10_000_000)
        self._qty_spin.setDecimals(0)
        self._qty_spin.setValue(1)
        ll.addWidget(self._qty_spin)

        self._special_cb = QCheckBox(self.tr.get("special_prize"))
        self._special_cb.toggled.connect(self._toggle_winners_vis)
        ll.addWidget(self._special_cb)

        self._winners_lbl = QLabel(self.tr.get("top_winners") + ":")
        self._winners_spin = QSpinBox(); self._winners_spin.setRange(1, 10_000)
        ll.addWidget(self._winners_lbl); ll.addWidget(self._winners_spin)
        self._winners_lbl.setVisible(False); self._winners_spin.setVisible(False)

        ll.addSpacing(4)
        self._add_btn = primary_btn(self.tr.get("add"))
        self._add_btn.clicked.connect(self._handle_add)
        ll.addWidget(self._add_btn)

        self._cancel_btn = QPushButton(self.tr.get("cancel"))
        self._cancel_btn.setVisible(False)
        self._cancel_btn.clicked.connect(self._cancel_edit)
        ll.addWidget(self._cancel_btn)

        ll.addSpacing(8)

        self._batch_grp = QGroupBox(self.tr.get("batch_input"))
        bl = QVBoxLayout(self._batch_grp)
        self._batch_fmt_lbl = QLabel(self.tr.get("batch_prize_format"))
        self._batch_fmt_lbl.setWordWrap(True)
        self._batch_fmt_lbl.setObjectName("subtitle")
        bl.addWidget(self._batch_fmt_lbl)
        self._batch_edit = QPlainTextEdit()
        self._batch_edit.setPlaceholderText(self.tr.get("batch_prize_placeholder"))
        self._batch_edit.setMinimumHeight(100)
        self._batch_edit.setMaximumHeight(130)
        bl.addWidget(self._batch_edit)
        self._batch_load_btn = primary_btn(self.tr.get("load"))
        self._batch_load_btn.clicked.connect(self._handle_batch)
        bl.addWidget(self._batch_load_btn)
        ll.addWidget(self._batch_grp)

        ll.addStretch()
        self._clear_btn = danger_btn(self.tr.get("clear"))
        self._clear_btn.clicked.connect(self._clear_all)
        ll.addWidget(self._clear_btn)
        root.addWidget(left)

        right = QVBoxLayout()
        hdr = QHBoxLayout()
        self._lbl_table_section = section_label(self.tr.get("prizes"))
        hdr.addWidget(self._lbl_table_section)
        hdr.addStretch()
        self._count_lbl = QLabel("0"); self._count_lbl.setObjectName("subtitle")
        hdr.addWidget(self._count_lbl)
        right.addLayout(hdr)

        self._table = SortableTable([
            (self.tr.get("id"), 48), (self.tr.get("prize_name"), 0),
            (self.tr.get("quantity"), 100), ("★", 44),
            (self.tr.get("top_winners"), 76), ("✎", 38), ("✖", 38),
        ], action_cols={5, 6})
        self._table.cellClicked.connect(self._on_cell_click)
        right.addWidget(self._table)
        root.addLayout(right)

    # ── Autocomplete ──────────────────────────────────────────────────────────

    def _setup_completer(self):
        self._completer_model = QStandardItemModel()
        c = QCompleter(self._completer_model, self._name_input)
        c.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        c.setFilterMode(Qt.MatchFlag.MatchContains)
        c.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self._name_input.setCompleter(c)
        self._refresh_completer()

    def _refresh_completer(self):
        names: set[str] = {p.name for p in self.prizes}
        if self._state_mgr:
            for s in self._state_mgr.states:
                names.update(p.name for p in s.prizes)
        self._completer_model.clear()
        for name in sorted(names, key=str.lower):
            self._completer_model.appendRow(QStandardItem(name))

    def refresh_completer_from_states(self):
        self._refresh_completer()

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _toggle_winners_vis(self, checked: bool):
        self._winners_lbl.setVisible(checked)
        self._winners_spin.setVisible(checked)

    # ── Logic ─────────────────────────────────────────────────────────────────

    def _handle_add(self):
        name = self._name_input.text().strip()
        if not name:
            QMessageBox.warning(self, self.tr.get("error"), self.tr.get("name_required")); return
        qty = self._qty_spin.value()
        if qty <= 0:
            QMessageBox.warning(self, self.tr.get("error"), self.tr.get("quantity_must_be_positive")); return
        is_special = self._special_cb.isChecked()
        top_w = self._winners_spin.value() if is_special else 1

        if self._editing_id is not None:
            for p in self.prizes:
                if p.id == self._editing_id:
                    p.name, p.quantity, p.is_special, p.top_winners = name, qty, is_special, top_w
                    break
            self.tr.log_info("log_prize_edited", name=name)
            self._editing_id = None
            self._add_btn.setText(self.tr.get("add"))
            self._cancel_btn.setVisible(False)
        else:
            if any(p.name.lower() == name.lower() for p in self.prizes):
                QMessageBox.warning(self, self.tr.get("error"), self.tr.get("name_exists")); return
            self.prizes.append(Prize(self._next_id, name, qty, is_special, top_w))
            self.tr.log_info("log_prize_added", name=name)
            self._next_id += 1

        self._reset_form(); self._refresh(); self.prizes_changed.emit()

    def _handle_batch(self):
        text = self._batch_edit.toPlainText().strip()
        if not text: return
        errors = []
        for line in text.splitlines():
            line = line.strip()
            if not line: continue
            parts = [p.strip() for p in line.split(":")]
            if len(parts) < 2:
                errors.append(f"{self.tr.get('missing_separator')}: {line}"); continue
            name = parts[0]
            if not name:
                errors.append(f"{self.tr.get('missing_name')}: {line}"); continue
            try:
                qty = float(parts[1])
            except ValueError:
                errors.append(f"{self.tr.get('invalid_quantity')}: {line}"); continue
            is_special = len(parts) >= 3 and parts[2].lower() == "s"
            top_w = 1
            if is_special and len(parts) >= 4:
                try: top_w = int(parts[3])
                except ValueError:
                    errors.append(f"{self.tr.get('invalid_winners')}: {line}"); continue
            existing = next((p for p in self.prizes if p.name.lower() == name.lower()), None)
            if existing:
                existing.quantity, existing.is_special, existing.top_winners = qty, is_special, top_w
                self.tr.log_info("log_prize_edited", name=name)
            else:
                self.prizes.append(Prize(self._next_id, name, qty, is_special, top_w))
                self.tr.log_info("log_prize_added", name=name)
                self._next_id += 1
        if errors: QMessageBox.warning(self, self.tr.get("error"), "\n".join(errors))
        self._batch_edit.clear(); self._refresh(); self.prizes_changed.emit()

    def _on_cell_click(self, row: int, col: int):
        if col == 5: self._start_edit(row)
        elif col == 6: self._delete_row(row)

    def _start_edit(self, row: int):
        item = self._table.item(row, 0)
        if not item: return
        prize = next((p for p in self.prizes if p.id == int(item.text())), None)
        if not prize: return
        self._editing_id = prize.id
        self._name_input.setText(prize.name); self._qty_spin.setValue(prize.quantity)
        self._special_cb.setChecked(prize.is_special); self._winners_spin.setValue(prize.top_winners)
        self._add_btn.setText(self.tr.get("save")); self._cancel_btn.setVisible(True)

    def _cancel_edit(self):
        self._editing_id = None; self._reset_form()
        self._add_btn.setText(self.tr.get("add")); self._cancel_btn.setVisible(False)

    def _delete_row(self, row: int):
        item = self._table.item(row, 0)
        if not item: return
        pid = int(item.text())
        prize = next((p for p in self.prizes if p.id == pid), None)
        if QMessageBox.question(self, self.tr.get("confirm"), self.tr.get("confirm_delete_prize"),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                ) == QMessageBox.StandardButton.Yes:
            self.prizes = [p for p in self.prizes if p.id != pid]
            if prize: self.tr.log_info("log_prize_deleted", name=prize.name)
            self._refresh(); self.prizes_changed.emit()

    def _clear_all(self):
        if not self.prizes: return
        if QMessageBox.question(self, self.tr.get("confirm"), self.tr.get("confirm_clear_prizes"),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                ) == QMessageBox.StandardButton.Yes:
            self.prizes.clear(); self._next_id = 1; self._refresh(); self.prizes_changed.emit()

    def _reset_form(self):
        self._name_input.clear(); self._qty_spin.setValue(1); self._special_cb.setChecked(False)
        self._winners_spin.setValue(1)

    # ── Table refresh ─────────────────────────────────────────────────────────

    def _refresh(self):
        self._table.setRowCount(0); self._table.reset_sort()
        for prize in self.prizes:
            r = self._table.rowCount(); self._table.insertRow(r)
            self._table.setItem(r, 0, mono_item(prize.id))
            self._table.setItem(r, 1, center_item(prize.name))
            self._table.setItem(r, 2, mono_item(DistributionEngine.format_number(prize.quantity)))
            star = center_item("★" if prize.is_special else "")
            if prize.is_special: star.setForeground(QColor("#f0a500"))
            self._table.setItem(r, 3, star)
            self._table.setItem(r, 4, mono_item(prize.top_winners if prize.is_special else "—"))
            self._table.setItem(r, 5, center_item("✎"))
            self._table.setItem(r, 6, center_item("✖"))
            self._table.setRowHeight(r, 36)
        self._count_lbl.setText(f"{len(self.prizes)} {self.tr.get('prizes').lower()}")
        self._refresh_completer()

    # ── State load ────────────────────────────────────────────────────────────

    def load_prizes(self, prizes: list[Prize], next_id: int):
        self.prizes = [p.copy() for p in prizes]; self._next_id = next_id
        self._editing_id = None; self._reset_form()
        self._add_btn.setText(self.tr.get("add")); self._cancel_btn.setVisible(False)
        self._refresh()

    # ── Retranslation ─────────────────────────────────────────────────────────

    def retranslate_ui(self):
        tr = self.tr
        self._lbl_add_section.setText(tr.get("add").upper())
        self._lbl_prize_name.setText(tr.get("prize_name") + ":")
        self._name_input.setPlaceholderText(tr.get("prize_name") + "…")
        self._lbl_quantity.setText(tr.get("quantity") + ":")
        self._special_cb.setText(tr.get("special_prize"))
        self._winners_lbl.setText(tr.get("top_winners") + ":")
        self._add_btn.setText(tr.get("save") if self._editing_id is not None else tr.get("add"))
        self._cancel_btn.setText(tr.get("cancel"))
        self._batch_grp.setTitle(tr.get("batch_input"))
        self._batch_fmt_lbl.setText(tr.get("batch_prize_format"))
        self._batch_edit.setPlaceholderText(tr.get("batch_prize_placeholder"))
        self._batch_load_btn.setText(tr.get("load"))
        self._clear_btn.setText(tr.get("clear"))
        self._lbl_table_section.setText(tr.get("prizes").upper())
        self._table.update_headers([
            tr.get("id"), tr.get("prize_name"), tr.get("quantity"),
            "★", tr.get("top_winners"), "✎", "✖",
        ])
        self._count_lbl.setText(f"{len(self.prizes)} {tr.get('prizes').lower()}")
