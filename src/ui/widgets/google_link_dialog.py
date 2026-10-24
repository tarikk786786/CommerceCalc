"""
Google Account and Cloud Services Linking Dialog for CommerceCalc.
Allows users to manage Google Cloud / Gemini AI credentials, test live connectivity,
and launch Google SEO and commerce tools (Trends, Search Console, Keyword Planner, Merchant Center).
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QMessageBox, QGridLayout, QGroupBox
)
from PySide6.QtCore import Qt, Signal, QThread
from PySide6.QtGui import QFont
import webbrowser

from ...services.google_integration_service import GoogleIntegrationService
from ...services.ai_service import CommerceCalcAI, get_api_key


class LiveTestWorker(QThread):
    finished_signal = Signal(bool, str)

    def __init__(self, key: str):
        super().__init__()
        self.key = key

    def run(self):
        try:
            # Test key by invoking Gemini Flash or AI service test
            import urllib.request
            import json

            # Live ping to Google Gemini models list endpoint
            url = f"https://generativelanguage.googleapis.com/v1beta/models?key={self.key}"
            req = urllib.request.Request(url, headers={"User-Agent": "CommerceCalc/1.0"})
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read().decode())
                models = [m.get("name", "") for m in data.get("models", [])]
                flash_available = any("gemini-2.5-flash" in m or "gemini-1.5-flash" in m for m in models)
                msg = f"Connected successfully! {len(models)} Google AI models active."
                if flash_available:
                    msg += " Gemini 2.5 Flash is verified and ready."
                self.finished_signal.emit(True, msg)
        except Exception as e:
            self.finished_signal.emit(False, f"Google Verification Failed: {str(e)}")


class GoogleLinkDialog(QDialog):
    """Dialog for connecting Google account, Gemini API, and SEO tools."""

    connection_changed = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Google Account & Cloud Services Linking Manager")
        self.setMinimumWidth(640)
        self.setStyleSheet("""
            QDialog {
                background: #0f172a;
                color: #f8fafc;
            }
            QGroupBox {
                font-weight: bold;
                border: 1px solid #334155;
                border-radius: 6px;
                margin-top: 12px;
                padding-top: 12px;
                background: #1e293b;
                color: #f8fafc;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 4px;
                color: #38bdf8;
            }
            QLabel {
                color: #e2e8f0;
            }
            QLineEdit {
                background-color: #0f172a;
                border: 1px solid #334155;
                border-radius: 6px;
                padding: 6px 10px;
                color: #f8fafc;
            }
            QLineEdit:focus {
                border-color: #38bdf8;
            }
            QPushButton {
                background-color: #1e293b;
                border: 1px solid #475569;
                border-radius: 6px;
                padding: 6px 12px;
                color: #f8fafc;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #334155;
            }
        """)
        self._init_ui()
        self._refresh_status()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(20, 20, 20, 20)

        # Header card
        header = QFrame()
        header.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1e3a8a, stop:1 #2563eb);
                border-radius: 8px;
                padding: 14px;
            }
        """)
        h_layout = QVBoxLayout(header)
        h_layout.setContentsMargins(12, 10, 12, 10)

        title = QLabel("🔗 Google Cloud & E-Commerce Integration")
        title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        title.setStyleSheet("color: #ffffff; background: transparent;")
        h_layout.addWidget(title)

        desc = QLabel(
            "Connect your Google account and AI Studio key to power high-ranking keyword research, "
            "Gemini 2.5 Flash listing optimization, real-time Trends, and Search Console tools."
        )
        desc.setFont(QFont("Segoe UI", 9))
        desc.setStyleSheet("color: #dbeafe; background: transparent;")
        desc.setWordWrap(True)
        h_layout.addWidget(desc)
        layout.addWidget(header)

        # Status box
        self.status_box = QGroupBox("Active Link Status")
        sb_layout = QVBoxLayout(self.status_box)

        self.lbl_status = QLabel("Checking connection...")
        self.lbl_status.setFont(QFont("Segoe UI", 10, QFont.Bold))
        sb_layout.addWidget(self.lbl_status)

        self.lbl_active_services = QLabel("")
        self.lbl_active_services.setStyleSheet("color: #475569; font-size: 9pt;")
        self.lbl_active_services.setWordWrap(True)
        sb_layout.addWidget(self.lbl_active_services)
        layout.addWidget(self.status_box)

        # Credentials Group
        cred_group = QGroupBox("Google AI Studio / Gemini API Key Configuration")
        cg_layout = QVBoxLayout(cred_group)

        cg_layout.addWidget(QLabel("Google API Key:"))
        key_row = QHBoxLayout()
        self.txt_api_key = QLineEdit()
        self.txt_api_key.setEchoMode(QLineEdit.Password)
        self.txt_api_key.setPlaceholderText("AIzaSy...")
        self.txt_api_key.setFixedHeight(34)
        key_row.addWidget(self.txt_api_key, 1)

        self.btn_toggle_echo = QPushButton("👁️ Show")
        self.btn_toggle_echo.setFixedHeight(34)
        self.btn_toggle_echo.clicked.connect(self._toggle_echo)
        key_row.addWidget(self.btn_toggle_echo)
        cg_layout.addLayout(key_row)

        btn_row = QHBoxLayout()
        btn_get_key = QPushButton("🔑 Get Free Google Key (Google AI Studio)")
        btn_get_key.setFixedHeight(32)
        btn_get_key.clicked.connect(lambda: webbrowser.open("https://aistudio.google.com/app/apikey"))
        btn_row.addWidget(btn_get_key)

        self.btn_test = QPushButton("⚡ Test Live Connection")
        self.btn_test.setFixedHeight(32)
        self.btn_test.setStyleSheet("background: #0284c7; color: #ffffff; font-weight: bold; border-radius: 4px;")
        self.btn_test.clicked.connect(self._test_connection)
        btn_row.addWidget(self.btn_test)

        self.btn_save = QPushButton("💾 Save & Link Google")
        self.btn_save.setFixedHeight(32)
        self.btn_save.setStyleSheet("background: #16a34a; color: #ffffff; font-weight: bold; border-radius: 4px;")
        self.btn_save.clicked.connect(self._save_credentials)
        btn_row.addWidget(self.btn_save)

        cg_layout.addLayout(btn_row)
        layout.addWidget(cred_group)

        # Quick External Tools Hub
        tools_group = QGroupBox("Google E-Commerce & SEO Tools Hub")
        tg_layout = QGridLayout(tools_group)

        btn_trends = QPushButton("📈 Google Trends Explorer")
        btn_trends.setFixedHeight(32)
        btn_trends.clicked.connect(lambda: GoogleIntegrationService.open_google_trends("ecommerce"))
        tg_layout.addWidget(btn_trends, 0, 0)

        btn_planner = QPushButton("💡 Google Keyword Planner")
        btn_planner.setFixedHeight(32)
        btn_planner.clicked.connect(GoogleIntegrationService.open_google_keyword_planner)
        tg_layout.addWidget(btn_planner, 0, 1)

        btn_gsc = QPushButton("🔍 Google Search Console")
        btn_gsc.setFixedHeight(32)
        btn_gsc.clicked.connect(GoogleIntegrationService.open_google_search_console)
        tg_layout.addWidget(btn_gsc, 1, 0)

        btn_merchant = QPushButton("🛍️ Google Merchant Center")
        btn_merchant.setFixedHeight(32)
        btn_merchant.clicked.connect(GoogleIntegrationService.open_google_merchant_center)
        tg_layout.addWidget(btn_merchant, 1, 1)

        layout.addWidget(tools_group)

        # Close
        close_btn = QPushButton("Done")
        close_btn.setFixedHeight(34)
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

    def _toggle_echo(self):
        if self.txt_api_key.echoMode() == QLineEdit.Password:
            self.txt_api_key.setEchoMode(QLineEdit.Normal)
            self.btn_toggle_echo.setText("🔒 Hide")
        else:
            self.txt_api_key.setEchoMode(QLineEdit.Password)
            self.btn_toggle_echo.setText("👁️ Show")

    def _refresh_status(self):
        status = GoogleIntegrationService.get_status()
        if status["connected"]:
            self.lbl_status.setText(f"🟢 Connected — Key: {status['masked_key']}")
            self.lbl_status.setStyleSheet("color: #15803d; font-size: 10pt; font-weight: bold;")
            svcs = " • ".join(status["services_active"])
            self.lbl_active_services.setText(f"Active Capabilities:\n{svcs}")
        else:
            self.lbl_status.setText("⚪ Unlinked (Using Free Live Public Google Engine)")
            self.lbl_status.setStyleSheet("color: #64748b; font-size: 10pt; font-weight: bold;")
            svcs = " • ".join(status["services_active"])
            self.lbl_active_services.setText(f"Active Capabilities:\n{svcs}")

    def _save_credentials(self):
        key = self.txt_api_key.text().strip()
        if not key:
            QMessageBox.warning(self, "Invalid Key", "Please paste a valid Google API Key.")
            return

        success = GoogleIntegrationService.save_google_credentials(key)
        if success:
            QMessageBox.information(
                self, "Google Linked",
                "Google API credentials have been successfully updated and recorded in appinfo11.txt!"
            )
            self._refresh_status()
            self.connection_changed.emit(True)
        else:
            QMessageBox.critical(self, "Error", "Failed to save Google credentials.")

    def _test_connection(self):
        key = self.txt_api_key.text().strip()
        if not key:
            status = GoogleIntegrationService.get_status()
            from ...services.ai_service import get_api_key
            key = get_api_key("GEMINI_API_KEY") or get_api_key("GOOGLE_API_KEY")

        if not key:
            QMessageBox.warning(self, "Key Required", "Please enter or configure a Google API key first.")
            return

        self.btn_test.setEnabled(False)
        self.btn_test.setText("Testing...")

        self.worker = LiveTestWorker(key)
        self.worker.finished_signal.connect(self._on_test_finished)
        self.worker.start()

    def _on_test_finished(self, success: bool, msg: str):
        self.btn_test.setEnabled(True)
        self.btn_test.setText("⚡ Test Live Connection")
        if success:
            QMessageBox.information(self, "Live Google Connection Verified", msg)
            self._refresh_status()
        else:
            QMessageBox.warning(self, "Connection Test", msg)
