"""
Comprehensive E-Commerce SEO & Keyword Intelligence Suite for CommerceCalc.

Features:
- Tab 1: 🔍 Multi-Channel Keyword Discovery (Google India, Amazon Buyers, Flipkart, Wholesale).
- Tab 2: ✍️ Title & SERP Snippet Preview (Google & Amazon search preview, char counters).
- Tab 3: 🏷️ Amazon 249-Byte Backend Search Terms Formatter (UTF-8 byte safety, 1-click clean).
- Tab 4: 🚫 Negative Keywords Builder (PPC budget protection for Amazon & Google Ads).
- Tab 5: 📊 Keyword Density & On-Page SEO Analyzer (Real-time occurrences & density check).
- Tab 6: ✨ AI Listing & PPC Copilot (Gemini 2.5 Flash / Groq listing generator).
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextBrowser,
    QLineEdit, QPushButton, QComboBox, QCheckBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QProgressBar, QGroupBox, QGridLayout,
    QFrame, QMessageBox, QApplication, QFileDialog, QTabWidget,
    QTextEdit, QSplitter
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont, QColor
import csv

from ...services.keyword_service import GoogleKeywordResearchService
from ...services.google_integration_service import GoogleIntegrationService
from ..widgets.ai_dialog import markdown_to_html_simple
from ..widgets.google_link_dialog import GoogleLinkDialog


class KeywordWorker(QThread):
    finished_signal = Signal(list)
    error_signal = Signal(str)

    def __init__(self, seed: str, country: str, channel: str, deep: bool):
        super().__init__()
        self.seed = seed
        self.country = country
        self.channel = channel
        self.deep = deep

    def run(self):
        try:
            results = GoogleKeywordResearchService.fetch_google_suggestions(
                self.seed, country=self.country, channel_filter=self.channel, deep_scan=self.deep
            )
            self.finished_signal.emit(results)
        except Exception as e:
            self.error_signal.emit(str(e))


class AISeoWorker(QThread):
    finished_signal = Signal(str)
    error_signal = Signal(str)

    def __init__(self, seed: str, keywords: list, channel: str):
        super().__init__()
        self.seed = seed
        self.keywords = keywords
        self.channel = channel

    def run(self):
        try:
            res = GoogleKeywordResearchService.generate_seo_strategy_with_ai(
                self.seed, self.keywords, channel=self.channel
            )
            self.finished_signal.emit(res)
        except Exception as e:
            self.error_signal.emit(str(e))


class KeywordResearchPage(QWidget):
    """Production-grade E-Commerce SEO and Keyword Intelligence Suite."""

    def __init__(self, db_session=None, parent=None):
        super().__init__(parent)
        self.db_session = db_session
        self._current_keywords = []
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 24)
        main_layout.setSpacing(14)

        # ─── Top Header Card ──────────────────────────────────────────
        header_card = QFrame()
        header_card.setObjectName("card")
        h_layout = QVBoxLayout(header_card)
        h_layout.setContentsMargins(16, 12, 16, 12)
        h_layout.setSpacing(6)

        top_row = QHBoxLayout()
        title_box = QVBoxLayout()
        lbl_title = QLabel("🔍 E-Commerce Keyword Intelligence & SEO Suite")
        lbl_title.setFont(QFont("Segoe UI", 15, QFont.Bold))
        lbl_title.setObjectName("section_title")
        title_box.addWidget(lbl_title)

        lbl_desc = QLabel(
            "Live Google, Amazon & Flipkart buyer queries • Amazon 249-Byte Backend Terms • SERP Snippet Preview • Negative Keywords • AI Listing Copy"
        )
        lbl_desc.setStyleSheet("color: #94a3b8; font-size: 10pt;")
        title_box.addWidget(lbl_desc)
        top_row.addLayout(title_box)
        top_row.addStretch()

        self.lbl_google_badge = QLabel()
        self.lbl_google_badge.setFont(QFont("Segoe UI", 9, QFont.Bold))
        top_row.addWidget(self.lbl_google_badge)

        self.btn_google_link = QPushButton("🔗 Google Linking Options")
        self.btn_google_link.setObjectName("secondary_btn")
        self.btn_google_link.setFixedHeight(34)
        self.btn_google_link.clicked.connect(self._open_google_link_dialog)
        top_row.addWidget(self.btn_google_link)

        h_layout.addLayout(top_row)
        main_layout.addWidget(header_card)
        self._refresh_google_badge()

        # ─── Main Tabs ────────────────────────────────────────────────
        self.tabs = QTabWidget()
        self.tabs.setObjectName("seo_tabs")

        # Tab 1: Keyword Finder
        self.tab_keywords = QWidget()
        self._setup_tab_keywords()
        self.tabs.addTab(self.tab_keywords, "🔍 Keyword Discovery")

        # Tab 2: Title & SERP Snippet
        self.tab_serp = QWidget()
        self._setup_tab_serp()
        self.tabs.addTab(self.tab_serp, "✍️ Title & SERP Preview")

        # Tab 3: Amazon 249-Byte Backend Formatter
        self.tab_backend = QWidget()
        self._setup_tab_backend()
        self.tabs.addTab(self.tab_backend, "🏷️ Amazon 249-Byte Terms")

        # Tab 4: Negative Keywords
        self.tab_negative = QWidget()
        self._setup_tab_negative()
        self.tabs.addTab(self.tab_negative, "🚫 Negative Keywords (PPC)")

        # Tab 5: Keyword Density & On-Page
        self.tab_density = QWidget()
        self._setup_tab_density()
        self.tabs.addTab(self.tab_density, "📊 Keyword Density")

        # Tab 6: AI Listing & PPC
        self.tab_ai = QWidget()
        self._setup_tab_ai()
        self.tabs.addTab(self.tab_ai, "✨ AI Listing Copilot")

        main_layout.addWidget(self.tabs, 1)

    # ═══════════════════════════════════════════════════════════════════
    # TAB 1: KEYWORD DISCOVERY
    # ═══════════════════════════════════════════════════════════════════
    def _setup_tab_keywords(self):
        layout = QVBoxLayout(self.tab_keywords)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        # Search Controls Card
        ctrl_card = QFrame()
        ctrl_card.setObjectName("card")
        c_layout = QVBoxLayout(ctrl_card)
        c_layout.setContentsMargins(12, 10, 12, 10)

        r1 = QHBoxLayout()
        r1.addWidget(QLabel("Product / Niche Seed:"))

        self.txt_seed = QLineEdit("leather wallet")
        self.txt_seed.setPlaceholderText("e.g. bluetooth earbuds, cotton t shirt, saffron face cream...")
        self.txt_seed.setFixedHeight(36)
        self.txt_seed.returnPressed.connect(self._run_keyword_search)
        r1.addWidget(self.txt_seed, 2)

        r1.addWidget(QLabel("Channel:"))
        self.cmb_channel = QComboBox()
        self.cmb_channel.addItems([
            "All Channels",
            "Google India (gl=in)",
            "Amazon India Buyers",
            "Flipkart Buyers",
            "Wholesale & B2B",
        ])
        self.cmb_channel.setFixedHeight(36)
        r1.addWidget(self.cmb_channel, 1)

        r1.addWidget(QLabel("Region:"))
        self.cmb_country = QComboBox()
        self.cmb_country.addItem("India (gl=in)", "in")
        self.cmb_country.addItem("United States (gl=us)", "us")
        self.cmb_country.addItem("United Kingdom (gl=uk)", "uk")
        self.cmb_country.addItem("UAE (gl=ae)", "ae")
        self.cmb_country.setFixedHeight(36)
        r1.addWidget(self.cmb_country)

        self.chk_deep = QCheckBox("Deep A-Z Scan")
        self.chk_deep.setChecked(True)
        r1.addWidget(self.chk_deep)

        self.btn_search = QPushButton("🔍 Find Keywords")
        self.btn_search.setObjectName("primary_btn")
        self.btn_search.setFixedHeight(36)
        self.btn_search.clicked.connect(self._run_keyword_search)
        r1.addWidget(self.btn_search)

        c_layout.addLayout(r1)
        layout.addWidget(ctrl_card)

        # Progress bar
        self.prog = QProgressBar()
        self.prog.setRange(0, 0)
        self.prog.setFixedHeight(4)
        self.prog.setVisible(False)
        layout.addWidget(self.prog)

        # Table & Actions Bar
        tbl_top = QHBoxLayout()
        self.lbl_count = QLabel("Discovered Keywords: 0")
        self.lbl_count.setFont(QFont("Segoe UI", 10, QFont.Bold))
        tbl_top.addWidget(self.lbl_count)
        tbl_top.addStretch()

        self.btn_send_backend = QPushButton("🏷️ Send to 249-Byte Optimizer")
        self.btn_send_backend.setObjectName("secondary_btn")
        self.btn_send_backend.setFixedHeight(30)
        self.btn_send_backend.clicked.connect(self._send_to_backend_tab)
        tbl_top.addWidget(self.btn_send_backend)

        self.btn_copy_kws = QPushButton("📋 Copy All")
        self.btn_copy_kws.setObjectName("secondary_btn")
        self.btn_copy_kws.setFixedHeight(30)
        self.btn_copy_kws.clicked.connect(self._copy_all_kws)
        tbl_top.addWidget(self.btn_copy_kws)

        self.btn_export_csv = QPushButton("📤 Export CSV")
        self.btn_export_csv.setObjectName("secondary_btn")
        self.btn_export_csv.setFixedHeight(30)
        self.btn_export_csv.clicked.connect(self._export_csv)
        tbl_top.addWidget(self.btn_export_csv)

        self.btn_planner = QPushButton("💡 Keyword Planner")
        self.btn_planner.setObjectName("secondary_btn")
        self.btn_planner.setFixedHeight(30)
        self.btn_planner.clicked.connect(GoogleIntegrationService.open_google_keyword_planner)
        tbl_top.addWidget(self.btn_planner)

        layout.addLayout(tbl_top)

        # Table with rich metrics
        self.table = QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels([
            "#", "Search Query", "Channel", "Search Intent", "Est. Volume", "Est. CPC", "KD%", "Google Trends"
        ])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeToContents)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table, 1)

    # ═══════════════════════════════════════════════════════════════════
    # TAB 2: PRODUCT TITLE & SERP SNIPPET PREVIEW
    # ═══════════════════════════════════════════════════════════════════
    def _setup_tab_serp(self):
        layout = QVBoxLayout(self.tab_serp)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(14)

        top_form = QFrame()
        top_form.setObjectName("card")
        tf_layout = QGridLayout(top_form)
        tf_layout.setSpacing(10)

        # Title Field
        tf_layout.addWidget(QLabel("Product Listing Title:"), 0, 0)
        self.txt_listing_title = QLineEdit("Urban Hide Men's Genuine Hunter Leather RFID Protected Bifold Wallet with Coin Pocket")
        self.txt_listing_title.setFixedHeight(34)
        self.txt_listing_title.textChanged.connect(self._update_serp_previews)
        tf_layout.addWidget(self.txt_listing_title, 0, 1)

        self.lbl_title_count = QLabel("Chars: 0 / 200")
        self.lbl_title_count.setFixedWidth(120)
        self.lbl_title_count.setFont(QFont("Segoe UI", 9, QFont.Bold))
        tf_layout.addWidget(self.lbl_title_count, 0, 2)

        # Brand & Price Field
        tf_layout.addWidget(QLabel("Brand Name & Selling Price:"), 1, 0)
        b_row = QHBoxLayout()
        self.txt_brand = QLineEdit("Urban Hide")
        self.txt_brand.setPlaceholderText("Brand name")
        self.txt_brand.setFixedHeight(32)
        self.txt_brand.textChanged.connect(self._update_serp_previews)
        b_row.addWidget(self.txt_brand, 1)

        self.txt_serp_price = QLineEdit("799")
        self.txt_serp_price.setPlaceholderText("Price in ₹")
        self.txt_serp_price.setFixedHeight(32)
        self.txt_serp_price.textChanged.connect(self._update_serp_previews)
        b_row.addWidget(self.txt_serp_price, 1)
        tf_layout.addLayout(b_row, 1, 1)

        # Meta Description / Key Feature
        tf_layout.addWidget(QLabel("Meta Description / Highlights:"), 2, 0)
        self.txt_meta_desc = QLineEdit("Crafted from 100% genuine vintage hunter leather. Features 8 card slots, 2 currency compartments, RFID blocking layer, and gift box packaging.")
        self.txt_meta_desc.setFixedHeight(34)
        self.txt_meta_desc.textChanged.connect(self._update_serp_previews)
        tf_layout.addWidget(self.txt_meta_desc, 2, 1)

        self.lbl_desc_count = QLabel("Chars: 0 / 160")
        self.lbl_desc_count.setFixedWidth(120)
        self.lbl_desc_count.setFont(QFont("Segoe UI", 9, QFont.Bold))
        tf_layout.addWidget(self.lbl_desc_count, 2, 2)

        layout.addWidget(top_form)

        # Live Previews Splitter
        preview_group = QGroupBox("Live Marketplace & Google SERP Simulations")
        pg_layout = QVBoxLayout(preview_group)
        pg_layout.setSpacing(12)

        # Google Search Preview Box
        self.serp_google = QTextBrowser()
        self.serp_google.setFixedHeight(120)
        self.serp_google.setObjectName("serp_box")
        pg_layout.addWidget(QLabel("🌐 Google Search Results Simulation (Desktop):"))
        pg_layout.addWidget(self.serp_google)

        # Amazon Search Result Card Preview
        self.serp_amazon = QTextBrowser()
        self.serp_amazon.setFixedHeight(140)
        self.serp_amazon.setObjectName("serp_box")
        pg_layout.addWidget(QLabel("🛍️ Amazon India Product Card Simulation:"))
        pg_layout.addWidget(self.serp_amazon)

        layout.addWidget(preview_group)
        self._update_serp_previews()

    def _update_serp_previews(self):
        title = self.txt_listing_title.text().strip()
        brand = self.txt_brand.text().strip()
        price = self.txt_serp_price.text().strip() or "799"
        desc = self.txt_meta_desc.text().strip()

        # Update counters
        t_len = len(title)
        self.lbl_title_count.setText(f"Chars: {t_len} / 200")
        if 140 <= t_len <= 200:
            self.lbl_title_count.setStyleSheet("color: #4ade80;")
        elif t_len > 200:
            self.lbl_title_count.setStyleSheet("color: #f87171;")
        else:
            self.lbl_title_count.setStyleSheet("color: #fbbf24;")

        d_len = len(desc)
        self.lbl_desc_count.setText(f"Chars: {d_len} / 160")
        if 120 <= d_len <= 160:
            self.lbl_desc_count.setStyleSheet("color: #4ade80;")
        elif d_len > 160:
            self.lbl_desc_count.setStyleSheet("color: #f87171;")
        else:
            self.lbl_desc_count.setStyleSheet("color: #cbd5e1;")

        # Google HTML
        google_html = f"""
        <div style='font-family: Arial, sans-serif; padding: 10px; background: #ffffff; color: #1a0dab; border-radius: 6px;'>
            <div style='font-size: 12px; color: #202124;'>https://www.yourbrand.in › products › {brand.lower().replace(" ", "-")}</div>
            <div style='font-size: 17px; font-weight: normal; color: #1a0dab; text-decoration: underline; margin-top: 2px;'>{title[:65]}{'...' if len(title) > 65 else ''}</div>
            <div style='font-size: 13px; color: #4d5156; margin-top: 3px;'>₹{price}.00 · In stock · {desc[:155]}</div>
        </div>
        """
        self.serp_google.setHtml(google_html)

        # Amazon HTML
        amazon_html = f"""
        <div style='font-family: Arial, sans-serif; padding: 12px; background: #ffffff; color: #0f1111; border-radius: 6px;'>
            <div style='font-size: 11px; color: #565959; font-weight: bold;'>Sponsored · {brand}</div>
            <div style='font-size: 15px; font-weight: 500; color: #007185; margin-top: 2px;'>{title}</div>
            <div style='font-size: 12px; color: #e67a00; margin-top: 4px;'>★★★★☆ <span style='color: #007185;'>(1,284 ratings)</span></div>
            <div style='font-size: 18px; font-weight: bold; color: #b12704; margin-top: 4px;'>₹{price} <span style='font-size: 12px; color: #565959; text-decoration: line-through;'>₹1,999</span> <span style='font-size: 11px; color: #007600;'>prime FREE One-Day</span></div>
        </div>
        """
        self.serp_amazon.setHtml(amazon_html)

    # ═══════════════════════════════════════════════════════════════════
    # TAB 3: AMAZON 249-BYTE BACKEND SEARCH TERMS FORMATTER
    # ═══════════════════════════════════════════════════════════════════
    def _setup_tab_backend(self):
        layout = QVBoxLayout(self.tab_backend)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)

        info = QFrame()
        info.setObjectName("info_box")
        i_layout = QVBoxLayout(info)
        i_title = QLabel("Amazon Strictly Enforces the 249-Byte Generic Keywords Limit")
        i_title.setFont(QFont("Segoe UI", 10, QFont.Bold))
        i_layout.addWidget(i_title)
        i_desc = QLabel(
            "• If your backend search terms exceed 249 bytes, Amazon indexes ZERO of them.\n"
            "• Do NOT use commas, periods, or punctuation (use spaces only).\n"
            "• Do NOT duplicate words already in your title or bullet points.\n"
            "• Do NOT include brand names, competitor trademarks, or subjective claims ('best', 'cheap')."
        )
        i_desc.setStyleSheet("font-size: 9.5pt;")
        i_layout.addWidget(i_desc)
        layout.addWidget(info)

        layout.addWidget(QLabel("Raw Keyword Ideas / Candidate Search Terms:"))
        self.txt_raw_backend = QTextEdit()
        self.txt_raw_backend.setPlaceholderText("Paste all keywords, queries, or ideas here (commas, newlines, duplicate terms are fine)...")
        self.txt_raw_backend.setFixedHeight(110)
        self.txt_raw_backend.textChanged.connect(self._recalculate_backend_bytes)
        layout.addWidget(self.txt_raw_backend)

        btn_row = QHBoxLayout()
        self.btn_optimize_backend = QPushButton("⚡ Clean & Compress to 249 Bytes")
        self.btn_optimize_backend.setObjectName("primary_btn")
        self.btn_optimize_backend.setFixedHeight(36)
        self.btn_optimize_backend.clicked.connect(self._optimize_backend_terms)
        btn_row.addWidget(self.btn_optimize_backend)

        self.btn_copy_backend = QPushButton("📋 Copy Clean Backend String")
        self.btn_copy_backend.setObjectName("secondary_btn")
        self.btn_copy_backend.setFixedHeight(36)
        self.btn_copy_backend.clicked.connect(self._copy_backend_terms)
        btn_row.addWidget(self.btn_copy_backend)
        layout.addLayout(btn_row)

        layout.addWidget(QLabel("Amazon-Ready Generic Keywords (Strictly Space-Separated):"))
        self.txt_clean_backend = QLineEdit()
        self.txt_clean_backend.setFixedHeight(38)
        self.txt_clean_backend.textChanged.connect(self._recalculate_backend_bytes)
        layout.addWidget(self.txt_clean_backend)

        # Byte Gauge
        gauge_box = QHBoxLayout()
        self.prog_bytes = QProgressBar()
        self.prog_bytes.setRange(0, 249)
        self.prog_bytes.setValue(0)
        self.prog_bytes.setFixedHeight(16)
        gauge_box.addWidget(self.prog_bytes, 1)

        self.lbl_byte_status = QLabel("0 / 249 UTF-8 bytes (Safe)")
        self.lbl_byte_status.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.lbl_byte_status.setFixedWidth(220)
        gauge_box.addWidget(self.lbl_byte_status)
        layout.addLayout(gauge_box)

        layout.addStretch()

    def _optimize_backend_terms(self):
        raw = self.txt_raw_backend.toPlainText().strip()
        if not raw and self._current_keywords:
            raw = " ".join([k["keyword"] for k in self._current_keywords])
            self.txt_raw_backend.setPlainText(raw)

        if not raw:
            QMessageBox.information(self, "No Terms", "Please enter keywords or fetch suggestions first.")
            return

        res = GoogleKeywordResearchService.optimize_amazon_backend_search_terms(raw)
        self.txt_clean_backend.setText(res["clean_terms"])
        self._recalculate_backend_bytes()

    def _recalculate_backend_bytes(self):
        text = self.txt_clean_backend.text().strip()
        byte_count = len(text.encode("utf-8"))
        self.prog_bytes.setValue(min(byte_count, 249))

        if byte_count <= 249:
            self.lbl_byte_status.setText(f"🟢 {byte_count} / 249 bytes (SAFE)")
            self.lbl_byte_status.setStyleSheet("color: #4ade80;")
        else:
            self.lbl_byte_status.setText(f"🔴 {byte_count} / 249 bytes (OVER LIMIT!)")
            self.lbl_byte_status.setStyleSheet("color: #f87171;")

    def _copy_backend_terms(self):
        text = self.txt_clean_backend.text().strip()
        if not text:
            return
        clipboard = QApplication.clipboard()
        clipboard.setText(text)
        QMessageBox.information(self, "Copied", f"Copied {len(text.encode('utf-8'))} bytes to clipboard!")

    def _send_to_backend_tab(self):
        if not self._current_keywords:
            QMessageBox.information(self, "No Keywords", "Please discover keywords first.")
            return
        raw = " ".join([k["keyword"] for k in self._current_keywords])
        self.txt_raw_backend.setPlainText(raw)
        self._optimize_backend_terms()
        self.tabs.setCurrentWidget(self.tab_backend)

    # ═══════════════════════════════════════════════════════════════════
    # TAB 4: NEGATIVE KEYWORDS BUILDER (PPC BUDGET PROTECTION)
    # ═══════════════════════════════════════════════════════════════════
    def _setup_tab_negative(self):
        layout = QVBoxLayout(self.tab_negative)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)

        info = QFrame()
        info.setObjectName("warning_box")
        i_layout = QVBoxLayout(info)
        w_title = QLabel("Protect Your PPC Budget from Wasted Ad Spend")
        w_title.setFont(QFont("Segoe UI", 10, QFont.Bold))
        i_layout.addWidget(w_title)
        w_desc = QLabel(
            "Adding negative keywords prevents unqualified buyers (e.g. searching 'free', 'diy', 'repair', 'fake') "
            "from clicking your sponsored ads and draining your ad budget."
        )
        i_layout.addWidget(w_desc)
        layout.addWidget(info)

        r1 = QHBoxLayout()
        r1.addWidget(QLabel("Product Niche Seed:"))
        self.txt_neg_seed = QLineEdit("leather wallet")
        self.txt_neg_seed.setFixedHeight(34)
        r1.addWidget(self.txt_neg_seed, 1)

        btn_gen_neg = QPushButton("🚫 Generate Negative Keyword Lists")
        btn_gen_neg.setObjectName("primary_btn")
        btn_gen_neg.setFixedHeight(34)
        btn_gen_neg.clicked.connect(self._generate_negatives)
        r1.addWidget(btn_gen_neg)
        layout.addLayout(r1)

        split = QHBoxLayout()

        # Left: Negative Phrase
        col1 = QVBoxLayout()
        col1.addWidget(QLabel("Negative Phrase Keywords (Block terms in any phrase):"))
        self.txt_neg_phrase = QTextEdit()
        self.txt_neg_phrase.setReadOnly(True)
        col1.addWidget(self.txt_neg_phrase)
        btn_copy_p = QPushButton("📋 Copy Negative Phrase List")
        btn_copy_p.setObjectName("secondary_btn")
        btn_copy_p.clicked.connect(lambda: self._copy_text(self.txt_neg_phrase.toPlainText()))
        col1.addWidget(btn_copy_p)
        split.addLayout(col1)

        # Right: Negative Exact
        col2 = QVBoxLayout()
        col2.addWidget(QLabel("Negative Exact Keywords (Block specific non-converting searches):"))
        self.txt_neg_exact = QTextEdit()
        self.txt_neg_exact.setReadOnly(True)
        col2.addWidget(self.txt_neg_exact)
        btn_copy_e = QPushButton("📋 Copy Negative Exact List")
        btn_copy_e.setObjectName("secondary_btn")
        btn_copy_e.clicked.connect(lambda: self._copy_text(self.txt_neg_exact.toPlainText()))
        col2.addWidget(btn_copy_e)
        split.addLayout(col2)

        layout.addLayout(split)
        self._generate_negatives()

    def _generate_negatives(self):
        seed = self.txt_neg_seed.text().strip()
        candidates = [k["keyword"] for k in self._current_keywords]
        res = GoogleKeywordResearchService.generate_negative_keywords(seed, candidates)
        self.txt_neg_phrase.setPlainText("\n".join(res["negative_phrase"]))
        self.txt_neg_exact.setPlainText("\n".join(res["negative_exact"]))

    def _copy_text(self, text: str):
        if not text:
            return
        QApplication.clipboard().setText(text)
        QMessageBox.information(self, "Copied", f"Copied {len(text.splitlines())} negative keywords to clipboard!")

    # ═══════════════════════════════════════════════════════════════════
    # TAB 5: KEYWORD DENSITY & ON-PAGE SEO ANALYZER
    # ═══════════════════════════════════════════════════════════════════
    def _setup_tab_density(self):
        layout = QVBoxLayout(self.tab_density)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)

        layout.addWidget(QLabel("Focus Keywords to Check (comma-separated):"))
        self.txt_focus_kws = QLineEdit("leather wallet, rfid wallet, bifold, coin pocket, mens wallet")
        self.txt_focus_kws.setFixedHeight(34)
        self.txt_focus_kws.textChanged.connect(self._run_density_check)
        layout.addWidget(self.txt_focus_kws)

        layout.addWidget(QLabel("Product Listing Description / Bullet Points Content:"))
        self.txt_body_content = QTextEdit()
        self.txt_body_content.setPlainText(
            "This genuine leather wallet for men is engineered with RFID blocking technology. "
            "Our leather wallet features a classic bifold design with an integrated coin pocket and 8 credit card slots. "
            "Whether you need an everyday mens wallet or a premium gift, this rfid wallet delivers lasting durability and luxury."
        )
        self.txt_body_content.setFixedHeight(120)
        self.txt_body_content.textChanged.connect(self._run_density_check)
        layout.addWidget(self.txt_body_content)

        layout.addWidget(QLabel("Keyword Frequency & Density Analysis:"))
        self.tbl_density = QTableWidget(0, 4)
        self.tbl_density.setHorizontalHeaderLabels(["Focus Keyword", "Occurrences", "Density %", "SEO Optimization Status"])
        self.tbl_density.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tbl_density.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.tbl_density.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.tbl_density.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.tbl_density.setAlternatingRowColors(True)
        layout.addWidget(self.tbl_density, 1)

        self._run_density_check()

    def _run_density_check(self):
        content = self.txt_body_content.toPlainText()
        raw_kws = [k.strip() for k in self.txt_focus_kws.text().split(",") if k.strip()]
        results = GoogleKeywordResearchService.analyze_keyword_density(content, raw_kws)

        self.tbl_density.setRowCount(0)
        for i, item in enumerate(results):
            self.tbl_density.insertRow(i)
            self.tbl_density.setItem(i, 0, QTableWidgetItem(item["keyword"]))
            self.tbl_density.setItem(i, 1, QTableWidgetItem(str(item["count"])))
            self.tbl_density.setItem(i, 2, QTableWidgetItem(item["density_pct"]))

            status_item = QTableWidgetItem(item["status"])
            if "Optimal" in item["status"]:
                status_item.setForeground(QColor("#4ade80"))
            elif "Warning" in item["status"]:
                status_item.setForeground(QColor("#f87171"))
            else:
                status_item.setForeground(QColor("#fbbf24"))
            self.tbl_density.setItem(i, 3, status_item)

    # ═══════════════════════════════════════════════════════════════════
    # TAB 6: AI LISTING & PPC STRATEGY COPILOT
    # ═══════════════════════════════════════════════════════════════════
    def _setup_tab_ai(self):
        layout = QVBoxLayout(self.tab_ai)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)

        ctrl_row = QHBoxLayout()
        ctrl_row.addWidget(QLabel("Target E-Commerce Channel:"))
        self.cmb_ai_channel = QComboBox()
        self.cmb_ai_channel.addItems(["Amazon India", "Flipkart", "Shopify D2C Store", "Google Shopping"])
        self.cmb_ai_channel.setFixedHeight(34)
        ctrl_row.addWidget(self.cmb_ai_channel, 1)

        self.btn_ai_gen = QPushButton("✨ Generate Complete Listing & PPC Blueprint (Gemini 2.5 Flash)")
        self.btn_ai_gen.setObjectName("primary_btn")
        self.btn_ai_gen.setFixedHeight(36)
        self.btn_ai_gen.clicked.connect(self._generate_ai_seo)
        ctrl_row.addWidget(self.btn_ai_gen, 2)
        layout.addLayout(ctrl_row)

        self.out_seo = QTextBrowser()
        self.out_seo.setObjectName("card")
        self.out_seo.setHtml("""
            <div style='font-family: Segoe UI, sans-serif; color: #94a3b8; padding: 24px; text-align: center;'>
                <h3>AI E-Commerce SEO Copilot</h3>
                <p>Click 'Generate Complete Listing & PPC Blueprint' to synthesize all discovered keywords into an optimized Title, 5 Bullet Points, 249-byte Backend Search Terms, and targeted PPC Ad Campaigns.</p>
            </div>
        """)
        layout.addWidget(self.out_seo, 1)

    # ═══════════════════════════════════════════════════════════════════
    # CONTROLLER LOGIC
    # ═══════════════════════════════════════════════════════════════════
    def _refresh_google_badge(self):
        status = GoogleIntegrationService.get_status()
        if status["connected"]:
            self.lbl_google_badge.setText(f"🟢 Google Linked ({status['masked_key']})")
            self.lbl_google_badge.setStyleSheet("color: #4ade80; background: transparent; padding-right: 8px;")
        else:
            self.lbl_google_badge.setText("⚪ Google: Free Live Suggest Mode")
            self.lbl_google_badge.setStyleSheet("color: #94a3b8; background: transparent; padding-right: 8px;")

    def _open_google_link_dialog(self):
        dlg = GoogleLinkDialog(self)
        dlg.connection_changed.connect(lambda _: self._refresh_google_badge())
        dlg.exec()
        self._refresh_google_badge()

    def _run_keyword_search(self):
        seed = self.txt_seed.text().strip()
        if not seed:
            return

        self.btn_search.setEnabled(False)
        self.prog.setVisible(True)
        country = self.cmb_country.currentData() or "in"
        channel = self.cmb_channel.currentText()
        deep = self.chk_deep.isChecked()

        self.kw_worker = KeywordWorker(seed, country, channel, deep)
        self.kw_worker.finished_signal.connect(self._on_keywords_found)
        self.kw_worker.error_signal.connect(self._on_keyword_error)
        self.kw_worker.start()

    def _on_keywords_found(self, keywords: list):
        self.btn_search.setEnabled(True)
        self.prog.setVisible(False)
        self._current_keywords = keywords
        self.lbl_count.setText(f"Discovered Keywords: {len(keywords)}")

        country = self.cmb_country.currentData() or "in"
        self.table.setRowCount(0)
        for i, item in enumerate(keywords):
            self.table.insertRow(i)
            self.table.setItem(i, 0, QTableWidgetItem(str(i + 1)))

            kw_item = QTableWidgetItem(item["keyword"])
            kw_item.setFont(QFont("Segoe UI", 9, QFont.Bold))
            self.table.setItem(i, 1, kw_item)

            self.table.setItem(i, 2, QTableWidgetItem(item.get("channel", "Google Web")))

            intent_item = QTableWidgetItem(item.get("intent", "General"))
            if "Transactional" in item.get("intent", ""):
                intent_item.setForeground(QColor("#4ade80"))
            elif "Commercial" in item.get("intent", ""):
                intent_item.setForeground(QColor("#38bdf8"))
            self.table.setItem(i, 3, intent_item)

            self.table.setItem(i, 4, QTableWidgetItem(str(item.get("est_volume", "Medium"))))
            self.table.setItem(i, 5, QTableWidgetItem(str(item.get("est_cpc", "₹25.00"))))
            self.table.setItem(i, 6, QTableWidgetItem(str(item.get("kd_pct", "50%"))))

            # Column 7: Google Trends launcher button for this keyword
            btn_trend = QPushButton("📈 Trends")
            btn_trend.setObjectName("secondary_btn")
            btn_trend.setFixedHeight(24)
            kw_text = item["keyword"]
            btn_trend.clicked.connect(lambda checked=False, k=kw_text, c=country: GoogleIntegrationService.open_google_trends(k, c))
            self.table.setCellWidget(i, 7, btn_trend)

        # Update Negative Seed and Focus Keywords automatically
        self.txt_neg_seed.setText(self.txt_seed.text().strip())
        self._generate_negatives()

    def _on_keyword_error(self, err: str):
        self.btn_search.setEnabled(True)
        self.prog.setVisible(False)
        QMessageBox.warning(self, "Keyword Error", f"Failed to retrieve suggestions:\n{err}")

    def _generate_ai_seo(self):
        seed = self.txt_seed.text().strip()
        if not self._current_keywords:
            QMessageBox.information(self, "No Keywords", "Please search for keywords first.")
            return

        kws = [k["keyword"] for k in self._current_keywords]
        channel = self.cmb_ai_channel.currentText()

        self.btn_ai_gen.setEnabled(False)
        self.prog.setVisible(True)
        self.out_seo.setHtml("<div style='color: #38bdf8; padding: 12px;'><strong>Analyzing keyword clusters & synthesizing listing blueprint with Gemini 2.5 Flash...</strong></div>")

        self.seo_worker = AISeoWorker(seed, kws, channel)
        self.seo_worker.finished_signal.connect(self._on_seo_success)
        self.seo_worker.error_signal.connect(self._on_seo_error)
        self.seo_worker.start()

    def _on_seo_success(self, text: str):
        self.btn_ai_gen.setEnabled(True)
        self.prog.setVisible(False)
        self.out_seo.setHtml(markdown_to_html_simple(text))

    def _on_seo_error(self, err: str):
        self.btn_ai_gen.setEnabled(True)
        self.prog.setVisible(False)
        self.out_seo.setHtml(f"<div style='color: #f87171; padding: 12px;'><strong>AI Error:</strong> {err}</div>")

    def _copy_all_kws(self):
        if not self._current_keywords:
            return
        lines = [k["keyword"] for k in self._current_keywords]
        clipboard = QApplication.clipboard()
        clipboard.setText("\n".join(lines))
        QMessageBox.information(self, "Copied", f"Copied {len(lines)} keywords to clipboard!")

    def _export_csv(self):
        if not self._current_keywords:
            return
        path, _ = QFileDialog.getSaveFileName(self, "Save Keywords CSV", "ecommerce_high_rank_keywords.csv", "CSV Files (*.csv)")
        if path:
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["Rank", "Keyword", "Channel", "Intent", "Est. Volume", "Est. CPC", "KD%", "Source"])
                for i, k in enumerate(self._current_keywords, 1):
                    writer.writerow([
                        i,
                        k["keyword"],
                        k.get("channel", "Google"),
                        k.get("intent", "General"),
                        k.get("est_volume", ""),
                        k.get("est_cpc", ""),
                        k.get("kd_pct", ""),
                        k.get("source", "Google Live Autocomplete")
                    ])
            QMessageBox.information(self, "Exported", f"Successfully saved to:\n{path}")
