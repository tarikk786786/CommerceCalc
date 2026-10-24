"""
Landed Cost and Sourcing Calculator for CommerceCalc.

Calculates domestic and international sourcing landed costs:
- Supplier invoice amount in foreign currency
- Exchange rate & conversion markup
- International freight, insurance, port handling
- Customs Basic Customs Duty (BCD), Social Welfare Surcharge (SWS), and IGST
- Domestic inbound haulage, warehousing, and QC
- Recoverable vs Non-recoverable tax segregation
"""
from decimal import Decimal
from dataclasses import dataclass, field
from typing import List, Optional
from .money import to_decimal, money, pct, safe_divide


@dataclass
class LandedCostInputs:
    # Sourcing invoice
    shipment_units: int = 1000
    supplier_unit_price_foreign: Decimal = Decimal("0")
    currency_code: str = "USD"
    exchange_rate: Decimal = Decimal("83.5")
    bank_fx_fee_pct: Decimal = Decimal("2.0")

    # Freight & Logistics to Port
    international_freight_foreign: Decimal = Decimal("0")
    marine_cargo_insurance_inr: Decimal = Decimal("0")
    port_terminal_handling_inr: Decimal = Decimal("0")
    customs_brokerage_inr: Decimal = Decimal("0")

    # Customs Duties (Indian Tariffs)
    basic_customs_duty_pct: Decimal = Decimal("10.0")  # BCD e.g. 10%
    sws_pct: Decimal = Decimal("10.0")  # Social Welfare Surcharge: typically 10% on BCD
    import_igst_rate_pct: Decimal = Decimal("18.0")  # IGST on assessable value + BCD + SWS
    is_igst_recoverable_as_itc: bool = True  # Can the importer claim ITC on import IGST?

    # Domestic Post-Port
    domestic_transport_inr: Decimal = Decimal("0")
    qc_inspection_inr: Decimal = Decimal("0")
    repackaging_inr: Decimal = Decimal("0")

    def __post_init__(self):
        for f in ["supplier_unit_price_foreign", "exchange_rate", "bank_fx_fee_pct",
                  "international_freight_foreign", "marine_cargo_insurance_inr",
                  "port_terminal_handling_inr", "customs_brokerage_inr",
                  "basic_customs_duty_pct", "sws_pct", "import_igst_rate_pct",
                  "domestic_transport_inr", "qc_inspection_inr", "repackaging_inr"]:
            setattr(self, f, to_decimal(getattr(self, f)))


@dataclass
class LandedCostResult:
    effective_fx_rate: Decimal = Decimal("0")
    fob_value_inr: Decimal = Decimal("0")
    freight_value_inr: Decimal = Decimal("0")
    cif_assessable_value_inr: Decimal = Decimal("0")

    bcd_amount_inr: Decimal = Decimal("0")
    sws_amount_inr: Decimal = Decimal("0")
    import_igst_amount_inr: Decimal = Decimal("0")
    total_customs_paid_inr: Decimal = Decimal("0")

    port_and_clearance_inr: Decimal = Decimal("0")
    domestic_handling_inr: Decimal = Decimal("0")

    total_cash_outlay_shipment: Decimal = Decimal("0")
    recoverable_itc_shipment: Decimal = Decimal("0")
    net_accounting_cost_shipment: Decimal = Decimal("0")

    cash_outlay_per_unit: Decimal = Decimal("0")
    landed_cost_per_unit: Decimal = Decimal("0")  # Accounting landed cost excl. recoverable ITC

    warnings: List[str] = field(default_factory=list)


def calculate_landed_cost(inputs: LandedCostInputs) -> LandedCostResult:
    result = LandedCostResult()
    warnings = []
    units = max(inputs.shipment_units, 1)

    # Effective Exchange Rate
    eff_fx = inputs.exchange_rate * (Decimal("1") + pct(inputs.bank_fx_fee_pct))
    result.effective_fx_rate = eff_fx

    # FOB & Freight in INR
    tot_foreign_goods = inputs.supplier_unit_price_foreign * to_decimal(units)
    fob_inr = tot_foreign_goods * eff_fx
    freight_inr = inputs.international_freight_foreign * eff_fx
    result.fob_value_inr = money(fob_inr)
    result.freight_value_inr = money(freight_inr)

    # CIF / Assessable Value for Indian Customs = FOB + Freight + Insurance
    cif_assessable = fob_inr + freight_inr + inputs.marine_cargo_insurance_inr
    result.cif_assessable_value_inr = money(cif_assessable)

    # Customs Duties
    bcd = cif_assessable * pct(inputs.basic_customs_duty_pct)
    sws = bcd * pct(inputs.sws_pct)  # SWS is 10% on BCD, not CIF
    base_for_igst = cif_assessable + bcd + sws
    igst = base_for_igst * pct(inputs.import_igst_rate_pct)

    result.bcd_amount_inr = money(bcd)
    result.sws_amount_inr = money(sws)
    result.import_igst_amount_inr = money(igst)
    tot_customs = bcd + sws + igst
    result.total_customs_paid_inr = money(tot_customs)

    # Clearance & Port
    clearance = inputs.port_terminal_handling_inr + inputs.customs_brokerage_inr
    result.port_and_clearance_inr = money(clearance)

    # Domestic handling
    domestic = inputs.domestic_transport_inr + inputs.qc_inspection_inr + inputs.repackaging_inr
    result.domestic_handling_inr = money(domestic)

    # Total Cash Outlay
    tot_cash = cif_assessable + tot_customs + clearance + domestic
    result.total_cash_outlay_shipment = money(tot_cash)
    result.cash_outlay_per_unit = money(safe_divide(tot_cash, units))

    # Accounting Landed Cost:
    # If IGST is recoverable as Input Tax Credit, it is NOT an expense, but an asset/credit.
    itc = igst if inputs.is_igst_recoverable_as_itc else Decimal("0")
    result.recoverable_itc_shipment = money(itc)

    net_cost = tot_cash - itc
    result.net_accounting_cost_shipment = money(net_cost)
    result.landed_cost_per_unit = money(safe_divide(net_cost, units))

    if not inputs.is_igst_recoverable_as_itc:
        warnings.append("Import IGST marked as non-recoverable. Full IGST added to landed product cost.")

    result.warnings = warnings
    return result
