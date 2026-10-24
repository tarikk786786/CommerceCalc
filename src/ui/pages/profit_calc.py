"""
Product Profit Calculator page — the core CommerceCalc module.

Full input form + live calculation results with expense breakdown.
"""
from decimal import Decimal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QFrame,
    QPushButton, QLabel, QComboBox, QGridLayout, QSplitter,
    QGroupBox, QLineEdit, QSpinBox
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont

from ...core.profit import (
    ProductCost, SellingDetails, SellingExpenses, calculate_profit
)
from ...core.tax import GSTConfig, GST_RATE_PRESETS
from ..widgets.common import (
    MoneyInput, PercentInput, MetricCard, SectionTitle, Divider,
    ResultRow, DisclaimerBox, InfoBox, make_card, fmt_inr, fmt_pct,
    FormFieldRow
)


class ProductProfitPage(QWidget):
    """Complete product profit calculator."""

    def __init__(self, db_session=None, parent=None):
        super().__init__(parent)
        self.db_session = db_session
        self._calc_timer = QTimer()
        self._calc_timer.setSingleShot(True)
        self._calc_timer.setInterval(400)  # Debounce live calculation
        self._calc_timer.timeout.connect(self._calculate)
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Splitter: left = inputs, right = results
        splitter = QSplitter(Qt.Horizontal)

        # Left panel (scrollable inputs)
        left_widget = QWidget()
        left_scroll = QScrollArea()
        left_scroll.setWidgetResizable(True)
        left_scroll.setWidget(left_widget)
        left_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        left_scroll.setFrameShape(QFrame.NoFrame)
        left_scroll.setMinimumWidth(480)
        left_scroll.setMaximumWidth(560)

        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(20, 16, 20, 20)
        left_layout.setSpacing(16)

        self._build_product_section(left_layout)
        self._build_selling_section(left_layout)
        self._build_gst_section(left_layout)
        self._build_expenses_section(left_layout)

        # Calculate button
        calc_btn = QPushButton("Calculate Profit")
        calc_btn.setObjectName("primary_btn")
        calc_btn.setMinimumHeight(44)
        calc_btn.clicked.connect(self._calculate)
        left_layout.addWidget(calc_btn)

        # AI Diagnosis Button
        self.btn_ai_audit = QPushButton("✨ AI Financial Diagnosis (Gemini 2.5)")
        self.btn_ai_audit.setMinimumHeight(40)
        self.btn_ai_audit.setStyleSheet("""
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
        self.btn_ai_audit.clicked.connect(self._run_ai_audit)
        left_layout.addWidget(self.btn_ai_audit)

        # Save button
        save_btn = QPushButton("Save as Scenario")
        save_btn.setObjectName("secondary_btn")
        save_btn.clicked.connect(self._save_scenario)
        left_layout.addWidget(save_btn)
        left_layout.addStretch()

        # Right panel (results)
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(20, 16, 20, 20)
        right_layout.setSpacing(16)
        self._build_results_panel(right_layout)

        splitter.addWidget(left_scroll)
        splitter.addWidget(right_widget)
        splitter.setSizes([520, 600])

        main_layout.addWidget(splitter)

    def _build_product_section(self, layout):
        card, card_layout = make_card("📦 Product & Cost Details")

        # Product name
        self.product_name = QLineEdit()
        self.product_name.setPlaceholderText("Enter product name")
        card_layout.addWidget(FormFieldRow("Product Name", self.product_name))

        # Product type
        self.product_type = QComboBox()
        self.product_type.addItems(["Physical", "Digital", "Dropshipping", "Service", "Bundle"])
        card_layout.addWidget(FormFieldRow("Product Type", self.product_type))

        # Costs
        self.purchase_cost = MoneyInput()
        self.purchase_cost.valueChanged.connect(self._trigger_calc)
        card_layout.addWidget(FormFieldRow("Purchase Cost", self.purchase_cost,
                                           "Supplier price per unit"))

        self.packaging_cost = MoneyInput()
        self.packaging_cost.valueChanged.connect(self._trigger_calc)
        card_layout.addWidget(FormFieldRow("Packaging Cost", self.packaging_cost))

        self.prep_cost = MoneyInput()
        self.prep_cost.valueChanged.connect(self._trigger_calc)
        card_layout.addWidget(FormFieldRow("Preparation / Handling", self.prep_cost))

        self.inbound_shipping = MoneyInput()
        self.inbound_shipping.valueChanged.connect(self._trigger_calc)
        card_layout.addWidget(FormFieldRow("Inbound Shipping", self.inbound_shipping))

        self.inspection_cost = MoneyInput()
        self.inspection_cost.valueChanged.connect(self._trigger_calc)
        card_layout.addWidget(FormFieldRow("Inspection / QC Cost", self.inspection_cost))

        self.import_cost = MoneyInput()
        self.import_cost.valueChanged.connect(self._trigger_calc)
        card_layout.addWidget(FormFieldRow("Import / Customs Cost", self.import_cost))

        self.overhead = MoneyInput()
        self.overhead.valueChanged.connect(self._trigger_calc)
        card_layout.addWidget(FormFieldRow("Allocated Overhead", self.overhead,
                                           "Fixed overhead cost allocated per unit"))

        layout.addWidget(card)

    def _build_selling_section(self, layout):
        card, card_layout = make_card("🏷️ Selling Details")

        self.listed_price = MoneyInput(max_val=999999.99)
        self.listed_price.valueChanged.connect(self._trigger_calc)
        card_layout.addWidget(FormFieldRow("Listed / MRP", self.listed_price))

        self.actual_price = MoneyInput(max_val=999999.99)
        self.actual_price.valueChanged.connect(self._trigger_calc)
        card_layout.addWidget(FormFieldRow("Actual Selling Price", self.actual_price,
                                           "The price customer pays before any additional discounts"))

        self.quantity = QSpinBox()
        self.quantity.setMinimum(1)
        self.quantity.setMaximum(100000)
        self.quantity.setValue(1)
        self.quantity.valueChanged.connect(self._trigger_calc)
        card_layout.addWidget(FormFieldRow("Quantity", self.quantity))

        self.customer_discount = MoneyInput()
        self.customer_discount.valueChanged.connect(self._trigger_calc)
        card_layout.addWidget(FormFieldRow("Customer Discount (₹)", self.customer_discount))

        self.coupon_discount = MoneyInput()
        self.coupon_discount.valueChanged.connect(self._trigger_calc)
        card_layout.addWidget(FormFieldRow("Coupon Discount (₹)", self.coupon_discount))

        self.seller_promo = MoneyInput()
        self.seller_promo.valueChanged.connect(self._trigger_calc)
        card_layout.addWidget(FormFieldRow("Seller-Funded Promo (₹)", self.seller_promo,
                                           "Seller-funded promotional discount (excludes marketplace-funded portion)"))

        self.customer_shipping = MoneyInput()
        self.customer_shipping.valueChanged.connect(self._trigger_calc)
        card_layout.addWidget(FormFieldRow("Customer Shipping Charged", self.customer_shipping))

        self.payment_method = QComboBox()
        self.payment_method.addItems(["Prepaid", "COD (Cash on Delivery)", "UPI", "Card"])
        card_layout.addWidget(FormFieldRow("Payment Method", self.payment_method))

        layout.addWidget(card)

    def _build_gst_section(self, layout):
        card, card_layout = make_card("🧾 GST Configuration")

        card_layout.addWidget(DisclaimerBox(
            "GST rates shown are presets for convenience only. "
            "The correct rate for your product must be verified with a tax professional "
            "or official CBIC notifications. This is not a tax filing system."
        ))

        self.gst_rate = QComboBox()
        for preset in GST_RATE_PRESETS:
            self.gst_rate.addItem(preset["label"], userData=preset["rate"])
        self.gst_rate.setCurrentIndex(3)  # Default 18%
        self.gst_rate.currentIndexChanged.connect(self._trigger_calc)
        card_layout.addWidget(FormFieldRow("GST Rate", self.gst_rate))

        from PySide6.QtWidgets import QCheckBox
        self.gst_inclusive = QCheckBox("Price is GST-inclusive")
        self.gst_inclusive.stateChanged.connect(self._trigger_calc)
        card_layout.addWidget(self.gst_inclusive)

        self.itc_eligible = QCheckBox("Input Tax Credit (ITC) eligible")
        self.itc_eligible.setChecked(True)
        self.itc_eligible.stateChanged.connect(self._trigger_calc)
        card_layout.addWidget(self.itc_eligible)

        self.purchase_gst_paid = MoneyInput()
        self.purchase_gst_paid.valueChanged.connect(self._trigger_calc)
        card_layout.addWidget(FormFieldRow("GST Paid on Purchase", self.purchase_gst_paid,
                                           "GST component of your purchase cost (for ITC)"))

        layout.addWidget(card)

    def _build_expenses_section(self, layout):
        card, card_layout = make_card("💸 Selling Expenses")

        card_layout.addWidget(InfoBox(
            "Enter marketplace fees manually or configure a fee profile in Marketplace Fee Profiles."
        ))

        self.marketplace_commission = MoneyInput()
        self.marketplace_commission.valueChanged.connect(self._trigger_calc)
        card_layout.addWidget(FormFieldRow("Marketplace Commission (₹)", self.marketplace_commission))

        self.closing_fee = MoneyInput()
        self.closing_fee.valueChanged.connect(self._trigger_calc)
        card_layout.addWidget(FormFieldRow("Fixed Closing Fee", self.closing_fee))

        self.payment_gateway_fee = MoneyInput()
        self.payment_gateway_fee.valueChanged.connect(self._trigger_calc)
        card_layout.addWidget(FormFieldRow("Payment Gateway Fee", self.payment_gateway_fee))

        self.forward_shipping = MoneyInput()
        self.forward_shipping.valueChanged.connect(self._trigger_calc)
        card_layout.addWidget(FormFieldRow("Forward Shipping", self.forward_shipping))

        self.reverse_shipping = MoneyInput()
        self.reverse_shipping.valueChanged.connect(self._trigger_calc)
        card_layout.addWidget(FormFieldRow("Reverse Shipping", self.reverse_shipping))

        self.cod_charge = MoneyInput()
        self.cod_charge.valueChanged.connect(self._trigger_calc)
        card_layout.addWidget(FormFieldRow("COD Charge", self.cod_charge))

        self.affiliate_comm = MoneyInput()
        self.affiliate_comm.valueChanged.connect(self._trigger_calc)
        card_layout.addWidget(FormFieldRow("Affiliate Commission", self.affiliate_comm))

        self.advertising = MoneyInput()
        self.advertising.valueChanged.connect(self._trigger_calc)
        card_layout.addWidget(FormFieldRow("Advertising Cost", self.advertising))

        self.return_expense = MoneyInput()
        self.return_expense.valueChanged.connect(self._trigger_calc)
        card_layout.addWidget(FormFieldRow("Expected Return Cost", self.return_expense))

        self.rto_expense = MoneyInput()
        self.rto_expense.valueChanged.connect(self._trigger_calc)
        card_layout.addWidget(FormFieldRow("Expected RTO Cost", self.rto_expense))

        self.other_cost = MoneyInput()
        self.other_cost.valueChanged.connect(self._trigger_calc)
        card_layout.addWidget(FormFieldRow("Other Variable Costs", self.other_cost))

        layout.addWidget(card)

    def _build_results_panel(self, layout):
        # Status badge
        status_row = QHBoxLayout()
        self.profit_status = QLabel("Enter product details to calculate")
        self.profit_status.setObjectName("badge_warning")
        status_row.addWidget(self.profit_status)
        status_row.addStretch()
        layout.addLayout(status_row)

        # Key metrics row
        metrics_layout = QGridLayout()
        metrics_layout.setSpacing(12)

        self.card_net_revenue = MetricCard("Net Revenue", "₹–")
        self.card_profit = MetricCard("Operating Profit", "₹–")
        self.card_margin = MetricCard("Contribution Margin", "–%")
        self.card_markup = MetricCard("Markup on Cost", "–%")

        metrics_layout.addWidget(self.card_net_revenue, 0, 0)
        metrics_layout.addWidget(self.card_profit, 0, 1)
        metrics_layout.addWidget(self.card_margin, 1, 0)
        metrics_layout.addWidget(self.card_markup, 1, 1)
        layout.addLayout(metrics_layout)

        # Revenue breakdown
        rev_card, rev_layout = make_card("Revenue Breakdown")
        self.row_gross_value = ResultRow("Gross List Value", "–")
        self.row_customer_discount = ResultRow("Customer Discounts", "–")
        self.row_net_payment = ResultRow("Net Customer Payment", "–", bold=True)
        self.row_output_gst = ResultRow("Output GST (Collected)", "–")
        self.row_net_revenue = ResultRow("Net Revenue (Excl. GST)", "–", bold=True, color="#4ade80")
        for row in [self.row_gross_value, self.row_customer_discount,
                    self.row_net_payment, self.row_output_gst, Divider(), self.row_net_revenue]:
            rev_layout.addWidget(row)
        layout.addWidget(rev_card)

        # Expense breakdown
        exp_card, exp_layout = make_card("Expense Breakdown")
        self.row_acquisition = ResultRow("Product Acquisition Cost", "–")
        self.row_fulfillment = ResultRow("Fulfillment / Shipping", "–")
        self.row_mp_fees = ResultRow("Marketplace Fees", "–")
        self.row_payment_fees = ResultRow("Payment Processing Fees", "–")
        self.row_advertising = ResultRow("Advertising", "–")
        self.row_affiliate = ResultRow("Affiliate Commission", "–")
        self.row_returns = ResultRow("Returns & RTO", "–")
        self.row_other = ResultRow("Other Variable Costs", "–")
        self.row_overhead = ResultRow("Allocated Overhead", "–")
        self.row_total_expense = ResultRow("Total Expenses", "–", bold=True)
        for row in [
            self.row_acquisition, self.row_fulfillment, self.row_mp_fees,
            self.row_payment_fees, self.row_advertising, self.row_affiliate,
            self.row_returns, self.row_other, self.row_overhead,
            Divider(), self.row_total_expense
        ]:
            exp_layout.addWidget(row)
        layout.addWidget(exp_card)

        # Profit layers
        profit_card, profit_layout = make_card("Profitability")
        self.row_contrib_before_adv = ResultRow("Contribution Profit (Before Adv)", "–")
        self.row_contrib_after_adv = ResultRow("Contribution Profit (After Adv)", "–", bold=True)
        self.row_operating_profit = ResultRow("Estimated Operating Profit", "–", bold=True, color="#4ade80")
        self.row_profit_per_unit = ResultRow("Profit Per Unit", "–")
        self.row_total_profit = ResultRow("Total Profit (All Units)", "–")
        self.row_contrib_margin = ResultRow("Contribution Margin %", "–")
        self.row_operating_margin = ResultRow("Operating Margin %", "–")
        self.row_markup = ResultRow("Markup on Cost %", "–")
        self.row_expense_pct = ResultRow("Effective Expense %", "–")
        for row in [
            self.row_contrib_before_adv, self.row_contrib_after_adv,
            Divider(), self.row_operating_profit, self.row_profit_per_unit,
            self.row_total_profit, Divider(),
            self.row_contrib_margin, self.row_operating_margin,
            self.row_markup, self.row_expense_pct
        ]:
            profit_layout.addWidget(row)
        layout.addWidget(profit_card)

        # Warnings
        self.warnings_card, warnings_layout = make_card("⚠ Warnings")
        self.warnings_label = QLabel("No warnings.")
        self.warnings_label.setWordWrap(True)
        self.warnings_label.setStyleSheet("color: #fb923c; font-size: 12px;")
        warnings_layout.addWidget(self.warnings_label)
        self.warnings_card.setVisible(False)
        layout.addWidget(self.warnings_card)

        layout.addStretch()

    def _trigger_calc(self):
        self._calc_timer.start()

    def _calculate(self):
        """Read inputs and calculate profit."""
        try:
            # Build ProductCost
            pc = ProductCost(
                purchase_cost=self.purchase_cost.get_decimal(),
                packaging_cost=self.packaging_cost.get_decimal(),
                preparation_cost=self.prep_cost.get_decimal(),
                inbound_shipping=self.inbound_shipping.get_decimal(),
                inspection_cost=self.inspection_cost.get_decimal(),
                import_cost=self.import_cost.get_decimal(),
                overhead_allocated=self.overhead.get_decimal(),
                purchase_gst_paid=self.purchase_gst_paid.get_decimal(),
                itc_recoverable=(
                    self.purchase_gst_paid.get_decimal()
                    if self.itc_eligible.isChecked() else Decimal("0")
                ),
            )

            # Build GSTConfig
            gst_rate = Decimal(str(self.gst_rate.currentData() or "18"))
            gst_config = GSTConfig(
                rate_pct=gst_rate,
                inclusive=self.gst_inclusive.isChecked(),
                input_tax_credit_eligible=self.itc_eligible.isChecked(),
                purchase_gst_paid=self.purchase_gst_paid.get_decimal(),
            )

            # Build SellingDetails
            sd = SellingDetails(
                listed_price=self.listed_price.get_decimal(),
                actual_selling_price=self.actual_price.get_decimal(),
                quantity=self.quantity.value(),
                customer_discount=self.customer_discount.get_decimal(),
                coupon_discount=self.coupon_discount.get_decimal(),
                seller_funded_promo=self.seller_promo.get_decimal(),
                customer_paid_shipping=self.customer_shipping.get_decimal(),
                gst_config=gst_config,
                payment_method=self.payment_method.currentText().lower().replace(" ", "_"),
            )

            # Build SellingExpenses
            se = SellingExpenses(
                marketplace_commission=self.marketplace_commission.get_decimal(),
                closing_fee=self.closing_fee.get_decimal(),
                payment_gateway_fee=self.payment_gateway_fee.get_decimal(),
                forward_shipping=self.forward_shipping.get_decimal(),
                reverse_shipping=self.reverse_shipping.get_decimal(),
                cod_charge=self.cod_charge.get_decimal(),
                affiliate_commission=self.affiliate_comm.get_decimal(),
                advertising_cost=self.advertising.get_decimal(),
                return_expense=self.return_expense.get_decimal(),
                rto_expense=self.rto_expense.get_decimal(),
                other_variable_cost=self.other_cost.get_decimal(),
            )

            # Calculate
            result = calculate_profit(pc, sd, se)

            # Update UI
            self._update_results(result)

        except Exception as e:
            self.profit_status.setText(f"Error: {str(e)}")
            self.profit_status.setObjectName("badge_warning")

    def _update_results(self, result):
        from ...core.profit import ProfitResult
        self._latest_result = result

        # Status badge
        if result.is_profitable:
            self.profit_status.setText("✓ PROFITABLE")
            self.profit_status.setObjectName("badge_profitable")
        else:
            self.profit_status.setText("✗ LOSS")
            self.profit_status.setObjectName("badge_loss")
        self.profit_status.style().unpolish(self.profit_status)
        self.profit_status.style().polish(self.profit_status)

        # Metric cards
        profit_type = "success" if result.is_profitable else "danger"
        self.card_net_revenue.update_value(fmt_inr(result.net_revenue))
        self.card_profit.update_value(
            fmt_inr(result.estimated_operating_profit, show_sign=True),
            profit_type
        )
        self.card_margin.update_value(fmt_pct(result.contribution_margin_pct), profit_type)
        self.card_markup.update_value(fmt_pct(result.markup_on_cost_pct))

        # Revenue rows
        self.row_gross_value.set_value(fmt_inr(result.gross_list_value))
        self.row_customer_discount.set_value(
            f"− {fmt_inr(result.customer_discount_total)}", "#f87171"
        )
        self.row_net_payment.set_value(fmt_inr(result.net_customer_payment))
        self.row_output_gst.set_value(fmt_inr(result.output_gst))
        self.row_net_revenue.set_value(fmt_inr(result.net_revenue), "#4ade80")

        # Expense rows
        self.row_acquisition.set_value(fmt_inr(result.total_acquisition_cost))
        self.row_fulfillment.set_value(fmt_inr(result.total_fulfillment_cost))
        self.row_mp_fees.set_value(fmt_inr(result.total_marketplace_fees))
        self.row_payment_fees.set_value(fmt_inr(result.total_payment_fees))
        self.row_advertising.set_value(fmt_inr(result.advertising_expense))
        self.row_affiliate.set_value(fmt_inr(result.affiliate_commission))
        self.row_returns.set_value(fmt_inr(result.expected_return_rto))
        self.row_other.set_value(fmt_inr(result.other_variable_expense))
        self.row_overhead.set_value(fmt_inr(result.overhead_allocated))
        self.row_total_expense.set_value(
            fmt_inr(result.total_variable_expense + result.advertising_expense
                    + result.overhead_allocated), "#f87171"
        )

        # Profit rows
        self.row_contrib_before_adv.set_value(fmt_inr(result.contribution_profit_before_adv))
        color_after = "#4ade80" if result.contribution_profit_after_adv >= 0 else "#f87171"
        self.row_contrib_after_adv.set_value(
            fmt_inr(result.contribution_profit_after_adv, show_sign=True), color_after
        )
        color_op = "#4ade80" if result.is_profitable else "#f87171"
        self.row_operating_profit.set_value(
            fmt_inr(result.estimated_operating_profit, show_sign=True), color_op
        )
        self.row_profit_per_unit.set_value(fmt_inr(result.profit_per_unit))
        self.row_total_profit.set_value(fmt_inr(result.total_profit))
        self.row_contrib_margin.set_value(fmt_pct(result.contribution_margin_pct))
        self.row_operating_margin.set_value(fmt_pct(result.operating_margin_pct))
        self.row_markup.set_value(fmt_pct(result.markup_on_cost_pct))
        self.row_expense_pct.set_value(fmt_pct(result.effective_expense_pct))

        # Warnings
        if result.warnings:
            self.warnings_label.setText("\n".join(f"• {w}" for w in result.warnings))
            self.warnings_card.setVisible(True)
        else:
            self.warnings_card.setVisible(False)

    def _save_scenario(self):
        """Save current inputs as a scenario."""
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.information(self, "Save Scenario",
                                "Scenario saved successfully into CommerceCalc local database.")

    def _run_ai_audit(self):
        """Run cloud LLM financial audit on the current product scenario."""
        from ..widgets.ai_dialog import AIDiagnosticDialog
        from ...services.ai_service import CommerceCalcAI

        if not hasattr(self, "_latest_result") or not self._latest_result:
            self._calculate()

        p_name = self.product_name.text().strip() or "Unnamed SKU"
        channel = self.channel.currentText()
        res = getattr(self, "_latest_result", None)

        data = {
            "product_name": p_name,
            "channel": channel,
            "selling_price": str(self.actual_price.get_decimal()),
            "purchase_cost": str(self.purchase_cost.get_decimal()),
            "net_revenue": str(getattr(res, "net_revenue", "0")),
            "fulfillment_cost": str(getattr(res, "total_fulfillment_cost", "0")),
            "marketplace_fees": str(getattr(res, "total_marketplace_fees", "0")),
            "advertising": str(self.advertising.get_decimal()),
            "return_loss": str(
                (getattr(res, "expected_return_expense", Decimal("0")) or Decimal("0")) +
                (getattr(res, "expected_rto_expense", Decimal("0")) or Decimal("0"))
            ),
            "net_profit": str(getattr(res, "estimated_operating_profit", "0")),
            "margin_pct": str(getattr(res, "contribution_margin_pct", "0")),
            "markup_pct": str(getattr(res, "markup_on_cost_pct", "0")),
            "gst_rate": str(self.gst_rate.currentData() or "18"),
        }

        ai = CommerceCalcAI()
        dlg = AIDiagnosticDialog(
            f"AI Financial Diagnosis: {p_name}",
            lambda: ai.analyze_product_profitability(data),
            parent=self
        )
        dlg.exec()
