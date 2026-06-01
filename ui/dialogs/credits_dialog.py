import webbrowser

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QFrame,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from core.translations import TranslationManager
from ui.widgets import hsep


class CreditsDialog(QDialog):
    def __init__(self, tr: TranslationManager, parent=None):
        super().__init__(parent)
        self.tr = tr
        self.setWindowTitle(self.tr.get("credits"))
        self.setFixedSize(420, 370)
        self.setWindowFlag(Qt.WindowType.WindowContextHelpButtonHint, False)
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setSpacing(14)
        root.setContentsMargins(28, 24, 28, 20)

        # ── Developer ─────────────────────────────────────────────────────────
        dev_lbl = QLabel(self.tr.get("developer"))
        dev_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        dev_font = QFont()
        dev_font.setPointSize(13)
        dev_font.setBold(True)
        dev_lbl.setFont(dev_font)
        root.addWidget(dev_lbl)

        dev_row = QHBoxLayout()
        dev_row.addStretch()

        name_lbl = QLabel("Luke0094")
        name_font = QFont()
        name_font.setPointSize(11)
        name_lbl.setFont(name_font)
        dev_row.addWidget(name_lbl)

        github_btn = QPushButton("  GitHub")
        github_btn.setFixedWidth(100)
        github_btn.clicked.connect(
            lambda: webbrowser.open("https://github.com/Luke0094/Prize_DIstribution")
        )
        dev_row.addWidget(github_btn)
        dev_row.addStretch()
        root.addLayout(dev_row)

        root.addWidget(hsep())

        # ── Donations ─────────────────────────────────────────────────────────
        don_lbl = QLabel(self.tr.get("donations"))
        don_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        don_font = QFont()
        don_font.setPointSize(12)
        don_font.setBold(True)
        don_lbl.setFont(don_font)
        root.addWidget(don_lbl)

        def _wallet_row(coin: str, address: str):
            row = QHBoxLayout()
            lbl = QLabel(f"{coin}:")
            lbl.setFixedWidth(60)
            lbl_font = QFont()
            lbl_font.setBold(True)
            lbl.setFont(lbl_font)
            row.addWidget(lbl)
            entry = QLineEdit(address)
            entry.setReadOnly(True)
            entry.setAlignment(Qt.AlignmentFlag.AlignCenter)
            row.addWidget(entry)
            return row

        root.addLayout(_wallet_row("Bitcoin",  "3G3MDNUh51g6iK7ZRSQPX4EeBXEb3UyAtw"))
        root.addLayout(_wallet_row("Litecoin", "MEmeHh7A3Cfp9KvcqurviaJXpYL9HXuVJV"))

        root.addStretch()
        root.addWidget(hsep())

        close_btn = QPushButton(self.tr.get("close"))
        close_btn.setObjectName("primary")
        close_btn.setFixedWidth(120)
        close_btn.clicked.connect(self.accept)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_row.addWidget(close_btn)
        btn_row.addStretch()
        root.addLayout(btn_row)
