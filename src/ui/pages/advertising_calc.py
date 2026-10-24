"""
Advertising & ROAS Calculator page for CommerceCalc.
"""
from decimal import Decimal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QScrollArea,
    QPushButton, QLabel, QGridLayout, QSplitter
)
from PySide6.QtCore import Qt, QTimer
from ..widgets.common import (
    MoneyInput, PercentInput, MetricCard, Divider,
    ResultRow, DisclaimerBox, InfoBox, make_card, fmt_inr, fmt_pct,
    FormFieldRow
)
from ...core.advertising import AdvertisingInputs, calculate_advertising
from ...core.money import to_decimal


class AdvertisingPage(QWidget):
    """Advertising metrics and ROAS calculator."""

    def __init__(self, db_session=None, parent=None):
        super().__init__(parent)
        self._calc_timer = QTimer()
        self._calc_timer.setSingleShot(True)
        self._calc_timer.setInterval(400)
        self._calc_timer.timeout.connect(self._calculate)
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        splitter = QSplitter(Qt.Horizontal)

        left = QWidget()
        left_scroll = QScrollArea()
        left_scroll.setWidgetResizable(True)
        left_scroll.setWidget(left)
        left_scroll.setFrameShape(QFrame.NoFrame)
        left_scroll.setMaximumWidth(520)

        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(20, 16, 20, 20)
        left_layout.setSpacing(16)

        self._build_inputs(left_layout)
        calc_btn = QPushButton("Calculate Advertising Metrics")
        calc_btn.setObjectName("primary_btn")
        calc_btn.clicked.connect(self._calculate)
        left_layout.addWidget(calc_btn)

        self.btn_ai_ad = QPushButton("✨ AI ROAS & Spend Diagnostics (Gemini 2.5)")
        self.btn_ai_ad.setMinimumHeight(40)
        self.btn_ai_ad.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4f46e5, stop:1 #7c3aed);
                color: #ffffff;
                font-weight: bold;
                border: none;
                border-radius: 6px;
                padding: 6px 14px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4338ca, stop:1 #6d28d9);
            }
        """)
        self.btn_ai_ad.clicked.connect(self._run_ai_ad_audit)
        left_layout.addWidget(self.btn_ai_ad)

        left_layout.addStretch()

        right = QWidget()
        right_scroll = QScrollArea()
        right_scroll.setWidgetResizable(True)
        right_scroll.setWidget(right)
        right_scroll.setFrameShape(QFrame.NoFrame)

        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(20, 16, 20, 20)
        right_layout.setSpacing(16)
        self._build_results(right_layout)

        splitter.addWidget(left_scroll)
        splitter.addWidget(right_scroll)
        splitter.setSizes([480, 580])
        main_layout.addWidget(splitter)

    def _build_inputs(self, layout):
        card, cl = make_card("📢 Campaign Inputs")
        cl.addWidget(DisclaimerBox(
            "ROAS is NOT the same as profit. High ROAS with low margins can still lose money. "
            "Always verify contribution margin before advertising."
        ))

        self.ad_spend = MoneyInput(max_val=9999999.99)
        self.ad_spend.valueChanged.connect(self._trigger_calc)
        cl.addWidget(FormFieldRow("Total Ad Spend", self.ad_spend))

        self.impressions = MoneyInput(prefix="", max_val=999999999)
        self.impressions.setDecimals(0)
        self.impressions.valueChanged.connect(self._trigger_calc)
        cl.addWidget(FormFieldRow("Impressions", self.impressions))

        self.clicks = MoneyInput(prefix="", max_val=999999999)
        self.clicks.setDecimals(0)
        self.clicks.valueChanged.connect(self._trigger_calc)
        cl.addWidget(FormFieldRow("Clicks", self.clicks))

        self.attributed_orders = MoneyInput(prefix="", max_val=999999)
        self.attributed_orders.setDecimals(0)
        self.attributed_orders.valueChanged.connect(self._trigger_calc)
        cl.addWidget(FormFieldRow("Attributed Orders", self.attributed_orders))

        self.attributed_revenue = MoneyInput(max_val=9999999.99)
        self.attributed_revenue.valueChanged.connect(self._trigger_calc)
        cl.addWidget(FormFieldRow("Attributed Revenue (excl. GST)", self.attributed_revenue))

        self.net_revenue = MoneyInput(max_val=9999999.99)
        self.net_revenue.valueChanged.connect(self._trigger_calc)
        cl.addWidget(FormFieldRow("Total Net Revenue (excl. GST)", self.net_revenue,
                                   "Overall store revenue, not just attributed"))

        self.cm_pct = PercentInput()
        self.cm_pct.setValue(35.0)
        self.cm_pct.valueChanged.connect(self._trigger_calc)
        cl.addWidget(FormFieldRow("Contribution Margin Before Adv %", self.cm_pct,
                                   "Margin before deducting advertising costs"))

        layout.addWidget(card)

    def _build_results(self, layout):
        metrics = QGridLayout()
        metrics.setSpacing(12)
        self.card_roas = MetricCard("ROAS", "–")
        self.card_breakeven_roas = MetricCard("Break-Even ROAS", "–")
        self.card_cac = MetricCard("Customer Acquisition Cost", "₹–")
        self.card_profit_after_adv = MetricCard("Contribution After Adv", "₹–")
        metrics.addWidget(self.card_roas, 0, 0)
        metrics.addWidget(self.card_breakeven_roas, 0, 1)
        metrics.addWidget(self.card_cac, 1, 0)
        metrics.addWidget(self.card_profit_after_adv, 1, 1)
        layout.addLayout(metrics)

        card1, l1 = make_card("Efficiency Metrics")
        self.row_cpm = ResultRow("CPM (per 1000 impressions)", "–")
        self.row_cpc = ResultRow("CPC (Cost per Click)", "–")
        self.row_ctr = ResultRow("CTR %", "–")
        self.row_cvr = ResultRow("Conversion Rate %", "–")
        self.row_cpa = ResultRow("Cost per Acquisition", "–")
        self.row_aov = ResultRow("Average Order Value", "–")
        for r in [self.row_cpm, self.row_cpc, self.row_ctr, self.row_cvr,
                  self.row_cpa, self.row_aov]:
            l1.addWidget(r)
        layout.addWidget(card1)

        card2, l2 = make_card("ROAS & Profitability")
        self.row_roas = ResultRow("ROAS", "–", bold=True)
        self.row_be_roas = ResultRow("Break-Even ROAS", "–")
        self.row_acos = ResultRow("ACoS %", "–", tooltip="Ad Cost of Sales (ads / attributed rev)")
        self.row_tacos = ResultRow("TACoS %", "–", tooltip="Total ACoS (ads / total net revenue)")
        self.row_contrib_before = ResultRow("Contribution Profit (Before Adv)", "–")
        self.row_contrib_after = ResultRow("Contribution Profit (After Adv)", "–", bold=True)
        self.row_profit_per_cust = ResultRow("Profit per Acquired Customer", "–")
        for r in [self.row_roas, self.row_be_roas, self.row_acos, self.row_tacos,
                  Divider(), self.row_contrib_before, self.row_contrib_after,
                  self.row_profit_per_cust]:
            l2.addWidget(r)
        layout.addWidget(card2)

        card3, l3 = make_card("Break-Even Analysis")
        self.row_max_cac = ResultRow("Max Allowable CAC", "–")
        self.row_max_cpc = ResultRow("Max CPC (at current CVR)", "–")
        self.row_target_roas = ResultRow("Target ROAS (to not lose money)", "–")
        self.row_req_cvr = ResultRow("Required Conversion Rate %", "–")
        self.row_req_rev = ResultRow("Required Revenue to Break Even", "–")
        self.row_req_orders = ResultRow("Required Orders to Recover Spend", "–")
        for r in [self.row_max_cac, self.row_max_cpc, self.row_target_roas,
                  self.row_req_cvr, self.row_req_rev, self.row_req_orders]:
            l3.addWidget(r)
        layout.addWidget(card3)

        self.warnings_label = QLabel()
        self.warnings_label.setWordWrap(True)
        self.warnings_label.setStyleSheet("color: #fb923c; font-size: 12px; padding: 8px;")
        layout.addWidget(self.warnings_label)
        layout.addStretch()

    def _trigger_calc(self):
        self._calc_timer.start()

    def _calculate(self):
        try:
            inputs = AdvertisingInputs(
                ad_spend=self.ad_spend.get_decimal(),
                impressions=int(self.impressions.value()),
                clicks=int(self.clicks.value()),
                attributed_orders=int(self.attributed_orders.value()),
                attributed_revenue=self.attributed_revenue.get_decimal(),
                net_revenue=self.net_revenue.get_decimal(),
                contribution_margin_before_adv=self.cm_pct.get_decimal(),
            )
            result = calculate_advertising(inputs)
            self._update_results(result)
        except Exception as e:
            self.warnings_label.setText(f"Error: {str(e)}")

    def _update_results(self, result):
        self._latest_result = result
        roas_type = "success" if result.roas >= result.break_even_roas > 0 else "danger"
        self.card_roas.update_value(
            f"{result.roas:.2f}x" if result.roas > 0 else "–", roas_type
        )
        self.card_breakeven_roas.update_value(
            f"{result.break_even_roas:.2f}x" if result.break_even_roas > 0 else "–"
        )
        self.card_cac.update_value(fmt_inr(result.cost_per_acquisition))
        contrib_type = "success" if result.contribution_profit_after_adv >= 0 else "danger"
        self.card_profit_after_adv.update_value(
            fmt_inr(result.contribution_profit_after_adv, show_sign=True), contrib_type
        )

        self.row_cpm.set_value(fmt_inr(result.cpm))
        self.row_cpc.set_value(fmt_inr(result.cpc))
        self.row_ctr.set_value(fmt_pct(result.ctr_pct))
        self.row_cvr.set_value(fmt_pct(result.conversion_rate_pct))
        self.row_cpa.set_value(fmt_inr(result.cost_per_acquisition))
        self.row_aov.set_value(fmt_inr(result.average_order_value))

        self.row_roas.set_value(f"{result.roas:.2f}x" if result.roas > 0 else "–")
        self.row_be_roas.set_value(
            f"{result.break_even_roas:.2f}x" if result.break_even_roas > 0 else "Undefined"
        )
        self.row_acos.set_value(fmt_pct(result.acos_pct))
        self.row_tacos.set_value(fmt_pct(result.tacos_pct))
        self.row_contrib_before.set_value(fmt_inr(result.contribution_profit_before_adv))
        color = "#4ade80" if result.contribution_profit_after_adv >= 0 else "#f87171"
        self.row_contrib_after.set_value(
            fmt_inr(result.contribution_profit_after_adv, show_sign=True), color
        )
        self.row_profit_per_cust.set_value(fmt_inr(result.profit_per_acquired_customer))

        self.row_max_cac.set_value(fmt_inr(result.max_allowable_cac))
        self.row_max_cpc.set_value(fmt_inr(result.max_cpc))
        self.row_target_roas.set_value(
            f"{result.target_roas:.2f}x" if result.target_roas > 0 else "–"
        )
        self.row_req_cvr.set_value(fmt_pct(result.required_conversion_rate_pct))
        self.row_req_rev.set_value(fmt_inr(result.required_revenue_to_break_even))
        self.row_req_orders.set_value(f"{result.required_orders_to_recover_spend:.1f}")

        if result.warnings:
            self.warnings_label.setText("⚠ " + " | ".join(result.warnings))
        else:
            self.warnings_label.setText("")

    def _run_ai_ad_audit(self):
        """Run cloud LLM advertising diagnostics."""
        from ..widgets.ai_dialog import AIDiagnosticDialog
        from ...services.ai_service import CommerceCalcAI

        if not hasattr(self, "_latest_result") or not self._latest_result:
            self._calculate()

        res = getattr(self, "_latest_result", None)
        data = {
            "ad_spend": str(self.ad_spend.get_decimal()),
            "impressions": str(int(self.impressions.value())),
            "clicks": str(int(self.clicks.value())),
            "ctr": str(getattr(res, "ctr_pct", "0")),
            "cpc": str(getattr(res, "cpc", "0")),
            "orders": str(int(self.attributed_orders.value())),
            "cvr": str(getattr(res, "conversion_rate_pct", "0")),
            "attributed_revenue": str(self.attributed_revenue.get_decimal()),
            "roas": str(getattr(res, "roas", "0")),
            "be_roas": str(getattr(res, "break_even_roas", "0")),
            "margin_before_ads": str(self.cm_pct.get_decimal()),
        }

        ai = CommerceCalcAI()
        dlg = AIDiagnosticDialog(
            "AI Advertising & ROAS Diagnostics",
            lambda: ai.optimize_advertising_roas(data),
            parent=self
        )
        dlg.exec()
