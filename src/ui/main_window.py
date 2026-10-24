"""
Main application window for CommerceCalc.

Manages navigation sidebar, page routing, toolbar, and global settings.
"""
import sys
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QLabel,
    QPushButton, QStackedWidget, QFrame, QSizePolicy, QLineEdit,
    QScrollArea, QApplication, QSplitter, QMessageBox, QStatusBar
)
from PySide6.QtCore import Qt, QSize, QTimer
from PySide6.QtGui import QFont, QIcon, QColor, QPalette, QAction

from .styles import DARK_THEME, LIGHT_THEME
from .pages.dashboard import DashboardPage
from .pages.profit_calc import ProductProfitPage
from .pages.target_price import TargetPricePage
from .pages.gst_calc import GSTCalculatorPage
from .pages.advertising_calc import AdvertisingPage
from .pages.shipping_calc import ShippingPage
from .pages.returns_calc import ReturnsRTOPage
from .pages.discounts_calc import DiscountsPage
from .pages.bundles_calc import BundleCalcPage
from .pages.dropshipping_calc import DropshippingPage
from .pages.digital_calc import DigitalProductsPage
from .pages.inventory_calc import InventoryPage
from .pages.landed_cost_calc import LandedCostPage
from .pages.settlement_calc import CashFlowPage
from .pages.bulk_calc import BulkCalcPage
from .pages.fee_profiles import FeeProfilesPage
from .pages.catalog import CatalogPage
from .pages.scenarios import ScenariosPage
from .pages.reports import ReportsPage
from .pages.settings_page import SettingsPage
from .pages.help_page import HelpPage
from .pages.ai_copilot import AICopilotPage
from .pages.integrations_page import IntegrationsPage
from .pages.updater_page import UpdaterPage
from .pages.keyword_research import KeywordResearchPage


class NavButton(QPushButton):
    """Navigation sidebar button."""

    def __init__(self, text: str, icon: str = "", parent=None):
        super().__init__(parent)
        display_text = f"  {icon}  {text}" if icon else f"  {text}"
        self.setText(display_text)
        self.setObjectName("nav_btn")
        self.setCheckable(True)
        self.setFlat(True)
        self.setMinimumHeight(42)
        self.setCursor(Qt.PointingHandCursor)
        self.setProperty("active", False)
        font = QFont()
        font.setPointSize(11)
        self.setFont(font)

    def set_active(self, active: bool):
        self.setProperty("active", "true" if active else "false")
        self.style().unpolish(self)
        self.style().polish(self)


class Sidebar(QFrame):
    """Navigation sidebar."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setFrameShape(QFrame.StyledPanel)
        self._nav_buttons = {}
        self._setup()

    def _setup(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Brand header
        brand_frame = QFrame()
        brand_frame.setObjectName("sidebar_brand")
        brand_layout = QVBoxLayout(brand_frame)
        brand_layout.setContentsMargins(16, 18, 16, 14)
        brand_layout.setSpacing(4)

        brand_name = QLabel("CommerceCalc")
        brand_name.setObjectName("brand_name")
        brand_font = QFont()
        brand_font.setPointSize(16)
        brand_font.setBold(True)
        brand_name.setFont(brand_font)

        brand_tagline = QLabel("E-Commerce Profit Suite")
        brand_tagline.setObjectName("brand_tagline")

        brand_layout.addWidget(brand_name)
        brand_layout.addWidget(brand_tagline)
        layout.addWidget(brand_frame)

        # Scrollable nav area
        nav_scroll = QScrollArea()
        nav_scroll.setWidgetResizable(True)
        nav_scroll.setFrameShape(QFrame.NoFrame)
        nav_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        nav_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        nav_widget = QWidget()
        nav_layout = QVBoxLayout(nav_widget)
        nav_layout.setContentsMargins(8, 8, 8, 8)
        nav_layout.setSpacing(2)

        # Navigation groups
        nav_groups = [
            ("OVERVIEW", [
                ("Dashboard", "🏠", "dashboard"),
                ("AI Strategic Copilot", "✨", "ai_copilot"),
                ("Keyword & SEO Suite", "🔍", "keyword_research"),
            ]),
            ("CALCULATORS", [
                ("Profit Calculator", "📊", "profit_calc"),
                ("Target Pricing", "🎯", "target_price"),
                ("GST & Tax", "🧾", "gst_calc"),
                ("Advertising & ROAS", "📢", "advertising"),
                ("Shipping & Logistics", "🚚", "shipping"),
                ("Returns & RTO", "↩", "returns_rto"),
                ("Discount & Promo", "🏷", "discounts"),
                ("Bundle Calculator", "📦", "bundle_calc"),
                ("Dropshipping", "🌐", "dropshipping"),
                ("Digital Products", "💾", "digital_products"),
            ]),
            ("BUSINESS OPS", [
                ("Inventory & Reorder", "📋", "inventory"),
                ("Landed Cost", "🌏", "landed_cost"),
                ("Cash Flow", "💸", "cash_flow"),
                ("Bulk Calculator", "⚡", "bulk_calc"),
                ("Public APIs & Pipedream", "🌐", "integrations"),
            ]),
            ("MANAGEMENT", [
                ("Product Catalog", "🗂", "catalog"),
                ("Fee Profiles", "🏪", "fee_profiles"),
                ("Saved Scenarios", "💾", "scenarios"),
                ("Reports & Exports", "📑", "reports"),
                ("Software Updates", "🔄", "updater"),
                ("Settings", "⚙", "settings"),
                ("Help & Reference", "❓", "help"),
            ]),
        ]

        for group_name, items in nav_groups:
            # Group label
            group_lbl = QLabel(group_name)
            group_lbl.setObjectName("nav_group_label")
            group_lbl.setContentsMargins(12, 10, 12, 4)
            nav_layout.addWidget(group_lbl)

            for label, icon, page_key in items:
                btn = NavButton(label, icon)
                btn.page_key = page_key
                self._nav_buttons[page_key] = btn
                nav_layout.addWidget(btn)

        nav_layout.addStretch()
        nav_scroll.setWidget(nav_widget)
        layout.addWidget(nav_scroll, 1)

        # Bottom status
        bottom = QFrame()
        bottom.setStyleSheet("border-top: 1px solid #2d3248; padding: 8px;")
        bottom_layout = QVBoxLayout(bottom)
        bottom_layout.setContentsMargins(12, 8, 12, 8)
        self.version_btn = QPushButton("v1.0.0 • AI & Cloud Active 🔄")
        self.version_btn.setFlat(True)
        self.version_btn.setCursor(Qt.PointingHandCursor)
        self.version_btn.setStyleSheet("""
            QPushButton {
                color: #6366f1;
                font-size: 11px;
                font-weight: 600;
                text-align: left;
                padding: 4px 0;
                border: none;
            }
            QPushButton:hover {
                color: #818cf8;
            }
        """)
        bottom_layout.addWidget(self.version_btn)
        layout.addWidget(bottom)

    def get_buttons(self) -> dict:
        return self._nav_buttons

    def set_active(self, page_key: str):
        for key, btn in self._nav_buttons.items():
            btn.set_active(key == page_key)


class Toolbar(QFrame):
    """Top toolbar with page title and search."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("toolbar")
        self.setFrameShape(QFrame.StyledPanel)
        self.setFixedHeight(52)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(16)

        self._title = QLabel("Dashboard")
        self._title.setObjectName("page_title")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        self._title.setFont(title_font)

        # Search
        self._search = QLineEdit()
        self._search.setObjectName("search_bar")
        self._search.setPlaceholderText("🔍  Search calculators, settings...")
        self._search.setMaximumWidth(300)

        layout.addWidget(self._title)
        layout.addStretch()

        # Quick AI Button
        self._ai_btn = QPushButton("✨ AI Copilot")
        self._ai_btn.setCursor(Qt.PointingHandCursor)
        self._ai_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4f46e5, stop:1 #7c3aed);
                color: #ffffff;
                font-weight: bold;
                border: none;
                border-radius: 6px;
                padding: 6px 14px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4338ca, stop:1 #6d28d9);
            }
        """)
        layout.addWidget(self._ai_btn)

        # Quick Updates Button
        self._updates_btn = QPushButton("🔄 Updates")
        self._updates_btn.setCursor(Qt.PointingHandCursor)
        self._updates_btn.setStyleSheet("""
            QPushButton {
                background: #334155;
                color: #f8fafc;
                font-weight: 600;
                border: 1px solid #475569;
                border-radius: 6px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background: #475569;
            }
        """)
        layout.addWidget(self._updates_btn)

        layout.addWidget(self._search)

        # Theme toggle
        self._theme_btn = QPushButton("☀")
        self._theme_btn.setObjectName("secondary_btn")
        self._theme_btn.setFixedSize(36, 36)
        self._theme_btn.setToolTip("Toggle Light/Dark Theme")
        layout.addWidget(self._theme_btn)

    def set_title(self, title: str):
        self._title.setText(title)

    @property
    def theme_button(self):
        return self._theme_btn

    @property
    def search_input(self):
        return self._search

    @property
    def ai_button(self):
        return self._ai_btn

    @property
    def updates_button(self):
        return self._updates_btn


class MainWindow(QMainWindow):
    """CommerceCalc main application window."""

    PAGE_TITLES = {
        "dashboard": "Dashboard",
        "ai_copilot": "AI Strategic Copilot (Gemini 2.5 Flash)",
        "keyword_research": "E-Commerce Keyword Intelligence & SEO Suite",
        "profit_calc": "Product Profit Calculator",
        "target_price": "Target Selling Price Calculator",
        "gst_calc": "GST & Tax Breakdown",
        "advertising": "Advertising & ROAS Calculator",
        "shipping": "Shipping & Fulfillment Calculator",
        "returns_rto": "Returns & RTO Loss Calculator",
        "discounts": "Discount & Promotion Calculator",
        "bundle_calc": "Bundle & Multi-Unit Calculator",
        "dropshipping": "Dropshipping Calculator",
        "digital_products": "Digital Product Calculator",
        "inventory": "Inventory & Reorder Calculator",
        "landed_cost": "Landed Cost Calculator",
        "cash_flow": "Cash Flow & Settlement",
        "bulk_calc": "Bulk Product Calculator",
        "integrations": "E-Commerce Public APIs & Pipedream Hub",
        "catalog": "Product Catalog",
        "fee_profiles": "Marketplace Fee Profiles",
        "scenarios": "Saved Scenarios",
        "reports": "Reports & Exports",
        "updater": "Software Updates & Maintenance",
        "settings": "Settings",
        "help": "Help & Formula Reference",
    }

    def __init__(self, db_session=None):
        super().__init__()
        self.db_session = db_session
        self._current_theme = "dark"
        self._pages = {}
        self._setup_window()
        self._setup_ui()
        self._connect_signals()
        self._navigate("dashboard")

    def _setup_window(self):
        self.setWindowTitle("CommerceCalc — E-Commerce Profit & Pricing Suite")
        self.setMinimumSize(1200, 720)
        self.resize(1400, 860)
        # Center on screen
        screen = QApplication.primaryScreen().availableGeometry()
        self.move(
            (screen.width() - 1400) // 2,
            (screen.height() - 860) // 2,
        )

    def _setup_ui(self):
        self.setStyleSheet(DARK_THEME)

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Sidebar
        self._sidebar = Sidebar()
        main_layout.addWidget(self._sidebar)

        # Right side: toolbar + content
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        self._toolbar = Toolbar()
        right_layout.addWidget(self._toolbar)

        # Content area
        content_frame = QFrame()
        content_frame.setObjectName("content_area")
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        self._stack = QStackedWidget()
        content_layout.addWidget(self._stack)
        right_layout.addWidget(content_frame, 1)

        main_layout.addWidget(right, 1)

        # Status bar
        self.statusBar().showMessage("Ready — All calculations are offline and local.")
        self.statusBar().setStyleSheet(
            "background-color: #1a1d27; color: #475569; border-top: 1px solid #2d3248;"
        )

        # Register implemented pages
        self._register_pages()

    def _register_pages(self):
        """Create and register all 24 fully functional application page widgets."""
        implemented = {
            "dashboard": DashboardPage,
            "ai_copilot": AICopilotPage,
            "keyword_research": KeywordResearchPage,
            "profit_calc": ProductProfitPage,
            "target_price": TargetPricePage,
            "gst_calc": GSTCalculatorPage,
            "advertising": AdvertisingPage,
            "shipping": ShippingPage,
            "returns_rto": ReturnsRTOPage,
            "discounts": DiscountsPage,
            "bundle_calc": BundleCalcPage,
            "dropshipping": DropshippingPage,
            "digital_products": DigitalProductsPage,
            "inventory": InventoryPage,
            "landed_cost": LandedCostPage,
            "cash_flow": CashFlowPage,
            "bulk_calc": BulkCalcPage,
            "integrations": IntegrationsPage,
            "catalog": CatalogPage,
            "fee_profiles": FeeProfilesPage,
            "scenarios": ScenariosPage,
            "reports": ReportsPage,
            "updater": UpdaterPage,
            "settings": SettingsPage,
            "help": HelpPage,
        }

        for key, PageClass in implemented.items():
            page = PageClass(db_session=self.db_session)
            if key == "dashboard" and hasattr(page, "navigate_requested"):
                page.navigate_requested.connect(self._navigate)
            self._pages[key] = page
            self._stack.addWidget(page)

    def _connect_signals(self):
        for key, btn in self._sidebar.get_buttons().items():
            btn.clicked.connect(lambda checked, k=key: self._navigate(k))
        self._toolbar.theme_button.clicked.connect(self._toggle_theme)
        self._toolbar.ai_button.clicked.connect(lambda: self._navigate("ai_copilot"))
        self._toolbar.updates_button.clicked.connect(lambda: self._navigate("updater"))
        self._sidebar.version_btn.clicked.connect(lambda: self._navigate("updater"))

    def _navigate(self, page_key: str):
        if page_key not in self._pages:
            return
        page = self._pages[page_key]
        self._stack.setCurrentWidget(page)
        self._sidebar.set_active(page_key)
        title = self.PAGE_TITLES.get(page_key, page_key.replace("_", " ").title())
        self._toolbar.set_title(title)
        self.statusBar().showMessage(f"Viewing: {title}")

        # Refresh dashboard when navigating to it
        if page_key == "dashboard" and hasattr(page, "refresh"):
            page.refresh()

    def _toggle_theme(self):
        if self._current_theme == "dark":
            self.setStyleSheet(LIGHT_THEME)
            self._current_theme = "light"
            self._toolbar.theme_button.setText("🌙")
        else:
            self.setStyleSheet(DARK_THEME)
            self._current_theme = "dark"
            self._toolbar.theme_button.setText("☀")
