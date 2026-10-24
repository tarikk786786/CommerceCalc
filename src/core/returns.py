"""
Returns, RTO, and failed delivery loss calculator for CommerceCalc.

Inputs are user-defined probability assumptions (0-100%).
Results are EXPECTED losses, not actual recorded transactions.
"""
from decimal import Decimal
from dataclasses import dataclass, field
from typing import List
from .money import to_decimal, money, percent_of, safe_divide, pct


@dataclass
class ReturnRTOInputs:
    """Risk assumptions for returns, refunds, and RTO."""
    total_orders: int = 100

    # Rate inputs (as percentages 0-100)
    return_rate_pct: Decimal = Decimal("0")
    rto_rate_pct: Decimal = Decimal("0")
    cancellation_rate_pct: Decimal = Decimal("0")
    damage_rate_pct: Decimal = Decimal("0")

    # Cost per event
    product_cost_per_unit: Decimal = Decimal("0")
    forward_shipping_cost: Decimal = Decimal("0")
    reverse_shipping_cost: Decimal = Decimal("0")
    rto_shipping_cost: Decimal = Decimal("0")
    refund_amount_per_return: Decimal = Decimal("0")
    non_refundable_fees_per_return: Decimal = Decimal("0")
    restocking_cost_per_unit: Decimal = Decimal("0")
    replacement_cost_per_unit: Decimal = Decimal("0")
    recovery_value_per_returned_unit: Decimal = Decimal("0")

    # What % of returns are resalable
    resalable_pct: Decimal = Decimal("70")

    def __post_init__(self):
        for f in self.__dataclass_fields__:
            val = getattr(self, f)
            if isinstance(val, (int, float, str)) and not isinstance(val, bool) and f != "total_orders":
                setattr(self, f, to_decimal(val))

    def validate(self) -> List[str]:
        errors = []
        for rate_field in ["return_rate_pct", "rto_rate_pct", "cancellation_rate_pct", "damage_rate_pct"]:
            val = getattr(self, rate_field)
            if val < 0 or val > 100:
                errors.append(f"{rate_field} must be 0-100%, got {val}%")
        total_loss_rate = (self.return_rate_pct + self.rto_rate_pct
                          + self.cancellation_rate_pct)
        if total_loss_rate > 100:
            errors.append(
                f"Combined return/RTO/cancellation rate ({total_loss_rate}%) exceeds 100%."
            )
        return errors


@dataclass
class ReturnRTOResult:
    """Expected loss breakdown from returns and RTO."""
    # Volumes
    expected_successful_deliveries: Decimal = Decimal("0")
    expected_returns: Decimal = Decimal("0")
    expected_rto: Decimal = Decimal("0")
    expected_cancellations: Decimal = Decimal("0")
    expected_damaged: Decimal = Decimal("0")
    expected_resalable_returns: Decimal = Decimal("0")

    # Financial impact
    recovered_inventory_value: Decimal = Decimal("0")
    unrecovered_product_cost: Decimal = Decimal("0")
    logistics_loss: Decimal = Decimal("0")
    refund_loss: Decimal = Decimal("0")
    non_refundable_fee_loss: Decimal = Decimal("0")
    restocking_cost_total: Decimal = Decimal("0")
    replacement_cost_total: Decimal = Decimal("0")

    # Summary
    expected_net_loss_per_order: Decimal = Decimal("0")
    total_expected_loss: Decimal = Decimal("0")
    adjusted_profit_per_successful_order: Decimal = Decimal("0")
    break_even_price_adjustment: Decimal = Decimal("0")

    warnings: List[str] = field(default_factory=list)


def calculate_return_rto_loss(inputs: ReturnRTOInputs,
                               base_profit_per_successful_order: Decimal = Decimal("0")
                               ) -> ReturnRTOResult:
    """
    Calculate expected losses from returns, RTO, and failed deliveries.

    Args:
        inputs: Risk assumptions
        base_profit_per_successful_order: Profit before accounting for return risk

    Returns:
        ReturnRTOResult with expected loss breakdown
    """
    result = ReturnRTOResult()
    warnings = inputs.validate()

    n = to_decimal(inputs.total_orders)

    # Expected volumes
    return_n = money(n * pct(inputs.return_rate_pct))
    rto_n = money(n * pct(inputs.rto_rate_pct))
    cancel_n = money(n * pct(inputs.cancellation_rate_pct))
    damage_n = money(n * pct(inputs.damage_rate_pct))
    successful_n = money(
        max(n - return_n - rto_n - cancel_n, Decimal("0"))
    )
    resalable_n = money(return_n * pct(inputs.resalable_pct))

    result.expected_successful_deliveries = successful_n
    result.expected_returns = return_n
    result.expected_rto = rto_n
    result.expected_cancellations = cancel_n
    result.expected_damaged = damage_n
    result.expected_resalable_returns = resalable_n

    # Inventory recovery
    result.recovered_inventory_value = money(
        resalable_n * inputs.recovery_value_per_returned_unit
    )
    result.unrecovered_product_cost = money(
        (return_n - resalable_n) * inputs.product_cost_per_unit
    )

    # Logistics losses
    # Returns: paid forward (already counted) + reverse shipping
    return_logistics = money(return_n * inputs.reverse_shipping_cost)
    # RTO: forward shipping wasted + RTO charge
    rto_logistics = money(rto_n * (inputs.forward_shipping_cost + inputs.rto_shipping_cost))
    result.logistics_loss = money(return_logistics + rto_logistics)

    # Refund losses
    result.refund_loss = money(return_n * inputs.refund_amount_per_return)
    result.non_refundable_fee_loss = money(
        (return_n + rto_n) * inputs.non_refundable_fees_per_return
    )

    # Restocking & replacement
    result.restocking_cost_total = money(return_n * inputs.restocking_cost_per_unit)
    result.replacement_cost_total = money(damage_n * inputs.replacement_cost_per_unit)

    # Total loss
    total_loss = money(
        result.unrecovered_product_cost
        + result.logistics_loss
        + result.refund_loss
        + result.non_refundable_fee_loss
        + result.restocking_cost_total
        + result.replacement_cost_total
        - result.recovered_inventory_value
    )
    result.total_expected_loss = max(total_loss, Decimal("0"))

    # Per-order impact
    result.expected_net_loss_per_order = money(safe_divide(result.total_expected_loss, n))

    # Adjusted profit per successful order
    profit = to_decimal(base_profit_per_successful_order)
    result.adjusted_profit_per_successful_order = money(
        profit - result.expected_net_loss_per_order
    )

    # Break-even price adjustment per order
    result.break_even_price_adjustment = result.expected_net_loss_per_order

    if warnings:
        result.warnings = warnings
    return result
