"""
Landed Cost and Import Sourcing Calculator Page for CommerceCalc.
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
from ...core.landed_cost import LandedCostInputs, calculate_landed_cost


class LandedCostPage(QWidget):
    """Import customs duties and landed cost calculator."""

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
            "Customs tariff rates (BCD, SWS, IGST) vary by HSN code and CBIC notifications. "
            "Enter verified rates from ICEGATE or customs tariff schedules."
        ))

        # 1. Foreign Invoice
        inv_card, inv_layout = make_card("🚢 Overseas Sourcing & Freight")
        self.units_in = MoneyInput(prefix="", max_val=1000000)
        self.units_in.setDecimals(0)
        self.units_in.setValue(500.0)
        self.units_in.valueChanged.connect(self._trigger_calc)
        inv_layout.addWidget(FormFieldRow("Shipment Total Quantity", self.units_in))

        self.unit_price_usd = MoneyInput(prefix="$ ", max_val=99999.0)
        self.unit_price_usd.setValue(8.50)
        self.unit_price_usd.valueChanged.connect(self._trigger_calc)
        inv_layout.addWidget(FormFieldRow("Supplier Unit Price ($)", self.unit_price_usd))

        self.fx_rate = MoneyInput(prefix="₹ ", max_val=999.0)
        self.fx_rate.setValue(84.0)
        self.fx_rate.valueChanged.connect(self._trigger_calc)
        inv_layout.addWidget(FormFieldRow("Forex Exchange Rate (USD to INR)", self.fx_rate))

        self.fx_bank_fee = PercentInput()
        self.fx_bank_fee.setValue(1.5)
        self.fx_bank_fee.valueChanged.connect(self._trigger_calc)
        inv_layout.addWidget(FormFieldRow("Bank FX Spread / TT Fee %", self.fx_bank_fee))

        self.intl_freight = MoneyInput(prefix="$ ", max_val=999999.0)
        self.intl_freight.setValue(600.0)
        self.intl_freight.valueChanged.connect(self._trigger_calc)
        inv_layout.addWidget(FormFieldRow("International Ocean/Air Freight ($)", self.intl_freight))

        self.insurance_inr = MoneyInput(max_val=999999.0)
        self.insurance_inr.setValue(3500.0)
        self.insurance_inr.valueChanged.connect(self._trigger_calc)
        inv_layout.addWidget(FormFieldRow("Marine Cargo Transit Insurance (₹)", self.insurance_inr))
        left_layout.addWidget(inv_card)

        # 2. Indian Customs Tariffs
        cust_card, cust_layout = make_card("🏛️ Indian Customs Tariffs (Assessable Value)")
        self.bcd_pct = PercentInput()
        self.bcd_pct.setValue(10.0)
        self.bcd_pct.valueChanged.connect(self._trigger_calc)
        cust_layout.addWidget(FormFieldRow("Basic Customs Duty (BCD) %", self.bcd_pct))

        self.sws_pct = PercentInput()
        self.sws_pct.setValue(10.0)  # SWS is standard 10% on BCD
        self.sws_pct.valueChanged.connect(self._trigger_calc)
        cust_layout.addWidget(FormFieldRow("Social Welfare Surcharge (SWS) %", self.sws_pct,
                                            "10% of BCD amount per Indian Customs Act."))

        self.igst_pct = PercentInput()
        self.igst_pct.setValue(18.0)
        self.igst_pct.valueChanged.connect(self._trigger_calc)
        cust_layout.addWidget(FormFieldRow("Import IGST %", self.igst_pct))

        self.itc_eligible = QCheckBox("Import IGST is Recoverable as Input Tax Credit (ITC)")
        self.itc_eligible.setChecked(True)
        self.itc_eligible.stateChanged.connect(self._trigger_calc)
        cust_layout.addWidget(self.itc_eligible)
        left_layout.addWidget(cust_card)

        # 3. Port Clearance & Domestic Transport
        dom_card, dom_layout = make_card("🚚 Port Clearance & Inbound Logistics")
        self.port_fees = MoneyInput(max_val=999999.0)
        self.port_fees.setValue(8500.0)
        self.port_fees.valueChanged.connect(self._trigger_calc)
        dom_layout.addWidget(FormFieldRow("CHA / Customs Brokerage & Port", self.port_fees))

        self.dom_freight = MoneyInput(max_val=999999.0)
        self.dom_freight.setValue(6500.0)
        self.dom_freight.valueChanged.connect(self._trigger_calc)
        dom_layout.addWidget(FormFieldRow("Port-to-Warehouse Domestic Trucking", self.dom_freight))

        self.qc_repack = MoneyInput(max_val=999999.0)
        self.qc_repack.setValue(2500.0)
        self.qc_repack.valueChanged.connect(self._trigger_calc)
        dom_layout.addWidget(FormFieldRow("QC Inspection & Repackaging (₹)", self.qc_repack))
        left_layout.addWidget(dom_card)

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
        self.card_landed_unit = MetricCard("Landed Cost / Unit (Net)", "₹–", "success")
        self.card_cash_outlay_unit = MetricCard("Cash Outlay / Unit", "₹–", "default")
        self.card_total_customs = MetricCard("Total Customs Paid", "₹–", "default")
        self.card_itc_shipment = MetricCard("Recoverable ITC", "₹–", "default")
        metrics_grid.addWidget(self.card_landed_unit, 0, 0)
        metrics_grid.addWidget(self.card_cash_outlay_unit, 0, 1)
        metrics_grid.addWidget(self.card_total_customs, 1, 0)
        metrics_grid.addWidget(self.card_itc_shipment, 1, 1)
        right_layout.addLayout(metrics_grid)

        # Breakdown
        res_card, res_layout = make_card("Landed Cost & Tariff Schedule")
        self.row_effective_fx = ResultRow("Effective Exchange Rate", "–")
        self.row_fob = ResultRow("Goods Invoice Value (FOB in INR)", "–")
        self.row_cif = ResultRow("CIF Assessable Value (Goods + Freight + Ins)", "–", bold=True)
        self.row_bcd = ResultRow("Basic Customs Duty (BCD)", "–")
        self.row_sws = ResultRow("Social Welfare Surcharge (SWS on BCD)", "–")
        self.row_igst = ResultRow("Import IGST (Assessable + BCD + SWS)", "–")
        self.row_tot_customs = ResultRow("Total Customs Duty Paid at Port", "–", bold=True)
        self.row_clearance = ResultRow("CHA, Port & Domestic Logistics", "–")
        self.row_tot_cash = ResultRow("Total Cash Outflow for Shipment", "–", bold=True)
        self.row_itc = ResultRow("Input Tax Credit on Import IGST", "–", color="#4ade80")
        self.row_net_cost = ResultRow("True Net Accounting Landed Cost", "–", bold=True, color="#4ade80")

        for r in [
            self.row_effective_fx, self.row_fob, self.row_cif, Divider(),
            self.row_bcd, self.row_sws, self.row_igst, self.row_tot_customs,
            self.row_clearance, Divider(),
            self.row_tot_cash, self.row_itc, Divider(), self.row_net_cost
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
            inputs = LandedCostInputs(
                shipment_units=max(int(self.units_in.value()), 1),
                supplier_unit_price_foreign=self.unit_price_usd.get_decimal(),
                exchange_rate=self.fx_rate.get_decimal(),
                bank_fx_fee_pct=self.fx_bank_fee.get_decimal(),
                international_freight_foreign=self.intl_freight.get_decimal(),
                marine_cargo_insurance_inr=self.insurance_inr.get_decimal(),
                basic_customs_duty_pct=self.bcd_pct.get_decimal(),
                sws_pct=self.sws_pct.get_decimal(),
                import_igst_rate_pct=self.igst_pct.get_decimal(),
                is_igst_recoverable_as_itc=self.itc_eligible.isChecked(),
                port_terminal_handling_inr=self.port_fees.get_decimal(),
                domestic_transport_inr=self.dom_freight.get_decimal(),
                qc_inspection_inr=self.qc_repack.get_decimal(),
            )
            res = calculate_landed_cost(inputs)

            self.card_landed_unit.update_value(fmt_inr(res.landed_cost_per_unit), "success")
            self.card_cash_outlay_unit.update_value(fmt_inr(res.cash_outlay_per_unit))
            self.card_total_customs.update_value(fmt_inr(res.total_customs_paid_inr))
            self.card_itc_shipment.update_value(fmt_inr(res.recoverable_itc_shipment))

            self.row_effective_fx.set_value(f"1 USD = ₹{res.effective_fx_rate:.2f}")
            self.row_fob.set_value(fmt_inr(res.fob_value_inr))
            self.row_cif.set_value(fmt_inr(res.cif_assessable_value_inr))
            self.row_bcd.set_value(fmt_inr(res.bcd_amount_inr))
            self.row_sws.set_value(fmt_inr(res.sws_amount_inr))
            self.row_igst.set_value(fmt_inr(res.import_igst_amount_inr))
            self.row_tot_customs.set_value(fmt_inr(res.total_customs_paid_inr))
            self.row_clearance.set_value(fmt_inr(res.port_and_clearance_inr + res.domestic_handling_inr))
            self.row_tot_cash.set_value(fmt_inr(res.total_cash_outlay_shipment))
            self.row_itc.set_value(f"− {fmt_inr(res.recoverable_itc_shipment)} (ITC Claimable)", "#4ade80")
            self.row_net_cost.set_value(f"{fmt_inr(res.net_accounting_cost_shipment)} (₹{res.landed_cost_per_unit:.2f}/unit)", "#4ade80")

            if res.warnings:
                self.warnings_label.setText("⚠ " + " | ".join(res.warnings))
            else:
                self.warnings_label.setText("")
        except Exception as e:
            self.warnings_label.setText(f"Error: {str(e)}")
