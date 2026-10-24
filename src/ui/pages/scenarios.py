"""
Scenario Comparison Page for CommerceCalc.
"""
from decimal import Decimal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QFrame,
    QPushButton, QLabel, QGridLayout, QTableWidget, QTableWidgetItem, QHeaderView
)
from PySide6.QtCore import Qt
from ..widgets.common import (
    MetricCard, make_card, fmt_inr, fmt_pct, InfoBox
)
from ...core.profit import ProductCost, SellingDetails, SellingExpenses, calculate_profit
from ...core.tax import GSTConfig


class ScenariosPage(QWidget):
    """Multi-channel & multi-pricing scenario comparison."""

    def __init__(self, db_session=None, parent=None):
        super().__init__(parent)
        self.db_session = db_session
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 24)
        layout.setSpacing(16)

        header_card, h_layout = make_card()
        h_layout.addWidget(QLabel("Multi-Channel Scenario Comparison"))
        h_layout.addWidget(InfoBox(
            "Side-by-side comparison of selling the exact same product across channels: "
            "Amazon India vs Flipkart vs Direct Shopify D2C Website."
        ))
        layout.addWidget(header_card)

        # Build 3 scenarios:
        # Common Product: Cost = 350 INR, Selling Price = 999 INR
        # Scenario 1: Amazon (15% MP fee = 150, 70 shipping, 20 closing = 240 fee, 50 ad)
        # Scenario 2: Flipkart (12% MP fee = 120, 65 shipping, 15 closing = 200 fee, 40 ad)
        # Scenario 3: Shopify (2% PG = 20, 60 shipping, 0 closing, 250 ad CAC)

        scenarios = [
            ("Amazon India (FBA / EasyShip)", Decimal("999"), Decimal("350"), Decimal("150"), Decimal("70"), Decimal("20"), Decimal("50")),
            ("Flipkart (Assured)", Decimal("999"), Decimal("350"), Decimal("120"), Decimal("65"), Decimal("15"), Decimal("40")),
            ("Direct D2C Website (Shopify + Meta Ads)", Decimal("999"), Decimal("350"), Decimal("20"), Decimal("60"), Decimal("0"), Decimal("220")),
        ]

        results = []
        for name, sp, cost, mp_fee, ship, closing, ad in scenarios:
            pc = ProductCost(purchase_cost=cost)
            sd = SellingDetails(actual_selling_price=sp, quantity=1, gst_config=GSTConfig(rate_pct=Decimal("18")))
            se = SellingExpenses(
                marketplace_commission=mp_fee,
                forward_shipping=ship,
                closing_fee=closing,
                advertising_cost=ad
            )
            r = calculate_profit(pc, sd, se)
            results.append((name, r, ad))

        # Comparison Grid Cards
        cards_grid = QGridLayout()
        cards_grid.setSpacing(12)
        for i, (name, res, ad) in enumerate(results):
            card = QFrame()
            card.setObjectName("card")
            c_lay = QVBoxLayout(card)
            c_lay.setContentsMargins(16, 14, 16, 14)
            c_lay.setSpacing(8)

            t_lbl = QLabel(name)
            t_lbl.setStyleSheet("font-weight: bold; color: #a5b4fc; font-size: 13px;")
            p_lbl = QLabel(f"Net Profit: {fmt_inr(res.estimated_operating_profit, show_sign=True)}")
            p_lbl.setStyleSheet("font-size: 18px; font-weight: bold; color: #4ade80;")
            m_lbl = QLabel(f"Margin: {fmt_pct(res.contribution_margin_pct)} | Markup: {fmt_pct(res.markup_on_cost_pct)}")
            m_lbl.setStyleSheet("color: #94a3b8; font-size: 11px;")

            c_lay.addWidget(t_lbl)
            c_lay.addWidget(p_lbl)
            c_lay.addWidget(m_lbl)
            cards_grid.addWidget(card, 0, i)

        layout.addLayout(cards_grid)

        # Full Table Comparison
        self.table = QTableWidget(9, 4)
        self.table.setHorizontalHeaderLabels(["Financial Metric", "Amazon India", "Flipkart", "Shopify D2C"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        for c in [1, 2, 3]:
            self.table.horizontalHeader().setSectionResizeMode(c, QHeaderView.Stretch)

        rows = [
            ("Customer Price (incl. GST)", [fmt_inr(r.gross_list_value) for _, r, _ in results]),
            ("Net Taxable Revenue", [fmt_inr(r.net_revenue) for _, r, _ in results]),
            ("Goods Acquisition Cost (COGS)", [fmt_inr(r.total_acquisition_cost) for _, r, _ in results]),
            ("Courier & Logistics Delivery", [fmt_inr(r.total_fulfillment_cost) for _, r, _ in results]),
            ("Marketplace Commission & Closing", [fmt_inr(r.total_marketplace_fees) for _, r, _ in results]),
            ("Ad Spend / Customer Acquisition (CAC)", [fmt_inr(ad) for _, _, ad in results]),
            ("Net Contribution Profit", [fmt_inr(r.estimated_operating_profit, show_sign=True) for _, r, _ in results]),
            ("Contribution Margin %", [fmt_pct(r.contribution_margin_pct) for _, r, _ in results]),
            ("Outcome Verdict", ["Solid Volume" if i == 0 else "High Efficiency" if i == 1 else "Highest Margin" for i in range(3)]),
        ]

        for row_idx, (metric_name, vals) in enumerate(rows):
            self.table.setItem(row_idx, 0, QTableWidgetItem(metric_name))
            for col_idx, val in enumerate(vals):
                it = QTableWidgetItem(val)
                if "Net Contribution Profit" in metric_name:
                    it.setForeground(Qt.green)
                self.table.setItem(row_idx, col_idx + 1, it)

        layout.addWidget(self.table, 1)
