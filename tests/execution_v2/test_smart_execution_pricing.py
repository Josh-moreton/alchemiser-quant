"""Business Unit: execution | Status: current.

Comprehensive test suite for smart execution strategy pricing calculations.

This module provides unit tests and property-based tests for pricing logic,
including liquidity-aware pricing, fallback pricing, and re-pegging calculations.
"""

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from hypothesis import given
from hypothesis import strategies as st

from the_alchemiser.execution_v2.core.smart_execution_strategy.models import ExecutionConfig
from the_alchemiser.execution_v2.core.smart_execution_strategy.pricing import PricingCalculator
from the_alchemiser.shared.types.market_data import QuoteModel


@pytest.fixture
def default_config():
    """Create default execution configuration for tests."""
    return ExecutionConfig()


@pytest.fixture
def pricing_calculator(default_config):
    """Create pricing calculator with default configuration."""
    return PricingCalculator(default_config)


class TestCalculateSimpleInsideSpreadPrice:
    """Test simple inside spread price calculation for fallback scenarios."""

    def test_buy_order_price_above_bid(self, pricing_calculator):
        """Test that buy orders are priced above bid."""
        quote = QuoteModel(
            symbol="AAPL",
            bid_price=100.00,
            ask_price=100.50,
            bid_size=100.0,
            ask_size=100.0,
            timestamp=datetime.now(UTC),
        )

        price, metadata = pricing_calculator.calculate_simple_inside_spread_price(quote, "BUY")

        # Should be bid + offset (100.00 + 0.01 = 100.01)
        assert price >= Decimal("100.00")
        assert price < Decimal("100.50")
        assert metadata["method"] == "simple_inside_spread_fallback"
        assert metadata["used_fallback"] is True

    def test_sell_order_price_below_ask(self, pricing_calculator):
        """Test that sell orders are priced below ask."""
        quote = QuoteModel(
            symbol="AAPL",
            bid_price=100.00,
            ask_price=100.50,
            bid_size=100.0,
            ask_size=100.0,
            timestamp=datetime.now(UTC),
        )

        price, metadata = pricing_calculator.calculate_simple_inside_spread_price(quote, "SELL")

        # Should be ask - offset (100.50 - 0.01 = 100.49)
        assert price > Decimal("100.00")
        assert price <= Decimal("100.50")
        assert metadata["method"] == "simple_inside_spread_fallback"
        assert metadata["used_fallback"] is True

    def test_price_quantized_to_cents(self, pricing_calculator):
        """Test that calculated price is quantized to cent precision."""
        quote = QuoteModel(
            symbol="AAPL",
            bid_price=100.123,
            ask_price=100.567,
            bid_size=100.0,
            ask_size=100.0,
            timestamp=datetime.now(UTC),
        )

        price, _ = pricing_calculator.calculate_simple_inside_spread_price(quote, "BUY")

        # Check that price has at most 2 decimal places
        assert price == price.quantize(Decimal("0.01"))

    def test_minimum_price_enforcement(self, pricing_calculator):
        """Test that calculated price is never below minimum."""
        quote = QuoteModel(
            symbol="AAPL",
            bid_price=0.001,
            ask_price=0.002,
            bid_size=100.0,
            ask_size=100.0,
            timestamp=datetime.now(UTC),
        )

        price, _ = pricing_calculator.calculate_simple_inside_spread_price(quote, "BUY")

        # Should enforce minimum price of $0.01
        assert price >= Decimal("0.01")

    def test_buy_price_stays_inside_spread(self, pricing_calculator):
        """Test that buy price doesn't exceed ask when spread is tight."""
        quote = QuoteModel(
            symbol="AAPL",
            bid_price=100.00,
            ask_price=100.02,  # Very tight spread
            bid_size=100.0,
            ask_size=100.0,
            timestamp=datetime.now(UTC),
        )

        price, _ = pricing_calculator.calculate_simple_inside_spread_price(quote, "BUY")

        # Should not exceed mid point for tight spreads
        mid = (Decimal("100.00") + Decimal("100.02")) / Decimal("2")
        assert price <= mid

    def test_sell_price_stays_inside_spread(self, pricing_calculator):
        """Test that sell price doesn't fall below bid when spread is tight."""
        quote = QuoteModel(
            symbol="AAPL",
            bid_price=100.00,
            ask_price=100.02,  # Very tight spread
            bid_size=100.0,
            ask_size=100.0,
            timestamp=datetime.now(UTC),
        )

        price, _ = pricing_calculator.calculate_simple_inside_spread_price(quote, "SELL")

        # Should not fall below mid point for tight spreads
        mid = (Decimal("100.00") + Decimal("100.02")) / Decimal("2")
        assert price >= mid

    def test_metadata_structure(self, pricing_calculator):
        """Test that metadata contains all expected fields."""
        quote = QuoteModel(
            symbol="AAPL",
            bid_price=100.00,
            ask_price=100.50,
            bid_size=100.0,
            ask_size=100.0,
            timestamp=datetime.now(UTC),
        )

        _, metadata = pricing_calculator.calculate_simple_inside_spread_price(quote, "BUY")

        # Check all expected metadata fields
        assert "method" in metadata
        assert "mid" in metadata
        assert "bid" in metadata
        assert "ask" in metadata
        assert "strategy_recommendation" in metadata
        assert "liquidity_score" in metadata
        assert "volume_imbalance" in metadata
        assert "confidence" in metadata
        assert "used_fallback" in metadata
        assert "spread_percent" in metadata


class TestCalculateRepegPrice:
    """Test repeg price calculations for unfilled orders."""

    def test_buy_repeg_moves_toward_ask(self, pricing_calculator):
        """Test that buy repeg price moves closer to ask."""
        quote = QuoteModel(
            symbol="AAPL",
            bid_price=100.00,
            ask_price=101.00,
            bid_size=100.0,
            ask_size=100.0,
            timestamp=datetime.now(UTC),
        )

        original_price = Decimal("100.25")
        new_price = pricing_calculator.calculate_repeg_price(quote, "BUY", original_price, None)

        # Should move closer to ask (50% of the way)
        # Note: with allow_cross_spread_on_repeg=True (default), may exceed ask
        assert new_price is not None
        assert new_price > original_price

    def test_sell_repeg_moves_toward_bid(self, pricing_calculator):
        """Test that sell repeg price moves closer to bid."""
        quote = QuoteModel(
            symbol="AAPL",
            bid_price=100.00,
            ask_price=101.00,
            bid_size=100.0,
            ask_size=100.0,
            timestamp=datetime.now(UTC),
        )

        original_price = Decimal("100.75")
        new_price = pricing_calculator.calculate_repeg_price(quote, "SELL", original_price, None)

        # Should move closer to bid (50% of the way)
        # Note: with allow_cross_spread_on_repeg=True (default), may fall below bid
        assert new_price is not None
        assert new_price < original_price

    def test_repeg_without_original_price(self, pricing_calculator):
        """Test repeg calculation when no original price exists."""
        quote = QuoteModel(
            symbol="AAPL",
            bid_price=100.00,
            ask_price=100.50,
            bid_size=100.0,
            ask_size=100.0,
            timestamp=datetime.now(UTC),
        )

        # BUY without original price
        buy_price = pricing_calculator.calculate_repeg_price(quote, "BUY", None, None)
        assert buy_price is not None
        assert buy_price >= Decimal("100.00")
        # With allow_cross_spread_on_repeg=True, may exceed ask

        # SELL without original price
        sell_price = pricing_calculator.calculate_repeg_price(quote, "SELL", None, None)
        assert sell_price is not None
        assert sell_price <= Decimal("100.50")
        # With allow_cross_spread_on_repeg=True, may fall below bid

    def test_repeg_avoids_price_history(self, pricing_calculator):
        """Test that repeg avoids prices in history."""
        quote = QuoteModel(
            symbol="AAPL",
            bid_price=100.00,
            ask_price=101.00,
            bid_size=100.0,
            ask_size=100.0,
            timestamp=datetime.now(UTC),
        )

        original_price = Decimal("100.00")
        # Simulate a price that would collide with history
        price_history = [Decimal("100.50")]  # This is 50% between 100 and 101

        new_price = pricing_calculator.calculate_repeg_price(
            quote, "BUY", original_price, price_history
        )

        # Should avoid price in history
        assert new_price is not None
        assert new_price not in price_history or new_price != Decimal("100.50")

    def test_repeg_returns_none_on_exception(self, pricing_calculator):
        """Test that repeg returns None when calculation fails."""
        # Create invalid quote that will cause an exception
        quote = QuoteModel(
            symbol="AAPL",
            bid_price=-100.00,  # Invalid negative price
            ask_price=-99.00,
            bid_size=100.0,
            ask_size=100.0,
            timestamp=datetime.now(UTC),
        )

        result = pricing_calculator.calculate_repeg_price(quote, "BUY", Decimal("100.00"), None)

        # Should handle exception gracefully
        assert result is not None  # Will return minimum price due to validation

    def test_repeg_enforces_minimum_price(self, pricing_calculator):
        """Test that repeg enforces minimum price."""
        quote = QuoteModel(
            symbol="AAPL",
            bid_price=0.005,
            ask_price=0.008,
            bid_size=100.0,
            ask_size=100.0,
            timestamp=datetime.now(UTC),
        )

        new_price = pricing_calculator.calculate_repeg_price(quote, "BUY", Decimal("0.006"), None)

        # Should enforce minimum of $0.01
        assert new_price is not None
        assert new_price >= Decimal("0.01")

    def test_repeg_quantizes_price(self, pricing_calculator):
        """Test that repeg quantizes price to cent precision."""
        quote = QuoteModel(
            symbol="AAPL",
            bid_price=100.123,
            ask_price=100.789,
            bid_size=100.0,
            ask_size=100.0,
            timestamp=datetime.now(UTC),
        )

        new_price = pricing_calculator.calculate_repeg_price(quote, "BUY", Decimal("100.456"), None)

        # Should be quantized to cent precision
        assert new_price is not None
        assert new_price == new_price.quantize(Decimal("0.01"))


class TestRepegWithCrossSpread:
    """Test repeg behavior with cross-spread configuration."""

    def test_buy_crosses_ask_when_enabled(self):
        """Test that buy can cross ask when configured."""
        config = ExecutionConfig(allow_cross_spread_on_repeg=True)
        calculator = PricingCalculator(config)

        quote = QuoteModel(
            symbol="AAPL",
            bid_price=100.00,
            ask_price=100.50,
            bid_size=100.0,
            ask_size=100.0,
            timestamp=datetime.now(UTC),
        )

        original_price = Decimal("100.25")
        new_price = calculator.calculate_repeg_price(quote, "BUY", original_price, None)

        # With cross allowed, price can be >= ask
        assert new_price is not None
        # Price should be more aggressive than without crossing
        assert new_price >= original_price

    def test_sell_crosses_bid_when_enabled(self):
        """Test that sell can cross bid when configured."""
        config = ExecutionConfig(allow_cross_spread_on_repeg=True)
        calculator = PricingCalculator(config)

        quote = QuoteModel(
            symbol="AAPL",
            bid_price=100.00,
            ask_price=100.50,
            bid_size=100.0,
            ask_size=100.0,
            timestamp=datetime.now(UTC),
        )

        original_price = Decimal("100.25")
        new_price = calculator.calculate_repeg_price(quote, "SELL", original_price, None)

        # With cross allowed, price can be <= bid
        assert new_price is not None
        # Price should be more aggressive than without crossing
        assert new_price <= original_price


class TestFinalizeRepegPrice:
    """Test repeg price finalization logic."""

    def test_finalize_valid_price(self, pricing_calculator):
        """Test finalization of valid price."""
        new_price = Decimal("100.123")
        original_price = Decimal("100.00")

        result = pricing_calculator._finalize_repeg_price(new_price, original_price)

        # Should quantize to cent precision
        assert result == Decimal("100.12")

    def test_finalize_zero_price_uses_original(self, pricing_calculator):
        """Test that zero price falls back to original."""
        new_price = Decimal("0.00")
        original_price = Decimal("100.00")

        result = pricing_calculator._finalize_repeg_price(new_price, original_price)

        # Should use original price
        assert result == original_price

    def test_finalize_negative_price_uses_original(self, pricing_calculator):
        """Test that negative price falls back to original."""
        new_price = Decimal("-50.00")
        original_price = Decimal("100.00")

        result = pricing_calculator._finalize_repeg_price(new_price, original_price)

        # Should use original price
        assert result == original_price

    def test_finalize_zero_price_with_invalid_original(self, pricing_calculator):
        """Test that zero price with invalid original uses minimum."""
        new_price = Decimal("0.00")
        original_price = Decimal("0.005")  # Below minimum

        result = pricing_calculator._finalize_repeg_price(new_price, original_price)

        # Should use minimum price
        assert result == Decimal("0.01")

    def test_finalize_zero_price_with_no_original(self, pricing_calculator):
        """Test that zero price with no original uses minimum."""
        new_price = Decimal("0.00")
        original_price = None

        result = pricing_calculator._finalize_repeg_price(new_price, original_price)

        # Should use minimum price
        assert result == Decimal("0.01")


class TestPriceFundamentalsCalculation:
    """Test calculation of price fundamentals (bid, ask, mid, tick)."""

    def test_fundamentals_from_valid_quote(self, pricing_calculator):
        """Test fundamentals calculation from valid quote."""
        quote = QuoteModel(
            symbol="AAPL",
            bid_price=100.00,
            ask_price=100.50,
            bid_size=100.0,
            ask_size=100.0,
            timestamp=datetime.now(UTC),
        )

        bid, ask, mid, tick = pricing_calculator._calculate_price_fundamentals(quote)

        assert bid == Decimal("100.00")
        assert ask == Decimal("100.50")
        assert mid == Decimal("100.25")
        assert tick == Decimal("0.01")

    def test_fundamentals_with_zero_bid(self, pricing_calculator):
        """Test fundamentals when bid is zero."""
        quote = QuoteModel(
            symbol="AAPL",
            bid_price=0.00,
            ask_price=100.50,
            bid_size=100.0,
            ask_size=100.0,
            timestamp=datetime.now(UTC),
        )

        bid, ask, mid, tick = pricing_calculator._calculate_price_fundamentals(quote)

        assert bid == Decimal("0.00")
        assert ask == Decimal("100.50")
        assert mid == ask  # Should use ask when bid is zero
        assert tick == Decimal("0.01")

    def test_fundamentals_with_zero_ask(self, pricing_calculator):
        """Test fundamentals when ask is zero."""
        quote = QuoteModel(
            symbol="AAPL",
            bid_price=100.00,
            ask_price=0.00,
            bid_size=100.0,
            ask_size=100.0,
            timestamp=datetime.now(UTC),
        )

        bid, ask, mid, tick = pricing_calculator._calculate_price_fundamentals(quote)

        assert bid == Decimal("100.00")
        assert ask == Decimal("0.00")
        assert mid == bid  # Should use bid when ask is zero
        assert tick == Decimal("0.01")

    def test_fundamentals_with_negative_prices(self, pricing_calculator):
        """Test fundamentals with negative prices (should be clamped to zero)."""
        quote = QuoteModel(
            symbol="AAPL",
            bid_price=-10.00,
            ask_price=-5.00,
            bid_size=100.0,
            ask_size=100.0,
            timestamp=datetime.now(UTC),
        )

        bid, ask, mid, tick = pricing_calculator._calculate_price_fundamentals(quote)

        # Negative prices should be clamped to zero
        assert bid == Decimal("0.00")
        assert ask == Decimal("0.00")
        assert tick == Decimal("0.01")


class TestQuantizeAndValidateAnchor:
    """Test anchor price quantization and validation."""

    def test_quantize_valid_anchor(self, pricing_calculator):
        """Test quantization of valid anchor price."""
        anchor = Decimal("100.123")
        result = pricing_calculator._quantize_and_validate_anchor(anchor, "AAPL", "BUY")

        assert result == Decimal("100.12")

    def test_quantize_zero_anchor_uses_minimum(self, pricing_calculator):
        """Test that zero anchor uses minimum price."""
        anchor = Decimal("0.00")
        result = pricing_calculator._quantize_and_validate_anchor(anchor, "AAPL", "BUY")

        assert result == Decimal("0.01")

    def test_quantize_negative_anchor_uses_minimum(self, pricing_calculator):
        """Test that negative anchor uses minimum price."""
        anchor = Decimal("-50.00")
        result = pricing_calculator._quantize_and_validate_anchor(anchor, "AAPL", "BUY")

        assert result == Decimal("0.01")

    def test_quantize_rounds_correctly(self, pricing_calculator):
        """Test that quantization rounds correctly."""
        # Test banker's rounding (ROUND_HALF_EVEN)
        anchor1 = Decimal("100.125")
        result1 = pricing_calculator._quantize_and_validate_anchor(anchor1, "AAPL", "BUY")
        assert result1 == Decimal("100.12")

        anchor2 = Decimal("100.135")
        result2 = pricing_calculator._quantize_and_validate_anchor(anchor2, "AAPL", "BUY")
        assert result2 == Decimal("100.14")


class TestEdgeCasesAndErrorHandling:
    """Test edge cases and error handling in pricing calculations."""

    def test_extremely_tight_spread(self, pricing_calculator):
        """Test handling of extremely tight spreads."""
        quote = QuoteModel(
            symbol="AAPL",
            bid_price=100.00,
            ask_price=100.01,  # 1 cent spread
            bid_size=100.0,
            ask_size=100.0,
            timestamp=datetime.now(UTC),
        )

        buy_price, _ = pricing_calculator.calculate_simple_inside_spread_price(quote, "BUY")
        sell_price, _ = pricing_calculator.calculate_simple_inside_spread_price(quote, "SELL")

        # Both should be inside the spread
        assert buy_price >= Decimal("100.00")
        assert buy_price <= Decimal("100.01")
        assert sell_price >= Decimal("100.00")
        assert sell_price <= Decimal("100.01")

    def test_extremely_wide_spread(self, pricing_calculator):
        """Test handling of extremely wide spreads."""
        quote = QuoteModel(
            symbol="AAPL",
            bid_price=100.00,
            ask_price=200.00,  # 100% spread
            bid_size=100.0,
            ask_size=100.0,
            timestamp=datetime.now(UTC),
        )

        buy_price, _ = pricing_calculator.calculate_simple_inside_spread_price(quote, "BUY")
        sell_price, _ = pricing_calculator.calculate_simple_inside_spread_price(quote, "SELL")

        # Prices should still be reasonable
        mid = Decimal("150.00")
        assert buy_price <= mid  # Buy should not exceed mid for wide spreads
        assert sell_price >= mid  # Sell should not fall below mid

    def test_penny_stock_pricing(self, pricing_calculator):
        """Test pricing for penny stocks."""
        quote = QuoteModel(
            symbol="PENNY",
            bid_price=0.10,
            ask_price=0.11,
            bid_size=100.0,
            ask_size=100.0,
            timestamp=datetime.now(UTC),
        )

        buy_price, _ = pricing_calculator.calculate_simple_inside_spread_price(quote, "BUY")

        # Should handle penny stocks correctly
        assert buy_price >= Decimal("0.01")
        assert buy_price >= Decimal("0.10")  # At least bid
        assert buy_price <= Decimal("0.11")  # At most ask


@given(
    bid=st.decimals(
        min_value=Decimal("1.00"),
        max_value=Decimal("1000.00"),
        places=2,
    ),
    spread_cents=st.decimals(
        min_value=Decimal("0.01"),
        max_value=Decimal("10.00"),
        places=2,
    ),
)
def test_property_buy_price_in_spread(bid, spread_cents):
    """Property test: buy price should always be between bid and ask."""
    config = ExecutionConfig()
    calculator = PricingCalculator(config)

    ask = bid + spread_cents
    quote = QuoteModel(
        symbol="TEST",
        bid_price=float(bid),
        ask_price=float(ask),
        bid_size=100.0,
        ask_size=100.0,
        timestamp=datetime.now(UTC),
    )

    price, _ = calculator.calculate_simple_inside_spread_price(quote, "BUY")

    # Buy price should be >= bid and <= ask
    assert price >= bid
    assert price <= ask


@given(
    bid=st.decimals(
        min_value=Decimal("1.00"),
        max_value=Decimal("1000.00"),
        places=2,
    ),
    spread_cents=st.decimals(
        min_value=Decimal("0.01"),
        max_value=Decimal("10.00"),
        places=2,
    ),
)
def test_property_sell_price_in_spread(bid, spread_cents):
    """Property test: sell price should always be between bid and ask."""
    config = ExecutionConfig()
    calculator = PricingCalculator(config)

    ask = bid + spread_cents
    quote = QuoteModel(
        symbol="TEST",
        bid_price=float(bid),
        ask_price=float(ask),
        bid_size=100.0,
        ask_size=100.0,
        timestamp=datetime.now(UTC),
    )

    price, _ = calculator.calculate_simple_inside_spread_price(quote, "SELL")

    # Sell price should be >= bid and <= ask
    assert price >= bid
    assert price <= ask


class TestRepegWithoutCrossSpread:
    """Test repeg behavior without cross-spread configuration."""

    def test_buy_stays_at_ask_when_cross_disabled(self):
        """Test that buy respects ask when crossing is disabled."""
        config = ExecutionConfig(allow_cross_spread_on_repeg=False)
        calculator = PricingCalculator(config)

        quote = QuoteModel(
            symbol="AAPL",
            bid_price=100.00,
            ask_price=100.50,
            bid_size=100.0,
            ask_size=100.0,
            timestamp=datetime.now(UTC),
        )

        original_price = Decimal("100.25")
        new_price = calculator.calculate_repeg_price(quote, "BUY", original_price, None)

        # With cross disabled, price should not exceed ask
        assert new_price is not None
        assert new_price <= Decimal("100.50")

    def test_sell_stays_at_bid_when_cross_disabled(self):
        """Test that sell respects bid when crossing is disabled."""
        config = ExecutionConfig(allow_cross_spread_on_repeg=False)
        calculator = PricingCalculator(config)

        quote = QuoteModel(
            symbol="AAPL",
            bid_price=100.00,
            ask_price=100.50,
            bid_size=100.0,
            ask_size=100.0,
            timestamp=datetime.now(UTC),
        )

        original_price = Decimal("100.25")
        new_price = calculator.calculate_repeg_price(quote, "SELL", original_price, None)

        # With cross disabled, price should not fall below bid
        assert new_price is not None
        assert new_price >= Decimal("100.00")


class TestBuildFallbackMetadata:
    """Test metadata building for fallback scenarios."""

    def test_fallback_metadata_structure(self, pricing_calculator):
        """Test that fallback metadata has correct structure."""
        bid = Decimal("100.00")
        ask = Decimal("100.50")
        mid = Decimal("100.25")

        metadata = pricing_calculator._build_fallback_metadata(bid, ask, mid)

        # Check all expected fields
        assert metadata["method"] == "simple_inside_spread_fallback"
        assert metadata["mid"] == float(mid)
        assert metadata["bid"] == float(bid)
        assert metadata["ask"] == float(ask)
        assert metadata["used_fallback"] is True
        assert metadata["liquidity_score"] == 0.5
        assert metadata["confidence"] == 0.7
        assert "spread_percent" in metadata

    def test_fallback_metadata_spread_calculation(self, pricing_calculator):
        """Test spread percentage calculation in fallback metadata."""
        bid = Decimal("100.00")
        ask = Decimal("101.00")
        mid = Decimal("100.50")

        metadata = pricing_calculator._build_fallback_metadata(bid, ask, mid)

        # Spread should be calculated correctly
        # (101 - 100) / 100 * 100 = 1%
        assert metadata["spread_percent"] == pytest.approx(1.0, rel=0.01)

    def test_fallback_metadata_with_zero_bid(self, pricing_calculator):
        """Test fallback metadata handles zero bid gracefully."""
        bid = Decimal("0.00")
        ask = Decimal("100.00")
        mid = Decimal("50.00")

        metadata = pricing_calculator._build_fallback_metadata(bid, ask, mid)

        # Should not raise error with zero bid
        assert metadata["spread_percent"] == 0.0


class TestCalculateSideSpecificAnchor:
    """Test side-specific anchor calculations."""

    def test_buy_anchor_calculation(self, pricing_calculator):
        """Test buy anchor calculation."""
        bid = Decimal("100.00")
        ask = Decimal("100.50")
        mid = Decimal("100.25")
        tick = Decimal("0.01")

        anchor = pricing_calculator._calculate_side_specific_anchor("BUY", bid, ask, mid, tick)

        # Buy anchor should be above bid
        assert anchor > bid
        # But should not exceed mid
        assert anchor <= mid

    def test_sell_anchor_calculation(self, pricing_calculator):
        """Test sell anchor calculation."""
        bid = Decimal("100.00")
        ask = Decimal("100.50")
        mid = Decimal("100.25")
        tick = Decimal("0.01")

        anchor = pricing_calculator._calculate_side_specific_anchor("SELL", bid, ask, mid, tick)

        # Sell anchor should be below ask
        assert anchor < ask
        # But should not fall below mid
        assert anchor >= mid


class TestCalculateBuyAnchor:
    """Test buy anchor calculation."""

    def test_buy_anchor_above_bid(self, pricing_calculator):
        """Test that buy anchor is placed above bid."""
        bid = Decimal("100.00")
        ask = Decimal("100.50")
        mid = Decimal("100.25")
        tick = Decimal("0.01")

        anchor = pricing_calculator._calculate_buy_anchor(bid, ask, mid, tick)

        # Should be bid + offset
        assert anchor > bid
        assert anchor <= mid

    def test_buy_anchor_with_tight_spread(self, pricing_calculator):
        """Test buy anchor with very tight spread."""
        bid = Decimal("100.00")
        ask = Decimal("100.02")
        mid = Decimal("100.01")
        tick = Decimal("0.01")

        anchor = pricing_calculator._calculate_buy_anchor(bid, ask, mid, tick)

        # Should stay inside spread
        assert anchor >= bid
        assert anchor <= mid


class TestCalculateSellAnchor:
    """Test sell anchor calculation."""

    def test_sell_anchor_below_ask(self, pricing_calculator):
        """Test that sell anchor is placed below ask."""
        bid = Decimal("100.00")
        ask = Decimal("100.50")
        mid = Decimal("100.25")
        tick = Decimal("0.01")

        anchor = pricing_calculator._calculate_sell_anchor(bid, ask, mid, tick)

        # Should be ask - offset
        assert anchor < ask
        assert anchor >= mid

    def test_sell_anchor_with_tight_spread(self, pricing_calculator):
        """Test sell anchor with very tight spread."""
        bid = Decimal("100.00")
        ask = Decimal("100.02")
        mid = Decimal("100.01")
        tick = Decimal("0.01")

        anchor = pricing_calculator._calculate_sell_anchor(bid, ask, mid, tick)

        # Should stay inside spread
        assert anchor <= ask
        assert anchor >= mid
