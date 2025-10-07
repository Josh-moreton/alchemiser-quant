"""Business Unit: strategy | Status: current.

Indicator utility functions for safe calculation and error handling.

This module provides helper functions for safely calculating and retrieving technical indicator values.
"""

from __future__ import annotations

from collections.abc import Callable

import pandas as pd

from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.errors.exceptions import MarketDataError

logger = get_logger(__name__)

# Module-level constant for fallback value when indicator calculation fails
# RSI-neutral value (50.0) is used as a conservative fallback
FALLBACK_INDICATOR_VALUE = 50.0


def _extract_series(input_data: pd.Series | pd.DataFrame) -> pd.Series:
    """Extract a Series from DataFrame or return Series as-is.

    Args:
        input_data: Either a pandas Series or DataFrame containing market data.

    Returns:
        pd.Series: If DataFrame, returns 'Close' column if present, otherwise first
        numeric column. If no numeric columns exist, returns empty float Series.
        If Series, returns input unchanged.

    Note:
        Prefers 'Close' column as standard OHLC convention for price data.

    """
    if isinstance(input_data, pd.DataFrame):
        if "Close" in input_data.columns:
            return input_data["Close"]
        numeric_cols = input_data.select_dtypes(include=["number"]).columns
        return input_data[numeric_cols[0]] if len(numeric_cols) > 0 else pd.Series(dtype=float)
    return input_data


def _last_valid_value(series: pd.Series) -> float | None:
    """Get the last valid (non-NaN) value from a series.

    Args:
        series: Pandas Series potentially containing NaN values.

    Returns:
        float: Last non-NaN value as float, or None if series is empty or all NaN.

    Note:
        Returns float type to ensure consistent numeric handling for indicator values.

    """
    valid_series = series.dropna()
    return float(valid_series.iloc[-1]) if len(valid_series) > 0 else None


def _log_insufficient_data(func_name: str, series: pd.Series) -> None:
    """Log insufficient data scenarios with appropriate level.

    Args:
        func_name: Name of the indicator function that failed.
        series: The input series that was insufficient for calculation.

    Note:
        Uses debug level for < 2 data points (expected for warm-up period).
        Uses warning level for ≥ 2 points but no indicator results (unexpected).

    """
    if len(series) < 2:
        logger.debug(f"Insufficient data for indicator {func_name} (only {len(series)} points)")
    else:
        tail_repr = series.tail(1) if hasattr(series, "tail") else series
        logger.warning(f"Indicator {func_name} returned no results for data: {tail_repr}")


def _safe_repr(input_data: pd.Series | pd.DataFrame) -> pd.Series | pd.DataFrame | str:
    """Safely represent data for logging without raising exceptions.

    Args:
        input_data: Data to represent safely (typically pandas Series or DataFrame).

    Returns:
        Tail of input data (last row) if available, otherwise original input.
        On exception, returns string representation to prevent logging failures.

    Note:
        This function prioritizes logging success over perfect representation.
        Any exception during repr is caught to prevent logging failures.

    """
    try:
        return input_data.tail(1) if hasattr(input_data, "tail") else input_data
    except Exception as e:
        # Log the repr failure but return a safe string representation
        logger.debug(f"Exception in _safe_repr: {e}")
        return f"<Unable to represent data: {type(input_data).__name__}>"


def safe_get_indicator(
    data: pd.Series | pd.DataFrame,
    indicator_func: Callable[..., pd.Series],
    *args: int | float | str,
    **kwargs: int | float | str | bool,
) -> float:
    """Safely get an indicator value, logging exceptions and handling NaN values.

    Args:
        data: Market data as pandas Series or DataFrame. If DataFrame, 'Close' column
            is preferred, falling back to first numeric column.
        indicator_func: Callable that takes a Series and returns a Series of indicator values.
        *args: Positional arguments to pass to indicator_func (e.g., window sizes).
        **kwargs: Keyword arguments to pass to indicator_func (e.g., parameters).

    Returns:
        float: Last valid indicator value, or FALLBACK_INDICATOR_VALUE (50.0) on any error.

    Raises:
        No exceptions - all errors are caught and logged, returning fallback value.

    Note:
        This function is designed for maximum reliability, never raising exceptions.
        The fallback value (50.0) represents RSI-neutral, suitable for most indicators.

    Example:
        >>> import pandas as pd
        >>> from the_alchemiser.strategy_v2.indicators import TechnicalIndicators
        >>> data = pd.Series([100, 102, 101, 103, 105])
        >>> rsi_value = safe_get_indicator(data, TechnicalIndicators.rsi, window=14)
        >>> print(f"RSI: {rsi_value}")

    """
    if not callable(indicator_func):
        logger.error(f"indicator_func is not callable: {type(indicator_func)}")
        return FALLBACK_INDICATOR_VALUE

    try:
        series = _extract_series(data)
        if series.empty:
            logger.debug(
                f"Insufficient data for indicator {indicator_func.__name__} (empty series)"
            )
            return FALLBACK_INDICATOR_VALUE

        result = indicator_func(series, *args, **kwargs)

        # Validate result is a Series-like object
        if not hasattr(result, "iloc") or len(result) == 0:
            _log_insufficient_data(indicator_func.__name__, series)
            return FALLBACK_INDICATOR_VALUE

        last_value = _last_valid_value(result)
        if last_value is not None:
            return last_value

        # No valid values found
        tail_repr = series.tail(1) if hasattr(series, "tail") else series
        logger.debug(
            f"No valid values for indicator {indicator_func.__name__} on data: {tail_repr}"
        )
        return FALLBACK_INDICATOR_VALUE

    except MarketDataError as e:
        # Re-raise enhanced errors (these are domain-specific validation errors)
        logger.warning(f"Validation error in indicator {indicator_func.__name__}: {e}")
        raise
    except Exception as e:
        # Catch all other exceptions, log with context, and return fallback
        data_repr = _safe_repr(data)
        logger.error(
            f"Exception in safe_get_indicator for {indicator_func.__name__}: {e}",
            extra={
                "indicator_func": indicator_func.__name__,
                "error_type": type(e).__name__,
                "data_repr": str(data_repr),
            },
        )
        return FALLBACK_INDICATOR_VALUE
