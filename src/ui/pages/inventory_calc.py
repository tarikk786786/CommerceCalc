"""
Inventory, Reorder Point, and EOQ Calculator Page for CommerceCalc.
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
from ...core.inventory import InventoryInputs, calculate_inventory


class InventoryPage(QWidget):
    """Inventory control, reorder point, and runout risk calculator."""

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
            "Prevent costly stockouts and dead capital. Computes exact Reorder Point (ROP), "
            "Days of Inventory Remaining (DIR), and Economic Order Quantity (EOQ)."
        ))

        # 1. Product & On-Hand Stock
        stock_card, stock_layout = make_card("📦 Stock Levels")
        self.unit_cost = MoneyInput(max_val=999999.0)
        self.unit_cost.setValue(320.0)
        self.unit_cost.valueChanged.connect(self._trigger_calc)
        stock_layout.addWidget(FormFieldRow("Product Cost per Unit", self.unit_cost))

        self.selling_price = MoneyInput(max_val=999999.0)
        self.selling_price.setValue(799.0)
        self.selling_price.valueChanged.connect(self._trigger_calc)
        stock_layout.addWidget(FormFieldRow("Retail Selling Price", self.selling_price))

        self.on_hand = MoneyInput(prefix="", max_val=1000000)
        self.on_hand.setDecimals(0)
        self.on_hand.setValue(120.0)
        self.on_hand.valueChanged.connect(self._trigger_calc)
        stock_layout.addWidget(FormFieldRow("Physical On-Hand Stock", self.on_hand))

        self.reserved_stock = MoneyInput(prefix="", max_val=1000000)
        self.reserved_stock.setDecimals(0)
        self.reserved_stock.setValue(15.0)
        self.reserved_stock.valueChanged.connect(self._trigger_calc)
        stock_layout.addWidget(FormFieldRow("Reserved / Unshipped Orders", self.reserved_stock))

        self.incoming_stock = MoneyInput(prefix="", max_val=1000000)
        self.incoming_stock.setDecimals(0)
        self.incoming_stock.setValue(50.0)
        self.incoming_stock.valueChanged.connect(self._trigger_calc)
        stock_layout.addWidget(FormFieldRow("Stock in Transit from Supplier", self.incoming_stock))
        left_layout.addWidget(stock_card)

        # 2. Demand Velocity & Lead Time
        vel_card, vel_layout = make_card("⏱️ Demand Velocity & Lead Times")
        self.daily_sales = MoneyInput(prefix="", max_val=10000.0)
        self.daily_sales.setValue(8.0)
        self.daily_sales.valueChanged.connect(self._trigger_calc)
        vel_layout.addWidget(FormFieldRow("Average Daily Sales (Units)", self.daily_sales))

        self.lead_time = MoneyInput(prefix="", max_val=365)
        self.lead_time.setDecimals(0)
        self.lead_time.setValue(14.0)
        self.lead_time.valueChanged.connect(self._trigger_calc)
        vel_layout.addWidget(FormFieldRow("Supplier Lead Time (Days)", self.lead_time,
                                           "Days between order placement and goods arrival in warehouse."))

        self.safety_days = MoneyInput(prefix="", max_val=180)
        self.safety_days.setDecimals(0)
        self.safety_days.setValue(7.0)
        self.safety_days.valueChanged.connect(self._trigger_calc)
        vel_layout.addWidget(FormFieldRow("Buffer / Safety Stock (Days)", self.safety_days))

        self.moq = MoneyInput(prefix="", max_val=100000)
        self.moq.setDecimals(0)
        self.moq.setValue(50.0)
        self.moq.valueChanged.connect(self._trigger_calc)
        vel_layout.addWidget(FormFieldRow("Supplier MOQ (Min Order Qty)", self.moq))

        self.carry_cost_pct = PercentInput()
        self.carry_cost_pct.setValue(18.0)
        self.carry_cost_pct.valueChanged.connect(self._trigger_calc)
        vel_layout.addWidget(FormFieldRow("Annual Holding Cost %", self.carry_cost_pct))
        left_layout.addWidget(vel_card)

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

        # Status badge
        status_row = QHBoxLayout()
        self.stock_status_lbl = QLabel("Stock Status: Normal")
        self.stock_status_lbl.setObjectName("badge_profitable")
        status_row.addWidget(self.stock_status_lbl)
        status_row.addStretch()
        right_layout.addLayout(status_row)

        # Metrics
        metrics_grid = QGridLayout()
        metrics_grid.setSpacing(12)
        self.card_runout_days = MetricCard("Runout Runway (DIR)", "– days", "default")
        self.card_reorder_point = MetricCard("Reorder Point (ROP)", "– units", "default")
        self.card_suggested_reorder = MetricCard("Suggested Reorder Qty", "– units", "default")
        self.card_capital_tied = MetricCard("Stock Capital Tied Up", "₹–", "default")
        metrics_grid.addWidget(self.card_runout_days, 0, 0)
        metrics_grid.addWidget(self.card_reorder_point, 0, 1)
        metrics_grid.addWidget(self.card_suggested_reorder, 1, 0)
        metrics_grid.addWidget(self.card_capital_tied, 1, 1)
        right_layout.addLayout(metrics_grid)

        # Breakdown
        res_card, res_layout = make_card("Inventory Planning Analysis")
        self.row_ats = ResultRow("Available to Sell Stock", "–")
        self.row_eff_stock = ResultRow("Total Effective Stock (inc. transit)", "–")
        self.row_lead_demand = ResultRow("Demand During Supplier Lead Time", "–")
        self.row_safety_units = ResultRow("Safety Stock Buffer Units", "–")
        self.row_rop = ResultRow("Reorder Threshold Trigger (ROP)", "–", bold=True)
        self.row_reorder_alert = ResultRow("Purchase Order Status", "–", bold=True)
        self.row_suggested_qty = ResultRow("Suggested Order Quantity (30d cover / MOQ)", "–", bold=True, color="#4ade80")
        self.row_eoq = ResultRow("Economic Order Quantity (EOQ)", "–")
        self.row_holding_cost = ResultRow("Annual Carrying Cost (Holding)", "–")
        self.row_gmroi = ResultRow("GMROI (Gross Margin Return on Inventory)", "–")

        for r in [
            self.row_ats, self.row_eff_stock, Divider(),
            self.row_lead_demand, self.row_safety_units, self.row_rop, Divider(),
            self.row_reorder_alert, self.row_suggested_qty, self.row_eoq, Divider(),
            self.row_holding_cost, self.row_gmroi
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
            inputs = InventoryInputs(
                unit_cost=self.unit_cost.get_decimal(),
                selling_price=self.selling_price.get_decimal(),
                available_stock=max(int(self.on_hand.value()), 0),
                reserved_stock=max(int(self.reserved_stock.value()), 0),
                incoming_stock=max(int(self.incoming_stock.value()), 0),
                average_daily_sales=self.daily_sales.get_decimal(),
                lead_time_days=max(int(self.lead_time.value()), 1),
                safety_stock_days=max(int(self.safety_days.value()), 0),
                minimum_order_quantity=max(int(self.moq.value()), 1),
                annual_holding_cost_pct=self.carry_cost_pct.get_decimal(),
            )
            res = calculate_inventory(inputs)

            if "CRITICAL" in res.stockout_risk_status:
                self.stock_status_lbl.setText("🚨 CRITICAL: Stockout Imminent")
                self.stock_status_lbl.setObjectName("badge_loss")
            elif "WARNING" in res.stockout_risk_status:
                self.stock_status_lbl.setText("⚠ REORDER NEEDED: Stock Below ROP")
                self.stock_status_lbl.setObjectName("badge_warning")
            else:
                self.stock_status_lbl.setText("✓ Healthy Stock Level")
                self.stock_status_lbl.setObjectName("badge_profitable")
            self.stock_status_lbl.style().unpolish(self.stock_status_lbl)
            self.stock_status_lbl.style().polish(self.stock_status_lbl)

            runout_type = "danger" if res.days_of_inventory_remaining < 15 else "default"
            self.card_runout_days.update_value(f"{res.days_of_inventory_remaining:.1f} days", runout_type)
            self.card_reorder_point.update_value(f"{res.reorder_point_units} units")
            reorder_type = "danger" if res.reorder_needed else "default"
            self.card_suggested_reorder.update_value(f"{res.suggested_reorder_quantity} units", reorder_type)
            self.card_capital_tied.update_value(fmt_inr(res.total_inventory_value))

            self.row_ats.set_value(f"{res.available_to_sell} units")
            self.row_eff_stock.set_value(f"{res.total_effective_stock} units")
            self.row_lead_demand.set_value(f"{res.lead_time_demand_units} units")
            self.row_safety_units.set_value(f"{res.safety_stock_units} units")
            self.row_rop.set_value(f"{res.reorder_point_units} units", bold=True)
            self.row_reorder_alert.set_value(
                "🚨 PLACE PURCHASE ORDER NOW" if res.reorder_needed else "✓ Stock Adequate",
                "#f87171" if res.reorder_needed else "#4ade80"
            )
            self.row_suggested_qty.set_value(f"{res.suggested_reorder_quantity} units", "#4ade80" if res.reorder_needed else None)
            self.row_eoq.set_value(f"{res.estimated_eoq} units")
            self.row_holding_cost.set_value(fmt_inr(res.annual_carrying_cost))
            self.row_gmroi.set_value(fmt_pct(res.gmroi_pct))

            if res.warnings:
                self.warnings_label.setText("⚠ " + " | ".join(res.warnings))
            else:
                self.warnings_label.setText("")
        except Exception as e:
            self.warnings_label.setText(f"Error: {str(e)}")
