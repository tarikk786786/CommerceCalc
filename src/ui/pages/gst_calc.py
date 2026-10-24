"""
GST Tax Breakdown Calculator page.
"""
from decimal import Decimal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QScrollArea,
    QPushButton, QLabel, QComboBox, QGridLayout, QCheckBox
)
from PySide6.QtCore import Qt, QTimer
from ..widgets.common import (
    MoneyInput, PercentInput, MetricCard, SectionTitle, Divider,
    ResultRow, DisclaimerBox, make_card, fmt_inr, FormFieldRow
)
from ...core.tax import GSTConfig, GSTBreakdown, calculate_gst, GST_RATE_PRESETS
from ...core.money import to_decimal


class GSTCalculatorPage(QWidget):
    """Indian GST breakdown calculator."""

    def __init__(self, db_session=None, parent=None):
        super().__init__(parent)
        self._calc_timer = QTimer()
        self._calc_timer.setSingleShot(True)
        self._calc_timer.setInterval(300)
        self._calc_timer.timeout.connect(self._calculate)
        self._setup_ui()

    def _setup_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(24, 16, 24, 24)
        layout.setSpacing(16)

        layout.addWidget(DisclaimerBox(
            "IMPORTANT: This calculator provides estimates only. "
            "GST rates shown are presets for convenience — the correct rate for your specific "
            "product/service must be verified against CBIC notifications. This is NOT a "
            "substitute for official GST filing software or a tax professional."
        ))

        # Inputs card
        inputs_card, inputs_layout = make_card("GST Calculation Inputs")

        self.amount_input = MoneyInput(max_val=9999999.99)
        self.amount_input.valueChanged.connect(self._trigger_calc)
        inputs_layout.addWidget(FormFieldRow("Amount", self.amount_input,
                                              "Enter the price amount"))

        self.gst_inclusive = QCheckBox("Amount is GST-inclusive (reverse calculation)")
        self.gst_inclusive.stateChanged.connect(self._trigger_calc)
        inputs_layout.addWidget(self.gst_inclusive)

        self.gst_rate_combo = QComboBox()
        for preset in GST_RATE_PRESETS:
            self.gst_rate_combo.addItem(preset["label"], userData=preset["rate"])
        self.gst_rate_combo.setCurrentIndex(3)
        self.gst_rate_combo.currentIndexChanged.connect(self._trigger_calc)
        inputs_layout.addWidget(FormFieldRow("GST Rate", self.gst_rate_combo))

        self.is_intra_state = QCheckBox("Intra-state sale (CGST + SGST)")
        self.is_intra_state.setChecked(True)
        self.is_intra_state.stateChanged.connect(self._trigger_calc)
        inputs_layout.addWidget(self.is_intra_state)

        self.itc_eligible = QCheckBox("Input Tax Credit eligible")
        self.itc_eligible.setChecked(True)
        self.itc_eligible.stateChanged.connect(self._trigger_calc)
        inputs_layout.addWidget(self.itc_eligible)

        self.purchase_gst = MoneyInput()
        self.purchase_gst.valueChanged.connect(self._trigger_calc)
        inputs_layout.addWidget(FormFieldRow("GST Paid on Purchase", self.purchase_gst,
                                              "Used for ITC calculation"))

        self.quantity = MoneyInput(prefix="× ", max_val=100000)
        self.quantity.setValue(1)
        self.quantity.valueChanged.connect(self._trigger_calc)
        inputs_layout.addWidget(FormFieldRow("Quantity", self.quantity))

        calc_btn = QPushButton("Calculate GST")
        calc_btn.setObjectName("primary_btn")
        calc_btn.clicked.connect(self._calculate)
        inputs_layout.addWidget(calc_btn)

        layout.addWidget(inputs_card)

        # Results cards
        metrics_row = QHBoxLayout()
        self.card_taxable = MetricCard("Taxable Value", "₹–")
        self.card_gst = MetricCard("Output GST", "₹–")
        self.card_total = MetricCard("Customer Total", "₹–")
        metrics_row.addWidget(self.card_taxable)
        metrics_row.addWidget(self.card_gst)
        metrics_row.addWidget(self.card_total)
        layout.addLayout(metrics_row)

        results_card, results_layout = make_card("GST Breakdown")
        self.row_taxable = ResultRow("Taxable Value", "–")
        self.row_cgst = ResultRow("CGST (50% of GST)", "–")
        self.row_sgst = ResultRow("SGST (50% of GST)", "–")
        self.row_igst = ResultRow("IGST (Inter-state)", "–")
        self.row_output_gst = ResultRow("Total Output GST", "–", bold=True)
        self.row_total_incl = ResultRow("Customer-Facing Total", "–", bold=True, color="#4ade80")
        self.row_itc_recoverable = ResultRow("ITC Recoverable", "–")
        self.row_net_gst_expense = ResultRow("Net GST Expense (after ITC)", "–")
        for row in [
            self.row_taxable, self.row_cgst, self.row_sgst, self.row_igst,
            self.row_output_gst, Divider(), self.row_total_incl, Divider(),
            self.row_itc_recoverable, self.row_net_gst_expense
        ]:
            results_layout.addWidget(row)
        layout.addWidget(results_card)

        # Warning card
        self.warning_card, warning_layout = make_card("⚠ Notes")
        self.warning_label = QLabel()
        self.warning_label.setWordWrap(True)
        self.warning_label.setStyleSheet("color: #fb923c; font-size: 12px;")
        warning_layout.addWidget(self.warning_label)
        self.warning_card.setVisible(False)
        layout.addWidget(self.warning_card)

        layout.addStretch()
        scroll.setWidget(content)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)

        # Initial calc
        self._calculate()

    def _trigger_calc(self):
        self._calc_timer.start()

    def _calculate(self):
        try:
            amount = self.amount_input.get_decimal()
            rate = Decimal(str(self.gst_rate_combo.currentData() or "18"))
            qty = max(int(self.quantity.value()), 1)

            config = GSTConfig(
                rate_pct=rate,
                inclusive=self.gst_inclusive.isChecked(),
                is_intra_state=self.is_intra_state.isChecked(),
                input_tax_credit_eligible=self.itc_eligible.isChecked(),
                purchase_gst_paid=self.purchase_gst.get_decimal(),
            )

            result = calculate_gst(amount, config, qty)
            self._update_results(result)

        except Exception as e:
            self.warning_label.setText(f"Error: {str(e)}")
            self.warning_card.setVisible(True)

    def _update_results(self, result: GSTBreakdown):
        self.card_taxable.update_value(fmt_inr(result.taxable_value))
        self.card_gst.update_value(fmt_inr(result.output_gst))
        self.card_total.update_value(fmt_inr(result.total_inclusive))

        self.row_taxable.set_value(fmt_inr(result.taxable_value))
        self.row_cgst.set_value(fmt_inr(result.cgst))
        self.row_sgst.set_value(fmt_inr(result.sgst))
        self.row_igst.set_value(fmt_inr(result.igst))
        self.row_output_gst.set_value(fmt_inr(result.output_gst))
        self.row_total_incl.set_value(fmt_inr(result.total_inclusive))
        self.row_itc_recoverable.set_value(fmt_inr(result.itc_recoverable))
        self.row_net_gst_expense.set_value(fmt_inr(result.net_gst_expense))

        if result.warning:
            self.warning_label.setText(result.warning)
            self.warning_card.setVisible(True)
        else:
            self.warning_card.setVisible(False)
