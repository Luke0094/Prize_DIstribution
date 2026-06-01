"""Reusable widget helpers shared across all tabs."""
from PySide6.QtWidgets import (
    QPushButton, QLabel, QTableWidget, QHeaderView,
    QFrame, QSizePolicy, QTableWidgetItem,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor


# ── Buttons ───────────────────────────────────────────────────────────────────

def primary_btn(text: str, parent=None) -> QPushButton:
    btn = QPushButton(text, parent)
    btn.setObjectName("primary")
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    return btn


def danger_btn(text: str, parent=None) -> QPushButton:
    btn = QPushButton(text, parent)
    btn.setObjectName("danger")
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    return btn


def icon_btn(icon: str, tooltip: str = "", size: int = 32, parent=None) -> QPushButton:
    btn = QPushButton(icon, parent)
    btn.setObjectName("icon_btn")
    btn.setFixedSize(size, size)
    if tooltip:
        btn.setToolTip(tooltip)
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    return btn


# ── Labels ────────────────────────────────────────────────────────────────────

def section_label(text: str, parent=None) -> QLabel:
    lbl = QLabel(text.upper(), parent)
    lbl.setObjectName("section_label")
    return lbl


def stat_value_label(text: str = "—", parent=None) -> QLabel:
    lbl = QLabel(text, parent)
    lbl.setObjectName("stat_value")
    lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    return lbl


# ── Separator ─────────────────────────────────────────────────────────────────

def hsep() -> QFrame:
    f = QFrame()
    f.setFrameShape(QFrame.Shape.HLine)
    f.setFrameShadow(QFrame.Shadow.Sunken)
    return f


# ── Table factory ─────────────────────────────────────────────────────────────

def make_table(columns: list[tuple[str, int]]) -> QTableWidget:
    tbl = QTableWidget()
    tbl.setColumnCount(len(columns))
    tbl.setHorizontalHeaderLabels([c[0] for c in columns])
    tbl.verticalHeader().setVisible(False)
    tbl.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
    tbl.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
    tbl.setAlternatingRowColors(True)
    tbl.horizontalHeader().setHighlightSections(False)
    tbl.setShowGrid(True)
    tbl.setWordWrap(False)
    tbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
    tbl.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
    tbl.viewport().setAutoFillBackground(True)  # ensure theme propagates to viewport
    for i, (_, w) in enumerate(columns):
        if w == 0:
            tbl.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)
        else:
            tbl.setColumnWidth(i, w)
            tbl.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeMode.Interactive)
    return tbl


# ── Table item helpers ────────────────────────────────────────────────────────

def center_item(text: str) -> QTableWidgetItem:
    item = QTableWidgetItem(str(text))
    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
    return item


def mono_item(text: str) -> QTableWidgetItem:
    item = QTableWidgetItem(str(text))
    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
    item.setFont(QFont("Consolas", 9))
    return item


# ── Sortable table ────────────────────────────────────────────────────────────

class SortableTable(QTableWidget):
    """
    QTableWidget with click-on-header column sorting.
    Sort direction is shown with a distinct ↑ / ↓ indicator.
    Action columns (by index) are excluded from sorting.
    """
    def __init__(self, columns: list[tuple[str, int]], action_cols: set[int] | None = None):
        super().__init__()
        self._action_cols  = action_cols or set()
        self._sort_col     = -1
        self._sort_asc     = True
        self._orig_labels  = [c[0] for c in columns]

        self.setColumnCount(len(columns))
        self.setHorizontalHeaderLabels(self._orig_labels)
        self.verticalHeader().setVisible(False)
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.setAlternatingRowColors(True)
        self.horizontalHeader().setHighlightSections(False)
        self.setShowGrid(True)
        self.setWordWrap(False)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
        self.viewport().setAutoFillBackground(True)

        for i, (_, w) in enumerate(columns):
            if w == 0:
                self.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)
            else:
                self.setColumnWidth(i, w)
                self.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeMode.Interactive)

        self.horizontalHeader().sectionClicked.connect(self._on_header_click)
        self.horizontalHeader().setCursor(Qt.CursorShape.PointingHandCursor)

    def _on_header_click(self, col: int):
        if col in self._action_cols:
            return
        if self._sort_col == col:
            self._sort_asc = not self._sort_asc
        else:
            self._sort_col = col
            self._sort_asc = True
        self._update_labels()
        self.sortItems(
            col,
            Qt.SortOrder.AscendingOrder if self._sort_asc else Qt.SortOrder.DescendingOrder,
        )

    def _update_labels(self):
        for i, base in enumerate(self._orig_labels):
            h = self.horizontalHeaderItem(i)
            if h is None:
                continue
            if i == self._sort_col:
                # Prominent arrows using full-width chars
                arrow = "  ⬆" if self._sort_asc else "  ⬇"
                h.setText(base + arrow)
            else:
                h.setText(base)

    def reset_sort(self):
        self._sort_col = -1
        self._sort_asc = True
        for i, base in enumerate(self._orig_labels):
            h = self.horizontalHeaderItem(i)
            if h:
                h.setText(base)

    def update_headers(self, labels: list[str]):
        """Call after retranslation to refresh header text."""
        self._orig_labels = labels
        self.setHorizontalHeaderLabels(labels)
        self.reset_sort()
