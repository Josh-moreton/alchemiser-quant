"""Business Unit: execution | Status: current.

Comprehensive test suite for smart execution strategy quote provider.

This module provides unit tests for quote acquisition, validation, streaming,
and REST API fallback logic.
"""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from unittest.mock import Mock, patch

import pytest

from the_alchemiser.execution_v2.core.smart_execution_strategy.models import ExecutionConfig
from the_alchemiser.execution_v2.core.smart_execution_strategy.quotes import QuoteProvider
from the_alchemiser.shared.types.market_data import QuoteModel


@pytest.fixture
def default_config():
    """Create default execution configuration for tests."""
    return ExecutionConfig()


@pytest.fixture
def mock_alpaca_manager():
    """Create mock Alpaca manager."""
    return Mock()


@pytest.fixture
def mock_pricing_service():
    """Create mock pricing service."""
    return Mock()


@pytest.fixture
def quote_provider(mock_alpaca_manager, mock_pricing_service, default_config):
    """Create quote provider with mocked dependencies."""
    return QuoteProvider(
        alpaca_manager=mock_alpaca_manager,
        pricing_service=mock_pricing_service,
        config=default_config,
    )


class TestGetQuoteWithValidation:
    """Test quote retrieval with validation logic."""

    def test_returns_streaming_quote_when_valid(self, quote_provider, mock_pricing_service):
        """Test that valid streaming quote is returned directly."""
        valid_quote = QuoteModel(
            symbol="AAPL",
            bid_price=Decimal("100.00"),
            ask_price=Decimal("100.50"),
            bid_size=Decimal("100.0"),
            ask_size=Decimal("100.0"),
            timestamp=datetime.now(UTC),
        )
        
        mock_pricing_service.get_quote_data.return_value = valid_quote
        
        result = quote_provider.get_quote_with_validation("AAPL")
        
        assert result is not None
        quote, used_fallback = result
        assert quote.symbol == "AAPL"
        assert used_fallback is False

    def test_falls_back_to_rest_when_streaming_unavailable(
        self, quote_provider, mock_pricing_service, mock_alpaca_manager
    ):
        """Test fallback to REST API when streaming is unavailable."""
        # Streaming returns None
        mock_pricing_service.get_quote_data.return_value = None
        
        # REST returns valid quote
        rest_quote = Mock()
        rest_quote.bid_price = Decimal("100.00")
        rest_quote.ask_price = Decimal("100.50")
        mock_alpaca_manager.get_latest_quote.return_value = rest_quote
        
        result = quote_provider.get_quote_with_validation("AAPL")
        
        assert result is not None
        quote, used_fallback = result
        assert quote.symbol == "AAPL"
        assert used_fallback is True
        mock_alpaca_manager.get_latest_quote.assert_called_once_with("AAPL")

    def test_returns_none_when_both_sources_fail(
        self, quote_provider, mock_pricing_service, mock_alpaca_manager
    ):
        """Test returns None when both streaming and REST fail."""
        # Both sources return None
        mock_pricing_service.get_quote_data.return_value = None
        mock_alpaca_manager.get_latest_quote.return_value = None
        
        result = quote_provider.get_quote_with_validation("AAPL")
        
        assert result is None


class TestStreamingQuoteValidation:
    """Test streaming quote validation logic."""

    def test_valid_fresh_quote_passes(self, quote_provider):
        """Test that fresh quote with valid prices passes validation."""
        quote = QuoteModel(
            symbol="AAPL",
            bid_price=Decimal("100.00"),
            ask_price=Decimal("100.50"),
            bid_size=Decimal("100.0"),
            ask_size=Decimal("100.0"),
            timestamp=datetime.now(UTC),
        )
        
        is_valid = quote_provider._is_streaming_quote_valid(quote, "AAPL")
        
        assert is_valid is True

    def test_stale_quote_fails_validation(self, quote_provider):
        """Test that stale quote fails validation."""
        # Quote is 10 seconds old (> 5 second freshness requirement)
        old_timestamp = datetime.now(UTC) - timedelta(seconds=10)
        quote = QuoteModel(
            symbol="AAPL",
            bid_price=Decimal("100.00"),
            ask_price=Decimal("100.50"),
            bid_size=Decimal("100.0"),
            ask_size=Decimal("100.0"),
            timestamp=old_timestamp,
        )
        
        is_valid = quote_provider._is_streaming_quote_valid(quote, "AAPL")
        
        assert is_valid is False

    def test_invalid_prices_fail_validation(self, quote_provider):
        """Test that both prices being zero fails validation."""
        # Both zero bid and ask prices
        quote = QuoteModel(
            symbol="AAPL",
            bid_price=Decimal("0.00"),
            ask_price=Decimal("0.00"),
            bid_size=Decimal("100.0"),
            ask_size=Decimal("100.0"),
            timestamp=datetime.now(UTC),
        )
        
        is_valid = quote_provider._is_streaming_quote_valid(quote, "AAPL")
        
        assert is_valid is False

    def test_negative_prices_fail_validation(self, quote_provider):
        """Test that both negative prices fail validation."""
        quote = QuoteModel(
            symbol="AAPL",
            bid_price=Decimal("-10.00"),
            ask_price=Decimal("-5.00"),
            bid_size=Decimal("100.0"),
            ask_size=Decimal("100.0"),
            timestamp=datetime.now(UTC),
        )
        
        is_valid = quote_provider._is_streaming_quote_valid(quote, "AAPL")
        
        assert is_valid is False


class TestSuspiciousQuoteDetection:
    """Test suspicious quote pattern detection."""

    def test_negative_prices_detected_as_suspicious(self, quote_provider):
        """Test that negative prices are flagged as suspicious."""
        quote = QuoteModel(
            symbol="AAPL",
            bid_price=Decimal("-1.00"),
            ask_price=Decimal("100.00"),
            bid_size=Decimal("100.0"),
            ask_size=Decimal("100.0"),
            timestamp=datetime.now(UTC),
        )
        
        is_suspicious = quote_provider._is_streaming_quote_suspicious(quote, "AAPL")
        
        assert is_suspicious is True

    def test_inverted_spread_detected_as_suspicious(self, quote_provider):
        """Test that inverted spread (ask < bid) is flagged."""
        quote = QuoteModel(
            symbol="AAPL",
            bid_price=Decimal("100.00"),
            ask_price=Decimal("99.00"),  # Ask < Bid
            bid_size=Decimal("100.0"),
            ask_size=Decimal("100.0"),
            timestamp=datetime.now(UTC),
        )
        
        is_suspicious = quote_provider._is_streaming_quote_suspicious(quote, "AAPL")
        
        assert is_suspicious is True

    def test_penny_stock_prices_detected_as_suspicious(self, quote_provider):
        """Test that unreasonably low prices are flagged."""
        quote = QuoteModel(
            symbol="AAPL",
            bid_price=Decimal("0.005"),
            ask_price=Decimal("0.008"),
            bid_size=Decimal("100.0"),
            ask_size=Decimal("100.0"),
            timestamp=datetime.now(UTC),
        )
        
        is_suspicious = quote_provider._is_streaming_quote_suspicious(quote, "AAPL")
        
        assert is_suspicious is True

    def test_excessive_spread_detected_as_suspicious(self, quote_provider):
        """Test that excessive spreads are flagged."""
        quote = QuoteModel(
            symbol="AAPL",
            bid_price=Decimal("100.00"),
            ask_price=Decimal("115.00"),  # 15% spread
            bid_size=Decimal("100.0"),
            ask_size=Decimal("100.0"),
            timestamp=datetime.now(UTC),
        )
        
        is_suspicious = quote_provider._is_streaming_quote_suspicious(quote, "AAPL")
        
        assert is_suspicious is True

    def test_normal_quote_not_suspicious(self, quote_provider):
        """Test that normal quotes are not flagged."""
        quote = QuoteModel(
            symbol="AAPL",
            bid_price=Decimal("100.00"),
            ask_price=Decimal("100.25"),  # 0.25% spread
            bid_size=Decimal("100.0"),
            ask_size=Decimal("100.0"),
            timestamp=datetime.now(UTC),
        )
        
        is_suspicious = quote_provider._is_streaming_quote_suspicious(quote, "AAPL")
        
        assert is_suspicious is False


class TestRestFallbackQuote:
    """Test REST API fallback quote retrieval."""

    def test_rest_quote_success(self, quote_provider, mock_alpaca_manager):
        """Test successful REST quote retrieval."""
        rest_quote = Mock()
        rest_quote.bid_price = Decimal("100.00")
        rest_quote.ask_price = Decimal("100.50")
        mock_alpaca_manager.get_latest_quote.return_value = rest_quote
        
        result = quote_provider._try_rest_fallback_quote("AAPL")
        
        assert result is not None
        quote, used_fallback = result
        assert quote.symbol == "AAPL"
        assert quote.bid_price == 100.00
        assert quote.ask_price == 100.50
        assert used_fallback is True

    def test_rest_quote_failure(self, quote_provider, mock_alpaca_manager):
        """Test REST quote failure returns None."""
        mock_alpaca_manager.get_latest_quote.return_value = None
        
        result = quote_provider._try_rest_fallback_quote("AAPL")
        
        assert result is None

    def test_rest_quote_sets_zero_sizes(self, quote_provider, mock_alpaca_manager):
        """Test that REST quote sets bid/ask sizes to zero."""
        rest_quote = Mock()
        rest_quote.bid_price = Decimal("100.00")
        rest_quote.ask_price = Decimal("100.50")
        mock_alpaca_manager.get_latest_quote.return_value = rest_quote
        
        result = quote_provider._try_rest_fallback_quote("AAPL")
        
        assert result is not None
        quote, _ = result
        assert quote.bid_size == 0.0
        assert quote.ask_size == 0.0


class TestValidateQuoteLiquidity:
    """Test quote liquidity validation."""

    def test_valid_liquid_quote_passes(self, quote_provider):
        """Test that quote with good liquidity passes validation."""
        quote = {
            "bid_price": 100.00,
            "ask_price": 100.25,
            "bid_size": 200,
            "ask_size": 200,
        }
        
        is_valid = quote_provider.validate_quote_liquidity("AAPL", quote)
        
        assert is_valid is True

    def test_zero_bid_price_fails(self, quote_provider):
        """Test that zero bid price fails validation."""
        quote = {
            "bid_price": 0.00,
            "ask_price": 100.25,
            "bid_size": 200,
            "ask_size": 200,
        }
        
        is_valid = quote_provider.validate_quote_liquidity("AAPL", quote)
        
        assert is_valid is False

    def test_zero_ask_price_fails(self, quote_provider):
        """Test that zero ask price fails validation."""
        quote = {
            "bid_price": 100.00,
            "ask_price": 0.00,
            "bid_size": 200,
            "ask_size": 200,
        }
        
        is_valid = quote_provider.validate_quote_liquidity("AAPL", quote)
        
        assert is_valid is False

    def test_wide_spread_fails(self, quote_provider):
        """Test that wide spread fails validation."""
        quote = {
            "bid_price": 100.00,
            "ask_price": 101.00,  # 1% spread (> 0.5% limit)
            "bid_size": 200,
            "ask_size": 200,
        }
        
        is_valid = quote_provider.validate_quote_liquidity("AAPL", quote)
        
        assert is_valid is False

    def test_insufficient_bid_size_fails(self, quote_provider):
        """Test that insufficient bid size fails validation."""
        quote = {
            "bid_price": 100.00,
            "ask_price": 100.25,
            "bid_size": 50,  # < 100 minimum
            "ask_size": 200,
        }
        
        is_valid = quote_provider.validate_quote_liquidity("AAPL", quote)
        
        assert is_valid is False

    def test_insufficient_ask_size_fails(self, quote_provider):
        """Test that insufficient ask size fails validation."""
        quote = {
            "bid_price": 100.00,
            "ask_price": 100.25,
            "bid_size": 200,
            "ask_size": 50,  # < 100 minimum
        }
        
        is_valid = quote_provider.validate_quote_liquidity("AAPL", quote)
        
        assert is_valid is False

    def test_handles_object_format(self, quote_provider):
        """Test that validation works with object format."""
        quote = Mock()
        quote.bid_price = 100.00
        quote.ask_price = 100.25
        quote.bid_size = 200
        quote.ask_size = 200
        
        is_valid = quote_provider.validate_quote_liquidity("AAPL", quote)
        
        assert is_valid is True

    def test_handles_exception_gracefully(self, quote_provider):
        """Test that validation handles exceptions gracefully."""
        # Invalid quote that will cause attribute error
        quote = None
        
        is_valid = quote_provider.validate_quote_liquidity("AAPL", quote)
        
        assert is_valid is False


class TestCheckQuoteSuspiciousPatterns:
    """Test quote suspicious pattern checking without logging."""

    def test_returns_tuple_of_bool_and_reasons(self, quote_provider):
        """Test that function returns correct tuple format."""
        quote = QuoteModel(
            symbol="AAPL",
            bid_price=Decimal("-1.00"),
            ask_price=Decimal("100.00"),
            bid_size=Decimal("100.0"),
            ask_size=Decimal("100.0"),
            timestamp=datetime.now(UTC),
        )
        
        is_suspicious, reasons = quote_provider._check_quote_suspicious_patterns(quote)
        
        assert isinstance(is_suspicious, bool)
        assert isinstance(reasons, list)
        assert is_suspicious is True
        assert len(reasons) > 0

    def test_normal_quote_returns_empty_reasons(self, quote_provider):
        """Test that normal quote returns no reasons."""
        quote = QuoteModel(
            symbol="AAPL",
            bid_price=Decimal("100.00"),
            ask_price=Decimal("100.25"),
            bid_size=Decimal("100.0"),
            ask_size=Decimal("100.0"),
            timestamp=datetime.now(UTC),
        )
        
        is_suspicious, reasons = quote_provider._check_quote_suspicious_patterns(quote)
        
        assert is_suspicious is False
        assert len(reasons) == 0


class TestQuoteProviderInitialization:
    """Test quote provider initialization."""

    def test_initializes_with_all_dependencies(self):
        """Test initialization with all dependencies provided."""
        alpaca = Mock()
        pricing = Mock()
        config = ExecutionConfig()
        
        provider = QuoteProvider(alpaca, pricing, config)
        
        assert provider.alpaca_manager is alpaca
        assert provider.pricing_service is pricing
        assert provider.config is config

    def test_initializes_with_default_config(self):
        """Test initialization uses default config when not provided."""
        alpaca = Mock()
        pricing = Mock()
        
        provider = QuoteProvider(alpaca, pricing)
        
        assert provider.config is not None
        assert isinstance(provider.config, ExecutionConfig)

    def test_initializes_without_pricing_service(self):
        """Test initialization works without pricing service."""
        alpaca = Mock()
        
        provider = QuoteProvider(alpaca, None)
        
        assert provider.pricing_service is None
        assert provider.alpaca_manager is alpaca


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_handles_missing_quote_fields(self, quote_provider):
        """Test handling of quotes with missing fields."""
        incomplete_quote = {
            "bid_price": 100.00,
            # Missing ask_price, bid_size, ask_size
        }
        
        is_valid = quote_provider.validate_quote_liquidity("AAPL", incomplete_quote)
        
        # Should handle gracefully and return False
        assert is_valid is False

    def test_handles_quote_at_spread_boundary(self, quote_provider):
        """Test quote validation at exact spread limit."""
        # Exactly at 0.5% spread limit
        quote = {
            "bid_price": 100.00,
            "ask_price": 100.50,  # 0.5% spread
            "bid_size": 200,
            "ask_size": 200,
        }
        
        is_valid = quote_provider.validate_quote_liquidity("AAPL", quote)
        
        # Should pass at exact limit
        assert is_valid is True

    def test_handles_quote_at_size_boundary(self, quote_provider):
        """Test quote validation at exact size limit."""
        # Exactly at 100 size limit
        quote = {
            "bid_price": 100.00,
            "ask_price": 100.25,
            "bid_size": 100,  # Exactly at minimum
            "ask_size": 100,  # Exactly at minimum
        }
        
        is_valid = quote_provider.validate_quote_liquidity("AAPL", quote)
        
        # Should pass at exact limit
        assert is_valid is True


class TestWaitForQuoteData:
    """Test waiting for quote data with timeouts."""

    def test_returns_none_when_no_pricing_service(self, mock_alpaca_manager):
        """Test that function returns None when pricing service is unavailable."""
        provider = QuoteProvider(mock_alpaca_manager, None)
        
        result = provider.wait_for_quote_data("AAPL", timeout=1.0)
        
        assert result is None

    def test_returns_immediate_quote_if_available(
        self, quote_provider, mock_pricing_service
    ):
        """Test that immediate quote is returned if available."""
        real_time_quote = Mock()
        real_time_quote.bid = 100.00
        real_time_quote.ask = 100.50
        real_time_quote.timestamp = datetime.now(UTC)
        
        mock_pricing_service.get_real_time_quote.return_value = real_time_quote
        
        result = quote_provider.wait_for_quote_data("AAPL", timeout=1.0)
        
        assert result is not None
        assert result["bid_price"] == 100.00
        assert result["ask_price"] == 100.50


class TestValidateSuspiciousQuoteWithRest:
    """Test validation of suspicious quotes using REST API."""

    def test_returns_rest_quote_when_rest_is_valid(
        self, quote_provider, mock_alpaca_manager
    ):
        """Test that valid REST quote is returned."""
        streaming_quote = QuoteModel(
            symbol="AAPL",
            bid_price=Decimal("-1.00"),  # Suspicious
            ask_price=Decimal("100.00"),
            bid_size=Decimal("100.0"),
            ask_size=Decimal("100.0"),
            timestamp=datetime.now(UTC),
        )
        
        rest_quote = QuoteModel(
            symbol="AAPL",
            bid_price=Decimal("100.00"),
            ask_price=Decimal("100.50"),
            bid_size=Decimal("100"),
            ask_size=Decimal("100"),
            timestamp=datetime.now(UTC),
        )
        mock_alpaca_manager.get_latest_quote.return_value = rest_quote
        
        result = quote_provider._validate_suspicious_quote_with_rest(
            streaming_quote, "AAPL"
        )
        
        assert result is not None
        quote, used_fallback = result
        assert quote.bid_price == Decimal("100.00")
        assert used_fallback is True

    def test_returns_none_when_rest_fails(
        self, quote_provider, mock_alpaca_manager
    ):
        """Test returns None when REST quote fetch fails."""
        streaming_quote = QuoteModel(
            symbol="AAPL",
            bid_price=Decimal("-1.00"),  # Suspicious
            ask_price=Decimal("100.00"),
            bid_size=Decimal("100.0"),
            ask_size=Decimal("100.0"),
            timestamp=datetime.now(UTC),
        )
        
        mock_alpaca_manager.get_latest_quote.return_value = None
        
        result = quote_provider._validate_suspicious_quote_with_rest(
            streaming_quote, "AAPL"
        )
        
        assert result is None

    def test_returns_none_when_rest_also_suspicious(
        self, quote_provider, mock_alpaca_manager
    ):
        """Test returns None when REST quote is also suspicious."""
        streaming_quote = QuoteModel(
            symbol="AAPL",
            bid_price=Decimal("-1.00"),  # Suspicious
            ask_price=Decimal("100.00"),
            bid_size=Decimal("100.0"),
            ask_size=Decimal("100.0"),
            timestamp=datetime.now(UTC),
        )
        
        # REST quote is also suspicious
        rest_quote = Mock()
        rest_quote.bid_price = Decimal("-2.00")  # Also suspicious
        rest_quote.ask_price = Decimal("100.00")
        mock_alpaca_manager.get_latest_quote.return_value = rest_quote
        
        result = quote_provider._validate_suspicious_quote_with_rest(
            streaming_quote, "AAPL"
        )
        
        assert result is None

    def test_prefers_rest_when_mid_differs_significantly(
        self, quote_provider, mock_alpaca_manager
    ):
        """Test that REST is preferred when mid-price differs significantly."""
        streaming_quote = QuoteModel(
            symbol="AAPL",
            bid_price=Decimal("100.00"),
            ask_price=Decimal("120.00"),  # Suspicious wide spread
            bid_size=Decimal("100.0"),
            ask_size=Decimal("100.0"),
            timestamp=datetime.now(UTC),
        )
        
        # REST quote with normal spread
        rest_quote = Mock()
        rest_quote.bid_price = Decimal("100.00")
        rest_quote.ask_price = Decimal("100.50")
        mock_alpaca_manager.get_latest_quote.return_value = rest_quote
        
        result = quote_provider._validate_suspicious_quote_with_rest(
            streaming_quote, "AAPL"
        )
        
        assert result is not None
        quote, _ = result
        # Should use REST quote
        assert quote.bid_price == 100.00
        assert quote.ask_price == 100.50


class TestSuspiciousQuoteIntegration:
    """Test integration of suspicious quote detection with get_quote_with_validation."""

    def test_validates_suspicious_streaming_quote_with_rest(
        self, quote_provider, mock_pricing_service, mock_alpaca_manager
    ):
        """Test that suspicious streaming quote triggers REST validation."""
        # Suspicious streaming quote
        suspicious_quote = QuoteModel(
            symbol="AAPL",
            bid_price=Decimal("-1.00"),  # Suspicious negative price
            ask_price=Decimal("100.00"),
            bid_size=Decimal("100.0"),
            ask_size=Decimal("100.0"),
            timestamp=datetime.now(UTC),
        )
        
        mock_pricing_service.get_quote_data.return_value = suspicious_quote
        
        # Valid REST quote
        rest_quote = Mock()
        rest_quote.bid_price = Decimal("100.00")
        rest_quote.ask_price = Decimal("100.50")
        mock_alpaca_manager.get_latest_quote.return_value = rest_quote
        
        result = quote_provider.get_quote_with_validation("AAPL")
        
        # Should return REST quote due to suspicious streaming quote
        assert result is not None
        quote, used_fallback = result
        assert quote.bid_price == 100.00
        assert used_fallback is True
        mock_alpaca_manager.get_latest_quote.assert_called_once()

    def test_uses_streaming_quote_when_rest_validation_fails(
        self, quote_provider, mock_pricing_service, mock_alpaca_manager
    ):
        """Test that streaming quote is used when REST validation fails."""
        # Suspicious streaming quote
        suspicious_quote = QuoteModel(
            symbol="AAPL",
            bid_price=Decimal("-1.00"),  # Suspicious
            ask_price=Decimal("100.00"),
            bid_size=Decimal("100.0"),
            ask_size=Decimal("100.0"),
            timestamp=datetime.now(UTC),
        )
        
        mock_pricing_service.get_quote_data.return_value = suspicious_quote
        
        # REST fetch fails
        mock_alpaca_manager.get_latest_quote.return_value = None
        
        result = quote_provider.get_quote_with_validation("AAPL")
        
        # Should return streaming quote despite being suspicious
        assert result is not None
        quote, used_fallback = result
        assert quote.symbol == "AAPL"
        assert used_fallback is False


class TestInvertedSpreadValidation:
    """Test detection and handling of inverted spreads."""

    def test_inverted_spread_fails_validate_quote_prices(self, quote_provider):
        """Test that inverted spread (bid > ask) fails validation."""
        quote = QuoteModel(
            symbol="AAPL",
            bid_price=Decimal("100.50"),  # Bid > Ask
            ask_price=Decimal("100.00"),
            bid_size=Decimal("100.0"),
            ask_size=Decimal("100.0"),
            timestamp=datetime.now(UTC),
        )
        
        is_valid = quote_provider._is_streaming_quote_valid(quote, "AAPL")
        
        # Should fail due to inverted spread
        assert is_valid is False


class TestTryStreamingQuote:
    """Test streaming quote retrieval logic."""

    def test_returns_none_when_no_pricing_service(self, mock_alpaca_manager):
        """Test returns None when pricing service is not available."""
        provider = QuoteProvider(mock_alpaca_manager, None)
        
        result = provider._try_streaming_quote("AAPL")
        
        assert result is None

    def test_returns_valid_quote_from_service(self, quote_provider, mock_pricing_service):
        """Test returns valid quote from pricing service."""
        valid_quote = QuoteModel(
            symbol="AAPL",
            bid_price=Decimal("100.00"),
            ask_price=Decimal("100.50"),
            bid_size=Decimal("100.0"),
            ask_size=Decimal("100.0"),
            timestamp=datetime.now(UTC),
        )
        
        mock_pricing_service.get_quote_data.return_value = valid_quote
        
        result = quote_provider._try_streaming_quote("AAPL")
        
        assert result is not None
        assert result.symbol == "AAPL"

    def test_returns_none_when_quote_invalid(self, quote_provider, mock_pricing_service):
        """Test returns None when quote is invalid (stale)."""
        # Stale quote
        stale_quote = QuoteModel(
            symbol="AAPL",
            bid_price=Decimal("100.00"),
            ask_price=Decimal("100.50"),
            bid_size=Decimal("100.0"),
            ask_size=Decimal("100.0"),
            timestamp=datetime.now(UTC) - timedelta(seconds=10),
        )
        
        mock_pricing_service.get_quote_data.return_value = stale_quote
        
        result = quote_provider._try_streaming_quote("AAPL")
        
        assert result is None


class TestWaitForStreamingQuote:
    """Test waiting logic for streaming quotes."""

    def test_returns_none_when_no_pricing_service(self, mock_alpaca_manager):
        """Test returns None immediately when no pricing service."""
        provider = QuoteProvider(mock_alpaca_manager, None)
        
        result = provider._wait_for_streaming_quote("AAPL")
        
        assert result is None

    def test_returns_quote_when_available(self, quote_provider, mock_pricing_service):
        """Test returns quote when it becomes available."""
        valid_quote = QuoteModel(
            symbol="AAPL",
            bid_price=Decimal("100.00"),
            ask_price=Decimal("100.50"),
            bid_size=Decimal("100.0"),
            ask_size=Decimal("100.0"),
            timestamp=datetime.now(UTC),
        )
        
        mock_pricing_service.get_quote_data.return_value = valid_quote
        
        result = quote_provider._wait_for_streaming_quote("AAPL")
        
        assert result is not None


class TestRestQuoteExtraction:
    """Test REST quote data extraction."""

    def test_extracts_bid_ask_from_rest_quote(self, quote_provider, mock_alpaca_manager):
        """Test that bid/ask are correctly extracted from REST quote."""
        rest_quote = Mock()
        rest_quote.bid_price = Decimal("99.75")
        rest_quote.ask_price = Decimal("100.25")
        mock_alpaca_manager.get_latest_quote.return_value = rest_quote
        
        result = quote_provider._try_rest_fallback_quote("AAPL")
        
        assert result is not None
        quote, _ = result
        assert quote.bid_price == 99.75
        assert quote.ask_price == 100.25

    def test_sets_timestamp_to_now(self, quote_provider, mock_alpaca_manager):
        """Test that REST quote timestamp is set to current time."""
        rest_quote = Mock()
        rest_quote.bid_price = Decimal("100.00")
        rest_quote.ask_price = Decimal("100.50")
        mock_alpaca_manager.get_latest_quote.return_value = rest_quote
        
        before = datetime.now(UTC)
        result = quote_provider._try_rest_fallback_quote("AAPL")
        after = datetime.now(UTC)
        
        assert result is not None
        quote, _ = result
        assert before <= quote.timestamp <= after


class TestMidPriceComparison:
    """Test mid-price comparison logic in REST validation."""

    def test_uses_rest_when_streaming_mid_is_zero(
        self, quote_provider, mock_alpaca_manager
    ):
        """Test that REST is preferred when streaming mid-price is zero."""
        streaming_quote = QuoteModel(
            symbol="AAPL",
            bid_price=Decimal("0.00"),
            ask_price=Decimal("0.00"),
            bid_size=Decimal("100.0"),
            ask_size=Decimal("100.0"),
            timestamp=datetime.now(UTC),
        )
        
        rest_quote = Mock()
        rest_quote.bid_price = Decimal("100.00")
        rest_quote.ask_price = Decimal("100.50")
        mock_alpaca_manager.get_latest_quote.return_value = rest_quote
        
        result = quote_provider._validate_suspicious_quote_with_rest(
            streaming_quote, "AAPL"
        )
        
        assert result is not None

    def test_uses_rest_when_mid_prices_similar(
        self, quote_provider, mock_alpaca_manager
    ):
        """Test that REST is used for safety when mid-prices are similar."""
        streaming_quote = QuoteModel(
            symbol="AAPL",
            bid_price=Decimal("100.00"),
            ask_price=Decimal("100.50"),  # Mid = 100.25
            bid_size=Decimal("100.0"),
            ask_size=Decimal("100.0"),
            timestamp=datetime.now(UTC),
        )
        
        # REST with similar mid-price
        rest_quote = Mock()
        rest_quote.bid_price = Decimal("100.10")
        rest_quote.ask_price = Decimal("100.40")  # Mid = 100.25 (same)
        mock_alpaca_manager.get_latest_quote.return_value = rest_quote
        
        result = quote_provider._validate_suspicious_quote_with_rest(
            streaming_quote, "AAPL"
        )
        
        assert result is not None
        quote, used_fallback = result
        # Should use REST for safety
        assert used_fallback is True
