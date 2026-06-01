from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLineEdit, QDoubleSpinBox, QPushButton, QCheckBox,
    QLabel, QMessageBox, QPlainTextEdit, QFrame,
    QCompleter,
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QColor, QStandardItemModel, QStandardItem

from models import Participant
from core.translations import TranslationManager
from core.distribution import DistributionEngine
from core.state_manager import StateManager
from ui.widgets import (
    primary_btn, danger_btn, SortableTable,
    center_item, mono_item, section_label,
)


class ParticipantsTab(QWidget):
    participants_changed = Signal()

    def __init__(self, tr: TranslationManager, state_mgr: StateManager | None = None):
        super().__init__()
        self.tr         = tr
        self._state_mgr = state_mgr
        self.participants: list[Participant] = []
        self._next_id   = 1
        self._editing_id: int | None = None
        self._build_ui()
        self._setup_completer()

    # ── Build ─────────────────────────────────────────────────────────────────

    def _build_ui(self):
        root = QHBoxLayout(self)
        root.setSpacing(12); root.setContentsMargins(4, 4, 4, 4)

        left = QFrame(); left.setObjectName("panel"); left.setFixedWidth(290)
        ll = QVBoxLayout(left); ll.setSpacing(10); ll.setContentsMargins(12, 12, 12, 12)

        self._lbl_add_section = section_label(self.tr.get("add"))
        ll.addWidget(self._lbl_add_section)

        self._lbl_participant = QLabel(self.tr.get("participant") + ":")
        ll.addWidget(self._lbl_participant)
        self._name_input = QLineEdit()
        self._name_input.setPlaceholderText(self.tr.get("participant") + "…")
        ll.addWidget(self._name_input)

        self._lbl_damage = QLabel(self.tr.get("damage") + ":")
        ll.addWidget(self._lbl_damage)
        self._dmg_spin = QDoubleSpinBox()
        self._dmg_spin.setRange(0, 10_000_000_000)
        self._dmg_spin.setDecimals(0); self._dmg_spin.setValue(0)
        ll.addWidget(self._dmg_spin)

        self._enabled_cb = QCheckBox(self.tr.get("enabled"))
        self._enabled_cb.setChecked(True)
        ll.addWidget(self._enabled_cb)

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
        self._batch_fmt_lbl = QLabel(self.tr.get("batch_participant_format"))
        self._batch_fmt_lbl.setWordWrap(True)
        self._batch_fmt_lbl.setObjectName("subtitle")
        bl.addWidget(self._batch_fmt_lbl)
        self._batch_edit = QPlainTextEdit()
        self._batch_edit.setPlaceholderText(self.tr.get("batch_participant_placeholder"))
        self._batch_edit.setMinimumHeight(100); self._batch_edit.setMaximumHeight(130)
        bl.addWidget(self._batch_edit)
        self._batch_load_btn = primary_btn(self.tr.get("load"))
        self._batch_load_btn.clicked.connect(self._handle_batch)
        bl.addWidget(self._batch_load_btn)
        ll.addWidget(self._batch_grp)

        ll.addStretch()
        self._total_lbl = QLabel("—")
        self._total_lbl.setObjectName("stat_value")
        ll.addWidget(self._total_lbl)

        self._clear_btn = danger_btn(self.tr.get("clear"))
        self._clear_btn.clicked.connect(self._clear_all)
        ll.addWidget(self._clear_btn)
        root.addWidget(left)

        right = QVBoxLayout()
        hdr_row = QHBoxLayout()
        self._lbl_table_section = section_label(self.tr.get("participants"))
        hdr_row.addWidget(self._lbl_table_section)
        hdr_row.addStretch()
        self._count_lbl = QLabel("0"); self._count_lbl.setObjectName("subtitle")
        hdr_row.addWidget(self._count_lbl)
        right.addLayout(hdr_row)

        self._table = SortableTable([
            (self.tr.get("id"), 48), (self.tr.get("participant"), 0),
            (self.tr.get("damage"), 110), (self.tr.get("percentage"), 80),
            (self.tr.get("enabled"), 60), ("✎", 38), ("✖", 38), ("⏻", 38),
        ], action_cols={5, 6, 7})
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
        names: set[str] = {p.name for p in self.participants}
        if self._state_mgr:
            for s in self._state_mgr.states:
                names.update(p.name for p in s.participants)
        self._completer_model.clear()
        for name in sorted(names, key=str.lower):
            self._completer_model.appendRow(QStandardItem(name))

    def refresh_completer_from_states(self):
        self._refresh_completer()

    # ── Logic ─────────────────────────────────────────────────────────────────

    def _handle_add(self):
        name = self._name_input.text().strip()
        if not name:
            QMessageBox.warning(self, self.tr.get("error"), self.tr.get("name_required")); return
        dmg = self._dmg_spin.value()
        if dmg < 0:
            QMessageBox.warning(self, self.tr.get("error"), self.tr.get("damage_must_be_non_negative")); return
        enabled = self._enabled_cb.isChecked()

        if self._editing_id is not None:
            for p in self.participants:
                if p.id == self._editing_id:
                    p.name, p.damage, p.enabled = name, dmg, enabled; break
            self.tr.log_info("log_participant_edited", name=name)
            self._editing_id = None
            self._add_btn.setText(self.tr.get("add")); self._cancel_btn.setVisible(False)
        else:
            if any(p.name.lower() == name.lower() for p in self.participants):
                QMessageBox.warning(self, self.tr.get("error"), self.tr.get("name_exists")); return
            self.participants.append(Participant(self._next_id, name, dmg, enabled))
            self.tr.log_info("log_participant_added", name=name)
            self._next_id += 1

        self._reset_form(); self._refresh(); self.participants_changed.emit()

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
            if parts[1] == "#":
                before = len(self.participants)
                self.participants = [p for p in self.participants if p.name.lower() != name.lower()]
                if len(self.participants) < before:
                    self.tr.log_info("log_participant_deleted", name=name)
                continue
            try:
                dmg = float(parts[1])
            except ValueError:
                errors.append(f"{self.tr.get('invalid_damage')}: {line}"); continue
            existing = next((p for p in self.participants if p.name.lower() == name.lower()), None)
            if existing:
                existing.damage = dmg; self.tr.log_info("log_participant_edited", name=name)
            else:
                self.participants.append(Participant(self._next_id, name, dmg))
                self.tr.log_info("log_participant_added", name=name)
                self._next_id += 1
        if errors: QMessageBox.warning(self, self.tr.get("error"), "\n".join(errors))
        self._batch_edit.clear(); self._refresh(); self.participants_changed.emit()

    def _on_cell_click(self, row: int, col: int):
        if col == 5: self._start_edit(row)
        elif col == 6: self._delete_row(row)
        elif col == 7: self._toggle_row(row)

    def _start_edit(self, row: int):
        item = self._table.item(row, 0)
        if not item: return
        p = next((x for x in self.participants if x.id == int(item.text())), None)
        if not p: return
        self._editing_id = p.id
        self._name_input.setText(p.name); self._dmg_spin.setValue(p.damage)
        self._enabled_cb.setChecked(p.enabled)
        self._add_btn.setText(self.tr.get("save")); self._cancel_btn.setVisible(True)

    def _cancel_edit(self):
        self._editing_id = None; self._reset_form()
        self._add_btn.setText(self.tr.get("add")); self._cancel_btn.setVisible(False)

    def _delete_row(self, row: int):
        item = self._table.item(row, 0)
        if not item: return
        pid = int(item.text())
        p = next((x for x in self.participants if x.id == pid), None)
        if QMessageBox.question(self, self.tr.get("confirm"), self.tr.get("confirm_delete_participant"),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                ) == QMessageBox.StandardButton.Yes:
            self.participants = [x for x in self.participants if x.id != pid]
            if p: self.tr.log_info("log_participant_deleted", name=p.name)
            self._refresh(); self.participants_changed.emit()

    def _toggle_row(self, row: int):
        item = self._table.item(row, 0)
        if not item: return
        pid = int(item.text())
        for p in self.participants:
            if p.id == pid:
                p.enabled = not p.enabled
                self.tr.log_info("log_participant_toggled", name=p.name); break
        self._refresh(); self.participants_changed.emit()

    def _clear_all(self):
        if not self.participants: return
        if QMessageBox.question(self, self.tr.get("confirm"), self.tr.get("confirm_clear_participants"),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                ) == QMessageBox.StandardButton.Yes:
            self.participants.clear(); self._next_id = 1
            self._refresh(); self.participants_changed.emit()

    def _reset_form(self):
        self._name_input.clear(); self._dmg_spin.setValue(0); self._enabled_cb.setChecked(True)

    # ── Table refresh ─────────────────────────────────────────────────────────

    def _refresh(self):
        self._table.setRowCount(0); self._table.reset_sort()
        active = [p for p in self.participants if p.enabled]
        total_dmg = sum(p.damage for p in active)

        for p in self.participants:
            r = self._table.rowCount(); self._table.insertRow(r)
            pct = f"{p.damage/total_dmg*100:.3f}%" if (p.enabled and total_dmg > 0) else "—"
            self._table.setItem(r, 0, mono_item(p.id))
            self._table.setItem(r, 1, center_item(p.name))
            self._table.setItem(r, 2, mono_item(DistributionEngine.format_number(p.damage)))
            self._table.setItem(r, 3, mono_item(pct))
            en = center_item("✓" if p.enabled else "✗")
            en.setForeground(QColor("#2dd284") if p.enabled else QColor("#e05252"))
            self._table.setItem(r, 4, en)
            self._table.setItem(r, 5, center_item("✎"))
            self._table.setItem(r, 6, center_item("✖"))
            tog = center_item("⏻")
            tog.setForeground(QColor("#4da6ff") if p.enabled else QColor("#505570"))
            self._table.setItem(r, 7, tog)
            self._table.setRowHeight(r, 36)
            if not p.enabled:
                for c in range(self._table.columnCount()):
                    it = self._table.item(r, c)
                    if it: it.setForeground(QColor("#505570"))

        n = len(active)
        self._count_lbl.setText(f"{len(self.participants)} ({n} {self.tr.get('enabled').lower()})")
        self._total_lbl.setText(
            f"{self.tr.get('total_damage')}:\n{DistributionEngine.format_number(total_dmg)}")
        self._refresh_completer()

    # ── State load ────────────────────────────────────────────────────────────

    def load_participants(self, participants: list[Participant], next_id: int):
        self.participants = [p.copy() for p in participants]; self._next_id = next_id
        self._editing_id = None; self._reset_form()
        self._add_btn.setText(self.tr.get("add")); self._cancel_btn.setVisible(False)
        self._refresh()

    # ── Retranslation ─────────────────────────────────────────────────────────

    def retranslate_ui(self):
        tr = self.tr
        self._lbl_add_section.setText(tr.get("add").upper())
        self._lbl_participant.setText(tr.get("participant") + ":")
        self._name_input.setPlaceholderText(tr.get("participant") + "…")
        self._lbl_damage.setText(tr.get("damage") + ":")
        self._enabled_cb.setText(tr.get("enabled"))
        self._add_btn.setText(tr.get("save") if self._editing_id is not None else tr.get("add"))
        self._cancel_btn.setText(tr.get("cancel"))
        self._batch_grp.setTitle(tr.get("batch_input"))
        self._batch_fmt_lbl.setText(tr.get("batch_participant_format"))
        self._batch_edit.setPlaceholderText(tr.get("batch_participant_placeholder"))
        self._batch_load_btn.setText(tr.get("load"))
        self._clear_btn.setText(tr.get("clear"))
        self._lbl_table_section.setText(tr.get("participants").upper())
        self._table.update_headers([
            tr.get("id"), tr.get("participant"), tr.get("damage"),
            tr.get("percentage"), tr.get("enabled"), "✎", "✖", "⏻",
        ])
        self._refresh()
