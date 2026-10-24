"""
Discount, Coupon, and Promotion Calculator for CommerceCalc.

Calculates:
- Percentage discounts
- Fixed discounts
- Coupons
- BOGO (Buy One Get One)
- Quantity-based breaks
- Seller vs Marketplace funded promotions
- Break-even order volume to compensate for discounts
"""
from decimal import Decimal
from dataclasses import dataclass, field
from typing import List, Optional
from .money import to_decimal, money, pct, percent_of, safe_divide


@dataclass
class PromotionInputs:
    original_price: Decimal = Decimal("0")
    promo_type: str = "percentage"  # percentage, fixed, coupon, bogo, quantity_break
    discount_value: Decimal = Decimal("0")  # % or INR
    coupon_amount: Decimal = Decimal("0")
    seller_funded_pct: Decimal = Decimal("100")  # % of promo funded by seller (vs platform)
    baseline_units_sold: int = 100
    baseline_unit_cost: Decimal = Decimal("0")
    baseline_shipping_and_fees: Decimal = Decimal("0")

    # BOGO settings
    buy_quantity: int = 1
    get_quantity: int = 1

    def __post_init__(self):
        for f in ["original_price", "discount_value", "coupon_amount", 
                  "seller_funded_pct", "baseline_unit_cost", "baseline_shipping_and_fees"]:
            setattr(self, f, to_decimal(getattr(self, f)))


@dataclass
class PromotionResult:
    original_price: Decimal = Decimal("0")
    total_customer_discount: Decimal = Decimal("0")
    effective_discount_pct: Decimal = Decimal("0")
    customer_pays: Decimal = Decimal("0")
    seller_discount_share: Decimal = Decimal("0")
    marketplace_discount_share: Decimal = Decimal("0")
    adjusted_seller_revenue: Decimal = Decimal("0")

    baseline_profit_per_unit: Decimal = Decimal("0")
    promo_profit_per_unit: Decimal = Decimal("0")
    profit_reduction_per_unit: Decimal = Decimal("0")
    incremental_orders_needed_pct: Decimal = Decimal("0")
    required_units_for_same_profit: int = 0
    is_profitable: bool = True
    warnings: List[str] = field(default_factory=list)


def calculate_promotion(inputs: PromotionInputs) -> PromotionResult:
    result = PromotionResult()
    warnings = []
    p = inputs.original_price
    result.original_price = p

    total_disc = Decimal("0")
    if inputs.promo_type == "percentage":
        total_disc = percent_of(p, inputs.discount_value)
    elif inputs.promo_type == "fixed":
        total_disc = min(inputs.discount_value, p)
    elif inputs.promo_type == "coupon":
        total_disc = min(inputs.coupon_amount, p)
    elif inputs.promo_type == "bogo":
        # Buy X get Y free: effective discount is Y / (X + Y)
        tot_qty = inputs.buy_quantity + inputs.get_quantity
        if tot_qty > 0:
            eff_rate = safe_divide(inputs.get_quantity, tot_qty)
            total_disc = p * eff_rate
    else:
        total_disc = min(inputs.discount_value, p)

    result.total_customer_discount = money(total_disc)
    result.customer_pays = money(max(p - total_disc, Decimal("0")))
    result.effective_discount_pct = money(safe_divide(total_disc, p) * Decimal("100")) if p > 0 else Decimal("0")

    seller_share_factor = pct(inputs.seller_funded_pct)
    result.seller_discount_share = money(total_disc * seller_share_factor)
    result.marketplace_discount_share = money(total_disc - result.seller_discount_share)
    
    # Revenue seller receives: customer payment + marketplace funded share
    result.adjusted_seller_revenue = money(result.customer_pays + result.marketplace_discount_share)

    # Unit economics
    cost = inputs.baseline_unit_cost + inputs.baseline_shipping_and_fees
    baseline_profit = p - cost
    promo_profit = result.adjusted_seller_revenue - cost

    result.baseline_profit_per_unit = money(baseline_profit)
    result.promo_profit_per_unit = money(promo_profit)
    result.profit_reduction_per_unit = money(baseline_profit - promo_profit)
    result.is_profitable = promo_profit > 0

    if promo_profit <= 0:
        warnings.append("Promotion causes loss on each unit sold.")
        result.incremental_orders_needed_pct = Decimal("0")
        result.required_units_for_same_profit = 0
    else:
        if baseline_profit > 0:
            # Baseline total profit for 100 units = baseline_profit * baseline_units
            # Target units = (baseline_profit * baseline_units) / promo_profit
            target_units = (baseline_profit * to_decimal(inputs.baseline_units_sold)) / promo_profit
            import math
            result.required_units_for_same_profit = math.ceil(float(target_units))
            inc_pct = ((target_units - to_decimal(inputs.baseline_units_sold)) / to_decimal(inputs.baseline_units_sold)) * Decimal("100")
            result.incremental_orders_needed_pct = money(inc_pct)
        else:
            result.required_units_for_same_profit = inputs.baseline_units_sold

    result.warnings = warnings
    return result
