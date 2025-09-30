"""Business Unit: strategy | Status: current.

Indicator utility functions for safe calculation and error handling.

This module provides helper functions for safely calculating and retrieving technical indicator values.
"""

from __future__ import annotations

from collections.abc import Callable

import pandas as pd

from the_alchemiser.shared.logging.logging_utils import get_logger

logger = get_logger(__name__)


def _extract_series(input_data: pd.Series | pd.DataFrame) -> pd.Series:
    """Extract a Series from DataFrame or return Series as-is."""
    if isinstance(input_data, pd.DataFrame):
        if "Close" in input_data.columns:
            return input_data["Close"]
        numeric_cols = input_data.select_dtypes(include=["number"]).columns
        return input_data[numeric_cols[0]] if len(numeric_cols) > 0 else pd.Series(dtype=float)
    return input_data


def _last_valid_value(series: pd.Series) -> float | None:
    """Get the last valid (non-NaN) value from a series."""
    valid_series = series.dropna()
    return float(valid_series.iloc[-1]) if len(valid_series) > 0 else None


def _log_insufficient_data(func_name: str, series: pd.Series) -> None:
    """Log insufficient data scenarios with appropriate level."""
    if len(series) < 2:
        logger.debug(f"Insufficient data for indicator {func_name} (only {len(series)} points)")
    else:
        tail_repr = series.tail(1) if hasattr(series, "tail") else series
        logger.warning(f"Indicator {func_name} returned no results for data: {tail_repr}")


def _safe_repr(input_data: pd.Series | pd.DataFrame) -> pd.Series | pd.DataFrame:
    """Safely represent data for logging without raising exceptions."""
    try:
        return input_data.tail(1) if hasattr(input_data, "tail") else input_data
    except Exception:
        return input_data


def safe_get_indicator(
    data: pd.Series | pd.DataFrame,
    indicator_func: Callable[..., pd.Series],
    *args: int | float | str,
    **kwargs: int | float | str | bool,
) -> float:
    """Safely get an indicator value, logging exceptions and handling NaN values."""
    FALLBACK_VALUE = 50.0

    try:
        series = _extract_series(data)
        if series.empty:
            logger.debug(
                f"Insufficient data for indicator {indicator_func.__name__} (empty series)"
            )
            return FALLBACK_VALUE

        result = indicator_func(series, *args, **kwargs)
        if not hasattr(result, "iloc") or len(result) == 0:
            _log_insufficient_data(indicator_func.__name__, series)
            return FALLBACK_VALUE

        last_value = _last_valid_value(result)
        if last_value is not None:
            return last_value

        # No valid values found
        tail_repr = series.tail(1) if hasattr(series, "tail") else series
        logger.debug(
            f"No valid values for indicator {indicator_func.__name__} on data: {tail_repr}"
        )
        return FALLBACK_VALUE

    except Exception as e:
        data_repr = _safe_repr(data)
        logger.error(
            f"Exception in safe_get_indicator for {indicator_func.__name__}: {e}\nData: {data_repr}"
        )
        return FALLBACK_VALUE
