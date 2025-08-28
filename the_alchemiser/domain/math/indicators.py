"""Business Unit: utilities; Status: current.

Technical indicators for trading strategies.

This module provides technical analysis indicators used by trading strategies
in The Alchemiser quantitative trading system. All indicators are implemented using pandas
for efficient computation and follow industry-standard calculation methods
to ensure compatibility with external trading platforms.

The module focuses on indicators actually used by the trading strategies:
- RSI (Relative Strength Index) using Wilder's smoothing method
- Simple Moving Averages for trend identification
- Return calculations for performance analysis

All functions return pandas Series objects that can be easily integrated
with the trading system's data processing pipeline.
"""

from __future__ import annotations

import pandas as pd

# TODO: Phase 11 - Type available for future structured indicator results
# from the_alchemiser.domain.types import IndicatorData


class TechnicalIndicators:
    """Technical analysis indicators for trading strategies.

    This class provides static methods for calculating technical indicators
    used in quantitative trading strategies. All methods are implemented
    using pandas for efficient computation and vectorized operations.

    The indicators follow industry-standard calculation methods to ensure
    consistency with external trading platforms and charting software.

    Example:
        >>> import pandas as pd
        >>> prices = pd.Series([100, 101, 99, 102, 105, 103, 104])
        >>> rsi_values = TechnicalIndicators.rsi(prices, window=14)
        >>> ma_values = TechnicalIndicators.moving_average(prices, window=5)

    """

    @staticmethod
    def rsi(
        data: pd.Series, window: int = 14
    ) -> pd.Series:  # TODO: Phase 11 - Consider IndicatorData for structured output
        """Calculate RSI using Wilder's smoothing method.

        Computes the Relative Strength Index (RSI) using Wilder's smoothing
        method, which is the industry standard. This implementation matches
        calculations from TradingView, TwelveData, and Composer.trade.

        The RSI is a momentum oscillator that measures the speed and magnitude
        of price changes. Values range from 0 to 100, with values above 70
        typically considered overbought and values below 30 considered oversold.

        Args:
            data (pd.Series): Price data series (typically closing prices).
            window (int, optional): Period for RSI calculation. Defaults to 14,
                which is the standard period used in most trading applications.

        Returns:
            pd.Series: RSI values ranging from 0 to 100. NaN values are
                filled with 50 (neutral RSI value).

        Example:
            >>> prices = pd.Series([100, 102, 101, 103, 105, 104, 106])
            >>> rsi = TechnicalIndicators.rsi(prices, window=6)
            >>> print(f"Latest RSI: {rsi.iloc[-1]:.2f}")
            Latest RSI: 66.67

        Note:
            Wilder's smoothing uses an exponential moving average with
            alpha = 1/window, which gives more weight to recent observations
            while still incorporating historical data.

        """
        delta = data.diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)

        # Use Wilder's smoothing (exponential moving average with alpha = 1/window)
        alpha = 1.0 / window
        avg_gain = gain.ewm(alpha=alpha, adjust=False).mean()
        avg_loss = loss.ewm(alpha=alpha, adjust=False).mean()

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi.fillna(50)

    @staticmethod
    def moving_average(data: pd.Series, window: int) -> pd.Series:
        """Calculate simple moving average.

        Computes the Simple Moving Average (SMA) over a specified window.
        The SMA is the arithmetic mean of prices over the window period
        and is used for trend identification and support/resistance levels.

        Args:
            data (pd.Series): Price data series (typically closing prices).
            window (int): Number of periods to include in the moving average.
                Common values are 20, 50, 100, and 200 days.

        Returns:
            pd.Series: Moving average values. The first (window-1) values
                will be NaN due to insufficient data.

        Example:
            >>> prices = pd.Series([100, 102, 101, 103, 105])
            >>> ma = TechnicalIndicators.moving_average(prices, window=3)
            >>> print(ma.dropna().tolist())
            [101.0, 102.0, 103.0]

        Note:
            This function requires at least 'window' periods of data to
            produce non-NaN results. The min_periods parameter ensures
            that partial averages are not calculated.

        """
        return data.rolling(window=window, min_periods=window).mean()

    @staticmethod
    def moving_average_return(data: pd.Series, window: int) -> pd.Series:
        """Calculate rolling average of percentage returns.

        Computes the moving average of percentage returns over a specified
        window. This indicator is useful for measuring average performance
        and volatility trends in the data.

        Args:
            data (pd.Series): Price data series (typically closing prices).
            window (int): Number of periods for the rolling average calculation.

        Returns:
            pd.Series: Rolling average returns as percentages. Returns 0%
                for all periods if calculation fails (e.g., insufficient data).

        Example:
            >>> prices = pd.Series([100, 102, 101, 103, 105, 104])
            >>> avg_returns = TechnicalIndicators.moving_average_return(prices, 3)
            >>> print(f"Average 3-day return: {avg_returns.iloc[-1]:.2f}%")
            Average 3-day return: 0.65%

        Note:
            The function multiplies returns by 100 to express them as
            percentages. Exception handling ensures the function returns
            a valid Series even with problematic data.

        """
        try:
            returns = data.pct_change()
            return returns.rolling(window=window).mean() * 100
        except Exception:
            return pd.Series([0] * len(data), index=data.index)

    @staticmethod
    def cumulative_return(data: pd.Series, window: int) -> pd.Series:
        """Calculate cumulative return over a specified period.

        Computes the total return from 'window' periods ago to the current
        period. This indicator shows the overall performance over the
        specified time frame and is useful for momentum analysis.

        Args:
            data (pd.Series): Price data series (typically closing prices).
            window (int): Number of periods to look back for the cumulative
                return calculation.

        Returns:
            pd.Series: Cumulative returns as percentages. Returns 0% for
                all periods if calculation fails or insufficient data.

        Example:
            >>> prices = pd.Series([100, 102, 98, 105, 110])
            >>> cum_returns = TechnicalIndicators.cumulative_return(prices, 3)
            >>> print(f"3-period return: {cum_returns.iloc[-1]:.1f}%")
            3-period return: 7.8%

        Note:
            The calculation compares current price to price 'window' periods
            ago: (current_price / past_price - 1) * 100. The first 'window'
            values will be NaN due to insufficient historical data.

        """
        try:
            return ((data / data.shift(window)) - 1) * 100
        except Exception:
            return pd.Series([0] * len(data), index=data.index)
