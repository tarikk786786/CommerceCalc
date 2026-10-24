"""
Bundle and Multi-Unit Profit Calculator Page for CommerceCalc.
"""
from decimal import Decimal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QFrame,
    QPushButton, QLabel, QGridLayout, QSplitter, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit
)
from PySide6.QtCore import Qt, QTimer
from ..widgets.common import (
    MoneyInput, PercentInput, MetricCard, SectionTitle, Divider,
    ResultRow, InfoBox, make_card, fmt_inr, fmt_pct, FormFieldRow
)
from ...core.bundles import BundleInputs, BundleItem, calculate_bundle


class BundleCalcPage(QWidget):
    """Multi-SKU bundle pricing and profit allocation calculator."""

    def __init__(self, db_session=None, parent=None):
        super().__init__(parent)
        self.db_session = db_session
        self._items = [
            BundleItem(sku="SKU-1", name="Product A (Main Unit)", unit_cost=Decimal("200"), quantity=1, individual_selling_price=Decimal("499")),
            BundleItem(sku="SKU-2", name="Product B (Complementary)", unit_cost=Decimal("150"), quantity=1, individual_selling_price=Decimal("399")),
        ]
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
        left_scroll.setMinimumWidth(500)
        left_scroll.setMaximumWidth(580)

        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(20, 16, 20, 20)
        left_layout.setSpacing(16)

        left_layout.addWidget(InfoBox(
            "Combine multiple products or multi-packs into a single offer. "
            "Transparently allocates shared courier and packaging costs across constituent items."
        ))

        # 1. Bundle Items Table
        items_card, items_layout = make_card("📦 Bundle Constituent Items")
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["SKU / Item", "Cost (₹)", "Qty", "Price (₹)"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.setMinimumHeight(140)
        items_layout.addWidget(self.table)

        btn_row = QHBoxLayout()
        add_btn = QPushButton("+ Add Product to Bundle")
        add_btn.setObjectName("secondary_btn")
        add_btn.clicked.connect(self._add_item_dialog)
        del_btn = QPushButton("Remove Selected Item")
        del_btn.setObjectName("danger_btn")
        del_btn.clicked.connect(self._remove_selected_item)
        btn_row.addWidget(add_btn)
        btn_row.addWidget(del_btn)
        items_layout.addLayout(btn_row)
        left_layout.addWidget(items_card)

        # 2. Bundle Pricing & Shared Costs
        price_card, price_layout = make_card("🏷️ Bundle Pricing & Shared Expenses")
        self.bundle_price = MoneyInput(max_val=999999.0)
        self.bundle_price.setValue(749.0)
        self.bundle_price.valueChanged.connect(self._trigger_calc)
        price_layout.addWidget(FormFieldRow("Bundle Selling Price", self.bundle_price))

        self.shared_pack = MoneyInput(max_val=9999.0)
        self.shared_pack.setValue(25.0)
        self.shared_pack.valueChanged.connect(self._trigger_calc)
        price_layout.addWidget(FormFieldRow("Shared Combo Packaging", self.shared_pack))

        self.shared_ship = MoneyInput(max_val=9999.0)
        self.shared_ship.setValue(80.0)
        self.shared_ship.valueChanged.connect(self._trigger_calc)
        price_layout.addWidget(FormFieldRow("Combined Forward Shipping", self.shared_ship))

        self.mp_fee_pct = PercentInput()
        self.mp_fee_pct.setValue(10.0)
        self.mp_fee_pct.valueChanged.connect(self._trigger_calc)
        price_layout.addWidget(FormFieldRow("Marketplace Commission %", self.mp_fee_pct))

        self.fixed_closing = MoneyInput(max_val=999.0)
        self.fixed_closing.setValue(20.0)
        self.fixed_closing.valueChanged.connect(self._trigger_calc)
        price_layout.addWidget(FormFieldRow("Fixed Closing Fee (₹)", self.fixed_closing))

        self.alloc_method = QComboBox()
        self.alloc_method.addItems(["Cost Share (Recommended)", "Quantity Share", "Standalone Price Share"])
        self.alloc_method.currentIndexChanged.connect(self._trigger_calc)
        price_layout.addWidget(FormFieldRow("Shared Cost Allocation", self.alloc_method))
        left_layout.addWidget(price_card)

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
        self.card_bundle_profit = MetricCard("Bundle Net Profit", "₹–", "success")
        self.card_bundle_margin = MetricCard("Bundle Margin %", "–%", "success")
        self.card_standalone_val = MetricCard("Total Standalone Value", "₹–", "default")
        self.card_discount_pct = MetricCard("Customer Savings %", "–%", "default")
        metrics_grid.addWidget(self.card_bundle_profit, 0, 0)
        metrics_grid.addWidget(self.card_bundle_margin, 0, 1)
        metrics_grid.addWidget(self.card_standalone_val, 1, 0)
        metrics_grid.addWidget(self.card_discount_pct, 1, 1)
        right_layout.addLayout(metrics_grid)

        # Bundle Financial Summary
        sum_card, sum_layout = make_card("Bundle Financial Summary")
        self.row_standalone = ResultRow("Sum of Standalone Prices", "–")
        self.row_discount = ResultRow("Bundle Discount Given to Buyer", "–", color="#f87171")
        self.row_prod_cost = ResultRow("Total Goods Acquisition Cost", "–")
        self.row_shared_ops = ResultRow("Shared Packaging & Shipping", "–")
        self.row_mp_deductions = ResultRow("Total Marketplace Deductions", "–")
        self.row_net_profit = ResultRow("Net Operating Profit per Bundle", "–", bold=True, color="#4ade80")
        self.row_breakeven_bundle = ResultRow("Minimum Break-Even Bundle Price", "–", bold=True)

        for r in [
            self.row_standalone, self.row_discount, Divider(),
            self.row_prod_cost, self.row_shared_ops, self.row_mp_deductions,
            Divider(), self.row_net_profit, self.row_breakeven_bundle
        ]:
            sum_layout.addWidget(r)
        right_layout.addWidget(sum_card)

        # SKU Allocation Table
        alloc_card, alloc_layout = make_card("Per-SKU Cost & Profit Allocation")
        self.alloc_table = QTableWidget(0, 5)
        self.alloc_table.setHorizontalHeaderLabels(["SKU", "Direct Cost", "Alloc. Shared", "Alloc. Revenue", "Alloc. Profit"])
        self.alloc_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.alloc_table.setMinimumHeight(140)
        alloc_layout.addWidget(self.alloc_table)
        right_layout.addWidget(alloc_card)

        self.warnings_label = QLabel()
        self.warnings_label.setWordWrap(True)
        self.warnings_label.setStyleSheet("color: #fb923c; font-size: 12px;")
        right_layout.addWidget(self.warnings_label)
        right_layout.addStretch()

        splitter.addWidget(left_scroll)
        splitter.addWidget(right_scroll)
        splitter.setSizes([520, 600])
        main_layout.addWidget(splitter)

        self._refresh_table()
        self._calculate()

    def _refresh_table(self):
        self.table.setRowCount(len(self._items))
        for row, item in enumerate(self._items):
            self.table.setItem(row, 0, QTableWidgetItem(f"{item.sku} ({item.name})"))
            self.table.setItem(row, 1, QTableWidgetItem(f"₹{item.unit_cost:,.2f}"))
            self.table.setItem(row, 2, QTableWidgetItem(str(item.quantity)))
            self.table.setItem(row, 3, QTableWidgetItem(f"₹{item.individual_selling_price:,.2f}"))

    def _add_item_dialog(self):
        new_item = BundleItem(
            sku=f"SKU-{len(self._items)+1}",
            name=f"Extra Accessory {len(self._items)+1}",
            unit_cost=Decimal("100"),
            quantity=1,
            individual_selling_price=Decimal("299")
        )
        self._items.append(new_item)
        self._refresh_table()
        self._calculate()

    def _remove_selected_item(self):
        cur_row = self.table.currentRow()
        if 0 <= cur_row < len(self._items) and len(self._items) > 1:
            self._items.pop(cur_row)
            self._refresh_table()
            self._calculate()

    def _trigger_calc(self):
        self._calc_timer.start()

    def _calculate(self):
        try:
            methods = ["cost_share", "quantity_share", "price_share"]
            chosen_method = methods[self.alloc_method.currentIndex()]

            inputs = BundleInputs(
                items=self._items,
                bundle_selling_price=self.bundle_price.get_decimal(),
                shared_packaging_cost=self.shared_pack.get_decimal(),
                combined_shipping_cost=self.shared_ship.get_decimal(),
                marketplace_fee_pct=self.mp_fee_pct.get_decimal(),
                fixed_marketplace_fee=self.fixed_closing.get_decimal(),
                allocation_method=chosen_method,
            )
            res = calculate_bundle(inputs)

            p_type = "success" if res.bundle_net_profit > 0 else "danger"
            self.card_bundle_profit.update_value(fmt_inr(res.bundle_net_profit, show_sign=True), p_type)
            self.card_bundle_margin.update_value(fmt_pct(res.bundle_margin_pct), p_type)
            self.card_standalone_val.update_value(fmt_inr(res.total_standalone_price))
            self.card_discount_pct.update_value(fmt_pct(res.bundle_discount_pct))

            self.row_standalone.set_value(fmt_inr(res.total_standalone_price))
            self.row_discount.set_value(f"− {fmt_inr(res.bundle_discount_amount)} ({res.bundle_discount_pct:.1f}%)", "#f87171")
            self.row_prod_cost.set_value(fmt_inr(res.total_product_cost))
            self.row_shared_ops.set_value(fmt_inr(res.total_shared_cost))
            self.row_mp_deductions.set_value(fmt_inr(res.total_marketplace_fees))
            self.row_net_profit.set_value(fmt_inr(res.bundle_net_profit, show_sign=True), "#4ade80" if res.bundle_net_profit > 0 else "#f87171")
            self.row_breakeven_bundle.set_value(fmt_inr(res.break_even_bundle_price))

            # Populate per-item table
            self.alloc_table.setRowCount(len(res.item_breakdowns))
            for r, ib in enumerate(res.item_breakdowns):
                self.alloc_table.setItem(r, 0, QTableWidgetItem(ib.sku))
                self.alloc_table.setItem(r, 1, QTableWidgetItem(f"₹{ib.direct_cost:,.2f}"))
                self.alloc_table.setItem(r, 2, QTableWidgetItem(f"₹{ib.allocated_shared_cost:,.2f}"))
                self.alloc_table.setItem(r, 3, QTableWidgetItem(f"₹{ib.allocated_revenue:,.2f}"))
                prof_item = QTableWidgetItem(f"₹{ib.allocated_profit:,.2f} ({ib.profit_margin_pct:.1f}%)")
                prof_item.setForeground(Qt.green if ib.allocated_profit >= 0 else Qt.red)
                self.alloc_table.setItem(r, 4, prof_item)

            if res.warnings:
                self.warnings_label.setText("⚠ " + " | ".join(res.warnings))
            else:
                self.warnings_label.setText("")
        except Exception as e:
            self.warnings_label.setText(f"Error: {str(e)}")
