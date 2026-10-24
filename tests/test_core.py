"""
Comprehensive test suite for CommerceCalc financial engine.

All expected values are derived independently from the implementation.
Tests cover the PRD-specified test cases plus edge cases.
"""
import pytest
import sys
from pathlib import Path
from decimal import Decimal

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.money import (
    to_decimal, money, pct, percent_of, add_percent,
    extract_tax_inclusive, apply_tax_exclusive,
    safe_divide, margin, markup, round_price
)
from src.core.tax import GSTConfig, calculate_gst
from src.core.profit import ProductCost, SellingDetails, SellingExpenses, calculate_profit
from src.core.pricing import PriceSolverInputs, PriceSolverTarget, solve_target_price
from src.core.returns import ReturnRTOInputs, calculate_return_rto_loss
from src.core.advertising import AdvertisingInputs, calculate_advertising
from src.core.shipping import ShippingInputs, calculate_shipping


# ─────────────────────────────────────────────────────────────────
# 1. MONEY / DECIMAL ARITHMETIC
# ─────────────────────────────────────────────────────────────────

class TestMoneyArithmetic:

    def test_to_decimal_from_int(self):
        assert to_decimal(100) == Decimal("100")

    def test_to_decimal_from_float(self):
        # Float 0.1 + 0.2 ≠ 0.3 in binary; our function handles this
        d = to_decimal(0.1)
        assert isinstance(d, Decimal)

    def test_to_decimal_from_string(self):
        assert to_decimal("1234.56") == Decimal("1234.56")

    def test_to_decimal_none_returns_default(self):
        assert to_decimal(None) == Decimal("0")

    def test_to_decimal_invalid_returns_default(self):
        assert to_decimal("not_a_number") == Decimal("0")

    def test_money_rounds_half_up(self):
        assert money(Decimal("1.005")) == Decimal("1.01")
        assert money(Decimal("1.004")) == Decimal("1.00")

    def test_pct_converts_correctly(self):
        assert pct(18) == Decimal("0.18")
        assert pct(5) == Decimal("0.05")
        assert pct(0) == Decimal("0")

    def test_percent_of(self):
        # 18% of 1000 = 180
        assert percent_of(1000, 18) == Decimal("180.000000")

    def test_safe_divide_by_zero(self):
        assert safe_divide(100, 0) == Decimal("0")
        assert safe_divide(0, 0) == Decimal("0")

    def test_safe_divide_normal(self):
        result = safe_divide(Decimal("200"), Decimal("1000"))
        assert result == Decimal("0.2")

    def test_round_price_nearest(self):
        assert round_price(Decimal("499.40"), "nearest") == Decimal("499")

    def test_round_price_end_99(self):
        assert round_price(Decimal("500.00"), "end_99") == Decimal("599")
        assert round_price(Decimal("499.00"), "end_99") == Decimal("499")

    def test_round_price_end_9(self):
        assert round_price(Decimal("500.00"), "end_9") == Decimal("509")
        assert round_price(Decimal("509.00"), "end_9") == Decimal("509")


# ─────────────────────────────────────────────────────────────────
# 2. GST CALCULATIONS (PRD Test Cases D)
# ─────────────────────────────────────────────────────────────────

class TestGST:

    # PRD Test D: GST-inclusive calculation
    def test_gst_inclusive_18pct(self):
        """Customer pays ₹1180 inclusive of 18% GST → taxable ₹1000, GST ₹180"""
        result = extract_tax_inclusive(Decimal("1180"), Decimal("18"))
        assert result["taxable_value"] == Decimal("1000.00"), (
            f"Expected ₹1000, got ₹{result['taxable_value']}"
        )
        assert result["tax_amount"] == Decimal("180.00"), (
            f"Expected ₹180, got ₹{result['tax_amount']}"
        )
        assert result["total_inclusive"] == Decimal("1180.00")

    # PRD Test D: GST-exclusive calculation
    def test_gst_exclusive_18pct(self):
        """Taxable value ₹1000 + 18% GST → total ₹1180"""
        result = apply_tax_exclusive(Decimal("1000"), Decimal("18"))
        assert result["taxable_value"] == Decimal("1000.00")
        assert result["tax_amount"] == Decimal("180.00")
        assert result["total_inclusive"] == Decimal("1180.00")

    def test_gst_zero_rate(self):
        result = apply_tax_exclusive(Decimal("1000"), Decimal("0"))
        assert result["tax_amount"] == Decimal("0.00")
        assert result["total_inclusive"] == Decimal("1000.00")

    def test_gst_5pct(self):
        result = apply_tax_exclusive(Decimal("1000"), Decimal("5"))
        assert result["tax_amount"] == Decimal("50.00")
        assert result["total_inclusive"] == Decimal("1050.00")

    def test_gst_12pct(self):
        result = apply_tax_exclusive(Decimal("1000"), Decimal("12"))
        assert result["tax_amount"] == Decimal("120.00")

    def test_gst_28pct(self):
        result = apply_tax_exclusive(Decimal("1000"), Decimal("28"))
        assert result["tax_amount"] == Decimal("280.00")

    def test_gst_intra_state_split(self):
        """Intra-state: CGST = SGST = 50% each"""
        config = GSTConfig(rate_pct=Decimal("18"), inclusive=False, is_intra_state=True)
        result = calculate_gst(Decimal("1000"), config, 1)
        assert result.cgst == Decimal("90.00")
        assert result.sgst == Decimal("90.00")
        assert result.igst == Decimal("0.00")
        assert result.output_gst == Decimal("180.00")

    def test_gst_inter_state_igst(self):
        """Inter-state: IGST only"""
        config = GSTConfig(rate_pct=Decimal("18"), inclusive=False, is_intra_state=False)
        result = calculate_gst(Decimal("1000"), config, 1)
        assert result.igst == Decimal("180.00")
        assert result.cgst == Decimal("0.00")
        assert result.sgst == Decimal("0.00")

    def test_gst_itc_recoverable(self):
        """ITC reduces net GST expense"""
        config = GSTConfig(
            rate_pct=Decimal("18"),
            inclusive=False,
            input_tax_credit_eligible=True,
            purchase_gst_paid=Decimal("72"),  # Paid 72 GST on purchase
        )
        result = calculate_gst(Decimal("1000"), config, 1)
        assert result.output_gst == Decimal("180.00")
        assert result.itc_recoverable == Decimal("72.00")
        assert result.net_gst_expense == Decimal("108.00")

    def test_gst_itc_not_eligible(self):
        """When ITC not eligible, full GST is expense"""
        config = GSTConfig(
            rate_pct=Decimal("18"),
            inclusive=False,
            input_tax_credit_eligible=False,
            purchase_gst_paid=Decimal("72"),
        )
        result = calculate_gst(Decimal("1000"), config, 1)
        assert result.itc_recoverable == Decimal("0.00")
        assert result.net_gst_expense == Decimal("180.00")

    def test_gst_invalid_rate_raises(self):
        with pytest.raises(ValueError):
            extract_tax_inclusive(Decimal("1180"), Decimal("100"))

    def test_gst_quantity_scales(self):
        """GST calculated on per-unit * quantity"""
        config = GSTConfig(rate_pct=Decimal("18"), inclusive=False)
        result = calculate_gst(Decimal("500"), config, 2)
        assert result.taxable_value == Decimal("1000.00")
        assert result.output_gst == Decimal("180.00")


# ─────────────────────────────────────────────────────────────────
# 3. MARGIN vs MARKUP (PRD Test Case C)
# ─────────────────────────────────────────────────────────────────

class TestMarginMarkup:

    # PRD Test C
    def test_margin_calculation(self):
        """Net revenue ₹1000, total cost ₹800, profit ₹200 → margin 20%"""
        net_revenue = Decimal("1000")
        total_cost = Decimal("800")
        profit = net_revenue - total_cost
        result_margin = margin(profit, net_revenue)
        assert result_margin == Decimal("20.00"), (
            f"Expected 20%, got {result_margin}%"
        )

    def test_markup_calculation(self):
        """Same scenario → markup on ₹800 cost = 25%"""
        profit = Decimal("200")
        cost = Decimal("800")
        result_markup = markup(profit, cost)
        assert result_markup == Decimal("25.00"), (
            f"Expected 25%, got {result_markup}%"
        )

    def test_margin_zero_revenue_returns_zero(self):
        assert margin(Decimal("100"), Decimal("0")) == Decimal("0")

    def test_markup_zero_cost_returns_zero(self):
        assert markup(Decimal("100"), Decimal("0")) == Decimal("0")

    def test_margin_and_markup_are_different(self):
        """Margin 20% ≠ Markup 25% — they must not be equal"""
        profit = Decimal("200")
        revenue = Decimal("1000")
        cost = Decimal("800")
        m = margin(profit, revenue)
        mu = markup(profit, cost)
        assert m != mu, "Margin and markup should be different numbers"
        assert m < mu, "Markup is always higher than margin for the same profit"


# ─────────────────────────────────────────────────────────────────
# 4. PRODUCT PROFIT CALCULATOR (PRD Test Cases A, B)
# ─────────────────────────────────────────────────────────────────

class TestProductProfit:

    def _make_simple_result(
        self,
        selling_price: Decimal,
        purchase_cost: Decimal,
        packaging: Decimal = Decimal("0"),
        shipping: Decimal = Decimal("0"),
        mp_commission: Decimal = Decimal("0"),
        advertising: Decimal = Decimal("0"),
        gst_rate: Decimal = Decimal("0"),
        quantity: int = 1,
    ):
        """Helper to compute profit with simple inputs."""
        pc = ProductCost(
            purchase_cost=purchase_cost,
            packaging_cost=packaging,
        )
        gst_config = GSTConfig(rate_pct=gst_rate, inclusive=False)
        sd = SellingDetails(
            listed_price=selling_price,
            actual_selling_price=selling_price,
            quantity=quantity,
            gst_config=gst_config,
        )
        se = SellingExpenses(
            marketplace_commission=mp_commission,
            forward_shipping=shipping,
            advertising_cost=advertising,
        )
        return calculate_profit(pc, sd, se)

    # PRD Test A: Basic product profit
    def test_basic_product_profit(self):
        """
        Revenue ₹1000, product cost ₹400, packaging ₹50, shipping ₹100,
        marketplace fee ₹100, advertising ₹100 → contribution profit ₹250
        """
        result = self._make_simple_result(
            selling_price=Decimal("1000"),
            purchase_cost=Decimal("400"),
            packaging=Decimal("50"),
            shipping=Decimal("100"),
            mp_commission=Decimal("100"),
            advertising=Decimal("100"),
            gst_rate=Decimal("0"),
        )
        assert result.contribution_profit_after_adv == Decimal("250.00"), (
            f"Expected ₹250, got ₹{result.contribution_profit_after_adv}"
        )
        assert result.contribution_margin_pct == Decimal("25.00"), (
            f"Expected 25%, got {result.contribution_margin_pct}%"
        )

    # PRD Test B: Percentage marketplace fee
    def test_percentage_marketplace_fee(self):
        """
        Selling price ₹1000, product cost ₹400, marketplace fee 10%,
        shipping ₹100 → fee ₹100, profit (before other costs) = ₹400
        """
        result = self._make_simple_result(
            selling_price=Decimal("1000"),
            purchase_cost=Decimal("400"),
            shipping=Decimal("100"),
            mp_commission=Decimal("100"),  # 10% of 1000 = 100
            gst_rate=Decimal("0"),
        )
        assert result.total_marketplace_fees == Decimal("100.00"), (
            f"Expected ₹100 marketplace fee, got ₹{result.total_marketplace_fees}"
        )
        expected_profit = Decimal("1000") - Decimal("400") - Decimal("100") - Decimal("100")
        assert result.contribution_profit_after_adv == expected_profit, (
            f"Expected ₹{expected_profit}, got ₹{result.contribution_profit_after_adv}"
        )

    def test_profit_with_gst_excluded_from_revenue(self):
        """GST must NOT be counted as revenue."""
        pc = ProductCost(purchase_cost=Decimal("400"))
        gst_config = GSTConfig(rate_pct=Decimal("18"), inclusive=False)
        sd = SellingDetails(
            listed_price=Decimal("1180"),
            actual_selling_price=Decimal("1000"),  # Taxable value
            quantity=1,
            gst_config=gst_config,
        )
        se = SellingExpenses()
        result = calculate_profit(pc, sd, se)

        # Net revenue should be ₹1000 (taxable), not ₹1180 (inclusive)
        assert result.output_gst == Decimal("180.00"), (
            f"Expected output GST ₹180, got ₹{result.output_gst}"
        )
        assert result.net_revenue == Decimal("1000.00"), (
            f"Net revenue should be ₹1000 (excl. GST), got ₹{result.net_revenue}"
        )

    def test_profitable_product(self):
        result = self._make_simple_result(
            selling_price=Decimal("1000"),
            purchase_cost=Decimal("200"),
            gst_rate=Decimal("0"),
        )
        assert result.is_profitable is True

    def test_loss_making_product(self):
        result = self._make_simple_result(
            selling_price=Decimal("300"),
            purchase_cost=Decimal("400"),
            gst_rate=Decimal("0"),
        )
        assert result.is_profitable is False
        assert result.estimated_operating_profit < Decimal("0")

    def test_zero_selling_price(self):
        result = self._make_simple_result(
            selling_price=Decimal("0"),
            purchase_cost=Decimal("400"),
            gst_rate=Decimal("0"),
        )
        assert result.is_profitable is False
        assert len(result.warnings) > 0

    def test_quantity_scales_profit(self):
        """Profit for 5 units should be 5x profit for 1 unit."""
        r1 = self._make_simple_result(
            selling_price=Decimal("1000"),
            purchase_cost=Decimal("400"),
            gst_rate=Decimal("0"),
            quantity=1,
        )
        r5 = self._make_simple_result(
            selling_price=Decimal("1000"),
            purchase_cost=Decimal("400"),
            gst_rate=Decimal("0"),
            quantity=5,
        )
        assert r5.total_profit == r1.total_profit * 5

    def test_discounts_reduce_revenue(self):
        pc = ProductCost(purchase_cost=Decimal("400"))
        gst = GSTConfig(rate_pct=Decimal("0"))
        sd = SellingDetails(
            listed_price=Decimal("1000"),
            actual_selling_price=Decimal("1000"),
            quantity=1,
            customer_discount=Decimal("100"),
            gst_config=gst,
        )
        se = SellingExpenses()
        result = calculate_profit(pc, sd, se)
        assert result.customer_discount_total == Decimal("100.00")


# ─────────────────────────────────────────────────────────────────
# 5. TARGET PRICE SOLVER (PRD Test Case E)
# ─────────────────────────────────────────────────────────────────

class TestPriceSolver:

    # PRD Test E: Target profit calculation
    def test_target_profit_break_even(self):
        """
        Product cost ₹400, fixed ops ₹100, target profit ₹200.
        No percentage fees. Target price = ₹700.
        """
        inputs = PriceSolverInputs(
            product_cost=Decimal("400"),
            fixed_overhead=Decimal("100"),
            gst_rate_pct=Decimal("0"),
            # No variable % fees
        )
        target = PriceSolverTarget(
            objective="target_profit",
            target_profit_per_unit=Decimal("200"),
            price_rounding_method="nearest",
        )
        result = solve_target_price(inputs, target)
        assert result.is_feasible is True
        assert result.taxable_value == Decimal("700.00"), (
            f"Expected ₹700, got ₹{result.taxable_value}"
        )

    def test_break_even_price(self):
        """Break-even: total costs = ₹500, no % fees → break-even at ₹500"""
        inputs = PriceSolverInputs(
            product_cost=Decimal("300"),
            packaging_cost=Decimal("50"),
            fixed_fulfillment_cost=Decimal("100"),
            fixed_marketplace_fee=Decimal("50"),
            gst_rate_pct=Decimal("0"),
        )
        target = PriceSolverTarget(objective="break_even", price_rounding_method="nearest")
        result = solve_target_price(inputs, target)
        assert result.is_feasible is True
        assert result.break_even_price == Decimal("500.00")

    def test_target_margin_25pct(self):
        """
        Fixed cost ₹750, target 25% margin.
        P * (1 - 0.25) = 750 → P = 750 / 0.75 = ₹1000
        """
        inputs = PriceSolverInputs(
            product_cost=Decimal("750"),
            gst_rate_pct=Decimal("0"),
        )
        target = PriceSolverTarget(
            objective="target_margin",
            target_margin_pct=Decimal("25"),
            price_rounding_method="nearest",
        )
        result = solve_target_price(inputs, target)
        assert result.is_feasible is True
        assert result.taxable_value == Decimal("1000.00")

    def test_variable_fee_adjustment(self):
        """
        Fixed cost ₹500, 10% commission. 
        P * 0.90 = 500 → P = 555.56 → break-even ₹555.56
        """
        inputs = PriceSolverInputs(
            product_cost=Decimal("500"),
            marketplace_commission_pct=Decimal("10"),
            gst_rate_pct=Decimal("0"),
        )
        target = PriceSolverTarget(objective="break_even", price_rounding_method="nearest")
        result = solve_target_price(inputs, target)
        assert result.is_feasible is True
        # Break-even = 500 / (1 - 0.10) = 555.55...
        assert Decimal("555") < result.break_even_price < Decimal("557")

    def test_infeasible_100pct_variable_cost(self):
        """100% variable cost → no valid price"""
        inputs = PriceSolverInputs(
            product_cost=Decimal("100"),
            marketplace_commission_pct=Decimal("100"),
            gst_rate_pct=Decimal("0"),
        )
        target = PriceSolverTarget(objective="break_even")
        result = solve_target_price(inputs, target)
        assert result.is_feasible is False
        assert result.infeasibility_reason != ""

    def test_infeasible_margin_too_high(self):
        """Target margin > available after variable costs → infeasible"""
        inputs = PriceSolverInputs(
            product_cost=Decimal("100"),
            marketplace_commission_pct=Decimal("50"),
            payment_gateway_pct=Decimal("40"),
            gst_rate_pct=Decimal("0"),
        )
        target = PriceSolverTarget(
            objective="target_margin",
            target_margin_pct=Decimal("30"),  # 90% var + 30% margin > 100%
        )
        result = solve_target_price(inputs, target)
        assert result.is_feasible is False

    def test_gst_added_on_top(self):
        """When GST rate set, recommended price includes GST on top."""
        inputs = PriceSolverInputs(
            product_cost=Decimal("500"),
            gst_rate_pct=Decimal("18"),
            gst_inclusive_in_price=False,
        )
        target = PriceSolverTarget(objective="break_even", price_rounding_method="nearest")
        result = solve_target_price(inputs, target)
        assert result.is_feasible is True
        # incl_gst must be > taxable_value
        assert result.recommended_price_incl_gst > result.taxable_value


# ─────────────────────────────────────────────────────────────────
# 6. RETURNS & RTO
# ─────────────────────────────────────────────────────────────────

class TestReturnRTO:

    def test_basic_return_calculation(self):
        inputs = ReturnRTOInputs(
            total_orders=100,
            return_rate_pct=Decimal("10"),
            rto_rate_pct=Decimal("5"),
            product_cost_per_unit=Decimal("500"),
            reverse_shipping_cost=Decimal("80"),
            rto_shipping_cost=Decimal("80"),
            forward_shipping_cost=Decimal("80"),
            resalable_pct=Decimal("70"),
            recovery_value_per_returned_unit=Decimal("300"),
        )
        result = calculate_return_rto_loss(inputs)
        assert result.expected_returns == Decimal("10.00")
        assert result.expected_rto == Decimal("5.00")
        assert result.expected_successful_deliveries == Decimal("85.00")

    def test_invalid_rate_validation(self):
        inputs = ReturnRTOInputs(
            total_orders=100,
            return_rate_pct=Decimal("150"),  # Invalid
        )
        errors = inputs.validate()
        assert len(errors) > 0

    def test_zero_rates_no_loss(self):
        inputs = ReturnRTOInputs(
            total_orders=100,
            return_rate_pct=Decimal("0"),
            rto_rate_pct=Decimal("0"),
        )
        result = calculate_return_rto_loss(inputs)
        assert result.total_expected_loss == Decimal("0.00")
        assert result.expected_successful_deliveries == Decimal("100.00")

    def test_return_loss_adjusts_profit(self):
        inputs = ReturnRTOInputs(
            total_orders=100,
            return_rate_pct=Decimal("10"),
            rto_rate_pct=Decimal("0"),
            product_cost_per_unit=Decimal("500"),
            reverse_shipping_cost=Decimal("100"),
            resalable_pct=Decimal("0"),
            recovery_value_per_returned_unit=Decimal("0"),
        )
        result = calculate_return_rto_loss(inputs, base_profit_per_successful_order=Decimal("200"))
        assert result.adjusted_profit_per_successful_order < Decimal("200")


# ─────────────────────────────────────────────────────────────────
# 7. ADVERTISING METRICS
# ─────────────────────────────────────────────────────────────────

class TestAdvertising:

    def test_roas_calculation(self):
        """ROAS = attributed revenue / ad spend"""
        inputs = AdvertisingInputs(
            ad_spend=Decimal("1000"),
            attributed_revenue=Decimal("5000"),
            attributed_orders=10,
            contribution_margin_before_adv=Decimal("40"),
        )
        result = calculate_advertising(inputs)
        assert result.roas == Decimal("5.00")

    def test_break_even_roas_from_margin(self):
        """Break-even ROAS = 1 / contribution_margin (as decimal)"""
        # 40% margin → break-even ROAS = 1 / 0.40 = 2.5
        inputs = AdvertisingInputs(
            ad_spend=Decimal("100"),
            attributed_revenue=Decimal("1000"),
            attributed_orders=1,
            contribution_margin_before_adv=Decimal("40"),
        )
        result = calculate_advertising(inputs)
        assert result.break_even_roas == Decimal("2.50"), (
            f"Expected break-even ROAS 2.50, got {result.break_even_roas}"
        )

    def test_zero_margin_warns(self):
        """0% margin → ROAS undefined, warning produced"""
        inputs = AdvertisingInputs(
            ad_spend=Decimal("100"),
            attributed_revenue=Decimal("1000"),
            attributed_orders=1,
            contribution_margin_before_adv=Decimal("0"),
        )
        result = calculate_advertising(inputs)
        assert len(result.warnings) > 0
        assert result.break_even_roas == Decimal("0")

    def test_profitable_ads(self):
        """ROAS above break-even = profitable campaign"""
        inputs = AdvertisingInputs(
            ad_spend=Decimal("1000"),
            attributed_revenue=Decimal("5000"),
            attributed_orders=10,
            contribution_margin_before_adv=Decimal("40"),
        )
        result = calculate_advertising(inputs)
        # ROAS 5 > break-even ROAS 2.5 → contribution positive
        assert result.contribution_profit_after_adv > Decimal("0")

    def test_ctr_calculation(self):
        """CTR = clicks / impressions * 100"""
        inputs = AdvertisingInputs(
            ad_spend=Decimal("100"),
            impressions=10000,
            clicks=200,
            attributed_orders=5,
            attributed_revenue=Decimal("2000"),
            contribution_margin_before_adv=Decimal("35"),
        )
        result = calculate_advertising(inputs)
        assert result.ctr_pct == Decimal("2.00"), (
            f"Expected CTR 2%, got {result.ctr_pct}%"
        )

    def test_cpm_calculation(self):
        """CPM = ad spend / impressions * 1000"""
        inputs = AdvertisingInputs(
            ad_spend=Decimal("100"),
            impressions=10000,
            attributed_revenue=Decimal("1000"),
            attributed_orders=5,
            contribution_margin_before_adv=Decimal("30"),
        )
        result = calculate_advertising(inputs)
        assert result.cpm == Decimal("10.00"), (
            f"Expected CPM ₹10, got ₹{result.cpm}"
        )


# ─────────────────────────────────────────────────────────────────
# 8. SHIPPING CALCULATOR
# ─────────────────────────────────────────────────────────────────

class TestShipping:

    def test_dimensional_weight_calculation(self):
        """DIM weight = L * W * H / divisor"""
        inputs = ShippingInputs(
            length_cm=Decimal("30"),
            width_cm=Decimal("20"),
            height_cm=Decimal("15"),
            actual_weight_kg=Decimal("0.5"),
            dimensional_weight_divisor=Decimal("5000"),
        )
        result = calculate_shipping(inputs)
        # Volume = 30 * 20 * 15 = 9000 cc
        # DIM weight = 9000 / 5000 = 1.8 kg
        assert result.dimensional_weight_kg == Decimal("1.80")
        # Chargeable = max(0.5, 1.8) = 1.8
        assert result.chargeable_weight_kg == Decimal("1.80")

    def test_actual_weight_used_when_higher(self):
        inputs = ShippingInputs(
            length_cm=Decimal("10"),
            width_cm=Decimal("10"),
            height_cm=Decimal("10"),
            actual_weight_kg=Decimal("5.0"),
            dimensional_weight_divisor=Decimal("5000"),
        )
        result = calculate_shipping(inputs)
        # Volume = 1000 cc, DIM = 0.2 kg < 5.0 actual
        assert result.chargeable_weight_kg == Decimal("5.0")

    def test_forward_shipping_basic(self):
        inputs = ShippingInputs(
            length_cm=Decimal("20"),
            width_cm=Decimal("15"),
            height_cm=Decimal("10"),
            actual_weight_kg=Decimal("0.4"),
            dimensional_weight_divisor=Decimal("5000"),
            forward_rate_per_500g=Decimal("50"),
            additional_500g_rate=Decimal("30"),
            weight_slab_grams=500,
        )
        result = calculate_shipping(inputs)
        # Chargeable = max(0.4, 20*15*10/5000) = max(0.4, 0.6) = 0.6 kg → 2 slabs
        # Forward = 50 + (2-1) * 30 = 80
        assert result.forward_delivery_cost == Decimal("80.00")


# ─────────────────────────────────────────────────────────────────
# 9. EDGE CASES & DIVISION BY ZERO
# ─────────────────────────────────────────────────────────────────

class TestEdgeCases:

    def test_division_by_zero_margin(self):
        assert margin(Decimal("200"), Decimal("0")) == Decimal("0")

    def test_division_by_zero_markup(self):
        assert markup(Decimal("200"), Decimal("0")) == Decimal("0")

    def test_very_large_inputs(self):
        """Should not raise on very large inputs."""
        inputs = PriceSolverInputs(
            product_cost=Decimal("9999999"),
            gst_rate_pct=Decimal("18"),
        )
        target = PriceSolverTarget(objective="break_even")
        result = solve_target_price(inputs, target)
        assert result.is_feasible is True

    def test_zero_cost_product(self):
        """Digital product with zero cost should be profitable."""
        pc = ProductCost(purchase_cost=Decimal("0"))
        gst = GSTConfig(rate_pct=Decimal("0"))
        sd = SellingDetails(
            listed_price=Decimal("999"),
            actual_selling_price=Decimal("999"),
            gst_config=gst,
        )
        se = SellingExpenses()
        result = calculate_profit(pc, sd, se)
        assert result.is_profitable is True

    def test_price_exactly_at_breakeven(self):
        """Profit at break-even should be ~0."""
        inputs = PriceSolverInputs(
            product_cost=Decimal("500"),
            gst_rate_pct=Decimal("0"),
        )
        target = PriceSolverTarget(objective="break_even", price_rounding_method="nearest")
        result = solve_target_price(inputs, target)
        assert result.is_feasible is True
        # At break-even price, contribution profit should be near 0
        # (may be slightly above due to rounding)
        assert abs(result.contribution_profit_per_unit) <= Decimal("1.00")

    def test_negative_value_handling(self):
        """Negative values in non-allowed fields should not crash."""
        pc = ProductCost(purchase_cost=Decimal("400"))
        gst = GSTConfig(rate_pct=Decimal("0"))
        sd = SellingDetails(
            listed_price=Decimal("500"),
            actual_selling_price=Decimal("500"),
            quantity=1,
            customer_discount=Decimal("600"),  # Discount > price
            gst_config=gst,
        )
        se = SellingExpenses()
        # Should not crash; will show negative net revenue
        result = calculate_profit(pc, sd, se)
        assert result is not None


# ─────────────────────────────────────────────────────────────────
# 10. ROUNDING BEHAVIOR
# ─────────────────────────────────────────────────────────────────

class TestRounding:

    @pytest.mark.parametrize("input_price,method,expected", [
        (Decimal("500"), "end_99", Decimal("599")),
        (Decimal("599"), "end_99", Decimal("599")),
        (Decimal("600"), "end_99", Decimal("699")),
        (Decimal("1000"), "end_99", Decimal("1099")),
        (Decimal("500"), "end_9", Decimal("509")),
        (Decimal("509"), "end_9", Decimal("509")),
        (Decimal("500"), "nearest", Decimal("500")),
        (Decimal("500.49"), "nearest", Decimal("500")),
        (Decimal("500.50"), "nearest", Decimal("501")),
    ])
    def test_price_rounding(self, input_price, method, expected):
        result = round_price(input_price, method)
        assert result == expected, (
            f"round_price({input_price}, {method}) = {result}, expected {expected}"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
