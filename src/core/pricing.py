"""
Target selling price solver for CommerceCalc.

Solves for the minimum selling price needed to achieve a target
profit, margin, or markup — accounting for percentage-based fees
that depend on selling price (solving circular dependencies).
"""
from decimal import Decimal, ROUND_HALF_UP
from dataclasses import dataclass, field
from typing import Optional, List, Tuple, Dict
from .money import to_decimal, money, pct, percent_of, safe_divide, round_price


@dataclass
class PriceSolverInputs:
    """All costs and fee structure inputs for the price solver."""
    # Fixed costs (per unit)
    product_cost: Decimal = Decimal("0")
    packaging_cost: Decimal = Decimal("0")
    fixed_fulfillment_cost: Decimal = Decimal("0")   # shipping, handling
    fixed_marketplace_fee: Decimal = Decimal("0")    # fixed closing fee
    fixed_payment_fee: Decimal = Decimal("0")
    fixed_advertising_cost: Decimal = Decimal("0")
    fixed_overhead: Decimal = Decimal("0")
    fixed_return_rto_cost: Decimal = Decimal("0")
    other_fixed_cost: Decimal = Decimal("0")

    # Percentage costs (as % of selling price)
    marketplace_commission_pct: Decimal = Decimal("0")
    payment_gateway_pct: Decimal = Decimal("0")
    affiliate_pct: Decimal = Decimal("0")
    advertising_pct: Decimal = Decimal("0")      # if expressed as % of revenue
    seller_funded_discount_pct: Decimal = Decimal("0")

    # GST
    gst_rate_pct: Decimal = Decimal("0")
    gst_inclusive_in_price: bool = False          # Is target price GST-inclusive?
    gst_on_fees: bool = False                     # Do fees attract GST?
    fees_gst_rate_pct: Decimal = Decimal("18")   # GST on marketplace fees

    # Quantity assumption
    quantity: int = 1

    def __post_init__(self):
        for f in self.__dataclass_fields__:
            val = getattr(self, f)
            if isinstance(val, (int, float, str)) and not isinstance(val, bool):
                setattr(self, f, to_decimal(val))

    @property
    def total_fixed_cost(self) -> Decimal:
        return money(
            self.product_cost
            + self.packaging_cost
            + self.fixed_fulfillment_cost
            + self.fixed_marketplace_fee
            + self.fixed_payment_fee
            + self.fixed_advertising_cost
            + self.fixed_overhead
            + self.fixed_return_rto_cost
            + self.other_fixed_cost
        )

    @property
    def total_variable_pct(self) -> Decimal:
        """Sum of all percentage-based costs as decimal fraction."""
        total_pct = (
            self.marketplace_commission_pct
            + self.payment_gateway_pct
            + self.affiliate_pct
            + self.advertising_pct
            + self.seller_funded_discount_pct
        )
        return pct(total_pct)


@dataclass
class PriceSolverTarget:
    """What the user wants to achieve."""
    objective: str = "break_even"
    # Objectives: 'break_even', 'target_profit', 'target_margin', 'target_markup'
    target_profit_per_unit: Decimal = Decimal("0")
    target_margin_pct: Decimal = Decimal("0")
    target_markup_pct: Decimal = Decimal("0")
    price_rounding_method: str = "nearest"
    price_rounding_ending: str = "99"

    def __post_init__(self):
        for f in ["target_profit_per_unit", "target_margin_pct", "target_markup_pct"]:
            setattr(self, f, to_decimal(getattr(self, f)))


@dataclass
class PriceSolverResult:
    """Result of the price solving calculation."""
    break_even_price: Decimal = Decimal("0")
    recommended_price: Decimal = Decimal("0")
    recommended_price_incl_gst: Decimal = Decimal("0")
    taxable_value: Decimal = Decimal("0")
    contribution_profit_per_unit: Decimal = Decimal("0")
    total_profit_at_quantity: Decimal = Decimal("0")

    # Risk analysis
    max_tolerable_adv_cost: Decimal = Decimal("0")
    max_allowable_cac: Decimal = Decimal("0")
    max_discount_before_breakeven: Decimal = Decimal("0")

    # Sensitivity
    sensitivity: Dict[str, str] = field(default_factory=dict)

    # Meta
    is_feasible: bool = True
    infeasibility_reason: str = ""
    formula_explanation: str = ""
    warnings: List[str] = field(default_factory=list)


def solve_target_price(
    inputs: PriceSolverInputs,
    target: PriceSolverTarget,
) -> PriceSolverResult:
    """
    Solve for the selling price that achieves the given target.

    MATH:
    Let P = net revenue per unit (taxable selling price, excl GST)
    Let F = total fixed costs
    Let V = sum of variable cost % (as decimal, e.g. 0.15 for 15%)
    Let T = target profit

    Revenue after variable fees = P * (1 - V)
    Profit = P * (1 - V) - F = T
    → P = (F + T) / (1 - V)

    If target is margin M%:
    Profit = P * M/100
    → P * (1 - V) - F = P * M/100
    → P * (1 - V - M/100) = F
    → P = F / (1 - V - M/100)

    If 1 - V - M/100 <= 0, there is NO valid solution.
    """
    result = PriceSolverResult()
    warnings = []

    fixed = inputs.total_fixed_cost
    var_rate = inputs.total_variable_pct   # as decimal fraction

    if var_rate >= Decimal("1"):
        result.is_feasible = False
        result.infeasibility_reason = (
            f"Variable cost percentage ({var_rate * 100}%) equals or exceeds 100% of revenue. "
            "No valid selling price exists."
        )
        return result

    # --- Break-even price ---
    # P * (1 - var_rate) = fixed
    # P = fixed / (1 - var_rate)
    denom_be = Decimal("1") - var_rate
    if denom_be <= Decimal("0"):
        result.is_feasible = False
        result.infeasibility_reason = "Variable costs consume entire revenue. Cannot break even."
        return result

    break_even_taxable = fixed / denom_be
    result.break_even_price = money(break_even_taxable)

    # --- Target price based on objective ---
    obj = target.objective

    if obj == "break_even":
        target_taxable = break_even_taxable

    elif obj == "target_profit":
        t_profit = target.target_profit_per_unit
        # P = (fixed + t_profit) / (1 - var_rate)
        target_taxable = (fixed + t_profit) / denom_be

    elif obj == "target_margin":
        m = pct(target.target_margin_pct)
        # P * (1 - var_rate - m) = fixed
        denom_m = Decimal("1") - var_rate - m
        if denom_m <= Decimal("0"):
            result.is_feasible = False
            result.infeasibility_reason = (
                f"Target margin {target.target_margin_pct}% cannot be achieved "
                f"with current variable costs ({var_rate * 100:.1f}%). "
                f"Reduce costs or target margin."
            )
            return result
        target_taxable = fixed / denom_m

    elif obj == "target_markup":
        mu = pct(target.target_markup_pct)
        # Markup = profit / cost → profit = cost * mu
        # (fixed + cost * mu) — but cost is also fixed here
        # profit = P * (1 - var_rate) - fixed
        # profit = fixed * mu   [markup on total fixed cost]
        t_profit = inputs.total_fixed_cost * mu
        target_taxable = (fixed + t_profit) / denom_be

    else:
        target_taxable = break_even_taxable
        warnings.append(f"Unknown objective '{obj}', defaulted to break-even.")

    result.taxable_value = money(target_taxable)

    # Apply GST if price is GST-exclusive
    if not inputs.gst_inclusive_in_price and inputs.gst_rate_pct > 0:
        gst_amt = percent_of(target_taxable, inputs.gst_rate_pct)
        result.recommended_price_incl_gst = money(target_taxable + gst_amt)
    else:
        result.recommended_price_incl_gst = money(target_taxable)

    # Round the recommended price
    rounded = round_price(
        result.recommended_price_incl_gst,
        method=target.price_rounding_method,
        ending=target.price_rounding_ending,
    )
    result.recommended_price = rounded

    # Contribution profit at recommended price
    rounded_taxable = money(
        rounded / (Decimal("1") + pct(inputs.gst_rate_pct))
        if inputs.gst_rate_pct > 0 and not inputs.gst_inclusive_in_price
        else rounded
    )
    variable_fees_at_rounded = rounded_taxable * var_rate
    result.contribution_profit_per_unit = money(
        rounded_taxable - variable_fees_at_rounded - fixed
    )
    result.total_profit_at_quantity = money(
        result.contribution_profit_per_unit * to_decimal(inputs.quantity)
    )

    # Max tolerable advertising cost (at recommended price, to break even)
    result.max_tolerable_adv_cost = money(
        max(result.contribution_profit_per_unit, Decimal("0"))
    )

    # Max discount before break-even
    result.max_discount_before_breakeven = money(
        max(result.recommended_price - result.break_even_price, Decimal("0"))
    )

    # Sensitivity analysis
    sensitivity = {}
    # 1% increase in marketplace fee
    test_var_rate = var_rate + Decimal("0.01")
    if test_var_rate < Decimal("1"):
        new_price = fixed / (Decimal("1") - test_var_rate)
        sensitivity["1% marketplace fee increase"] = f"+₹{money(new_price - target_taxable)}"

    # 10% shipping increase
    new_fixed = fixed + percent_of(inputs.fixed_fulfillment_cost, Decimal("10"))
    new_price = new_fixed / denom_be
    sensitivity["10% shipping cost increase"] = f"+₹{money(new_price - target_taxable)}"

    # 2% higher return rate
    test_return = inputs.fixed_return_rto_cost + money(target_taxable * Decimal("0.02"))
    new_fixed2 = fixed + test_return
    new_price2 = new_fixed2 / denom_be
    sensitivity["2% higher return rate"] = f"+₹{money(new_price2 - target_taxable)}"

    result.sensitivity = sensitivity

    # Formula explanation
    result.formula_explanation = (
        f"Target Taxable Price = (Fixed Costs + Target Profit) / (1 - Variable Cost Rate)\n"
        f"= (₹{money(fixed)} + ₹{money(target.target_profit_per_unit)}) / "
        f"(1 - {var_rate * 100:.2f}%)\n"
        f"= ₹{money(target_taxable)}\n\n"
        f"Fixed Costs: ₹{money(fixed)}\n"
        f"Variable Rate: {var_rate * 100:.2f}%\n"
        f"GST Rate: {inputs.gst_rate_pct}%"
    )

    result.warnings = warnings
    return result
