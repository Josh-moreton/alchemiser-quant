"""Business Unit: strategy | Status: current.

Comprehensive tests for technical indicators.

This module tests all technical indicator calculations including:
- RSI (Relative Strength Index)
- Moving averages (simple and exponential)
- Return calculations (moving average, cumulative, standard deviation)
- Maximum drawdown

Tests include unit tests for correctness and property-based tests
for mathematical invariants using Hypothesis.
"""

from __future__ import annotations

import math

import pandas as pd
import pytest
from hypothesis import given, strategies as st

from the_alchemiser.shared.errors.exceptions import MarketDataError
from the_alchemiser.strategy_v2.indicators.indicators import (
    DEFAULT_RSI_WINDOW,
    NEUTRAL_RSI_VALUE,
    TechnicalIndicators,
)


@pytest.mark.unit
class TestRSI:
    """Test RSI calculations."""

    def test_rsi_neutral_on_flat_prices(self):
        """RSI should be neutral (50) when prices are flat."""
        prices = pd.Series([100.0] * 20)
        rsi = TechnicalIndicators.rsi(prices, window=14)
        
        # All values should be neutral RSI
        valid_rsi = rsi.dropna()
        assert len(valid_rsi) > 0
        for val in valid_rsi:
            assert abs(val - NEUTRAL_RSI_VALUE) < 0.01

    def test_rsi_uses_default_window(self):
        """RSI should use default window when not specified."""
        prices = pd.Series([100 + i for i in range(20)])
        rsi = TechnicalIndicators.rsi(prices)
        
        # Should not raise and should return valid series
        assert isinstance(rsi, pd.Series)
        assert len(rsi) == len(prices)

    def test_rsi_uptrend_above_neutral(self):
        """RSI should be above neutral in a strong uptrend."""
        prices = pd.Series([100 + i * 2 for i in range(20)])
        rsi = TechnicalIndicators.rsi(prices, window=14)
        
        # Last RSI value should be significantly above neutral
        assert rsi.iloc[-1] > 60.0

    def test_rsi_downtrend_below_neutral(self):
        """RSI should be below neutral in a strong downtrend."""
        prices = pd.Series([100 - i * 2 for i in range(20)])
        rsi = TechnicalIndicators.rsi(prices, window=14)
        
        # Last RSI value should be significantly below neutral
        assert rsi.iloc[-1] < 40.0

    def test_rsi_handles_insufficient_data(self):
        """RSI should return neutral values when data is insufficient."""
        prices = pd.Series([100.0, 101.0, 102.0])
        rsi = TechnicalIndicators.rsi(prices, window=14)
        
        # Should return neutral RSI for all values
        assert len(rsi) == len(prices)
        for val in rsi:
            assert val == NEUTRAL_RSI_VALUE

    def test_rsi_rejects_negative_window(self):
        """RSI should reject negative window."""
        prices = pd.Series([100.0] * 20)
        
        with pytest.raises(MarketDataError, match="must be positive"):
            TechnicalIndicators.rsi(prices, window=-1)

    def test_rsi_rejects_zero_window(self):
        """RSI should reject zero window."""
        prices = pd.Series([100.0] * 20)
        
        with pytest.raises(MarketDataError, match="must be positive"):
            TechnicalIndicators.rsi(prices, window=0)

    def test_rsi_handles_empty_series(self):
        """RSI should handle empty series gracefully."""
        prices = pd.Series(dtype=float)
        rsi = TechnicalIndicators.rsi(prices, window=14)
        
        assert len(rsi) == 0
        assert isinstance(rsi, pd.Series)

    def test_rsi_handles_division_by_zero(self):
        """RSI should handle cases where average loss is zero."""
        # All gains, no losses
        prices = pd.Series([100 + i for i in range(20)])
        rsi = TechnicalIndicators.rsi(prices, window=14)
        
        # Should handle gracefully without inf or errors
        assert not rsi.isna().all()
        assert not (rsi == float('inf')).any()


@pytest.mark.unit
class TestMovingAverage:
    """Test simple moving average calculations."""

    def test_moving_average_correct_calculation(self):
        """Moving average should calculate correctly."""
        prices = pd.Series([100.0, 102.0, 101.0, 103.0, 105.0])
        ma = TechnicalIndicators.moving_average(prices, window=3)
        
        # First two values should be NaN
        assert pd.isna(ma.iloc[0])
        assert pd.isna(ma.iloc[1])
        
        # Third value should be average of first 3 prices
        expected = (100.0 + 102.0 + 101.0) / 3
        assert abs(ma.iloc[2] - expected) < 0.01

    def test_moving_average_rejects_negative_window(self):
        """Moving average should reject negative window."""
        prices = pd.Series([100.0] * 20)
        
        with pytest.raises(MarketDataError, match="must be positive"):
            TechnicalIndicators.moving_average(prices, window=-1)

    def test_moving_average_handles_empty_series(self):
        """Moving average should handle empty series gracefully."""
        prices = pd.Series(dtype=float)
        ma = TechnicalIndicators.moving_average(prices, window=3)
        
        assert len(ma) == 0
        assert isinstance(ma, pd.Series)


@pytest.mark.unit
class TestExponentialMovingAverage:
    """Test exponential moving average calculations."""

    def test_ema_masks_early_values(self):
        """EMA should mask early values similar to SMA."""
        prices = pd.Series([100.0, 102.0, 101.0, 103.0, 105.0])
        ema = TechnicalIndicators.exponential_moving_average(prices, window=3)
        
        # First two values should be masked
        assert pd.isna(ema.iloc[0])
        assert pd.isna(ema.iloc[1])
        
        # Later values should not be NaN
        assert not pd.isna(ema.iloc[2])

    def test_ema_rejects_negative_window(self):
        """EMA should reject negative window."""
        prices = pd.Series([100.0] * 20)
        
        with pytest.raises(MarketDataError, match="must be positive"):
            TechnicalIndicators.exponential_moving_average(prices, window=-1)

    def test_ema_handles_empty_series(self):
        """EMA should handle empty series gracefully."""
        prices = pd.Series(dtype=float)
        ema = TechnicalIndicators.exponential_moving_average(prices, window=3)
        
        assert len(ema) == 0
        assert isinstance(ema, pd.Series)


@pytest.mark.unit
class TestMovingAverageReturn:
    """Test moving average return calculations."""

    def test_moving_average_return_calculation(self):
        """Moving average return should calculate correctly."""
        prices = pd.Series([100.0, 102.0, 101.0, 103.0, 105.0])
        returns = TechnicalIndicators.moving_average_return(prices, window=3)
        
        # Should return a series of same length
        assert len(returns) == len(prices)
        
        # Values should be in percentage form
        assert isinstance(returns.iloc[-1], float)

    def test_moving_average_return_handles_insufficient_data(self):
        """Moving average return should handle insufficient data."""
        prices = pd.Series([100.0, 101.0])
        returns = TechnicalIndicators.moving_average_return(prices, window=5)
        
        # Should return zero series
        assert all(returns == 0)

    def test_moving_average_return_rejects_negative_window(self):
        """Moving average return should reject negative window."""
        prices = pd.Series([100.0] * 20)
        
        with pytest.raises(MarketDataError, match="must be positive"):
            TechnicalIndicators.moving_average_return(prices, window=-1)


@pytest.mark.unit
class TestCumulativeReturn:
    """Test cumulative return calculations."""

    def test_cumulative_return_calculation(self):
        """Cumulative return should calculate correctly."""
        prices = pd.Series([100.0, 102.0, 98.0, 105.0, 110.0])
        cum_ret = TechnicalIndicators.cumulative_return(prices, window=2)
        
        # Third value should be (98 / 100 - 1) * 100 = -2%
        assert abs(cum_ret.iloc[2] - (-2.0)) < 0.01
        
        # Fourth value should be (105 / 102 - 1) * 100 ≈ 2.94%
        expected = ((105.0 / 102.0) - 1) * 100
        assert abs(cum_ret.iloc[3] - expected) < 0.01

    def test_cumulative_return_handles_insufficient_data(self):
        """Cumulative return should handle insufficient data."""
        prices = pd.Series([100.0, 101.0])
        cum_ret = TechnicalIndicators.cumulative_return(prices, window=5)
        
        # Should return zero series
        assert all(cum_ret == 0)

    def test_cumulative_return_rejects_negative_window(self):
        """Cumulative return should reject negative window."""
        prices = pd.Series([100.0] * 20)
        
        with pytest.raises(MarketDataError, match="must be positive"):
            TechnicalIndicators.cumulative_return(prices, window=-1)


@pytest.mark.unit
class TestStdevReturn:
    """Test standard deviation of returns calculations."""

    def test_stdev_return_calculation(self):
        """Standard deviation return should calculate correctly."""
        prices = pd.Series([100.0, 102.0, 98.0, 105.0, 103.0, 110.0])
        stdev = TechnicalIndicators.stdev_return(prices, window=3)
        
        # Should return a series of same length
        assert len(stdev) == len(prices)
        
        # Values should be positive (or NaN for insufficient data)
        valid_values = stdev.dropna()
        assert all(valid_values >= 0)

    def test_stdev_return_handles_insufficient_data(self):
        """Standard deviation return should handle insufficient data."""
        prices = pd.Series([100.0, 101.0])
        stdev = TechnicalIndicators.stdev_return(prices, window=5)
        
        # Should return zero series
        assert all(stdev == 0)

    def test_stdev_return_rejects_negative_window(self):
        """Standard deviation return should reject negative window."""
        prices = pd.Series([100.0] * 20)
        
        with pytest.raises(MarketDataError, match="must be positive"):
            TechnicalIndicators.stdev_return(prices, window=-1)


@pytest.mark.unit
class TestMaxDrawdown:
    """Test maximum drawdown calculations."""

    def test_max_drawdown_calculation(self):
        """Maximum drawdown should calculate correctly."""
        prices = pd.Series([100.0, 105.0, 98.0, 102.0, 95.0, 110.0])
        mdd = TechnicalIndicators.max_drawdown(prices, window=3)
        
        # Should return a series of same length
        assert len(mdd) == len(prices)
        
        # Values should be positive (or NaN for insufficient data)
        valid_values = mdd.dropna()
        assert all(valid_values >= 0)

    def test_max_drawdown_peak_to_trough(self):
        """Maximum drawdown should measure peak to trough correctly."""
        # Create a clear peak-to-trough scenario
        prices = pd.Series([100.0, 110.0, 90.0, 95.0])
        mdd = TechnicalIndicators.max_drawdown(prices, window=3)
        
        # At index 2: window [100, 110, 90]
        # Max drawdown should be (110 - 90) / 110 * 100 ≈ 18.18%
        expected = ((110.0 - 90.0) / 110.0) * 100
        assert abs(mdd.iloc[2] - expected) < 0.5

    def test_max_drawdown_handles_insufficient_data(self):
        """Maximum drawdown should handle insufficient data."""
        prices = pd.Series([100.0, 101.0])
        mdd = TechnicalIndicators.max_drawdown(prices, window=5)
        
        # Should return zero series
        assert all(mdd == 0)

    def test_max_drawdown_rejects_negative_window(self):
        """Maximum drawdown should reject negative window."""
        prices = pd.Series([100.0] * 20)
        
        with pytest.raises(MarketDataError, match="must be positive"):
            TechnicalIndicators.max_drawdown(prices, window=-1)


@pytest.mark.unit
@pytest.mark.property
class TestIndicatorProperties:
    """Property-based tests for mathematical invariants."""

    @given(st.lists(st.floats(min_value=1.0, max_value=1000.0), min_size=20, max_size=100))
    def test_rsi_bounds(self, prices):
        """Property: RSI should always be between 0 and 100."""
        series = pd.Series(prices)
        rsi = TechnicalIndicators.rsi(series, window=14)
        
        # All non-NaN values should be in [0, 100]
        valid_rsi = rsi.dropna()
        if len(valid_rsi) > 0:
            assert (valid_rsi >= 0).all()
            assert (valid_rsi <= 100).all()

    @given(st.lists(st.floats(min_value=1.0, max_value=1000.0), min_size=10, max_size=50))
    def test_moving_average_smoothness(self, prices):
        """Property: Moving average should smooth out variations."""
        series = pd.Series(prices)
        if len(series) < 5:
            return  # Skip if insufficient data
        
        ma = TechnicalIndicators.moving_average(series, window=5)
        valid_ma = ma.dropna()
        
        if len(valid_ma) > 1:
            # MA should exist and be within range of original prices
            assert valid_ma.min() >= series.min() * 0.5
            assert valid_ma.max() <= series.max() * 1.5

    @given(st.lists(st.floats(min_value=10.0, max_value=1000.0), min_size=10, max_size=50))
    def test_cumulative_return_symmetry(self, prices):
        """Property: Cumulative return should be symmetric with price changes."""
        series = pd.Series(prices)
        if len(series) < 5:
            return  # Skip if insufficient data
        
        cum_ret = TechnicalIndicators.cumulative_return(series, window=1)
        
        # 1-period cumulative return should match pct_change * 100
        pct_change = series.pct_change() * 100
        
        # Compare non-NaN values
        valid_indices = ~(cum_ret.isna() | pct_change.isna())
        if valid_indices.sum() > 0:
            assert abs((cum_ret[valid_indices] - pct_change[valid_indices]).max()) < 0.1

    @given(st.lists(st.floats(min_value=10.0, max_value=1000.0), min_size=10, max_size=50))
    def test_max_drawdown_non_negative(self, prices):
        """Property: Maximum drawdown should always be non-negative."""
        series = pd.Series(prices)
        if len(series) < 5:
            return  # Skip if insufficient data
        
        mdd = TechnicalIndicators.max_drawdown(series, window=5)
        valid_mdd = mdd.dropna()
        
        if len(valid_mdd) > 0:
            # All drawdowns should be >= 0
            assert (valid_mdd >= 0).all()


@pytest.mark.unit
class TestInputValidation:
    """Test input validation across all indicators."""

    def test_all_indicators_reject_negative_windows(self):
        """All indicators should reject negative windows."""
        prices = pd.Series([100.0] * 20)
        
        indicators = [
            TechnicalIndicators.rsi,
            TechnicalIndicators.moving_average,
            TechnicalIndicators.exponential_moving_average,
            TechnicalIndicators.moving_average_return,
            TechnicalIndicators.cumulative_return,
            TechnicalIndicators.stdev_return,
            TechnicalIndicators.max_drawdown,
        ]
        
        for indicator in indicators:
            with pytest.raises(MarketDataError, match="must be positive"):
                indicator(prices, window=-1)

    def test_all_indicators_handle_empty_series(self):
        """All indicators should handle empty series gracefully."""
        prices = pd.Series(dtype=float)
        
        indicators = [
            TechnicalIndicators.rsi,
            TechnicalIndicators.moving_average,
            TechnicalIndicators.exponential_moving_average,
            TechnicalIndicators.moving_average_return,
            TechnicalIndicators.cumulative_return,
            TechnicalIndicators.stdev_return,
            TechnicalIndicators.max_drawdown,
        ]
        
        for indicator in indicators:
            result = indicator(prices, window=5)
            assert isinstance(result, pd.Series)
            assert len(result) == 0


@pytest.mark.unit
class TestDeterminism:
    """Test that indicators produce deterministic results."""

    def test_rsi_deterministic(self):
        """RSI should produce same results for same input."""
        prices = pd.Series([100 + i * 0.5 for i in range(30)])
        
        rsi1 = TechnicalIndicators.rsi(prices, window=14)
        rsi2 = TechnicalIndicators.rsi(prices, window=14)
        
        # Results should be identical
        pd.testing.assert_series_equal(rsi1, rsi2)

    def test_moving_average_deterministic(self):
        """Moving average should produce same results for same input."""
        prices = pd.Series([100 + i * 0.5 for i in range(30)])
        
        ma1 = TechnicalIndicators.moving_average(prices, window=10)
        ma2 = TechnicalIndicators.moving_average(prices, window=10)
        
        # Results should be identical
        pd.testing.assert_series_equal(ma1, ma2)
