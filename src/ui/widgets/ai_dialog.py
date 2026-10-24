"""
Non-blocking AI Analysis & Diagnostics Modal Dialog for CommerceCalc.

Runs LLM queries (Gemini 2.5 Flash / Groq) asynchronously using QThread
to ensure smooth 60fps desktop UI interaction with no freezing.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTextBrowser,
    QPushButton, QProgressBar, QApplication, QMessageBox, QFrame
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont, QIcon
from typing import Callable, Any
import html
import re


def markdown_to_html_simple(md_text: str, is_dark: bool = True) -> str:
    """Clean conversion of Markdown to stylized high-contrast HTML for QTextBrowser."""
    text = html.escape(md_text)
    
    header_color = "#38bdf8"
    h1_color = "#60a5fa"
    code_bg = "#1e293b"
    code_color = "#f43f5e"
    
    # Headers
    text = re.sub(r"^### (.*?)$", rf"<h3 style='color: {header_color}; margin-top: 14px; margin-bottom: 4px; font-weight: bold;'>\1</h3>", text, flags=re.M)
    text = re.sub(r"^## (.*?)$", rf"<h2 style='color: {h1_color}; border-bottom: 1px solid #334155; padding-bottom: 4px; margin-top: 16px; font-weight: bold;'>\1</h2>", text, flags=re.M)
    text = re.sub(r"^# (.*?)$", rf"<h1 style='color: {h1_color}; font-size: 16pt; margin-top: 10px; font-weight: 800;'>\1</h1>", text, flags=re.M)
    
    # Bold & Italic
    text = re.sub(r"\*\*(.*?)\*\*", r"<strong style='color: #f8fafc;'>\1</strong>", text)
    text = re.sub(r"\*(.*?)\*", r"<em>\1</em>", text)
    
    # Bullet points
    text = re.sub(r"^[•\-\*] (.*?)$", r"<li style='margin-bottom: 4px; color: #e2e8f0;'>\1</li>", text, flags=re.M)
    
    # Code blocks
    text = re.sub(r"`(.*?)`", rf"<code style='background: {code_bg}; padding: 2px 5px; border-radius: 4px; color: {code_color}; font-family: monospace;'>\1</code>", text)
    
    # Line breaks
    text = text.replace("\n\n", "<p style='margin: 8px 0; color: #e2e8f0;'>").replace("\n", "<br>")
    
    html_doc = f"""
    <div style='font-family: -apple-system, Segoe UI, sans-serif; font-size: 10.5pt; color: #e2e8f0; line-height: 1.6;'>
        {text}
    </div>
    """
    return html_doc


class AIWorkerThread(QThread):
    """Background worker thread for cloud LLM API calls."""
    finished_signal = Signal(str)
    error_signal = Signal(str)

    def __init__(self, task_fn: Callable[[], str]):
        super().__init__()
        self.task_fn = task_fn

    def run(self):
        try:
            result = self.task_fn()
            self.finished_signal.emit(result)
        except Exception as e:
            self.error_signal.emit(str(e))


class AIDiagnosticDialog(QDialog):
    """Modern modal dialog displaying AI financial strategy and audit."""

    def __init__(self, title: str, task_fn: Callable[[], str], parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumSize(780, 560)
        self.resize(850, 620)
        self.task_fn = task_fn
        self.raw_result = ""

        self._init_ui(title)
        self._start_task()

    def _init_ui(self, title: str):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header card
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4f46e5, stop:1 #7c3aed);
                border-radius: 8px;
                padding: 12px;
            }
        """)
        h_layout = QVBoxLayout(header_frame)
        h_layout.setContentsMargins(16, 12, 16, 12)

        self.lbl_header = QLabel(f"✨ {title}")
        self.lbl_header.setFont(QFont("Segoe UI", 14, QFont.Bold))
        self.lbl_header.setStyleSheet("color: #ffffff; background: transparent;")
        h_layout.addWidget(self.lbl_header)

        self.lbl_sub = QLabel("Powered by Gemini 2.5 Flash & Groq LLM Cloud Intelligence")
        self.lbl_sub.setFont(QFont("Segoe UI", 9))
        self.lbl_sub.setStyleSheet("color: #e0e7ff; background: transparent;")
        h_layout.addWidget(self.lbl_sub)

        layout.addWidget(header_frame)

        # Status & Progress bar
        self.status_box = QHBoxLayout()
        self.lbl_status = QLabel("⚡ Contacting Cloud AI Model & Processing Financial Formulas...")
        self.lbl_status.setFont(QFont("Segoe UI", 10, QFont.Medium))
        self.lbl_status.setStyleSheet("color: #475569;")
        self.status_box.addWidget(self.lbl_status)
        layout.addLayout(self.status_box)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # indeterminate animation
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #e2e8f0;
                border-radius: 3px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #4f46e5;
                border-radius: 3px;
            }
        """)
        layout.addWidget(self.progress_bar)

        # Output browser
        self.text_browser = QTextBrowser()
        self.text_browser.setFont(QFont("Segoe UI", 10))
        self.text_browser.setStyleSheet("""
            QTextBrowser {
                background-color: #ffffff;
                border: 1px solid #cbd5e1;
                border-radius: 8px;
                padding: 16px;
            }
        """)
        self.text_browser.setOpenExternalLinks(True)
        layout.addWidget(self.text_browser, 1)

        # Bottom buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)

        self.btn_copy = QPushButton("📋 Copy AI Report")
        self.btn_copy.setFixedHeight(36)
        self.btn_copy.setEnabled(False)
        self.btn_copy.setStyleSheet("""
            QPushButton {
                background-color: #f1f5f9;
                color: #1e293b;
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                padding: 6px 16px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #e2e8f0;
            }
        """)
        self.btn_copy.clicked.connect(self._copy_to_clipboard)
        btn_layout.addWidget(self.btn_copy)

        btn_layout.addStretch()

        self.btn_close = QPushButton("Close")
        self.btn_close.setFixedHeight(36)
        self.btn_close.setStyleSheet("""
            QPushButton {
                background-color: #4f46e5;
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 6px 20px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #4338ca;
            }
        """)
        self.btn_close.clicked.connect(self.accept)
        btn_layout.addWidget(self.btn_close)

        layout.addLayout(btn_layout)

    def _start_task(self):
        self.worker = AIWorkerThread(self.task_fn)
        self.worker.finished_signal.connect(self._on_success)
        self.worker.error_signal.connect(self._on_error)
        self.worker.start()

    def _on_success(self, text: str):
        self.raw_result = text
        self.progress_bar.setVisible(False)
        self.lbl_status.setText("✅ AI Strategy Analysis Ready")
        self.lbl_status.setStyleSheet("color: #16a34a; font-weight: bold;")
        self.btn_copy.setEnabled(True)

        html_content = markdown_to_html_simple(text)
        self.text_browser.setHtml(html_content)

    def _on_error(self, err_msg: str):
        self.progress_bar.setVisible(False)
        self.lbl_status.setText("⚠️ AI Request Failed")
        self.lbl_status.setStyleSheet("color: #dc2626; font-weight: bold;")

        error_html = f"""
        <div style='color: #dc2626; font-family: Segoe UI, sans-serif; padding: 12px;'>
            <h3 style='margin-top: 0;'>Could Not Complete AI Request</h3>
            <p><strong>Error Details:</strong> {html.escape(err_msg)}</p>
            <hr style='border: 0; border-top: 1px solid #fee2e2; margin: 16px 0;'>
            <h4>Troubleshooting Steps:</h4>
            <ul>
                <li>Verify your <code>GEMINI_API_KEY</code> or <code>GROQ_API_KEY</code> in <code>appinfo11.txt</code>.</li>
                <li>Ensure you have an active internet connection to contact Google Cloud / Groq servers.</li>
                <li>Check your account quota / billing on Google AI Studio or Groq Console.</li>
            </ul>
        </div>
        """
        self.text_browser.setHtml(error_html)

    def _copy_to_clipboard(self):
        if self.raw_result:
            clipboard = QApplication.clipboard()
            clipboard.setText(self.raw_result)
            QMessageBox.information(self, "Copied", "AI financial diagnosis copied to clipboard!")
