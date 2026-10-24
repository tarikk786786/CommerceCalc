"""
Shipping and fulfillment calculator for CommerceCalc.

Users must enter their own courier rate cards.
Do not assume universal rates — all rates are user-configurable.
"""
from decimal import Decimal
from dataclasses import dataclass, field
from typing import Optional, List
from .money import to_decimal, money, percent_of, safe_divide


@dataclass
class ShippingInputs:
    """Physical package and shipping parameters."""
    # Package dimensions (cm)
    length_cm: Decimal = Decimal("0")
    width_cm: Decimal = Decimal("0")
    height_cm: Decimal = Decimal("0")

    # Weight
    actual_weight_kg: Decimal = Decimal("0")
    dimensional_weight_divisor: Decimal = Decimal("5000")  # common, but verify with courier

    # Rates (user-configurable, no defaults assumed)
    forward_rate_per_500g: Decimal = Decimal("0")
    additional_500g_rate: Decimal = Decimal("0")
    reverse_rate_per_500g: Decimal = Decimal("0")
    rto_rate_per_500g: Decimal = Decimal("0")
    min_forward_charge: Decimal = Decimal("0")
    min_reverse_charge: Decimal = Decimal("0")
    pickup_fee: Decimal = Decimal("0")
    cod_collection_fee: Decimal = Decimal("0")     # flat fee
    cod_collection_pct: Decimal = Decimal("0")     # % of COD amount
    cod_order_value: Decimal = Decimal("0")
    handling_fee: Decimal = Decimal("0")
    fuel_surcharge_pct: Decimal = Decimal("0")

    # Courier name
    courier_name: str = "Custom Courier"
    weight_slab_grams: int = 500  # weight slab in grams (100g, 250g, 500g, 1000g, etc.)

    def __post_init__(self):
        numeric_fields = [
            "length_cm", "width_cm", "height_cm", "actual_weight_kg",
            "dimensional_weight_divisor", "forward_rate_per_500g",
            "additional_500g_rate", "reverse_rate_per_500g", "rto_rate_per_500g",
            "min_forward_charge", "min_reverse_charge", "pickup_fee",
            "cod_collection_fee", "cod_collection_pct", "cod_order_value",
            "handling_fee", "fuel_surcharge_pct",
        ]
        for f in numeric_fields:
            setattr(self, f, to_decimal(getattr(self, f)))


@dataclass
class ShippingResult:
    """Computed shipping costs."""
    volume_cc: Decimal = Decimal("0")
    dimensional_weight_kg: Decimal = Decimal("0")
    chargeable_weight_kg: Decimal = Decimal("0")
    weight_slabs: Decimal = Decimal("0")

    forward_delivery_cost: Decimal = Decimal("0")
    reverse_delivery_cost: Decimal = Decimal("0")
    rto_cost: Decimal = Decimal("0")
    cod_cost: Decimal = Decimal("0")
    pickup_fee: Decimal = Decimal("0")
    handling_fee: Decimal = Decimal("0")
    fuel_surcharge: Decimal = Decimal("0")

    total_forward_order_cost: Decimal = Decimal("0")
    total_reverse_cost: Decimal = Decimal("0")
    total_logistics_cost: Decimal = Decimal("0")

    shipping_cost_pct_of_selling: Decimal = Decimal("0")
    min_shipping_revenue_needed: Decimal = Decimal("0")
    expected_delivery_cost_per_success: Decimal = Decimal("0")

    warnings: List[str] = field(default_factory=list)


def calculate_shipping(inputs: ShippingInputs, selling_price: Decimal = Decimal("0"),
                       is_cod: bool = False) -> ShippingResult:
    """Calculate shipping costs based on user-provided rate card."""
    result = ShippingResult()
    warnings = []

    # Volume
    vol = inputs.length_cm * inputs.width_cm * inputs.height_cm
    result.volume_cc = money(vol)

    # Dimensional weight
    if inputs.dimensional_weight_divisor > 0:
        dim_wt = vol / inputs.dimensional_weight_divisor
    else:
        dim_wt = Decimal("0")
        warnings.append("Dimensional weight divisor is 0. Check courier specification.")
    result.dimensional_weight_kg = money(dim_wt)

    # Chargeable weight = max(actual, dimensional)
    chargeable = max(inputs.actual_weight_kg, dim_wt)
    result.chargeable_weight_kg = chargeable

    # Weight slabs
    slab_kg = to_decimal(inputs.weight_slab_grams) / Decimal("1000")
    if slab_kg > 0:
        import math
        slabs = Decimal(str(math.ceil(float(chargeable) / float(slab_kg))))
    else:
        slabs = Decimal("1")
    result.weight_slabs = slabs

    # Forward cost
    if inputs.forward_rate_per_500g > 0:
        if slabs <= 1:
            forward_cost = inputs.forward_rate_per_500g
        else:
            forward_cost = inputs.forward_rate_per_500g + (slabs - 1) * inputs.additional_500g_rate
        forward_cost = max(forward_cost, inputs.min_forward_charge)
    else:
        forward_cost = Decimal("0")
        if inputs.courier_name != "Custom Courier":
            warnings.append(f"Forward shipping rate not configured for {inputs.courier_name}.")
    result.forward_delivery_cost = money(forward_cost)

    # Reverse cost
    if inputs.reverse_rate_per_500g > 0:
        reverse_cost = inputs.reverse_rate_per_500g * slabs
        reverse_cost = max(reverse_cost, inputs.min_reverse_charge)
    else:
        reverse_cost = Decimal("0")
    result.reverse_delivery_cost = money(reverse_cost)

    # RTO cost
    rto_cost = inputs.rto_rate_per_500g * slabs if inputs.rto_rate_per_500g > 0 else Decimal("0")
    result.rto_cost = money(rto_cost)

    # COD cost
    cod_cost = Decimal("0")
    if is_cod:
        cod_cost = inputs.cod_collection_fee
        if inputs.cod_collection_pct > 0 and selling_price > 0:
            cod_cost += percent_of(selling_price, inputs.cod_collection_pct)
    result.cod_cost = money(cod_cost)

    # Ancillary
    result.pickup_fee = inputs.pickup_fee
    result.handling_fee = inputs.handling_fee

    # Fuel surcharge on forward
    fuel = percent_of(forward_cost, inputs.fuel_surcharge_pct)
    result.fuel_surcharge = money(fuel)

    # Totals
    result.total_forward_order_cost = money(
        forward_cost + fuel + inputs.pickup_fee + inputs.handling_fee + cod_cost
    )
    result.total_reverse_cost = money(reverse_cost)
    result.total_logistics_cost = money(
        result.total_forward_order_cost + result.total_reverse_cost
    )

    # Shipping as % of selling price
    sp = to_decimal(selling_price)
    if sp > 0:
        result.shipping_cost_pct_of_selling = money(
            safe_divide(result.total_forward_order_cost, sp) * Decimal("100")
        )
        result.min_shipping_revenue_needed = result.total_forward_order_cost

    result.expected_delivery_cost_per_success = result.total_forward_order_cost
    result.warnings = warnings
    return result
