"""
Tax calculation module for CommerceCalc.

Handles Indian GST (CGST/SGST/IGST), configurable rates,
input tax credit, and taxability modes.
"""
from decimal import Decimal
from dataclasses import dataclass, field
from typing import Optional
from .money import (
    to_decimal, money, pct, percent_of,
    extract_tax_inclusive, apply_tax_exclusive
)


@dataclass
class GSTConfig:
    """Configurable GST settings for a product or session."""
    rate_pct: Decimal = Decimal("18")         # e.g. 0, 5, 12, 18, 28
    inclusive: bool = False                    # True = price includes GST
    is_intra_state: bool = True               # CGST+SGST vs IGST
    input_tax_credit_eligible: bool = True    # Can claim ITC?
    purchase_gst_rate_pct: Decimal = Decimal("18")  # GST rate on purchases
    purchase_gst_paid: Decimal = Decimal("0")       # GST paid on this product's cost
    hsn_code: Optional[str] = None
    notes: str = ""

    # LABEL: This is a user-configured estimate. Not a tax professional's determination.
    label: str = "User-configured GST estimate"

    def __post_init__(self):
        self.rate_pct = to_decimal(self.rate_pct)
        self.purchase_gst_rate_pct = to_decimal(self.purchase_gst_rate_pct)
        self.purchase_gst_paid = to_decimal(self.purchase_gst_paid)


@dataclass
class GSTBreakdown:
    """Full GST breakdown for a sale."""
    taxable_value: Decimal = Decimal("0")
    output_gst: Decimal = Decimal("0")
    cgst: Decimal = Decimal("0")
    sgst: Decimal = Decimal("0")
    igst: Decimal = Decimal("0")
    total_inclusive: Decimal = Decimal("0")
    rate_pct: Decimal = Decimal("0")
    is_intra_state: bool = True
    input_tax_paid: Decimal = Decimal("0")
    itc_eligible: bool = True
    itc_recoverable: Decimal = Decimal("0")
    net_gst_expense: Decimal = Decimal("0")   # output GST - ITC (if seller charges GST)
    warning: str = ""


def calculate_gst(
    amount: Decimal,
    config: GSTConfig,
    quantity: int = 1
) -> GSTBreakdown:
    """
    Calculate GST for a given amount and configuration.

    Args:
        amount: Selling price (per unit)
        config: GST configuration
        quantity: Number of units

    Returns:
        GSTBreakdown with all calculated fields
    """
    amount = to_decimal(amount)
    qty = to_decimal(quantity)
    total_amount = amount * qty

    if config.inclusive:
        result = extract_tax_inclusive(total_amount, config.rate_pct)
    else:
        result = apply_tax_exclusive(total_amount, config.rate_pct)

    taxable = result["taxable_value"]
    output_gst = result["tax_amount"]
    total_inc = result["total_inclusive"]

    # CGST/SGST split vs IGST
    if config.is_intra_state:
        half = money(output_gst / Decimal("2"))
        cgst = half
        sgst = output_gst - half  # handle odd paise
        igst = Decimal("0")
    else:
        cgst = Decimal("0")
        sgst = Decimal("0")
        igst = output_gst

    # Input tax credit
    itc = config.purchase_gst_paid * qty if config.input_tax_credit_eligible else Decimal("0")
    itc = money(itc)
    net_expense = money(output_gst - itc) if config.input_tax_credit_eligible else output_gst

    warning = ""
    if config.rate_pct == Decimal("0"):
        warning = "GST rate is 0%. Verify correct rate for this product category."
    if not config.input_tax_credit_eligible:
        warning = (warning + " ITC not claimed; purchase GST treated as full cost.").strip()

    return GSTBreakdown(
        taxable_value=taxable,
        output_gst=output_gst,
        cgst=cgst,
        sgst=sgst,
        igst=igst,
        total_inclusive=total_inc,
        rate_pct=config.rate_pct,
        is_intra_state=config.is_intra_state,
        input_tax_paid=config.purchase_gst_paid * qty,
        itc_eligible=config.input_tax_credit_eligible,
        itc_recoverable=itc,
        net_gst_expense=net_expense,
        warning=warning,
    )


# Commonly used GST rate presets (for UI display only - not official determinations)
GST_RATE_PRESETS = [
    {"label": "0% – Exempt / Nil Rated", "rate": Decimal("0")},
    {"label": "5% – Essential goods", "rate": Decimal("5")},
    {"label": "12% – Standard goods", "rate": Decimal("12")},
    {"label": "18% – Standard services/goods", "rate": Decimal("18")},
    {"label": "28% – Luxury / sin goods", "rate": Decimal("28")},
]
# DISCLAIMER: These presets are for convenience only. The correct GST rate
# for your specific product or service must be determined by a tax professional
# or verified against official CBIC notifications.
