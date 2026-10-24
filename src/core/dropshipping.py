"""
Dropshipping Calculator for CommerceCalc.

Dedicated workflow for dropshipping models:
- Supplier price + supplier shipping
- FX conversion rate and fees
- Customer selling price
- Payment gateway & platform subscription allocation
- Ad spend per acquired order
- Return and RTO adjustments
- COD versus Prepaid risk
"""
from decimal import Decimal
from dataclasses import dataclass, field
from typing import List, Optional
from .money import to_decimal, money, pct, safe_divide, margin


@dataclass
class DropshipInputs:
    # Supplier
    supplier_price_foreign: Decimal = Decimal("0")
    supplier_shipping_foreign: Decimal = Decimal("0")
    exchange_rate: Decimal = Decimal("1")  # e.g. 83.5 for USD to INR, 1 for domestic
    currency_conversion_fee_pct: Decimal = Decimal("0")  # e.g. 2.5% FX markup
    customs_handling_inr: Decimal = Decimal("0")

    # Selling
    customer_selling_price_inr: Decimal = Decimal("0")
    payment_gateway_pct: Decimal = Decimal("2.0")  # e.g. 2%
    store_platform_allocated_inr: Decimal = Decimal("0")  # e.g. Shopify plan split per order
    marketplace_commission_pct: Decimal = Decimal("0")

    # Marketing & Ops
    ad_spend_per_order_inr: Decimal = Decimal("0")  # target CAC
    custom_packaging_branding_inr: Decimal = Decimal("0")
    order_type: str = "prepaid"  # 'prepaid' or 'cod'
    cod_fee_inr: Decimal = Decimal("0")

    # Risk assumptions
    rto_rate_pct: Decimal = Decimal("0")  # especially relevant for COD
    refund_chargeback_rate_pct: Decimal = Decimal("0")
    unrecovered_shipping_loss_inr: Decimal = Decimal("0")  # shipping paid to supplier but lost

    def __post_init__(self):
        for f in ["supplier_price_foreign", "supplier_shipping_foreign", "exchange_rate",
                  "currency_conversion_fee_pct", "customs_handling_inr", "customer_selling_price_inr",
                  "payment_gateway_pct", "store_platform_allocated_inr", "marketplace_commission_pct",
                  "ad_spend_per_order_inr", "custom_packaging_branding_inr", "cod_fee_inr",
                  "rto_rate_pct", "refund_chargeback_rate_pct", "unrecovered_shipping_loss_inr"]:
            setattr(self, f, to_decimal(getattr(self, f)))


@dataclass
class DropshipResult:
    landed_supplier_cost_inr: Decimal = Decimal("0")
    fx_effective_rate: Decimal = Decimal("0")
    customer_selling_price: Decimal = Decimal("0")

    total_platform_and_payment_fees: Decimal = Decimal("0")
    total_marketing_and_branding: Decimal = Decimal("0")
    expected_risk_loss_per_order: Decimal = Decimal("0")
    total_cost_per_order: Decimal = Decimal("0")

    profit_per_order: Decimal = Decimal("0")
    contribution_margin_pct: Decimal = Decimal("0")
    break_even_selling_price: Decimal = Decimal("0")
    max_allowable_cac: Decimal = Decimal("0")
    max_tolerable_supplier_price_inr: Decimal = Decimal("0")

    is_profitable: bool = True
    warnings: List[str] = field(default_factory=list)


def calculate_dropship(inputs: DropshipInputs) -> DropshipResult:
    result = DropshipResult()
    warnings = []

    # Landed supplier cost in INR
    effective_rate = inputs.exchange_rate * (Decimal("1") + pct(inputs.currency_conversion_fee_pct))
    result.fx_effective_rate = effective_rate
    foreign_total = inputs.supplier_price_foreign + inputs.supplier_shipping_foreign
    supplier_cost_inr = (foreign_total * effective_rate) + inputs.customs_handling_inr
    result.landed_supplier_cost_inr = money(supplier_cost_inr)

    p = inputs.customer_selling_price_inr
    result.customer_selling_price = p

    # Fees
    pg_fee = p * pct(inputs.payment_gateway_pct)
    mp_fee = p * pct(inputs.marketplace_commission_pct)
    cod_charge = inputs.cod_fee_inr if inputs.order_type == "cod" else Decimal("0")
    tot_fees = pg_fee + mp_fee + inputs.store_platform_allocated_inr + cod_charge
    result.total_platform_and_payment_fees = money(tot_fees)

    # Marketing & Branding
    tot_mktg = inputs.ad_spend_per_order_inr + inputs.custom_packaging_branding_inr
    result.total_marketing_and_branding = money(tot_mktg)

    # Risk Loss
    # If COD RTO occurs, supplier shipping + COD fee might be lost without receiving revenue
    rto_loss = (supplier_cost_inr + inputs.unrecovered_shipping_loss_inr) * pct(inputs.rto_rate_pct)
    chargeback_loss = p * pct(inputs.refund_chargeback_rate_pct)
    expected_risk = rto_loss + chargeback_loss
    result.expected_risk_loss_per_order = money(expected_risk)

    # Total cost
    tot_cost = supplier_cost_inr + tot_fees + tot_mktg + expected_risk
    result.total_cost_per_order = money(tot_cost)

    # Profit
    prof = p - tot_cost
    result.profit_per_order = money(prof)
    result.contribution_margin_pct = margin(prof, p)
    result.is_profitable = prof > 0

    # Break-even price
    # P * (1 - pg_pct - mp_pct - chargeback_pct) = fixed_costs
    pct_deductions = pct(inputs.payment_gateway_pct) + pct(inputs.marketplace_commission_pct) + pct(inputs.refund_chargeback_rate_pct)
    fixed_costs = supplier_cost_inr + inputs.store_platform_allocated_inr + cod_charge + tot_mktg + rto_loss
    denom = Decimal("1") - pct_deductions
    if denom > 0:
        result.break_even_selling_price = money(fixed_costs / denom)
    else:
        result.break_even_selling_price = Decimal("0")
        warnings.append("Percentage deductions exceed 100%. Cannot break even.")

    # Max allowable CAC (to break even at current selling price)
    profit_before_cac = p - (supplier_cost_inr + tot_fees + inputs.custom_packaging_branding_inr + expected_risk)
    result.max_allowable_cac = money(max(profit_before_cac, Decimal("0")))

    # Max tolerable supplier cost
    max_supplier = p - (tot_fees + tot_mktg + expected_risk)
    result.max_tolerable_supplier_price_inr = money(max(max_supplier, Decimal("0")))

    if inputs.order_type == "cod" and inputs.rto_rate_pct == Decimal("0"):
        warnings.append("COD selected but RTO rate is 0%. In Indian dropshipping, COD typically has 15-30% RTO.")

    result.warnings = warnings
    return result
