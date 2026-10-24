"""
Discount, Coupon, and Promotion Impact Calculator for CommerceCalc.
"""
from decimal import Decimal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QFrame,
    QPushButton, QLabel, QGridLayout, QSplitter, QComboBox
)
from PySide6.QtCore import Qt, QTimer
from ..widgets.common import (
    MoneyInput, PercentInput, MetricCard, SectionTitle, Divider,
    ResultRow, DisclaimerBox, InfoBox, make_card, fmt_inr, fmt_pct,
    FormFieldRow
)
from ...core.discounts import PromotionInputs, calculate_promotion


class DiscountsPage(QWidget):
    """Promotion and discount impact calculator."""

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
            "Model the financial impact of sales discounts, coupons, and BOGO deals. "
            "Calculates the exact volume boost required to prevent a drop in total gross profit."
        ))

        # 1. Promotion Details
        promo_card, promo_layout = make_card("🏷️ Promotion Configuration")
        self.orig_price = MoneyInput(max_val=999999.0)
        self.orig_price.setValue(999.0)
        self.orig_price.valueChanged.connect(self._trigger_calc)
        promo_layout.addWidget(FormFieldRow("Original Selling Price", self.orig_price))

        self.promo_type = QComboBox()
        self.promo_type.addItems(["Percentage Discount (%)", "Fixed Amount Off (₹)", "Coupon Discount (₹)", "Buy 1 Get 1 (BOGO)"])
        self.promo_type.currentIndexChanged.connect(self._on_type_changed)
        self.promo_type.currentIndexChanged.connect(self._trigger_calc)
        promo_layout.addWidget(FormFieldRow("Promotion Mechanism", self.promo_type))

        self.discount_val = MoneyInput(prefix="", max_val=999999.0)
        self.discount_val.setValue(20.0)
        self.discount_val.valueChanged.connect(self._trigger_calc)
        self.discount_row = FormFieldRow("Discount Value (% or ₹)", self.discount_val)
        promo_layout.addWidget(self.discount_row)

        self.seller_funded = PercentInput()
        self.seller_funded.setValue(100.0)
        self.seller_funded.valueChanged.connect(self._trigger_calc)
        promo_layout.addWidget(FormFieldRow("Seller-Funded Share %", self.seller_funded,
                                             "100% = seller pays all; 50% = platform co-funds 50%."))
        left_layout.addWidget(promo_card)

        # 2. Baseline Unit Economics
        base_card, base_layout = make_card("📈 Baseline Economics")
        self.base_cost = MoneyInput(max_val=999999.0)
        self.base_cost.setValue(380.0)
        self.base_cost.valueChanged.connect(self._trigger_calc)
        base_layout.addWidget(FormFieldRow("Product Acquisition Cost", self.base_cost))

        self.base_ops = MoneyInput(max_val=999999.0)
        self.base_ops.setValue(180.0)
        self.base_ops.valueChanged.connect(self._trigger_calc)
        base_layout.addWidget(FormFieldRow("Courier & Marketplace Fees", self.base_ops))

        self.base_units = MoneyInput(prefix="", max_val=1000000)
        self.base_units.setDecimals(0)
        self.base_units.setValue(100.0)
        self.base_units.valueChanged.connect(self._trigger_calc)
        base_layout.addWidget(FormFieldRow("Standard Monthly Volume", self.base_units))
        left_layout.addWidget(base_card)

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
        self.card_customer_pays = MetricCard("Customer Pays", "₹–", "default")
        self.card_promo_profit = MetricCard("Promo Profit / Unit", "₹–", "success")
        self.card_req_units = MetricCard("Units to Match Profit", "–", "default")
        self.card_volume_boost = MetricCard("Required Volume Boost", "–%", "default")
        metrics_grid.addWidget(self.card_customer_pays, 0, 0)
        metrics_grid.addWidget(self.card_promo_profit, 0, 1)
        metrics_grid.addWidget(self.card_req_units, 1, 0)
        metrics_grid.addWidget(self.card_volume_boost, 1, 1)
        right_layout.addLayout(metrics_grid)

        # Breakdown
        res_card, res_layout = make_card("Discount & Volume Breakdown")
        self.row_total_discount = ResultRow("Total Customer Discount", "–")
        self.row_effective_pct = ResultRow("Effective Discount %", "–")
        self.row_seller_share = ResultRow("Seller Absorbed Discount", "–", color="#f87171")
        self.row_marketplace_share = ResultRow("Marketplace Subsidized Share", "–", color="#4ade80")
        self.row_seller_revenue = ResultRow("Effective Seller Revenue Realized", "–", bold=True)
        self.row_baseline_profit = ResultRow("Normal Profit per Unit", "–")
        self.row_profit_drop = ResultRow("Profit Drop per Unit", "–", color="#f87171")
        self.row_required_sales = ResultRow("Required Sales Units for Parity", "–", bold=True, color="#4ade80")

        for r in [
            self.row_total_discount, self.row_effective_pct, self.row_seller_share, self.row_marketplace_share,
            Divider(), self.row_seller_revenue, self.row_baseline_profit, self.row_profit_drop,
            Divider(), self.row_required_sales
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

    def _on_type_changed(self, idx):
        if idx == 0:
            self.discount_val.setPrefix("")
            self.discount_val.setValue(20.0)
        elif idx in (1, 2):
            self.discount_val.setPrefix("₹ ")
            self.discount_val.setValue(150.0)
        elif idx == 3:
            self.discount_val.setPrefix("")
            self.discount_val.setValue(50.0)  # BOGO 50% eff

    def _trigger_calc(self):
        self._calc_timer.start()

    def _calculate(self):
        try:
            type_keys = ["percentage", "fixed", "coupon", "bogo"]
            sel_type = type_keys[self.promo_type.currentIndex()]

            inputs = PromotionInputs(
                original_price=self.orig_price.get_decimal(),
                promo_type=sel_type,
                discount_value=self.discount_val.get_decimal(),
                coupon_amount=self.discount_val.get_decimal(),
                seller_funded_pct=self.seller_funded.get_decimal(),
                baseline_units_sold=max(int(self.base_units.value()), 1),
                baseline_unit_cost=self.base_cost.get_decimal(),
                baseline_shipping_and_fees=self.base_ops.get_decimal(),
            )
            res = calculate_promotion(inputs)

            self.card_customer_pays.update_value(fmt_inr(res.customer_pays))
            p_type = "success" if res.promo_profit_per_unit > 0 else "danger"
            self.card_promo_profit.update_value(fmt_inr(res.promo_profit_per_unit, show_sign=True), p_type)
            self.card_req_units.update_value(f"{res.required_units_for_same_profit} units")
            self.card_volume_boost.update_value(f"+{res.incremental_orders_needed_pct:.1f}%")

            self.row_total_discount.set_value(fmt_inr(res.total_customer_discount))
            self.row_effective_pct.set_value(fmt_pct(res.effective_discount_pct))
            self.row_seller_share.set_value(f"− {fmt_inr(res.seller_discount_share)}", "#f87171")
            self.row_marketplace_share.set_value(f"+ {fmt_inr(res.marketplace_discount_share)}", "#4ade80")
            self.row_seller_revenue.set_value(fmt_inr(res.adjusted_seller_revenue))
            self.row_baseline_profit.set_value(fmt_inr(res.baseline_profit_per_unit))
            self.row_profit_drop.set_value(f"− {fmt_inr(res.profit_reduction_per_unit)}", "#f87171")
            self.row_required_sales.set_value(f"{res.required_units_for_same_profit} units (vs {inputs.baseline_units_sold})", "#4ade80")

            if res.warnings:
                self.warnings_label.setText("⚠ " + " | ".join(res.warnings))
            else:
                self.warnings_label.setText("")
        except Exception as e:
            self.warnings_label.setText(f"Error: {str(e)}")
