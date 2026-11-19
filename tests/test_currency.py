"""
Unit tests for the centralized INR currency formatting utility.
Covers Indian number grouping, edge cases, and compact display format.
"""

from decimal import Decimal

from omnix.core.currency import (
    CURRENCY_CODE,
    CURRENCY_SYMBOL,
    format_inr,
    format_inr_compact,
)


class TestCurrencyConstants:
    def test_symbol_is_rupee(self):
        assert CURRENCY_SYMBOL == "₹"

    def test_code_is_inr(self):
        assert CURRENCY_CODE == "INR"


class TestIndianGrouping:
    """Verify correct Indian comma placement (3-2-2-2...) at every common magnitude."""

    def test_below_1000(self):
        assert format_inr(500) == "₹500.00"

    def test_exactly_1000(self):
        assert format_inr(1000) == "₹1,000.00"

    def test_ten_thousand(self):
        assert format_inr(25_000) == "₹25,000.00"

    def test_one_lakh(self):
        # 1,00,000
        assert format_inr(1_00_000) == "₹1,00,000.00"

    def test_one_lakh_twenty_five_thousand(self):
        # 1,25,000
        assert format_inr(1_25_000) == "₹1,25,000.00"

    def test_twelve_lakh_fifty_thousand(self):
        # 12,50,000
        assert format_inr(12_50_000) == "₹12,50,000.00"

    def test_one_crore(self):
        # 1,00,00,000
        assert format_inr(1_00_00_000) == "₹1,00,00,000.00"

    def test_decimal_precision(self):
        assert format_inr(2_84_520.50) == "₹2,84,520.50"

    def test_zero(self):
        assert format_inr(0) == "₹0.00"

    def test_decimal_input(self):
        assert format_inr(Decimal("1850.00")) == "₹1,850.00"

    def test_string_input(self):
        assert format_inr("25200") == "₹25,200.00"

    def test_no_usd_symbol(self):
        result = format_inr(100)
        assert "$" not in result
        assert "USD" not in result

    def test_inr_symbol_present(self):
        result = format_inr(100)
        assert "₹" in result


class TestCompactFormat:
    def test_compact_lakh(self):
        result = format_inr_compact(1_25_000)
        assert "L" in result
        assert "₹" in result

    def test_compact_crore(self):
        result = format_inr_compact(1_00_00_000)
        assert "Cr" in result
        assert "₹" in result

    def test_compact_below_lakh(self):
        # Should fall through to full formatting
        result = format_inr_compact(25_000)
        assert "₹" in result
        assert "L" not in result


class TestPurchaseOrderAmounts:
    """Verify that the placeholder PO data has consistent INR amounts."""

    def test_po_89_rice_sugar(self):
        # 100 × ₹1,850 + 50 × ₹2,200 = ₹1,85,000 + ₹1,10,000 = ₹2,95,000
        rice_total = 100 * 1_850.00
        sugar_total = 50 * 2_200.00
        expected = rice_total + sugar_total
        assert expected == 2_95_000.00
        assert format_inr(expected) == "₹2,95,000.00"

    def test_po_88_flour(self):
        # 60 × ₹420 = ₹25,200
        flour_total = 60 * 420.00
        assert flour_total == 25_200.00
        assert format_inr(flour_total) == "₹25,200.00"

    def test_po_87_oil(self):
        # 120 × ₹760 = ₹91,200
        oil_total = 120 * 760.00
        assert oil_total == 91_200.00
        assert format_inr(oil_total) == "₹91,200.00"


class TestConfigDefaults:
    """Verify that app configuration defaults are set to INR."""

    def test_default_currency_is_inr(self):
        from omnix.core.config import get_settings
        settings = get_settings()
        assert settings.default_currency == "INR"

    def test_approval_limits_are_inr_values(self):
        from omnix.core.config import get_settings
        settings = get_settings()
        # INR thresholds must be meaningfully larger than USD equivalents
        assert settings.max_auto_approval_limit >= 50_000  # min ₹50,000
        assert settings.high_value_threshold >= 2_00_000   # min ₹2,00,000
