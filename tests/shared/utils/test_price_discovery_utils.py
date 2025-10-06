"""Business Unit: shared | Status: current

Comprehensive unit tests for price discovery utilities.

This test suite provides full coverage of all price discovery functions,
including edge cases, error conditions, and protocol implementations.
"""

import math
from decimal import Decimal
from unittest.mock import Mock

import pytest

from the_alchemiser.shared.types.quote import QuoteModel
from the_alchemiser.shared.utils.price_discovery_utils import (
    LegacyQuoteProvider,
    PriceProvider,
    QuoteProvider,
    calculate_midpoint_price,
    get_current_price_as_decimal,
    get_current_price_from_quote,
    get_current_price_with_fallback,
)


class TestCalculateMidpointPrice:
    """Test midpoint price calculation functionality."""

    def test_valid_bid_ask_returns_midpoint(self):
        """Test that valid bid-ask spread returns correct midpoint."""
        result = calculate_midpoint_price(100.0, 101.0)
        assert result == 100.5

    def test_equal_bid_ask_returns_same_price(self):
        """Test that equal bid and ask returns the same price."""
        result = calculate_midpoint_price(100.0, 100.0)
        assert result == 100.0

    def test_zero_bid_returns_none(self):
        """Test that zero bid returns None."""
        result = calculate_midpoint_price(0.0, 101.0)
        assert result is None

    def test_zero_ask_returns_none(self):
        """Test that zero ask returns None."""
        result = calculate_midpoint_price(100.0, 0.0)
        assert result is None

    def test_negative_bid_returns_none(self):
        """Test that negative bid returns None."""
        result = calculate_midpoint_price(-1.0, 101.0)
        assert result is None

    def test_negative_ask_returns_none(self):
        """Test that negative ask returns None."""
        result = calculate_midpoint_price(100.0, -1.0)
        assert result is None

    def test_ask_less_than_bid_returns_none(self):
        """Test that ask < bid (crossed market) returns None."""
        result = calculate_midpoint_price(101.0, 100.0)
        assert result is None

    def test_type_error_returns_none(self):
        """Test that TypeError is handled gracefully."""
        result = calculate_midpoint_price("invalid", 100.0)  # type: ignore
        assert result is None

    def test_value_error_returns_none(self):
        """Test that ValueError is handled gracefully."""
        result = calculate_midpoint_price(float("nan"), 100.0)
        assert result is None

    def test_large_spread_calculates_correctly(self):
        """Test calculation with large spread."""
        result = calculate_midpoint_price(100.0, 200.0)
        assert result == 150.0

    def test_small_prices_precision(self):
        """Test precision with small prices."""
        result = calculate_midpoint_price(0.01, 0.02)
        assert result is not None
        # Use tolerance for float comparison
        assert math.isclose(result, 0.015, rel_tol=1e-9)


class TestGetCurrentPriceFromQuote:
    """Test getting current price from quote provider."""

    def test_quote_provider_with_quote_model(self):
        """Test QuoteProvider returning QuoteModel."""
        mock_provider = Mock(spec=QuoteProvider)
        quote = QuoteModel(
            ts=None, bid=Decimal("100.0"), ask=Decimal("101.0")
        )
        mock_provider.get_latest_quote.return_value = quote

        result = get_current_price_from_quote(mock_provider, "AAPL")

        assert result == 100.5
        mock_provider.get_latest_quote.assert_called_once_with("AAPL")

    def test_legacy_quote_provider_with_tuple(self):
        """Test LegacyQuoteProvider returning tuple."""
        mock_provider = Mock(spec=LegacyQuoteProvider)
        mock_provider.get_latest_quote.return_value = (100.0, 101.0)

        result = get_current_price_from_quote(mock_provider, "AAPL")

        assert result == 100.5
        mock_provider.get_latest_quote.assert_called_once_with("AAPL")

    def test_quote_model_with_mid_property(self):
        """Test QuoteModel with pre-calculated mid property."""
        mock_provider = Mock(spec=QuoteProvider)
        quote = QuoteModel(
            ts=None, bid=Decimal("100.0"), ask=Decimal("102.0")
        )
        mock_provider.get_latest_quote.return_value = quote

        result = get_current_price_from_quote(mock_provider, "AAPL")

        # Should calculate from bid/ask, not use mid directly
        assert result == 101.0

    def test_none_quote_returns_none(self):
        """Test that None quote returns None."""
        mock_provider = Mock(spec=QuoteProvider)
        mock_provider.get_latest_quote.return_value = None

        result = get_current_price_from_quote(mock_provider, "AAPL")

        assert result is None

    def test_invalid_tuple_length_returns_none(self):
        """Test that invalid tuple length returns None."""
        mock_provider = Mock(spec=LegacyQuoteProvider)
        mock_provider.get_latest_quote.return_value = (100.0,)  # Wrong length

        result = get_current_price_from_quote(mock_provider, "AAPL")

        assert result is None

    def test_unexpected_quote_type_returns_none(self):
        """Test that unexpected quote type returns None."""
        mock_provider = Mock(spec=QuoteProvider)
        mock_provider.get_latest_quote.return_value = {"bid": 100.0, "ask": 101.0}

        result = get_current_price_from_quote(mock_provider, "AAPL")

        assert result is None

    def test_exception_handling_returns_none(self):
        """Test that exceptions are caught and None is returned."""
        mock_provider = Mock(spec=QuoteProvider)
        mock_provider.get_latest_quote.side_effect = RuntimeError("API error")

        result = get_current_price_from_quote(mock_provider, "AAPL")

        assert result is None

    def test_invalid_bid_ask_returns_none(self):
        """Test that invalid bid/ask in QuoteModel returns None."""
        mock_provider = Mock(spec=QuoteProvider)
        quote = QuoteModel(
            ts=None, bid=Decimal("0.0"), ask=Decimal("101.0")
        )
        mock_provider.get_latest_quote.return_value = quote

        result = get_current_price_from_quote(mock_provider, "AAPL")

        assert result is None


class TestGetCurrentPriceWithFallback:
    """Test price discovery with fallback strategy."""

    def test_primary_provider_success(self):
        """Test that primary provider is used when successful."""
        primary = Mock(spec=PriceProvider)
        primary.get_current_price.return_value = 100.0
        fallback = Mock(spec=PriceProvider)

        result = get_current_price_with_fallback(primary, fallback, "AAPL")

        assert result == 100.0
        primary.get_current_price.assert_called_once_with("AAPL")
        fallback.get_current_price.assert_not_called()

    def test_fallback_provider_used_when_primary_fails(self):
        """Test that fallback is used when primary returns None."""
        primary = Mock(spec=PriceProvider)
        primary.get_current_price.return_value = None
        fallback = Mock(spec=PriceProvider)
        fallback.get_current_price.return_value = 100.0

        result = get_current_price_with_fallback(primary, fallback, "AAPL")

        assert result == 100.0
        primary.get_current_price.assert_called_once_with("AAPL")
        fallback.get_current_price.assert_called_once_with("AAPL")

    def test_both_providers_fail_returns_none(self):
        """Test that None is returned when both providers fail."""
        primary = Mock(spec=PriceProvider)
        primary.get_current_price.return_value = None
        fallback = Mock(spec=PriceProvider)
        fallback.get_current_price.return_value = None

        result = get_current_price_with_fallback(primary, fallback, "AAPL")

        assert result is None

    def test_none_fallback_provider(self):
        """Test behavior when fallback provider is None."""
        primary = Mock(spec=PriceProvider)
        primary.get_current_price.return_value = None

        result = get_current_price_with_fallback(primary, None, "AAPL")

        assert result is None

    def test_quote_provider_as_primary(self):
        """Test using QuoteProvider as primary."""
        primary = Mock(spec=QuoteProvider)
        quote = QuoteModel(
            ts=None, bid=Decimal("100.0"), ask=Decimal("101.0")
        )
        primary.get_latest_quote.return_value = quote
        fallback = Mock(spec=PriceProvider)

        result = get_current_price_with_fallback(primary, fallback, "AAPL")

        assert result == 100.5

    def test_exception_in_primary_uses_fallback(self):
        """Test that exception in primary still attempts fallback."""
        primary = Mock(spec=PriceProvider)
        primary.get_current_price.side_effect = RuntimeError("API error")
        fallback = Mock(spec=PriceProvider)
        fallback.get_current_price.return_value = 100.0

        result = get_current_price_with_fallback(primary, fallback, "AAPL")

        # Exception is caught and fallback is used
        assert result == 100.0
        fallback.get_current_price.assert_called_once_with("AAPL")


class TestGetCurrentPriceAsDecimal:
    """Test getting current price as Decimal."""

    def test_price_provider_returns_decimal(self):
        """Test that PriceProvider result is converted to Decimal."""
        provider = Mock(spec=PriceProvider)
        provider.get_current_price.return_value = 100.5

        result = get_current_price_as_decimal(provider, "AAPL")

        assert result == Decimal("100.5")
        assert isinstance(result, Decimal)

    def test_quote_provider_returns_decimal(self):
        """Test that QuoteProvider result is converted to Decimal."""
        provider = Mock(spec=QuoteProvider)
        quote = QuoteModel(
            ts=None, bid=Decimal("100.0"), ask=Decimal("101.0")
        )
        provider.get_latest_quote.return_value = quote

        result = get_current_price_as_decimal(provider, "AAPL")

        assert result == Decimal("100.5")
        assert isinstance(result, Decimal)

    def test_none_price_returns_none(self):
        """Test that None price returns None."""
        provider = Mock(spec=PriceProvider)
        provider.get_current_price.return_value = None

        result = get_current_price_as_decimal(provider, "AAPL")

        assert result is None

    def test_float_precision_preserved_via_string(self):
        """Test that float is converted via string to preserve precision."""
        provider = Mock(spec=PriceProvider)
        # This value has precision issues when converted directly
        provider.get_current_price.return_value = 0.1 + 0.2

        result = get_current_price_as_decimal(provider, "AAPL")

        # Should be converted via string, preserving the float's representation
        assert result is not None
        # The result should match the string representation of the float
        assert result == Decimal(str(0.1 + 0.2))

    def test_exception_handling_returns_none(self):
        """Test that exceptions are caught and None is returned."""
        provider = Mock(spec=PriceProvider)
        provider.get_current_price.side_effect = RuntimeError("API error")

        result = get_current_price_as_decimal(provider, "AAPL")

        assert result is None

    def test_large_price_converted_correctly(self):
        """Test that large prices are converted correctly."""
        provider = Mock(spec=PriceProvider)
        provider.get_current_price.return_value = 12345.6789

        result = get_current_price_as_decimal(provider, "AAPL")

        assert result == Decimal("12345.6789")


class TestProtocolImplementations:
    """Test that protocols work correctly with different implementations."""

    def test_quote_provider_protocol_compliance(self):
        """Test that custom QuoteProvider implementation works."""

        class CustomQuoteProvider:
            def get_latest_quote(self, symbol: str) -> QuoteModel | None:
                return QuoteModel(
                    ts=None, bid=Decimal("100.0"), ask=Decimal("101.0")
                )

        provider = CustomQuoteProvider()
        result = get_current_price_from_quote(provider, "AAPL")

        assert result == 100.5

    def test_legacy_quote_provider_protocol_compliance(self):
        """Test that custom LegacyQuoteProvider implementation works."""

        class CustomLegacyProvider:
            def get_latest_quote(self, symbol: str) -> tuple[float, float] | None:
                return (100.0, 101.0)

        provider = CustomLegacyProvider()
        result = get_current_price_from_quote(provider, "AAPL")

        assert result == 100.5

    def test_price_provider_protocol_compliance(self):
        """Test that custom PriceProvider implementation works."""

        class CustomPriceProvider:
            def get_current_price(self, symbol: str) -> float | None:
                return 100.5

        provider = CustomPriceProvider()
        result = get_current_price_as_decimal(provider, "AAPL")

        assert result == Decimal("100.5")
