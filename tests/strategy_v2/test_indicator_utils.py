"""Business Unit: strategy | Status: current.

Unit tests for indicator_utils module.

Tests cover safe indicator value extraction with edge cases including:
- Empty data handling
- NaN value handling  
- DataFrame vs Series input
- Exception handling and error types
- Fallback value behavior
"""

from __future__ import annotations

import pandas as pd
import pytest

from the_alchemiser.shared.errors import EnhancedDataError
from the_alchemiser.strategy_v2.indicators.indicator_utils import (
    INDICATOR_FALLBACK_VALUE,
    _extract_series,
    _last_valid_value,
    _log_insufficient_data,
    _safe_tail_repr,
    safe_get_indicator,
)


class TestExtractSeries:
    """Tests for _extract_series helper function."""

    def test_extract_series_from_series(self) -> None:
        """Test that Series input is returned unchanged."""
        series = pd.Series([100.0, 101.0, 102.0])
        result = _extract_series(series)
        assert isinstance(result, pd.Series)
        pd.testing.assert_series_equal(result, series)

    def test_extract_series_from_dataframe_with_close(self) -> None:
        """Test extraction of Close column from DataFrame."""
        df = pd.DataFrame({
            "Close": [100.0, 101.0, 102.0],
            "Open": [99.0, 100.0, 101.0],
        })
        result = _extract_series(df)
        assert isinstance(result, pd.Series)
        pd.testing.assert_series_equal(result, df["Close"])

    def test_extract_series_from_dataframe_without_close(self) -> None:
        """Test extraction of first numeric column when Close is absent."""
        df = pd.DataFrame({
            "Price": [100.0, 101.0, 102.0],
            "Volume": [1000, 1100, 1200],
        })
        result = _extract_series(df)
        assert isinstance(result, pd.Series)
        # Should get first numeric column (Price)
        assert result.equals(df["Price"])

    def test_extract_series_from_empty_dataframe(self) -> None:
        """Test handling of DataFrame with no numeric columns."""
        df = pd.DataFrame({"Symbol": ["AAPL", "GOOGL"]})
        result = _extract_series(df)
        assert isinstance(result, pd.Series)
        assert result.empty
        assert result.dtype == float

    def test_extract_series_from_empty_series(self) -> None:
        """Test handling of empty Series."""
        series = pd.Series([], dtype=float)
        result = _extract_series(series)
        assert isinstance(result, pd.Series)
        assert result.empty


class TestLastValidValue:
    """Tests for _last_valid_value helper function."""

    def test_last_valid_value_all_valid(self) -> None:
        """Test extraction from series with all valid values."""
        series = pd.Series([1.0, 2.0, 3.0, 4.0])
        result = _last_valid_value(series)
        assert result == 4.0

    def test_last_valid_value_with_trailing_nan(self) -> None:
        """Test extraction when last values are NaN."""
        series = pd.Series([1.0, 2.0, 3.0, float("nan"), float("nan")])
        result = _last_valid_value(series)
        assert result == 3.0

    def test_last_valid_value_with_leading_nan(self) -> None:
        """Test extraction with leading NaN values."""
        series = pd.Series([float("nan"), float("nan"), 1.0, 2.0])
        result = _last_valid_value(series)
        assert result == 2.0

    def test_last_valid_value_all_nan(self) -> None:
        """Test handling of series with all NaN values."""
        series = pd.Series([float("nan"), float("nan"), float("nan")])
        result = _last_valid_value(series)
        assert result is None

    def test_last_valid_value_empty_series(self) -> None:
        """Test handling of empty series."""
        series = pd.Series([], dtype=float)
        result = _last_valid_value(series)
        assert result is None

    def test_last_valid_value_single_value(self) -> None:
        """Test extraction from single-value series."""
        series = pd.Series([42.0])
        result = _last_valid_value(series)
        assert result == 42.0


class TestSafeTailRepr:
    """Tests for _safe_tail_repr helper function."""

    def test_safe_tail_repr_series(self) -> None:
        """Test string representation of Series."""
        series = pd.Series([1, 2, 3, 4, 5])
        result = _safe_tail_repr(series)
        assert isinstance(result, str)
        assert "5" in result  # Should contain last value

    def test_safe_tail_repr_dataframe(self) -> None:
        """Test string representation of DataFrame."""
        df = pd.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]})
        result = _safe_tail_repr(df)
        assert isinstance(result, str)
        # Should contain last row values
        assert "3" in result or "6" in result

    def test_safe_tail_repr_empty_series(self) -> None:
        """Test handling of empty series."""
        series = pd.Series([], dtype=float)
        result = _safe_tail_repr(series)
        assert isinstance(result, str)
        # Should not raise exception

    def test_safe_tail_repr_no_tail_method(self) -> None:
        """Test handling of objects without tail method."""
        # Mock object without tail - simulating non-pandas input
        obj = "test_string"
        result = _safe_tail_repr(obj)
        assert isinstance(result, str)
        assert result == "test_string"


class TestLogInsufficientData:
    """Tests for _log_insufficient_data helper function."""

    def test_log_insufficient_data_minimal(self) -> None:
        """Test debug logging for minimal data (< 2 points)."""
        series = pd.Series([1.0])
        # Should not raise exception
        _log_insufficient_data("test_indicator", series)

    def test_log_insufficient_data_sufficient(self) -> None:
        """Test warning logging when indicator returns no results despite sufficient data."""
        series = pd.Series([1.0, 2.0, 3.0])
        # Should not raise exception
        _log_insufficient_data("test_indicator", series)


class TestSafeGetIndicator:
    """Tests for safe_get_indicator main function."""

    def test_safe_get_indicator_valid_result(self) -> None:
        """Test successful indicator calculation."""
        # Simple moving average indicator
        def simple_ma(data: pd.Series, window: int = 3) -> pd.Series:
            return data.rolling(window=window).mean()

        prices = pd.Series([100.0, 101.0, 102.0, 103.0, 104.0])
        result = safe_get_indicator(prices, simple_ma, 3)
        
        assert isinstance(result, float)
        assert result > 0
        # Last value should be around 103.0 (average of 102, 103, 104)
        assert 102.5 < result < 103.5

    def test_safe_get_indicator_empty_series(self) -> None:
        """Test handling of empty input series."""
        def dummy_indicator(data: pd.Series) -> pd.Series:
            return data * 2

        empty_series = pd.Series([], dtype=float)
        result = safe_get_indicator(empty_series, dummy_indicator)
        
        assert result == INDICATOR_FALLBACK_VALUE

    def test_safe_get_indicator_dataframe_input(self) -> None:
        """Test handling of DataFrame input."""
        def simple_ma(data: pd.Series, window: int = 2) -> pd.Series:
            return data.rolling(window=window).mean()

        df = pd.DataFrame({
            "Close": [100.0, 102.0, 104.0],
            "Open": [99.0, 101.0, 103.0],
        })
        result = safe_get_indicator(df, simple_ma, 2)
        
        assert isinstance(result, float)
        assert result > 0

    def test_safe_get_indicator_all_nan_result(self) -> None:
        """Test handling when indicator returns all NaN values."""
        def nan_indicator(data: pd.Series) -> pd.Series:
            return pd.Series([float("nan")] * len(data))

        prices = pd.Series([100.0, 101.0, 102.0])
        result = safe_get_indicator(prices, nan_indicator)
        
        assert result == INDICATOR_FALLBACK_VALUE

    def test_safe_get_indicator_empty_result(self) -> None:
        """Test handling when indicator returns empty series."""
        def empty_indicator(data: pd.Series) -> pd.Series:
            return pd.Series([], dtype=float)

        prices = pd.Series([100.0, 101.0, 102.0])
        result = safe_get_indicator(prices, empty_indicator)
        
        assert result == INDICATOR_FALLBACK_VALUE

    def test_safe_get_indicator_with_args_kwargs(self) -> None:
        """Test passing arguments to indicator function."""
        def parameterized_indicator(
            data: pd.Series, 
            multiplier: int, 
            offset: float = 0.0
        ) -> pd.Series:
            return data * multiplier + offset

        prices = pd.Series([100.0, 101.0, 102.0])
        result = safe_get_indicator(prices, parameterized_indicator, 2, offset=10.0)
        
        assert isinstance(result, float)
        # Last value: 102 * 2 + 10 = 214
        assert result == 214.0

    def test_safe_get_indicator_value_error_raises_enhanced_error(self) -> None:
        """Test that ValueError during calculation raises EnhancedDataError."""
        def failing_indicator(data: pd.Series) -> pd.Series:
            raise ValueError("Invalid data for calculation")

        prices = pd.Series([100.0, 101.0, 102.0])
        
        with pytest.raises(EnhancedDataError) as exc_info:
            safe_get_indicator(prices, failing_indicator)
        
        assert "Failed to calculate indicator" in str(exc_info.value)

    def test_safe_get_indicator_key_error_raises_enhanced_error(self) -> None:
        """Test that KeyError during calculation raises EnhancedDataError."""
        def failing_indicator(data: pd.Series) -> pd.Series:
            raise KeyError("Missing required data key")

        prices = pd.Series([100.0, 101.0, 102.0])
        
        with pytest.raises(EnhancedDataError) as exc_info:
            safe_get_indicator(prices, failing_indicator)
        
        assert "Failed to calculate indicator" in str(exc_info.value)

    def test_safe_get_indicator_unexpected_error_returns_fallback(self) -> None:
        """Test that unexpected errors return fallback value instead of raising."""
        def failing_indicator(data: pd.Series) -> pd.Series:
            # Simulate unexpected runtime error
            raise RuntimeError("Unexpected calculation error")

        prices = pd.Series([100.0, 101.0, 102.0])
        result = safe_get_indicator(prices, failing_indicator)
        
        # Should return fallback instead of raising
        assert result == INDICATOR_FALLBACK_VALUE

    def test_safe_get_indicator_non_series_result_returns_fallback(self) -> None:
        """Test handling when indicator returns non-Series type."""
        def bad_indicator(data: pd.Series) -> pd.Series:
            # Intentionally return wrong type to test error handling
            return 42  # pyright: ignore[reportReturnType]

        prices = pd.Series([100.0, 101.0, 102.0])
        result = safe_get_indicator(prices, bad_indicator)
        
        assert result == INDICATOR_FALLBACK_VALUE

    def test_safe_get_indicator_preserves_last_valid_with_nans(self) -> None:
        """Test that function correctly extracts last valid value when trailing NaNs exist."""
        def indicator_with_nans(data: pd.Series, window: int = 2) -> pd.Series:
            # Calculate rolling mean, last value may be NaN
            result = data.rolling(window=window).mean()
            # Explicitly add trailing NaN
            return pd.concat([result, pd.Series([float("nan")])])

        prices = pd.Series([100.0, 102.0, 104.0])
        result = safe_get_indicator(prices, indicator_with_nans, 2)
        
        # Should get last valid value (103.0) not the trailing NaN
        assert result == 103.0


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_single_value_series(self) -> None:
        """Test handling of single-value input."""
        def identity_indicator(data: pd.Series) -> pd.Series:
            return data

        prices = pd.Series([100.0])
        result = safe_get_indicator(prices, identity_indicator)
        
        assert result == 100.0

    def test_large_series_performance(self) -> None:
        """Test handling of large data series."""
        def simple_mean(data: pd.Series) -> pd.Series:
            return pd.Series([data.mean()] * len(data))

        # Create large series
        large_prices = pd.Series(range(10000), dtype=float)
        result = safe_get_indicator(large_prices, simple_mean)
        
        assert isinstance(result, float)
        assert result > 0

    def test_fallback_value_constant(self) -> None:
        """Test that fallback value is the expected constant."""
        assert INDICATOR_FALLBACK_VALUE == 50.0
