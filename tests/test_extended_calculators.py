"""
Tests for extended calculators:
- Discounts & promotions
- Bundles
- Dropshipping
- Digital products
- Inventory & reorder
- Landed cost & imports
- Cash flow & settlements
"""
from decimal import Decimal
import pytest
from src.core.discounts import PromotionInputs, calculate_promotion
from src.core.bundles import BundleInputs, BundleItem, calculate_bundle
from src.core.dropshipping import DropshipInputs, calculate_dropship
from src.core.digital import DigitalProductInputs, calculate_digital_product
from src.core.inventory import InventoryInputs, calculate_inventory
from src.core.landed_cost import LandedCostInputs, calculate_landed_cost
from src.core.settlement import SettlementInputs, calculate_settlement


def test_discounts_percentage():
    inp = PromotionInputs(
        original_price=Decimal("1000"),
        promo_type="percentage",
        discount_value=Decimal("20"),
        baseline_units_sold=100,
        baseline_unit_cost=Decimal("400"),
        baseline_shipping_and_fees=Decimal("100"),
    )
    res = calculate_promotion(inp)
    assert res.total_customer_discount == Decimal("200.00")
    assert res.customer_pays == Decimal("800.00")
    assert res.effective_discount_pct == Decimal("20.00")
    assert res.baseline_profit_per_unit == Decimal("500.00")
    assert res.promo_profit_per_unit == Decimal("300.00")
    assert res.is_profitable is True
    assert res.required_units_for_same_profit > 100


def test_bundles_cost_allocation():
    items = [
        BundleItem(sku="SKU-A", name="Item A", unit_cost=Decimal("100"), quantity=1, individual_selling_price=Decimal("300")),
        BundleItem(sku="SKU-B", name="Item B", unit_cost=Decimal("200"), quantity=1, individual_selling_price=Decimal("500")),
    ]
    inp = BundleInputs(
        items=items,
        bundle_selling_price=Decimal("699"),
        shared_packaging_cost=Decimal("20"),
        combined_shipping_cost=Decimal("50"),
        marketplace_fee_pct=Decimal("10"),
    )
    res = calculate_bundle(inp)
    assert res.total_standalone_price == Decimal("800.00")
    assert res.total_product_cost == Decimal("300.00")
    assert res.bundle_discount_amount == Decimal("101.00")
    assert res.bundle_net_profit > 0
    assert len(res.item_breakdowns) == 2


def test_dropshipping_economics():
    inp = DropshipInputs(
        supplier_price_foreign=Decimal("5"),
        supplier_shipping_foreign=Decimal("2"),
        exchange_rate=Decimal("84"),
        customer_selling_price_inr=Decimal("1499"),
        payment_gateway_pct=Decimal("2"),
        ad_spend_per_order_inr=Decimal("400"),
    )
    res = calculate_dropship(inp)
    # foreign cost = 7 USD * 84 = 588 INR
    assert res.landed_supplier_cost_inr == Decimal("588.00")
    assert res.profit_per_order > 0
    assert res.is_profitable is True
    assert res.max_allowable_cac > Decimal("0")


def test_digital_products_amortization():
    inp = DigitalProductInputs(
        selling_price=Decimal("999"),
        expected_sales_units=100,
        creation_cost=Decimal("20000"),
        hosting_delivery_per_unit=Decimal("10"),
        platform_fee_pct=Decimal("5"),
        payment_gateway_pct=Decimal("2"),
    )
    res = calculate_digital_product(inp)
    assert res.total_upfront_cost == Decimal("20000.00")
    assert res.amortized_cost_per_unit == Decimal("200.00")
    assert res.units_needed_to_break_even > 0
    assert res.is_profitable is True


def test_inventory_reorder_point():
    inp = InventoryInputs(
        sku="TEST-SKU",
        unit_cost=Decimal("250"),
        selling_price=Decimal("500"),
        available_stock=50,
        reserved_stock=10,
        average_daily_sales=Decimal("5"),
        lead_time_days=10,
        safety_stock_days=5,
    )
    res = calculate_inventory(inp)
    assert res.available_to_sell == 40
    # Demand during lead time = 5 * 10 = 50. Safety stock = 5 * 5 = 25. ROP = 75.
    assert res.lead_time_demand_units == 50
    assert res.safety_stock_units == 25
    assert res.reorder_point_units == 75
    assert res.reorder_needed is True  # 40 <= 75


def test_landed_cost_calculation():
    inp = LandedCostInputs(
        shipment_units=100,
        supplier_unit_price_foreign=Decimal("10"),
        exchange_rate=Decimal("80"),
        bank_fx_fee_pct=Decimal("0"),
        international_freight_foreign=Decimal("100"),
        marine_cargo_insurance_inr=Decimal("1000"),
        basic_customs_duty_pct=Decimal("10"),
        sws_pct=Decimal("10"),
        import_igst_rate_pct=Decimal("18"),
        is_igst_recoverable_as_itc=True,
    )
    res = calculate_landed_cost(inp)
    # FOB = 100 * 10 * 80 = 80,000 INR
    # Freight = 100 * 80 = 8,000 INR
    # Insurance = 1,000 INR
    # CIF = 89,000 INR
    assert res.cif_assessable_value_inr == Decimal("89000.00")
    assert res.bcd_amount_inr == Decimal("8900.00")  # 10% of 89,000
    assert res.sws_amount_inr == Decimal("890.00")   # 10% of 8,900
    assert res.landed_cost_per_unit > Decimal("0")


def test_settlement_reconciliation():
    inp = SettlementInputs(
        gross_order_sales_inr=Decimal("100000"),
        marketplace_commission_inr=Decimal("10000"),
        marketplace_shipping_deductions_inr=Decimal("5000"),
        marketplace_fixed_closing_fees_inr=Decimal("1000"),
        gst_tcs_rate_pct=Decimal("1.0"),
        income_tax_tds_rate_pct=Decimal("0.1"),
        gst_on_marketplace_fees_pct=Decimal("18.0"),
        actual_product_cost_inr=Decimal("40000"),
    )
    res = calculate_settlement(inp)
    assert res.gross_sales == Decimal("100000.00")
    assert res.total_platform_fees_before_gst == Decimal("16000.00")
    assert res.gst_on_platform_fees == Decimal("2880.00")  # 18% of 16,000
    assert res.tcs_withheld == Decimal("1000.00")          # 1% of 100,000
    assert res.tds_withheld == Decimal("100.00")           # 0.1% of 100,000
    assert res.net_bank_settlement < Decimal("100000.00")
    assert res.net_bank_settlement > Decimal("0")
