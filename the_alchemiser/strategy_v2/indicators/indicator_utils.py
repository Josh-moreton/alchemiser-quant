"""Business Unit: strategy | Status: current.

Indicator utility functions for safe calculation and error handling.

This module provides helper functions for safely calculating and retrieving technical indicator values.
It handles edge cases like empty data, NaN values, and exceptions gracefully, always returning
valid numeric values with appropriate fallbacks for use in trading strategies.
"""

from __future__ import annotations

from collections.abc import Callable

import pandas as pd

from the_alchemiser.shared.errors import EnhancedDataError
from the_alchemiser.shared.logging import get_logger

logger = get_logger(__name__)

# Fallback value for indicators when data is insufficient or invalid
# 50.0 represents a neutral value suitable for RSI (0-100 scale) and similar bounded indicators
# For unbounded indicators, this may need adjustment based on typical ranges
INDICATOR_FALLBACK_VALUE = 50.0


def _extract_series(input_data: pd.Series | pd.DataFrame) -> pd.Series:
    """Extract a Series from DataFrame or return Series as-is.
    
    Args:
        input_data: Either a pandas Series or DataFrame containing numeric data
        
    Returns:
        pd.Series: Extracted series from DataFrame (prefers 'Close' column) or the input Series
        Returns empty Series with float dtype if no numeric columns found
        
    Examples:
        >>> df = pd.DataFrame({'Close': [100, 101, 102]})
        >>> series = _extract_series(df)
        >>> isinstance(series, pd.Series)
        True

    """
    if isinstance(input_data, pd.DataFrame):
        if "Close" in input_data.columns:
            return input_data["Close"]
        numeric_cols = input_data.select_dtypes(include=["number"]).columns
        if len(numeric_cols) > 0:
            return input_data[numeric_cols[0]]
        return pd.Series(dtype=float)
    return input_data


def _last_valid_value(series: pd.Series) -> float | None:
    """Get the last valid (non-NaN) value from a series.
    
    Args:
        series: pandas Series to extract value from
        
    Returns:
        float | None: The last valid value as a float, or None if no valid values exist
        
    Examples:
        >>> series = pd.Series([1.0, 2.0, float('nan'), 3.0])
        >>> _last_valid_value(series)
        3.0
        >>> empty = pd.Series([float('nan')])
        >>> _last_valid_value(empty) is None
        True

    """
    valid_series = series.dropna()
    if len(valid_series) > 0:
        return float(valid_series.iloc[-1])
    return None


def _log_insufficient_data(func_name: str, series: pd.Series) -> None:
    """Log insufficient data scenarios with appropriate level.
    
    Uses debug level for minimal data (< 2 points) and warning for cases where
    indicator computation returned no results despite having sufficient input data.
    
    Args:
        func_name: Name of the indicator function being called
        series: Input series that had insufficient data
        
    Examples:
        >>> series = pd.Series([1.0])
        >>> _log_insufficient_data('rsi', series)  # Logs at debug level

    """
    if len(series) < 2:
        logger.debug(
            "Insufficient data for indicator",
            indicator=func_name,
            data_points=len(series)
        )
    else:
        tail_repr = _safe_tail_repr(series)
        logger.warning(
            "Indicator returned no results despite sufficient data",
            indicator=func_name,
            data_sample=tail_repr
        )


def _safe_tail_repr(input_data: pd.Series | pd.DataFrame) -> str:
    """Safely represent last element of data for logging without raising exceptions.
    
    Args:
        input_data: pandas Series or DataFrame to get representation from
        
    Returns:
        str: String representation of last element, or fallback message if extraction fails
        
    Examples:
        >>> series = pd.Series([1, 2, 3])
        >>> repr_str = _safe_tail_repr(series)
        >>> '3' in repr_str
        True

    """
    try:
        if hasattr(input_data, "tail"):
            return str(input_data.tail(1))
        return str(input_data)
    except Exception as e:
        logger.debug("Failed to create data representation for logging", error=str(e))
        return "<data repr unavailable>"


def safe_get_indicator(
    data: pd.Series | pd.DataFrame,
    indicator_func: Callable[..., pd.Series],
    *args: int | float | str,
    **kwargs: int | float | str | bool,
) -> float:
    """Safely get an indicator value, logging exceptions and handling NaN values.
    
    This function provides a robust wrapper around indicator calculation functions,
    handling edge cases and ensuring a valid numeric value is always returned.
    
    Args:
        data: Input price data as either a pandas Series or DataFrame
        indicator_func: Function that computes the indicator, must return pd.Series
        *args: Positional arguments to pass to the indicator function
        **kwargs: Keyword arguments to pass to the indicator function
        
    Returns:
        float: The last valid indicator value, or INDICATOR_FALLBACK_VALUE (50.0)
            if data is insufficient or computation fails
            
    Raises:
        EnhancedDataError: If indicator computation fails due to data issues
        
    Examples:
        >>> import pandas as pd
        >>> from the_alchemiser.strategy_v2.indicators.indicators import TechnicalIndicators
        >>> prices = pd.Series([100, 102, 101, 103, 105])
        >>> rsi = safe_get_indicator(prices, TechnicalIndicators.rsi, 14)
        >>> isinstance(rsi, float)
        True
        
    Notes:
        - Always returns a float value (never None or NaN)
        - Fallback value of 50.0 is suitable for RSI and similar 0-100 bounded indicators
        - For unbounded indicators, consider the appropriateness of the fallback value

    """
    try:
        series = _extract_series(data)
        if series.empty:
            logger.debug(
                "Insufficient data for indicator (empty series)",
                indicator=indicator_func.__name__
            )
            return INDICATOR_FALLBACK_VALUE

        result = indicator_func(series, *args, **kwargs)
        
        # Validate result is a pandas Series with data
        if not isinstance(result, pd.Series) or len(result) == 0:
            _log_insufficient_data(indicator_func.__name__, series)
            return INDICATOR_FALLBACK_VALUE

        last_value = _last_valid_value(result)
        if last_value is not None:
            return last_value

        # No valid values found in result
        tail_repr = _safe_tail_repr(series)
        logger.debug(
            "No valid values for indicator",
            indicator=indicator_func.__name__,
            data_sample=tail_repr
        )
        return INDICATOR_FALLBACK_VALUE

    except (ValueError, KeyError, IndexError, TypeError) as e:
        # Data-related errors that prevent indicator calculation
        data_repr = _safe_tail_repr(data)
        logger.error(
            "Data error in indicator calculation",
            indicator=indicator_func.__name__,
            error_type=type(e).__name__,
            error_message=str(e),
            data_sample=data_repr
        )
        raise EnhancedDataError(
            f"Failed to calculate indicator {indicator_func.__name__}: {e}",
            context={
                "indicator": indicator_func.__name__,
                "error_type": type(e).__name__,
                "args": str(args),
                "kwargs": str(kwargs),
            }
        ) from e
    except Exception as e:
        # Unexpected errors - log and return fallback for resilience
        data_repr = _safe_tail_repr(data)
        logger.error(
            "Unexpected error in indicator calculation",
            indicator=indicator_func.__name__,
            error_type=type(e).__name__,
            error_message=str(e),
            data_sample=data_repr
        )
        # Return fallback instead of raising for operational resilience
        # but log at error level for investigation
        return INDICATOR_FALLBACK_VALUE
