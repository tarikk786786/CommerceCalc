"""
Marketplace Settlement Reconciliation & Cash Flow Calculator for CommerceCalc.
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
from ...core.settlement import SettlementInputs, calculate_settlement


class CashFlowPage(QWidget):
    """Marketplace payout settlement reconciliation and statutory withholding calculator."""

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
            "Reconciles actual bank deposits vs gross order volume for Amazon India, Flipkart, Meesho. "
            "TCS and TDS are statutory tax withholdings creditable against GST and Income Tax returns."
        ))

        # 1. Gross Order Volume
        gross_card, gross_layout = make_card("💰 Gross Bi-Weekly / Monthly Sales")
        self.gross_sales = MoneyInput(max_val=99999999.0)
        self.gross_sales.setValue(250000.0)
        self.gross_sales.valueChanged.connect(self._trigger_calc)
        gross_layout.addWidget(FormFieldRow("Gross Customer Orders (₹)", self.gross_sales))

        self.orders_count = MoneyInput(prefix="", max_val=1000000)
        self.orders_count.setDecimals(0)
        self.orders_count.setValue(250.0)
        self.orders_count.valueChanged.connect(self._trigger_calc)
        gross_layout.addWidget(FormFieldRow("Number of Orders in Statement", self.orders_count))

        self.prod_cost = MoneyInput(max_val=99999999.0)
        self.prod_cost.setValue(95000.0)
        self.prod_cost.valueChanged.connect(self._trigger_calc)
        gross_layout.addWidget(FormFieldRow("Actual Cost of Goods Sold (COGS)", self.prod_cost,
                                             "Total purchase cost of inventory shipped in this payout period."))
        left_layout.addWidget(gross_card)

        # 2. Marketplace Deductions
        mp_card, mp_layout = make_card("🏪 Marketplace Deductions")
        self.mp_commission = MoneyInput(max_val=9999999.0)
        self.mp_commission.setValue(27500.0)
        self.mp_commission.valueChanged.connect(self._trigger_calc)
        mp_layout.addWidget(FormFieldRow("Marketplace Commission", self.mp_commission))

        self.mp_shipping = MoneyInput(max_val=9999999.0)
        self.mp_shipping.setValue(18500.0)
        self.mp_shipping.valueChanged.connect(self._trigger_calc)
        mp_layout.addWidget(FormFieldRow("Logistics / EasyShip Deductions", self.mp_shipping))

        self.closing_fees = MoneyInput(max_val=9999999.0)
        self.closing_fees.setValue(5000.0)
        self.closing_fees.valueChanged.connect(self._trigger_calc)
        mp_layout.addWidget(FormFieldRow("Fixed Closing Fees", self.closing_fees))

        self.seller_promos = MoneyInput(max_val=9999999.0)
        self.seller_promos.setValue(4500.0)
        self.seller_promos.valueChanged.connect(self._trigger_calc)
        mp_layout.addWidget(FormFieldRow("Seller-Funded Lightning Deals / Coupons", self.seller_promos))
        left_layout.addWidget(mp_card)

        # 3. Statutory Withholding & Reserves
        tax_card, tax_layout = make_card("🏛️ Statutory Taxes & Reserves")
        self.tcs_pct = PercentInput()
        self.tcs_pct.setValue(1.0)  # 1% TCS under Sec 52
        self.tcs_pct.valueChanged.connect(self._trigger_calc)
        tax_layout.addWidget(FormFieldRow("GST TCS % (Sec 52 CGST Act)", self.tcs_pct,
                                           "Tax Collected at Source withheld by marketplace. Claimable in GSTR-8."))

        self.tds_pct = PercentInput()
        self.tds_pct.setValue(0.1)  # 0.1% TDS under Sec 194-O
        self.tds_pct.valueChanged.connect(self._trigger_calc)
        tax_layout.addWidget(FormFieldRow("Income Tax TDS % (Sec 194-O)", self.tds_pct,
                                           "TDS withheld by marketplace. Claimable against advance tax in 26AS."))

        self.refunds_clawback = MoneyInput(max_val=9999999.0)
        self.refunds_clawback.setValue(12500.0)
        self.refunds_clawback.valueChanged.connect(self._trigger_calc)
        tax_layout.addWidget(FormFieldRow("Customer Return & Refund Deductions", self.refunds_clawback))

        self.reserve_pct = PercentInput()
        self.reserve_pct.setValue(0.0)  # Rolling reserve
        self.reserve_pct.valueChanged.connect(self._trigger_calc)
        tax_layout.addWidget(FormFieldRow("Platform Rolling Reserve Held %", self.reserve_pct))
        left_layout.addWidget(tax_card)

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
        self.card_net_payout = MetricCard("Net Bank Settlement", "₹–", "success")
        self.card_realization = MetricCard("Realization Rate %", "–%", "default")
        self.card_cash_profit = MetricCard("Cash Profit (after COGS)", "₹–", "success")
        self.card_total_withheld = MetricCard("Taxes Withheld (TCS+TDS)", "₹–", "default")
        metrics_grid.addWidget(self.card_net_payout, 0, 0)
        metrics_grid.addWidget(self.card_realization, 0, 1)
        metrics_grid.addWidget(self.card_cash_profit, 1, 0)
        metrics_grid.addWidget(self.card_total_withheld, 1, 1)
        right_layout.addLayout(metrics_grid)

        # Breakdown
        res_card, res_layout = make_card("Settlement Statement Reconciliation")
        self.row_gross = ResultRow("Gross Customer Order Total", "–")
        self.row_base_fees = ResultRow("Marketplace Fees (Commission + Courier)", "–")
        self.row_gst_fees = ResultRow("18% GST on Marketplace Services", "–", color="#f87171")
        self.row_tcs = ResultRow("GST TCS (Creditable in GST cash ledger)", "–", color="#60a5fa")
        self.row_tds = ResultRow("Income Tax TDS (Creditable in Form 26AS)", "–", color="#60a5fa")
        self.row_refunds = ResultRow("Customer Returns & Refund Adjustments", "–", color="#f87171")
        self.row_reserve = ResultRow("Account Reserve Holdback", "–")
        self.row_net_payout = ResultRow("Expected Net Bank Deposit", "–", bold=True, color="#4ade80")
        self.row_cogs = ResultRow("Inventory Cost of Goods Sold", "–")
        self.row_cash_profit = ResultRow("Net Available Cash Profit", "–", bold=True, color="#4ade80")

        for r in [
            self.row_gross, Divider(),
            self.row_base_fees, self.row_gst_fees,
            self.row_tcs, self.row_tds, self.row_refunds, self.row_reserve,
            Divider(), self.row_net_payout, self.row_cogs, Divider(), self.row_cash_profit
        ]:
            res_layout.addWidget(r)
        right_layout.addWidget(res_card)

        # Notes
        self.notes_card, notes_layout = make_card("Tax Compliance & Form Guidance")
        self.notes_label = QLabel()
        self.notes_label.setWordWrap(True)
        self.notes_label.setStyleSheet("color: #94a3b8; font-size: 12px;")
        notes_layout.addWidget(self.notes_label)
        right_layout.addWidget(self.notes_card)

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
            inputs = SettlementInputs(
                gross_order_sales_inr=self.gross_sales.get_decimal(),
                total_orders_count=max(int(self.orders_count.value()), 1),
                actual_product_cost_inr=self.prod_cost.get_decimal(),
                marketplace_commission_inr=self.mp_commission.get_decimal(),
                marketplace_shipping_deductions_inr=self.mp_shipping.get_decimal(),
                marketplace_fixed_closing_fees_inr=self.closing_fees.get_decimal(),
                seller_funded_promotions_inr=self.seller_promos.get_decimal(),
                gst_tcs_rate_pct=self.tcs_pct.get_decimal(),
                income_tax_tds_rate_pct=self.tds_pct.get_decimal(),
                refunds_deducted_inr=self.refunds_clawback.get_decimal(),
                platform_reserve_held_pct=self.reserve_pct.get_decimal(),
            )
            res = calculate_settlement(inputs)

            p_type = "success" if res.net_bank_settlement > 0 else "danger"
            self.card_net_payout.update_value(fmt_inr(res.net_bank_settlement), p_type)
            self.card_realization.update_value(fmt_pct(res.settlement_realization_pct))
            cp_type = "success" if res.cash_profit_after_inventory_cost > 0 else "danger"
            self.card_cash_profit.update_value(fmt_inr(res.cash_profit_after_inventory_cost, show_sign=True), cp_type)
            self.card_total_withheld.update_value(fmt_inr(res.total_statutory_withholding))

            self.row_gross.set_value(fmt_inr(res.gross_sales))
            self.row_base_fees.set_value(fmt_inr(res.total_platform_fees_before_gst))
            self.row_gst_fees.set_value(f"− {fmt_inr(res.gst_on_platform_fees)}", "#f87171")
            self.row_tcs.set_value(f"− {fmt_inr(res.tcs_withheld)} (1% TCS)", "#60a5fa")
            self.row_tds.set_value(f"− {fmt_inr(res.tds_withheld)} (0.1% TDS)", "#60a5fa")
            self.row_refunds.set_value(f"− {fmt_inr(res.refunds_and_returns_clawback)}", "#f87171")
            self.row_reserve.set_value(f"− {fmt_inr(res.reserve_withheld)}")
            self.row_net_payout.set_value(fmt_inr(res.net_bank_settlement), "#4ade80" if res.net_bank_settlement > 0 else "#f87171")
            self.row_cogs.set_value(f"− {fmt_inr(inputs.actual_product_cost_inr)}")
            self.row_cash_profit.set_value(fmt_inr(res.cash_profit_after_inventory_cost, show_sign=True), "#4ade80" if res.cash_profit_after_inventory_cost > 0 else "#f87171")

            self.notes_label.setText("\n".join(f"• {n}" for n in res.accounting_notes))

            if res.warnings:
                self.warnings_label.setText("⚠ " + " | ".join(res.warnings))
            else:
                self.warnings_label.setText("")
        except Exception as e:
            self.warnings_label.setText(f"Error: {str(e)}")
