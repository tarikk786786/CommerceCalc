"""
Advertising and ROAS calculator for CommerceCalc.

Handles Meta Ads, Google Ads, marketplace ads, affiliates, etc.
Clearly distinguishes ROAS from profitability.
"""
from decimal import Decimal
from dataclasses import dataclass, field
from typing import Optional, List, Dict
from .money import to_decimal, money, percent_of, safe_divide, pct


@dataclass
class AdvertisingInputs:
    """Advertising campaign inputs."""
    ad_spend: Decimal = Decimal("0")
    impressions: int = 0
    clicks: int = 0
    sessions: int = 0
    conversions: int = 0
    attributed_orders: int = 0
    attributed_revenue: Decimal = Decimal("0")        # Revenue from ad-attributed orders
    net_revenue: Decimal = Decimal("0")               # After removing sales tax
    contribution_margin_before_adv: Decimal = Decimal("0")  # As % (e.g. 40 for 40%)
    channel: str = "Custom"
    campaign_name: str = ""

    def __post_init__(self):
        for f in ["ad_spend", "attributed_revenue", "net_revenue", "contribution_margin_before_adv"]:
            setattr(self, f, to_decimal(getattr(self, f)))


@dataclass
class AdvertisingResult:
    """Computed advertising metrics."""
    # Efficiency metrics
    cpm: Decimal = Decimal("0")           # Cost per 1000 impressions
    cpc: Decimal = Decimal("0")           # Cost per click
    ctr_pct: Decimal = Decimal("0")       # Click-through rate %
    conversion_rate_pct: Decimal = Decimal("0")
    cost_per_acquisition: Decimal = Decimal("0")
    customer_acquisition_cost: Decimal = Decimal("0")

    # Revenue metrics
    average_order_value: Decimal = Decimal("0")
    roas: Decimal = Decimal("0")          # Revenue / Ad Spend
    break_even_roas: Decimal = Decimal("0")
    acos_pct: Decimal = Decimal("0")      # Ad Cost of Sales % (ads / attributed rev)
    tacos_pct: Decimal = Decimal("0")     # Total ACoS (ads / total net revenue)

    # Profit metrics
    contribution_profit_before_adv: Decimal = Decimal("0")
    contribution_profit_after_adv: Decimal = Decimal("0")
    profit_per_acquired_customer: Decimal = Decimal("0")

    # Break-even analysis
    break_even_cac: Decimal = Decimal("0")
    max_allowable_cac: Decimal = Decimal("0")
    max_cpc: Decimal = Decimal("0")
    target_roas: Decimal = Decimal("0")
    required_conversion_rate_pct: Decimal = Decimal("0")
    required_revenue_to_break_even: Decimal = Decimal("0")
    required_orders_to_recover_spend: Decimal = Decimal("0")

    warnings: List[str] = field(default_factory=list)


def calculate_advertising(inputs: AdvertisingInputs) -> AdvertisingResult:
    """Calculate complete advertising metrics."""
    result = AdvertisingResult()
    warnings = []

    spend = inputs.ad_spend
    impr = to_decimal(inputs.impressions)
    clicks_d = to_decimal(inputs.clicks)
    orders_d = to_decimal(max(inputs.attributed_orders, 0))
    attr_rev = inputs.attributed_revenue
    net_rev = inputs.net_revenue
    cm_pct = pct(inputs.contribution_margin_before_adv)  # e.g. 0.40

    # Warn if margin is non-positive
    if cm_pct <= 0:
        warnings.append(
            "Contribution margin before advertising is 0 or negative. "
            "Break-even ROAS is undefined — do not advertise at a loss."
        )

    # --- Efficiency Metrics ---
    if impr > 0:
        result.cpm = money(safe_divide(spend, impr) * Decimal("1000"))
    if clicks_d > 0:
        result.cpc = money(safe_divide(spend, clicks_d))
    if impr > 0:
        result.ctr_pct = money(safe_divide(clicks_d, impr) * Decimal("100"))
    sessions_d = to_decimal(inputs.sessions) if inputs.sessions > 0 else clicks_d
    if sessions_d > 0:
        result.conversion_rate_pct = money(safe_divide(orders_d, sessions_d) * Decimal("100"))

    if orders_d > 0:
        result.cost_per_acquisition = money(safe_divide(spend, orders_d))
        result.customer_acquisition_cost = result.cost_per_acquisition
        result.average_order_value = money(safe_divide(attr_rev, orders_d))

    # --- ROAS ---
    if spend > 0 and attr_rev > 0:
        result.roas = money(safe_divide(attr_rev, spend))
    elif spend > 0:
        warnings.append("No attributed revenue — ROAS is undefined.")

    # Break-even ROAS = 1 / contribution_margin (before adv)
    # At break-even ROAS, adv revenue * margin = ad spend
    # So: break_even_roas = 1 / margin (as decimal)
    if cm_pct > 0:
        result.break_even_roas = money(Decimal("1") / cm_pct)
    else:
        result.break_even_roas = Decimal("0")
        warnings.append(
            "Cannot compute break-even ROAS: contribution margin <= 0. "
            "Verify that GST and non-advertising costs are excluded correctly."
        )

    # ACoS and TACoS
    if attr_rev > 0:
        result.acos_pct = money(safe_divide(spend, attr_rev) * Decimal("100"))
    if net_rev > 0:
        result.tacos_pct = money(safe_divide(spend, net_rev) * Decimal("100"))

    # --- Contribution Profit ---
    # contribution_profit_before_adv = attributed_revenue * contribution_margin_pct
    result.contribution_profit_before_adv = money(attr_rev * cm_pct)
    result.contribution_profit_after_adv = money(result.contribution_profit_before_adv - spend)

    if orders_d > 0:
        result.profit_per_acquired_customer = money(
            safe_divide(result.contribution_profit_after_adv, orders_d)
        )

    # --- Break-even Analysis ---
    if cm_pct > 0:
        # Max CAC = contribution margin per order (at AOV)
        result.max_allowable_cac = money(result.average_order_value * cm_pct)
        result.break_even_cac = result.max_allowable_cac

        # Max CPC: if conversion rate is known
        if result.conversion_rate_pct > 0:
            conv_rate = pct(result.conversion_rate_pct)
            result.max_cpc = money(result.max_allowable_cac * conv_rate)

        # Target ROAS = Break-even ROAS (for not losing money on ads)
        result.target_roas = result.break_even_roas

        # Required conversion rate for profitable ads at current CPC
        if result.cpc > 0 and result.average_order_value > 0:
            # max_cac = aov * margin → cpc / conv_rate = max_cac → conv_rate = cpc / max_cac
            result.required_conversion_rate_pct = money(
                safe_divide(result.cpc, result.max_allowable_cac) * Decimal("100")
            )

        # Required revenue to break even
        if cm_pct > 0:
            result.required_revenue_to_break_even = money(safe_divide(spend, cm_pct))

        # Required orders
        if result.average_order_value > 0 and cm_pct > 0:
            contrib_per_order = result.average_order_value * cm_pct
            result.required_orders_to_recover_spend = money(
                safe_divide(spend, contrib_per_order)
            )

    result.warnings = warnings
    return result
