"""
Digital Products, Ebooks, Courses, and Software Calculator for CommerceCalc.

Calculates economics for products with zero marginal physical shipping:
- Upfront creation/content cost amortization
- Hosting/CDN/bandwidth cost per download or user
- Payment processing, affiliate commission, platform fees
- Refund rates and chargebacks
- Amortization period and units needed to recover development costs
"""
from decimal import Decimal
from dataclasses import dataclass, field
from typing import List, Optional
from .money import to_decimal, money, pct, safe_divide, margin


@dataclass
class DigitalProductInputs:
    selling_price: Decimal = Decimal("0")
    expected_sales_units: int = 100

    # Fixed upfront development costs
    creation_cost: Decimal = Decimal("0")  # content, authoring, software dev
    assets_licensing_cost: Decimal = Decimal("0")

    # Variable delivery costs (per sale)
    hosting_delivery_per_unit: Decimal = Decimal("0")  # bandwidth, serverless compute
    customer_support_per_unit: Decimal = Decimal("0")

    # Platform & sales fees
    platform_fee_pct: Decimal = Decimal("0")  # e.g. Gumroad, Teachable, Udemy, Stripe
    fixed_platform_fee: Decimal = Decimal("0")
    payment_gateway_pct: Decimal = Decimal("2.0")
    fixed_payment_fee: Decimal = Decimal("0")
    affiliate_commission_pct: Decimal = Decimal("0")

    # Risk
    refund_rate_pct: Decimal = Decimal("0")

    def __post_init__(self):
        for f in ["selling_price", "creation_cost", "assets_licensing_cost",
                  "hosting_delivery_per_unit", "customer_support_per_unit",
                  "platform_fee_pct", "fixed_platform_fee", "payment_gateway_pct",
                  "fixed_payment_fee", "affiliate_commission_pct", "refund_rate_pct"]:
            setattr(self, f, to_decimal(getattr(self, f)))


@dataclass
class DigitalProductResult:
    selling_price: Decimal = Decimal("0")
    net_revenue_per_unit: Decimal = Decimal("0")
    variable_cost_per_unit: Decimal = Decimal("0")
    contribution_profit_per_unit: Decimal = Decimal("0")
    contribution_margin_pct: Decimal = Decimal("0")

    total_upfront_cost: Decimal = Decimal("0")
    amortized_cost_per_unit: Decimal = Decimal("0")
    net_profit_per_unit: Decimal = Decimal("0")
    total_projected_net_profit: Decimal = Decimal("0")

    units_needed_to_break_even: int = 0
    break_even_selling_price: Decimal = Decimal("0")
    is_profitable: bool = True
    warnings: List[str] = field(default_factory=list)


def calculate_digital_product(inputs: DigitalProductInputs) -> DigitalProductResult:
    result = DigitalProductResult()
    warnings = []

    p = inputs.selling_price
    result.selling_price = p

    # Net revenue after refund expectation
    refund_loss = p * pct(inputs.refund_rate_pct)
    net_rev = p - refund_loss
    result.net_revenue_per_unit = money(net_rev)

    # Variable fees
    plat_fee = (p * pct(inputs.platform_fee_pct)) + inputs.fixed_platform_fee
    pg_fee = (p * pct(inputs.payment_gateway_pct)) + inputs.fixed_payment_fee
    aff_fee = p * pct(inputs.affiliate_commission_pct)
    delivery_ops = inputs.hosting_delivery_per_unit + inputs.customer_support_per_unit

    var_cost = plat_fee + pg_fee + aff_fee + delivery_ops
    result.variable_cost_per_unit = money(var_cost)

    unit_contrib = net_rev - var_cost
    result.contribution_profit_per_unit = money(unit_contrib)
    result.contribution_margin_pct = margin(unit_contrib, p)

    # Upfront costs
    tot_upfront = inputs.creation_cost + inputs.assets_licensing_cost
    result.total_upfront_cost = money(tot_upfront)

    qty = max(inputs.expected_sales_units, 1)
    amortized = safe_divide(tot_upfront, qty)
    result.amortized_cost_per_unit = money(amortized)

    unit_net = unit_contrib - amortized
    result.net_profit_per_unit = money(unit_net)
    result.total_projected_net_profit = money(unit_net * to_decimal(qty))
    result.is_profitable = unit_net > 0

    # Break-even units
    if unit_contrib > 0:
        import math
        be_units = math.ceil(float(tot_upfront / unit_contrib))
        result.units_needed_to_break_even = be_units
    else:
        result.units_needed_to_break_even = 0
        warnings.append("Variable costs exceed revenue per unit. Development cost cannot be recovered.")

    # Break-even selling price (for expected sales units)
    denom = Decimal("1") - pct(inputs.platform_fee_pct) - pct(inputs.payment_gateway_pct) - pct(inputs.affiliate_commission_pct) - pct(inputs.refund_rate_pct)
    fixed_per_unit = amortized + delivery_ops + inputs.fixed_platform_fee + inputs.fixed_payment_fee
    if denom > 0:
        result.break_even_selling_price = money(fixed_per_unit / denom)
    else:
        result.break_even_selling_price = Decimal("0")
        warnings.append("Variable percentage deductions exceed 100%. Cannot break even.")

    result.warnings = warnings
    return result
