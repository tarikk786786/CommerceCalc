"""
Returns, Refunds, and RTO Loss Risk Calculator Page for CommerceCalc.
"""
from decimal import Decimal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QFrame,
    QPushButton, QLabel, QGridLayout, QSplitter
)
from PySide6.QtCore import Qt, QTimer
from ..widgets.common import (
    MoneyInput, PercentInput, MetricCard, SectionTitle, Divider,
    ResultRow, DisclaimerBox, InfoBox, make_card, fmt_inr, fmt_pct,
    FormFieldRow
)
from ...core.returns import ReturnRTOInputs, calculate_return_rto_loss


class ReturnsRTOPage(QWidget):
    """Expected operational loss calculator for returns & RTO risk."""

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

        left_layout.addWidget(DisclaimerBox(
            "Expected loss models use user-defined probability estimates (0-100%). "
            "RTO (rejected before delivery) is distinct from Customer Returns (accepted then returned)."
        ))

        # 1. Volume & Probability Rates
        vol_card, vol_layout = make_card("📊 Batch Order & Risk Rates")
        self.orders_in = MoneyInput(prefix="", max_val=1000000)
        self.orders_in.setDecimals(0)
        self.orders_in.setValue(100.0)
        self.orders_in.valueChanged.connect(self._trigger_calc)
        vol_layout.addWidget(FormFieldRow("Total Orders in Batch", self.orders_in))

        self.rto_rate = PercentInput()
        self.rto_rate.setValue(15.0)  # Typical COD in India is 15-25%
        self.rto_rate.valueChanged.connect(self._trigger_calc)
        vol_layout.addWidget(FormFieldRow("RTO Rate % (Failed Deliveries)", self.rto_rate,
                                           "Orders rejected at doorstep or undeliverable."))

        self.return_rate = PercentInput()
        self.return_rate.setValue(8.0)
        self.return_rate.valueChanged.connect(self._trigger_calc)
        vol_layout.addWidget(FormFieldRow("Customer Return Rate %", self.return_rate,
                                           "Delivered orders returned by customers for refund."))

        self.damage_rate = PercentInput()
        self.damage_rate.setValue(2.0)
        self.damage_rate.valueChanged.connect(self._trigger_calc)
        vol_layout.addWidget(FormFieldRow("Product Transit Damage %", self.damage_rate))

        self.resalable_pct = PercentInput()
        self.resalable_pct.setValue(75.0)
        self.resalable_pct.valueChanged.connect(self._trigger_calc)
        vol_layout.addWidget(FormFieldRow("Resalable Return Stock %", self.resalable_pct,
                                           "Returned units in good enough condition to repack and resell."))
        left_layout.addWidget(vol_card)

        # 2. Financial Costs per Event
        cost_card, cost_layout = make_card("💸 Cost Impact Per Unit/Event")
        self.unit_cost = MoneyInput(max_val=999999.0)
        self.unit_cost.setValue(350.0)
        self.unit_cost.valueChanged.connect(self._trigger_calc)
        cost_layout.addWidget(FormFieldRow("Product Unit Cost", self.unit_cost))

        self.fwd_shipping = MoneyInput(max_val=9999.0)
        self.fwd_shipping.setValue(70.0)
        self.fwd_shipping.valueChanged.connect(self._trigger_calc)
        cost_layout.addWidget(FormFieldRow("Forward Shipping Wasted", self.fwd_shipping))

        self.rto_shipping = MoneyInput(max_val=9999.0)
        self.rto_shipping.setValue(65.0)
        self.rto_shipping.valueChanged.connect(self._trigger_calc)
        cost_layout.addWidget(FormFieldRow("RTO Return Shipping Fee", self.rto_shipping))

        self.rev_shipping = MoneyInput(max_val=9999.0)
        self.rev_shipping.setValue(75.0)
        self.rev_shipping.valueChanged.connect(self._trigger_calc)
        cost_layout.addWidget(FormFieldRow("Customer Reverse Shipping", self.rev_shipping))

        self.non_refundable_fee = MoneyInput(max_val=9999.0)
        self.non_refundable_fee.setValue(25.0)
        self.non_refundable_fee.valueChanged.connect(self._trigger_calc)
        cost_layout.addWidget(FormFieldRow("Non-Refundable Platform Fees", self.non_refundable_fee,
                                           "Closing fees or payment charges not reversed on returns."))

        self.restocking_fee = MoneyInput(max_val=9999.0)
        self.restocking_fee.setValue(15.0)
        self.restocking_fee.valueChanged.connect(self._trigger_calc)
        cost_layout.addWidget(FormFieldRow("Restocking & QC Cost", self.restocking_fee))

        self.recovery_val = MoneyInput(max_val=999999.0)
        self.recovery_val.setValue(250.0)
        self.recovery_val.valueChanged.connect(self._trigger_calc)
        cost_layout.addWidget(FormFieldRow("Recovery Value per Returned Unit", self.recovery_val))

        self.base_profit = MoneyInput(max_val=999999.0)
        self.base_profit.setValue(220.0)
        self.base_profit.valueChanged.connect(self._trigger_calc)
        cost_layout.addWidget(FormFieldRow("Base Profit per Success (Pre-Risk)", self.base_profit))
        left_layout.addWidget(cost_card)

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
        self.card_total_loss = MetricCard("Total Expected Loss", "₹–", "danger")
        self.card_loss_per_order = MetricCard("Expected Loss / Order", "₹–", "danger")
        self.card_adjusted_profit = MetricCard("Risk-Adjusted Profit", "₹–", "success")
        self.card_success_count = MetricCard("Expected Deliveries", "–", "default")
        metrics_grid.addWidget(self.card_total_loss, 0, 0)
        metrics_grid.addWidget(self.card_loss_per_order, 0, 1)
        metrics_grid.addWidget(self.card_adjusted_profit, 1, 0)
        metrics_grid.addWidget(self.card_success_count, 1, 1)
        right_layout.addLayout(metrics_grid)

        # Breakdown
        res_card, res_layout = make_card("Expected Risk Breakdown")
        self.row_success_orders = ResultRow("Expected Successful Deliveries", "–")
        self.row_rto_orders = ResultRow("Expected RTO Shipments", "–")
        self.row_return_orders = ResultRow("Expected Customer Returns", "–")
        self.row_damaged_orders = ResultRow("Expected Damaged Units", "–")
        self.row_logistics_loss = ResultRow("Total Courier Waste (Fwd + Rev + RTO)", "–", bold=True, color="#f87171")
        self.row_inventory_loss = ResultRow("Unrecovered Inventory Write-off", "–")
        self.row_fee_loss = ResultRow("Non-Refundable Marketplace Charges", "–")
        self.row_recovered_val = ResultRow("Salvage Value Recovered", "–", color="#4ade80")
        self.row_be_adjustment = ResultRow("Required Price Buffer per Order", "–", bold=True)

        for r in [
            self.row_success_orders, self.row_rto_orders, self.row_return_orders, self.row_damaged_orders,
            Divider(), self.row_logistics_loss, self.row_inventory_loss, self.row_fee_loss, self.row_recovered_val,
            Divider(), self.row_be_adjustment
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
            inputs = ReturnRTOInputs(
                total_orders=max(int(self.orders_in.value()), 1),
                return_rate_pct=self.return_rate.get_decimal(),
                rto_rate_pct=self.rto_rate.get_decimal(),
                damage_rate_pct=self.damage_rate.get_decimal(),
                resalable_pct=self.resalable_pct.get_decimal(),
                product_cost_per_unit=self.unit_cost.get_decimal(),
                forward_shipping_cost=self.fwd_shipping.get_decimal(),
                reverse_shipping_cost=self.rev_shipping.get_decimal(),
                rto_shipping_cost=self.rto_shipping.get_decimal(),
                non_refundable_fees_per_return=self.non_refundable_fee.get_decimal(),
                restocking_cost_per_unit=self.restocking_fee.get_decimal(),
                recovery_value_per_returned_unit=self.recovery_val.get_decimal(),
            )
            base_p = self.base_profit.get_decimal()
            res = calculate_return_rto_loss(inputs, base_profit_per_successful_order=base_p)

            self.card_total_loss.update_value(fmt_inr(res.total_expected_loss), "danger")
            self.card_loss_per_order.update_value(fmt_inr(res.expected_net_loss_per_order), "danger")
            adj_type = "success" if res.adjusted_profit_per_successful_order > 0 else "danger"
            self.card_adjusted_profit.update_value(fmt_inr(res.adjusted_profit_per_successful_order, show_sign=True), adj_type)
            self.card_success_count.update_value(f"{res.expected_successful_deliveries:.0f} orders")

            self.row_success_orders.set_value(f"{res.expected_successful_deliveries:.1f}")
            self.row_rto_orders.set_value(f"{res.expected_rto:.1f}")
            self.row_return_orders.set_value(f"{res.expected_returns:.1f}")
            self.row_damaged_orders.set_value(f"{res.expected_damaged:.1f}")
            self.row_logistics_loss.set_value(fmt_inr(res.logistics_loss), "#f87171")
            self.row_inventory_loss.set_value(fmt_inr(res.unrecovered_product_cost))
            self.row_fee_loss.set_value(fmt_inr(res.non_refundable_fee_loss))
            self.row_recovered_val.set_value(f"+ {fmt_inr(res.recovered_inventory_value)}", "#4ade80")
            self.row_be_adjustment.set_value(f"+ {fmt_inr(res.break_even_price_adjustment)} / order")

            if res.warnings:
                self.warnings_label.setText("⚠ " + " | ".join(res.warnings))
            else:
                self.warnings_label.setText("")
        except Exception as e:
            self.warnings_label.setText(f"Error: {str(e)}")
