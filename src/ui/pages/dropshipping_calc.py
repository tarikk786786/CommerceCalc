"""
Dropshipping Economics & Risk Calculator Page for CommerceCalc.
"""
from decimal import Decimal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QFrame,
    QPushButton, QLabel, QGridLayout, QSplitter, QComboBox, QCheckBox
)
from PySide6.QtCore import Qt, QTimer
from ..widgets.common import (
    MoneyInput, PercentInput, MetricCard, SectionTitle, Divider,
    ResultRow, DisclaimerBox, InfoBox, make_card, fmt_inr, fmt_pct,
    FormFieldRow
)
from ...core.dropshipping import DropshipInputs, calculate_dropship


class DropshippingPage(QWidget):
    """International and domestic dropshipping profit calculator."""

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
            "Designed for Indian dropshippers selling locally or internationally. "
            "Accounts for FX currency conversion fees, ad spend (CAC), and COD doorstep rejection losses."
        ))

        # 1. Supplier & Forex
        sup_card, sup_layout = make_card("🌏 Sourcing & Currency Exchange")
        self.sup_price = MoneyInput(prefix="$ ", max_val=99999.0)
        self.sup_price.setValue(6.50)
        self.sup_price.valueChanged.connect(self._trigger_calc)
        sup_layout.addWidget(FormFieldRow("Supplier Item Price ($)", self.sup_price))

        self.sup_ship = MoneyInput(prefix="$ ", max_val=99999.0)
        self.sup_ship.setValue(2.50)
        self.sup_ship.valueChanged.connect(self._trigger_calc)
        sup_layout.addWidget(FormFieldRow("Supplier Shipping / Packet ($)", self.sup_ship))

        self.fx_rate = MoneyInput(prefix="₹ ", max_val=999.0)
        self.fx_rate.setValue(84.0)
        self.fx_rate.valueChanged.connect(self._trigger_calc)
        sup_layout.addWidget(FormFieldRow("Base Exchange Rate (USD to INR)", self.fx_rate))

        self.fx_fee_pct = PercentInput()
        self.fx_fee_pct.setValue(2.5)  # Card / Paypal FX spread
        self.fx_fee_pct.valueChanged.connect(self._trigger_calc)
        sup_layout.addWidget(FormFieldRow("Bank FX Spread / Fee %", self.fx_fee_pct))
        left_layout.addWidget(sup_card)

        # 2. Store & Selling Details
        store_card, store_layout = make_card("🏪 Store Selling & Payment")
        self.selling_price = MoneyInput(max_val=999999.0)
        self.selling_price.setValue(1499.0)
        self.selling_price.valueChanged.connect(self._trigger_calc)
        store_layout.addWidget(FormFieldRow("Customer Selling Price (₹)", self.selling_price))

        self.order_mode = QComboBox()
        self.order_mode.addItems(["Prepaid (Online Card/UPI)", "Cash on Delivery (COD)"])
        self.order_mode.currentIndexChanged.connect(self._trigger_calc)
        store_layout.addWidget(FormFieldRow("Order Payment Flow", self.order_mode))

        self.pg_pct = PercentInput()
        self.pg_pct.setValue(2.0)
        self.pg_pct.valueChanged.connect(self._trigger_calc)
        store_layout.addWidget(FormFieldRow("Payment Gateway Fee %", self.pg_pct))

        self.store_alloc = MoneyInput(max_val=999.0)
        self.store_alloc.setValue(20.0)
        self.store_alloc.valueChanged.connect(self._trigger_calc)
        store_layout.addWidget(FormFieldRow("Store Plan Alloc. / Order (₹)", self.store_alloc,
                                             "Allocated share of Shopify / theme apps subscription cost."))
        left_layout.addWidget(store_card)

        # 3. Marketing & Delivery Risk
        risk_card, risk_layout = make_card("📢 Marketing & Delivery Risk")
        self.target_cac = MoneyInput(max_val=99999.0)
        self.target_cac.setValue(450.0)
        self.target_cac.valueChanged.connect(self._trigger_calc)
        risk_layout.addWidget(FormFieldRow("Ad Spend per Order (Target CAC)", self.target_cac))

        self.rto_rate = PercentInput()
        self.rto_rate.setValue(20.0)  # Typical COD dropshipping RTO
        self.rto_rate.valueChanged.connect(self._trigger_calc)
        risk_layout.addWidget(FormFieldRow("COD RTO Rate %", self.rto_rate,
                                            "Percentage of COD orders refused or returned at doorstep."))

        self.cod_charge = MoneyInput(max_val=999.0)
        self.cod_charge.setValue(40.0)
        self.cod_charge.valueChanged.connect(self._trigger_calc)
        risk_layout.addWidget(FormFieldRow("Courier COD Handling Charge", self.cod_charge))
        left_layout.addWidget(risk_card)

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
        self.card_profit = MetricCard("Profit per Order", "₹–", "success")
        self.card_margin = MetricCard("Contribution Margin", "–%", "success")
        self.card_landed_supplier = MetricCard("Landed Supplier Cost", "₹–", "default")
        self.card_max_cac = MetricCard("Maximum Safe CAC", "₹–", "default")
        metrics_grid.addWidget(self.card_profit, 0, 0)
        metrics_grid.addWidget(self.card_margin, 0, 1)
        metrics_grid.addWidget(self.card_landed_supplier, 1, 0)
        metrics_grid.addWidget(self.card_max_cac, 1, 1)
        right_layout.addLayout(metrics_grid)

        # Breakdown
        res_card, res_layout = make_card("Dropshipping Unit Economics")
        self.row_effective_fx = ResultRow("Effective Exchange Rate (incl. fee)", "–")
        self.row_supplier_cost = ResultRow("Total Supplier Outlay in INR", "–")
        self.row_selling_price = ResultRow("Customer Selling Price", "–")
        self.row_fees = ResultRow("Payment & Store Platform Fees", "–")
        self.row_ad_spend = ResultRow("Target Ad Spend (CAC)", "–")
        self.row_risk_loss = ResultRow("Expected Loss per Order (RTO/Refunds)", "–", color="#f87171")
        self.row_net_profit = ResultRow("Net Contribution Profit", "–", bold=True, color="#4ade80")
        self.row_breakeven_price = ResultRow("Break-Even Selling Price", "–", bold=True)
        self.row_max_supplier_price = ResultRow("Max Tolerable Supplier Cost", "–")

        for r in [
            self.row_effective_fx, self.row_supplier_cost, Divider(),
            self.row_selling_price, self.row_fees, self.row_ad_spend, self.row_risk_loss,
            Divider(), self.row_net_profit, self.row_breakeven_price, self.row_max_supplier_price
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
            is_cod = self.order_mode.currentIndex() == 1
            inputs = DropshipInputs(
                supplier_price_foreign=self.sup_price.get_decimal(),
                supplier_shipping_foreign=self.sup_ship.get_decimal(),
                exchange_rate=self.fx_rate.get_decimal(),
                currency_conversion_fee_pct=self.fx_fee_pct.get_decimal(),
                customer_selling_price_inr=self.selling_price.get_decimal(),
                payment_gateway_pct=self.pg_pct.get_decimal(),
                store_platform_allocated_inr=self.store_alloc.get_decimal(),
                ad_spend_per_order_inr=self.target_cac.get_decimal(),
                order_type="cod" if is_cod else "prepaid",
                cod_fee_inr=self.cod_charge.get_decimal() if is_cod else Decimal("0"),
                rto_rate_pct=self.rto_rate.get_decimal() if is_cod else Decimal("0"),
            )
            res = calculate_dropship(inputs)

            p_type = "success" if res.profit_per_order > 0 else "danger"
            self.card_profit.update_value(fmt_inr(res.profit_per_order, show_sign=True), p_type)
            self.card_margin.update_value(fmt_pct(res.contribution_margin_pct), p_type)
            self.card_landed_supplier.update_value(fmt_inr(res.landed_supplier_cost_inr))
            self.card_max_cac.update_value(fmt_inr(res.max_allowable_cac))

            self.row_effective_fx.set_value(f"1 USD = ₹{res.fx_effective_rate:.2f}")
            self.row_supplier_cost.set_value(fmt_inr(res.landed_supplier_cost_inr))
            self.row_selling_price.set_value(fmt_inr(res.customer_selling_price))
            self.row_fees.set_value(fmt_inr(res.total_platform_and_payment_fees))
            self.row_ad_spend.set_value(fmt_inr(inputs.ad_spend_per_order_inr))
            self.row_risk_loss.set_value(f"− {fmt_inr(res.expected_risk_loss_per_order)}", "#f87171")
            self.row_net_profit.set_value(fmt_inr(res.profit_per_order, show_sign=True), "#4ade80" if res.profit_per_order > 0 else "#f87171")
            self.row_breakeven_price.set_value(fmt_inr(res.break_even_selling_price))
            self.row_max_supplier_price.set_value(fmt_inr(res.max_tolerable_supplier_price_inr))

            if res.warnings:
                self.warnings_label.setText("⚠ " + " | ".join(res.warnings))
            else:
                self.warnings_label.setText("")
        except Exception as e:
            self.warnings_label.setText(f"Error: {str(e)}")
