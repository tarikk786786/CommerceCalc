"""
Application Settings & Regional Preferences Page for CommerceCalc.
"""
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QFrame,
    QPushButton, QLabel, QComboBox, QLineEdit, QFileDialog, QMessageBox, QGridLayout
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from ..widgets.common import (
    make_card, FormFieldRow, InfoBox, SectionTitle, Divider
)
from ...db.database import DB_PATH, backup_database, restore_database
from ...services.google_integration_service import GoogleIntegrationService
from ..widgets.google_link_dialog import GoogleLinkDialog


class SettingsPage(QWidget):
    """User preferences, currency, tax defaults, and database maintenance."""

    def __init__(self, db_session=None, parent=None):
        super().__init__(parent)
        self.db_session = db_session
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 24)
        layout.setSpacing(16)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        content = QWidget()
        c_layout = QVBoxLayout(content)
        c_layout.setContentsMargins(0, 0, 0, 0)
        c_layout.setSpacing(16)

        # 1. Regional & Currency Settings
        reg_card, reg_layout = make_card("🌐 Regional & Financial Display Preferences")
        self.currency_combo = QComboBox()
        self.currency_combo.addItems(["INR (₹) — Indian Rupee", "USD ($) — US Dollar", "EUR (€) — Euro", "GBP (£) — British Pound"])
        reg_layout.addWidget(FormFieldRow("Display Currency", self.currency_combo))

        self.gst_default_combo = QComboBox()
        self.gst_default_combo.addItems(["18% — Standard Goods & Services", "12% — Standard Goods", "5% — Essential Commodities", "28% — Luxury / Sin Goods", "0% — Exempt / Nil-Rated"])
        reg_layout.addWidget(FormFieldRow("Default GST Rate Preset", self.gst_default_combo))

        self.rounding_combo = QComboBox()
        self.rounding_combo.addItems(["End in ₹99 (e.g. ₹499, ₹999)", "End in ₹49 (e.g. ₹449, ₹749)", "End in ₹9 (e.g. ₹199, ₹299)", "Nearest Integer Rupee", "Round Up Always"])
        reg_layout.addWidget(FormFieldRow("Default Price Rounding", self.rounding_combo))
        c_layout.addWidget(reg_card)

        # 2. Appearance & Interface
        ui_card, ui_layout = make_card("🎨 Appearance & Accessibility")
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Dark Theme (Default Professional)", "Light Theme"])
        ui_layout.addWidget(FormFieldRow("Color Theme", self.theme_combo))

        self.motion_combo = QComboBox()
        self.motion_combo.addItems(["Enabled", "Reduced Motion (Immediate Transitions)"])
        ui_layout.addWidget(FormFieldRow("Motion & Animations", self.motion_combo))
        c_layout.addWidget(ui_card)

        # 3. Google Account, Cloud & AI Linking
        g_card, g_layout = make_card("🔗 Google Account, Cloud Services & AI Linking")
        self.lbl_g_status = QLabel()
        self.lbl_g_status.setFont(QFont("Segoe UI", 10, QFont.Bold))
        g_layout.addWidget(self.lbl_g_status)

        self.lbl_g_details = QLabel()
        self.lbl_g_details.setStyleSheet("color: #475569; font-size: 9pt;")
        self.lbl_g_details.setWordWrap(True)
        g_layout.addWidget(self.lbl_g_details)

        g_btn_row = QHBoxLayout()
        self.btn_manage_g = QPushButton("🔗 Manage Google Connection & API Keys")
        self.btn_manage_g.setObjectName("primary_btn")
        self.btn_manage_g.clicked.connect(self._open_google_dialog)
        g_btn_row.addWidget(self.btn_manage_g)

        btn_g_trends = QPushButton("📈 Google Trends")
        btn_g_trends.setObjectName("secondary_btn")
        btn_g_trends.clicked.connect(lambda: GoogleIntegrationService.open_google_trends("ecommerce"))
        g_btn_row.addWidget(btn_g_trends)

        btn_g_console = QPushButton("🔍 Search Console")
        btn_g_console.setObjectName("secondary_btn")
        btn_g_console.clicked.connect(GoogleIntegrationService.open_google_search_console)
        g_btn_row.addWidget(btn_g_console)

        btn_g_planner = QPushButton("💡 Keyword Planner")
        btn_g_planner.setObjectName("secondary_btn")
        btn_g_planner.clicked.connect(GoogleIntegrationService.open_google_keyword_planner)
        g_btn_row.addWidget(btn_g_planner)

        g_layout.addLayout(g_btn_row)
        c_layout.addWidget(g_card)
        self._refresh_google_status()

        # 4. Database Maintenance & Local Backup
        db_card, db_layout = make_card("💾 Local SQLite Database & Backups")
        db_layout.addWidget(InfoBox(
            f"All products, fee profiles, and calculation records are stored locally at:\n{DB_PATH}"
        ))

        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)

        backup_btn = QPushButton("📦 Backup Database Now")
        backup_btn.setObjectName("primary_btn")
        backup_btn.clicked.connect(self._backup_db)
        btn_row.addWidget(backup_btn)

        restore_btn = QPushButton("🔄 Restore from Backup File")
        restore_btn.setObjectName("secondary_btn")
        restore_btn.clicked.connect(self._restore_db)
        btn_row.addWidget(restore_btn)

        db_layout.addLayout(btn_row)
        c_layout.addWidget(db_card)

        c_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll)

    def _refresh_google_status(self):
        status = GoogleIntegrationService.get_status()
        if status["connected"]:
            self.lbl_g_status.setText(f"🟢 Connected — Key: {status['masked_key']}")
            self.lbl_g_status.setStyleSheet("color: #15803d;")
            svcs = " • ".join(status["services_active"])
            self.lbl_g_details.setText(f"Active Google Services: {svcs}")
        else:
            self.lbl_g_status.setText("⚪ Google Services Unlinked (Public Live Search Suggest Active)")
            self.lbl_g_status.setStyleSheet("color: #64748b;")
            svcs = " • ".join(status["services_active"])
            self.lbl_g_details.setText(f"Active Google Services: {svcs}\nLink your Google AI Studio key to activate Gemini 2.5 Flash listing copilot and deep SEO analysis.")

    def _open_google_dialog(self):
        dlg = GoogleLinkDialog(self)
        dlg.connection_changed.connect(lambda _: self._refresh_google_status())
        dlg.exec()
        self._refresh_google_status()

    def _backup_db(self):
        try:
            saved_file = backup_database()
            QMessageBox.information(self, "Backup Created", f"Local database safely backed up to:\n{saved_file}")
        except Exception as e:
            QMessageBox.critical(self, "Backup Error", f"Failed to create backup: {str(e)}")

    def _restore_db(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Backup File", "", "Database Files (*.db)")
        if path:
            try:
                restore_database(path)
                QMessageBox.information(self, "Database Restored", "Database restored successfully. Please restart CommerceCalc.")
            except Exception as e:
                QMessageBox.critical(self, "Restore Error", f"Failed to restore: {str(e)}")
