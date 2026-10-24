"""
Digital Products, Ebooks, Courses, and Software Calculator Page for CommerceCalc.
"""
from decimal import Decimal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QFrame,
    QPushButton, QLabel, QGridLayout, QSplitter
)
from PySide6.QtCore import Qt, QTimer
from ..widgets.common import (
    MoneyInput, PercentInput, MetricCard, SectionTitle, Divider,
    ResultRow, InfoBox, make_card, fmt_inr, fmt_pct, FormFieldRow
)
from ...core.digital import DigitalProductInputs, calculate_digital_product


class DigitalProductsPage(QWidget):
    """Digital goods, courses, and software profit calculator."""

    def __init__(self, db_session=None, parent=None):
        super().__init__(parent)
        self.db_session = db_session
        self._calc_timer = QTimer()
        self._calc_timer.setSingleShot(True)
        self._calc_timer.setInterval(300)
        self._calc_timer.timeout.connect(self._calculate)
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        splitter = QSplitter(Qt.Horizontal)

        # Left inputs panel
        left_widget = QWidget()
        left_scroll = QScrollArea()
        left_scroll.setWidgetResizable(True)
        left_scroll.setWidget(left_widget)
        left_scroll.setFrameShape(QFrame.NoFrame)
        left_scroll.setMinimumWidth(480)
        left_scroll.setMaximumWidth(540)

        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(20, 16, 20, 20)
        left_layout.setSpacing(16)

        left_layout.addWidget(InfoBox(
            "Designed for digital products with zero physical delivery costs. "
            "Amortizes upfront production/development costs across target unit sales."
        ))

        # 1. Product & Volume
        prod_card, prod_layout = make_card("💻 Pricing & Volume Forecast")
        self.selling_price = MoneyInput(max_val=999999.0)
        self.selling_price.setValue(999.0)
        self.selling_price.valueChanged.connect(self._trigger_calc)
        prod_layout.addWidget(FormFieldRow("Selling Price (₹)", self.selling_price))

        self.target_units = MoneyInput(prefix="", max_val=1000000)
        self.target_units.setDecimals(0)
        self.target_units.setValue(150.0)
        self.target_units.valueChanged.connect(self._trigger_calc)
        prod_layout.addWidget(FormFieldRow("Target Lifetime Sales Units", self.target_units))
        left_layout.addWidget(prod_card)

        # 2. Upfront Development Costs
        dev_card, dev_layout = make_card("🏗️ Upfront Creation & Licensing")
        self.creation_cost = MoneyInput(max_val=9999999.0)
        self.creation_cost.setValue(25000.0)
        self.creation_cost.valueChanged.connect(self._trigger_calc)
        dev_layout.addWidget(FormFieldRow("Content / Software Dev Cost", self.creation_cost))

        self.assets_cost = MoneyInput(max_val=9999999.0)
        self.assets_cost.setValue(5000.0)
        self.assets_cost.valueChanged.connect(self._trigger_calc)
        dev_layout.addWidget(FormFieldRow("Asset Licensing / Fonts / Audio", self.assets_cost))
        left_layout.addWidget(dev_card)

        # 3. Variable Fees & Bandwidth
        var_card, var_layout = make_card("⚡ Variable Platform & Delivery Fees")
        self.hosting_per_unit = MoneyInput(max_val=999.0)
        self.hosting_per_unit.setValue(10.0)
        self.hosting_per_unit.valueChanged.connect(self._trigger_calc)
        var_layout.addWidget(FormFieldRow("Bandwidth / Serverless Delivery", self.hosting_per_unit))

        self.platform_fee_pct = PercentInput()
        self.platform_fee_pct.setValue(5.0)  # Gumroad / Teachable
        self.platform_fee_pct.valueChanged.connect(self._trigger_calc)
        var_layout.addWidget(FormFieldRow("Store Platform Fee %", self.platform_fee_pct))

        self.pg_pct = PercentInput()
        self.pg_pct.setValue(2.0)
        self.pg_pct.valueChanged.connect(self._trigger_calc)
        var_layout.addWidget(FormFieldRow("Payment Gateway Fee %", self.pg_pct))

        self.affiliate_pct = PercentInput()
        self.affiliate_pct.setValue(10.0)
        self.affiliate_pct.valueChanged.connect(self._trigger_calc)
        var_layout.addWidget(FormFieldRow("Affiliate Commission %", self.affiliate_pct))

        self.refund_pct = PercentInput()
        self.refund_pct.setValue(3.0)
        self.refund_pct.valueChanged.connect(self._trigger_calc)
        var_layout.addWidget(FormFieldRow("Expected Refund Rate %", self.refund_pct))
        left_layout.addWidget(var_card)

        left_layout.addStretch()

        # Right results panel
        right_widget = QWidget()
        right_scroll = QScrollArea()
        right_scroll.setWidgetResizable(True)
        right_scroll.setWidget(right_widget)
        right_scroll.setFrameShape(QFrame.NoFrame)

        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(20, 16, 20, 20)
        right_layout.setSpacing(16)

        # Metrics
        metrics_grid = QGridLayout()
        metrics_grid.setSpacing(12)
        self.card_net_profit_unit = MetricCard("Net Profit / Unit", "₹–", "success")
        self.card_total_projected = MetricCard("Total Projected Net Profit", "₹–", "success")
        self.card_be_units = MetricCard("Break-Even Units", "–", "default")
        self.card_margin = MetricCard("Contribution Margin", "–%", "default")
        metrics_grid.addWidget(self.card_net_profit_unit, 0, 0)
        metrics_grid.addWidget(self.card_total_projected, 0, 1)
        metrics_grid.addWidget(self.card_be_units, 1, 0)
        metrics_grid.addWidget(self.card_margin, 1, 1)
        right_layout.addLayout(metrics_grid)

        # Breakdown
        res_card, res_layout = make_card("Digital Unit Economics & Amortization")
        self.row_selling_price = ResultRow("Selling Price", "–")
        self.row_net_revenue = ResultRow("Net Revenue after Refund Reserve", "–")
        self.row_variable_cost = ResultRow("Platform, PG & Bandwidth Delivery", "–", color="#f87171")
        self.row_contrib_profit = ResultRow("Unit Contribution Profit", "–", bold=True)
        self.row_total_upfront = ResultRow("Total Upfront Development Outlay", "–")
        self.row_amortized = ResultRow("Amortized Cost per Target Unit", "–")
        self.row_net_profit_unit = ResultRow("Net Accounting Profit per Unit", "–", bold=True, color="#4ade80")
        self.row_be_units = ResultRow("Sales Units Needed to Break Even", "–", bold=True)
        self.row_be_price = ResultRow("Break-Even Price at Planned Volume", "–")

        for r in [
            self.row_selling_price, self.row_net_revenue, self.row_variable_cost,
            self.row_contrib_profit, Divider(),
            self.row_total_upfront, self.row_amortized, Divider(),
            self.row_net_profit_unit, self.row_be_units, self.row_be_price
        ]:
            res_layout.addWidget(r)
        right_layout.addWidget(res_card)

        self.warnings_label = QLabel()
        self.warnings_label.setWordWrap(True)
        self.warnings_label.setStyleSheet("color: #fb923c; font-size: 12px;")
        right_layout.addWidget(self.warnings_label)
        right_layout.addStretch()

        splitter.addWidget(left_scroll)
        splitter.addWidget(right_scroll)
        splitter.setSizes([500, 580])
        main_layout.addWidget(splitter)

        self._calculate()

    def _trigger_calc(self):
        self._calc_timer.start()

    def _calculate(self):
        try:
            inputs = DigitalProductInputs(
                selling_price=self.selling_price.get_decimal(),
                expected_sales_units=max(int(self.target_units.value()), 1),
                creation_cost=self.creation_cost.get_decimal(),
                assets_licensing_cost=self.assets_cost.get_decimal(),
                hosting_delivery_per_unit=self.hosting_per_unit.get_decimal(),
                platform_fee_pct=self.platform_fee_pct.get_decimal(),
                payment_gateway_pct=self.pg_pct.get_decimal(),
                affiliate_commission_pct=self.affiliate_pct.get_decimal(),
                refund_rate_pct=self.refund_pct.get_decimal(),
            )
            res = calculate_digital_product(inputs)

            p_type = "success" if res.net_profit_per_unit > 0 else "danger"
            self.card_net_profit_unit.update_value(fmt_inr(res.net_profit_per_unit, show_sign=True), p_type)
            self.card_total_projected.update_value(fmt_inr(res.total_projected_net_profit, show_sign=True), p_type)
            self.card_be_units.update_value(f"{res.units_needed_to_break_even} sales")
            self.card_margin.update_value(fmt_pct(res.contribution_margin_pct))

            self.row_selling_price.set_value(fmt_inr(res.selling_price))
            self.row_net_revenue.set_value(fmt_inr(res.net_revenue_per_unit))
            self.row_variable_cost.set_value(f"− {fmt_inr(res.variable_cost_per_unit)}", "#f87171")
            self.row_contrib_profit.set_value(fmt_inr(res.contribution_profit_per_unit))
            self.row_total_upfront.set_value(fmt_inr(res.total_upfront_cost))
            self.row_amortized.set_value(fmt_inr(res.amortized_cost_per_unit))
            self.row_net_profit_unit.set_value(fmt_inr(res.net_profit_per_unit, show_sign=True), "#4ade80" if res.net_profit_per_unit > 0 else "#f87171")
            self.row_be_units.set_value(f"{res.units_needed_to_break_even} units (at current price)", "#4ade80")
            self.row_be_price.set_value(fmt_inr(res.break_even_selling_price))

            if res.warnings:
                self.warnings_label.setText("⚠ " + " | ".join(res.warnings))
            else:
                self.warnings_label.setText("")
        except Exception as e:
            self.warnings_label.setText(f"Error: {str(e)}")
