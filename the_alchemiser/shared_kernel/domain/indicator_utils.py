"""Business Unit: utilities; Status: current.

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
    try:
        # Accept DataFrame inputs by extracting Close series when present
        series: pd.Series
        if isinstance(data, pd.DataFrame):
            if "Close" in data.columns:
                series = data["Close"]
            else:
                # Use the first numeric column as a fallback
                numeric_cols = data.select_dtypes(include=["number"]).columns
                series = data[numeric_cols[0]] if len(numeric_cols) > 0 else pd.Series(dtype=float)
        else:
            series = data

        if series.empty:
            logging.debug(
                f"Insufficient data for indicator {indicator_func.__name__} (empty series)"
            )
            return 50.0

        result = indicator_func(series, *args, **kwargs)
        if hasattr(result, "iloc") and len(result) > 0:
            value = result.iloc[-1]
            # Check if value is NaN - if so, try to find the last valid value
            if pd.isna(value):
                # Find the last non-NaN value
                valid_values = result.dropna()
                if len(valid_values) > 0:
                    value = valid_values.iloc[-1]
                else:
                    # Debug level for insufficient data - this is expected with limited historical data
                    tail_repr = series.tail(1) if hasattr(series, "tail") else series
                    logging.debug(
                        f"No valid values for indicator {indicator_func.__name__} on data: {tail_repr}"
                    )
                    return 50.0  # Fallback only if no valid values
            return float(value)
        # Check if it's due to insufficient data (common with recent dates)
        if len(series) < 2:
            logging.debug(
                f"Insufficient data for indicator {indicator_func.__name__} (only {len(series)} points)"
            )
        else:
            tail_repr = series.tail(1) if hasattr(series, "tail") else series
            logging.warning(
                f"Indicator {indicator_func.__name__} returned no results for data: {tail_repr}"
            )
        return 50.0
    except Exception as e:
        try:
            tail_repr = data.tail(1) if hasattr(data, "tail") else data
        except Exception:
            tail_repr = data
        logging.error(
            f"Exception in safe_get_indicator for {indicator_func.__name__}: {e}\nData: {tail_repr}"
        )
        return 50.0
