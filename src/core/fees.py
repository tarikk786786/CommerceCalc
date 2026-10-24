"""
Marketplace fee engine for CommerceCalc.

Fee profiles are user-configurable. Built-in profiles contain
structure but NOT pre-filled verified rates — users must enter
or import verified rates from official platform sources.
"""
from decimal import Decimal
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import date
from .money import to_decimal, money, pct, percent_of, safe_divide


@dataclass
class FeeRule:
    """A single fee rule within a marketplace profile."""
    name: str
    fee_type: str          # 'percentage', 'fixed', 'tiered', 'per_kg', 'conditional'
    amount: Decimal = Decimal("0")       # percentage (0-100) or fixed INR amount
    min_amount: Optional[Decimal] = None  # minimum fee INR
    max_amount: Optional[Decimal] = None  # maximum fee INR
    applies_to: str = "selling_price"    # 'selling_price', 'taxable_value', 'order_value'
    tier_breakpoints: List[Dict] = field(default_factory=list)
    # [{"up_to": 500, "rate": 5}, {"up_to": 1000, "rate": 8}, {"up_to": None, "rate": 10}]
    condition: str = ""    # optional: 'cod_only', 'prepaid_only', etc.
    is_taxable: bool = False   # True if this fee itself attracts GST
    fee_gst_rate_pct: Decimal = Decimal("18")  # GST on this fee (usually 18%)
    enabled: bool = True
    notes: str = ""

    def __post_init__(self):
        self.amount = to_decimal(self.amount)
        if self.min_amount is not None:
            self.min_amount = to_decimal(self.min_amount)
        if self.max_amount is not None:
            self.max_amount = to_decimal(self.max_amount)
        self.fee_gst_rate_pct = to_decimal(self.fee_gst_rate_pct)

    def calculate(self, base_amount: Decimal, **kwargs) -> Decimal:
        """Calculate this fee for the given base amount."""
        if not self.enabled:
            return Decimal("0")

        base = to_decimal(base_amount)

        if self.fee_type == "fixed":
            fee = self.amount
        elif self.fee_type == "percentage":
            fee = percent_of(base, self.amount)
        elif self.fee_type == "tiered":
            fee = self._calculate_tiered(base)
        elif self.fee_type == "per_kg":
            weight_kg = to_decimal(kwargs.get("weight_kg", 0))
            fee = self.amount * weight_kg
        else:
            fee = Decimal("0")

        # Apply min/max
        if self.min_amount is not None:
            fee = max(fee, self.min_amount)
        if self.max_amount is not None:
            fee = min(fee, self.max_amount)

        # Add GST on the fee if applicable
        if self.is_taxable and self.fee_gst_rate_pct > 0:
            fee_gst = percent_of(fee, self.fee_gst_rate_pct)
            fee = fee + fee_gst

        return money(fee)

    def _calculate_tiered(self, base: Decimal) -> Decimal:
        """Calculate tiered fee."""
        if not self.tier_breakpoints:
            return percent_of(base, self.amount)

        b = float(base)
        for tier in sorted(self.tier_breakpoints, key=lambda x: x.get("up_to") or float("inf")):
            up_to = tier.get("up_to")
            rate = to_decimal(tier.get("rate", 0))
            if up_to is None or b <= float(up_to):
                return percent_of(base, rate)
        # Fallback to last tier
        last_rate = to_decimal(self.tier_breakpoints[-1].get("rate", 0))
        return percent_of(base, last_rate)


@dataclass
class MarketplaceProfile:
    """
    A complete fee profile for one marketplace or sales channel.

    IMPORTANT: Built-in profiles do NOT contain pre-verified fee rates.
    Users must enter rates verified from official platform fee schedules.
    Fee amounts are left at zero/unconfigured by default.
    """
    id: str
    name: str
    platform: str          # 'amazon_india', 'flipkart', 'meesho', 'shopify', etc.
    category: str = ""     # Product category this profile applies to
    currency: str = "INR"
    fee_rules: List[FeeRule] = field(default_factory=list)
    is_verified: bool = False
    source_url: str = ""
    source_document: str = ""
    last_verified_date: Optional[date] = None
    effective_from: Optional[date] = None
    notes: str = ""
    is_archived: bool = False
    created_at: Optional[date] = None
    updated_at: Optional[date] = None

    # Profile completeness
    @property
    def completeness_warnings(self) -> List[str]:
        warnings = []
        if not self.fee_rules:
            warnings.append("No fee rules configured.")
        if not self.is_verified:
            warnings.append("Rates not verified against official source.")
        if not self.source_url and not self.source_document:
            warnings.append("No source reference provided.")
        if not self.last_verified_date:
            warnings.append("No verification date set.")
        enabled_rules = [r for r in self.fee_rules if r.enabled]
        if not enabled_rules:
            warnings.append("All fee rules are disabled.")
        return warnings

    @property
    def is_complete(self) -> bool:
        return len(self.completeness_warnings) == 0

    def calculate_fees(self, selling_price: Decimal, **kwargs) -> Dict[str, Decimal]:
        """
        Calculate all applicable fees.

        Returns:
            dict mapping rule_name -> fee_amount, plus 'total_fees'
        """
        sp = to_decimal(selling_price)
        results = {}
        total = Decimal("0")

        for rule in self.fee_rules:
            if not rule.enabled:
                continue
            # Skip conditional rules that don't match
            condition = rule.condition.lower()
            if condition == "cod_only" and not kwargs.get("is_cod", False):
                continue
            if condition == "prepaid_only" and kwargs.get("is_cod", False):
                continue

            # Determine base for this rule
            base_amount_type = rule.applies_to
            if base_amount_type == "taxable_value":
                base = to_decimal(kwargs.get("taxable_value", sp))
            elif base_amount_type == "order_value":
                base = to_decimal(kwargs.get("order_value", sp))
            else:
                base = sp

            fee = rule.calculate(base, **kwargs)
            results[rule.name] = fee
            total += fee

        results["total_fees"] = money(total)
        return results

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "platform": self.platform,
            "category": self.category,
            "is_verified": self.is_verified,
            "source_url": self.source_url,
            "notes": self.notes,
            "fee_rules_count": len(self.fee_rules),
            "completeness_warnings": self.completeness_warnings,
        }


def create_empty_amazon_india_profile(profile_id: str = "amazon_in_default") -> MarketplaceProfile:
    """
    Create an Amazon India fee profile structure with empty (unconfigured) rates.
    Users must fill in verified rates from https://sell.amazon.in/fees
    """
    return MarketplaceProfile(
        id=profile_id,
        name="Amazon India (Unconfigured)",
        platform="amazon_india",
        notes=(
            "UNCONFIGURED: Enter verified rates from Amazon India's official fee schedule. "
            "Source: https://sell.amazon.in/fees — Last checked by user on: [add date]"
        ),
        fee_rules=[
            FeeRule(
                name="Referral Fee",
                fee_type="percentage",
                amount=Decimal("0"),  # USER MUST ENTER VERIFIED RATE
                applies_to="selling_price",
                notes="Verify current category-specific referral fee % at sell.amazon.in/fees",
            ),
            FeeRule(
                name="Closing Fee",
                fee_type="fixed",
                amount=Decimal("0"),  # USER MUST ENTER VERIFIED AMOUNT
                notes="Verify current closing fee at sell.amazon.in/fees",
                enabled=False,
            ),
            FeeRule(
                name="Weight Handling Fee (Forward)",
                fee_type="per_kg",
                amount=Decimal("0"),
                notes="Enter weight-based forward shipping rate.",
                enabled=False,
            ),
            FeeRule(
                name="COD Collection Fee",
                fee_type="percentage",
                amount=Decimal("0"),
                condition="cod_only",
                notes="Enter COD collection fee % for COD orders.",
                enabled=False,
            ),
        ],
        is_verified=False,
        source_url="https://sell.amazon.in/fees",
    )


def create_empty_flipkart_profile(profile_id: str = "flipkart_default") -> MarketplaceProfile:
    """Create an empty Flipkart fee profile."""
    return MarketplaceProfile(
        id=profile_id,
        name="Flipkart (Unconfigured)",
        platform="flipkart",
        notes=(
            "UNCONFIGURED: Enter verified rates from Flipkart Seller Hub. "
            "Source: https://seller.flipkart.com — verify current category fees."
        ),
        fee_rules=[
            FeeRule(
                name="Commission Fee",
                fee_type="percentage",
                amount=Decimal("0"),
                applies_to="selling_price",
                notes="Enter category-specific commission % from Flipkart seller portal.",
            ),
            FeeRule(
                name="Collection Fee",
                fee_type="percentage",
                amount=Decimal("0"),
                notes="Enter collection/payment fee %.",
                enabled=False,
            ),
            FeeRule(
                name="Shipping Fee (Forward)",
                fee_type="per_kg",
                amount=Decimal("0"),
                notes="Enter per-kg forward shipping rate.",
                enabled=False,
            ),
        ],
        is_verified=False,
        source_url="https://seller.flipkart.com",
    )


def create_empty_meesho_profile(profile_id: str = "meesho_default") -> MarketplaceProfile:
    """Create an empty Meesho fee profile."""
    return MarketplaceProfile(
        id=profile_id,
        name="Meesho (Unconfigured)",
        platform="meesho",
        notes=(
            "UNCONFIGURED: Enter verified rates from Meesho Supplier Hub. "
            "Note: Meesho fee structures have changed over time. Verify current rates."
        ),
        fee_rules=[
            FeeRule(
                name="Commission",
                fee_type="percentage",
                amount=Decimal("0"),
                notes="Enter current Meesho commission % from supplier.meesho.com",
            ),
            FeeRule(
                name="Payment Gateway Fee",
                fee_type="percentage",
                amount=Decimal("0"),
                notes="Enter payment processing fee %.",
                enabled=False,
            ),
        ],
        is_verified=False,
        source_url="https://supplier.meesho.com",
    )


def create_custom_profile(profile_id: str, name: str) -> MarketplaceProfile:
    """Create a blank custom profile."""
    return MarketplaceProfile(
        id=profile_id,
        name=name,
        platform="custom",
        notes="User-defined custom marketplace profile.",
        fee_rules=[],
        is_verified=False,
    )


# Default profile registry
DEFAULT_PROFILES = {
    "amazon_india": create_empty_amazon_india_profile,
    "flipkart": create_empty_flipkart_profile,
    "meesho": create_empty_meesho_profile,
}
