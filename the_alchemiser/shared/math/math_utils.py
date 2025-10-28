"""Business Unit: utilities; Status: current.

Mathematical Utilities for Trading Strategies.

This module provides statistical and mathematical functions commonly used
across different trading strategies, particularly for return calculations,
volatility measurements, and time series analysis.

Functions include:
- Standard deviation of returns calculations
- Moving average calculations with robust error handling
- Return-based metrics for strategy evaluation
- Statistical measures for ensemble selection
"""

from __future__ import annotations

from math import isclose

import pandas as pd

from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.math.num import floats_equal

logger = get_logger(__name__)


def calculate_stdev_returns(close_prices: pd.Series, window: int) -> float:
    """Calculate standard deviation of returns over a specified window.

    This function computes the rolling standard deviation of percentage returns,
    which is commonly used for volatility measurement and risk assessment in
    trading strategies.

    Args:
        close_prices (pd.Series): Series of closing prices
        window (int): Number of periods for the rolling calculation

    Returns:
        float: Standard deviation of returns, or 0.1 as fallback for insufficient data

    Example:
        >>> prices = pd.Series([100, 102, 101, 103, 105])
        >>> volatility = calculate_stdev_returns(prices, 3)
        >>> print(f"Volatility: {volatility:.4f}")

    """
    if len(close_prices) < window + 1:
        return 0.1  # Default volatility fallback

    returns = close_prices.pct_change().dropna()
    if len(returns) < window:
        return 0.1

    stdev_returns = returns.rolling(window=window).std()
    result = stdev_returns.iloc[-1] if not pd.isna(stdev_returns.iloc[-1]) else 0.1
    return float(result)


def calculate_moving_average(close_prices: pd.Series, window: int) -> float:
    """Calculate simple moving average with robust error handling.

    Computes the simple moving average over the specified window period.
    Handles insufficient data gracefully by returning the current price.

    Args:
        close_prices (pd.Series): Series of closing prices
        window (int): Number of periods for the moving average

    Returns:
        float: Moving average value, or current price if insufficient data

    Example:
        >>> prices = pd.Series([100, 102, 101, 103, 105])
        >>> ma = calculate_moving_average(prices, 3)
        >>> print(f"3-period MA: {ma:.2f}")

    """
    try:
        if len(close_prices) < window:
            # Not enough data for full window, return current price
            return float(close_prices.iloc[-1])

        ma = close_prices.rolling(window=window).mean()
        if len(ma) > 0 and not pd.isna(ma.iloc[-1]):
            return float(ma.iloc[-1])
        # Fallback to current price if MA calculation fails
        return float(close_prices.iloc[-1])
    except (AttributeError, KeyError, IndexError) as e:
        # Data access errors
        logger.warning(f"Data access error calculating MA({window}): {e}, using current price", error_type=type(e).__name__)
        return float(close_prices.iloc[-1]) if len(close_prices) > 0 else 0.0
    except (ValueError, TypeError) as e:
        # Type or conversion errors
        logger.warning(f"Conversion error calculating MA({window}): {e}, using current price", error_type=type(e).__name__)
        return float(close_prices.iloc[-1]) if len(close_prices) > 0 else 0.0
    except Exception as e:
        # Last-resort catch for unexpected errors
        logger.warning(f"Unexpected error calculating MA({window}): {e}, using current price", error_type=type(e).__name__, exc_info=True)
        return float(close_prices.iloc[-1]) if len(close_prices) > 0 else 0.0


def calculate_moving_average_return(close_prices: pd.Series, window: int = 20) -> float:
    """Calculate moving average return with robust error handling.

    Computes the percentage change in the moving average value from the previous
    period, which is useful for trend analysis and momentum calculations.

    Args:
        close_prices (pd.Series): Series of closing prices
        window (int): Number of periods for the moving average calculation

    Returns:
        float: Moving average return as percentage, or 0.0 if insufficient data

    Example:
        >>> prices = pd.Series([100, 102, 101, 103, 105, 107])
        >>> ma_return = calculate_moving_average_return(prices, 3)
        >>> print(f"MA Return: {ma_return:.2f}%")

    """
    try:
        if len(close_prices) < window + 1:
            return 0.0

        ma = close_prices.rolling(window=window).mean()
        if len(ma) >= 2 and not pd.isna(ma.iloc[-1]) and not pd.isna(ma.iloc[-2]):
            current_ma = ma.iloc[-1]
            prev_ma = ma.iloc[-2]
            if not floats_equal(prev_ma, 0.0):
                return float(((current_ma - prev_ma) / prev_ma) * 100)
        return 0.0
    except (AttributeError, KeyError, IndexError) as e:
        # Data access errors
        logger.warning(f"Data access error calculating MA return({window}): {e}", error_type=type(e).__name__)
        return 0.0
    except (ValueError, TypeError, ZeroDivisionError) as e:
        # Conversion or mathematical errors
        logger.warning(f"Calculation error in MA return({window}): {e}", error_type=type(e).__name__)
        return 0.0
    except Exception as e:
        # Last-resort catch for unexpected errors
        logger.warning(f"Unexpected error calculating MA return({window}): {e}", error_type=type(e).__name__, exc_info=True)
        return 0.0


def calculate_percentage_change(current_value: float, previous_value: float) -> float:
    """Calculate percentage change between two values.

    Args:
        current_value (float): Current value
        previous_value (float): Previous value for comparison

    Returns:
        float: Percentage change, or 0.0 if previous value is zero

    """
    if floats_equal(previous_value, 0.0):
        return 0.0
    return ((current_value - previous_value) / previous_value) * 100


def _get_fallback_value_for_metric(data: pd.Series, metric: str) -> float:
    """Get fallback value when insufficient data for rolling calculation.

    Args:
        data: Input data series
        metric: Statistical metric type

    Returns:
        Appropriate fallback value for the metric type

    """
    if len(data) == 0:
        return 0.1 if metric == "std" else 0.0

    from collections.abc import Callable

    fallback_handlers: dict[str, Callable[[], float]] = {
        "mean": lambda: float(data.mean()),
        "std": lambda: 0.1,  # Default volatility
        "min": lambda: float(data.min()),
        "max": lambda: float(data.max()),
    }

    handler = fallback_handlers.get(metric)
    return handler() if handler else 0.0


def calculate_rolling_metric(data: pd.Series, window: int, metric: str = "mean") -> float:
    """Calculate a rolling statistical metric with error handling.

    Args:
        data (pd.Series): Input data series
        window (int): Rolling window size
        metric (str): Statistical metric to calculate ('mean', 'std', 'min', 'max')

    Returns:
        float: Calculated metric value, or appropriate fallback

    """
    if len(data) < window:
        return _get_fallback_value_for_metric(data, metric)

    try:
        rolling_result = getattr(data.rolling(window=window), metric)()
        result = rolling_result.iloc[-1]
        return float(result) if not pd.isna(result) else 0.0
    except (AttributeError, KeyError, IndexError) as e:
        # Data access errors or invalid metric
        logger.warning(f"Data access error calculating rolling {metric}: {e}", error_type=type(e).__name__)
        return 0.0
    except (ValueError, TypeError) as e:
        # Conversion or type errors
        logger.warning(f"Conversion error calculating rolling {metric}: {e}", error_type=type(e).__name__)
        return 0.0
    except Exception as e:
        # Last-resort catch for unexpected errors
        logger.warning(f"Unexpected error calculating rolling {metric}: {e}", error_type=type(e).__name__, exc_info=True)
        return 0.0


def safe_division(numerator: float, denominator: float, fallback: float = 0.0) -> float:
    """Perform safe division with fallback for zero or invalid denominators.

    Args:
        numerator (float): Numerator value
        denominator (float): Denominator value
        fallback (float): Fallback value if division is invalid

    Returns:
        float: Division result or fallback value

    """
    try:
        if floats_equal(denominator, 0.0) or pd.isna(denominator) or pd.isna(numerator):
            return fallback
        return numerator / denominator
    except (ZeroDivisionError, TypeError):
        return fallback


def normalize_to_range(
    value: float,
    min_val: float,
    max_val: float,
    target_min: float = 0.0,
    target_max: float = 1.0,
) -> float:
    """Normalize a value from one range to another.

    Args:
        value (float): Value to normalize
        min_val (float): Minimum of the original range
        max_val (float): Maximum of the original range
        target_min (float): Minimum of the target range
        target_max (float): Maximum of the target range

    Returns:
        float: Normalized value in the target range

    """
    if floats_equal(max_val, min_val):
        return target_min

    normalized = (value - min_val) / (max_val - min_val)
    return target_min + normalized * (target_max - target_min)


def _normalize_ensemble_weights(metrics: list[float], weights: list[float] | None) -> list[float]:
    """Normalize weights to match the number of metrics.

    Args:
        metrics: List of valid metric values
        weights: Optional weights list

    Returns:
        Normalized weights matching metrics length

    """
    if weights is None:
        return [1.0] * len(metrics)

    # Truncate if too long
    normalized = weights[: len(metrics)]

    # Pad if too short
    if len(normalized) < len(metrics):
        normalized.extend([1.0] * (len(metrics) - len(normalized)))

    return normalized


def _clamp_result_to_range(result: float, min_val: float, max_val: float) -> float:
    """Clamp result within valid range accounting for floating point tolerance.

    Args:
        result: Calculated result value
        min_val: Minimum allowed value
        max_val: Maximum allowed value

    Returns:
        Clamped result within [min_val, max_val]

    """
    if result < min_val and isclose(result, min_val, rel_tol=1e-12, abs_tol=1e-12):
        return min_val
    if result > max_val and isclose(result, max_val, rel_tol=1e-12, abs_tol=1e-12):
        return max_val
    return result


def calculate_ensemble_score(
    performance_metrics: list[float], weights: list[float] | None = None
) -> float:
    """Calculate a weighted ensemble score from multiple performance metrics.

    Args:
        performance_metrics (list): List of performance values
        weights (list, optional): Weights for each metric. If None, equal weights are used

    Returns:
        float: Weighted ensemble score

    """
    if not performance_metrics:
        return 0.0

    metrics = [float(m) for m in performance_metrics if not pd.isna(m)]
    if not metrics:
        return 0.0

    normalized_weights = _normalize_ensemble_weights(metrics, weights)

    try:
        weighted_sum = sum(m * w for m, w in zip(metrics, normalized_weights, strict=False))
        total_weight = sum(normalized_weights)
        if total_weight <= 0:
            return 0.0

        result = weighted_sum / total_weight

        # Clamp to within [min(metrics), max(metrics)] allowing for floating point tolerances
        min_val = min(metrics)
        max_val = max(metrics)
        return _clamp_result_to_range(result, min_val, max_val)
    except (ValueError, ZeroDivisionError) as e:
        # Mathematical errors during ensemble calculation
        logger.debug(f"Calculation error in ensemble score: {e}", error_type=type(e).__name__)
        return 0.0
    except Exception as e:
        # Last-resort catch for unexpected errors
        logger.debug(f"Unexpected error in ensemble score: {e}", error_type=type(e).__name__, exc_info=True)
        return 0.0
