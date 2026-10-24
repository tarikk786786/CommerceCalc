"""
Core profit calculation engine for CommerceCalc.

Implements the documented accounting model:
  Net Sales Revenue
  - Product Acquisition Cost
  - Fulfillment Costs
  - Marketplace Fees
  - Payment Processing Fees
  = Contribution Profit Before Advertising
  - Advertising Expense
  = Contribution Profit After Advertising
  - Overhead
  = Estimated Operating Profit
"""
from decimal import Decimal
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime
from .money import (
    to_decimal, money, percent_of, safe_divide, margin, markup, add_percent
)
from .tax import GSTConfig, GSTBreakdown, calculate_gst
from .fees import MarketplaceProfile


@dataclass
class ProductCost:
    """All acquisition and preparation costs for a product."""
    purchase_cost: Decimal = Decimal("0")           # Supplier cost per unit
    packaging_cost: Decimal = Decimal("0")          # Packaging materials
    preparation_cost: Decimal = Decimal("0")        # Handling/prep labor
    inbound_shipping: Decimal = Decimal("0")        # Inbound logistics
    inspection_cost: Decimal = Decimal("0")         # QC cost
    overhead_allocated: Decimal = Decimal("0")      # Fixed overhead per unit
    import_cost: Decimal = Decimal("0")             # Import duties/customs
    other_cost: Decimal = Decimal("0")              # Other acquisition expenses
    purchase_gst_paid: Decimal = Decimal("0")       # GST paid on purchase
    itc_recoverable: Decimal = Decimal("0")         # Expected ITC recovery

    def __post_init__(self):
        for f in self.__dataclass_fields__:
            setattr(self, f, to_decimal(getattr(self, f)))

    @property
    def total_acquisition_cost(self) -> Decimal:
        """Total product cost (excluding recoverable ITC)."""
        return money(
            self.purchase_cost
            + self.packaging_cost
            + self.preparation_cost
            + self.inbound_shipping
            + self.inspection_cost
            + self.import_cost
            + self.other_cost
            + self.purchase_gst_paid
            - self.itc_recoverable
        )

    @property
    def non_overhead_cost(self) -> Decimal:
        """Variable cost excluding overhead."""
        return money(self.total_acquisition_cost - self.overhead_allocated)


@dataclass
class SellingDetails:
    """Selling price and sales channel details."""
    listed_price: Decimal = Decimal("0")
    actual_selling_price: Decimal = Decimal("0")
    quantity: int = 1
    customer_discount: Decimal = Decimal("0")       # Amount discounted to customer
    coupon_discount: Decimal = Decimal("0")         # Coupon-based discount
    seller_funded_promo: Decimal = Decimal("0")     # Seller-funded promotion cost
    marketplace_funded_discount: Decimal = Decimal("0")  # NOT seller's cost
    customer_paid_shipping: Decimal = Decimal("0")  # Shipping charged to customer
    gst_config: Optional[GSTConfig] = None
    payment_method: str = "prepaid"                 # 'prepaid', 'cod', 'upi'
    marketplace_profile: Optional[MarketplaceProfile] = None
    channel_name: str = ""

    def __post_init__(self):
        for f in ["listed_price", "actual_selling_price", "customer_discount",
                  "coupon_discount", "seller_funded_promo", "marketplace_funded_discount",
                  "customer_paid_shipping"]:
            setattr(self, f, to_decimal(getattr(self, f)))
        if self.gst_config is None:
            self.gst_config = GSTConfig(rate_pct=Decimal("0"), inclusive=False)

    @property
    def gross_selling_value(self) -> Decimal:
        """Listed price * quantity before any deductions."""
        return money(self.listed_price * to_decimal(self.quantity))

    @property
    def net_customer_payment(self) -> Decimal:
        """What the customer actually pays (actual price - customer discount + shipping)."""
        return money(
            self.actual_selling_price * to_decimal(self.quantity)
            - self.customer_discount
            - self.coupon_discount
            + self.customer_paid_shipping
        )


@dataclass
class SellingExpenses:
    """All variable selling and fulfillment expenses per order."""
    marketplace_commission: Decimal = Decimal("0")  # % or fixed from profile
    closing_fee: Decimal = Decimal("0")
    transaction_fee: Decimal = Decimal("0")
    payment_gateway_fee: Decimal = Decimal("0")
    payment_collection_fee: Decimal = Decimal("0")
    forward_shipping: Decimal = Decimal("0")
    reverse_shipping: Decimal = Decimal("0")
    packaging_fulfillment: Decimal = Decimal("0")
    cod_charge: Decimal = Decimal("0")
    affiliate_commission: Decimal = Decimal("0")
    advertising_cost: Decimal = Decimal("0")
    return_expense: Decimal = Decimal("0")          # Expected return loss
    rto_expense: Decimal = Decimal("0")             # Expected RTO loss
    other_variable_cost: Decimal = Decimal("0")

    def __post_init__(self):
        for f in self.__dataclass_fields__:
            setattr(self, f, to_decimal(getattr(self, f)))

    @property
    def total_marketplace_fees(self) -> Decimal:
        return money(self.marketplace_commission + self.closing_fee + self.transaction_fee)

    @property
    def total_payment_fees(self) -> Decimal:
        return money(
            self.payment_gateway_fee
            + self.payment_collection_fee
            + self.cod_charge
        )

    @property
    def total_fulfillment_cost(self) -> Decimal:
        return money(
            self.forward_shipping
            + self.reverse_shipping
            + self.packaging_fulfillment
        )

    @property
    def total_return_rto_cost(self) -> Decimal:
        return money(self.return_expense + self.rto_expense)

    @property
    def total_non_advertising_expense(self) -> Decimal:
        return money(
            self.total_marketplace_fees
            + self.total_payment_fees
            + self.total_fulfillment_cost
            + self.affiliate_commission
            + self.total_return_rto_cost
            + self.other_variable_cost
        )

    @property
    def total_expense(self) -> Decimal:
        return money(self.total_non_advertising_expense + self.advertising_cost)


@dataclass
class ProfitResult:
    """Complete profit calculation result."""
    # Revenue
    gross_list_value: Decimal = Decimal("0")
    customer_discount_total: Decimal = Decimal("0")
    net_customer_payment: Decimal = Decimal("0")
    output_gst: Decimal = Decimal("0")
    net_revenue: Decimal = Decimal("0")              # Excl. GST

    # Costs
    total_acquisition_cost: Decimal = Decimal("0")
    total_fulfillment_cost: Decimal = Decimal("0")
    total_marketplace_fees: Decimal = Decimal("0")
    total_payment_fees: Decimal = Decimal("0")
    advertising_expense: Decimal = Decimal("0")
    expected_return_rto: Decimal = Decimal("0")
    other_variable_expense: Decimal = Decimal("0")
    overhead_allocated: Decimal = Decimal("0")
    affiliate_commission: Decimal = Decimal("0")
    total_variable_expense: Decimal = Decimal("0")

    # Profit layers
    contribution_profit_before_adv: Decimal = Decimal("0")
    contribution_profit_after_adv: Decimal = Decimal("0")
    estimated_operating_profit: Decimal = Decimal("0")

    # Per-unit metrics
    profit_per_unit: Decimal = Decimal("0")
    net_profit_per_order: Decimal = Decimal("0")
    total_profit: Decimal = Decimal("0")

    # Margins
    gross_margin_pct: Decimal = Decimal("0")
    contribution_margin_pct: Decimal = Decimal("0")
    operating_margin_pct: Decimal = Decimal("0")
    markup_on_cost_pct: Decimal = Decimal("0")
    effective_expense_pct: Decimal = Decimal("0")

    # GST details
    gst_breakdown: Optional[GSTBreakdown] = None

    # Metadata
    is_profitable: bool = False
    warnings: List[str] = field(default_factory=list)
    calculation_timestamp: str = ""
    formula_version: str = "1.0"
    assumptions_used: Dict[str, Any] = field(default_factory=dict)
    expense_breakdown: Dict[str, Decimal] = field(default_factory=dict)


def calculate_profit(
    product_cost: ProductCost,
    selling: SellingDetails,
    expenses: SellingExpenses,
) -> ProfitResult:
    """
    Calculate complete profitability for a product.

    Uses the documented accounting model:
    Net Revenue = Net Customer Payment - Output GST (if seller-registered)
    Contribution Profit Before Adv = Net Revenue - Acquisition Cost - All Non-Adv Expenses
    Contribution Profit After Adv = above - Advertising
    Operating Profit = above - Overhead

    NOTE: Output GST is collected by seller and remitted to government —
    it is NOT revenue. ITC on purchases offsets GST liability, not direct profit.
    """
    qty = to_decimal(selling.quantity)
    result = ProfitResult()
    result.calculation_timestamp = datetime.now().isoformat()
    warnings = []

    # --- Revenue Calculation ---
    result.gross_list_value = selling.gross_selling_value
    result.customer_discount_total = money(
        selling.customer_discount + selling.coupon_discount
    )
    result.net_customer_payment = selling.net_customer_payment

    # Calculate GST
    gst_config = selling.gst_config or GSTConfig(rate_pct=Decimal("0"))
    per_unit_price = to_decimal(selling.actual_selling_price)

    gst_break = calculate_gst(per_unit_price, gst_config, int(qty))
    result.gst_breakdown = gst_break
    result.output_gst = gst_break.output_gst

    # Net revenue excludes GST (GST is collected for govt, not business income)
    # Also add customer-paid shipping as revenue offset
    net_rev_before_shipping = money(
        gst_break.taxable_value
        - selling.seller_funded_promo
        + selling.customer_paid_shipping
    )
    result.net_revenue = net_rev_before_shipping

    if result.net_revenue <= Decimal("0"):
        warnings.append("Net revenue is zero or negative — check pricing and discounts.")

    # --- Cost Calculation ---
    # Scale per-unit costs by quantity
    # total_acquisition_cost is computed per unit; multiply by quantity
    total_acquisition = money(product_cost.total_acquisition_cost * qty)
    result.total_acquisition_cost = total_acquisition
    result.overhead_allocated = money(product_cost.overhead_allocated * qty)

    # Marketplace fees from profile or from manually entered expenses
    if selling.marketplace_profile and selling.marketplace_profile.fee_rules:
        sp = per_unit_price * qty
        taxable = gst_break.taxable_value
        fee_results = selling.marketplace_profile.calculate_fees(
            sp,
            taxable_value=taxable,
            is_cod=(selling.payment_method == "cod"),
        )
        marketplace_fees_calc = fee_results.get("total_fees", Decimal("0"))
        # Override manually entered commission if profile provided
        expenses.marketplace_commission = marketplace_fees_calc
        if not selling.marketplace_profile.is_complete:
            for w in selling.marketplace_profile.completeness_warnings:
                warnings.append(f"Fee profile: {w}")
    else:
        if selling.marketplace_profile:
            warnings.append("No fee rules in selected marketplace profile.")

    result.total_marketplace_fees = expenses.total_marketplace_fees
    result.total_payment_fees = expenses.total_payment_fees
    result.total_fulfillment_cost = expenses.total_fulfillment_cost
    result.advertising_expense = expenses.advertising_cost
    result.expected_return_rto = expenses.total_return_rto_cost
    result.affiliate_commission = expenses.affiliate_commission
    result.other_variable_expense = expenses.other_variable_cost

    result.total_variable_expense = money(
        result.total_acquisition_cost
        + result.total_marketplace_fees
        + result.total_payment_fees
        + result.total_fulfillment_cost
        + result.affiliate_commission
        + result.expected_return_rto
        + result.other_variable_expense
    )

    # --- Profit Layers ---
    result.contribution_profit_before_adv = money(
        result.net_revenue - result.total_variable_expense
    )
    result.contribution_profit_after_adv = money(
        result.contribution_profit_before_adv - result.advertising_expense
    )
    result.estimated_operating_profit = money(
        result.contribution_profit_after_adv - result.overhead_allocated
    )

    # Per-unit metrics
    result.profit_per_unit = money(
        safe_divide(result.contribution_profit_after_adv, qty)
    )
    result.net_profit_per_order = result.estimated_operating_profit
    result.total_profit = result.estimated_operating_profit

    # --- Margin Calculations ---
    rev = result.net_revenue
    result.contribution_margin_pct = margin(
        result.contribution_profit_after_adv, rev
    )
    result.gross_margin_pct = margin(
        result.contribution_profit_before_adv, rev
    )
    result.operating_margin_pct = margin(result.estimated_operating_profit, rev)
    result.markup_on_cost_pct = markup(
        result.contribution_profit_after_adv,
        result.total_acquisition_cost
    )

    if rev > Decimal("0"):
        result.effective_expense_pct = money(
            safe_divide(result.total_variable_expense + result.advertising_expense, rev)
            * Decimal("100")
        )

    # Profitable?
    result.is_profitable = result.estimated_operating_profit > Decimal("0")

    # Expense breakdown for UI display
    result.expense_breakdown = {
        "Product Acquisition Cost": result.total_acquisition_cost,
        "Marketplace Fees": result.total_marketplace_fees,
        "Payment Processing Fees": result.total_payment_fees,
        "Fulfillment / Shipping": result.total_fulfillment_cost,
        "Advertising": result.advertising_expense,
        "Affiliate Commission": result.affiliate_commission,
        "Returns & RTO": result.expected_return_rto,
        "Other Variable Costs": result.other_variable_expense,
        "Allocated Overhead": result.overhead_allocated,
    }

    result.warnings = warnings
    result.assumptions_used = {
        "quantity": int(qty),
        "gst_rate_pct": str(gst_config.rate_pct),
        "gst_inclusive": gst_config.inclusive,
        "marketplace_profile": selling.marketplace_profile.name
        if selling.marketplace_profile else "None",
        "payment_method": selling.payment_method,
        "itc_eligible": gst_config.input_tax_credit_eligible,
    }

    return result
