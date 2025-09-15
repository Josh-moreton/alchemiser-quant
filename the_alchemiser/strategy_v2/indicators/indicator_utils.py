"""Business Unit: strategy | Status: current.

Indicator utility functions for safe calculation and error handling.

This module provides helper functions for safely calculating and retrieving technical indicator values.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

import pandas as pd


def safe_get_indicator(
    data: pd.Series | pd.DataFrame,
    indicator_func: Callable[..., pd.Series],
    *args: Any,
    **kwargs: Any,
) -> float:
    """Safely get an indicator value, logging exceptions and handling NaN values.

    This function attempts to calculate an indicator and returns the last valid
    numeric value from the resulting series. It includes robust error handling
    and fallbacks.

    Args:
        data (pd.Series | pd.DataFrame): The input data for the indicator function. If a
            DataFrame is provided, the 'Close' column will be used when available.
        indicator_func (callable): The function to call to calculate the indicator.
        *args: Positional arguments to pass to the indicator function.
        **kwargs: Keyword arguments to pass to the indicator function.

    Returns:
        float: The calculated indicator value, or a fallback value (50.0) if an
               error occurs or no valid data is found.

    """
    
    def _extract_series_from_data(input_data: pd.Series | pd.DataFrame) -> pd.Series:
        """Extract a pandas Series from the input data."""
        if isinstance(input_data, pd.DataFrame):
            if "Close" in input_data.columns:
                return input_data["Close"]
            # Use the first numeric column as a fallback
            numeric_cols = input_data.select_dtypes(include=["number"]).columns
            return input_data[numeric_cols[0]] if len(numeric_cols) > 0 else pd.Series(dtype=float)
        return input_data

    def _get_last_valid_value(result_series: pd.Series) -> float | None:
        """Get the last valid (non-NaN) value from a series."""
        if len(result_series) == 0:
            return None
        
        last_value = result_series.iloc[-1]
        if not pd.isna(last_value):
            return float(last_value)
        
        # Find the last non-NaN value
        valid_values = result_series.dropna()
        if len(valid_values) > 0:
            return float(valid_values.iloc[-1])
        
        return None

    def _log_insufficient_data(func_name: str, series: pd.Series) -> None:
        """Log insufficient data conditions."""
        if len(series) < 2:
            logging.debug(f"Insufficient data for indicator {func_name} (only {len(series)} points)")
        else:
            tail_repr = series.tail(1) if hasattr(series, "tail") else series
            logging.warning(f"Indicator {func_name} returned no results for data: {tail_repr}")

    def _get_data_repr(input_data: pd.Series | pd.DataFrame) -> Any:
        """Get a safe representation of data for logging."""
        try:
            return input_data.tail(1) if hasattr(input_data, "tail") else input_data
        except Exception:
            return input_data

    FALLBACK_VALUE = 50.0
    
    try:
        series = _extract_series_from_data(data)
        
        if series.empty:
            logging.debug(f"Insufficient data for indicator {indicator_func.__name__} (empty series)")
            return FALLBACK_VALUE

        result = indicator_func(series, *args, **kwargs)
        
        if not hasattr(result, "iloc") or len(result) == 0:
            _log_insufficient_data(indicator_func.__name__, series)
            return FALLBACK_VALUE
        
        last_valid = _get_last_valid_value(result)
        if last_valid is not None:
            return last_valid
        
        # No valid values found
        tail_repr = series.tail(1) if hasattr(series, "tail") else series
        logging.debug(f"No valid values for indicator {indicator_func.__name__} on data: {tail_repr}")
        return FALLBACK_VALUE

    except Exception as e:
        data_repr = _get_data_repr(data)
        logging.error(f"Exception in safe_get_indicator for {indicator_func.__name__}: {e}\nData: {data_repr}")
        return FALLBACK_VALUE
