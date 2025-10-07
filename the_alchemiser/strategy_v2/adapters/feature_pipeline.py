#!/usr/bin/env python3
"""Business Unit: strategy | Status: current.

Feature pipeline for computed features and non-financial statistics.

Provides utilities for computing features from raw market data,
handling float-based statistical calculations with appropriate tolerances.
"""

from __future__ import annotations

import math

import numpy as np

from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.schemas.market_bar import MarketBar

logger = get_logger(__name__)


class FeaturePipeline:
    """Pipeline for computing features from market data.

    Handles non-financial statistical computations using float arithmetic
    with appropriate tolerance checks for comparisons.
    """

    def __init__(self, default_tolerance: float = 1e-9) -> None:
        """Initialize feature pipeline.

        Args:
            default_tolerance: Default tolerance for float comparisons

        """
        self._tolerance = default_tolerance

    def compute_returns(self, bars: list[MarketBar]) -> list[float]:
        """Compute price returns from bar data.

        Args:
            bars: List of MarketBar objects with closing prices

        Returns:
            List of returns (excluding first bar which has no prior price)

        Note:
            Uses float arithmetic for statistical calculations.
            Returns empty list if insufficient data.

        """
        if len(bars) < 2:
            return []

        returns = []
        for i in range(1, len(bars)):
            try:
                prev_close = float(bars[i - 1].close_price)
                curr_close = float(bars[i].close_price)

                # Use direct comparison with a small epsilon for financial price data
                if prev_close < 1e-6:
                    logger.warning(
                        "Zero or near-zero price encountered in returns calculation"
                    )
                    returns.append(0.0)
                else:
                    ret = (curr_close - prev_close) / prev_close
                    returns.append(ret)
            except (ValueError, TypeError) as e:
                logger.warning(f"Invalid bar data in returns calculation: {e}")
                returns.append(0.0)

        return returns

    def compute_volatility(
        self, returns: list[float], window: int | None = None, *, annualize: bool = True
    ) -> float:
        """Compute volatility from returns.

        Args:
            returns: List of returns
            window: Optional window for rolling volatility (uses all data if None)
            annualize: Whether to annualize volatility (assumes daily returns)

        Returns:
            Volatility as float (0.0 if insufficient data)

        Note:
            Uses float arithmetic for statistical calculations.

        """
        if not returns or len(returns) < 2:
            return 0.0

        try:
            # Use most recent window if specified
            data = returns[-window:] if window else returns

            if len(data) < 2:
                return 0.0

            # Calculate standard deviation
            mean_return = sum(data) / len(data)
            variance = sum((r - mean_return) ** 2 for r in data) / (len(data) - 1)
            vol = math.sqrt(variance)

            # Annualize if requested (assumes daily returns, multiply by sqrt(252))
            if annualize:
                vol *= math.sqrt(252)

            return vol

        except Exception as e:
            logger.warning(f"Error computing volatility: {e}")
            return 0.0

    def compute_moving_average(self, values: list[float], window: int) -> list[float]:
        """Compute simple moving average.

        Args:
            values: List of values
            window: Window size for moving average

        Returns:
            List of moving averages (shorter than input by window-1)

        Note:
            Uses float arithmetic for statistical calculations.

        """
        if len(values) < window or window <= 0:
            return []

        averages = []
        for i in range(window - 1, len(values)):
            window_values = values[i - window + 1 : i + 1]
            avg = sum(window_values) / len(window_values)
            averages.append(avg)

        return averages

    def compute_correlation(self, series1: list[float], series2: list[float]) -> float:
        """Compute correlation between two series.

        Args:
            series1: First time series
            series2: Second time series

        Returns:
            Correlation coefficient (-1 to 1, 0.0 if error)

        Note:
            Uses float arithmetic with tolerance checking.

        """
        if len(series1) != len(series2) or len(series1) < 2:
            return 0.0

        try:
            # Convert to numpy for efficient computation
            arr1 = np.array(series1, dtype=float)
            arr2 = np.array(series2, dtype=float)

            # Use numpy correlation
            corr_matrix = np.corrcoef(arr1, arr2)
            correlation = corr_matrix[0, 1]

            # Handle NaN case
            if math.isnan(correlation):
                return 0.0

            return float(correlation)

        except Exception as e:
            logger.warning(f"Error computing correlation: {e}")
            return 0.0

    def is_close(self, a: float, b: float, tolerance: float | None = None) -> bool:
        """Check if two float values are close within tolerance.

        Args:
            a: First value
            b: Second value
            tolerance: Optional tolerance (uses default if None)

        Returns:
            True if values are close within tolerance

        Note:
            Helper for float comparisons in non-financial contexts.

        """
        tol = tolerance if tolerance is not None else self._tolerance
        return math.isclose(a, b, abs_tol=tol)

    def _compute_ma_ratio(self, closes: list[float], lookback_window: int) -> float:
        """Compute moving average ratio feature.

        Args:
            closes: List of closing prices
            lookback_window: Window for moving average calculation

        Returns:
            Ratio of current price to moving average (1.0 if insufficient data)

        """
        if len(closes) >= lookback_window:
            ma = self.compute_moving_average(closes, lookback_window)
            return closes[-1] / ma[-1] if ma and not self.is_close(ma[-1], 0.0) else 1.0
        return 1.0

    def _compute_price_position(
        self, bars: list[MarketBar], current_close: float, lookback_window: int
    ) -> float:
        """Compute price position within high-low range.

        Args:
            bars: List of MarketBar objects
            current_close: Current closing price
            lookback_window: Window for high-low range calculation

        Returns:
            Price position in range [0, 1] (0.5 if insufficient data or no range)

        """
        if len(bars) >= lookback_window:
            recent_bars = bars[-lookback_window:]
            max_high = max(float(bar.high_price) for bar in recent_bars)
            min_low = min(float(bar.low_price) for bar in recent_bars)

            # If there is a price range (max_high != min_low), calculate price_position;
            # otherwise, use the default value of 0.5 when no price range exists.
            if not self.is_close(max_high, min_low):
                # Clamp result to [0, 1] to handle cases where current_close is outside the range
                position = (current_close - min_low) / (max_high - min_low)
                return max(0.0, min(1.0, position))
        return 0.5

    def _compute_volume_ratio(
        self, volumes: list[float], lookback_window: int
    ) -> float:
        """Compute volume ratio feature.

        Args:
            volumes: List of volume values
            lookback_window: Window for average volume calculation

        Returns:
            Ratio of current volume to average volume (1.0 if insufficient data)

        """
        if len(volumes) >= lookback_window:
            avg_volume = sum(volumes[-lookback_window:]) / lookback_window
            return (
                volumes[-1] / avg_volume if not self.is_close(avg_volume, 0.0) else 1.0
            )
        return 1.0

    def extract_price_features(
        self, bars: list[MarketBar], lookback_window: int = 20
    ) -> dict[str, float]:
        """Extract common price-based features from bar data.

        Args:
            bars: List of MarketBar objects
            lookback_window: Window for rolling calculations

        Returns:
            Dictionary of computed features

        Note:
            Returns 0.0 for features that cannot be computed.

        """
        if not bars:
            return {}

        features: dict[str, float] = {}

        try:
            # Extract prices
            closes = [float(bar.close_price) for bar in bars]
            volumes = [bar.volume for bar in bars]

            # Current price
            features["current_price"] = closes[-1] if closes else 0.0

            # Returns and volatility
            returns = self.compute_returns(bars)
            features["volatility"] = self.compute_volatility(
                returns, window=lookback_window
            )

            # Moving averages
            features["ma_ratio"] = self._compute_ma_ratio(closes, lookback_window)

            # High-low range (normalized by close)
            features["price_position"] = self._compute_price_position(
                bars, closes[-1], lookback_window
            )

            # Volume features
            features["volume_ratio"] = self._compute_volume_ratio(
                [float(v) for v in volumes], lookback_window
            )

        except Exception as e:
            logger.warning(f"Error extracting price features: {e}")
            # Return default features on error
            features = {
                "current_price": 0.0,
                "volatility": 0.0,
                "ma_ratio": 1.0,
                "price_position": 0.5,
                "volume_ratio": 1.0,
            }

        return features
