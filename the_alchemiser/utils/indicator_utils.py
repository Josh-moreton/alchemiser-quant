"""
Indicator Utilities

This module provides helper functions for safely calculating and retrieving technical indicator values.
"""

import logging

import pandas as pd


def safe_get_indicator(data, indicator_func, *args, **kwargs):
    """
    Safely get an indicator value, logging exceptions and handling NaN values.

    This function attempts to calculate an indicator and returns the last valid
    numeric value from the resulting series. It includes robust error handling
    and fallbacks.

    Args:
        data (pd.DataFrame): The input data for the indicator function.
        indicator_func (callable): The function to call to calculate the indicator.
        *args: Positional arguments to pass to the indicator function.
        **kwargs: Keyword arguments to pass to the indicator function.

    Returns:
        float: The calculated indicator value, or a fallback value (50.0) if an
               error occurs or no valid data is found.
    """
    try:
        result = indicator_func(data, *args, **kwargs)
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
                    logging.debug(
                        f"No valid values for indicator {indicator_func.__name__} on data: {data.tail(1)}"
                    )
                    return 50.0  # Fallback only if no valid values
            return float(value)
        # Check if it's due to insufficient data (common with recent dates)
        if len(data) < 2:
            logging.debug(
                f"Insufficient data for indicator {indicator_func.__name__} (only {len(data)} points)"
            )
        else:
            logging.warning(
                f"Indicator {indicator_func.__name__} returned no results for data: {data.tail(1)}"
            )
        return 50.0
    except Exception as e:
        logging.error(
            f"Exception in safe_get_indicator for {indicator_func.__name__}: {e}\nData: {data.tail(1)}"
        )
        return 50.0
