"""
Theme system — dark (default) and light.

Fixes applied vs previous version:
- box-sizing removed (invalid Qt property)
- QAbstractScrollArea viewport styled so tables go light in light theme
- QSpinBox up/down buttons: visible arrows, wider, contrasted on dark
- QGroupBox title background matches parent (no stray bg)
- QCheckBox inside GroupBox explicitly inherits GroupBox bg → no rogue bg
- QPushButton:checked for theme-toggle buttons
- Header in light theme uses softer navy, readable in both themes
"""

DARK: dict = {
    "name":            "dark",
    "bg_window":       "#0f1117",
    "bg_panel":        "#171b26",
    "bg_card":         "#1e2235",
    "bg_input":        "#252a3d",
    "bg_header":       "#131726",
    "border":          "#2d3352",
    "border_focus":    "#f0a500",
    "text_primary":    "#e8eaf0",
    "text_secondary":  "#8b92a8",
    "text_header":     "#8b92a8",   # same as text_secondary on dark header
    "text_muted":      "#505570",
    "text_inverse":    "#0f1117",
    "accent":          "#f0a500",
    "accent_hover":    "#ffba2e",
    "accent_pressed":  "#cc8d00",
    "accent_subtle":   "#2a2200",
    "success":         "#2dd284",
    "success_subtle":  "#1a3a28",
    "warning":         "#f0a500",
    "danger":          "#e05252",
    "danger_subtle":   "#4a1a1a",
    "info":            "#4da6ff",
    "row_alt":         "#1a1e2e",
    "row_selected_bg": "#2a2200",
    "row_selected_fg": "#f0a500",
    "scroll_handle":   "#2d3352",
    "scroll_hover":    "#3d4462",
    "tab_active_bg":   "#1e2235",
    "tab_active_fg":   "#f0a500",
    "tab_inactive_bg": "#131726",
    "tab_inactive_fg": "#8b92a8",
    # Separate table-header bg from app-header bg
    "bg_table_header":   "#131726",
    "text_table_header": "#8b92a8",
    # SpinBox arrow colours (need contrast on dark bg_card)
    "spin_arrow":      "#e8eaf0",
    "spin_btn_bg":     "#2d3352",
    "spin_btn_hover":  "#3d4462",
}

LIGHT: dict = {
    "name":            "light",
    "bg_window":       "#f0f2f8",
    "bg_panel":        "#ffffff",
    "bg_card":         "#e8ebf5",
    "bg_input":        "#ffffff",
    "bg_header":       "#2b3560",
    "border":          "#c8ccde",
    "border_focus":    "#c07800",
    "text_primary":    "#1e2235",
    "text_secondary":  "#505570",
    # header text must contrast against bg_header (navy), so always white
    "text_header":     "#e8eaf0",
    "text_muted":      "#9095ac",
    "text_inverse":    "#ffffff",
    "accent":          "#c07800",
    "accent_hover":    "#a06000",
    "accent_pressed":  "#804800",
    "accent_subtle":   "#fff3cc",
    "success":         "#1a9a5e",
    "success_subtle":  "#d0f5e6",
    "warning":         "#c07800",
    "danger":          "#c03030",
    "danger_subtle":   "#fce8e8",
    "info":            "#2070cc",
    "row_alt":         "#eef0f8",
    "row_selected_bg": "#fff3cc",
    "row_selected_fg": "#c07800",
    "scroll_handle":   "#c8cbdc",
    "scroll_hover":    "#a8abbc",
    "tab_active_bg":   "#ffffff",
    "tab_active_fg":   "#c07800",
    "tab_inactive_bg": "#e8ebf5",
    "tab_inactive_fg": "#505570",
    # Table headers: light bg + dark text (proper light-mode appearance)
    "bg_table_header":   "#dde2f0",
    "text_table_header": "#1e2235",
    "spin_arrow":      "#505570",
    "spin_btn_bg":     "#dde0ee",
    "spin_btn_hover":  "#c8ccde",
}

THEMES: dict = {"dark": DARK, "light": LIGHT}


def get_stylesheet(theme: dict) -> str:
    t = theme
    return f"""
/* ── Global ───────────────────────────────────────────────────────────── */
QWidget {{
    background-color: {t['bg_window']};
    color: {t['text_primary']};
    font-family: "Segoe UI", "SF Pro Display", "Ubuntu", "Helvetica Neue", sans-serif;
    font-size: 10pt;
    outline: none;
}}
QMainWindow, QDialog {{
    background-color: {t['bg_window']};
}}

/* ── Frames ───────────────────────────────────────────────────────────── */
QFrame#panel {{
    background-color: {t['bg_panel']};
    border: 1px solid {t['border']};
    border-radius: 10px;
}}
QFrame#header {{
    background-color: {t['bg_header']};
    border-bottom: 2px solid {t['accent']};
    border-radius: 0px;
}}

/* ── GroupBox ─────────────────────────────────────────────────────────── */
QGroupBox {{
    background-color: {t['bg_card']};
    border: 1px solid {t['border']};
    border-radius: 8px;
    margin-top: 22px;
    padding: 14px 10px 10px 10px;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 12px;
    top: 4px;
    padding: 0 6px;
    background-color: {t['bg_card']};
    color: {t['text_secondary']};
    font-size: 8pt;
    font-weight: 700;
    letter-spacing: 1.2px;
}}
/* Children of GroupBox inherit the card background so no rogue colour */
QGroupBox > QWidget {{
    background-color: transparent;
}}
QGroupBox QCheckBox {{
    background-color: transparent;
    color: {t['text_primary']};
}}
QGroupBox QLabel {{
    background-color: transparent;
    color: {t['text_primary']};
}}

/* ── Labels ───────────────────────────────────────────────────────────── */
QLabel {{
    color: {t['text_primary']};
    background: transparent;
}}
QLabel#title_label {{
    color: {t['accent']};
    font-size: 15pt;
    font-weight: 700;
    letter-spacing: 2px;
    background: transparent;
}}
QLabel[objectName="subtitle"] {{
    color: {t['text_secondary']};
    font-size: 9pt;
    background: transparent;
}}
QLabel#section_label {{
    color: {t['text_secondary']};
    font-size: 8pt;
    font-weight: 700;
    letter-spacing: 1px;
    background: transparent;
}}
QLabel#stat_value {{
    color: {t['accent']};
    font-size: 13pt;
    font-weight: 700;
    font-family: "Consolas", "JetBrains Mono", "Courier New", monospace;
    background: transparent;
}}

/* ── Input fields ─────────────────────────────────────────────────────── */
QLineEdit, QTextEdit, QPlainTextEdit {{
    background-color: {t['bg_input']};
    border: 1px solid {t['border']};
    border-radius: 6px;
    padding: 6px 10px;
    color: {t['text_primary']};
    selection-background-color: {t['accent']};
    selection-color: {t['text_inverse']};
}}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
    border-color: {t['border_focus']};
}}

/* ── SpinBox — visible +/- buttons on both themes ─────────────────────── */
QSpinBox, QDoubleSpinBox {{
    background-color: {t['bg_input']};
    border: 1px solid {t['border']};
    border-radius: 6px;
    padding: 5px 2px 5px 8px;
    color: {t['text_primary']};
    min-width: 64px;
}}
QSpinBox:focus, QDoubleSpinBox:focus {{ border-color: {t['border_focus']}; }}
QSpinBox::up-button, QDoubleSpinBox::up-button {{
    subcontrol-origin: border;
    subcontrol-position: top right;
    background-color: {t['spin_btn_bg']};
    border-left: 1px solid {t['border']};
    border-bottom: 1px solid {t['border']};
    border-top-right-radius: 5px;
    width: 22px;
    height: 13px;
}}
QSpinBox::down-button, QDoubleSpinBox::down-button {{
    subcontrol-origin: border;
    subcontrol-position: bottom right;
    background-color: {t['spin_btn_bg']};
    border-left: 1px solid {t['border']};
    border-bottom-right-radius: 5px;
    width: 22px;
    height: 13px;
}}
QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover,
QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {{
    background-color: {t['spin_btn_hover']};
}}
/* Use solid-color blocks as arrows — Qt QSS doesn't support CSS triangles.
   'image: none' with width/height:0 causes QPainter engine==0 error. */
QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {{
    background-color: {t['spin_arrow']};
    width: 6px;
    height: 4px;
}}
QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {{
    background-color: {t['spin_arrow']};
    width: 6px;
    height: 4px;
}}

/* ── ComboBox ─────────────────────────────────────────────────────────── */
QComboBox {{
    background-color: {t['bg_input']};
    border: 1px solid {t['border']};
    border-radius: 6px;
    padding: 5px 10px;
    color: {t['text_primary']};
    min-width: 60px;
}}
QComboBox:focus {{ border-color: {t['border_focus']}; }}
QComboBox::drop-down {{ border: none; width: 22px; }}
QComboBox::down-arrow {{
    background-color: {t['text_secondary']};
    width: 6px;
    height: 4px;
    margin-right: 6px;
}}
QComboBox QAbstractItemView {{
    background-color: {t['bg_card']};
    border: 1px solid {t['border']};
    color: {t['text_primary']};
    selection-background-color: {t['accent_subtle']};
    selection-color: {t['accent']};
    padding: 4px;
    outline: none;
}}

/* ── Buttons ──────────────────────────────────────────────────────────── */
QPushButton {{
    background-color: {t['bg_card']};
    color: {t['text_primary']};
    border: 1px solid {t['border']};
    border-radius: 6px;
    padding: 7px 16px;
    font-weight: 600;
    font-size: 9pt;
}}
QPushButton:hover {{
    background-color: {t['bg_panel']};
    border-color: {t['accent']};
    color: {t['accent']};
}}
QPushButton:pressed  {{ background-color: {t['accent_subtle']}; }}
QPushButton:disabled {{ color: {t['text_muted']}; border-color: {t['border']}; }}
QPushButton:checked  {{
    background-color: {t['accent']};
    color: {t['text_inverse']};
    border-color: {t['accent']};
    font-weight: 700;
}}
QPushButton#primary {{
    background-color: {t['accent']};
    color: {t['text_inverse']};
    border: none;
    font-weight: 700;
}}
QPushButton#primary:hover   {{ background-color: {t['accent_hover']};   border: none; }}
QPushButton#primary:pressed {{ background-color: {t['accent_pressed']}; }}
QPushButton#primary:disabled {{ background-color: {t['border']}; color: {t['text_muted']}; }}
QPushButton#danger {{
    background-color: {t['danger_subtle']};
    color: {t['danger']};
    border: 1px solid {t['danger']}44;
}}
QPushButton#danger:hover {{ background-color: {t['danger']}22; border-color: {t['danger']}; }}
QPushButton#icon_btn {{
    background: transparent;
    border: none;
    padding: 4px 8px;
    font-size: 13pt;
    color: {t['text_secondary']};
    border-radius: 6px;
}}
QPushButton#icon_btn:hover {{ background-color: {t['bg_card']}; color: {t['accent']}; border: none; }}

/* ── CheckBox / RadioButton ───────────────────────────────────────────── */
QCheckBox {{ color: {t['text_primary']}; spacing: 8px; background: transparent; }}
QCheckBox::indicator {{
    width: 16px; height: 16px;
    border: 2px solid {t['border']};
    border-radius: 4px;
    background: {t['bg_input']};
}}
QCheckBox::indicator:checked {{ background-color: {t['accent']}; border-color: {t['accent']}; }}
QRadioButton {{ color: {t['text_primary']}; spacing: 8px; }}
QRadioButton::indicator {{
    width: 16px; height: 16px;
    border: 2px solid {t['border']};
    border-radius: 8px;
    background: {t['bg_input']};
}}
QRadioButton::indicator:checked {{ background-color: {t['accent']}; border-color: {t['accent']}; }}

/* ── TabWidget ────────────────────────────────────────────────────────── */
QTabWidget::pane {{
    background-color: {t['bg_panel']};
    border: 1px solid {t['border']};
    border-radius: 0 10px 10px 10px;
    top: -1px;
}}
QTabBar::tab {{
    background-color: {t['tab_inactive_bg']};
    color: {t['tab_inactive_fg']};
    border: 1px solid {t['border']};
    border-bottom: none;
    padding: 9px 20px;
    margin-right: 2px;
    border-radius: 6px 6px 0 0;
    font-weight: 600;
    font-size: 9pt;
}}
QTabBar::tab:selected {{
    background-color: {t['tab_active_bg']};
    color: {t['tab_active_fg']};
    border-bottom: 2px solid {t['accent']};
}}
QTabBar::tab:hover:!selected {{ background-color: {t['bg_card']}; color: {t['text_primary']}; }}

/* ── Tables & viewports ───────────────────────────────────────────────── */
QTableWidget, QTableView {{
    background-color: {t['bg_panel']};
    alternate-background-color: {t['row_alt']};
    border: 1px solid {t['border']};
    border-radius: 8px;
    gridline-color: {t['border']};
    color: {t['text_primary']};
    font-size: 9pt;
    outline: none;
}}
/* The viewport is a QAbstractScrollArea child — must be styled explicitly */
QAbstractScrollArea {{
    background-color: {t['bg_panel']};
}}
QAbstractScrollArea > QWidget {{
    background-color: {t['bg_panel']};
    color: {t['text_primary']};
}}
QTableWidget::item, QTableView::item {{
    padding: 4px 8px;
    border: none;
}}
QTableWidget::item:selected, QTableView::item:selected {{
    background-color: {t['row_selected_bg']};
    color: {t['row_selected_fg']};
}}
QHeaderView {{
    background-color: {t['bg_table_header']};
    border: none;
}}
QHeaderView::section {{
    background-color: {t['bg_table_header']};
    color: {t['text_table_header']};
    border: none;
    border-right: 1px solid {t['border']};
    border-bottom: 2px solid {t['accent']};
    padding: 8px 10px;
    font-size: 8pt;
    font-weight: 700;
    letter-spacing: 1px;
}}
QHeaderView::section:last {{ border-right: none; }}
QHeaderView::section:hover {{ background-color: {t['accent']}; color: {t['text_inverse']}; }}
QTableCornerButton::section {{ background-color: {t['bg_table_header']}; border: none; }}

/* ── TreeWidget ───────────────────────────────────────────────────────── */
QTreeWidget {{
    background-color: {t['bg_panel']};
    border: 1px solid {t['border']};
    border-radius: 8px;
    color: {t['text_primary']};
    font-size: 9pt;
    outline: none;
}}
QTreeWidget::item {{ padding: 4px 6px; }}
QTreeWidget::item:selected {{ background-color: {t['row_selected_bg']}; color: {t['row_selected_fg']}; border-radius: 4px; }}
QTreeWidget::item:hover {{ background-color: {t['bg_card']}; }}
QTreeWidget::branch {{ background: transparent; }}

/* ── Scrollbar ────────────────────────────────────────────────────────── */
QScrollBar:vertical   {{ background: {t['bg_panel']}; width: 8px; }}
QScrollBar::handle:vertical {{ background: {t['scroll_handle']}; border-radius: 4px; min-height: 24px; }}
QScrollBar::handle:vertical:hover {{ background: {t['scroll_hover']}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar:horizontal {{ background: {t['bg_panel']}; height: 8px; }}
QScrollBar::handle:horizontal {{ background: {t['scroll_handle']}; border-radius: 4px; min-width: 24px; }}
QScrollBar::handle:horizontal:hover {{ background: {t['scroll_hover']}; }}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}

/* ── Splitter ─────────────────────────────────────────────────────────── */
QSplitter::handle {{ background: {t['border']}; }}

/* ── StatusBar ────────────────────────────────────────────────────────── */
QStatusBar {{
    background-color: {t['bg_header']};
    color: {t['text_header']};
    border-top: 1px solid {t['border']};
    font-size: 8pt;
}}
QStatusBar::item {{ border: none; }}

/* ── ToolTip ──────────────────────────────────────────────────────────── */
QToolTip {{
    background-color: {t['bg_card']};
    color: {t['text_primary']};
    border: 1px solid {t['border']};
    border-radius: 6px;
    padding: 4px 8px;
}}

/* ── MessageBox ───────────────────────────────────────────────────────── */
QMessageBox {{ background-color: {t['bg_panel']}; }}
QMessageBox QLabel {{ color: {t['text_primary']}; }}

/* ── Separator line ───────────────────────────────────────────────────── */
QFrame[frameShape="4"], QFrame[frameShape="5"] {{
    color: {t['border']};
    background-color: {t['border']};
    border: none;
    max-height: 1px;
}}

/* ── ListWidget ───────────────────────────────────────────────────────── */
QListWidget {{
    background-color: {t['bg_panel']};
    border: 1px solid {t['border']};
    border-radius: 6px;
    color: {t['text_primary']};
    outline: none;
}}
QListWidget::item {{ padding: 5px 10px; }}
QListWidget::item:selected {{ background-color: {t['row_selected_bg']}; color: {t['row_selected_fg']}; }}
QListWidget::item:hover {{ background-color: {t['bg_card']}; }}

/* ── Completer popup ──────────────────────────────────────────────────── */
QAbstractItemView {{
    background-color: {t['bg_card']};
    color: {t['text_primary']};
    border: 1px solid {t['border']};
    selection-background-color: {t['accent_subtle']};
    selection-color: {t['accent']};
    outline: none;
}}

/* ── Slider ───────────────────────────────────────────────────────────── */
QSlider::groove:horizontal {{ background: {t['border']}; height: 4px; border-radius: 2px; }}
QSlider::handle:horizontal {{
    background: {t['accent']};
    width: 14px; height: 14px;
    margin: -5px 0;
    border-radius: 7px;
}}
QSlider::sub-page:horizontal {{ background: {t['accent']}; border-radius: 2px; }}
"""
