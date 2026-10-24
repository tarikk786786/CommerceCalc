"""
E-Commerce Public APIs & Integrations Hub for CommerceCalc.

Directly utilizes:
- Public APIs (public-apis/public-apis)
- Public API Lists (public-api-lists/public-api-lists)
- OpenAPI Directory (APIs-guru/openapi-directory)
- Free Public APIs (free-public-apis/apis)
- Pipedream (PipedreamHQ/pipedream)
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextBrowser,
    QLineEdit, QPushButton, QComboBox, QTabWidget, QTableWidget,
    QTableWidgetItem, QHeaderView, QProgressBar, QGroupBox, QGridLayout,
    QFrame, QMessageBox
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont
import json
import urllib.request

from ...services.api_directory_service import APIDirectoryService


class AsyncAPIWorker(QThread):
    finished_signal = Signal(dict)
    error_signal = Signal(str)

    def __init__(self, fn, *args):
        super().__init__()
        self.fn = fn
        self.args = args

    def run(self):
        try:
            res = self.fn(*self.args)
            self.finished_signal.emit(res)
        except Exception as e:
            self.error_signal.emit(str(e))


class IntegrationsPage(QWidget):
    """Integrations, Public APIs & Pipedream Webhook Hub."""

    def __init__(self, db_session=None, parent=None):
        super().__init__(parent)
        self.db_session = db_session
        self.api_service = APIDirectoryService()
        self.worker = None
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(28, 28, 28, 28)
        main_layout.setSpacing(18)

        # Header banner
        banner = QFrame()
        banner.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0f172a, stop:1 #1e293b);
                border-radius: 10px;
                padding: 16px;
            }
        """)
        b_layout = QVBoxLayout(banner)
        b_layout.setContentsMargins(16, 12, 16, 12)

        lbl_title = QLabel("🌐 E-Commerce Public APIs & Automation Hub")
        lbl_title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        lbl_title.setStyleSheet("color: #ffffff; background: transparent;")
        b_layout.addWidget(lbl_title)

        lbl_desc = QLabel(
            "Integrated with verified free endpoints from Public APIs, OpenAPI Directory, "
            "and Pipedream Webhook workflows for zero-cost live currency, postal zones, and data pipelines."
        )
        lbl_desc.setFont(QFont("Segoe UI", 10))
        lbl_desc.setStyleSheet("color: #94a3b8; background: transparent;")
        b_layout.addWidget(lbl_desc)

        main_layout.addWidget(banner)

        # Tab widget
        self.tabs = QTabWidget()

        self.tab_forex = self._build_forex_tab()
        self.tab_pincode = self._build_pincode_tab()
        self.tab_pipedream = self._build_pipedream_tab()
        self.tab_directory = self._build_directory_tab()

        self.tabs.addTab(self.tab_forex, "💱 Live Forex Rates")
        self.tabs.addTab(self.tab_pincode, "📍 India PIN Code & Delivery Zones")
        self.tabs.addTab(self.tab_pipedream, "⚡ Pipedream Webhook Workflows")
        self.tabs.addTab(self.tab_directory, "📚 Curated Public APIs Directory")

        main_layout.addWidget(self.tabs, 1)

    # -------------------------------------------------------------
    # Tab 1: Live Forex Rates
    # -------------------------------------------------------------
    def _build_forex_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)

        top_bar = QHBoxLayout()
        top_bar.addWidget(QLabel("Base Sourcing Currency:"))

        self.cmb_forex_base = QComboBox()
        self.cmb_forex_base.addItems(["USD", "EUR", "GBP", "AED", "CNY", "JPY", "CAD", "AUD"])
        self.cmb_forex_base.setFixedWidth(100)
        top_bar.addWidget(self.cmb_forex_base)

        self.btn_refresh_forex = QPushButton("🔄 Fetch Live Rates (Public APIs)")
        self.btn_refresh_forex.setStyleSheet("""
            QPushButton {
                background: #0284c7;
                color: white;
                font-weight: bold;
                border-radius: 6px;
                padding: 6px 16px;
            }
            QPushButton:hover { background: #0369a1; }
        """)
        self.btn_refresh_forex.clicked.connect(self._fetch_forex)
        top_bar.addWidget(self.btn_refresh_forex)

        top_bar.addStretch()
        self.lbl_forex_status = QLabel("Source: open.er-api.com (No API key needed)")
        self.lbl_forex_status.setStyleSheet("color: #64748b; font-size: 9pt;")
        top_bar.addWidget(self.lbl_forex_status)

        layout.addLayout(top_bar)

        self.forex_table = QTableWidget(0, 3)
        self.forex_table.setHorizontalHeaderLabels(["Currency Pair", "Exchange Rate", "Target Currency"])
        self.forex_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.forex_table.setStyleSheet("border: 1px solid #e2e8f0; border-radius: 6px;")
        layout.addWidget(self.forex_table, 1)

        # Trigger initial fetch
        self._fetch_forex()
        return w

    def _fetch_forex(self):
        base = self.cmb_forex_base.currentText()
        self.btn_refresh_forex.setEnabled(False)
        self.lbl_forex_status.setText("Fetching live rates...")

        def call():
            return self.api_service.fetch_live_forex_rates(base)

        self.worker = AsyncAPIWorker(call)
        self.worker.finished_signal.connect(self._on_forex_success)
        self.worker.error_signal.connect(self._on_forex_error)
        self.worker.start()

    def _on_forex_success(self, res: dict):
        self.btn_refresh_forex.setEnabled(True)
        if not res.get("success"):
            self.lbl_forex_status.setText(f"Error: {res.get('error')}")
            return

        rates = res.get("rates", {})
        base = res.get("base", "USD")
        self.lbl_forex_status.setText(f"✅ Updated: {res.get('last_update')} via {res.get('source')}")

        display_currencies = ["INR", "USD", "EUR", "GBP", "AED", "CNY", "JPY", "CAD", "AUD", "SGD"]
        self.forex_table.setRowCount(0)

        for curr in display_currencies:
            if curr == base:
                continue
            val = rates.get(curr)
            if val is not None:
                row = self.forex_table.rowCount()
                self.forex_table.insertRow(row)
                self.forex_table.setItem(row, 0, QTableWidgetItem(f"1 {base} → {curr}"))
                self.forex_table.setItem(row, 1, QTableWidgetItem(f"{val:.4f}"))
                self.forex_table.setItem(row, 2, QTableWidgetItem(curr))

    def _on_forex_error(self, err: str):
        self.btn_refresh_forex.setEnabled(True)
        self.lbl_forex_status.setText(f"⚠️ Fetch Failed: {err}")

    # -------------------------------------------------------------
    # Tab 2: PIN Code & Delivery Zone
    # -------------------------------------------------------------
    def _build_pincode_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)

        box = QHBoxLayout()
        box.addWidget(QLabel("Enter 6-Digit Indian PIN Code:"))

        self.txt_pincode = QLineEdit("110001")
        self.txt_pincode.setFixedWidth(140)
        self.txt_pincode.returnPressed.connect(self._lookup_pin)
        box.addWidget(self.txt_pincode)

        self.btn_pincode = QPushButton("🔍 Resolve Postal Zone (Public APIs)")
        self.btn_pincode.setStyleSheet("""
            QPushButton {
                background: #0d9488;
                color: white;
                font-weight: bold;
                border-radius: 6px;
                padding: 6px 16px;
            }
            QPushButton:hover { background: #0f766e; }
        """)
        self.btn_pincode.clicked.connect(self._lookup_pin)
        box.addWidget(self.btn_pincode)
        box.addStretch()
        layout.addLayout(box)

        self.out_pincode = QTextBrowser()
        self.out_pincode.setStyleSheet("border: 1px solid #e2e8f0; border-radius: 6px; padding: 16px;")
        self.out_pincode.setHtml("""
            <div style='color: #64748b; font-family: Segoe UI, sans-serif;'>
                Enter any 6-digit Indian PIN Code to verify destination validity, district, state,
                and automatic Metro (Tier-1) vs Non-Metro courier zone categorization.
            </div>
        """)
        layout.addWidget(self.out_pincode, 1)

        return w

    def _lookup_pin(self):
        pin = self.txt_pincode.text().strip()
        self.btn_pincode.setEnabled(False)

        def call():
            return self.api_service.lookup_pincode_zone(pin)

        self.worker = AsyncAPIWorker(call)
        self.worker.finished_signal.connect(self._on_pin_success)
        self.worker.error_signal.connect(self._on_pin_error)
        self.worker.start()

    def _on_pin_success(self, res: dict):
        self.btn_pincode.setEnabled(True)
        if not res.get("success"):
            self.out_pincode.setHtml(f"<div style='color: #dc2626; padding: 12px;'>⚠️ {res.get('error')}</div>")
            return

        html = f"""
        <div style='font-family: Segoe UI, sans-serif; padding: 10px;'>
            <h2 style='color: #0f766e; margin-top: 0;'>Postal Destination Verified: {res['pincode']}</h2>
            <table style='width: 100%; border-collapse: collapse; font-size: 11pt;'>
                <tr style='border-bottom: 1px solid #e2e8f0;'><td style='padding: 8px; font-weight: bold;'>Post Office:</td><td>{res['post_office']}</td></tr>
                <tr style='border-bottom: 1px solid #e2e8f0;'><td style='padding: 8px; font-weight: bold;'>District:</td><td>{res['district']}</td></tr>
                <tr style='border-bottom: 1px solid #e2e8f0;'><td style='padding: 8px; font-weight: bold;'>State:</td><td>{res['state']}</td></tr>
                <tr style='border-bottom: 1px solid #e2e8f0;'><td style='padding: 8px; font-weight: bold;'>Logistics Zone:</td><td style='color: #0369a1; font-weight: bold;'>{res['zone_tier']}</td></tr>
                <tr><td style='padding: 8px; font-weight: bold;'>Registry Source:</td><td style='color: #64748b;'>{res['source']}</td></tr>
            </table>
        </div>
        """
        self.out_pincode.setHtml(html)

    def _on_pin_error(self, err: str):
        self.btn_pincode.setEnabled(True)
        self.out_pincode.setHtml(f"<div style='color: #dc2626; padding: 12px;'>Error: {err}</div>")

    # -------------------------------------------------------------
    # Tab 3: Pipedream Webhook Integration
    # -------------------------------------------------------------
    def _build_pipedream_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)

        info = QLabel(
            "<b>Pipedream (PipedreamHQ/pipedream)</b> allows you to connect CommerceCalc to 2,000+ cloud services "
            "(Google Sheets, Slack, Shopify, Discord, Airtable) without writing server code.<br>"
            "Create a free HTTP source in Pipedream and paste the endpoint URL below to sync calculations automatically."
        )
        info.setWordWrap(True)
        info.setStyleSheet("color: #334155; line-height: 1.4;")
        layout.addWidget(info)

        form = QGridLayout()
        form.addWidget(QLabel("Pipedream Webhook URL:"), 0, 0)
        self.txt_pipe_url = QLineEdit()
        self.txt_pipe_url.setPlaceholderText("https://eo...pipedream.net (or any Zapier/Make/custom webhook)")
        form.addWidget(self.txt_pipe_url, 0, 1)

        layout.addLayout(form)

        self.btn_send_pipe = QPushButton("⚡ Send Sample Calculation Payload to Pipedream")
        self.btn_send_pipe.setStyleSheet("""
            QPushButton {
                background: #4f46e5;
                color: white;
                font-weight: bold;
                border-radius: 6px;
                padding: 8px 18px;
            }
            QPushButton:hover { background: #4338ca; }
        """)
        self.btn_send_pipe.clicked.connect(self._send_pipedream_test)
        layout.addWidget(self.btn_send_pipe)

        self.out_pipe = QTextBrowser()
        self.out_pipe.setStyleSheet("border: 1px solid #e2e8f0; border-radius: 6px; padding: 12px;")
        layout.addWidget(self.out_pipe, 1)

        return w

    def _send_pipedream_test(self):
        url = self.txt_pipe_url.text().strip()
        if not url:
            QMessageBox.warning(self, "Missing URL", "Please enter your Pipedream webhook URL first.")
            return

        payload = {
            "source": "CommerceCalc Desktop",
            "event": "product_profit_calculation",
            "sku": "DEMO-SHIRT-001",
            "selling_price": 999.00,
            "cost_price": 320.00,
            "marketplace_fees": 180.00,
            "shipping_cost": 75.00,
            "net_profit": 344.00,
            "margin_pct": 34.4,
            "gst_tax_slab": "12%",
            "timestamp": "2026-10-23T10:55:00Z"
        }

        self.btn_send_pipe.setEnabled(False)

        def call():
            return self.api_service.send_to_pipedream(url, payload)

        self.worker = AsyncAPIWorker(call)
        self.worker.finished_signal.connect(self._on_pipe_success)
        self.worker.error_signal.connect(self._on_pipe_error)
        self.worker.start()

    def _on_pipe_success(self, res: dict):
        self.btn_send_pipe.setEnabled(True)
        if res.get("success"):
            self.out_pipe.setHtml(f"<div style='color: #16a34a; font-weight: bold;'>✅ {res.get('message')}</div>")
        else:
            self.out_pipe.setHtml(f"<div style='color: #dc2626;'>⚠️ {res.get('error')}</div>")

    def _on_pipe_error(self, err: str):
        self.btn_send_pipe.setEnabled(True)
        self.out_pipe.setHtml(f"<div style='color: #dc2626;'>Error: {err}</div>")

    # -------------------------------------------------------------
    # Tab 4: Curated Public APIs Directory
    # -------------------------------------------------------------
    def _build_directory_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)

        apis = self.api_service.get_curated_apis()
        table = QTableWidget(len(apis), 5)
        table.setHorizontalHeaderLabels(["API Name", "Category", "Catalog Source", "Auth", "Endpoint / Docs"])
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        table.setStyleSheet("border: 1px solid #e2e8f0; border-radius: 6px;")

        for i, item in enumerate(apis):
            table.setItem(i, 0, QTableWidgetItem(item["name"]))
            table.setItem(i, 1, QTableWidgetItem(item["category"]))
            table.setItem(i, 2, QTableWidgetItem(item["repo_source"]))
            table.setItem(i, 3, QTableWidgetItem(item["auth"]))
            table.setItem(i, 4, QTableWidgetItem(item["url"]))

        layout.addWidget(table, 1)

        note = QLabel(
            "Curated directly from <b>public-apis/public-apis</b>, <b>public-api-lists/public-api-lists</b>, "
            "and <b>APIs-guru/openapi-directory</b>. All selected endpoints operate with free access."
        )
        note.setStyleSheet("color: #64748b; font-size: 9pt;")
        layout.addWidget(note)

        return w
