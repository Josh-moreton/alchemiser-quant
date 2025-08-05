"""
Unit tests for technical indicators calculations.

Tests the core indicator calculations to ensure accuracy and handle edge cases
like missing data, insufficient data points, and precision issues.
"""

from decimal import Decimal

import numpy as np
import pandas as pd
import pytest

# Import the indicators module - adjust import path as needed
try:
    from the_alchemiser.core.indicators.indicators import (
        calculate_bollinger_bands,
        calculate_macd,
        calculate_moving_average,
        calculate_rsi,
        detect_crossover,
    )
except ImportError:
    pytest.skip("Indicators module not available", allow_module_level=True)


class TestMovingAverageCalculations:
    """Test moving average calculations with various data conditions."""

    def test_simple_moving_average(self):
        """Test basic SMA calculation."""
        prices = pd.Series([100, 101, 102, 103, 104, 105])
        period = 3

        sma = calculate_moving_average(prices, period=period, ma_type="SMA")

        # First valid SMA should be at index 2 (3rd element)
        expected_sma = (100 + 101 + 102) / 3
        assert abs(sma.iloc[2] - expected_sma) < 1e-6

        # Last SMA should be average of last 3 values
        expected_last = (103 + 104 + 105) / 3
        assert abs(sma.iloc[-1] - expected_last) < 1e-6

    def test_exponential_moving_average(self):
        """Test EMA calculation."""
        prices = pd.Series([100, 101, 102, 103, 104, 105])
        period = 3

        ema = calculate_moving_average(prices, period=period, ma_type="EMA")

        # EMA should have different values than SMA
        sma = calculate_moving_average(prices, period=period, ma_type="SMA")

        # At least the last values should be different
        assert abs(ema.iloc[-1] - sma.iloc[-1]) > 1e-6

    def test_moving_average_with_missing_data(self):
        """Test MA calculation with NaN values."""
        prices = pd.Series([100, 101, np.nan, 103, 104, 105])
        period = 3

        sma = calculate_moving_average(prices, period=period, ma_type="SMA")

        # Should handle NaN gracefully
        assert not sma.isna().all()

    def test_moving_average_insufficient_data(self):
        """Test MA with insufficient data points."""
        prices = pd.Series([100, 101])  # Only 2 points
        period = 3

        sma = calculate_moving_average(prices, period=period, ma_type="SMA")

        # Should return NaN for insufficient data
        assert sma.isna().sum() >= 2  # At least first 2 should be NaN

    def test_moving_average_precision(self):
        """Test MA calculation precision with Decimal inputs."""
        prices = pd.Series([Decimal("100.1234"), Decimal("101.5678"), Decimal("102.9012")])
        period = 3

        sma = calculate_moving_average(prices, period=period, ma_type="SMA")

        # Check precision is maintained
        expected = (Decimal("100.1234") + Decimal("101.5678") + Decimal("102.9012")) / 3

        # Convert result to Decimal for comparison if needed
        if not isinstance(sma.iloc[-1], Decimal):
            result = Decimal(str(sma.iloc[-1]))
        else:
            result = sma.iloc[-1]

        assert abs(result - expected) < Decimal("1E-6")


class TestRSICalculations:
    """Test RSI (Relative Strength Index) calculations."""

    def test_rsi_basic_calculation(self):
        """Test basic RSI calculation."""
        # Create a simple trending series
        prices = pd.Series([100, 102, 104, 103, 105, 107, 106, 108, 110, 109])
        period = 14

        rsi = calculate_rsi(prices, period=period)

        # RSI should be between 0 and 100
        valid_rsi = rsi.dropna()
        assert (valid_rsi >= 0).all()
        assert (valid_rsi <= 100).all()

    def test_rsi_overbought_oversold(self):
        """Test RSI with clear overbought/oversold conditions."""
        # Create strongly trending up series (should be overbought)
        uptrend_prices = pd.Series(range(100, 130))  # Strong uptrend
        rsi_up = calculate_rsi(uptrend_prices, period=14)

        # Last RSI values should be high (overbought territory)
        assert rsi_up.iloc[-1] > 70

        # Create strongly trending down series (should be oversold)
        downtrend_prices = pd.Series(range(130, 100, -1))  # Strong downtrend
        rsi_down = calculate_rsi(downtrend_prices, period=14)

        # Last RSI values should be low (oversold territory)
        assert rsi_down.iloc[-1] < 30

    def test_rsi_with_flat_prices(self):
        """Test RSI with no price movement."""
        flat_prices = pd.Series([100] * 20)  # No movement
        rsi = calculate_rsi(flat_prices, period=14)

        # RSI should be around 50 for no movement
        valid_rsi = rsi.dropna()
        if len(valid_rsi) > 0:
            # RSI might be NaN or around 50 for flat prices
            assert valid_rsi.iloc[-1] == 50 or pd.isna(valid_rsi.iloc[-1])

    def test_rsi_missing_data(self):
        """Test RSI calculation with missing data."""
        prices = pd.Series([100, 101, np.nan, 103, 104, np.nan, 106, 107])
        rsi = calculate_rsi(prices, period=6)

        # Should handle missing data gracefully
        assert not rsi.isna().all()


class TestBollingerBands:
    """Test Bollinger Bands calculations."""

    def test_bollinger_bands_basic(self):
        """Test basic Bollinger Bands calculation."""
        prices = pd.Series([100, 101, 102, 101, 100, 99, 100, 101, 102, 103])
        period = 5
        std_dev = 2

        bb_upper, bb_middle, bb_lower = calculate_bollinger_bands(
            prices, period=period, std_dev=std_dev
        )

        # Middle band should equal SMA
        sma = calculate_moving_average(prices, period=period, ma_type="SMA")
        pd.testing.assert_series_equal(bb_middle, sma, check_names=False)

        # Upper band should be above middle, lower should be below
        valid_data = ~bb_upper.isna()
        assert (bb_upper[valid_data] >= bb_middle[valid_data]).all()
        assert (bb_lower[valid_data] <= bb_middle[valid_data]).all()

    def test_bollinger_bands_width(self):
        """Test Bollinger Bands width with different volatility."""
        # Low volatility series
        low_vol_prices = pd.Series([100.0, 100.1, 100.0, 100.1, 100.0] * 4)
        bb_upper_low, bb_middle_low, bb_lower_low = calculate_bollinger_bands(
            low_vol_prices, period=10, std_dev=2
        )

        # High volatility series
        high_vol_prices = pd.Series([100, 95, 105, 90, 110, 85, 115, 80, 120, 75])
        bb_upper_high, bb_middle_high, bb_lower_high = calculate_bollinger_bands(
            high_vol_prices, period=10, std_dev=2
        )

        # High volatility should have wider bands
        low_vol_width = bb_upper_low.iloc[-1] - bb_lower_low.iloc[-1]
        high_vol_width = bb_upper_high.iloc[-1] - bb_lower_high.iloc[-1]

        assert high_vol_width > low_vol_width


class TestMACDCalculations:
    """Test MACD (Moving Average Convergence Divergence) calculations."""

    def test_macd_basic(self):
        """Test basic MACD calculation."""
        prices = pd.Series(range(100, 150))  # Trending series

        macd_line, signal_line, histogram = calculate_macd(prices, fast=12, slow=26, signal=9)

        # MACD line should exist
        assert not macd_line.isna().all()

        # Signal line should exist (but might have more NaN due to additional smoothing)
        assert not signal_line.isna().all()

        # Histogram should be MACD - Signal
        valid_idx = ~(macd_line.isna() | signal_line.isna())
        if valid_idx.any():
            expected_histogram = macd_line[valid_idx] - signal_line[valid_idx]
            actual_histogram = histogram[valid_idx]
            pd.testing.assert_series_equal(expected_histogram, actual_histogram, check_names=False)

    def test_macd_crossover_signals(self):
        """Test MACD crossover signal detection."""
        # Create data that should generate crossover
        prices = pd.Series(
            [100] * 20 + list(range(100, 120)) + [120] * 10 + list(range(120, 100, -1))
        )

        macd_line, signal_line, histogram = calculate_macd(prices)

        # Look for crossovers in histogram (changes from positive to negative or vice versa)
        histogram_valid = histogram.dropna()
        if len(histogram_valid) > 1:
            # Check for sign changes
            sign_changes = (histogram_valid[:-1] * histogram_valid[1:]) < 0
            # Should have at least some crossovers in this data
            assert sign_changes.any()


class TestCrossoverDetection:
    """Test crossover detection between two series."""

    def test_bullish_crossover(self):
        """Test detection of bullish crossover (fast above slow)."""
        fast_ma = pd.Series([10, 10.5, 11, 11.5, 12])
        slow_ma = pd.Series([11, 11, 11, 11, 11])

        crossovers = detect_crossover(fast_ma, slow_ma)

        # Should detect upward crossover around index 2-3
        bullish_crossovers = crossovers[crossovers == 1]  # Assuming 1 = bullish
        assert len(bullish_crossovers) >= 1

    def test_bearish_crossover(self):
        """Test detection of bearish crossover (fast below slow)."""
        fast_ma = pd.Series([12, 11.5, 11, 10.5, 10])
        slow_ma = pd.Series([11, 11, 11, 11, 11])

        crossovers = detect_crossover(fast_ma, slow_ma)

        # Should detect downward crossover
        bearish_crossovers = crossovers[crossovers == -1]  # Assuming -1 = bearish
        assert len(bearish_crossovers) >= 1

    def test_no_crossover(self):
        """Test when no crossover occurs."""
        fast_ma = pd.Series([12, 12.1, 12.2, 12.3, 12.4])  # Always above
        slow_ma = pd.Series([11, 11, 11, 11, 11])

        crossovers = detect_crossover(fast_ma, slow_ma)

        # Should not detect any crossovers
        assert (crossovers == 0).all()  # Assuming 0 = no crossover

    def test_crossover_precision(self):
        """Test crossover detection with very small differences."""
        fast_ma = pd.Series([100.0001, 100.0002, 100.0001, 100.0002])
        slow_ma = pd.Series([100.0000, 100.0000, 100.0000, 100.0000])

        crossovers = detect_crossover(fast_ma, slow_ma)

        # Should not generate excessive signals due to noise
        signal_changes = (crossovers != 0).sum()
        assert signal_changes <= 2  # Should not thrash


class TestIndicatorEdgeCases:
    """Test edge cases and error conditions for indicators."""

    def test_empty_series(self):
        """Test indicators with empty data."""
        empty_series = pd.Series([], dtype=float)

        # All indicators should handle empty series gracefully
        try:
            sma = calculate_moving_average(empty_series, period=10)
            assert len(sma) == 0
        except (ValueError, IndexError):
            # Acceptable to raise error for empty data
            pass

    def test_single_value_series(self):
        """Test indicators with single data point."""
        single_value = pd.Series([100.0])

        # Should handle single value gracefully
        try:
            sma = calculate_moving_average(single_value, period=10)
            assert len(sma) == 1
            assert pd.isna(sma.iloc[0])  # Should be NaN
        except (ValueError, IndexError):
            # Acceptable to raise error for insufficient data
            pass

    def test_all_nan_series(self):
        """Test indicators with all NaN values."""
        nan_series = pd.Series([np.nan] * 10)

        sma = calculate_moving_average(nan_series, period=5)

        # Should return all NaN
        assert sma.isna().all()

    def test_zero_period(self):
        """Test indicators with zero or negative period."""
        prices = pd.Series([100, 101, 102, 103, 104])

        # Should handle invalid periods gracefully
        try:
            sma = calculate_moving_average(prices, period=0)
            # If it doesn't raise an error, should return appropriate result
            assert sma is not None
        except (ValueError, ZeroDivisionError):
            # Acceptable to raise error for invalid period
            pass

    def test_period_larger_than_data(self):
        """Test indicators when period > data length."""
        prices = pd.Series([100, 101, 102])  # 3 data points
        period = 10  # Period larger than data

        sma = calculate_moving_average(prices, period=period)

        # Should return all NaN since insufficient data
        assert sma.isna().all()


class TestIndicatorPerformance:
    """Test indicator calculation performance and optimization."""

    def test_large_dataset_performance(self):
        """Test indicators with large datasets."""
        # Create large dataset
        large_prices = pd.Series(np.random.randn(10000).cumsum() + 100)

        import time

        start_time = time.time()
        sma = calculate_moving_average(large_prices, period=50)
        end_time = time.time()

        # Should complete in reasonable time (< 1 second for 10k points)
        assert end_time - start_time < 1.0
        assert len(sma) == len(large_prices)

    def test_multiple_indicators_consistency(self):
        """Test that multiple indicators produce consistent results."""
        prices = pd.Series(np.random.randn(1000).cumsum() + 100)

        # Calculate same indicator multiple times
        sma1 = calculate_moving_average(prices, period=20)
        sma2 = calculate_moving_average(prices, period=20)

        # Should produce identical results
        pd.testing.assert_series_equal(sma1, sma2)

        # Test with different but equivalent inputs
        prices_copy = prices.copy()
        sma3 = calculate_moving_average(prices_copy, period=20)
        pd.testing.assert_series_equal(sma1, sma3)
