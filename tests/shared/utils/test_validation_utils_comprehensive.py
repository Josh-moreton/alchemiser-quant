"""Business Unit: shared | Status: current

Comprehensive unit tests for validation utilities.

This test suite provides full coverage of all validation functions in the shared
validation_utils module, including edge cases and error conditions.
"""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from the_alchemiser.shared.utils.validation_utils import (
    detect_suspicious_quote_prices,
    validate_decimal_range,
    validate_enum_value,
    validate_non_negative_integer,
    validate_order_limit_price,
    validate_price_positive,
    validate_quote_freshness,
    validate_quote_prices,
    validate_spread_reasonable,
)


class TestValidateDecimalRange:
    """Test decimal range validation functionality."""

    def test_valid_range_accepts_value_in_bounds(self):
        """Test that values within range are accepted."""
        # Test boundaries
        validate_decimal_range(Decimal("10.0"), Decimal("10.0"), Decimal("20.0"))
        validate_decimal_range(Decimal("20.0"), Decimal("10.0"), Decimal("20.0"))

        # Test middle value
        validate_decimal_range(Decimal("15.0"), Decimal("10.0"), Decimal("20.0"))

    def test_invalid_range_raises_value_error(self):
        """Test that values outside range raise ValueError."""
        with pytest.raises(ValueError, match="Value must be between 10.0 and 20.0"):
            validate_decimal_range(Decimal("9.99"), Decimal("10.0"), Decimal("20.0"))

        with pytest.raises(ValueError, match="Value must be between 10.0 and 20.0"):
            validate_decimal_range(Decimal("20.01"), Decimal("10.0"), Decimal("20.0"))

    def test_custom_field_name_in_error_message(self):
        """Test that custom field name appears in error message."""
        with pytest.raises(ValueError, match="Price must be between 0.0 and 100.0"):
            validate_decimal_range(Decimal("-1.0"), Decimal("0.0"), Decimal("100.0"), "Price")

    def test_negative_ranges(self):
        """Test validation with negative ranges."""
        validate_decimal_range(Decimal("-5.0"), Decimal("-10.0"), Decimal("0.0"))

        with pytest.raises(ValueError):
            validate_decimal_range(Decimal("-11.0"), Decimal("-10.0"), Decimal("0.0"))


class TestValidateEnumValue:
    """Test enum value validation functionality."""

    def test_valid_enum_value_accepted(self):
        """Test that valid enum values are accepted."""
        valid_values = {"buy", "sell", "hold"}
        validate_enum_value("buy", valid_values)
        validate_enum_value("sell", valid_values)
        validate_enum_value("hold", valid_values)

    def test_invalid_enum_value_raises_error(self):
        """Test that invalid enum values raise ValueError."""
        valid_values = {"buy", "sell", "hold"}

        with pytest.raises(ValueError, match="Value must be one of"):
            validate_enum_value("invalid", valid_values)

    def test_custom_field_name_in_enum_error(self):
        """Test custom field name in enum validation error."""
        valid_values = {"up", "down"}

        with pytest.raises(ValueError, match="Direction must be one of"):
            validate_enum_value("sideways", valid_values, "Direction")

    def test_case_sensitive_enum_validation(self):
        """Test that enum validation is case sensitive."""
        valid_values = {"Buy", "Sell"}

        with pytest.raises(ValueError):
            validate_enum_value("buy", valid_values)  # lowercase should fail


class TestValidateNonNegativeInteger:
    """Test non-negative integer validation functionality."""

    def test_valid_non_negative_integers(self):
        """Test that valid non-negative integers are accepted."""
        validate_non_negative_integer(Decimal("0"))
        validate_non_negative_integer(Decimal("1"))
        validate_non_negative_integer(Decimal("100"))

    def test_negative_integer_raises_error(self):
        """Test that negative integers raise ValueError."""
        with pytest.raises(ValueError, match="Value must be non-negative"):
            validate_non_negative_integer(Decimal("-1"))

    def test_non_integer_raises_error(self):
        """Test that non-integer values raise ValueError."""
        with pytest.raises(ValueError, match="Value must be whole number"):
            validate_non_negative_integer(Decimal("1.5"))

        with pytest.raises(ValueError, match="Value must be whole number"):
            validate_non_negative_integer(Decimal("0.1"))

    def test_custom_field_name_in_integer_error(self):
        """Test custom field name in integer validation error."""
        with pytest.raises(ValueError, match="Quantity must be non-negative"):
            validate_non_negative_integer(Decimal("-5"), "Quantity")


class TestValidateOrderLimitPrice:
    """Test order limit price validation functionality."""

    def test_limit_order_requires_limit_price(self):
        """Test that limit orders require a limit price."""
        # Valid limit order
        validate_order_limit_price("limit", 100.0)
        validate_order_limit_price("limit", Decimal("100.0"))
        validate_order_limit_price("limit", 100)

    def test_limit_order_without_price_raises_error(self):
        """Test that limit orders without price raise ValueError."""
        with pytest.raises(ValueError, match="Limit price is required for limit orders"):
            validate_order_limit_price("limit", None)

    def test_market_order_with_price_raises_error(self):
        """Test that market orders with price raise ValueError."""
        with pytest.raises(
            ValueError, match="Limit price should not be provided for market orders"
        ):
            validate_order_limit_price("market", 100.0)

    def test_market_order_without_price_valid(self):
        """Test that market orders without price are valid."""
        validate_order_limit_price("market", None)


class TestValidatePricePositive:
    """Test positive price validation functionality."""

    def test_valid_positive_prices(self):
        """Test that valid positive prices are accepted."""
        validate_price_positive(Decimal("0.01"))  # Minimum valid price
        validate_price_positive(Decimal("1.00"))
        validate_price_positive(Decimal("999.99"))

    def test_zero_price_raises_error(self):
        """Test that zero price raises ValueError."""
        with pytest.raises(ValueError, match="Price must be positive"):
            validate_price_positive(Decimal("0.00"))

    def test_negative_price_raises_error(self):
        """Test that negative price raises ValueError."""
        with pytest.raises(ValueError, match="Price must be positive"):
            validate_price_positive(Decimal("-1.00"))

    def test_price_below_minimum_raises_error(self):
        """Test that price below minimum raises ValueError."""
        with pytest.raises(ValueError, match="Price must be at least 0.01"):
            validate_price_positive(Decimal("0.001"))

    def test_custom_field_name_in_price_error(self):
        """Test custom field name in price validation error."""
        with pytest.raises(ValueError, match="Bid must be positive"):
            validate_price_positive(Decimal("-5.0"), "Bid")


class TestValidateQuoteFreshness:
    """Test quote freshness validation functionality."""

    def test_fresh_quote_returns_true(self):
        """Test that fresh quotes return True."""
        now = datetime.now(UTC)
        fresh_timestamp = now - timedelta(seconds=1)  # 1 second old

        assert validate_quote_freshness(fresh_timestamp, 10.0) is True

    def test_stale_quote_returns_false(self):
        """Test that stale quotes return False."""
        now = datetime.now(UTC)
        stale_timestamp = now - timedelta(seconds=20)  # 20 seconds old

        assert validate_quote_freshness(stale_timestamp, 10.0) is False

    def test_quote_at_boundary_returns_true(self):
        """Test that quotes at the boundary are considered fresh."""
        now = datetime.now(UTC)
        boundary_timestamp = now - timedelta(seconds=9)  # 9 seconds old (just under boundary)

        # Should be fresh (<=)
        assert validate_quote_freshness(boundary_timestamp, 10.0) is True


class TestValidateQuotePrices:
    """Test quote price validation functionality."""

    def test_valid_quote_prices(self):
        """Test that valid quote prices return True."""
        assert validate_quote_prices(100.0, 100.5) is True  # Normal spread
        assert validate_quote_prices(100.0, 100.0) is True  # Same price
        assert validate_quote_prices(0.0, 100.0) is True  # Zero bid, positive ask
        assert validate_quote_prices(100.0, 0.0) is True  # Positive bid, zero ask

    def test_both_prices_zero_or_negative_returns_false(self):
        """Test that both prices zero or negative returns False."""
        assert validate_quote_prices(0.0, 0.0) is False
        assert validate_quote_prices(-1.0, -1.0) is False
        assert validate_quote_prices(0.0, -1.0) is False

    def test_inverted_spread_returns_false(self):
        """Test that inverted spread (bid > ask) returns False."""
        assert validate_quote_prices(101.0, 100.0) is False

    def test_negative_prices_with_positive_counterpart(self):
        """Test behavior with one negative and one positive price."""
        assert validate_quote_prices(-1.0, 100.0) is True  # Negative bid, positive ask
        assert validate_quote_prices(100.0, -1.0) is True  # Positive bid, negative ask


class TestValidateSpreadReasonable:
    """Test spread reasonableness validation functionality."""

    def test_reasonable_spread_returns_true(self):
        """Test that reasonable spreads return True."""
        assert validate_spread_reasonable(100.0, 100.25, 0.5) is True  # 0.25% spread
        assert validate_spread_reasonable(100.0, 100.5, 0.5) is True  # 0.5% spread

    def test_excessive_spread_returns_false(self):
        """Test that excessive spreads return False."""
        assert validate_spread_reasonable(100.0, 101.0, 0.5) is False  # 1% spread > 0.5%

    def test_zero_or_negative_prices_return_false(self):
        """Test that zero or negative prices return False."""
        assert validate_spread_reasonable(0.0, 100.0, 0.5) is False
        assert validate_spread_reasonable(100.0, 0.0, 0.5) is False
        assert validate_spread_reasonable(-1.0, 100.0, 0.5) is False

    def test_custom_spread_threshold(self):
        """Test custom spread threshold values."""
        # 1% spread should be reasonable with 2% threshold
        assert validate_spread_reasonable(100.0, 101.0, 2.0) is True

        # But not with 0.5% threshold
        assert validate_spread_reasonable(100.0, 101.0, 0.5) is False


class TestDetectSuspiciousQuotePrices:
    """Test suspicious quote price detection functionality."""

    def test_normal_quotes_not_suspicious(self):
        """Test that normal quotes are not flagged as suspicious."""
        is_suspicious, reasons = detect_suspicious_quote_prices(100.0, 100.25)
        assert not is_suspicious
        assert len(reasons) == 0

    def test_negative_prices_detected_as_suspicious(self):
        """Test that negative prices are detected as suspicious."""
        is_suspicious, reasons = detect_suspicious_quote_prices(-0.01, -0.02)
        assert is_suspicious
        assert "negative bid price: -0.01" in reasons
        assert "negative ask price: -0.02" in reasons

    def test_single_negative_price_detected(self):
        """Test that single negative price is detected."""
        is_suspicious, reasons = detect_suspicious_quote_prices(-1.0, 100.0)
        assert is_suspicious
        assert "negative bid price: -1.0" in reasons
        assert len(reasons) == 1

    def test_penny_stock_prices_detected(self):
        """Test that penny stock prices are detected as suspicious."""
        is_suspicious, reasons = detect_suspicious_quote_prices(0.005, 0.006)
        assert is_suspicious
        assert "bid price too low: 0.005 < 0.01" in reasons
        assert "ask price too low: 0.006 < 0.01" in reasons

    def test_inverted_spread_detected(self):
        """Test that inverted spreads are detected as suspicious."""
        is_suspicious, reasons = detect_suspicious_quote_prices(101.0, 100.0)
        assert is_suspicious
        assert "inverted spread: ask 100.0 < bid 101.0" in reasons

    def test_excessive_spread_detected(self):
        """Test that excessive spreads are detected as suspicious."""
        is_suspicious, reasons = detect_suspicious_quote_prices(
            100.0, 120.0
        )  # 16.67% spread (20/120 * 100)
        assert is_suspicious
        assert "excessive spread:" in reasons[0]
        assert "16.67%" in reasons[0]

    def test_custom_thresholds(self):
        """Test custom threshold values."""
        # Test custom min_price
        is_suspicious, reasons = detect_suspicious_quote_prices(0.05, 0.06, min_price=0.1)
        assert is_suspicious
        assert "bid price too low: 0.05 < 0.1" in reasons

        # Test custom max_spread_percent
        is_suspicious, reasons = detect_suspicious_quote_prices(
            100.0, 102.0, max_spread_percent=1.0
        )
        assert is_suspicious
        assert "excessive spread:" in reasons[0]

    def test_multiple_issues_detected(self):
        """Test that multiple issues are detected simultaneously."""
        is_suspicious, reasons = detect_suspicious_quote_prices(-1.0, -2.0)
        assert is_suspicious
        assert len(reasons) == 2
        assert "negative bid price: -1.0" in reasons
        assert "negative ask price: -2.0" in reasons

    def test_zero_prices_not_flagged_as_negative(self):
        """Test that zero prices are not flagged as negative."""
        is_suspicious, reasons = detect_suspicious_quote_prices(0.0, 100.0)
        assert not is_suspicious
        assert len(reasons) == 0

    def test_edge_case_exact_threshold_values(self):
        """Test behavior at exact threshold values."""
        # Exactly at min_price should not be suspicious
        is_suspicious, reasons = detect_suspicious_quote_prices(0.01, 0.01)
        assert not is_suspicious

        # Exactly at max_spread_percent should not be suspicious
        is_suspicious, reasons = detect_suspicious_quote_prices(
            100.0, 110.0, max_spread_percent=10.0
        )
        assert not is_suspicious
