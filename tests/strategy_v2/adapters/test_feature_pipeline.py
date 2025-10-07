#!/usr/bin/env python3
"""Business Unit: strategy_v2 | Status: current.

Tests for FeaturePipeline feature computation.

Comprehensive test suite including unit tests and property-based tests
for mathematical correctness and edge cases.
"""

from __future__ import annotations

import math
from datetime import datetime, timezone
from decimal import Decimal

import numpy as np
import pytest
from hypothesis import given
from hypothesis import strategies as st

from the_alchemiser.shared.schemas.market_bar import MarketBar
from the_alchemiser.strategy_v2.adapters.feature_pipeline import FeaturePipeline


@pytest.fixture
def feature_pipeline():
    """Create a feature pipeline instance."""
    return FeaturePipeline()


@pytest.fixture
def sample_bars():
    """Create sample market bars for testing."""
    return [
        MarketBar(
            timestamp=datetime(2025, 1, i, tzinfo=timezone.utc),
            symbol="AAPL",
            timeframe="1D",
            open_price=Decimal("100.00"),
            high_price=Decimal("105.00"),
            low_price=Decimal("99.00"),
            close_price=Decimal(f"{100 + i}.00"),
            volume=1000000,
        )
        for i in range(1, 31)
    ]


class TestInitialization:
    """Test FeaturePipeline initialization."""

    @pytest.mark.unit
    def test_default_initialization(self):
        """Test default initialization with default tolerance."""
        pipeline = FeaturePipeline()
        assert pipeline._tolerance == 1e-9

    @pytest.mark.unit
    def test_custom_tolerance(self):
        """Test initialization with custom tolerance."""
        pipeline = FeaturePipeline(default_tolerance=1e-6)
        assert pipeline._tolerance == 1e-6


class TestComputeReturns:
    """Test return calculation."""

    @pytest.mark.unit
    def test_returns_with_valid_data(self, feature_pipeline, sample_bars):
        """Test returns calculation with valid data."""
        returns = feature_pipeline.compute_returns(sample_bars)
        assert len(returns) == len(sample_bars) - 1
        assert all(isinstance(r, float) for r in returns)

    @pytest.mark.unit
    def test_empty_list_returns_empty(self, feature_pipeline):
        """Test that empty list returns empty."""
        assert feature_pipeline.compute_returns([]) == []

    @pytest.mark.unit
    def test_single_bar_returns_empty(self, feature_pipeline, sample_bars):
        """Test that single bar returns empty."""
        assert feature_pipeline.compute_returns([sample_bars[0]]) == []

    @pytest.mark.unit
    def test_returns_calculation_correctness(self, feature_pipeline):
        """Test that returns are calculated correctly."""
        bars = [
            MarketBar(
                timestamp=datetime(2025, 1, 1, tzinfo=timezone.utc),
                symbol="AAPL",
                timeframe="1D",
                open_price=Decimal("100.00"),
                high_price=Decimal("105.00"),
                low_price=Decimal("99.00"),
                close_price=Decimal("100.00"),
                volume=1000000,
            ),
            MarketBar(
                timestamp=datetime(2025, 1, 2, tzinfo=timezone.utc),
                symbol="AAPL",
                timeframe="1D",
                open_price=Decimal("100.00"),
                high_price=Decimal("105.00"),
                low_price=Decimal("99.00"),
                close_price=Decimal("110.00"),  # 10% gain
                volume=1000000,
            ),
        ]
        returns = feature_pipeline.compute_returns(bars)
        assert len(returns) == 1
        assert math.isclose(returns[0], 0.1, abs_tol=1e-9)

    @pytest.mark.unit
    def test_returns_with_zero_price_handling(self, feature_pipeline):
        """Test returns calculation handles near-zero prices."""
        bars = [
            MarketBar(
                timestamp=datetime(2025, 1, 1, tzinfo=timezone.utc),
                symbol="AAPL",
                timeframe="1D",
                open_price=Decimal("0.000001"),
                high_price=Decimal("0.000002"),
                low_price=Decimal("0.000001"),
                close_price=Decimal("0.000001"),
                volume=1000000,
            ),
            MarketBar(
                timestamp=datetime(2025, 1, 2, tzinfo=timezone.utc),
                symbol="AAPL",
                timeframe="1D",
                open_price=Decimal("0.000001"),
                high_price=Decimal("0.000002"),
                low_price=Decimal("0.000001"),
                close_price=Decimal("0.000002"),
                volume=1000000,
            ),
        ]
        returns = feature_pipeline.compute_returns(bars)
        # With prices 0.000001 -> 0.000002, return is (0.000002-0.000001)/0.000001 = 1.0
        assert returns[0] == 1.0

    @pytest.mark.property
    @given(
        st.lists(
            st.decimals(
                min_value=Decimal("1.0"),
                max_value=Decimal("1000.0"),
                allow_nan=False,
                allow_infinity=False,
            ),
            min_size=2,
            max_size=50,
        )
    )
    def test_returns_always_produces_n_minus_1_values(self, prices):
        """Property: returns list should have n-1 elements for n prices."""
        pipeline = FeaturePipeline()
        bars = [
            MarketBar(
                timestamp=datetime(2025, 1, i, tzinfo=timezone.utc),
                symbol="AAPL",
                timeframe="1D",
                open_price=price,
                high_price=price * Decimal("1.05"),
                low_price=price * Decimal("0.95"),
                close_price=price,
                volume=1000000,
            )
            for i, price in enumerate(prices, 1)
        ]
        returns = pipeline.compute_returns(bars)
        assert len(returns) == len(bars) - 1


class TestComputeVolatility:
    """Test volatility calculation."""

    @pytest.mark.unit
    def test_volatility_is_non_negative(self, feature_pipeline):
        """Test that volatility is always non-negative."""
        returns = [0.01, -0.02, 0.015, -0.01, 0.02]
        vol = feature_pipeline.compute_volatility(returns)
        assert vol >= 0.0

    @pytest.mark.unit
    def test_empty_returns_gives_zero_volatility(self, feature_pipeline):
        """Test that empty returns give zero volatility."""
        assert feature_pipeline.compute_volatility([]) == 0.0

    @pytest.mark.unit
    def test_single_return_gives_zero_volatility(self, feature_pipeline):
        """Test that single return gives zero volatility."""
        assert feature_pipeline.compute_volatility([0.01]) == 0.0

    @pytest.mark.unit
    def test_annualized_volatility(self, feature_pipeline):
        """Test annualized volatility calculation."""
        returns = [0.01, -0.01, 0.02, -0.02, 0.015]
        vol_annualized = feature_pipeline.compute_volatility(returns, annualize=True)
        vol_raw = feature_pipeline.compute_volatility(returns, annualize=False)

        # Annualized should be raw * sqrt(252)
        expected_annualized = vol_raw * math.sqrt(252)
        assert math.isclose(vol_annualized, expected_annualized, rel_tol=1e-9)

    @pytest.mark.unit
    def test_volatility_with_window(self, feature_pipeline):
        """Test volatility calculation with window parameter."""
        returns = [0.01, -0.02, 0.015, -0.01, 0.02, 0.005, -0.015]
        vol_window = feature_pipeline.compute_volatility(
            returns, window=3, annualize=False
        )
        vol_full = feature_pipeline.compute_volatility(returns, annualize=False)

        # Windowed volatility should be calculated from last 3 returns
        assert vol_window >= 0.0
        # Results should generally differ unless data is uniform
        assert isinstance(vol_window, float)

    @pytest.mark.property
    @given(
        st.lists(
            st.floats(
                min_value=-0.2, max_value=0.2, allow_nan=False, allow_infinity=False
            ),
            min_size=2,
            max_size=100,
        )
    )
    def test_volatility_always_non_negative(self, returns):
        """Property: volatility should always be non-negative."""
        pipeline = FeaturePipeline()
        vol = pipeline.compute_volatility(returns, annualize=False)
        assert vol >= 0.0

    @pytest.mark.property
    @given(
        st.floats(min_value=-0.1, max_value=0.1, allow_nan=False, allow_infinity=False)
    )
    def test_zero_volatility_for_constant_returns(self, constant_value):
        """Property: constant returns should give zero volatility."""
        pipeline = FeaturePipeline()
        returns = [constant_value] * 10
        vol = pipeline.compute_volatility(returns, annualize=False)
        assert math.isclose(vol, 0.0, abs_tol=1e-9)


class TestComputeMovingAverage:
    """Test moving average calculation."""

    @pytest.mark.unit
    def test_moving_average_with_valid_data(self, feature_pipeline):
        """Test moving average calculation with valid data."""
        values = [1.0, 2.0, 3.0, 4.0, 5.0]
        window = 3
        ma = feature_pipeline.compute_moving_average(values, window)

        assert len(ma) == len(values) - window + 1
        assert math.isclose(ma[0], 2.0, abs_tol=1e-9)  # (1+2+3)/3
        assert math.isclose(ma[1], 3.0, abs_tol=1e-9)  # (2+3+4)/3
        assert math.isclose(ma[2], 4.0, abs_tol=1e-9)  # (3+4+5)/3

    @pytest.mark.unit
    def test_moving_average_insufficient_data(self, feature_pipeline):
        """Test moving average with insufficient data."""
        values = [1.0, 2.0]
        window = 3
        ma = feature_pipeline.compute_moving_average(values, window)
        assert ma == []

    @pytest.mark.unit
    def test_moving_average_invalid_window(self, feature_pipeline):
        """Test moving average with invalid window."""
        values = [1.0, 2.0, 3.0, 4.0, 5.0]
        ma = feature_pipeline.compute_moving_average(values, 0)
        assert ma == []

        ma = feature_pipeline.compute_moving_average(values, -1)
        assert ma == []

    @pytest.mark.unit
    def test_moving_average_window_equals_length(self, feature_pipeline):
        """Test moving average when window equals data length."""
        values = [1.0, 2.0, 3.0, 4.0, 5.0]
        window = 5
        ma = feature_pipeline.compute_moving_average(values, window)

        assert len(ma) == 1
        assert math.isclose(ma[0], 3.0, abs_tol=1e-9)  # (1+2+3+4+5)/5


class TestComputeCorrelation:
    """Test correlation calculation."""

    @pytest.mark.unit
    def test_perfect_positive_correlation(self, feature_pipeline):
        """Test perfect positive correlation."""
        series = [1.0, 2.0, 3.0, 4.0, 5.0]
        corr = feature_pipeline.compute_correlation(series, series)
        assert math.isclose(corr, 1.0, abs_tol=1e-9)

    @pytest.mark.unit
    def test_perfect_negative_correlation(self, feature_pipeline):
        """Test perfect negative correlation."""
        series1 = [1.0, 2.0, 3.0, 4.0, 5.0]
        series2 = [5.0, 4.0, 3.0, 2.0, 1.0]
        corr = feature_pipeline.compute_correlation(series1, series2)
        assert math.isclose(corr, -1.0, abs_tol=1e-9)

    @pytest.mark.unit
    def test_zero_correlation(self, feature_pipeline):
        """Test zero correlation (orthogonal series)."""
        # Create orthogonal series
        series1 = [1.0, 2.0, 3.0, 4.0, 5.0]
        series2 = [3.0, 3.0, 3.0, 3.0, 3.0]  # Constant has undefined correlation
        corr = feature_pipeline.compute_correlation(series1, series2)
        # Should return 0.0 due to NaN handling
        assert corr == 0.0

    @pytest.mark.unit
    def test_correlation_mismatched_lengths(self, feature_pipeline):
        """Test correlation with mismatched series lengths."""
        series1 = [1.0, 2.0, 3.0]
        series2 = [1.0, 2.0, 3.0, 4.0]
        corr = feature_pipeline.compute_correlation(series1, series2)
        assert corr == 0.0

    @pytest.mark.unit
    def test_correlation_insufficient_data(self, feature_pipeline):
        """Test correlation with insufficient data."""
        series1 = [1.0]
        series2 = [2.0]
        corr = feature_pipeline.compute_correlation(series1, series2)
        assert corr == 0.0

    @pytest.mark.property
    @given(
        st.lists(
            st.floats(
                min_value=-100, max_value=100, allow_nan=False, allow_infinity=False
            ),
            min_size=2,
            max_size=100,
        )
    )
    def test_correlation_bounded(self, series):
        """Property: correlation should be in [-1, 1]."""
        pipeline = FeaturePipeline()
        corr = pipeline.compute_correlation(series, series)
        assert -1.0 <= corr <= 1.0

    @pytest.mark.property
    @given(
        st.lists(
            st.floats(
                min_value=-100, max_value=100, allow_nan=False, allow_infinity=False
            ),
            min_size=2,
            max_size=100,
        )
    )
    def test_correlation_symmetric(self, series):
        """Property: correlation should be symmetric."""
        pipeline = FeaturePipeline()
        # Create another series with different values
        series2 = [x + 1 for x in series]
        corr1 = pipeline.compute_correlation(series, series2)
        corr2 = pipeline.compute_correlation(series2, series)
        assert math.isclose(corr1, corr2, abs_tol=1e-9)


class TestIsClose:
    """Test float comparison helper."""

    @pytest.mark.unit
    def test_is_close_with_equal_values(self, feature_pipeline):
        """Test is_close with equal values."""
        assert feature_pipeline.is_close(1.0, 1.0)

    @pytest.mark.unit
    def test_is_close_within_tolerance(self, feature_pipeline):
        """Test is_close within default tolerance."""
        assert feature_pipeline.is_close(1.0, 1.0 + 1e-10)
        assert feature_pipeline.is_close(1.0, 1.0 - 1e-10)

    @pytest.mark.unit
    def test_is_close_outside_tolerance(self, feature_pipeline):
        """Test is_close outside default tolerance."""
        assert not feature_pipeline.is_close(1.0, 1.0 + 1e-6)
        assert not feature_pipeline.is_close(1.0, 1.0 - 1e-6)

    @pytest.mark.unit
    def test_is_close_custom_tolerance(self, feature_pipeline):
        """Test is_close with custom tolerance."""
        assert feature_pipeline.is_close(1.0, 1.1, tolerance=0.2)
        assert not feature_pipeline.is_close(1.0, 1.3, tolerance=0.2)


class TestExtractPriceFeatures:
    """Test feature extraction."""

    @pytest.mark.unit
    def test_extract_features_with_sufficient_data(self, feature_pipeline, sample_bars):
        """Test feature extraction with sufficient data."""
        features = feature_pipeline.extract_price_features(
            sample_bars, lookback_window=20
        )

        # Check all expected features are present
        expected_keys = {
            "current_price",
            "volatility",
            "ma_ratio",
            "price_position",
            "volume_ratio",
        }
        assert set(features.keys()) == expected_keys

        # Check all values are floats
        assert all(isinstance(v, float) for v in features.values())

        # Check reasonable ranges
        assert features["current_price"] > 0
        assert features["volatility"] >= 0
        assert features["ma_ratio"] > 0
        assert 0 <= features["price_position"] <= 1
        assert features["volume_ratio"] > 0

    @pytest.mark.unit
    def test_extract_features_empty_bars(self, feature_pipeline):
        """Test feature extraction with empty bars."""
        features = feature_pipeline.extract_price_features([])
        assert features == {}

    @pytest.mark.unit
    def test_extract_features_insufficient_data(self, feature_pipeline, sample_bars):
        """Test feature extraction with insufficient data for lookback."""
        # Use only 5 bars with lookback of 20
        features = feature_pipeline.extract_price_features(
            sample_bars[:5], lookback_window=20
        )

        # Should still return features but with defaults for some
        assert "current_price" in features
        assert "volatility" in features
        assert features["current_price"] > 0

    @pytest.mark.unit
    def test_extract_features_custom_lookback(self, feature_pipeline, sample_bars):
        """Test feature extraction with custom lookback window."""
        features_10 = feature_pipeline.extract_price_features(
            sample_bars, lookback_window=10
        )
        features_20 = feature_pipeline.extract_price_features(
            sample_bars, lookback_window=20
        )

        # Both should have all keys
        assert set(features_10.keys()) == set(features_20.keys())

        # Current price should be the same
        assert features_10["current_price"] == features_20["current_price"]

        # Other features may differ due to different windows
        assert isinstance(features_10["volatility"], float)
        assert isinstance(features_20["volatility"], float)


class TestPrivateMethods:
    """Test private helper methods."""

    @pytest.mark.unit
    def test_compute_ma_ratio(self, feature_pipeline):
        """Test moving average ratio calculation."""
        closes = [100.0, 110.0, 120.0, 130.0, 140.0]
        ratio = feature_pipeline._compute_ma_ratio(closes, lookback_window=3)

        # Current price is 140, MA of last 3 is (120+130+140)/3 = 130
        # Ratio should be 140/130
        expected = 140.0 / 130.0
        assert math.isclose(ratio, expected, abs_tol=1e-9)

    @pytest.mark.unit
    def test_compute_ma_ratio_insufficient_data(self, feature_pipeline):
        """Test MA ratio with insufficient data."""
        closes = [100.0, 110.0]
        ratio = feature_pipeline._compute_ma_ratio(closes, lookback_window=5)
        assert ratio == 1.0  # Default neutral value

    @pytest.mark.unit
    def test_compute_price_position(self, feature_pipeline, sample_bars):
        """Test price position calculation."""
        position = feature_pipeline._compute_price_position(
            sample_bars[:20], 102.5, lookback_window=20
        )

        # Position should be between 0 and 1
        assert 0.0 <= position <= 1.0

    @pytest.mark.unit
    def test_compute_price_position_at_high(self, feature_pipeline):
        """Test price position when at high."""
        bars = [
            MarketBar(
                timestamp=datetime(2025, 1, i, tzinfo=timezone.utc),
                symbol="AAPL",
                timeframe="1D",
                open_price=Decimal("100.00"),
                high_price=Decimal("110.00"),
                low_price=Decimal("90.00"),
                close_price=Decimal("100.00"),
                volume=1000000,
            )
            for i in range(1, 6)
        ]

        # Price at the high of the range
        position = feature_pipeline._compute_price_position(
            bars, 110.0, lookback_window=5
        )
        assert math.isclose(position, 1.0, abs_tol=1e-9)

    @pytest.mark.unit
    def test_compute_price_position_at_low(self, feature_pipeline):
        """Test price position when at low."""
        bars = [
            MarketBar(
                timestamp=datetime(2025, 1, i, tzinfo=timezone.utc),
                symbol="AAPL",
                timeframe="1D",
                open_price=Decimal("100.00"),
                high_price=Decimal("110.00"),
                low_price=Decimal("90.00"),
                close_price=Decimal("100.00"),
                volume=1000000,
            )
            for i in range(1, 6)
        ]

        # Price at the low of the range
        position = feature_pipeline._compute_price_position(
            bars, 90.0, lookback_window=5
        )
        assert math.isclose(position, 0.0, abs_tol=1e-9)

    @pytest.mark.unit
    def test_compute_price_position_no_range(self, feature_pipeline):
        """Test price position when high equals low."""
        bars = [
            MarketBar(
                timestamp=datetime(2025, 1, i, tzinfo=timezone.utc),
                symbol="AAPL",
                timeframe="1D",
                open_price=Decimal("100.00"),
                high_price=Decimal("100.00"),
                low_price=Decimal("100.00"),
                close_price=Decimal("100.00"),
                volume=1000000,
            )
            for i in range(1, 6)
        ]

        # When high == low, should return default 0.5
        position = feature_pipeline._compute_price_position(
            bars, 100.0, lookback_window=5
        )
        assert position == 0.5

    @pytest.mark.unit
    def test_compute_volume_ratio(self, feature_pipeline):
        """Test volume ratio calculation."""
        volumes = [1000000.0, 1100000.0, 1200000.0, 1300000.0, 1400000.0]
        ratio = feature_pipeline._compute_volume_ratio(volumes, lookback_window=5)

        # Current volume is 1400000, average is 1200000
        # Ratio should be 1400000/1200000
        expected = 1400000.0 / 1200000.0
        assert math.isclose(ratio, expected, abs_tol=1e-9)

    @pytest.mark.unit
    def test_compute_volume_ratio_insufficient_data(self, feature_pipeline):
        """Test volume ratio with insufficient data."""
        volumes = [1000000.0, 1100000.0]
        ratio = feature_pipeline._compute_volume_ratio(volumes, lookback_window=5)
        assert ratio == 1.0  # Default neutral value

    @pytest.mark.unit
    def test_compute_volume_ratio_zero_average(self, feature_pipeline):
        """Test volume ratio when average is zero."""
        volumes = [0.0, 0.0, 0.0, 0.0, 0.0]
        ratio = feature_pipeline._compute_volume_ratio(volumes, lookback_window=5)
        assert ratio == 1.0  # Default when denominator is zero


class TestEdgeCases:
    """Test edge cases and error handling."""

    @pytest.mark.unit
    def test_very_large_numbers(self, feature_pipeline):
        """Test handling of very large numbers."""
        bars = [
            MarketBar(
                timestamp=datetime(2025, 1, i, tzinfo=timezone.utc),
                symbol="AAPL",
                timeframe="1D",
                open_price=Decimal("1e10"),
                high_price=Decimal("1.05e10"),
                low_price=Decimal("0.95e10"),
                close_price=Decimal(f"{1e10 + i * 1e8}"),
                volume=1000000,
            )
            for i in range(1, 11)
        ]

        features = feature_pipeline.extract_price_features(bars)
        assert all(isinstance(v, float) for v in features.values())
        assert all(math.isfinite(v) for v in features.values())

    @pytest.mark.unit
    def test_very_small_numbers(self, feature_pipeline):
        """Test handling of very small numbers."""
        bars = [
            MarketBar(
                timestamp=datetime(2025, 1, i, tzinfo=timezone.utc),
                symbol="AAPL",
                timeframe="1D",
                open_price=Decimal("0.01"),
                high_price=Decimal("0.0105"),
                low_price=Decimal("0.0095"),
                close_price=Decimal(f"{0.01 + i * 0.0001}"),
                volume=1000000,
            )
            for i in range(1, 11)
        ]

        features = feature_pipeline.extract_price_features(bars)
        assert all(isinstance(v, float) for v in features.values())
        assert all(math.isfinite(v) for v in features.values())

    @pytest.mark.unit
    def test_all_same_prices(self, feature_pipeline):
        """Test when all prices are the same."""
        bars = [
            MarketBar(
                timestamp=datetime(2025, 1, i, tzinfo=timezone.utc),
                symbol="AAPL",
                timeframe="1D",
                open_price=Decimal("100.00"),
                high_price=Decimal("100.00"),
                low_price=Decimal("100.00"),
                close_price=Decimal("100.00"),
                volume=1000000,
            )
            for i in range(1, 11)
        ]

        features = feature_pipeline.extract_price_features(bars)

        # Should handle gracefully
        assert features["volatility"] == 0.0
        assert features["price_position"] == 0.5  # Default when no range
        assert features["ma_ratio"] == 1.0  # Current price / MA = 1 when all equal
