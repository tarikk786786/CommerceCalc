"""
Bundle and Multi-Unit Profit Calculator for CommerceCalc.

Supports bundles of multiple SKUs, shared packaging, bundle discounts,
combined shipping, and transparent cost allocation.
"""
from decimal import Decimal
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from .money import to_decimal, money, pct, safe_divide, margin


@dataclass
class BundleItem:
    sku: str
    name: str
    unit_cost: Decimal = Decimal("0")
    quantity: int = 1
    individual_selling_price: Decimal = Decimal("0")

    def __post_init__(self):
        self.unit_cost = to_decimal(self.unit_cost)
        self.individual_selling_price = to_decimal(self.individual_selling_price)

    @property
    def total_cost(self) -> Decimal:
        return money(self.unit_cost * to_decimal(self.quantity))

    @property
    def total_individual_value(self) -> Decimal:
        return money(self.individual_selling_price * to_decimal(self.quantity))


@dataclass
class BundleInputs:
    items: List[BundleItem] = field(default_factory=list)
    bundle_selling_price: Decimal = Decimal("0")
    shared_packaging_cost: Decimal = Decimal("0")
    combined_shipping_cost: Decimal = Decimal("0")
    marketplace_fee_pct: Decimal = Decimal("0")
    fixed_marketplace_fee: Decimal = Decimal("0")
    payment_gateway_pct: Decimal = Decimal("0")
    allocated_ad_spend: Decimal = Decimal("0")
    allocation_method: str = "cost_share"  # 'cost_share', 'quantity_share', 'price_share'

    def __post_init__(self):
        for f in ["bundle_selling_price", "shared_packaging_cost", "combined_shipping_cost",
                  "marketplace_fee_pct", "fixed_marketplace_fee", "payment_gateway_pct", "allocated_ad_spend"]:
            setattr(self, f, to_decimal(getattr(self, f)))


@dataclass
class BundleItemResult:
    sku: str
    name: str
    quantity: int
    direct_cost: Decimal
    allocated_shared_cost: Decimal
    total_cost: Decimal
    allocated_revenue: Decimal
    allocated_profit: Decimal
    profit_margin_pct: Decimal


@dataclass
class BundleResult:
    total_standalone_price: Decimal = Decimal("0")
    bundle_selling_price: Decimal = Decimal("0")
    bundle_discount_amount: Decimal = Decimal("0")
    bundle_discount_pct: Decimal = Decimal("0")

    total_product_cost: Decimal = Decimal("0")
    total_shared_cost: Decimal = Decimal("0")
    total_marketplace_fees: Decimal = Decimal("0")
    total_payment_fees: Decimal = Decimal("0")
    total_bundle_cost: Decimal = Decimal("0")

    bundle_net_profit: Decimal = Decimal("0")
    bundle_margin_pct: Decimal = Decimal("0")
    bundle_markup_pct: Decimal = Decimal("0")
    break_even_bundle_price: Decimal = Decimal("0")

    item_breakdowns: List[BundleItemResult] = field(default_factory=list)
    allocation_explanation: str = ""
    warnings: List[str] = field(default_factory=list)


def calculate_bundle(inputs: BundleInputs) -> BundleResult:
    result = BundleResult()
    warnings = []

    if not inputs.items:
        warnings.append("No items in bundle.")
        result.warnings = warnings
        return result

    tot_standalone = sum(item.total_individual_value for item in inputs.items)
    tot_product_cost = sum(item.total_cost for item in inputs.items)
    tot_units = sum(item.quantity for item in inputs.items)

    result.total_standalone_price = money(tot_standalone)
    result.bundle_selling_price = inputs.bundle_selling_price
    result.total_product_cost = money(tot_product_cost)

    disc = max(tot_standalone - inputs.bundle_selling_price, Decimal("0"))
    result.bundle_discount_amount = money(disc)
    result.bundle_discount_pct = money(safe_divide(disc, tot_standalone) * Decimal("100")) if tot_standalone > 0 else Decimal("0")

    # Shared costs
    shared_ops = inputs.shared_packaging_cost + inputs.combined_shipping_cost + inputs.allocated_ad_spend
    result.total_shared_cost = money(shared_ops)

    # Marketplace & payment fees on bundle price
    mp_comm = (inputs.bundle_selling_price * pct(inputs.marketplace_fee_pct)) + inputs.fixed_marketplace_fee
    pg_fee = inputs.bundle_selling_price * pct(inputs.payment_gateway_pct)
    result.total_marketplace_fees = money(mp_comm)
    result.total_payment_fees = money(pg_fee)

    tot_all_costs = tot_product_cost + shared_ops + mp_comm + pg_fee
    result.total_bundle_cost = money(tot_all_costs)

    net_prof = inputs.bundle_selling_price - tot_all_costs
    result.bundle_net_profit = money(net_prof)
    result.bundle_margin_pct = margin(net_prof, inputs.bundle_selling_price)
    result.bundle_markup_pct = money(safe_divide(net_prof, tot_all_costs) * Decimal("100")) if tot_all_costs > 0 else Decimal("0")

    # Break-even price
    denom = Decimal("1") - pct(inputs.marketplace_fee_pct) - pct(inputs.payment_gateway_pct)
    fixed_sum = tot_product_cost + shared_ops + inputs.fixed_marketplace_fee
    if denom > 0:
        result.break_even_bundle_price = money(fixed_sum / denom)
    else:
        result.break_even_bundle_price = Decimal("0")
        warnings.append("Variable fee percentage equals or exceeds 100%. Break-even undefined.")

    # Cost Allocation per Item
    item_results = []
    total_shared_to_distribute = shared_ops + mp_comm + pg_fee

    for item in inputs.items:
        # Determine weight
        if inputs.allocation_method == "quantity_share":
            weight = safe_divide(item.quantity, tot_units)
        elif inputs.allocation_method == "price_share" and tot_standalone > 0:
            weight = safe_divide(item.total_individual_value, tot_standalone)
        else:  # cost_share default
            weight = safe_divide(item.total_cost, tot_product_cost) if tot_product_cost > 0 else Decimal("0")

        item_shared = money(total_shared_to_distribute * weight)
        item_tot_cost = item.total_cost + item_shared
        item_rev = money(inputs.bundle_selling_price * weight)
        item_prof = money(item_rev - item_tot_cost)
        item_margin = margin(item_prof, item_rev)

        item_results.append(BundleItemResult(
            sku=item.sku,
            name=item.name,
            quantity=item.quantity,
            direct_cost=item.total_cost,
            allocated_shared_cost=item_shared,
            total_cost=item_tot_cost,
            allocated_revenue=item_rev,
            allocated_profit=item_prof,
            profit_margin_pct=item_margin
        ))

    result.item_breakdowns = item_results
    result.allocation_explanation = f"Shared costs (₹{money(total_shared_to_distribute)}) allocated via '{inputs.allocation_method}'."
    result.warnings = warnings
    return result
