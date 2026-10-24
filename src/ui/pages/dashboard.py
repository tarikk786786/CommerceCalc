"""
Dashboard page for CommerceCalc.
Shows aggregated metrics from saved products and scenarios.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QGridLayout,
    QPushButton, QScrollArea
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from ..widgets.common import MetricCard, SectionTitle, make_card, InfoBox


class DashboardPage(QWidget):
    """Main dashboard with product metrics and quick actions."""
    navigate_requested = Signal(str)

    def __init__(self, db_session=None, parent=None):
        super().__init__(parent)
        self.db_session = db_session
        self._setup_ui()

    def _setup_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(24, 20, 24, 24)
        layout.setSpacing(20)

        # Welcome header
        self._build_welcome(layout)
        # Quick actions
        self._build_quick_actions(layout)
        # Metrics
        self._build_metrics(layout)
        # Getting started
        self._build_getting_started(layout)

        layout.addStretch()
        scroll.setWidget(content)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)

    def _build_welcome(self, layout):
        card, cl = make_card()

        title = QLabel("Welcome to CommerceCalc")
        title_font = QFont()
        title_font.setPointSize(20)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setObjectName("section_title")

        subtitle = QLabel("All-in-One E-Commerce Profit, Pricing & Keyword SEO Suite")
        subtitle.setObjectName("metric_label")

        cl.addWidget(title)
        cl.addWidget(subtitle)
        cl.addWidget(InfoBox(
            "Start by calculating profit for a product using the Product Profit Calculator, "
            "or set up your marketplace fee profiles in the Fee Profiles section."
        ))
        layout.addWidget(card)

    def _build_quick_actions(self, layout):
        card, cl = make_card("⚡ Quick Actions")

        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)

        actions = [
            ("📊 Calculate Profit", "Calculate product profitability", "primary_btn", "profit_calc"),
            ("🎯 Find Target Price", "Set a price to hit your margin", "secondary_btn", "target_price"),
            ("🏪 Fee Profiles", "Configure marketplace fees", "secondary_btn", "fee_profiles"),
            ("📈 Import Bulk", "Calculate 100s of products", "secondary_btn", "bulk_calc"),
        ]

        for label, tip, btn_type, target_page in actions:
            btn = QPushButton(label)
            btn.setObjectName(btn_type)
            btn.setToolTip(tip)
            btn.setMinimumHeight(48)
            btn.clicked.connect(lambda checked, p=target_page: self.navigate_requested.emit(p))
            btn_row.addWidget(btn)

        cl.addLayout(btn_row)
        layout.addWidget(card)

    def _build_metrics(self, layout):
        card, cl = make_card("📊 Portfolio Overview")
        cl.addWidget(InfoBox(
            "Save products and scenarios to see portfolio metrics here. "
            "Metrics appear when you have calculated and saved at least one product."
        ))

        grid = QGridLayout()
        grid.setSpacing(12)

        placeholders = [
            ("Products Saved", "–", "default"),
            ("Profitable Products", "–", "default"),
            ("Avg Contribution Margin", "–", "default"),
            ("Products Below Target", "–", "default"),
        ]
        for i, (label, val, ctype) in enumerate(placeholders):
            card_widget = MetricCard(label, val, ctype)
            grid.addWidget(card_widget, i // 2, i % 2)

        cl.addLayout(grid)
        layout.addWidget(card)

    def _build_getting_started(self, layout):
        card, cl = make_card("🚀 Getting Started")

        steps = [
            ("1", "Set Up Fee Profiles",
             "Go to Marketplace Fee Profiles and configure the platforms you sell on. "
             "Enter verified rates from your seller portal."),
            ("2", "Calculate Your First Product",
             "Use the Product Profit Calculator to enter costs and selling details. "
             "Get a full breakdown of revenue, expenses, and profit."),
            ("3", "Find Your Target Price",
             "Use the Target Selling Price Calculator to solve for the price that hits "
             "your desired margin or profit goal."),
            ("4", "Analyze Returns & Advertising",
             "Model expected losses from returns/RTO and evaluate your ad spend "
             "efficiency with the advertising calculator."),
        ]

        for num, title, desc in steps:
            step_frame = QFrame()
            step_frame.setObjectName("card")
            step_layout = QHBoxLayout(step_frame)
            step_layout.setContentsMargins(16, 12, 16, 12)
            step_layout.setSpacing(16)

            num_lbl = QLabel(num)
            num_lbl.setFixedSize(32, 32)
            num_lbl.setAlignment(Qt.AlignCenter)
            num_lbl.setStyleSheet(
                "background-color: #312e81; color: #a5b4fc; "
                "border-radius: 16px; font-weight: bold; font-size: 14px;"
            )

            text_layout = QVBoxLayout()
            text_layout.setSpacing(4)
            title_lbl = QLabel(title)
            title_lbl.setStyleSheet("font-weight: bold; color: #e2e8f0; font-size: 13px;")
            desc_lbl = QLabel(desc)
            desc_lbl.setWordWrap(True)
            desc_lbl.setStyleSheet("color: #64748b; font-size: 12px;")
            text_layout.addWidget(title_lbl)
            text_layout.addWidget(desc_lbl)

            step_layout.addWidget(num_lbl)
            step_layout.addLayout(text_layout, 1)
            cl.addWidget(step_frame)

        layout.addWidget(card)

    def refresh(self):
        """Refresh metrics from database."""
        if self.db_session:
            try:
                from ...db.models import Scenario, Product
                # Update counts from DB when implemented
                pass
            except Exception:
                pass
