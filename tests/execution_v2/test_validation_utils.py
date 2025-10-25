"""Business Unit: execution | Status: current

Test for suspicious quote validation utilities.

This test focuses on the core validation logic without external dependencies.
"""

from the_alchemiser.shared.utils.validation_utils import detect_suspicious_quote_prices


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
