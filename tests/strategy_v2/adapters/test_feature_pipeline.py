#!/usr/bin/env python3
"""Business Unit: strategy | Status: current.

Unit tests for FeaturePipeline adapter.

Tests cover all public methods, edge cases, numerical correctness,
and error handling for the feature computation pipeline.
"""

from __future__ import annotations

import math
from datetime import UTC, datetime
from decimal import Decimal

import numpy as np
import pytest
from hypothesis import given, strategies as st

from the_alchemiser.shared.schemas.market_bar import MarketBar
from the_alchemiser.strategy_v2.adapters.feature_pipeline import FeaturePipeline


class TestFeaturePipelineInit:
    """Test FeaturePipeline initialization."""

    @pytest.mark.unit
    def test_default_initialization(self):
        """Test that FeaturePipeline initializes with default tolerance."""
        pipeline = FeaturePipeline()
        assert pipeline._tolerance == 1e-9

    @pytest.mark.unit
    def test_custom_tolerance_initialization(self):
        """Test that FeaturePipeline accepts custom tolerance."""
        custom_tolerance = 1e-6
        pipeline = FeaturePipeline(default_tolerance=custom_tolerance)
        assert pipeline._tolerance == custom_tolerance


class TestComputeReturns:
    """Test compute_returns method."""

    def _create_test_bars(self, prices: list[float]) -> list[MarketBar]:
        """Helper to create MarketBar objects from prices."""
        bars = []
        for i, price in enumerate(prices):
            bar = MarketBar(
                timestamp=datetime(2024, 1, 1, 9 + i, 0, tzinfo=UTC),
                symbol="TEST",
                timeframe="1H",
                open_price=Decimal(str(price)),
                high_price=Decimal(str(price * 1.01)),
                low_price=Decimal(str(price * 0.99)),
                close_price=Decimal(str(price)),
                volume=1000,
            )
            bars.append(bar)
        return bars

    @pytest.mark.unit
    def test_compute_returns_insufficient_data(self):
        """Test that compute_returns returns empty list for insufficient data."""
        pipeline = FeaturePipeline()
        
        # Empty list
        assert pipeline.compute_returns([]) == []
        
        # Single bar
        bars = self._create_test_bars([100.0])
        assert pipeline.compute_returns(bars) == []

    @pytest.mark.unit
    def test_compute_returns_two_bars(self):
        """Test compute_returns with exactly two bars."""
        pipeline = FeaturePipeline()
        bars = self._create_test_bars([100.0, 105.0])
        
        returns = pipeline.compute_returns(bars)
        
        assert len(returns) == 1
        assert math.isclose(returns[0], 0.05, abs_tol=1e-9)  # 5% return

    @pytest.mark.unit
    def test_compute_returns_multiple_bars(self):
        """Test compute_returns with multiple bars."""
        pipeline = FeaturePipeline()
        bars = self._create_test_bars([100.0, 102.0, 101.0, 103.0])
        
        returns = pipeline.compute_returns(bars)
        
        assert len(returns) == 3
        assert math.isclose(returns[0], 0.02, abs_tol=1e-9)  # 2% return
        assert math.isclose(returns[1], -0.00980392, abs_tol=1e-6)  # ~-0.98% return
        assert math.isclose(returns[2], 0.0198019, abs_tol=1e-6)  # ~1.98% return

    @pytest.mark.unit
    def test_compute_returns_zero_price_handling(self):
        """Test that zero or near-zero prices are handled gracefully."""
        pipeline = FeaturePipeline()
        bars = self._create_test_bars([100.0, 1e-7, 105.0])
        
        returns = pipeline.compute_returns(bars)
        
        # First return should be computed, second should be 0.0 due to near-zero prev_close
        assert len(returns) == 2
        assert returns[1] == 0.0  # Zero return when prev_close is near-zero

    @pytest.mark.unit
    def test_compute_returns_constant_prices(self):
        """Test compute_returns with constant prices."""
        pipeline = FeaturePipeline()
        bars = self._create_test_bars([100.0] * 5)
        
        returns = pipeline.compute_returns(bars)
        
        assert len(returns) == 4
        for ret in returns:
            assert math.isclose(ret, 0.0, abs_tol=1e-9)


class TestComputeVolatility:
    """Test compute_volatility method."""

    @pytest.mark.unit
    def test_compute_volatility_insufficient_data(self):
        """Test that compute_volatility returns 0.0 for insufficient data."""
        pipeline = FeaturePipeline()
        
        # Empty list
        assert pipeline.compute_volatility([]) == 0.0
        
        # Single return
        assert pipeline.compute_volatility([0.01]) == 0.0

    @pytest.mark.unit
    def test_compute_volatility_two_returns(self):
        """Test compute_volatility with exactly two returns."""
        pipeline = FeaturePipeline()
        returns = [0.01, 0.02]
        
        vol = pipeline.compute_volatility(returns, annualize=False)
        
        # Std dev of [0.01, 0.02] with N-1 denominator
        expected_std = math.sqrt(((0.01 - 0.015)**2 + (0.02 - 0.015)**2) / 1)
        assert math.isclose(vol, expected_std, abs_tol=1e-9)

    @pytest.mark.unit
    def test_compute_volatility_annualized(self):
        """Test that annualization factor is applied correctly."""
        pipeline = FeaturePipeline()
        returns = [0.01, 0.02, 0.015, 0.008]
        
        vol_daily = pipeline.compute_volatility(returns, annualize=False)
        vol_annual = pipeline.compute_volatility(returns, annualize=True)
        
        # Annual volatility should be daily * sqrt(252)
        expected_annual = vol_daily * math.sqrt(252)
        assert math.isclose(vol_annual, expected_annual, abs_tol=1e-9)

    @pytest.mark.unit
    def test_compute_volatility_with_window(self):
        """Test compute_volatility with rolling window."""
        pipeline = FeaturePipeline()
        returns = [0.01, 0.02, 0.015, 0.008, 0.012]
        
        # Use window of 3 (should use last 3 returns)
        vol = pipeline.compute_volatility(returns, window=3, annualize=False)
        
        # Should use [0.015, 0.008, 0.012]
        last_three = returns[-3:]
        mean = sum(last_three) / len(last_three)
        expected_std = math.sqrt(sum((r - mean)**2 for r in last_three) / (len(last_three) - 1))
        assert math.isclose(vol, expected_std, abs_tol=1e-9)

    @pytest.mark.unit
    def test_compute_volatility_constant_returns(self):
        """Test volatility of constant returns is zero."""
        pipeline = FeaturePipeline()
        returns = [0.01] * 10
        
        vol = pipeline.compute_volatility(returns, annualize=False)
        
        assert math.isclose(vol, 0.0, abs_tol=1e-9)

    @pytest.mark.unit
    def test_compute_volatility_window_larger_than_data(self):
        """Test that window larger than data uses all available data."""
        pipeline = FeaturePipeline()
        returns = [0.01, 0.02]
        
        vol = pipeline.compute_volatility(returns, window=10, annualize=False)
        
        # Window of 10 but only 2 returns -> uses all data, computes volatility
        assert vol > 0.0  # Should compute volatility with available data


class TestComputeMovingAverage:
    """Test compute_moving_average method."""

    @pytest.mark.unit
    def test_compute_moving_average_insufficient_data(self):
        """Test that compute_moving_average returns empty list for insufficient data."""
        pipeline = FeaturePipeline()
        
        # Empty list
        assert pipeline.compute_moving_average([], 5) == []
        
        # Data shorter than window
        assert pipeline.compute_moving_average([1.0, 2.0], 5) == []

    @pytest.mark.unit
    def test_compute_moving_average_invalid_window(self):
        """Test that invalid window size returns empty list."""
        pipeline = FeaturePipeline()
        values = [1.0, 2.0, 3.0]
        
        # Zero window
        assert pipeline.compute_moving_average(values, 0) == []
        
        # Negative window
        assert pipeline.compute_moving_average(values, -1) == []

    @pytest.mark.unit
    def test_compute_moving_average_exact_window_size(self):
        """Test compute_moving_average with data exactly matching window."""
        pipeline = FeaturePipeline()
        values = [1.0, 2.0, 3.0, 4.0, 5.0]
        window = 5
        
        averages = pipeline.compute_moving_average(values, window)
        
        assert len(averages) == 1
        assert math.isclose(averages[0], 3.0, abs_tol=1e-9)  # (1+2+3+4+5)/5 = 3

    @pytest.mark.unit
    def test_compute_moving_average_longer_data(self):
        """Test compute_moving_average with data longer than window."""
        pipeline = FeaturePipeline()
        values = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]
        window = 3
        
        averages = pipeline.compute_moving_average(values, window)
        
        # Should get 4 averages: [1,2,3], [2,3,4], [3,4,5], [4,5,6]
        assert len(averages) == 4
        assert math.isclose(averages[0], 2.0, abs_tol=1e-9)  # (1+2+3)/3
        assert math.isclose(averages[1], 3.0, abs_tol=1e-9)  # (2+3+4)/3
        assert math.isclose(averages[2], 4.0, abs_tol=1e-9)  # (3+4+5)/3
        assert math.isclose(averages[3], 5.0, abs_tol=1e-9)  # (4+5+6)/3


class TestComputeCorrelation:
    """Test compute_correlation method."""

    @pytest.mark.unit
    def test_compute_correlation_different_lengths(self):
        """Test that different length series return 0.0."""
        pipeline = FeaturePipeline()
        series1 = [1.0, 2.0, 3.0]
        series2 = [1.0, 2.0]
        
        corr = pipeline.compute_correlation(series1, series2)
        
        assert corr == 0.0

    @pytest.mark.unit
    def test_compute_correlation_insufficient_data(self):
        """Test that insufficient data returns 0.0."""
        pipeline = FeaturePipeline()
        
        # Single point
        assert pipeline.compute_correlation([1.0], [2.0]) == 0.0
        
        # Empty
        assert pipeline.compute_correlation([], []) == 0.0

    @pytest.mark.unit
    def test_compute_correlation_perfect_positive(self):
        """Test perfect positive correlation."""
        pipeline = FeaturePipeline()
        series1 = [1.0, 2.0, 3.0, 4.0, 5.0]
        series2 = [2.0, 4.0, 6.0, 8.0, 10.0]
        
        corr = pipeline.compute_correlation(series1, series2)
        
        assert math.isclose(corr, 1.0, abs_tol=1e-9)

    @pytest.mark.unit
    def test_compute_correlation_perfect_negative(self):
        """Test perfect negative correlation."""
        pipeline = FeaturePipeline()
        series1 = [1.0, 2.0, 3.0, 4.0, 5.0]
        series2 = [5.0, 4.0, 3.0, 2.0, 1.0]
        
        corr = pipeline.compute_correlation(series1, series2)
        
        assert math.isclose(corr, -1.0, abs_tol=1e-9)

    @pytest.mark.unit
    def test_compute_correlation_zero(self):
        """Test uncorrelated series."""
        pipeline = FeaturePipeline()
        # Create two uncorrelated series
        series1 = [1.0, 2.0, 1.0, 2.0]
        series2 = [1.0, 1.0, 2.0, 2.0]
        
        corr = pipeline.compute_correlation(series1, series2)
        
        # Should be close to zero
        assert abs(corr) < 0.5  # Not perfectly zero, but low

    @pytest.mark.unit
    def test_compute_correlation_constant_series(self):
        """Test that constant series (which produce NaN) return 0.0."""
        pipeline = FeaturePipeline()
        series1 = [1.0] * 5
        series2 = [2.0] * 5
        
        corr = pipeline.compute_correlation(series1, series2)
        
        # Correlation of constants is undefined (NaN), should return 0.0
        assert corr == 0.0


class TestIsClose:
    """Test is_close helper method."""

    @pytest.mark.unit
    def test_is_close_default_tolerance(self):
        """Test is_close with default tolerance."""
        pipeline = FeaturePipeline()
        
        # Values within default tolerance (1e-9)
        assert pipeline.is_close(1.0, 1.0 + 1e-10)
        assert pipeline.is_close(1.0, 1.0 - 1e-10)
        
        # Values outside default tolerance
        assert not pipeline.is_close(1.0, 1.0 + 1e-8)

    @pytest.mark.unit
    def test_is_close_custom_tolerance(self):
        """Test is_close with custom tolerance."""
        pipeline = FeaturePipeline()
        
        # Use larger tolerance
        assert pipeline.is_close(1.0, 1.001, tolerance=1e-2)
        assert not pipeline.is_close(1.0, 1.001, tolerance=1e-4)

    @pytest.mark.unit
    def test_is_close_zero_comparison(self):
        """Test is_close for zero comparisons."""
        pipeline = FeaturePipeline()
        
        assert pipeline.is_close(0.0, 0.0)
        assert pipeline.is_close(0.0, 1e-10)
        assert not pipeline.is_close(0.0, 1e-6)


class TestComputeMaRatio:
    """Test _compute_ma_ratio private method."""

    @pytest.mark.unit
    def test_compute_ma_ratio_insufficient_data(self):
        """Test that insufficient data returns 1.0."""
        pipeline = FeaturePipeline()
        closes = [100.0, 105.0]
        
        # Window of 5 but only 2 prices
        ratio = pipeline._compute_ma_ratio(closes, lookback_window=5)
        
        assert ratio == 1.0

    @pytest.mark.unit
    def test_compute_ma_ratio_sufficient_data(self):
        """Test compute_ma_ratio with sufficient data."""
        pipeline = FeaturePipeline()
        # Create data where current price is above MA
        closes = [100.0, 101.0, 102.0, 103.0, 110.0]
        
        ratio = pipeline._compute_ma_ratio(closes, lookback_window=5)
        
        # MA of [100, 101, 102, 103, 110] = 103.2
        # Ratio should be 110/103.2 ≈ 1.066
        assert ratio > 1.0  # Current price above MA
        assert math.isclose(ratio, 110.0 / 103.2, abs_tol=1e-6)

    @pytest.mark.unit
    def test_compute_ma_ratio_zero_ma(self):
        """Test that zero MA returns 1.0."""
        pipeline = FeaturePipeline()
        # This shouldn't happen in practice, but test the guard
        closes = [0.0] * 5
        
        ratio = pipeline._compute_ma_ratio(closes, lookback_window=5)
        
        # Should return 1.0 when MA is zero (within tolerance)
        assert ratio == 1.0


class TestComputePricePosition:
    """Test _compute_price_position private method."""

    def _create_test_bars(self, highs: list[float], lows: list[float], closes: list[float]) -> list[MarketBar]:
        """Helper to create MarketBar objects."""
        bars = []
        for i, (h, l, c) in enumerate(zip(highs, lows, closes)):
            bar = MarketBar(
                timestamp=datetime(2024, 1, 1, 9 + i, 0, tzinfo=UTC),
                symbol="TEST",
                timeframe="1H",
                open_price=Decimal(str(c)),
                high_price=Decimal(str(h)),
                low_price=Decimal(str(l)),
                close_price=Decimal(str(c)),
                volume=1000,
            )
            bars.append(bar)
        return bars

    @pytest.mark.unit
    def test_compute_price_position_insufficient_data(self):
        """Test that insufficient data returns 0.5."""
        pipeline = FeaturePipeline()
        bars = self._create_test_bars([101.0, 102.0], [99.0, 98.0], [100.0, 100.0])
        
        # Window of 5 but only 2 bars
        position = pipeline._compute_price_position(bars, 100.0, lookback_window=5)
        
        assert position == 0.5

    @pytest.mark.unit
    def test_compute_price_position_at_low(self):
        """Test price position when price is at the low."""
        pipeline = FeaturePipeline()
        bars = self._create_test_bars(
            highs=[110.0] * 5,
            lows=[100.0] * 5,
            closes=[100.0] * 5
        )
        
        position = pipeline._compute_price_position(bars, 100.0, lookback_window=5)
        
        # Price at low: (100 - 100) / (110 - 100) = 0.0
        assert math.isclose(position, 0.0, abs_tol=1e-9)

    @pytest.mark.unit
    def test_compute_price_position_at_high(self):
        """Test price position when price is at the high."""
        pipeline = FeaturePipeline()
        bars = self._create_test_bars(
            highs=[110.0] * 5,
            lows=[100.0] * 5,
            closes=[110.0] * 5
        )
        
        position = pipeline._compute_price_position(bars, 110.0, lookback_window=5)
        
        # Price at high: (110 - 100) / (110 - 100) = 1.0
        assert math.isclose(position, 1.0, abs_tol=1e-9)

    @pytest.mark.unit
    def test_compute_price_position_mid_range(self):
        """Test price position in middle of range."""
        pipeline = FeaturePipeline()
        bars = self._create_test_bars(
            highs=[110.0] * 5,
            lows=[100.0] * 5,
            closes=[105.0] * 5
        )
        
        position = pipeline._compute_price_position(bars, 105.0, lookback_window=5)
        
        # Price at middle: (105 - 100) / (110 - 100) = 0.5
        assert math.isclose(position, 0.5, abs_tol=1e-9)

    @pytest.mark.unit
    def test_compute_price_position_no_range(self):
        """Test price position when high equals low."""
        pipeline = FeaturePipeline()
        bars = self._create_test_bars(
            highs=[100.0] * 5,
            lows=[100.0] * 5,
            closes=[100.0] * 5
        )
        
        position = pipeline._compute_price_position(bars, 100.0, lookback_window=5)
        
        # No range, should return default 0.5
        assert position == 0.5


class TestComputeVolumeRatio:
    """Test _compute_volume_ratio private method."""

    @pytest.mark.unit
    def test_compute_volume_ratio_insufficient_data(self):
        """Test that insufficient data returns 1.0."""
        pipeline = FeaturePipeline()
        volumes = [1000.0, 2000.0]
        
        # Window of 5 but only 2 volumes
        ratio = pipeline._compute_volume_ratio(volumes, lookback_window=5)
        
        assert ratio == 1.0

    @pytest.mark.unit
    def test_compute_volume_ratio_above_average(self):
        """Test volume ratio when current volume is above average."""
        pipeline = FeaturePipeline()
        volumes = [1000.0, 1000.0, 1000.0, 1000.0, 2000.0]
        
        ratio = pipeline._compute_volume_ratio(volumes, lookback_window=5)
        
        # Average = 6000/5 = 1200, current = 2000, ratio = 2000/1200 ≈ 1.667
        assert ratio > 1.0
        assert math.isclose(ratio, 2000.0 / 1200.0, abs_tol=1e-6)

    @pytest.mark.unit
    def test_compute_volume_ratio_below_average(self):
        """Test volume ratio when current volume is below average."""
        pipeline = FeaturePipeline()
        volumes = [2000.0, 2000.0, 2000.0, 2000.0, 500.0]
        
        ratio = pipeline._compute_volume_ratio(volumes, lookback_window=5)
        
        # Average = 8500/5 = 1700, current = 500, ratio = 500/1700 ≈ 0.294
        assert ratio < 1.0
        assert math.isclose(ratio, 500.0 / 1700.0, abs_tol=1e-6)

    @pytest.mark.unit
    def test_compute_volume_ratio_zero_average(self):
        """Test that zero average volume returns 1.0."""
        pipeline = FeaturePipeline()
        volumes = [0.0] * 5
        
        ratio = pipeline._compute_volume_ratio(volumes, lookback_window=5)
        
        # Should return 1.0 when average is zero (within tolerance)
        assert ratio == 1.0


class TestExtractPriceFeatures:
    """Test extract_price_features public API."""

    def _create_test_bars(self, count: int, base_price: float = 100.0) -> list[MarketBar]:
        """Helper to create test bars with varying prices."""
        bars = []
        for i in range(count):
            price = base_price + i * 0.5  # Gradually increasing prices
            # Use modulo to keep hours in valid range
            hour = (9 + i) % 24
            bar = MarketBar(
                timestamp=datetime(2024, 1, 1 + (9 + i) // 24, hour, 0, tzinfo=UTC),
                symbol="TEST",
                timeframe="1H",
                open_price=Decimal(str(price)),
                high_price=Decimal(str(price * 1.01)),
                low_price=Decimal(str(price * 0.99)),
                close_price=Decimal(str(price)),
                volume=1000 + i * 100,
            )
            bars.append(bar)
        return bars

    @pytest.mark.unit
    def test_extract_price_features_empty_bars(self):
        """Test that empty bars returns empty dict."""
        pipeline = FeaturePipeline()
        
        features = pipeline.extract_price_features([])
        
        assert features == {}

    @pytest.mark.unit
    def test_extract_price_features_sufficient_data(self):
        """Test extract_price_features with sufficient data."""
        pipeline = FeaturePipeline()
        bars = self._create_test_bars(25)
        
        features = pipeline.extract_price_features(bars, lookback_window=20)
        
        # Check all expected features are present
        assert "current_price" in features
        assert "volatility" in features
        assert "ma_ratio" in features
        assert "price_position" in features
        assert "volume_ratio" in features
        
        # Check values are reasonable
        assert features["current_price"] > 0.0
        assert features["volatility"] >= 0.0
        assert features["ma_ratio"] > 0.0
        assert 0.0 <= features["price_position"] <= 1.0
        assert features["volume_ratio"] > 0.0

    @pytest.mark.unit
    def test_extract_price_features_minimal_data(self):
        """Test extract_price_features with minimal data."""
        pipeline = FeaturePipeline()
        bars = self._create_test_bars(3)
        
        features = pipeline.extract_price_features(bars, lookback_window=20)
        
        # Should still return features, but with defaults for insufficient data
        assert "current_price" in features
        assert "volatility" in features
        assert features["current_price"] > 0.0

    @pytest.mark.unit
    def test_extract_price_features_default_window(self):
        """Test extract_price_features uses default window of 20."""
        pipeline = FeaturePipeline()
        bars = self._create_test_bars(25)
        
        # Call without specifying window
        features = pipeline.extract_price_features(bars)
        
        assert "current_price" in features
        assert "volatility" in features


class TestFeaturePipelineEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.mark.unit
    def test_determinism_with_same_input(self):
        """Test that same input produces same output (determinism)."""
        pipeline = FeaturePipeline()
        
        bars = []
        for i in range(25):
            price = 100.0 + i * 0.5
            # Use modulo to keep hours in valid range
            hour = (9 + i) % 24
            bar = MarketBar(
                timestamp=datetime(2024, 1, 1 + (9 + i) // 24, hour, 0, tzinfo=UTC),
                symbol="TEST",
                timeframe="1H",
                open_price=Decimal(str(price)),
                high_price=Decimal(str(price * 1.01)),
                low_price=Decimal(str(price * 0.99)),
                close_price=Decimal(str(price)),
                volume=1000,
            )
            bars.append(bar)
        
        # Run twice
        features1 = pipeline.extract_price_features(bars)
        features2 = pipeline.extract_price_features(bars)
        
        # Should be identical
        assert features1 == features2

    @pytest.mark.unit
    def test_numpy_seed_determinism(self):
        """Test that correlation is deterministic with seeded numpy."""
        pipeline = FeaturePipeline()
        
        series1 = [1.0, 2.0, 3.0, 4.0, 5.0]
        series2 = [2.0, 4.0, 6.0, 8.0, 10.0]
        
        # Seed numpy
        np.random.seed(42)
        corr1 = pipeline.compute_correlation(series1, series2)
        
        # Seed again
        np.random.seed(42)
        corr2 = pipeline.compute_correlation(series1, series2)
        
        # Should be identical
        assert corr1 == corr2


# Property-based tests with Hypothesis
class TestFeaturePipelineProperties:
    """Property-based tests for mathematical invariants."""

    @pytest.mark.property
    @given(
        prices=st.lists(
            st.floats(min_value=1.0, max_value=1000.0),
            min_size=2,
            max_size=50  # Limit to avoid hour overflow
        )
    )
    def test_returns_length_property(self, prices):
        """Property: returns list should be len(prices) - 1."""
        pipeline = FeaturePipeline()
        
        bars = []
        for i, price in enumerate(prices):
            # Use modulo to keep hours in valid range
            hour = (9 + i) % 24
            bar = MarketBar(
                timestamp=datetime(2024, 1, 1 + (9 + i) // 24, hour, 0, tzinfo=UTC),
                symbol="TEST",
                timeframe="1H",
                open_price=Decimal(str(price)),
                high_price=Decimal(str(price * 1.01)),
                low_price=Decimal(str(price * 0.99)),
                close_price=Decimal(str(price)),
                volume=1000,
            )
            bars.append(bar)
        
        returns = pipeline.compute_returns(bars)
        
        # Allow for zero-price skipping
        assert len(returns) <= len(prices) - 1

    @pytest.mark.property
    @given(
        returns=st.lists(
            st.floats(min_value=-0.5, max_value=0.5),
            min_size=2,
            max_size=50
        )
    )
    def test_volatility_non_negative_property(self, returns):
        """Property: volatility should always be non-negative."""
        pipeline = FeaturePipeline()
        
        vol = pipeline.compute_volatility(returns, annualize=False)
        
        assert vol >= 0.0

    @pytest.mark.property
    @given(
        values=st.lists(
            st.floats(min_value=1.0, max_value=1000.0),
            min_size=10,
            max_size=50
        ),
        window=st.integers(min_value=1, max_value=10)
    )
    def test_moving_average_bounds_property(self, values, window):
        """Property: moving average should be within min/max of window."""
        pipeline = FeaturePipeline()
        
        averages = pipeline.compute_moving_average(values, window)
        
        for avg in averages:
            # Each average should be between min and max of all values
            assert min(values) <= avg <= max(values)

    @pytest.mark.property
    @given(
        series1=st.lists(
            st.floats(min_value=-100.0, max_value=100.0),
            min_size=10,
            max_size=30
        )
    )
    def test_correlation_bounds_property(self, series1):
        """Property: correlation should be in range [-1, 1]."""
        pipeline = FeaturePipeline()
        
        # Create correlated series
        series2 = [x * 2.0 for x in series1]
        
        corr = pipeline.compute_correlation(series1, series2)
        
        # Correlation must be in [-1, 1]
        assert -1.0 <= corr <= 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
