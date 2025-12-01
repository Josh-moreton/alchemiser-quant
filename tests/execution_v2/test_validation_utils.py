"""Business Unit: execution | Status: current

Test for suspicious quote validation utilities.

This test focuses on the core validation logic without external dependencies.
"""

from decimal import Decimal

import pytest

from the_alchemiser.shared.utils.validation_utils import (
    detect_suspicious_quote_prices,
    validate_order_notional,
    validate_quote_for_trading,
)


class TestSuspiciousQuoteDetection:
    """Test suspicious quote detection functionality."""

    def test_detect_suspicious_negative_prices(self):
        """Test detection of negative bid/ask prices."""
        # Test negative bid price - this was the COST issue
        is_suspicious, reasons = detect_suspicious_quote_prices(-0.01, 100.0)
        assert is_suspicious
        assert "negative bid price: -0.01" in reasons

        # Test negative ask price
        is_suspicious, reasons = detect_suspicious_quote_prices(100.0, -0.02)
        assert is_suspicious
        assert "negative ask price: -0.02" in reasons

        # Test both negative - exact COST scenario
        is_suspicious, reasons = detect_suspicious_quote_prices(-0.01, -0.02)
        assert is_suspicious
        assert len(reasons) == 2
        assert "negative bid price: -0.01" in reasons
        assert "negative ask price: -0.02" in reasons

    def test_detect_suspicious_inverted_spread(self):
        """Test detection of inverted spread (ask < bid)."""
        is_suspicious, reasons = detect_suspicious_quote_prices(100.0, 99.5)
        assert is_suspicious
        assert "inverted spread: ask 99.5 < bid 100.0" in reasons

    def test_detect_suspicious_penny_stock_prices(self):
        """Test detection of unreasonably low prices."""
        # Test low bid price
        is_suspicious, reasons = detect_suspicious_quote_prices(0.005, 100.0)
        assert is_suspicious
        assert "bid price too low: 0.005 < 0.01" in reasons

        # Test low ask price
        is_suspicious, reasons = detect_suspicious_quote_prices(100.0, 0.005)
        assert is_suspicious
        assert "ask price too low: 0.005 < 0.01" in reasons

    def test_detect_excessive_spread(self):
        """Test detection of excessive spreads."""
        # 15% spread should be flagged as suspicious (default max is 10%)
        is_suspicious, reasons = detect_suspicious_quote_prices(100.0, 115.0)
        assert is_suspicious
        assert "excessive spread: 13.04% > 10.0%" in reasons

    def test_normal_quotes_not_suspicious(self):
        """Test that normal quotes are not flagged as suspicious."""
        # Normal quote for COST around $923 - what it should have been
        is_suspicious, reasons = detect_suspicious_quote_prices(923.50, 923.77)
        assert not is_suspicious
        assert len(reasons) == 0

        # Normal quote with reasonable spread
        is_suspicious, reasons = detect_suspicious_quote_prices(100.0, 100.25)
        assert not is_suspicious
        assert len(reasons) == 0

    def test_edge_cases(self):
        """Test edge cases for suspicious detection."""
        # Both prices zero
        is_suspicious, reasons = detect_suspicious_quote_prices(0.0, 0.0)
        assert not is_suspicious  # Zero prices handled by existing validation

        # One price zero, one positive (should be handled by existing validation)
        is_suspicious, reasons = detect_suspicious_quote_prices(0.0, 100.0)
        assert not is_suspicious

        # Exactly at minimum price threshold
        is_suspicious, reasons = detect_suspicious_quote_prices(0.01, 0.01)
        assert not is_suspicious

    def test_cost_specific_scenario(self):
        """Test the specific COST scenario from the issue."""
        # This is the exact scenario that caused the problem:
        # "Invalid recommended bid -0.01 / ask -0.02 for COST"
        is_suspicious, reasons = detect_suspicious_quote_prices(-0.01, -0.02)

        assert is_suspicious
        assert len(reasons) == 2
        assert "negative bid price: -0.01" in reasons
        assert "negative ask price: -0.02" in reasons

        # The real COST price should not be suspicious
        real_cost_price = 923.77
        is_suspicious, reasons = detect_suspicious_quote_prices(
            real_cost_price - 0.27, real_cost_price
        )
        assert not is_suspicious
        assert len(reasons) == 0


class TestStrictQuoteValidation:
    """Test strict quote validation for trading."""

    def test_validate_quote_for_trading_valid_quote(self):
        """Test that valid quotes pass validation."""
        # Normal quote - should not raise
        validate_quote_for_trading("AAPL", 150.0, 150.05, 100, 100)

        # Quote with larger spread but within tolerance
        validate_quote_for_trading("SPY", 400.0, 404.0, 1000, 1000, max_spread_percent=5.0)

    def test_validate_quote_for_trading_zero_prices(self):
        """Test that zero prices raise ValueError."""
        # Zero ask price (TECL scenario: bid=107, ask=0)
        with pytest.raises(ValueError, match="Both prices must be positive"):
            validate_quote_for_trading("TECL", 107.0, 0.0, 100, 0)

        # Zero bid price
        with pytest.raises(ValueError, match="Both prices must be positive"):
            validate_quote_for_trading("TEST", 0.0, 100.0, 0, 100)

        # Both zero
        with pytest.raises(ValueError, match="Both prices must be positive"):
            validate_quote_for_trading("TEST", 0.0, 0.0, 0, 0)

    def test_validate_quote_for_trading_negative_prices(self):
        """Test that negative prices raise ValueError."""
        # Negative bid
        with pytest.raises(ValueError, match="Both prices must be positive"):
            validate_quote_for_trading("TEST", -1.0, 100.0)

        # Negative ask
        with pytest.raises(ValueError, match="Both prices must be positive"):
            validate_quote_for_trading("TEST", 100.0, -1.0)

    def test_validate_quote_for_trading_inverted_spread(self):
        """Test that inverted spreads raise ValueError."""
        with pytest.raises(ValueError, match="Inverted spread"):
            validate_quote_for_trading("TEST", 100.0, 99.0, 100, 100)

    def test_validate_quote_for_trading_excessive_spread(self):
        """Test that excessive spreads raise ValueError."""
        # 15% spread with 10% max
        with pytest.raises(ValueError, match="spread.*exceeds maximum"):
            validate_quote_for_trading("TEST", 100.0, 115.0, 100, 100, max_spread_percent=10.0)

    def test_validate_quote_for_trading_zero_sizes(self):
        """Test that zero sizes raise ValueError when required."""
        # Zero sizes with require_positive_sizes=True
        with pytest.raises(ValueError, match="Both sizes must be positive"):
            validate_quote_for_trading("TEST", 100.0, 100.05, 0, 100, require_positive_sizes=True)

        with pytest.raises(ValueError, match="Both sizes must be positive"):
            validate_quote_for_trading("TEST", 100.0, 100.05, 100, 0, require_positive_sizes=True)

        # Zero sizes allowed when require_positive_sizes=False
        validate_quote_for_trading("TEST", 100.0, 100.05, 0, 0, require_positive_sizes=False)

    def test_validate_quote_for_trading_below_minimum(self):
        """Test that prices below minimum raise ValueError."""
        # Sub-penny prices
        with pytest.raises(ValueError, match="below minimum"):
            validate_quote_for_trading("TEST", 0.005, 0.006)


class TestOrderNotionalValidation:
    """Test order notional validation for Alpaca constraints."""

    def test_validate_order_notional_valid(self):
        """Test that valid notional values pass."""
        # Normal order - $1500 notional
        validate_order_notional("AAPL", Decimal("150.00"), Decimal("10"))

        # Exactly at minimum
        validate_order_notional("TEST", Decimal("1.00"), Decimal("1"))

        # Just above minimum
        validate_order_notional("TEST", Decimal("1.01"), Decimal("1"))

    def test_validate_order_notional_below_minimum(self):
        """Test that notional below minimum raises ValueError."""
        # $0.01 notional (TECL scenario with bad $0.01 price)
        with pytest.raises(ValueError, match="below Alpaca minimum"):
            validate_order_notional("TECL", Decimal("0.01"), Decimal("1"))

        # $0.50 notional (still below $1 minimum)
        with pytest.raises(ValueError, match="below Alpaca minimum"):
            validate_order_notional("TEST", Decimal("0.50"), Decimal("1"))

        # $0.99 notional (just below $1)
        with pytest.raises(ValueError, match="below Alpaca minimum"):
            validate_order_notional("TEST", Decimal("0.99"), Decimal("1"))

    def test_validate_order_notional_fractional_shares(self):
        """Test notional validation with fractional shares."""
        # Valid fractional order
        validate_order_notional("AAPL", Decimal("150.00"), Decimal("0.01"))  # $1.50

        # Invalid fractional order
        with pytest.raises(ValueError, match="below Alpaca minimum"):
            validate_order_notional("AAPL", Decimal("50.00"), Decimal("0.01"))  # $0.50

    def test_validate_order_notional_custom_minimum(self):
        """Test notional validation with custom minimum."""
        # Pass with default minimum but fail with higher custom minimum
        validate_order_notional("TEST", Decimal("5.00"), Decimal("1"))

        with pytest.raises(ValueError, match="below Alpaca minimum"):
            validate_order_notional(
                "TEST", Decimal("5.00"), Decimal("1"), min_notional=Decimal("10.00")
            )
