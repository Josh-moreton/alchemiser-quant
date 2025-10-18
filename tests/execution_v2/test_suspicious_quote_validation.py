"""Business Unit: execution | Status: current

Test for suspicious quote detection and REST NBBO validation.

This test validates the guard mechanism that detects suspicious streaming prices
and falls back to REST NBBO for validation before placing orders.
"""

from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import Mock

import pytest

from the_alchemiser.execution_v2.core.smart_execution_strategy.models import (
    ExecutionConfig,
)
from the_alchemiser.execution_v2.core.smart_execution_strategy.quotes import (
    QuoteProvider,
)
from the_alchemiser.shared.types.market_data import QuoteModel
from the_alchemiser.shared.utils.validation_utils import detect_suspicious_quote_prices


class TestSuspiciousQuoteDetection:
    """Test suspicious quote detection functionality."""

    def test_detect_suspicious_negative_prices(self):
        """Test detection of negative bid/ask prices."""
        # Test negative bid price
        is_suspicious, reasons = detect_suspicious_quote_prices(-0.01, 100.0)
        assert is_suspicious
        assert "negative bid price: -0.01" in reasons

        # Test negative ask price
        is_suspicious, reasons = detect_suspicious_quote_prices(100.0, -0.02)
        assert is_suspicious
        assert "negative ask price: -0.02" in reasons

        # Test both negative
        is_suspicious, reasons = detect_suspicious_quote_prices(-0.01, -0.02)
        assert is_suspicious
        assert len(reasons) == 2

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
        # Normal quote for COST around $923
        is_suspicious, reasons = detect_suspicious_quote_prices(923.50, 923.77)
        assert not is_suspicious
        assert len(reasons) == 0

        # Normal quote with reasonable spread
        is_suspicious, reasons = detect_suspicious_quote_prices(100.0, 100.25)
        assert not is_suspicious
        assert len(reasons) == 0


class TestQuoteProviderSuspiciousValidation:
    """Test QuoteProvider's suspicious quote validation logic."""

    @pytest.fixture
    def mock_alpaca_manager(self):
        """Mock Alpaca manager for testing."""
        manager = Mock()
        # Mock REST quote that looks reasonable
        rest_quote = Mock()
        rest_quote.bid = 923.50
        rest_quote.ask = 923.77
        manager.get_latest_quote = Mock(return_value=rest_quote)
        return manager

    @pytest.fixture
    def mock_pricing_service(self):
        """Mock pricing service for testing."""
        service = Mock()
        return service

    @pytest.fixture
    def quote_provider(self, mock_alpaca_manager, mock_pricing_service):
        """Create quote provider with mocked dependencies."""
        config = ExecutionConfig()
        return QuoteProvider(mock_alpaca_manager, mock_pricing_service, config)

    def test_suspicious_streaming_quote_triggers_rest_validation(self, quote_provider):
        """Test that suspicious streaming quote triggers REST validation."""
        # Create suspicious streaming quote (negative prices like COST issue)
        suspicious_quote = QuoteModel(
            symbol="COST",
            bid_price=Decimal("-0.01"),  # Negative bid price
            ask_price=Decimal("-0.02"),  # Negative ask price
            bid_size=Decimal("1000"),
            ask_size=Decimal("1000"),
            timestamp=datetime.now(UTC),
        )

        # Mock streaming quote return
        quote_provider._try_streaming_quote = Mock(return_value=suspicious_quote)

        # Test that validation is triggered and REST quote is returned
        result = quote_provider.get_quote_with_validation("COST")

        assert result is not None
        quote, used_fallback = result

        # Should use REST fallback due to suspicious streaming data
        assert used_fallback is True
        # Should have reasonable prices from REST
        assert quote.bid_price == Decimal("923.50")
        assert quote.ask_price == Decimal("923.77")

    def test_normal_streaming_quote_no_rest_validation(self, quote_provider):
        """Test that normal streaming quote doesn't trigger REST validation."""
        # Create normal streaming quote
        normal_quote = QuoteModel(
            symbol="COST",
            bid_price=Decimal("923.50"),
            ask_price=Decimal("923.77"),
            bid_size=Decimal("1000"),
            ask_size=Decimal("1000"),
            timestamp=datetime.now(UTC),
        )

        # Mock streaming quote return
        quote_provider._try_streaming_quote = Mock(return_value=normal_quote)

        result = quote_provider.get_quote_with_validation("COST")

        assert result is not None
        quote, used_fallback = result

        # Should use streaming quote without REST validation
        assert used_fallback is False
        assert quote.bid_price == Decimal("923.50")
        assert quote.ask_price == Decimal("923.77")

    def test_suspicious_detection_method(self, quote_provider):
        """Test the _is_streaming_quote_suspicious method directly."""
        # Test with suspicious quote (negative prices)
        suspicious_quote = QuoteModel(
            symbol="TEST",
            bid_price=-0.01,
            ask_price=-0.02,
            bid_size=1000,
            ask_size=1000,
            timestamp=datetime.now(UTC),
        )

        assert quote_provider._is_streaming_quote_suspicious(suspicious_quote, "TEST") is True

        # Test with normal quote
        normal_quote = QuoteModel(
            symbol="TEST",
            bid_price=100.0,
            ask_price=100.25,
            bid_size=1000,
            ask_size=1000,
            timestamp=datetime.now(UTC),
        )

        assert quote_provider._is_streaming_quote_suspicious(normal_quote, "TEST") is False

    def test_rest_validation_handles_rest_failure(self, quote_provider):
        """Test that REST validation handles REST API failures gracefully."""
        # Mock REST API failure
        quote_provider.alpaca_manager.get_latest_quote = Mock(return_value=None)

        suspicious_quote = QuoteModel(
            symbol="COST",
            bid_price=-0.01,
            ask_price=-0.02,
            bid_size=1000,
            ask_size=1000,
            timestamp=datetime.now(UTC),
        )

        result = quote_provider._validate_suspicious_quote_with_rest(suspicious_quote, "COST")

        # Should return None when REST fails
        assert result is None
