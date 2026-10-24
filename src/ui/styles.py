"""
CommerceCalc Application Stylesheet — Human-Crafted, High-Contrast FinTech & E-Commerce Theme.
Designed following no-slop UI standards: restrained, crisp, Linear / Stripe inspired.
"""

DARK_THEME = """
/* ═══════════════════════════════════════════════════════════════
   CommerceCalc Dark Theme — High-Contrast Obsidian & Slate
   ═══════════════════════════════════════════════════════════════ */

QMainWindow, QWidget {
    background-color: #090d16;
    color: #f8fafc;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Inter", Roboto, Helvetica, Arial, sans-serif;
    font-size: 13px;
    selection-background-color: #2563eb;
    selection-color: #ffffff;
}

/* ─── Sidebar Navigation ──────────────────────────────────────── */
#sidebar {
    background-color: #0b1120;
    border-right: 1px solid #1e293b;
    min-width: 230px;
    max-width: 230px;
}

#sidebar_brand {
    background-color: #0b1120;
    padding: 20px 16px 14px 16px;
    border-bottom: 1px solid #1e293b;
}

#brand_name {
    font-size: 17px;
    font-weight: 800;
    color: #38bdf8;
    letter-spacing: -0.3px;
}

#brand_tagline {
    font-size: 11px;
    color: #94a3b8;
    margin-top: 2px;
}

QPushButton#nav_btn {
    background: transparent;
    border: none;
    border-radius: 6px;
    padding: 9px 14px;
    text-align: left;
    color: #cbd5e1;
    font-size: 13px;
    font-weight: 500;
    margin: 1px 8px;
}

QPushButton#nav_btn:hover {
    background-color: #1e293b;
    color: #ffffff;
}

QPushButton#nav_btn[active="true"] {
    background-color: #1e3a8a;
    color: #93c5fd;
    font-weight: 600;
    border-left: 3px solid #38bdf8;
}

QLabel#nav_group_label {
    color: #64748b;
    font-size: 10px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    padding: 14px 16px 4px 16px;
}

/* ─── Top Toolbar ─────────────────────────────────────────────── */
#toolbar {
    background-color: #0b1120;
    border-bottom: 1px solid #1e293b;
    padding: 8px 20px;
    min-height: 54px;
    max-height: 54px;
}

#page_title {
    font-size: 17px;
    font-weight: 700;
    color: #f8fafc;
}

#search_bar {
    background-color: #131d2e;
    border: 1px solid #283953;
    border-radius: 6px;
    padding: 7px 12px;
    color: #f8fafc;
    min-width: 240px;
    font-size: 13px;
}

#search_bar:focus {
    border-color: #38bdf8;
    background-color: #162238;
}

/* ─── Cards & Containers ──────────────────────────────────────── */
QFrame#card {
    background-color: #111a2c;
    border: 1px solid #202d44;
    border-radius: 8px;
    padding: 18px;
}

QFrame#card:hover {
    border-color: #2b3d5c;
}

QFrame#metric_card {
    background-color: #131d2e;
    border: 1px solid #202d44;
    border-radius: 8px;
    padding: 14px 16px;
}

QFrame#metric_card_success {
    background-color: #062319;
    border: 1px solid #0f5132;
    border-radius: 8px;
    padding: 14px 16px;
}

QFrame#metric_card_danger {
    background-color: #2a0e14;
    border: 1px solid #842029;
    border-radius: 8px;
    padding: 14px 16px;
}

QLabel#metric_label {
    color: #94a3b8;
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

QLabel#metric_value {
    color: #f8fafc;
    font-size: 20px;
    font-weight: 800;
}

QLabel#metric_value_positive {
    color: #4ade80;
    font-size: 20px;
    font-weight: 800;
}

QLabel#metric_value_negative {
    color: #f87171;
    font-size: 20px;
    font-weight: 800;
}

/* ─── Forms, Inputs, Dropdowns ────────────────────────────────── */
QLabel#form_label {
    color: #e2e8f0;
    font-size: 13px;
    font-weight: 500;
}

QLabel#section_title {
    color: #f8fafc;
    font-size: 14px;
    font-weight: 700;
    padding-bottom: 4px;
}

QLineEdit, QDoubleSpinBox, QSpinBox, QTextEdit, QPlainTextEdit {
    background-color: #0d1524;
    border: 1px solid #283953;
    border-radius: 6px;
    padding: 8px 12px;
    color: #f8fafc;
    font-size: 13px;
    min-height: 24px;
}

QLineEdit:focus, QDoubleSpinBox:focus, QSpinBox:focus, QTextEdit:focus, QPlainTextEdit:focus {
    border: 1px solid #38bdf8;
    background-color: #131d2e;
}

QLineEdit:disabled, QDoubleSpinBox:disabled, QSpinBox:disabled {
    background-color: #161e2e;
    color: #64748b;
    border-color: #1e293b;
}

QComboBox {
    background-color: #0d1524;
    border: 1px solid #283953;
    border-radius: 6px;
    padding: 7px 12px;
    color: #f8fafc;
    font-size: 13px;
    min-height: 24px;
}

QComboBox:focus {
    border-color: #38bdf8;
}

QComboBox::drop-down {
    border: none;
    padding-right: 10px;
}

QComboBox QAbstractItemView {
    background-color: #0f172a;
    border: 1px solid #334155;
    color: #f8fafc;
    selection-background-color: #2563eb;
    selection-color: #ffffff;
    padding: 4px;
}

QCheckBox {
    color: #cbd5e1;
    font-size: 13px;
    spacing: 8px;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 1px solid #334155;
    border-radius: 4px;
    background-color: #0d1524;
}

QCheckBox::indicator:checked {
    background-color: #2563eb;
    border-color: #38bdf8;
}

/* ─── Buttons ─────────────────────────────────────────────────── */
QPushButton#primary_btn {
    background-color: #2563eb;
    border: none;
    border-radius: 6px;
    padding: 9px 18px;
    color: #ffffff;
    font-size: 13px;
    font-weight: 600;
    min-height: 22px;
}

QPushButton#primary_btn:hover {
    background-color: #1d4ed8;
}

QPushButton#primary_btn:pressed {
    background-color: #1e40af;
}

QPushButton#secondary_btn {
    background-color: #162032;
    border: 1px solid #2c3e5a;
    border-radius: 6px;
    padding: 8px 16px;
    color: #e2e8f0;
    font-size: 13px;
    font-weight: 500;
    min-height: 22px;
}

QPushButton#secondary_btn:hover {
    background-color: #1e2c44;
    border-color: #38bdf8;
    color: #ffffff;
}

QPushButton#success_btn {
    background-color: #16a34a;
    border: none;
    border-radius: 6px;
    padding: 9px 18px;
    color: #ffffff;
    font-size: 13px;
    font-weight: 600;
}

QPushButton#success_btn:hover {
    background-color: #15803d;
}

QPushButton#danger_btn {
    background-color: #dc2626;
    border: none;
    border-radius: 6px;
    padding: 9px 18px;
    color: #ffffff;
    font-size: 13px;
    font-weight: 600;
}

QPushButton#danger_btn:hover {
    background-color: #b91c1c;
}

/* ─── Tables ──────────────────────────────────────────────────── */
QTableWidget, QTableView {
    background-color: #0d1524;
    alternate-background-color: #111a2c;
    border: 1px solid #202d44;
    border-radius: 6px;
    gridline-color: #1a2538;
    color: #f8fafc;
    font-size: 13px;
    selection-background-color: #1e3a8a;
    selection-color: #ffffff;
}

QHeaderView::section {
    background-color: #162238;
    color: #cbd5e1;
    border: none;
    border-bottom: 1px solid #283953;
    border-right: 1px solid #1a2538;
    padding: 8px 10px;
    font-size: 12px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.4px;
}

/* ─── Tabs ────────────────────────────────────────────────────── */
QTabWidget::pane {
    border: 1px solid #202d44;
    border-radius: 6px;
    background-color: #0d1524;
}

QTabBar::tab {
    background-color: transparent;
    border: none;
    padding: 9px 18px;
    color: #94a3b8;
    font-size: 13px;
    font-weight: 600;
}

QTabBar::tab:selected {
    color: #38bdf8;
    border-bottom: 2px solid #38bdf8;
}

QTabBar::tab:hover {
    color: #ffffff;
}

/* ─── Scrollbars ──────────────────────────────────────────────── */
QScrollBar:vertical {
    background: #090d16;
    width: 8px;
    border-radius: 4px;
}

QScrollBar::handle:vertical {
    background: #25334a;
    border-radius: 4px;
    min-height: 28px;
}

QScrollBar::handle:vertical:hover {
    background: #38bdf8;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

/* ─── Boxes & Callouts ────────────────────────────────────────── */
QFrame#info_box {
    background-color: #0f2442;
    border: 1px solid #1d4ed8;
    border-radius: 6px;
    padding: 12px 14px;
}

QFrame#warning_box {
    background-color: #381a0e;
    border: 1px solid #b45309;
    border-radius: 6px;
    padding: 12px 14px;
}

QFrame#disclaimer_box {
    background-color: #131d2e;
    border: 1px solid #202d44;
    border-left: 4px solid #f59e0b;
    border-radius: 4px;
    padding: 10px 14px;
}

QGroupBox {
    border: 1px solid #202d44;
    border-radius: 6px;
    margin-top: 14px;
    padding-top: 12px;
    color: #cbd5e1;
    font-weight: 600;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 6px;
    color: #38bdf8;
}

QToolTip {
    background-color: #0f172a;
    color: #f8fafc;
    border: 1px solid #334155;
    border-radius: 4px;
    padding: 6px 10px;
    font-size: 12px;
}
"""

LIGHT_THEME = """
/* ═══════════════════════════════════════════════════════════════
   CommerceCalc Light Theme — Crisp Stripe & Mercury FinTech
   ═══════════════════════════════════════════════════════════════ */

QMainWindow, QWidget {
    background-color: #f8fafc;
    color: #0f172a;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Inter", Roboto, Helvetica, Arial, sans-serif;
    font-size: 13px;
    selection-background-color: #2563eb;
    selection-color: #ffffff;
}

/* ─── Sidebar Navigation ──────────────────────────────────────── */
#sidebar {
    background-color: #0f172a;
    border-right: 1px solid #1e293b;
    min-width: 230px;
    max-width: 230px;
}

#sidebar_brand {
    background-color: #0f172a;
    padding: 20px 16px 14px 16px;
    border-bottom: 1px solid #1e293b;
}

#brand_name {
    font-size: 17px;
    font-weight: 800;
    color: #38bdf8;
    letter-spacing: -0.3px;
}

#brand_tagline {
    font-size: 11px;
    color: #94a3b8;
    margin-top: 2px;
}

QPushButton#nav_btn {
    background: transparent;
    border: none;
    border-radius: 6px;
    padding: 9px 14px;
    text-align: left;
    color: #cbd5e1;
    font-size: 13px;
    font-weight: 500;
    margin: 1px 8px;
}

QPushButton#nav_btn:hover {
    background-color: #1e293b;
    color: #ffffff;
}

QPushButton#nav_btn[active="true"] {
    background-color: #1e3a8a;
    color: #93c5fd;
    font-weight: 600;
    border-left: 3px solid #38bdf8;
}

QLabel#nav_group_label {
    color: #64748b;
    font-size: 10px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    padding: 14px 16px 4px 16px;
}

/* ─── Top Toolbar ─────────────────────────────────────────────── */
#toolbar {
    background-color: #ffffff;
    border-bottom: 1px solid #e2e8f0;
    padding: 8px 20px;
    min-height: 54px;
    max-height: 54px;
}

#page_title {
    font-size: 17px;
    font-weight: 700;
    color: #0f172a;
}

#search_bar {
    background-color: #f1f5f9;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 7px 12px;
    color: #0f172a;
    min-width: 240px;
    font-size: 13px;
}

#search_bar:focus {
    border-color: #2563eb;
    background-color: #ffffff;
}

/* ─── Cards & Containers ──────────────────────────────────────── */
QFrame#card {
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 18px;
}

QFrame#card:hover {
    border-color: #cbd5e1;
}

QFrame#metric_card {
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 14px 16px;
}

QFrame#metric_card_success {
    background-color: #f0fdf4;
    border: 1px solid #bbf7d0;
    border-radius: 8px;
    padding: 14px 16px;
}

QFrame#metric_card_danger {
    background-color: #fef2f2;
    border: 1px solid #fecaca;
    border-radius: 8px;
    padding: 14px 16px;
}

QLabel#metric_label {
    color: #64748b;
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

QLabel#metric_value {
    color: #0f172a;
    font-size: 20px;
    font-weight: 800;
}

QLabel#metric_value_positive {
    color: #16a34a;
    font-size: 20px;
    font-weight: 800;
}

QLabel#metric_value_negative {
    color: #dc2626;
    font-size: 20px;
    font-weight: 800;
}

/* ─── Forms, Inputs, Dropdowns ────────────────────────────────── */
QLabel#form_label {
    color: #334155;
    font-size: 13px;
    font-weight: 500;
}

QLabel#section_title {
    color: #0f172a;
    font-size: 14px;
    font-weight: 700;
    padding-bottom: 4px;
}

QLineEdit, QDoubleSpinBox, QSpinBox, QTextEdit, QPlainTextEdit {
    background-color: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 8px 12px;
    color: #0f172a;
    font-size: 13px;
    min-height: 24px;
}

QLineEdit:focus, QDoubleSpinBox:focus, QSpinBox:focus, QTextEdit:focus, QPlainTextEdit:focus {
    border: 1px solid #2563eb;
    background-color: #ffffff;
}

QLineEdit:disabled, QDoubleSpinBox:disabled, QSpinBox:disabled {
    background-color: #f1f5f9;
    color: #94a3b8;
    border-color: #e2e8f0;
}

QComboBox {
    background-color: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 7px 12px;
    color: #0f172a;
    font-size: 13px;
    min-height: 24px;
}

QComboBox:focus {
    border-color: #2563eb;
}

QComboBox::drop-down {
    border: none;
    padding-right: 10px;
}

QComboBox QAbstractItemView {
    background-color: #ffffff;
    border: 1px solid #cbd5e1;
    color: #0f172a;
    selection-background-color: #2563eb;
    selection-color: #ffffff;
    padding: 4px;
}

QCheckBox {
    color: #334155;
    font-size: 13px;
    spacing: 8px;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 1px solid #cbd5e1;
    border-radius: 4px;
    background-color: #ffffff;
}

QCheckBox::indicator:checked {
    background-color: #2563eb;
    border-color: #2563eb;
}

/* ─── Buttons ─────────────────────────────────────────────────── */
QPushButton#primary_btn {
    background-color: #2563eb;
    border: none;
    border-radius: 6px;
    padding: 9px 18px;
    color: #ffffff;
    font-size: 13px;
    font-weight: 600;
    min-height: 22px;
}

QPushButton#primary_btn:hover {
    background-color: #1d4ed8;
}

QPushButton#primary_btn:pressed {
    background-color: #1e40af;
}

QPushButton#secondary_btn {
    background-color: #f8fafc;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 8px 16px;
    color: #334155;
    font-size: 13px;
    font-weight: 500;
    min-height: 22px;
}

QPushButton#secondary_btn:hover {
    background-color: #f1f5f9;
    border-color: #94a3b8;
    color: #0f172a;
}

QPushButton#success_btn {
    background-color: #16a34a;
    border: none;
    border-radius: 6px;
    padding: 9px 18px;
    color: #ffffff;
    font-size: 13px;
    font-weight: 600;
}

QPushButton#success_btn:hover {
    background-color: #15803d;
}

QPushButton#danger_btn {
    background-color: #dc2626;
    border: none;
    border-radius: 6px;
    padding: 9px 18px;
    color: #ffffff;
    font-size: 13px;
    font-weight: 600;
}

QPushButton#danger_btn:hover {
    background-color: #b91c1c;
}

/* ─── Tables ──────────────────────────────────────────────────── */
QTableWidget, QTableView {
    background-color: #ffffff;
    alternate-background-color: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 6px;
    gridline-color: #f1f5f9;
    color: #0f172a;
    font-size: 13px;
    selection-background-color: #dbeafe;
    selection-color: #1e40af;
}

QHeaderView::section {
    background-color: #f1f5f9;
    color: #475569;
    border: none;
    border-bottom: 1px solid #e2e8f0;
    border-right: 1px solid #e2e8f0;
    padding: 8px 10px;
    font-size: 12px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.4px;
}

/* ─── Tabs ────────────────────────────────────────────────────── */
QTabWidget::pane {
    border: 1px solid #e2e8f0;
    border-radius: 6px;
    background-color: #ffffff;
}

QTabBar::tab {
    background-color: transparent;
    border: none;
    padding: 9px 18px;
    color: #64748b;
    font-size: 13px;
    font-weight: 600;
}

QTabBar::tab:selected {
    color: #2563eb;
    border-bottom: 2px solid #2563eb;
}

QTabBar::tab:hover {
    color: #0f172a;
}

/* ─── Scrollbars ──────────────────────────────────────────────── */
QScrollBar:vertical {
    background: #f8fafc;
    width: 8px;
    border-radius: 4px;
}

QScrollBar::handle:vertical {
    background: #cbd5e1;
    border-radius: 4px;
    min-height: 28px;
}

QScrollBar::handle:vertical:hover {
    background: #94a3b8;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

/* ─── Boxes & Callouts ────────────────────────────────────────── */
QFrame#info_box {
    background-color: #eff6ff;
    border: 1px solid #bfdbfe;
    border-radius: 6px;
    padding: 12px 14px;
}

QFrame#warning_box {
    background-color: #fffbeb;
    border: 1px solid #fde68a;
    border-radius: 6px;
    padding: 12px 14px;
}

QFrame#disclaimer_box {
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    border-left: 4px solid #f59e0b;
    border-radius: 4px;
    padding: 10px 14px;
}

QGroupBox {
    border: 1px solid #e2e8f0;
    border-radius: 6px;
    margin-top: 14px;
    padding-top: 12px;
    color: #334155;
    font-weight: 600;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 6px;
    color: #2563eb;
}

QToolTip {
    background-color: #0f172a;
    color: #ffffff;
    border: 1px solid #334155;
    border-radius: 4px;
    padding: 6px 10px;
    font-size: 12px;
}
"""
