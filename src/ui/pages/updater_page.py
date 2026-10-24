"""
Software Updates & Maintenance Page for CommerceCalc.

Provides:
- Current release version display (v1.0.0)
- One-click update check via GitHub Releases API / remote manifest
- Release channel selection (Stable / Beta)
- Automated startup check settings
- Release notes & changelog browser
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextBrowser,
    QPushButton, QComboBox, QCheckBox, QProgressBar, QGroupBox,
    QGridLayout, QFrame, QMessageBox
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont
import webbrowser

from ...services.updater import UpdateChecker, CURRENT_VERSION, BUILD_DATE
from ..widgets.ai_dialog import markdown_to_html_simple


class UpdateWorker(QThread):
    finished_signal = Signal(dict)
    error_signal = Signal(str)

    def __init__(self, checker: UpdateChecker):
        super().__init__()
        self.checker = checker

    def run(self):
        try:
            res = self.checker.check_for_updates()
            self.finished_signal.emit(res)
        except Exception as e:
            self.error_signal.emit(str(e))


class UpdaterPage(QWidget):
    """Software Updates and Version Maintenance page."""

    def __init__(self, db_session=None, parent=None):
        super().__init__(parent)
        self.db_session = db_session
        self.checker = UpdateChecker()
        self.worker = None
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(28, 28, 28, 28)
        main_layout.setSpacing(20)

        # Header Banner
        banner = QFrame()
        banner.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1e293b, stop:1 #334155);
                border-radius: 10px;
                padding: 16px;
            }
        """)
        b_layout = QVBoxLayout(banner)
        b_layout.setContentsMargins(16, 12, 16, 12)

        lbl_title = QLabel("🔄 Software Updates & Maintenance")
        lbl_title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        lbl_title.setStyleSheet("color: #ffffff; background: transparent;")
        b_layout.addWidget(lbl_title)

        lbl_desc = QLabel(
            "Manage releases, check for future feature updates, inspect release notes, and configure update channels."
        )
        lbl_desc.setFont(QFont("Segoe UI", 10))
        lbl_desc.setStyleSheet("color: #cbd5e1; background: transparent;")
        b_layout.addWidget(lbl_desc)

        main_layout.addWidget(banner)

        # Version Status Card
        status_card = QGroupBox("Current Installation Details")
        sc_layout = QGridLayout(status_card)
        sc_layout.setContentsMargins(16, 16, 16, 16)
        sc_layout.setSpacing(12)

        sc_layout.addWidget(QLabel("Installed Version:"), 0, 0)
        lbl_ver = QLabel(f"v{CURRENT_VERSION} (Production Build)")
        lbl_ver.setFont(QFont("Segoe UI", 10, QFont.Bold))
        lbl_ver.setStyleSheet("color: #16a34a;")
        sc_layout.addWidget(lbl_ver, 0, 1)

        sc_layout.addWidget(QLabel("Build Date:"), 0, 2)
        sc_layout.addWidget(QLabel(BUILD_DATE), 0, 3)

        sc_layout.addWidget(QLabel("Update Channel:"), 1, 0)
        self.cmb_channel = QComboBox()
        self.cmb_channel.addItems(["Stable (Recommended)", "Beta / Pre-Release", "Nightly"])
        self.cmb_channel.setFixedWidth(180)
        sc_layout.addWidget(self.cmb_channel, 1, 1)

        sc_layout.addWidget(QLabel("Update Source:"), 1, 2)
        sc_layout.addWidget(QLabel("GitHub Releases API (Official)"), 1, 3)

        self.chk_auto = QCheckBox("Check for updates automatically when application starts")
        self.chk_auto.setChecked(True)
        sc_layout.addWidget(self.chk_auto, 2, 0, 1, 4)

        main_layout.addWidget(status_card)

        # Action Buttons
        btn_box = QHBoxLayout()
        self.btn_check = QPushButton("🔍 Check for Updates Now")
        self.btn_check.setFixedHeight(42)
        self.btn_check.setStyleSheet("""
            QPushButton {
                background-color: #4f46e5;
                color: #ffffff;
                font-size: 10pt;
                font-weight: bold;
                border-radius: 6px;
                padding: 0 24px;
            }
            QPushButton:hover {
                background-color: #4338ca;
            }
        """)
        self.btn_check.clicked.connect(self._run_update_check)
        btn_box.addWidget(self.btn_check)

        self.btn_download = QPushButton("⬇️ Download Latest Release")
        self.btn_download.setFixedHeight(42)
        self.btn_download.setEnabled(False)
        self.btn_download.setStyleSheet("""
            QPushButton {
                background-color: #0284c7;
                color: #ffffff;
                font-size: 10pt;
                font-weight: bold;
                border-radius: 6px;
                padding: 0 24px;
            }
            QPushButton:hover {
                background-color: #0369a1;
            }
            QPushButton:disabled {
                background-color: #cbd5e1;
                color: #64748b;
            }
        """)
        self.btn_download.clicked.connect(self._open_download_url)
        btn_box.addWidget(self.btn_download)

        btn_box.addStretch()
        main_layout.addLayout(btn_box)

        # Progress bar
        self.prog = QProgressBar()
        self.prog.setRange(0, 0)
        self.prog.setFixedHeight(4)
        self.prog.setVisible(False)
        self.prog.setStyleSheet("QProgressBar::chunk { background: #4f46e5; }")
        main_layout.addWidget(self.prog)

        # Output / Changelog browser
        self.out_browser = QTextBrowser()
        self.out_browser.setObjectName("card")
        self._show_default_changelog()
        main_layout.addWidget(self.out_browser, 1)

    def _show_default_changelog(self):
        default_notes = f"""
        # CommerceCalc v{CURRENT_VERSION} Release Notes
        
        ### What's New in This Release:
        - **All-in-One E-Commerce Financial Suite**: 15 offline-first calculation modules with Decimal precision.
        - **Indian GST Engine**: Full CGST, SGST, IGST, Section 52 TCS, Section 194-O TDS compliance.
        - **AI Copilot**: Powered by Google Gemini 2.5 Flash and Groq Cloud with HSN discovery, margin diagnostics, and price war simulations.
        - **Free Public APIs Integration**: Live real-time currency conversion rates (USD, EUR, GBP, AED to INR) and India Post PIN code zone verification.
        - **Pipedream Webhook Hub**: One-click dispatch of calculations into automated workflows (Zapier, Sheets, Slack).
        - **Bulk Spreadsheet Engine**: High-throughput CSV & Excel processor with automatic validation.
        - **Desktop & Home Launcher**: Windows executable shortcuts and batch launchers.
        """
        self.out_browser.setHtml(markdown_to_html_simple(default_notes))

    def _run_update_check(self):
        self.btn_check.setEnabled(False)
        self.prog.setVisible(True)

        self.worker = UpdateWorker(self.checker)
        self.worker.finished_signal.connect(self._on_check_finished)
        self.worker.error_signal.connect(self._on_check_error)
        self.worker.start()

    def _on_check_finished(self, res: dict):
        self.btn_check.setEnabled(True)
        self.prog.setVisible(False)
        self.download_url = res.get("download_url", "")

        if res.get("update_available"):
            self.btn_download.setEnabled(True)
            msg = (
                f"# 🎉 Update Available: {res.get('release_title')}\n\n"
                f"**Current:** v{res.get('current_version')} | **Latest:** {res.get('latest_version')}\n\n"
                f"### Changelog & Improvements:\n{res.get('release_notes')}\n\n"
                f"[Click 'Download Latest Release' to obtain the installer package.]({self.download_url})"
            )
            self.out_browser.setHtml(markdown_to_html_simple(msg))
            QMessageBox.information(
                self,
                "New Version Available",
                f"Version {res.get('latest_version')} is available! Review the release notes below."
            )
        else:
            self.btn_download.setEnabled(False)
            msg = (
                f"# ✅ CommerceCalc is Up to Date\n\n"
                f"You are running version **v{CURRENT_VERSION}** (Channel: {self.cmb_channel.currentText()}).\n\n"
                f"Status: {res.get('status_message')}\n\n"
                f"---\n\n"
                f"### Current Build Highlights:\n"
                f"- Python 3.14 + PySide6 6.12.0\n"
                f"- Decimal-safe financial accounting\n"
                f"- Active Gemini 2.5 Flash AI integration\n"
                f"- Verified Public APIs and Pipedream connectivity"
            )
            self.out_browser.setHtml(markdown_to_html_simple(msg))

    def _on_check_error(self, err: str):
        self.btn_check.setEnabled(True)
        self.prog.setVisible(False)
        self.out_browser.setHtml(f"<div style='color: #dc2626; padding: 12px;'><strong>Update Check Failed:</strong> {err}</div>")

    def _open_download_url(self):
        if getattr(self, "download_url", None):
            webbrowser.open(self.download_url)
        else:
            webbrowser.open("https://github.com/CommerceCalc/CommerceCalc/releases")
