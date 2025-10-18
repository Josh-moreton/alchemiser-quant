"""Business Unit: strategy | Status: current.

Comprehensive tests for indicator utility functions.

This module tests the safe indicator calculation and error handling utilities
including:
- safe_get_indicator: Safe indicator value extraction with error handling
- _extract_series: Series extraction from DataFrame or Series
- _last_valid_value: Last valid value retrieval from Series
- _log_insufficient_data: Logging for insufficient data scenarios
- _safe_repr: Safe representation for logging

Tests include unit tests for correctness, edge cases, and error handling.
"""

from __future__ import annotations

from unittest.mock import Mock, patch

import pandas as pd
import pytest

from the_alchemiser.shared.errors.exceptions import MarketDataError
from the_alchemiser.strategy_v2.indicators.indicator_utils import (
    FALLBACK_INDICATOR_VALUE,
    _extract_series,
    _last_valid_value,
    _log_insufficient_data,
    _safe_repr,
    safe_get_indicator,
)


@pytest.mark.unit
class TestSafeGetIndicator:
    """Test safe_get_indicator function."""

    def test_successful_indicator_calculation(self):
        """Test normal operation with valid data."""
        # Create test data
        data = pd.Series([100.0, 102.0, 101.0, 103.0, 105.0])

        # Mock indicator function that returns a Series
        def mock_indicator(series: pd.Series, window: int = 3) -> pd.Series:
            return series.rolling(window=window).mean()

        result = safe_get_indicator(data, mock_indicator, 3)

        # Should return the last valid value
        assert isinstance(result, float)
        assert result > 0  # Should be a valid positive number

    def test_handles_empty_series(self):
        """Test with empty pandas Series."""
        data = pd.Series(dtype=float)

        def mock_indicator(series: pd.Series) -> pd.Series:
            return series

        result = safe_get_indicator(data, mock_indicator)

        # Should return fallback value
        assert result == FALLBACK_INDICATOR_VALUE

    def test_handles_all_nan_values(self):
        """Test with Series containing only NaN values."""
        data = pd.Series([float("nan"), float("nan"), float("nan")])

        def mock_indicator(series: pd.Series) -> pd.Series:
            return pd.Series([float("nan"), float("nan"), float("nan")])

        result = safe_get_indicator(data, mock_indicator)

        # Should return fallback value when no valid values exist
        assert result == FALLBACK_INDICATOR_VALUE

    def test_handles_indicator_exception(self):
        """Test when indicator function raises exception."""
        data = pd.Series([100.0, 102.0, 101.0])

        def failing_indicator(series: pd.Series) -> pd.Series:
            raise ValueError("Indicator calculation failed")

        result = safe_get_indicator(data, failing_indicator)

        # Should return fallback value on exception
        assert result == FALLBACK_INDICATOR_VALUE

    def test_returns_fallback_on_error(self):
        """Test fallback value is returned on various error conditions."""
        data = pd.Series([100.0, 102.0, 101.0])

        # Test with indicator that returns empty result
        def empty_indicator(series: pd.Series) -> pd.Series:
            return pd.Series(dtype=float)

        result = safe_get_indicator(data, empty_indicator)
        assert result == FALLBACK_INDICATOR_VALUE

    def test_extracts_from_dataframe(self):
        """Test extraction of Close column from DataFrame."""
        data = pd.DataFrame(
            {
                "Open": [100.0, 101.0, 102.0],
                "High": [102.0, 103.0, 104.0],
                "Low": [99.0, 100.0, 101.0],
                "Close": [101.0, 102.0, 103.0],
            }
        )

        def mock_indicator(series: pd.Series) -> pd.Series:
            return series  # Return as-is

        result = safe_get_indicator(data, mock_indicator)

        # Should extract Close column and return last value
        assert isinstance(result, float)
        assert result == 103.0

    def test_deterministic_results(self):
        """Test same inputs produce same outputs."""
        data = pd.Series([100.0, 102.0, 101.0, 103.0, 105.0])

        def mock_indicator(series: pd.Series) -> pd.Series:
            return series.rolling(window=3).mean()

        result1 = safe_get_indicator(data, mock_indicator)
        result2 = safe_get_indicator(data, mock_indicator)

        # Results should be identical
        assert result1 == result2

    def test_with_string_args(self):
        """Test with string arguments to indicator function."""
        data = pd.Series([100.0, 102.0, 101.0, 103.0, 105.0])

        def mock_indicator(series: pd.Series, method: str = "mean") -> pd.Series:
            if method == "mean":
                return series.rolling(window=3).mean()
            return series

        result = safe_get_indicator(data, mock_indicator, "mean")

        assert isinstance(result, float)
        assert result > 0

    def test_with_kwargs(self):
        """Test with keyword arguments to indicator function."""
        data = pd.Series([100.0, 102.0, 101.0, 103.0, 105.0])

        def mock_indicator(series: pd.Series, window: int = 3, min_periods: int = 1) -> pd.Series:
            return series.rolling(window=window, min_periods=min_periods).mean()

        result = safe_get_indicator(data, mock_indicator, window=3, min_periods=2)

        assert isinstance(result, float)
        assert result > 0

    def test_handles_indicator_returning_non_series(self):
        """Test when indicator returns something other than Series."""
        data = pd.Series([100.0, 102.0, 101.0])

        def bad_indicator(series: pd.Series) -> list:
            return [1, 2, 3]  # Returns list instead of Series

        result = safe_get_indicator(data, bad_indicator)

        # Should return fallback value
        assert result == FALLBACK_INDICATOR_VALUE

    def test_extracts_last_valid_value_with_trailing_nans(self):
        """Test that last valid value is extracted even with trailing NaNs."""
        data = pd.Series([100.0, 102.0, 101.0, 103.0, 105.0])

        def indicator_with_trailing_nans(series: pd.Series) -> pd.Series:
            result = series.rolling(window=3).mean()
            # Add trailing NaN
            result.iloc[-1] = float("nan")
            return result

        result = safe_get_indicator(data, indicator_with_trailing_nans)

        # Should find the last valid value before the NaN
        assert isinstance(result, float)
        assert not pd.isna(result)

    def test_rejects_non_callable_indicator_func(self):
        """Test that non-callable indicator_func returns fallback."""
        data = pd.Series([100.0, 102.0, 101.0])

        # Pass a non-callable object
        result = safe_get_indicator(data, "not_a_function")  # type: ignore

        # Should return fallback value
        assert result == FALLBACK_INDICATOR_VALUE

    def test_reraises_enhanced_data_error(self):
        """Test that MarketDataError is re-raised with warning."""
        data = pd.Series([100.0, 102.0, 101.0])

        def indicator_with_validation_error(series: pd.Series) -> pd.Series:
            raise MarketDataError("Validation failed")

        # Should re-raise the exception
        with pytest.raises(MarketDataError, match="Validation failed"):
            safe_get_indicator(data, indicator_with_validation_error)


@pytest.mark.unit
class TestExtractSeries:
    """Test _extract_series helper."""

    def test_returns_series_unchanged(self):
        """Test Series is returned as-is."""
        series = pd.Series([100.0, 102.0, 101.0])
        result = _extract_series(series)

        pd.testing.assert_series_equal(result, series)

    def test_extracts_close_from_dataframe(self):
        """Test Close column extracted from DataFrame."""
        df = pd.DataFrame(
            {
                "Open": [100.0, 101.0, 102.0],
                "High": [102.0, 103.0, 104.0],
                "Close": [101.0, 102.0, 103.0],
            }
        )

        result = _extract_series(df)

        pd.testing.assert_series_equal(result, df["Close"])

    def test_falls_back_to_first_numeric(self):
        """Test fallback when no Close column."""
        df = pd.DataFrame(
            {
                "Price": [100.0, 101.0, 102.0],
                "Volume": [1000, 1100, 1200],
            }
        )

        result = _extract_series(df)

        # Should return first numeric column (Price)
        pd.testing.assert_series_equal(result, df["Price"])

    def test_returns_empty_series_when_no_numeric_columns(self):
        """Test empty series returned when DataFrame has no numeric columns."""
        df = pd.DataFrame(
            {
                "Symbol": ["AAPL", "GOOGL", "MSFT"],
                "Name": ["Apple", "Google", "Microsoft"],
            }
        )

        result = _extract_series(df)

        assert isinstance(result, pd.Series)
        assert len(result) == 0
        assert result.dtype == float

    def test_prefers_close_over_other_numeric_columns(self):
        """Test that Close column is preferred even when other numeric columns exist."""
        df = pd.DataFrame(
            {
                "Volume": [1000, 1100, 1200],
                "Close": [101.0, 102.0, 103.0],
                "Price": [100.0, 101.0, 102.0],
            }
        )

        result = _extract_series(df)

        # Should extract Close, not Volume or Price
        pd.testing.assert_series_equal(result, df["Close"])


@pytest.mark.unit
class TestLastValidValue:
    """Test _last_valid_value helper."""

    def test_returns_last_non_nan(self):
        """Test retrieval of last valid value."""
        series = pd.Series([100.0, 102.0, 101.0, 103.0, 105.0])
        result = _last_valid_value(series)

        assert result == 105.0

    def test_returns_none_on_empty(self):
        """Test None returned for empty series."""
        series = pd.Series(dtype=float)
        result = _last_valid_value(series)

        assert result is None

    def test_returns_none_when_all_nan(self):
        """Test None returned when all values are NaN."""
        series = pd.Series([float("nan"), float("nan"), float("nan")])
        result = _last_valid_value(series)

        assert result is None

    def test_skips_trailing_nans(self):
        """Test that trailing NaN values are skipped."""
        series = pd.Series([100.0, 102.0, 103.0, float("nan"), float("nan")])
        result = _last_valid_value(series)

        assert result == 103.0

    def test_returns_float_type(self):
        """Test that result is always float type."""
        series = pd.Series([100, 102, 103])  # Integer values
        result = _last_valid_value(series)

        assert isinstance(result, float)
        assert result == 103.0

    def test_handles_single_valid_value(self):
        """Test with single valid value."""
        series = pd.Series([float("nan"), 102.0, float("nan")])
        result = _last_valid_value(series)

        assert result == 102.0


@pytest.mark.unit
class TestLogInsufficientData:
    """Test _log_insufficient_data helper."""

    @patch("the_alchemiser.strategy_v2.indicators.indicator_utils.logger")
    def test_debug_log_for_minimal_data(self, mock_logger):
        """Test debug logging when series has < 2 points."""
        series = pd.Series([100.0])
        _log_insufficient_data("test_indicator", series)

        # Should call debug, not warning
        assert mock_logger.debug.called
        assert not mock_logger.warning.called
        assert "only 1 points" in mock_logger.debug.call_args[0][0]

    @patch("the_alchemiser.strategy_v2.indicators.indicator_utils.logger")
    def test_debug_log_for_empty_series(self, mock_logger):
        """Test debug logging for empty series."""
        series = pd.Series(dtype=float)
        _log_insufficient_data("test_indicator", series)

        assert mock_logger.debug.called
        assert "only 0 points" in mock_logger.debug.call_args[0][0]

    @patch("the_alchemiser.strategy_v2.indicators.indicator_utils.logger")
    def test_warning_log_for_sufficient_but_failed_data(self, mock_logger):
        """Test warning logging when series has ≥2 points but indicator failed."""
        series = pd.Series([100.0, 102.0, 101.0])
        _log_insufficient_data("test_indicator", series)

        # Should call warning, not debug
        assert mock_logger.warning.called
        assert not mock_logger.debug.called
        assert "returned no results" in mock_logger.warning.call_args[0][0]


@pytest.mark.unit
class TestSafeRepr:
    """Test _safe_repr helper."""

    def test_returns_tail_for_series(self):
        """Test that tail is returned for Series."""
        series = pd.Series([100.0, 102.0, 101.0, 103.0, 105.0])
        result = _safe_repr(series)

        # Should return last element as Series
        assert isinstance(result, pd.Series)
        assert len(result) == 1
        assert result.iloc[0] == 105.0

    def test_returns_tail_for_dataframe(self):
        """Test that tail is returned for DataFrame."""
        df = pd.DataFrame(
            {
                "Close": [100.0, 102.0, 103.0],
                "Volume": [1000, 1100, 1200],
            }
        )
        result = _safe_repr(df)

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 1
        assert result["Close"].iloc[0] == 103.0

    def test_returns_input_on_exception(self):
        """Test that safe string is returned on exception."""
        # Create mock object that raises exception on tail()
        mock_obj = Mock()
        mock_obj.tail.side_effect = RuntimeError("Cannot get tail")

        result = _safe_repr(mock_obj)

        # Should return a safe string representation
        assert isinstance(result, str)
        assert "Unable to represent data" in result

    def test_returns_input_for_object_without_tail(self):
        """Test returns input for objects without tail attribute."""
        simple_obj = "not a pandas object"
        result = _safe_repr(simple_obj)

        # Should return input unchanged
        assert result == simple_obj


@pytest.mark.unit
class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_safe_get_indicator_with_dataframe_no_close(self):
        """Test safe_get_indicator with DataFrame lacking Close column."""
        df = pd.DataFrame(
            {
                "Price": [100.0, 102.0, 103.0],
                "Volume": [1000, 1100, 1200],
            }
        )

        def mock_indicator(series: pd.Series) -> pd.Series:
            return series

        result = safe_get_indicator(df, mock_indicator)

        # Should use first numeric column (Price)
        assert result == 103.0

    def test_safe_get_indicator_with_mixed_nan_values(self):
        """Test with Series containing mixed NaN and valid values."""
        data = pd.Series([100.0, float("nan"), 102.0, float("nan"), 103.0])

        def mock_indicator(series: pd.Series) -> pd.Series:
            return series  # Return as-is

        result = safe_get_indicator(data, mock_indicator)

        # Should return last valid value
        assert result == 103.0

    def test_safe_get_indicator_with_zero_values(self):
        """Test that zero values are treated as valid."""
        data = pd.Series([100.0, 0.0, 102.0, 0.0, 103.0])

        def mock_indicator(series: pd.Series) -> pd.Series:
            return series

        result = safe_get_indicator(data, mock_indicator)

        # Should return last value (103.0), zeros are valid
        assert result == 103.0

    def test_safe_get_indicator_with_negative_values(self):
        """Test that negative values are handled correctly."""
        data = pd.Series([100.0, -50.0, 102.0, -25.0, 103.0])

        def mock_indicator(series: pd.Series) -> pd.Series:
            return series

        result = safe_get_indicator(data, mock_indicator)

        # Should return last value
        assert result == 103.0

    def test_extract_series_with_single_numeric_column(self):
        """Test extraction with DataFrame having single numeric column."""
        df = pd.DataFrame(
            {
                "Symbol": ["AAPL", "GOOGL", "MSFT"],
                "Price": [100.0, 101.0, 102.0],
            }
        )

        result = _extract_series(df)

        pd.testing.assert_series_equal(result, df["Price"])


@pytest.mark.unit
class TestDeterminism:
    """Test that utility functions produce deterministic results."""

    def test_safe_get_indicator_deterministic(self):
        """Test safe_get_indicator produces same results for same input."""
        data = pd.Series([100.0, 102.0, 101.0, 103.0, 105.0])

        def mock_indicator(series: pd.Series) -> pd.Series:
            return series.rolling(window=3).mean()

        results = [safe_get_indicator(data, mock_indicator) for _ in range(5)]

        # All results should be identical
        assert len(set(results)) == 1

    def test_extract_series_deterministic(self):
        """Test _extract_series produces same results for same input."""
        df = pd.DataFrame(
            {
                "Close": [100.0, 101.0, 102.0],
                "Volume": [1000, 1100, 1200],
            }
        )

        results = [_extract_series(df) for _ in range(5)]

        # All results should be identical
        for i in range(1, len(results)):
            pd.testing.assert_series_equal(results[0], results[i])

    def test_last_valid_value_deterministic(self):
        """Test _last_valid_value produces same results for same input."""
        series = pd.Series([100.0, float("nan"), 102.0, 103.0])

        results = [_last_valid_value(series) for _ in range(5)]

        # All results should be identical
        assert len(set(results)) == 1
        assert results[0] == 103.0


@pytest.mark.unit
class TestLoggingBehavior:
    """Test logging behavior across different scenarios."""

    @patch("the_alchemiser.strategy_v2.indicators.indicator_utils.logger")
    def test_empty_series_logs_debug(self, mock_logger):
        """Test that empty series triggers debug logging."""
        data = pd.Series(dtype=float)

        def mock_indicator(series: pd.Series) -> pd.Series:
            return series

        safe_get_indicator(data, mock_indicator)

        assert mock_logger.debug.called
        debug_message = mock_logger.debug.call_args[0][0]
        assert "empty series" in debug_message.lower()

    @patch("the_alchemiser.strategy_v2.indicators.indicator_utils.logger")
    def test_exception_logs_error(self, mock_logger):
        """Test that exceptions trigger error logging."""
        data = pd.Series([100.0, 102.0])

        def failing_indicator(series: pd.Series) -> pd.Series:
            raise ValueError("Test error")

        safe_get_indicator(data, failing_indicator)

        assert mock_logger.error.called
        error_message = mock_logger.error.call_args[0][0]
        assert "exception" in error_message.lower()

    @patch("the_alchemiser.strategy_v2.indicators.indicator_utils.logger")
    def test_no_valid_values_logs_debug(self, mock_logger):
        """Test that no valid values triggers debug logging."""
        data = pd.Series([100.0, 102.0])

        def nan_indicator(series: pd.Series) -> pd.Series:
            return pd.Series([float("nan"), float("nan")])

        safe_get_indicator(data, nan_indicator)

        # Should have called debug for "no valid values"
        debug_calls = [call[0][0] for call in mock_logger.debug.call_args_list]
        assert any("no valid values" in msg.lower() for msg in debug_calls)
