"""
Decimal-safe monetary arithmetic for CommerceCalc.

All financial calculations use Python's decimal.Decimal to avoid
binary floating-point rounding errors. Never use float for money.
"""
from decimal import Decimal, ROUND_HALF_UP, ROUND_UP, ROUND_DOWN, InvalidOperation
from typing import Union

# Standard currency precisions
INR_PLACES = Decimal("0.01")    # 2 decimal places for INR display
CALC_PLACES = Decimal("0.000001")  # 6 dp for intermediate calculations

NumericLike = Union[int, float, str, Decimal]


def to_decimal(value: NumericLike, default: Decimal = Decimal("0")) -> Decimal:
    """Convert any numeric-like value to Decimal safely."""
    if value is None:
        return default
    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return default


def money(value: NumericLike) -> Decimal:
    """Round a value to 2 decimal places (INR display precision)."""
    d = to_decimal(value)
    return d.quantize(INR_PLACES, rounding=ROUND_HALF_UP)


def pct(value: NumericLike) -> Decimal:
    """Convert a percentage value (e.g. 18) to a fraction (0.18)."""
    return to_decimal(value) / Decimal("100")


def percent_of(base: NumericLike, rate_pct: NumericLike) -> Decimal:
    """Calculate rate_pct% of base."""
    return to_decimal(base) * pct(rate_pct)


def add_percent(base: NumericLike, rate_pct: NumericLike) -> Decimal:
    """Return base + rate_pct% of base."""
    b = to_decimal(base)
    return b + percent_of(b, rate_pct)


def extract_tax_inclusive(inclusive_amount: NumericLike, rate_pct: NumericLike) -> dict:
    """
    From a GST-inclusive amount, extract taxable value and GST.

    Args:
        inclusive_amount: Customer-facing price including tax
        rate_pct: GST rate as a percentage (e.g. 18 for 18%)

    Returns:
        dict with keys: taxable_value, tax_amount, total_inclusive
    """
    total = to_decimal(inclusive_amount)
    rate = pct(rate_pct)
    if rate < 0 or rate >= 1:
        raise ValueError(f"Tax rate must be between 0% and 99%, got {rate_pct}%")
    # taxable_value = total / (1 + rate)
    divisor = Decimal("1") + rate
    taxable = (total / divisor).quantize(CALC_PLACES, rounding=ROUND_HALF_UP)
    tax = total - money(taxable)
    return {
        "taxable_value": money(taxable),
        "tax_amount": money(tax),
        "total_inclusive": money(total),
    }


def apply_tax_exclusive(exclusive_amount: NumericLike, rate_pct: NumericLike) -> dict:
    """
    From a GST-exclusive amount, calculate tax and inclusive total.

    Args:
        exclusive_amount: Taxable selling price (before tax)
        rate_pct: GST rate as a percentage

    Returns:
        dict with keys: taxable_value, tax_amount, total_inclusive
    """
    taxable = to_decimal(exclusive_amount)
    rate = pct(rate_pct)
    if rate < 0 or rate >= 1:
        raise ValueError(f"Tax rate must be between 0% and 99%, got {rate_pct}%")
    tax = percent_of(taxable, rate_pct)
    return {
        "taxable_value": money(taxable),
        "tax_amount": money(tax),
        "total_inclusive": money(taxable + tax),
    }


def safe_divide(numerator: NumericLike, denominator: NumericLike,
                default: Decimal = Decimal("0")) -> Decimal:
    """Divide safely, returning default if denominator is zero."""
    n = to_decimal(numerator)
    d = to_decimal(denominator)
    if d == Decimal("0"):
        return default
    return n / d


def margin(profit: NumericLike, revenue: NumericLike) -> Decimal:
    """
    Calculate margin as a percentage.
    margin = profit / revenue * 100
    Returns 0 if revenue is zero.
    """
    return money(safe_divide(to_decimal(profit), to_decimal(revenue)) * Decimal("100"))


def markup(profit: NumericLike, cost: NumericLike) -> Decimal:
    """
    Calculate markup as a percentage.
    markup = profit / cost * 100
    Returns 0 if cost is zero.
    """
    return money(safe_divide(to_decimal(profit), to_decimal(cost)) * Decimal("100"))


def round_price(price: NumericLike, method: str = "nearest", ending: str = None) -> Decimal:
    """
    Round a price according to a specified convention.

    method:
        'nearest'  - Round to nearest rupee
        'up'       - Round up to next rupee
        'down'     - Round down
        'end_9'    - End in 9 (e.g. 499, 999)
        'end_49'   - End in 49 or 99
        'end_99'   - End in 99
        'custom'   - Use ending parameter (e.g. '99', '49', '0')

    ending:  digit string for custom, e.g. '99', '49', '9'
    """
    p = to_decimal(price)
    base = p.quantize(Decimal("1"), rounding=ROUND_UP)

    if method == "nearest":
        return p.quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    elif method == "up":
        return base
    elif method == "down":
        return p.quantize(Decimal("1"), rounding=ROUND_DOWN)
    elif method in ("end_9", "end_99", "end_49", "custom"):
        target_ending = {"end_9": "9", "end_99": "99", "end_49": "49"}.get(method, ending or "99")
        suffix = int(target_ending)
        modulus = 10 ** len(target_ending)
        base_int = int(base)
        remainder = base_int % modulus
        if remainder == suffix:
            return Decimal(str(base_int))
        delta = suffix - remainder
        if delta < 0:
            delta += modulus
        return Decimal(str(base_int + delta))
    else:
        return p.quantize(Decimal("1"), rounding=ROUND_HALF_UP)
