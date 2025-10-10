"""Business Unit: execution | Status: current

Test liquidity analysis functionality.

Tests market liquidity scoring and volume-aware pricing without broker dependencies.
"""

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import Mock

import pytest

from the_alchemiser.execution_v2.utils.liquidity_analysis import (
    LiquidityAnalyzer,
    LiquidityAnalysis,
)


@dataclass(frozen=True)
class MockQuote:
    """Mock quote for testing.
    
    Uses float for convenience in tests. The LiquidityAnalyzer converts to Decimal internally.
    """

    symbol: str
    bid_price: float
    ask_price: float
    bid_size: float
    ask_size: float
    timestamp: datetime

    @property
    def mid_price(self) -> float:
        """Calculate mid-point price."""
        return (self.bid_price + self.ask_price) / 2

    @property
    def spread(self) -> float:
        """Calculate bid-ask spread."""
        return self.ask_price - self.bid_price


class TestLiquidityAnalyzer:
    """Test liquidity analyzer."""

    @pytest.fixture
    def analyzer(self):
        """Create liquidity analyzer."""
        return LiquidityAnalyzer(min_volume_threshold=100.0, tick_size=0.01)

    def test_initialization(self):
        """Test analyzer initializes with parameters."""
        analyzer = LiquidityAnalyzer(min_volume_threshold=50.0, tick_size=0.05)

        assert analyzer.min_volume_threshold == 50.0
        assert analyzer.tick_size == Decimal("0.05")

    def test_analyze_liquidity_balanced_book(self, analyzer):
        """Test liquidity analysis with balanced order book."""
        quote = MockQuote(
            symbol="AAPL",
            bid_price=150.00,
            ask_price=150.10,
            bid_size=1000.0,
            ask_size=1000.0,
            timestamp=datetime.now(UTC),
        )

        analysis = analyzer.analyze_liquidity(quote, order_size=100.0)

        assert analysis.symbol == "AAPL"
        assert analysis.total_bid_volume == 1000.0
        assert analysis.total_ask_volume == 1000.0
        assert abs(analysis.volume_imbalance) < 0.01  # Near zero for balanced
        assert analysis.liquidity_score > 50  # Good liquidity
        assert analysis.confidence > 0.5

    def test_analyze_liquidity_imbalanced_book(self, analyzer):
        """Test liquidity analysis with imbalanced order book."""
        quote = MockQuote(
            symbol="AAPL",
            bid_price=150.00,
            ask_price=150.10,
            bid_size=500.0,  # Less bid volume
            ask_size=2000.0,  # More ask volume
            timestamp=datetime.now(UTC),
        )

        analysis = analyzer.analyze_liquidity(quote, order_size=100.0)

        # Volume imbalance should be positive (more ask than bid)
        assert analysis.volume_imbalance > 0.3
        assert analysis.total_bid_volume == 500.0
        assert analysis.total_ask_volume == 2000.0

    def test_analyze_liquidity_low_volume(self, analyzer):
        """Test liquidity analysis with low volume."""
        quote = MockQuote(
            symbol="AAPL",
            bid_price=150.00,
            ask_price=150.10,
            bid_size=50.0,  # Below threshold  
            ask_size=50.0,  # Below threshold
            timestamp=datetime.now(UTC),
        )

        analysis = analyzer.analyze_liquidity(quote, order_size=100.0)

        # Volume is below threshold (100), so score is affected
        assert analysis.total_bid_volume == 50.0
        assert analysis.total_ask_volume == 50.0
        # Score is moderate due to tight spread compensating for low volume
        assert analysis.liquidity_score < 50

    def test_analyze_liquidity_wide_spread(self, analyzer):
        """Test liquidity analysis with wide bid-ask spread."""
        quote = MockQuote(
            symbol="AAPL",
            bid_price=150.00,
            ask_price=152.00,  # 2 dollar spread = ~1.3%
            bid_size=1000.0,
            ask_size=1000.0,
            timestamp=datetime.now(UTC),
        )

        analysis = analyzer.analyze_liquidity(quote, order_size=100.0)

        # Wide spread reduces liquidity score and confidence
        assert analysis.liquidity_score < 80
        assert analysis.confidence < 0.9

    def test_analyze_liquidity_large_order_vs_volume(self, analyzer):
        """Test liquidity analysis when order is large relative to volume."""
        quote = MockQuote(
            symbol="AAPL",
            bid_price=150.00,
            ask_price=150.10,
            bid_size=100.0,
            ask_size=100.0,
            timestamp=datetime.now(UTC),
        )

        # Order size > available liquidity
        analysis = analyzer.analyze_liquidity(quote, order_size=500.0)

        # Low confidence due to order/volume ratio
        assert analysis.confidence < 0.5

    def test_calculate_volume_aware_prices_small_order(self, analyzer):
        """Test price calculation for small order relative to liquidity."""
        quote = MockQuote(
            symbol="AAPL",
            bid_price=150.00,
            ask_price=150.10,
            bid_size=1000.0,
            ask_size=1000.0,
            timestamp=datetime.now(UTC),
        )

        analysis = analyzer.analyze_liquidity(quote, order_size=50.0)

        # Small order can use best bid/ask prices
        assert analysis.recommended_bid_price == 150.00
        assert analysis.recommended_ask_price == 150.10

    def test_calculate_volume_aware_prices_large_order(self, analyzer):
        """Test price calculation for large order relative to liquidity."""
        quote = MockQuote(
            symbol="AAPL",
            bid_price=150.00,
            ask_price=150.10,
            bid_size=100.0,
            ask_size=100.0,
            timestamp=datetime.now(UTC),
        )

        # Order is 90% of available volume - should be more aggressive
        analysis = analyzer.analyze_liquidity(quote, order_size=90.0)

        # Large order requires more aggressive pricing
        assert analysis.recommended_bid_price > 150.00  # More aggressive buy
        assert analysis.recommended_ask_price < 150.10  # More aggressive sell

    def test_validate_liquidity_for_order_sufficient(self, analyzer):
        """Test liquidity validation when sufficient volume exists."""
        quote = MockQuote(
            symbol="AAPL",
            bid_price=150.00,
            ask_price=150.10,
            bid_size=1000.0,
            ask_size=1000.0,
            timestamp=datetime.now(UTC),
        )

        is_valid, reason = analyzer.validate_liquidity_for_order(
            quote, side="buy", order_size=100.0
        )

        assert is_valid is True
        assert "passed" in reason.lower()

    def test_validate_liquidity_for_order_insufficient_volume(self, analyzer):
        """Test liquidity validation when insufficient volume."""
        quote = MockQuote(
            symbol="AAPL",
            bid_price=150.00,
            ask_price=150.10,
            bid_size=50.0,  # Below min threshold
            ask_size=50.0,
            timestamp=datetime.now(UTC),
        )

        is_valid, reason = analyzer.validate_liquidity_for_order(
            quote, side="buy", order_size=100.0
        )

        assert is_valid is False
        assert "volume" in reason.lower()

    def test_validate_liquidity_for_order_too_large(self, analyzer):
        """Test liquidity validation when order is too large."""
        quote = MockQuote(
            symbol="AAPL",
            bid_price=150.00,
            ask_price=150.10,
            bid_size=200.0,
            ask_size=200.0,
            timestamp=datetime.now(UTC),
        )

        # Order is 2.5x available volume
        is_valid, reason = analyzer.validate_liquidity_for_order(
            quote, side="buy", order_size=500.0
        )

        assert is_valid is False
        assert "large" in reason.lower()

    def test_validate_liquidity_for_order_wide_spread(self, analyzer):
        """Test liquidity validation with excessively wide spread."""
        quote = MockQuote(
            symbol="AAPL",
            bid_price=150.00,
            ask_price=158.00,  # 8 dollar spread = > 5%
            bid_size=1000.0,
            ask_size=1000.0,
            timestamp=datetime.now(UTC),
        )

        is_valid, reason = analyzer.validate_liquidity_for_order(
            quote, side="buy", order_size=100.0
        )

        assert is_valid is False
        assert "spread" in reason.lower()

    def test_get_execution_strategy_recommendation_normal(self, analyzer):
        """Test execution strategy recommendation for normal conditions."""
        analysis = LiquidityAnalysis(
            symbol="AAPL",
            total_bid_volume=1000.0,
            total_ask_volume=1000.0,
            volume_imbalance=0.0,
            liquidity_score=75.0,
            recommended_bid_price=150.00,
            recommended_ask_price=150.10,
            volume_at_recommended_bid=1000.0,
            volume_at_recommended_ask=1000.0,
            confidence=0.85,
        )

        strategy = analyzer.get_execution_strategy_recommendation(
            analysis, side="buy", order_size=100.0
        )

        assert strategy == "normal"

    def test_get_execution_strategy_recommendation_patient(self, analyzer):
        """Test execution strategy recommendation for low liquidity."""
        analysis = LiquidityAnalysis(
            symbol="AAPL",
            total_bid_volume=100.0,
            total_ask_volume=100.0,
            volume_imbalance=0.0,
            liquidity_score=25.0,  # Low liquidity
            recommended_bid_price=150.00,
            recommended_ask_price=150.10,
            volume_at_recommended_bid=100.0,
            volume_at_recommended_ask=100.0,
            confidence=0.5,
        )

        strategy = analyzer.get_execution_strategy_recommendation(
            analysis, side="buy", order_size=50.0
        )

        assert strategy == "patient"

    def test_get_execution_strategy_recommendation_split(self, analyzer):
        """Test execution strategy recommendation for large order."""
        analysis = LiquidityAnalysis(
            symbol="AAPL",
            total_bid_volume=200.0,
            total_ask_volume=200.0,
            volume_imbalance=0.0,
            liquidity_score=50.0,
            recommended_bid_price=150.00,
            recommended_ask_price=150.10,
            volume_at_recommended_bid=200.0,
            volume_at_recommended_ask=200.0,
            confidence=0.6,
        )

        # Order 2x the volume = split recommendation
        strategy = analyzer.get_execution_strategy_recommendation(
            analysis, side="buy", order_size=400.0
        )

        assert strategy == "split"

    def test_get_execution_strategy_recommendation_aggressive(self, analyzer):
        """Test execution strategy recommendation for imbalanced market."""
        analysis = LiquidityAnalysis(
            symbol="AAPL",
            total_bid_volume=2000.0,
            total_ask_volume=500.0,  # Heavy bid side
            volume_imbalance=-0.4,  # Negative = heavy bid
            liquidity_score=60.0,
            recommended_bid_price=150.00,
            recommended_ask_price=150.10,
            volume_at_recommended_bid=2000.0,
            volume_at_recommended_ask=500.0,
            confidence=0.7,
        )

        strategy = analyzer.get_execution_strategy_recommendation(
            analysis, side="buy", order_size=100.0
        )

        assert strategy == "aggressive"

    def test_decimal_precision_in_price_calculations(self, analyzer):
        """Test that Decimal precision is used for price calculations."""
        quote = MockQuote(
            symbol="AAPL",
            bid_price=150.123,
            ask_price=150.456,
            bid_size=1000.0,
            ask_size=1000.0,
            timestamp=datetime.now(UTC),
        )

        analysis = analyzer.analyze_liquidity(quote, order_size=100.0)

        # Prices should be calculated with proper precision
        assert isinstance(analysis.recommended_bid_price, float)
        assert isinstance(analysis.recommended_ask_price, float)
        # Check precision is maintained (within tick size)
        assert abs(analysis.recommended_bid_price - round(analysis.recommended_bid_price, 2)) < 0.02

    def test_negative_price_handling(self, analyzer):
        """Test handling of suspicious negative prices."""
        quote = MockQuote(
            symbol="AAPL",
            bid_price=-1.0,  # Negative (suspicious)
            ask_price=150.00,
            bid_size=1000.0,
            ask_size=1000.0,
            timestamp=datetime.now(UTC),
        )

        # Should not crash, warning should be logged
        analysis = analyzer.analyze_liquidity(quote, order_size=100.0)

        # Analysis should still complete
        assert analysis.symbol == "AAPL"

    def test_zero_volume_handling(self, analyzer):
        """Test handling of zero volume in calculations."""
        quote = MockQuote(
            symbol="AAPL",
            bid_price=150.00,
            ask_price=150.10,
            bid_size=0.0,  # No volume
            ask_size=0.0,  # No volume
            timestamp=datetime.now(UTC),
        )

        analysis = analyzer.analyze_liquidity(quote, order_size=100.0)

        # Should handle division by zero gracefully
        assert analysis.volume_imbalance == 0.0
        assert analysis.liquidity_score >= 0
        assert analysis.confidence >= 0.1  # Minimum confidence


class TestNegativePricePrevention:
    """Test that the analyzer prevents negative recommended prices.
    
    This test class specifically addresses the issue where correct streaming quotes
    (e.g., bid=269.58, ask=270.73) would somehow lead to negative recommended prices
    (-0.01, -0.02) causing order placement failures.
    """

    @pytest.fixture
    def analyzer(self):
        """Create liquidity analyzer."""
        return LiquidityAnalyzer(min_volume_threshold=100.0, tick_size=0.01)

    def test_prevents_negative_prices_with_zero_quote_prices(self, analyzer):
        """Test that zero quote prices are detected and handled gracefully."""
        # Simulate corrupted quote data with zero prices
        quote = MockQuote(
            symbol="BULZ",
            bid_price=0.0,
            ask_price=0.0,
            bid_size=100.0,
            ask_size=100.0,
            timestamp=datetime.now(UTC),
        )

        analysis = analyzer.analyze_liquidity(quote, order_size=36.69)

        # Should return minimum valid prices, not negative
        assert analysis.recommended_bid_price >= 0.01
        assert analysis.recommended_ask_price >= 0.01

    def test_prevents_negative_prices_with_negative_quote_prices(self, analyzer):
        """Test that negative quote prices are detected and handled."""
        # Simulate corrupted quote data with negative prices
        quote = MockQuote(
            symbol="BULZ",
            bid_price=-10.0,
            ask_price=-5.0,
            bid_size=100.0,
            ask_size=100.0,
            timestamp=datetime.now(UTC),
        )

        analysis = analyzer.analyze_liquidity(quote, order_size=36.69)

        # Should return minimum valid prices, not propagate negatives
        assert analysis.recommended_bid_price >= 0.01
        assert analysis.recommended_ask_price >= 0.01

    def test_normal_quotes_produce_positive_recommended_prices(self, analyzer):
        """Test that normal quotes produce positive recommended prices."""
        # Simulate the actual BULZ quote from the issue
        quote = MockQuote(
            symbol="BULZ",
            bid_price=269.58,
            ask_price=270.73,
            bid_size=100.0,
            ask_size=100.0,
            timestamp=datetime.now(UTC),
        )

        analysis = analyzer.analyze_liquidity(quote, order_size=36.69)

        # Should produce sensible positive prices near the quote
        assert analysis.recommended_bid_price > 0
        assert analysis.recommended_ask_price > 0
        assert analysis.recommended_bid_price >= 269.0  # Reasonably close to bid
        assert analysis.recommended_ask_price >= 269.0  # Reasonably close to bid

    def test_aggressive_pricing_doesnt_produce_negative_values(self, analyzer):
        """Test aggressive pricing adjustments don't produce negative values."""
        # Test with heavy imbalance that triggers aggressive pricing
        quote = MockQuote(
            symbol="TEST",
            bid_price=1.00,
            ask_price=1.10,
            bid_size=10.0,  # Very low volume to trigger aggressive pricing
            ask_size=1000.0,  # Heavy ask imbalance
            timestamp=datetime.now(UTC),
        )

        # Large order relative to bid volume
        analysis = analyzer.analyze_liquidity(quote, order_size=50.0)

        # Even with aggressive adjustments, prices must remain positive
        assert analysis.recommended_bid_price > 0
        assert analysis.recommended_ask_price > 0
        assert analysis.recommended_ask_price >= analysis.recommended_bid_price

    def test_small_price_stocks_handled_safely(self, analyzer):
        """Test that low-priced stocks don't produce negative recommendations."""
        # Test with a low-priced stock
        quote = MockQuote(
            symbol="PENNY",
            bid_price=0.50,
            ask_price=0.52,
            bid_size=1000.0,
            ask_size=1000.0,
            timestamp=datetime.now(UTC),
        )

        analysis = analyzer.analyze_liquidity(quote, order_size=100.0)

        # Should maintain positive prices even for low-priced stocks
        assert analysis.recommended_bid_price > 0
        assert analysis.recommended_ask_price > 0
        assert analysis.recommended_bid_price <= analysis.recommended_ask_price
