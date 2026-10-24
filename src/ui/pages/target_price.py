"""
Target Selling Price Calculator page.

Solves for selling price given cost structure and profit targets.
"""
from decimal import Decimal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QFrame,
    QPushButton, QLabel, QComboBox, QGridLayout, QSplitter,
    QCheckBox, QLineEdit
)
from PySide6.QtCore import Qt, QTimer
from ..widgets.common import (
    MoneyInput, PercentInput, MetricCard, SectionTitle, Divider,
    ResultRow, DisclaimerBox, InfoBox, make_card, fmt_inr, fmt_pct,
    FormFieldRow
)
from ...core.pricing import PriceSolverInputs, PriceSolverTarget, solve_target_price


class TargetPricePage(QWidget):
    """Target selling price calculator."""

    def __init__(self, db_session=None, parent=None):
        super().__init__(parent)
        self.db_session = db_session
        self._calc_timer = QTimer()
        self._calc_timer.setSingleShot(True)
        self._calc_timer.setInterval(400)
        self._calc_timer.timeout.connect(self._calculate)
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        splitter = QSplitter(Qt.Horizontal)

        # Left: inputs
        left_widget = QWidget()
        left_scroll = QScrollArea()
        left_scroll.setWidgetResizable(True)
        left_scroll.setWidget(left_widget)
        left_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        left_scroll.setFrameShape(QFrame.NoFrame)
        left_scroll.setMinimumWidth(480)
        left_scroll.setMaximumWidth(540)

        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(20, 16, 20, 20)
        left_layout.setSpacing(16)

        self._build_cost_inputs(left_layout)
        self._build_fee_inputs(left_layout)
        self._build_target_inputs(left_layout)

        calc_btn = QPushButton("Calculate Target Price")
        calc_btn.setObjectName("primary_btn")
        calc_btn.setMinimumHeight(44)
        calc_btn.clicked.connect(self._calculate)
        left_layout.addWidget(calc_btn)
        left_layout.addStretch()

        # Right: results
        right_widget = QWidget()
        right_scroll = QScrollArea()
        right_scroll.setWidgetResizable(True)
        right_scroll.setWidget(right_widget)
        right_scroll.setFrameShape(QFrame.NoFrame)

        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(20, 16, 20, 20)
        right_layout.setSpacing(16)
        self._build_results(right_layout)

        splitter.addWidget(left_scroll)
        splitter.addWidget(right_scroll)
        splitter.setSizes([500, 580])
        main_layout.addWidget(splitter)

    def _build_cost_inputs(self, layout):
        card, cl = make_card("💰 Fixed Costs Per Unit")

        cl.addWidget(InfoBox(
            "Enter all costs that don't change with selling price. "
            "Percentage-based fees go in the Fee Structure section."
        ))

        self.product_cost = MoneyInput()
        self.product_cost.valueChanged.connect(self._trigger_calc)
        cl.addWidget(FormFieldRow("Product Cost", self.product_cost))

        self.packaging_cost = MoneyInput()
        self.packaging_cost.valueChanged.connect(self._trigger_calc)
        cl.addWidget(FormFieldRow("Packaging Cost", self.packaging_cost))

        self.fulfillment_cost = MoneyInput()
        self.fulfillment_cost.valueChanged.connect(self._trigger_calc)
        cl.addWidget(FormFieldRow("Fulfillment / Shipping", self.fulfillment_cost))

        self.fixed_mp_fee = MoneyInput()
        self.fixed_mp_fee.valueChanged.connect(self._trigger_calc)
        cl.addWidget(FormFieldRow("Fixed Marketplace Fee", self.fixed_mp_fee))

        self.fixed_adv_cost = MoneyInput()
        self.fixed_adv_cost.valueChanged.connect(self._trigger_calc)
        cl.addWidget(FormFieldRow("Fixed Advertising Cost", self.fixed_adv_cost))

        self.fixed_return_cost = MoneyInput()
        self.fixed_return_cost.valueChanged.connect(self._trigger_calc)
        cl.addWidget(FormFieldRow("Expected Return/RTO Cost", self.fixed_return_cost))

        self.overhead_cost = MoneyInput()
        self.overhead_cost.valueChanged.connect(self._trigger_calc)
        cl.addWidget(FormFieldRow("Overhead Allocated", self.overhead_cost))

        self.quantity = MoneyInput(prefix="× ", max_val=100000)
        self.quantity.setValue(1)
        self.quantity.valueChanged.connect(self._trigger_calc)
        cl.addWidget(FormFieldRow("Expected Quantity", self.quantity))

        layout.addWidget(card)

    def _build_fee_inputs(self, layout):
        card, cl = make_card("📊 Variable Fee Structure (% of Selling Price)")

        cl.addWidget(InfoBox(
            "These percentage fees are deducted from selling price. "
            "The solver accounts for these when calculating the target price."
        ))

        self.mp_commission_pct = PercentInput()
        self.mp_commission_pct.valueChanged.connect(self._trigger_calc)
        cl.addWidget(FormFieldRow("Marketplace Commission %", self.mp_commission_pct))

        self.payment_gw_pct = PercentInput()
        self.payment_gw_pct.valueChanged.connect(self._trigger_calc)
        cl.addWidget(FormFieldRow("Payment Gateway %", self.payment_gw_pct))

        self.affiliate_pct = PercentInput()
        self.affiliate_pct.valueChanged.connect(self._trigger_calc)
        cl.addWidget(FormFieldRow("Affiliate Commission %", self.affiliate_pct))

        self.adv_pct = PercentInput()
        self.adv_pct.valueChanged.connect(self._trigger_calc)
        cl.addWidget(FormFieldRow("Advertising (% of Revenue)", self.adv_pct))

        self.discount_pct = PercentInput()
        self.discount_pct.valueChanged.connect(self._trigger_calc)
        cl.addWidget(FormFieldRow("Seller Discount %", self.discount_pct))

        self.gst_rate = PercentInput(max_val=28.0)
        self.gst_rate.valueChanged.connect(self._trigger_calc)
        cl.addWidget(FormFieldRow("GST Rate %", self.gst_rate,
                                   "Tax on top of price. 0 = not applicable"))

        layout.addWidget(card)

    def _build_target_inputs(self, layout):
        card, cl = make_card("🎯 Profit Target")

        self.objective = QComboBox()
        self.objective.addItems([
            "Break-Even Price",
            "Target Profit (₹ per unit)",
            "Target Margin (%)",
            "Target Markup (%)",
        ])
        self.objective.currentIndexChanged.connect(self._on_objective_changed)
        self.objective.currentIndexChanged.connect(self._trigger_calc)
        cl.addWidget(FormFieldRow("Pricing Objective", self.objective))

        self.target_profit = MoneyInput()
        self.target_profit.valueChanged.connect(self._trigger_calc)
        self.target_profit_row = FormFieldRow("Target Profit per Unit", self.target_profit)
        cl.addWidget(self.target_profit_row)

        self.target_margin = PercentInput()
        self.target_margin.valueChanged.connect(self._trigger_calc)
        self.target_margin_row = FormFieldRow("Target Margin %", self.target_margin)
        cl.addWidget(self.target_margin_row)

        self.target_markup = PercentInput(max_val=1000.0)
        self.target_markup.valueChanged.connect(self._trigger_calc)
        self.target_markup_row = FormFieldRow("Target Markup %", self.target_markup)
        cl.addWidget(self.target_markup_row)

        cl.addWidget(Divider())

        self.rounding_method = QComboBox()
        self.rounding_method.addItems([
            "Nearest Rupee", "Round Up", "End in ₹9", "End in ₹49", "End in ₹99"
        ])
        self.rounding_method.setCurrentIndex(4)
        self.rounding_method.currentIndexChanged.connect(self._trigger_calc)
        cl.addWidget(FormFieldRow("Price Rounding", self.rounding_method))

        self._on_objective_changed(0)
        layout.addWidget(card)

    def _on_objective_changed(self, idx):
        # Show/hide relevant target inputs
        obj_map = {0: "break_even", 1: "target_profit", 2: "target_margin", 3: "target_markup"}
        obj = obj_map.get(idx, "break_even")
        self.target_profit_row.setVisible(obj == "target_profit")
        self.target_margin_row.setVisible(obj == "target_margin")
        self.target_markup_row.setVisible(obj == "target_markup")

    def _build_results(self, layout):
        self.infeasibility_label = QLabel()
        self.infeasibility_label.setWordWrap(True)
        self.infeasibility_label.setStyleSheet("color: #f87171; font-size: 13px; padding: 8px;")
        self.infeasibility_label.setVisible(False)
        layout.addWidget(self.infeasibility_label)

        metrics_layout = QGridLayout()
        metrics_layout.setSpacing(12)
        self.card_breakeven = MetricCard("Break-Even Price", "₹–")
        self.card_target = MetricCard("Recommended Price", "₹–", "success")
        self.card_incl_gst = MetricCard("Price incl. GST", "₹–")
        self.card_contribution = MetricCard("Contribution Profit/Unit", "₹–")
        metrics_layout.addWidget(self.card_breakeven, 0, 0)
        metrics_layout.addWidget(self.card_target, 0, 1)
        metrics_layout.addWidget(self.card_incl_gst, 1, 0)
        metrics_layout.addWidget(self.card_contribution, 1, 1)
        layout.addLayout(metrics_layout)

        price_card, price_layout = make_card("Price Analysis")
        self.row_taxable = ResultRow("Taxable Selling Price", "–")
        self.row_gst = ResultRow("GST Component", "–")
        self.row_customer_price = ResultRow("Customer-Facing Price", "–", bold=True)
        self.row_breakeven = ResultRow("Break-Even Price", "–")
        self.row_max_discount = ResultRow("Max Safe Discount", "–")
        self.row_total_profit_qty = ResultRow("Total Profit at Quantity", "–", bold=True, color="#4ade80")
        self.row_max_adv = ResultRow("Max Tolerable Ad Cost", "–")
        for r in [self.row_taxable, self.row_gst, self.row_customer_price,
                  Divider(), self.row_breakeven, self.row_max_discount,
                  self.row_total_profit_qty, self.row_max_adv]:
            price_layout.addWidget(r)
        layout.addWidget(price_card)

        # Sensitivity card
        sens_card, sens_layout = make_card("Sensitivity Analysis")
        self.sensitivity_label = QLabel("–")
        self.sensitivity_label.setWordWrap(True)
        self.sensitivity_label.setStyleSheet("color: #94a3b8; font-size: 12px;")
        sens_layout.addWidget(self.sensitivity_label)
        layout.addWidget(sens_card)

        # Formula explanation
        formula_card, formula_layout = make_card("Formula Explanation")
        self.formula_label = QLabel("–")
        self.formula_label.setWordWrap(True)
        self.formula_label.setStyleSheet("font-family: monospace; font-size: 11px; color: #94a3b8;")
        formula_layout.addWidget(self.formula_label)
        layout.addWidget(formula_card)

        layout.addStretch()

    def _trigger_calc(self):
        self._calc_timer.start()

    def _calculate(self):
        try:
            obj_map = {0: "break_even", 1: "target_profit", 2: "target_margin", 3: "target_markup"}
            rounding_map = {0: "nearest", 1: "up", 2: "end_9", 3: "end_49", 4: "end_99"}

            inputs = PriceSolverInputs(
                product_cost=self.product_cost.get_decimal(),
                packaging_cost=self.packaging_cost.get_decimal(),
                fixed_fulfillment_cost=self.fulfillment_cost.get_decimal(),
                fixed_marketplace_fee=self.fixed_mp_fee.get_decimal(),
                fixed_advertising_cost=self.fixed_adv_cost.get_decimal(),
                fixed_return_rto_cost=self.fixed_return_cost.get_decimal(),
                fixed_overhead=self.overhead_cost.get_decimal(),
                marketplace_commission_pct=self.mp_commission_pct.get_decimal(),
                payment_gateway_pct=self.payment_gw_pct.get_decimal(),
                affiliate_pct=self.affiliate_pct.get_decimal(),
                advertising_pct=self.adv_pct.get_decimal(),
                seller_funded_discount_pct=self.discount_pct.get_decimal(),
                gst_rate_pct=self.gst_rate.get_decimal(),
                quantity=max(int(self.quantity.value()), 1),
            )

            obj_idx = self.objective.currentIndex()
            target = PriceSolverTarget(
                objective=obj_map[obj_idx],
                target_profit_per_unit=self.target_profit.get_decimal(),
                target_margin_pct=self.target_margin.get_decimal(),
                target_markup_pct=self.target_markup.get_decimal(),
                price_rounding_method=rounding_map.get(self.rounding_method.currentIndex(), "end_99"),
                price_rounding_ending="99",
            )

            result = solve_target_price(inputs, target)
            self._update_results(result)
        except Exception as e:
            self.infeasibility_label.setText(f"Calculation error: {str(e)}")
            self.infeasibility_label.setVisible(True)

    def _update_results(self, result):
        if not result.is_feasible:
            self.infeasibility_label.setText(
                f"⚠ No valid price exists: {result.infeasibility_reason}"
            )
            self.infeasibility_label.setVisible(True)
            return

        self.infeasibility_label.setVisible(False)

        self.card_breakeven.update_value(fmt_inr(result.break_even_price))
        self.card_target.update_value(fmt_inr(result.recommended_price))
        self.card_incl_gst.update_value(fmt_inr(result.recommended_price_incl_gst))
        self.card_contribution.update_value(
            fmt_inr(result.contribution_profit_per_unit, show_sign=True),
            "success" if result.contribution_profit_per_unit >= 0 else "danger"
        )

        self.row_taxable.set_value(fmt_inr(result.taxable_value))
        gst_component = result.recommended_price_incl_gst - result.taxable_value
        self.row_gst.set_value(fmt_inr(gst_component))
        self.row_customer_price.set_value(fmt_inr(result.recommended_price_incl_gst))
        self.row_breakeven.set_value(fmt_inr(result.break_even_price))
        self.row_max_discount.set_value(fmt_inr(result.max_discount_before_breakeven))
        self.row_total_profit_qty.set_value(fmt_inr(result.total_profit_at_quantity))
        self.row_max_adv.set_value(fmt_inr(result.max_tolerable_adv_cost))

        # Sensitivity
        if result.sensitivity:
            sens_text = "\n".join(f"• {k}: {v}" for k, v in result.sensitivity.items())
        else:
            sens_text = "Not enough data for sensitivity analysis."
        self.sensitivity_label.setText(sens_text)

        # Formula
        self.formula_label.setText(result.formula_explanation or "–")

        # Warnings
        if result.warnings:
            self.infeasibility_label.setText("⚠ " + " | ".join(result.warnings))
            self.infeasibility_label.setVisible(True)
