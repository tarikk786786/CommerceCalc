"""
Shipping and Logistics Calculator Page for CommerceCalc.
"""
from decimal import Decimal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QFrame,
    QPushButton, QLabel, QGridLayout, QSplitter, QCheckBox, QComboBox
)
from PySide6.QtCore import Qt, QTimer
from ..widgets.common import (
    MoneyInput, PercentInput, MetricCard, SectionTitle, Divider,
    ResultRow, DisclaimerBox, InfoBox, make_card, fmt_inr, fmt_pct,
    FormFieldRow
)
from ...core.shipping import ShippingInputs, calculate_shipping


class ShippingPage(QWidget):
    """Courier shipping and dimensional weight calculator."""

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

        # 1. Package Dimensions
        dim_card, dim_layout = make_card("📦 Package Physical Dimensions")
        self.length_in = MoneyInput(prefix="", max_val=999.0)
        self.length_in.setValue(25.0)
        self.length_in.valueChanged.connect(self._trigger_calc)
        dim_layout.addWidget(FormFieldRow("Length (cm)", self.length_in))

        self.width_in = MoneyInput(prefix="", max_val=999.0)
        self.width_in.setValue(20.0)
        self.width_in.valueChanged.connect(self._trigger_calc)
        dim_layout.addWidget(FormFieldRow("Width (cm)", self.width_in))

        self.height_in = MoneyInput(prefix="", max_val=999.0)
        self.height_in.setValue(10.0)
        self.height_in.valueChanged.connect(self._trigger_calc)
        dim_layout.addWidget(FormFieldRow("Height (cm)", self.height_in))

        self.weight_in = MoneyInput(prefix="", max_val=999.0)
        self.weight_in.setValue(0.5)
        self.weight_in.setSingleStep(0.1)
        self.weight_in.valueChanged.connect(self._trigger_calc)
        dim_layout.addWidget(FormFieldRow("Actual Weight (kg)", self.weight_in))

        self.dim_divisor = MoneyInput(prefix="", max_val=10000.0)
        self.dim_divisor.setValue(5000.0)
        self.dim_divisor.valueChanged.connect(self._trigger_calc)
        dim_layout.addWidget(FormFieldRow("Dimensional Divisor", self.dim_divisor,
                                           "Standard is 5000 cc/kg for air/express; 4000 for surface."))
        left_layout.addWidget(dim_card)

        # 2. Courier Rate Card
        rate_card, rate_layout = make_card("🚚 Courier Rate Card (User-Configured)")
        rate_layout.addWidget(InfoBox(
            "Enter your carrier's negotiated rates (e.g., Delhivery, BlueDart, Shiprocket, Xpressbees)."
        ))

        self.fwd_rate = MoneyInput(max_val=9999.0)
        self.fwd_rate.setValue(60.0)
        self.fwd_rate.valueChanged.connect(self._trigger_calc)
        rate_layout.addWidget(FormFieldRow("Forward Rate (Base 500g)", self.fwd_rate))

        self.add_rate = MoneyInput(max_val=9999.0)
        self.add_rate.setValue(45.0)
        self.add_rate.valueChanged.connect(self._trigger_calc)
        rate_layout.addWidget(FormFieldRow("Additional 500g Rate", self.add_rate))

        self.rev_rate = MoneyInput(max_val=9999.0)
        self.rev_rate.setValue(70.0)
        self.rev_rate.valueChanged.connect(self._trigger_calc)
        rate_layout.addWidget(FormFieldRow("Reverse Shipping (Base)", self.rev_rate))

        self.rto_rate = MoneyInput(max_val=9999.0)
        self.rto_rate.setValue(65.0)
        self.rto_rate.valueChanged.connect(self._trigger_calc)
        rate_layout.addWidget(FormFieldRow("RTO Courier Charge", self.rto_rate))

        self.pickup_fee = MoneyInput(max_val=999.0)
        self.pickup_fee.setValue(0.0)
        self.pickup_fee.valueChanged.connect(self._trigger_calc)
        rate_layout.addWidget(FormFieldRow("Pickup / Hub Fee", self.pickup_fee))

        self.fuel_pct = PercentInput()
        self.fuel_pct.setValue(10.0)
        self.fuel_pct.valueChanged.connect(self._trigger_calc)
        rate_layout.addWidget(FormFieldRow("Fuel Surcharge %", self.fuel_pct))
        left_layout.addWidget(rate_card)

        # 3. Order Details
        order_card, order_layout = make_card("🏷️ Order Parameters")
        self.selling_price = MoneyInput(max_val=999999.0)
        self.selling_price.setValue(899.0)
        self.selling_price.valueChanged.connect(self._trigger_calc)
        order_layout.addWidget(FormFieldRow("Product Selling Price", self.selling_price))

        self.is_cod = QCheckBox("Cash on Delivery (COD) Order")
        self.is_cod.stateChanged.connect(self._trigger_calc)
        order_layout.addWidget(self.is_cod)

        self.cod_flat = MoneyInput(max_val=999.0)
        self.cod_flat.setValue(35.0)
        self.cod_flat.valueChanged.connect(self._trigger_calc)
        order_layout.addWidget(FormFieldRow("COD Fixed Collection Fee", self.cod_flat))

        self.cod_pct = PercentInput()
        self.cod_pct.setValue(1.5)
        self.cod_pct.valueChanged.connect(self._trigger_calc)
        order_layout.addWidget(FormFieldRow("COD Percentage Fee %", self.cod_pct))
        left_layout.addWidget(order_card)

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

        # Metrics Grid
        metrics_grid = QGridLayout()
        metrics_grid.setSpacing(12)
        self.card_chargeable_wt = MetricCard("Chargeable Weight", "– kg")
        self.card_forward_cost = MetricCard("Forward Shipping", "₹–", "default")
        self.card_rto_cost = MetricCard("RTO Cost (if failed)", "₹–", "danger")
        self.card_shipping_pct = MetricCard("Shipping % of Sale", "–%", "default")
        metrics_grid.addWidget(self.card_chargeable_wt, 0, 0)
        metrics_grid.addWidget(self.card_forward_cost, 0, 1)
        metrics_grid.addWidget(self.card_rto_cost, 1, 0)
        metrics_grid.addWidget(self.card_shipping_pct, 1, 1)
        right_layout.addLayout(metrics_grid)

        # Detailed breakdown
        res_card, res_layout = make_card("Weight & Freight Breakdown")
        self.row_volume = ResultRow("Package Volume", "– cc")
        self.row_dim_weight = ResultRow("Dimensional Weight", "– kg")
        self.row_act_weight = ResultRow("Actual Weight", "– kg")
        self.row_weight_slabs = ResultRow("Billable Slabs (500g each)", "–")
        self.row_base_forward = ResultRow("Base Forward Delivery", "–")
        self.row_fuel = ResultRow("Fuel Surcharge", "–")
        self.row_cod_fee = ResultRow("COD Collection Fee", "–")
        self.row_total_forward = ResultRow("Total Forward Order Freight", "–", bold=True, color="#4ade80")
        self.row_reverse_cost = ResultRow("Customer Return (Reverse) Cost", "–")
        self.row_rto_total = ResultRow("Full RTO Total Loss (Fwd + RTO)", "–", bold=True, color="#f87171")
        self.row_min_shipping_rev = ResultRow("Min Shipping Charge to Cover Cost", "–")

        for r in [
            self.row_volume, self.row_dim_weight, self.row_act_weight, self.row_weight_slabs,
            Divider(), self.row_base_forward, self.row_fuel, self.row_cod_fee,
            Divider(), self.row_total_forward, Divider(),
            self.row_reverse_cost, self.row_rto_total, self.row_min_shipping_rev
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
            inputs = ShippingInputs(
                length_cm=self.length_in.get_decimal(),
                width_cm=self.width_in.get_decimal(),
                height_cm=self.height_in.get_decimal(),
                actual_weight_kg=self.weight_in.get_decimal(),
                dimensional_weight_divisor=self.dim_divisor.get_decimal(),
                forward_rate_per_500g=self.fwd_rate.get_decimal(),
                additional_500g_rate=self.add_rate.get_decimal(),
                reverse_rate_per_500g=self.rev_rate.get_decimal(),
                rto_rate_per_500g=self.rto_rate.get_decimal(),
                pickup_fee=self.pickup_fee.get_decimal(),
                fuel_surcharge_pct=self.fuel_pct.get_decimal(),
                cod_collection_fee=self.cod_flat.get_decimal(),
                cod_collection_pct=self.cod_pct.get_decimal(),
            )
            sp = self.selling_price.get_decimal()
            is_cod_order = self.is_cod.isChecked()
            res = calculate_shipping(inputs, selling_price=sp, is_cod=is_cod_order)

            # Update UI
            self.card_chargeable_wt.update_value(f"{res.chargeable_weight_kg:.2f} kg")
            self.card_forward_cost.update_value(fmt_inr(res.total_forward_order_cost), "success")
            total_rto_loss = res.total_forward_order_cost + res.rto_cost
            self.card_rto_cost.update_value(fmt_inr(total_rto_loss), "danger")
            self.card_shipping_pct.update_value(fmt_pct(res.shipping_cost_pct_of_selling))

            self.row_volume.set_value(f"{res.volume_cc:,.1f} cc")
            self.row_dim_weight.set_value(f"{res.dimensional_weight_kg:.2f} kg")
            self.row_act_weight.set_value(f"{inputs.actual_weight_kg:.2f} kg")
            self.row_weight_slabs.set_value(f"{res.weight_slabs} slab(s)")
            self.row_base_forward.set_value(fmt_inr(res.forward_delivery_cost))
            self.row_fuel.set_value(fmt_inr(res.fuel_surcharge))
            self.row_cod_fee.set_value(fmt_inr(res.cod_cost) if is_cod_order else "₹0.00 (Prepaid)")
            self.row_total_forward.set_value(fmt_inr(res.total_forward_order_cost), "#4ade80")
            self.row_reverse_cost.set_value(fmt_inr(res.total_reverse_cost))
            self.row_rto_total.set_value(fmt_inr(total_rto_loss), "#f87171")
            self.row_min_shipping_rev.set_value(fmt_inr(res.min_shipping_revenue_needed))

            if res.warnings:
                self.warnings_label.setText("⚠ " + " | ".join(res.warnings))
            else:
                self.warnings_label.setText("")
        except Exception as e:
            self.warnings_label.setText(f"Error: {str(e)}")
