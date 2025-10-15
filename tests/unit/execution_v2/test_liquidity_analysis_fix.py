"""Unit tests for crossed market pricing fix in liquidity analyzer.

Business Unit: execution_v2 | Status: current

Tests verify the fix for GitHub issue where BUY orders were generating
limit prices ABOVE the ask (crossing the spread) due to incorrect volume
ratio logic.
"""

from datetime import datetime, UTC
from decimal import Decimal

import pytest
from hypothesis import given, strategies as st

from the_alchemiser.execution_v2.utils.liquidity_analysis import LiquidityAnalyzer
from the_alchemiser.shared.types.market_data import QuoteModel


class TestCrossedMarketFix:
    """Test suite for crossed market pricing bug fix."""

    @pytest.fixture
    def analyzer(self) -> LiquidityAnalyzer:
        """Create analyzer with standard settings."""
        return LiquidityAnalyzer(min_volume_threshold=100.0, tick_size=0.01)

    def test_soxs_reproduction_case(self, analyzer: LiquidityAnalyzer) -> None:
        """Reproduce exact SOXS case that triggered crossed market warning.

        Original failure:
        - Quote: bid=4.14, ask=4.15, bid_size=37, ask_size=70
        - Order: BUY 4478.287093 shares
        - Result: recommended_bid=4.16, recommended_ask=4.15 (CROSSED!)

        Expected fix:
        - BUY limit should be ≤ 4.15 (at or below ask)
        - No crossed state warnings
        """
        from datetime import datetime, UTC

        quote = QuoteModel(
            symbol="SOXS",
            bid_price=Decimal("4.14"),
            ask_price=Decimal("4.15"),
            bid_size=Decimal("37.0"),
            ask_size=Decimal("70.0"),
            timestamp=datetime.now(UTC),
        )

        order_size = 4478.287093

        # Analyze for BUY order
        analysis = analyzer.analyze_liquidity(quote, order_size, side="BUY")

        # CRITICAL: BUY limit must NOT cross above ask
        assert analysis.recommended_bid_price <= 4.15, (
            f"BUY limit {analysis.recommended_bid_price} crosses above ask {quote.ask_price}. "
            f"This recreates the original bug!"
        )

        # BUY limit should be AT ask (large order needs certainty)
        assert analysis.recommended_bid_price == 4.15, (
            f"Large BUY order should price at ask for fill certainty. "
            f"Got {analysis.recommended_bid_price}, expected 4.15"
        )

        # No self-cross: buy < sell always
        assert analysis.recommended_bid_price < analysis.recommended_ask_price, (
            f"Self-crossed: buy={analysis.recommended_bid_price} >= "
            f"sell={analysis.recommended_ask_price}"
        )

    def test_buy_order_never_crosses_ask(self, analyzer: LiquidityAnalyzer) -> None:
        """BUY limit price must never exceed ask price."""
        from datetime import datetime, UTC

        quote = QuoteModel(
            symbol="TEST",
            bid_price=Decimal("100.00"),
            ask_price=Decimal("100.05"),
            bid_size=Decimal("100.0"),
            ask_size=Decimal("50.0"),
            timestamp=datetime.now(UTC),
        )

        # Test various order sizes
        for order_size in [10.0, 50.0, 100.0, 500.0, 5000.0]:
            analysis = analyzer.analyze_liquidity(quote, order_size, side="BUY")

            assert analysis.recommended_bid_price <= quote.ask_price, (
                f"BUY limit {analysis.recommended_bid_price} for order_size={order_size} "
                f"crosses above ask {quote.ask_price}"
            )

    def test_sell_order_never_crosses_bid(self, analyzer: LiquidityAnalyzer) -> None:
        """SELL limit price must never go below bid price."""
        quote = QuoteModel(
            symbol="TEST",
            bid_price=Decimal("100.00"),
            ask_price=Decimal("100.05"),
            bid_size=Decimal("50.0"),
            ask_size=Decimal("100.0"),
            timestamp=datetime.now(UTC),
        )

        # Test various order sizes
        for order_size in [10.0, 50.0, 100.0, 500.0, 5000.0]:
            analysis = analyzer.analyze_liquidity(quote, order_size, side="SELL")

            assert analysis.recommended_ask_price >= float(quote.bid_price), (
                f"SELL limit {analysis.recommended_ask_price} for order_size={order_size} "
                f"crosses below bid {quote.bid_price}"
            )

    def test_no_self_cross_invariant(self, analyzer: LiquidityAnalyzer) -> None:
        """Buy limit must respect external quote and not cross ask; sell limit must not cross bid.

        IMPORTANT: This tests that each side independently respects the external market quote.
        It does NOT require buy_limit < sell_limit across separate trade scenarios,
        since those are independent pricing decisions for opposite sides of the market.
        """
        quote = QuoteModel(
            symbol="TEST",
            bid_price=Decimal("50.00"),
            ask_price=Decimal("50.10"),
            bid_size=Decimal("200.0"),
            ask_size=Decimal("200.0"),
            timestamp=datetime.now(UTC),
        )

        # Test with side-specific calls (production path)
        buy_analysis = analyzer.analyze_liquidity(quote, 300.0, side="BUY")
        sell_analysis = analyzer.analyze_liquidity(quote, 300.0, side="SELL")

        # Critical invariants: respect external market bounds
        assert buy_analysis.recommended_bid_price <= float(quote.ask_price), (
            f"BUY limit {buy_analysis.recommended_bid_price} crosses above ask {quote.ask_price}"
        )
        assert sell_analysis.recommended_ask_price >= float(quote.bid_price), (
            f"SELL limit {sell_analysis.recommended_ask_price} crosses below bid {quote.bid_price}"
        )

        # Test legacy mode (computing both sides)
        legacy_analysis = analyzer.analyze_liquidity(quote, 300.0, side=None)

        # Legacy mode MUST maintain the self-cross invariant since both are computed together
        assert legacy_analysis.recommended_bid_price < legacy_analysis.recommended_ask_price, (
            f"Legacy mode self-cross: buy={legacy_analysis.recommended_bid_price} >= "
            f"sell={legacy_analysis.recommended_ask_price}"
        )

    def test_tick_quantization(self, analyzer: LiquidityAnalyzer) -> None:
        """Prices must be quantized to tick_size (no floating point errors)."""
        quote = QuoteModel(
            symbol="TEST",
            bid_price=Decimal("10.123"),  # Not a clean tick multiple
            ask_price=Decimal("10.127"),
            bid_size=Decimal("100.0"),
            ask_size=Decimal("100.0"),
            timestamp=datetime.now(UTC),
        )

        analysis = analyzer.analyze_liquidity(quote, 50.0, side="BUY")

        # Convert to Decimal for precise comparison
        bid_decimal = Decimal(str(analysis.recommended_bid_price))
        tick_decimal = Decimal("0.01")

        # Check quantization: price should be exact multiple of tick_size
        remainder = bid_decimal % tick_decimal
        assert remainder == 0, (
            f"Price {analysis.recommended_bid_price} not properly quantized to tick_size=0.01. "
            f"Remainder: {remainder}"
        )

    def test_large_buy_order_pricing(self, analyzer: LiquidityAnalyzer) -> None:
        """Large BUY orders (>80% of ask liquidity) should price AT ask for fill certainty."""
        quote = QuoteModel(
            symbol="TEST",
            bid_price=Decimal("25.00"),
            ask_price=Decimal("25.05"),
            bid_size=Decimal("1000.0"),
            ask_size=Decimal("100.0"),  # Small ask liquidity
            timestamp=datetime.now(UTC),
        )

        # Order > 80% of ask_size
        large_order = 85.0
        analysis = analyzer.analyze_liquidity(quote, large_order, side="BUY")

        # Should price AT ask (not above, not below)
        assert analysis.recommended_bid_price == float(quote.ask_price), (
            f"Large BUY order should price at ask. "
            f"Got {analysis.recommended_bid_price}, expected {quote.ask_price}"
        )

    def test_large_sell_order_pricing(self, analyzer: LiquidityAnalyzer) -> None:
        """Large SELL orders (>80% of bid liquidity) should price AT bid for fill certainty."""
        quote = QuoteModel(
            symbol="TEST",
            bid_price=Decimal("25.00"),
            ask_price=Decimal("25.05"),
            bid_size=Decimal("100.0"),  # Small bid liquidity
            ask_size=Decimal("1000.0"),
            timestamp=datetime.now(UTC),
        )

        # Order > 80% of bid_size
        large_order = 85.0
        analysis = analyzer.analyze_liquidity(quote, large_order, side="SELL")

        # Should price AT bid (not below, not above)
        assert analysis.recommended_ask_price == float(quote.bid_price), (
            f"Large SELL order should price at bid. "
            f"Got {analysis.recommended_ask_price}, expected {quote.bid_price}"
        )

    def test_small_order_improvement_attempt(self, analyzer: LiquidityAnalyzer) -> None:
        """Small orders (<30% of liquidity) can attempt price improvement."""
        quote = QuoteModel(
            symbol="TEST",
            bid_price=Decimal("10.00"),
            ask_price=Decimal("10.10"),
            bid_size=Decimal("1000.0"),
            ask_size=Decimal("1000.0"),
            timestamp=datetime.now(UTC),
        )

        # Small BUY order (< 30% of ask_size)
        small_buy = 250.0
        buy_analysis = analyzer.analyze_liquidity(quote, small_buy, side="BUY")

        # Should try to improve (ask - tick), but still <= ask
        expected_buy = float(quote.ask_price) - 0.01  # One tick improvement
        assert buy_analysis.recommended_bid_price == expected_buy
        assert buy_analysis.recommended_bid_price < float(quote.ask_price)

        # Small SELL order (< 30% of bid_size)
        small_sell = 250.0
        sell_analysis = analyzer.analyze_liquidity(quote, small_sell, side="SELL")

        # Should try to improve (bid + tick), but still >= bid
        expected_sell = float(quote.bid_price) + 0.01  # One tick improvement
        assert sell_analysis.recommended_ask_price == expected_sell
        assert sell_analysis.recommended_ask_price > float(quote.bid_price)


class TestPropertyBasedInvariants:
    """Property-based tests using Hypothesis for comprehensive coverage."""

    @given(
        bid_price=st.floats(min_value=0.01, max_value=1000.0),
        spread_ticks=st.integers(min_value=1, max_value=100),
        bid_size=st.floats(min_value=1.0, max_value=10000.0),
        ask_size=st.floats(min_value=1.0, max_value=10000.0),
        order_size=st.floats(min_value=1.0, max_value=50000.0),
    )
    def test_no_cross_property(
        self,
        bid_price: float,
        spread_ticks: int,
        bid_size: float,
        ask_size: float,
        order_size: float,
    ) -> None:
        """Property: BUY limit <= ask, SELL limit >= bid for all valid inputs.

        This verifies that limit prices respect the external market quote bounds,
        which is the fundamental no-cross invariant. We do NOT require buy < sell
        across independent pricing calls, since those represent different trades.
        """
        # Construct valid quote with Decimal types
        tick_size = 0.01
        ask_price = bid_price + (spread_ticks * tick_size)

        quote = QuoteModel(
            symbol="TEST",
            bid_price=Decimal(str(round(bid_price, 2))),
            ask_price=Decimal(str(round(ask_price, 2))),
            bid_size=Decimal(str(bid_size)),
            ask_size=Decimal(str(ask_size)),
            timestamp=datetime.now(UTC),
        )

        analyzer = LiquidityAnalyzer(tick_size=tick_size)

        # Test BUY: must not cross above external ask
        buy_analysis = analyzer.analyze_liquidity(quote, order_size, side="BUY")
        assert buy_analysis.recommended_bid_price <= float(quote.ask_price), (
            f"BUY limit {buy_analysis.recommended_bid_price} crossed above ask {quote.ask_price}"
        )

        # Test SELL: must not cross below external bid
        sell_analysis = analyzer.analyze_liquidity(quote, order_size, side="SELL")
        assert sell_analysis.recommended_ask_price >= float(quote.bid_price), (
            f"SELL limit {sell_analysis.recommended_ask_price} crossed below bid {quote.bid_price}"
        )

    @given(
        bid_price=st.floats(min_value=0.01, max_value=1000.0),
        spread_ticks=st.integers(min_value=1, max_value=100),
        bid_size=st.floats(min_value=1.0, max_value=10000.0),
        ask_size=st.floats(min_value=1.0, max_value=10000.0),
        order_size=st.floats(min_value=1.0, max_value=50000.0),
    )
    def test_quantization_property(
        self,
        bid_price: float,
        spread_ticks: int,
        bid_size: float,
        ask_size: float,
        order_size: float,
    ) -> None:
        """Property: All prices must be exact multiples of tick_size."""
        tick_size = 0.01
        ask_price = bid_price + (spread_ticks * tick_size)

        quote = QuoteModel(
            symbol="TEST",
            bid_price=Decimal(str(round(bid_price, 2))),
            ask_price=Decimal(str(round(ask_price, 2))),
            bid_size=Decimal(str(bid_size)),
            ask_size=Decimal(str(ask_size)),
            timestamp=datetime.now(UTC),
        )

        analyzer = LiquidityAnalyzer(tick_size=tick_size)
        analysis = analyzer.analyze_liquidity(quote, order_size, side="BUY")

        # Check quantization
        bid_decimal = Decimal(str(analysis.recommended_bid_price))
        tick_decimal = Decimal(str(tick_size))
        assert (bid_decimal % tick_decimal) == 0, "Price not properly quantized"
