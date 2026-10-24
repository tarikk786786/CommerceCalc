"""
Inventory and Reorder Calculator for CommerceCalc.

Calculates:
- Available-to-sell inventory
- Runout days / Days of Inventory Remaining (DIR)
- Reorder Point (ROP) = (Daily Demand * Lead Time) + Safety Stock
- Economic Order Quantity (EOQ) or Suggested Reorder Quantity
- Inventory holding / carrying cost
- Cash tied up in stock
- GMROI (Gross Margin Return on Investment)
"""
from decimal import Decimal
import math
from dataclasses import dataclass, field
from typing import List, Optional
from .money import to_decimal, money, pct, safe_divide


@dataclass
class InventoryInputs:
    sku: str = ""
    unit_cost: Decimal = Decimal("0")
    selling_price: Decimal = Decimal("0")

    available_stock: int = 0
    reserved_stock: int = 0
    incoming_stock: int = 0  # stock in transit

    average_daily_sales: Decimal = Decimal("0")
    lead_time_days: int = 14
    safety_stock_days: int = 7
    minimum_order_quantity: int = 1  # MOQ

    annual_holding_cost_pct: Decimal = Decimal("18.0")  # e.g. 15-25% typical warehousing + capital cost
    order_fixed_placement_cost: Decimal = Decimal("500")  # Cost to place an order (paperwork, freight admin)

    def __post_init__(self):
        for f in ["unit_cost", "selling_price", "average_daily_sales",
                  "annual_holding_cost_pct", "order_fixed_placement_cost"]:
            setattr(self, f, to_decimal(getattr(self, f)))


@dataclass
class InventoryResult:
    available_to_sell: int = 0
    total_effective_stock: int = 0
    days_of_inventory_remaining: Decimal = Decimal("0")
    stockout_risk_status: str = "Normal"  # Normal, Reorder Soon, Immediate Stockout Risk

    safety_stock_units: int = 0
    lead_time_demand_units: int = 0
    reorder_point_units: int = 0
    reorder_needed: bool = False
    suggested_reorder_quantity: int = 0

    total_inventory_value: Decimal = Decimal("0")
    annual_carrying_cost: Decimal = Decimal("0")
    estimated_eoq: int = 0
    gmroi_pct: Decimal = Decimal("0")

    warnings: List[str] = field(default_factory=list)


def calculate_inventory(inputs: InventoryInputs) -> InventoryResult:
    result = InventoryResult()
    warnings = []

    ats = max(inputs.available_stock - inputs.reserved_stock, 0)
    eff_stock = ats + inputs.incoming_stock
    result.available_to_sell = ats
    result.total_effective_stock = eff_stock

    ads = inputs.average_daily_sales
    if ads > 0:
        dir_days = safe_divide(eff_stock, ads)
        result.days_of_inventory_remaining = money(dir_days)
    else:
        result.days_of_inventory_remaining = Decimal("9999")
        warnings.append("Average daily sales is 0. Runout time is infinite.")

    # Reorder Point calculation
    # ROP = (Lead Time * Daily Demand) + Safety Stock
    lt_units = math.ceil(float(ads * to_decimal(inputs.lead_time_days)))
    ss_units = math.ceil(float(ads * to_decimal(inputs.safety_stock_days)))
    rop = lt_units + ss_units

    result.lead_time_demand_units = lt_units
    result.safety_stock_units = ss_units
    result.reorder_point_units = rop
    result.reorder_needed = eff_stock <= rop

    # Stockout risk status
    if eff_stock <= ss_units:
        result.stockout_risk_status = "CRITICAL: Stockout Imminent"
    elif eff_stock <= rop:
        result.stockout_risk_status = "WARNING: Below Reorder Point"
    else:
        result.stockout_risk_status = "Healthy"

    # Suggested Reorder Quantity: bring inventory up to (ROP + 30 days demand) or MOQ
    target_cover_days = 30
    target_inventory = rop + math.ceil(float(ads * to_decimal(target_cover_days)))
    deficit = max(target_inventory - eff_stock, 0)
    suggested_qty = max(deficit, inputs.minimum_order_quantity) if result.reorder_needed else 0
    result.suggested_reorder_quantity = suggested_qty

    # Inventory Value & Holding Cost
    tot_val = inputs.unit_cost * to_decimal(eff_stock)
    result.total_inventory_value = money(tot_val)
    annual_carry = tot_val * pct(inputs.annual_holding_cost_pct)
    result.annual_carrying_cost = money(annual_carry)

    # EOQ = sqrt( (2 * Annual Demand * Order Cost) / Holding Cost per unit )
    annual_demand = ads * Decimal("365")
    holding_cost_per_unit = inputs.unit_cost * pct(inputs.annual_holding_cost_pct)
    if holding_cost_per_unit > 0 and annual_demand > 0 and inputs.order_fixed_placement_cost > 0:
        eoq = math.sqrt(float((2 * annual_demand * inputs.order_fixed_placement_cost) / holding_cost_per_unit))
        result.estimated_eoq = max(math.ceil(eoq), inputs.minimum_order_quantity)
    else:
        result.estimated_eoq = inputs.minimum_order_quantity

    # GMROI = (Annual Gross Margin) / (Average Inventory Investment)
    annual_gross_margin = (inputs.selling_price - inputs.unit_cost) * annual_demand
    if tot_val > 0:
        result.gmroi_pct = money(safe_divide(annual_gross_margin, tot_val) * Decimal("100"))

    result.warnings = warnings
    return result
