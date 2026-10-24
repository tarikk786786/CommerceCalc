"""
Cash Flow and Marketplace Settlement Calculator for CommerceCalc.

Distinguishes accounting profitability from cash settlement payouts.
Handles:
- Gross customer orders and buyer payments
- Marketplace commission, closing fee, shipping deductions
- TCS (Tax Collected at Source - GST law, typically 0.5% CGST + 0.5% SGST or 1% IGST)
- TDS (Section 194-O Income Tax, typically 0.1% - 1%)
- Return and customer refund clawbacks
- Marketplace rolling reserves and payment cycle delays
"""
from decimal import Decimal
from dataclasses import dataclass, field
from typing import List, Optional
from .money import to_decimal, money, pct, safe_divide


@dataclass
class SettlementInputs:
    # Gross Transactions
    gross_order_sales_inr: Decimal = Decimal("0")
    total_orders_count: int = 100

    # Marketplace Deductions
    marketplace_commission_inr: Decimal = Decimal("0")
    marketplace_shipping_deductions_inr: Decimal = Decimal("0")
    marketplace_fixed_closing_fees_inr: Decimal = Decimal("0")
    seller_funded_promotions_inr: Decimal = Decimal("0")

    # Statutory Withholdings (India)
    gst_tcs_rate_pct: Decimal = Decimal("1.0")  # Section 52 CGST Act
    income_tax_tds_rate_pct: Decimal = Decimal("0.1")  # Section 194-O Income Tax Act
    gst_on_marketplace_fees_pct: Decimal = Decimal("18.0")  # 18% GST charged by Amazon/Flipkart on their services

    # Returns / Claims Deductions
    refunds_deducted_inr: Decimal = Decimal("0")
    customer_return_shipping_inr: Decimal = Decimal("0")

    # Reserves / Policy
    platform_reserve_held_pct: Decimal = Decimal("0")  # e.g. 5-10% holdback on new accounts

    # Supplier / Product Cost (for cash profit comparison)
    actual_product_cost_inr: Decimal = Decimal("0")

    def __post_init__(self):
        for f in ["gross_order_sales_inr", "marketplace_commission_inr",
                  "marketplace_shipping_deductions_inr", "marketplace_fixed_closing_fees_inr",
                  "seller_funded_promotions_inr", "gst_tcs_rate_pct", "income_tax_tds_rate_pct",
                  "gst_on_marketplace_fees_pct", "refunds_deducted_inr", "customer_return_shipping_inr",
                  "platform_reserve_held_pct", "actual_product_cost_inr"]:
            setattr(self, f, to_decimal(getattr(self, f)))


@dataclass
class SettlementResult:
    gross_sales: Decimal = Decimal("0")
    total_platform_fees_before_gst: Decimal = Decimal("0")
    gst_on_platform_fees: Decimal = Decimal("0")
    total_platform_deductions: Decimal = Decimal("0")

    tcs_withheld: Decimal = Decimal("0")
    tds_withheld: Decimal = Decimal("0")
    total_statutory_withholding: Decimal = Decimal("0")

    refunds_and_returns_clawback: Decimal = Decimal("0")
    reserve_withheld: Decimal = Decimal("0")

    net_bank_settlement: Decimal = Decimal("0")
    cash_profit_after_inventory_cost: Decimal = Decimal("0")
    settlement_realization_pct: Decimal = Decimal("0")  # % of gross sales actually received in bank

    accounting_notes: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


def calculate_settlement(inputs: SettlementInputs) -> SettlementResult:
    result = SettlementResult()
    warnings = []
    notes = []

    gross = inputs.gross_order_sales_inr
    result.gross_sales = gross

    # Marketplace service fees (subject to 18% GST)
    base_mp_fees = inputs.marketplace_commission_inr + inputs.marketplace_fixed_closing_fees_inr + inputs.marketplace_shipping_deductions_inr
    gst_fees = base_mp_fees * pct(inputs.gst_on_marketplace_fees_pct)
    tot_mp_deductions = base_mp_fees + gst_fees + inputs.seller_funded_promotions_inr

    result.total_platform_fees_before_gst = money(base_mp_fees)
    result.gst_on_platform_fees = money(gst_fees)
    result.total_platform_deductions = money(tot_mp_deductions)

    # Statutory Tax Withholdings
    # TCS is 1% on net value of taxable supplies (Gross - Returns)
    net_taxable_supplies = max(gross - inputs.refunds_deducted_inr, Decimal("0"))
    tcs = net_taxable_supplies * pct(inputs.gst_tcs_rate_pct)
    tds = net_taxable_supplies * pct(inputs.income_tax_tds_rate_pct)

    result.tcs_withheld = money(tcs)
    result.tds_withheld = money(tds)
    result.total_statutory_withholding = money(tcs + tds)

    notes.append(f"TCS of ₹{result.tcs_withheld} is creditable against GST cash ledger via GSTR-8.")
    notes.append(f"TDS of ₹{result.tds_withheld} under Sec 194-O is creditable against annual Income Tax via Form 26AS.")

    # Refunds & Clawbacks
    refund_clawback = inputs.refunds_deducted_inr + inputs.customer_return_shipping_inr
    result.refunds_and_returns_clawback = money(refund_clawback)

    # Reserves
    reserve = gross * pct(inputs.platform_reserve_held_pct)
    result.reserve_withheld = money(reserve)

    # Net Settlement
    net_payout = gross - tot_mp_deductions - (tcs + tds) - refund_clawback - reserve
    result.net_bank_settlement = money(net_payout)

    # Realization %
    if gross > 0:
        result.settlement_realization_pct = money(safe_divide(net_payout, gross) * Decimal("100"))

    # Net Cash Profit after inventory cost
    cash_profit = net_payout - inputs.actual_product_cost_inr
    result.cash_profit_after_inventory_cost = money(cash_profit)

    if net_payout < 0:
        warnings.append("Net settlement is negative! Marketplace will debit your seller account or roll over balance.")

    result.accounting_notes = notes
    result.warnings = warnings
    return result
