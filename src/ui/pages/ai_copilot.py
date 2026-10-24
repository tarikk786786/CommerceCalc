"""
AI E-Commerce Copilot & Strategic Advisor Page for CommerceCalc.

Provides real-time cloud LLM powered capabilities:
1. Executive Strategy & E-Commerce Financial Chat
2. HSN Code & GST Slab Classifier
3. Competitor Price War & Buy-Box Defense Simulator
4. COD & RTO Loss Reduction Playbook Generator
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextBrowser,
    QLineEdit, QTextEdit, QPushButton, QComboBox, QTabWidget,
    QProgressBar, QGroupBox, QGridLayout, QFrame, QApplication, QMessageBox
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont

from ...services.ai_service import CommerceCalcAI
from ..widgets.ai_dialog import markdown_to_html_simple


class AICopilotWorker(QThread):
    finished_signal = Signal(str)
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


class AICopilotPage(QWidget):
    """Full-featured AI Copilot workspace."""

    def __init__(self, db_session=None, parent=None):
        super().__init__(parent)
        self.db_session = db_session
        self.ai = CommerceCalcAI()
        self.worker = None
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(28, 28, 28, 28)
        main_layout.setSpacing(18)

        # Header Banner
        banner = QFrame()
        banner.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #312e81, stop:1 #4338ca);
                border-radius: 10px;
                padding: 16px;
            }
        """)
        b_layout = QVBoxLayout(banner)
        b_layout.setContentsMargins(16, 12, 16, 12)

        lbl_title = QLabel("🤖 CommerceCalc AI Strategic Copilot")
        lbl_title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        lbl_title.setStyleSheet("color: #ffffff; background: transparent;")
        b_layout.addWidget(lbl_title)

        lbl_desc = QLabel(
            "Cloud-native intelligent advisor for Indian & global marketplaces. "
            "Optimizes pricing elasticity, detects GST/HSN codes, simulates competitor price wars, and minimizes RTO burn."
        )
        lbl_desc.setFont(QFont("Segoe UI", 10))
        lbl_desc.setStyleSheet("color: #c7d2fe; background: transparent;")
        b_layout.addWidget(lbl_desc)

        main_layout.addWidget(banner)

        # Tabs for 4 specialized AI modules
        self.tabs = QTabWidget()

        self.tab_chat = self._build_chat_tab()
        self.tab_hsn = self._build_hsn_tab()
        self.tab_war = self._build_war_tab()
        self.tab_rto = self._build_rto_tab()

        self.tabs.addTab(self.tab_chat, "💬 Strategic Financial Chat")
        self.tabs.addTab(self.tab_hsn, "🏷️ HSN Code & GST Finder")
        self.tabs.addTab(self.tab_war, "⚔️ Competitor Price War Simulator")
        self.tabs.addTab(self.tab_rto, "📦 RTO & COD Loss Reduction Playbook")

        main_layout.addWidget(self.tabs, 1)

    # -------------------------------------------------------------
    # Tab 1: Financial Chat
    # -------------------------------------------------------------
    def _build_chat_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Quick prompt buttons
        q_layout = QHBoxLayout()
        q_label = QLabel("Quick Prompts:")
        q_label.setStyleSheet("font-weight: bold; color: #475569;")
        q_layout.addWidget(q_label)

        prompts = [
            ("₹499 T-Shirt on Amazon", "How do I make a ₹499 Cotton T-Shirt profitable on Amazon India with 18% GST and ₹70 Easy Ship?"),
            ("30% COD RTO Fix", "My COD RTO rate is 32% on Shopify. How do I adjust product price and COD fees to stay profitable?"),
            ("Meta Ads ROAS Target", "I sell a ₹1,299 skin cream with ₹350 product cost. What is my break-even ROAS and max safe CPC on Meta Ads?"),
        ]
        for title, p_text in prompts:
            btn = QPushButton(title)
            btn.setStyleSheet("""
                QPushButton {
                    background: #f8fafc;
                    border: 1px solid #cbd5e1;
                    border-radius: 4px;
                    padding: 4px 10px;
                    font-size: 9pt;
                }
                QPushButton:hover {
                    background: #e0e7ff;
                    border-color: #6366f1;
                }
            """)
            btn.clicked.connect(lambda checked, t=p_text: self.txt_chat_input.setText(t))
            q_layout.addWidget(btn)
        q_layout.addStretch()
        layout.addLayout(q_layout)

        # Input & Send
        in_box = QHBoxLayout()
        self.txt_chat_input = QLineEdit()
        self.txt_chat_input.setPlaceholderText("Ask any e-commerce pricing, GST, marketplace commission, or profit question...")
        self.txt_chat_input.setFixedHeight(42)
        self.txt_chat_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                padding: 0 12px;
                font-size: 10pt;
            }
            QLineEdit:focus {
                border: 2px solid #4f46e5;
            }
        """)
        self.txt_chat_input.returnPressed.connect(self._run_chat_query)
        in_box.addWidget(self.txt_chat_input, 1)

        self.btn_send_chat = QPushButton("🚀 Ask AI Copilot")
        self.btn_send_chat.setFixedHeight(42)
        self.btn_send_chat.setStyleSheet("""
            QPushButton {
                background: #4f46e5;
                color: white;
                font-weight: bold;
                border-radius: 6px;
                padding: 0 20px;
            }
            QPushButton:hover {
                background: #4338ca;
            }
        """)
        self.btn_send_chat.clicked.connect(self._run_chat_query)
        in_box.addWidget(self.btn_send_chat)

        layout.addLayout(in_box)

        # Progress indicator
        self.prog_chat = QProgressBar()
        self.prog_chat.setRange(0, 0)
        self.prog_chat.setFixedHeight(4)
        self.prog_chat.setVisible(False)
        self.prog_chat.setStyleSheet("QProgressBar::chunk { background: #4f46e5; }")
        layout.addWidget(self.prog_chat)

        # Output browser
        self.out_chat = QTextBrowser()
        self.out_chat.setHtml("""
            <div style='font-family: Segoe UI, sans-serif; color: #64748b; padding: 20px; text-align: center;'>
                <h3>Welcome to CommerceCalc AI Copilot</h3>
                <p>Type any financial, marketplace, or tax scenario above, or click one of the quick prompts.</p>
                <p>Powered by active Google Gemini 2.5 Flash and Groq Cloud intelligence.</p>
            </div>
        """)
        self.out_chat.setStyleSheet("border: 1px solid #e2e8f0; border-radius: 6px; padding: 12px;")
        layout.addWidget(self.out_chat, 1)

        return w

    def _run_chat_query(self):
        query = self.txt_chat_input.text().strip()
        if not query:
            return

        self.prog_chat.setVisible(True)
        self.btn_send_chat.setEnabled(False)

        system_prompt = (
            "You are CommerceCalc AI, an elite e-commerce CFO, Amazon/Flipkart/Meesho marketplace expert, "
            "and Indian GST tax advisor. Provide highly accurate, math-backed, actionable e-commerce advice. "
            "Include specific numbers, formulas, and tactical recommendations where applicable. "
            "Format beautifully with clean Markdown headings, bullet points, and highlighted takeaways."
        )

        def call():
            return self.ai.generate_response(system_prompt, query)

        self.worker = AICopilotWorker(call)
        self.worker.finished_signal.connect(self._on_chat_success)
        self.worker.error_signal.connect(self._on_chat_error)
        self.worker.start()

    def _on_chat_success(self, text: str):
        self.prog_chat.setVisible(False)
        self.btn_send_chat.setEnabled(True)
        self.out_chat.setHtml(markdown_to_html_simple(text))

    def _on_chat_error(self, err: str):
        self.prog_chat.setVisible(False)
        self.btn_send_chat.setEnabled(True)
        self.out_chat.setHtml(f"<div style='color: #dc2626; padding: 12px;'><strong>Error:</strong> {err}</div>")

    # -------------------------------------------------------------
    # Tab 2: HSN & GST Finder
    # -------------------------------------------------------------
    def _build_hsn_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        lbl = QLabel("Enter Product Name or Description for Instant HSN & GST Slab Resolution:")
        lbl.setStyleSheet("font-weight: bold; color: #334155;")
        layout.addWidget(lbl)

        h_box = QHBoxLayout()
        self.txt_hsn_input = QLineEdit()
        self.txt_hsn_input.setPlaceholderText("e.g. Wireless Bluetooth Noise-Cancelling Over-Ear Headphones")
        self.txt_hsn_input.setFixedHeight(40)
        self.txt_hsn_input.returnPressed.connect(self._run_hsn_query)
        h_box.addWidget(self.txt_hsn_input, 1)

        self.btn_hsn = QPushButton("🔍 Classify HSN & GST")
        self.btn_hsn.setFixedHeight(40)
        self.btn_hsn.setStyleSheet("""
            QPushButton {
                background: #0284c7;
                color: white;
                font-weight: bold;
                border-radius: 6px;
                padding: 0 18px;
            }
            QPushButton:hover {
                background: #0369a1;
            }
        """)
        self.btn_hsn.clicked.connect(self._run_hsn_query)
        h_box.addWidget(self.btn_hsn)
        layout.addLayout(h_box)

        self.prog_hsn = QProgressBar()
        self.prog_hsn.setRange(0, 0)
        self.prog_hsn.setFixedHeight(4)
        self.prog_hsn.setVisible(False)
        self.prog_hsn.setStyleSheet("QProgressBar::chunk { background: #0284c7; }")
        layout.addWidget(self.prog_hsn)

        self.out_hsn = QTextBrowser()
        self.out_hsn.setHtml("""
            <div style='font-family: Segoe UI, sans-serif; color: #64748b; padding: 20px; text-align: center;'>
                Enter any item to find its 8-digit HSN code, Indian GST rate, and marketplace fee commission tier.
            </div>
        """)
        self.out_hsn.setStyleSheet("border: 1px solid #e2e8f0; border-radius: 6px; padding: 12px;")
        layout.addWidget(self.out_hsn, 1)

        return w

    def _run_hsn_query(self):
        desc = self.txt_hsn_input.text().strip()
        if not desc:
            return

        self.prog_hsn.setVisible(True)
        self.btn_hsn.setEnabled(False)

        def call():
            return self.ai.classify_product_and_fees(desc)

        self.worker = AICopilotWorker(call)
        self.worker.finished_signal.connect(self._on_hsn_success)
        self.worker.error_signal.connect(self._on_hsn_error)
        self.worker.start()

    def _on_hsn_success(self, text: str):
        self.prog_hsn.setVisible(False)
        self.btn_hsn.setEnabled(True)
        self.out_hsn.setHtml(markdown_to_html_simple(text))

    def _on_hsn_error(self, err: str):
        self.prog_hsn.setVisible(False)
        self.btn_hsn.setEnabled(True)
        self.out_hsn.setHtml(f"<div style='color: #dc2626; padding: 12px;'><strong>Error:</strong> {err}</div>")

    # -------------------------------------------------------------
    # Tab 3: Competitor Price War Simulator
    # -------------------------------------------------------------
    def _build_war_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        grid = QGridLayout()
        grid.setSpacing(10)

        grid.addWidget(QLabel("Your Current Selling Price (₹):"), 0, 0)
        self.txt_war_price = QLineEdit("999")
        grid.addWidget(self.txt_war_price, 0, 1)

        grid.addWidget(QLabel("Product Acquisition Cost (₹):"), 0, 2)
        self.txt_war_cost = QLineEdit("350")
        grid.addWidget(self.txt_war_cost, 0, 3)

        grid.addWidget(QLabel("Marketplace + Shipping Fees (₹):"), 1, 0)
        self.txt_war_fees = QLineEdit("260")
        grid.addWidget(self.txt_war_fees, 1, 1)

        grid.addWidget(QLabel("Competitor Undercut Threat:"), 1, 2)
        self.txt_war_threat = QLineEdit("Competitor dropped price from ₹999 to ₹799")
        grid.addWidget(self.txt_war_threat, 1, 3)

        layout.addLayout(grid)

        self.btn_war = QPushButton("⚔️ Simulate Price War & Counter-Tactics")
        self.btn_war.setFixedHeight(40)
        self.btn_war.setStyleSheet("""
            QPushButton {
                background: #b91c1c;
                color: white;
                font-weight: bold;
                border-radius: 6px;
            }
            QPushButton:hover {
                background: #991b1b;
            }
        """)
        self.btn_war.clicked.connect(self._run_war_query)
        layout.addWidget(self.btn_war)

        self.prog_war = QProgressBar()
        self.prog_war.setRange(0, 0)
        self.prog_war.setFixedHeight(4)
        self.prog_war.setVisible(False)
        self.prog_war.setStyleSheet("QProgressBar::chunk { background: #b91c1c; }")
        layout.addWidget(self.prog_war)

        self.out_war = QTextBrowser()
        self.out_war.setStyleSheet("border: 1px solid #e2e8f0; border-radius: 6px; padding: 12px;")
        layout.addWidget(self.out_war, 1)

        return w

    def _run_war_query(self):
        data = {
            "selling_price": self.txt_war_price.text().strip(),
            "purchase_cost": self.txt_war_cost.text().strip(),
            "fixed_fees": self.txt_war_fees.text().strip(),
            "breakeven_price": str(float(self.txt_war_cost.text() or 0) + float(self.txt_war_fees.text() or 0)),
            "net_profit": str(float(self.txt_war_price.text() or 0) - float(self.txt_war_cost.text() or 0) - float(self.txt_war_fees.text() or 0)),
            "competitor_discount": self.txt_war_threat.text().strip(),
        }

        self.prog_war.setVisible(True)
        self.btn_war.setEnabled(False)

        def call():
            return self.ai.simulate_competitor_price_war(data)

        self.worker = AICopilotWorker(call)
        self.worker.finished_signal.connect(self._on_war_success)
        self.worker.error_signal.connect(self._on_war_error)
        self.worker.start()

    def _on_war_success(self, text: str):
        self.prog_war.setVisible(False)
        self.btn_war.setEnabled(True)
        self.out_war.setHtml(markdown_to_html_simple(text))

    def _on_war_error(self, err: str):
        self.prog_war.setVisible(False)
        self.btn_war.setEnabled(True)
        self.out_war.setHtml(f"<div style='color: #dc2626; padding: 12px;'><strong>Error:</strong> {err}</div>")

    # -------------------------------------------------------------
    # Tab 4: RTO Reduction Playbook
    # -------------------------------------------------------------
    def _build_rto_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        lbl = QLabel("Generate a Customized Return & RTO Mitigation Playbook for your Store:")
        lbl.setStyleSheet("font-weight: bold; color: #334155;")
        layout.addWidget(lbl)

        grid = QGridLayout()
        grid.addWidget(QLabel("Primary Channel:"), 0, 0)
        self.cmb_rto_channel = QComboBox()
        self.cmb_rto_channel.addItems(["Shopify (COD-Heavy)", "Amazon Easy Ship", "Flipkart", "Meesho (No-Commission)", "WooCommerce D2C"])
        grid.addWidget(self.cmb_rto_channel, 0, 1)

        grid.addWidget(QLabel("Current COD %:"), 0, 2)
        self.txt_rto_cod = QLineEdit("65%")
        grid.addWidget(self.txt_rto_cod, 0, 3)

        grid.addWidget(QLabel("Current RTO %:"), 1, 0)
        self.txt_rto_rate = QLineEdit("28%")
        grid.addWidget(self.txt_rto_rate, 1, 1)

        grid.addWidget(QLabel("Avg Forward + Reverse Freight (₹):"), 1, 2)
        self.txt_rto_freight = QLineEdit("₹140")
        grid.addWidget(self.txt_rto_freight, 1, 3)

        layout.addLayout(grid)

        self.btn_rto = QPushButton("🛡️ Generate RTO Defense Strategy")
        self.btn_rto.setFixedHeight(40)
        self.btn_rto.setStyleSheet("""
            QPushButton {
                background: #059669;
                color: white;
                font-weight: bold;
                border-radius: 6px;
            }
            QPushButton:hover {
                background: #047857;
            }
        """)
        self.btn_rto.clicked.connect(self._run_rto_query)
        layout.addWidget(self.btn_rto)

        self.prog_rto = QProgressBar()
        self.prog_rto.setRange(0, 0)
        self.prog_rto.setFixedHeight(4)
        self.prog_rto.setVisible(False)
        self.prog_rto.setStyleSheet("QProgressBar::chunk { background: #059669; }")
        layout.addWidget(self.prog_rto)

        self.out_rto = QTextBrowser()
        self.out_rto.setStyleSheet("border: 1px solid #e2e8f0; border-radius: 6px; padding: 12px;")
        layout.addWidget(self.out_rto, 1)

        return w

    def _run_rto_query(self):
        channel = self.cmb_rto_channel.currentText()
        cod_pct = self.txt_rto_cod.text().strip()
        rto_pct = self.txt_rto_rate.text().strip()
        freight = self.txt_rto_freight.text().strip()

        prompt = (
            f"Generate a battle-tested RTO (Return to Origin) reduction playbook for an Indian e-commerce seller.\n"
            f"Channel: {channel}\n"
            f"COD Share: {cod_pct}\n"
            f"RTO Rate: {rto_pct}\n"
            f"Average Two-way Shipping Loss: {freight}\n\n"
            "Include: 1) WhatsApp/SMS automated order verification scripts, 2) Dynamic prepaid conversion incentives (e.g. ₹50 instant discount vs COD charge), "
            "3) High-risk PIN code blacklisting criteria, 4) Packaging and unboxing video stickers to fight customer false returns, "
            "and 5) Mathematical formula to bake RTO cost into product pricing without losing sales volume."
        )

        self.prog_rto.setVisible(True)
        self.btn_rto.setEnabled(False)

        system_prompt = (
            "You are India's premier D2C logistics & RTO turnaround specialist. "
            "Deliver an actionable, battle-tested playbook formatted with crisp Markdown."
        )

        def call():
            return self.ai.generate_response(system_prompt, prompt)

        self.worker = AICopilotWorker(call)
        self.worker.finished_signal.connect(self._on_rto_success)
        self.worker.error_signal.connect(self._on_rto_error)
        self.worker.start()

    def _on_rto_success(self, text: str):
        self.prog_rto.setVisible(False)
        self.btn_rto.setEnabled(True)
        self.out_rto.setHtml(markdown_to_html_simple(text))

    def _on_rto_error(self, err: str):
        self.prog_rto.setVisible(False)
        self.btn_rto.setEnabled(True)
        self.out_rto.setHtml(f"<div style='color: #dc2626; padding: 12px;'><strong>Error:</strong> {err}</div>")
