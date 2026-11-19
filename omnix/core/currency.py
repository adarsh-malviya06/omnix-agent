"""
Centralized INR currency formatting utility for OMNIX Agent.

All monetary display formatting must go through this module.
Keeps currency presentation logic in one place and out of business logic.

Monetary values are stored as numeric (Decimal/float) in the database and API.
Formatting is applied only at the presentation layer.

Indian Number Formatting rules:
  - First grouping: 3 digits from the right (thousands)
  - Subsequent groupings: 2 digits each (lakhs, crores, etc.)
  - Examples:
      1000       → ₹1,000.00
      25000      → ₹25,000.00
      125000     → ₹1,25,000.00
      1250000    → ₹12,50,000.00
      10000000   → ₹1,00,00,000.00
"""

from decimal import ROUND_HALF_UP, Decimal
from typing import Union


CURRENCY_SYMBOL: str = "₹"
CURRENCY_CODE: str = "INR"


def _apply_indian_grouping(integer_part: str) -> str:
    """
    Apply Indian comma grouping to the integer portion of a number.

    Groups: ...XX,XX,XX,XXX (rightmost 3, then 2s to the left).
    """
    # Work right-to-left: first group of 3, then groups of 2
    n = len(integer_part)
    if n <= 3:
        return integer_part

    # Rightmost 3 digits
    result = integer_part[-3:]
    remaining = integer_part[:-3]

    # Remaining digits grouped by 2 from the right
    while len(remaining) > 2:
        result = remaining[-2:] + "," + result
        remaining = remaining[:-2]

    if remaining:
        result = remaining + "," + result

    return result


def format_inr(amount: Union[int, float, Decimal, str], decimal_places: int = 2) -> str:
    """
    Format a numeric amount as an INR currency string with Indian comma grouping.

    Args:
        amount: Numeric value to format (int, float, Decimal, or numeric string).
        decimal_places: Number of decimal places (default 2).

    Returns:
        Formatted string such as "₹1,25,000.00".

    Examples:
        >>> format_inr(1000)
        '₹1,000.00'
        >>> format_inr(125000)
        '₹1,25,000.00'
        >>> format_inr(1250000)
        '₹12,50,000.00'
        >>> format_inr(10000000)
        '₹1,00,00,000.00'
        >>> format_inr(284520.50)
        '₹2,84,520.50'
    """
    try:
        value = Decimal(str(amount))
    except Exception:
        return f"{CURRENCY_SYMBOL}0.00"

    # Round to requested decimal places
    quantize_str = "1." + "0" * decimal_places
    value = value.quantize(Decimal(quantize_str), rounding=ROUND_HALF_UP)

    # Split on decimal point
    str_value = str(value)
    if "." in str_value:
        integer_part, decimal_part = str_value.split(".")
    else:
        integer_part = str_value
        decimal_part = "0" * decimal_places

    # Pad decimal part if needed
    decimal_part = decimal_part.ljust(decimal_places, "0")

    # Handle negative values
    negative = integer_part.startswith("-")
    if negative:
        integer_part = integer_part[1:]

    grouped = _apply_indian_grouping(integer_part)

    sign = "-" if negative else ""
    return f"{sign}{CURRENCY_SYMBOL}{grouped}.{decimal_part}"


def format_inr_compact(amount: Union[int, float, Decimal, str]) -> str:
    """
    Format large INR amounts in compact Indian notation for dashboard KPI cards.

    Uses lakh (₹X.XX L) and crore (₹X.XX Cr) suffixes.

    Examples:
        >>> format_inr_compact(125000)
        '₹1.25 L'
        >>> format_inr_compact(2500000)
        '₹25.00 L'
        >>> format_inr_compact(10000000)
        '₹1.00 Cr'
    """
    try:
        value = float(amount)
    except Exception:
        return f"{CURRENCY_SYMBOL}0"

    if abs(value) >= 1_00_00_000:  # 1 Crore
        return f"{CURRENCY_SYMBOL}{value / 1_00_00_000:.2f} Cr"
    elif abs(value) >= 1_00_000:  # 1 Lakh
        return f"{CURRENCY_SYMBOL}{value / 1_00_000:.2f} L"
    elif abs(value) >= 1_000:
        return format_inr(value)
    else:
        return format_inr(value)
