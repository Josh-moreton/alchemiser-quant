"""Business Unit: strategy | Status: current.

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

Technical indicators are appropriately located within strategy module as they
are strategy-specific computational utilities. This module provides pure
mathematical computations with no I/O or side effects.
"""

from __future__ import annotations

import math

import pandas as pd

from the_alchemiser.shared.errors.exceptions import MarketDataError
from the_alchemiser.shared.logging import get_logger

# Module-level constants for indicator calculations
DEFAULT_RSI_WINDOW = 14
NEUTRAL_RSI_VALUE = 50.0
RSI_OVERBOUGHT_THRESHOLD = 70.0
RSI_OVERSOLD_THRESHOLD = 30.0
TRADING_DAYS_PER_YEAR = 252  # Standard annualization factor

logger = get_logger(__name__)


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
        data: pd.Series, window: int = DEFAULT_RSI_WINDOW
    ) -> pd.Series:  # Enhanced: Ready for IndicatorData structured output in future phases
        """Calculate RSI using Wilder's smoothing method.

        Computes the Relative Strength Index (RSI) using Wilder's smoothing
        method, which is the industry standard. This implementation matches
        calculations from TradingView and Composer.trade.

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

        Raises:
            MarketDataError: If window is not positive or data is invalid.

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
        # Input validation
        if window <= 0:
            msg = f"RSI window must be positive, got {window}"
            logger.error(msg)
            raise MarketDataError(msg)

        if len(data) == 0:
            logger.warning("Empty data series provided to RSI calculation")
            return pd.Series(dtype=float)

        if len(data) < window:
            logger.warning(
                f"Insufficient data for RSI calculation: {len(data)} < {window}, "
                "returning neutral RSI values"
            )
            return pd.Series([NEUTRAL_RSI_VALUE] * len(data), index=data.index)

        try:
            delta = data.diff()
            gain = delta.where(delta > 0, 0)
            loss = -delta.where(delta < 0, 0)

            # Use Wilder's smoothing (exponential moving average with alpha = 1/window)
            alpha = 1.0 / window
            avg_gain = gain.ewm(alpha=alpha, adjust=False).mean()
            avg_loss = loss.ewm(alpha=alpha, adjust=False).mean()

            # Safe division to handle cases where avg_loss is zero
            rs = avg_gain.divide(avg_loss, fill_value=0.0)
            rsi = 100 - (100 / (1 + rs))

            # Fill NaN values with neutral RSI
            nan_count = rsi.isna().sum()
            if nan_count > 0:
                logger.debug(
                    f"Filled {nan_count} NaN values in RSI with neutral value {NEUTRAL_RSI_VALUE}"
                )

            return rsi.fillna(NEUTRAL_RSI_VALUE)
        except (ValueError, TypeError, KeyError) as e:
            logger.error(f"Error calculating RSI: {e}", exc_info=True)
            raise MarketDataError(f"Failed to calculate RSI: {e}") from e

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
                will be NaN due to insufficient data. Returns all NaN if
                insufficient data is available.

        Raises:
            MarketDataError: If window is not positive or data is invalid.

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
        # Input validation
        if window <= 0:
            msg = f"Moving average window must be positive, got {window}"
            logger.error(msg)
            raise MarketDataError(msg)

        if len(data) == 0:
            logger.warning("Empty data series provided to moving_average calculation")
            return pd.Series(dtype=float)

        try:
            return data.rolling(window=window, min_periods=window).mean()
        except (ValueError, TypeError, KeyError) as e:
            logger.error(f"Error calculating moving average: {e}", exc_info=True)
            raise MarketDataError(f"Failed to calculate moving average: {e}") from e

    @staticmethod
    def exponential_moving_average(data: pd.Series, window: int) -> pd.Series:
        """Calculate exponential moving average (EMA).

        Uses pandas ewm to compute the exponentially weighted moving average.
        The EMA gives more weight to recent prices compared to the simple
        moving average, making it more responsive to recent price changes.

        Args:
            data (pd.Series): Price data series (typically closing prices).
            window (int): EMA span (commonly 12, 26, 50). This determines
                how much weight is given to recent observations.

        Returns:
            pd.Series: EMA values. The first (window-1) values will be
                masked as pd.NA to align with SMA behavior.

        Raises:
            MarketDataError: If window is not positive or data is invalid.

        Example:
            >>> prices = pd.Series([100, 102, 101, 103, 105])
            >>> ema = TechnicalIndicators.exponential_moving_average(prices, window=3)
            >>> print(ema.dropna().tolist())
            [101.0, 102.0, 103.5]

        """
        # Input validation
        if window <= 0:
            msg = f"EMA window must be positive, got {window}"
            logger.error(msg)
            raise MarketDataError(msg)

        if len(data) == 0:
            logger.warning("Empty data series provided to exponential_moving_average calculation")
            return pd.Series(dtype=float)

        try:
            # align behavior with SMA min_periods by masking early values
            ema = data.ewm(span=window, adjust=False).mean()
            ema.iloc[: window - 1] = pd.NA
            return ema
        except (ValueError, TypeError, KeyError) as e:
            logger.error(f"Error calculating exponential moving average: {e}", exc_info=True)
            raise MarketDataError(f"Failed to calculate exponential moving average: {e}") from e

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
                for all periods if calculation fails due to insufficient data
                or invalid inputs.

        Raises:
            MarketDataError: If window is not positive or data contains invalid values.

        Example:
            >>> prices = pd.Series([100, 102, 101, 103, 105, 104])
            >>> avg_returns = TechnicalIndicators.moving_average_return(prices, 3)
            >>> print(f"Average 3-day return: {avg_returns.iloc[-1]:.2f}%")
            Average 3-day return: 0.65%

        Note:
            The function multiplies returns by 100 to express them as
            percentages. Returns are calculated as percentage changes
            between consecutive periods.

        """
        # Input validation
        if window <= 0:
            msg = f"Moving average return window must be positive, got {window}"
            logger.error(msg)
            raise MarketDataError(msg)

        if len(data) == 0:
            logger.warning("Empty data series provided to moving_average_return calculation")
            return pd.Series(dtype=float)

        if len(data) < window:
            logger.warning(
                f"Insufficient data for moving_average_return: {len(data)} < {window}, "
                "returning zero series"
            )
            return pd.Series([0] * len(data), index=data.index)

        try:
            returns = data.pct_change()
            return returns.rolling(window=window).mean() * 100
        except (ValueError, TypeError, KeyError) as e:
            logger.error(f"Error calculating moving average return: {e}", exc_info=True)
            raise MarketDataError(f"Failed to calculate moving average return: {e}") from e

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

        Raises:
            MarketDataError: If window is not positive or data contains invalid values.

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
        # Input validation
        if window <= 0:
            msg = f"Cumulative return window must be positive, got {window}"
            logger.error(msg)
            raise MarketDataError(msg)

        if len(data) == 0:
            logger.warning("Empty data series provided to cumulative_return calculation")
            return pd.Series(dtype=float)

        if len(data) <= window:
            logger.warning(
                f"Insufficient data for cumulative_return: {len(data)} <= {window}, "
                "returning zero series"
            )
            return pd.Series([0] * len(data), index=data.index)

        try:
            return ((data / data.shift(window)) - 1) * 100
        except (ValueError, TypeError, KeyError, ZeroDivisionError) as e:
            logger.error(f"Error calculating cumulative return: {e}", exc_info=True)
            raise MarketDataError(f"Failed to calculate cumulative return: {e}") from e

    @staticmethod
    def stdev_return(data: pd.Series, window: int) -> pd.Series:
        """Return annualized rolling standard deviation of percentage returns.

        Computes the annualized volatility of returns over a rolling window,
        matching Composer's standard deviation calculation methodology.

        Composer's algorithm:
        1. Compute each day's percent return over the window
        2. Compute the standard deviation of those daily returns (population std)
        3. Annualize by multiplying by sqrt(252)

        Args:
            data (pd.Series): Price data series (typically closing prices).
            window (int): Number of periods for the rolling window calculation.

        Returns:
            pd.Series: Annualized standard deviation of returns as percentages.
                The first (window-1) values will be NaN due to insufficient data.

        Raises:
            MarketDataError: If window is not positive or data contains invalid values.

        Example:
            >>> prices = pd.Series([100, 102, 98, 105, 103, 107])
            >>> vol = TechnicalIndicators.stdev_return(prices, 3)
            >>> print(f"3-day annualized volatility: {vol.iloc[-1]:.2f}%")
            3-day annualized volatility: 38.93%

        Note:
            Uses population standard deviation (ddof=0) and annualizes with
            sqrt(252) to match Composer's documented calculation method.

        """
        # Input validation
        if window <= 0:
            msg = f"Standard deviation window must be positive, got {window}"
            logger.error(msg)
            raise MarketDataError(msg)

        if len(data) == 0:
            logger.warning("Empty data series provided to stdev_return calculation")
            return pd.Series(dtype=float)

        if len(data) < window:
            logger.warning(
                f"Insufficient data for stdev_return: {len(data)} < {window}, returning zero series"
            )
            return pd.Series([0] * len(data), index=data.index)

        try:
            # Composer method: daily returns as percentages
            returns = data.pct_change() * 100
            # Population std (ddof=0) per Composer docs: "divide by number of observations"
            daily_std = returns.rolling(window=window, min_periods=window).std(ddof=0)
            # Annualize by multiplying by sqrt(252)
            return daily_std * math.sqrt(TRADING_DAYS_PER_YEAR)
        except (ValueError, TypeError, KeyError) as e:
            logger.error(f"Error calculating standard deviation of returns: {e}", exc_info=True)
            raise MarketDataError(f"Failed to calculate standard deviation of returns: {e}") from e

    @staticmethod
    def stdev_price(data: pd.Series, window: int) -> pd.Series:
        """Return rolling standard deviation of raw price values.

        Computes the volatility of prices over a rolling window. Unlike stdev_return
        which measures return volatility, this indicator measures price volatility
        directly in dollar terms. Useful for position sizing and risk assessment
        when absolute price movement matters.

        Args:
            data (pd.Series): Price data series (typically closing prices).
            window (int): Number of periods for the rolling window calculation.

        Returns:
            pd.Series: Standard deviation of raw prices in the same units as input.
                The first (window-1) values will be NaN due to insufficient data.

        Raises:
            MarketDataError: If window is not positive or data contains invalid values.

        Example:
            >>> prices = pd.Series([100, 102, 98, 105, 103, 107])
            >>> vol = TechnicalIndicators.stdev_price(prices, 3)
            >>> print(f"3-day price stdev: ${vol.iloc[-1]:.2f}")
            3-day price stdev: $2.00

        Note:
            Returns standard deviation of raw prices over a rolling window.
            For a $100 stock with stdev_price of $5, prices typically vary by ~$5.

        """
        # Input validation
        if window <= 0:
            msg = f"Standard deviation window must be positive, got {window}"
            logger.error(msg)
            raise MarketDataError(msg)

        if len(data) == 0:
            logger.warning("Empty data series provided to stdev_price calculation")
            return pd.Series(dtype=float)

        if len(data) < window:
            logger.warning(
                f"Insufficient data for stdev_price: {len(data)} < {window}, returning zero series"
            )
            return pd.Series([0] * len(data), index=data.index)

        try:
            return data.rolling(window=window, min_periods=window).std()
        except (ValueError, TypeError, KeyError) as e:
            logger.error(f"Error calculating standard deviation of prices: {e}", exc_info=True)
            raise MarketDataError(f"Failed to calculate standard deviation of prices: {e}") from e

    @staticmethod
    def max_drawdown(data: pd.Series, window: int) -> pd.Series:
        """Return rolling maximum drawdown over window (percentage magnitude).

        For each point, computes the maximum peak-to-trough decline within the
        rolling window. This matches Composer's max-drawdown calculation
        methodology as documented in their official docs.

        Composer's algorithm:
        1. Track the running maximum value (peak) seen so far in the window
        2. For each value, compute drawdown = (peak - current) / peak
        3. Max drawdown is the largest such decline within the window

        Args:
            data (pd.Series): Price data series (typically closing prices).
            window (int): Number of periods for the rolling window calculation.

        Returns:
            pd.Series: Maximum drawdown values as positive percentages.
                The first (window-1) values will be NaN due to insufficient data.

        Raises:
            MarketDataError: If window is not positive or data contains invalid values.

        Example:
            >>> prices = pd.Series([100, 110, 95, 105, 90, 100])
            >>> mdd = TechnicalIndicators.max_drawdown(prices, 4)
            >>> # Window [110, 95, 105, 90]: peak=110, trough=90, dd=(110-90)/110=18.2%
            >>> print(f"Max 4-day drawdown: {mdd.iloc[-1]:.1f}%")
            Max 4-day drawdown: 18.2%

        Note:
            This is the standard peak-to-trough drawdown calculation used by
            Composer and most financial platforms. It measures the greatest
            percentage decline from any peak to any subsequent trough within
            the window.

        """
        # Input validation
        if window <= 0:
            msg = f"Max drawdown window must be positive, got {window}"
            logger.error(msg)
            raise MarketDataError(msg)

        if len(data) == 0:
            logger.warning("Empty data series provided to max_drawdown calculation")
            return pd.Series(dtype=float)

        if len(data) < window:
            logger.warning(
                f"Insufficient data for max_drawdown: {len(data)} < {window}, returning zero series"
            )
            return pd.Series([0] * len(data), index=data.index)

        try:
            # Rolling window apply using Composer's peak-to-trough methodology
            def mdd_window(x: pd.Series) -> float:
                """Compute max drawdown using peak-to-trough (Composer methodology).

                Tracks the running maximum (peak) within the window and finds
                the largest percentage decline from any peak to any subsequent
                trough.

                Args:
                    x: Price series within the rolling window.

                Returns:
                    Maximum drawdown as a positive percentage value.

                """
                # Composer method: track running peak and measure decline from it
                cummax = x.cummax()  # Running maximum (peak tracking)
                drawdowns = (x / cummax) - 1.0  # Decline from peak at each point
                return float(-drawdowns.min() * 100.0)  # Largest decline as positive %

            return data.rolling(window=window, min_periods=window).apply(mdd_window, raw=False)
        except (ValueError, TypeError, KeyError) as e:
            logger.error(f"Error calculating maximum drawdown: {e}", exc_info=True)
            raise MarketDataError(f"Failed to calculate maximum drawdown: {e}") from e

    @staticmethod
    def percentage_price_oscillator(
        data: pd.Series, short_window: int = 12, long_window: int = 26
    ) -> pd.Series:
        """Calculate Percentage Price Oscillator (PPO).

        PPO measures the percentage difference between two exponential moving
        averages. It is similar to MACD but expressed as a percentage, making
        it easier to compare across different price ranges.

        Formula: PPO = ((EMA(short) - EMA(long)) / EMA(long)) * 100

        Args:
            data (pd.Series): Price data series (typically closing prices).
            short_window (int): Short-term EMA period. Default is 12.
            long_window (int): Long-term EMA period. Default is 26.

        Returns:
            pd.Series: PPO values as percentages. Positive values indicate
                short-term momentum is stronger than long-term.

        Raises:
            MarketDataError: If windows are invalid or data is insufficient.

        Example:
            >>> prices = pd.Series([100, 102, 101, 103, 105, 104, 106, 108])
            >>> ppo = TechnicalIndicators.percentage_price_oscillator(prices, 3, 5)
            >>> print(f"Latest PPO: {ppo.iloc[-1]:.2f}%")
            Latest PPO: 1.23%

        Note:
            PPO crossovers above/below zero indicate momentum shifts.
            A rising PPO suggests strengthening bullish momentum.

        """
        # Input validation
        if short_window <= 0:
            msg = f"PPO short window must be positive, got {short_window}"
            logger.error(msg)
            raise MarketDataError(msg)

        if long_window <= 0:
            msg = f"PPO long window must be positive, got {long_window}"
            logger.error(msg)
            raise MarketDataError(msg)

        if short_window >= long_window:
            msg = f"PPO short window ({short_window}) must be less than long window ({long_window})"
            logger.error(msg)
            raise MarketDataError(msg)

        if len(data) == 0:
            logger.warning("Empty data series provided to percentage_price_oscillator calculation")
            return pd.Series(dtype=float)

        if len(data) < long_window:
            logger.warning(
                f"Insufficient data for PPO: {len(data)} < {long_window}, returning zero series"
            )
            return pd.Series([0] * len(data), index=data.index)

        try:
            # Calculate EMAs
            ema_short = data.ewm(span=short_window, adjust=False).mean()
            ema_long = data.ewm(span=long_window, adjust=False).mean()

            # PPO = ((EMA_short - EMA_long) / EMA_long) * 100
            ppo = ((ema_short - ema_long) / ema_long) * 100

            # Mask early values with insufficient data
            ppo.iloc[: long_window - 1] = pd.NA

            return ppo
        except (ValueError, TypeError, KeyError, ZeroDivisionError) as e:
            logger.error(f"Error calculating PPO: {e}", exc_info=True)
            raise MarketDataError(f"Failed to calculate PPO: {e}") from e

    @staticmethod
    def percentage_price_oscillator_signal(
        data: pd.Series, short_window: int = 12, long_window: int = 26, smooth_window: int = 9
    ) -> pd.Series:
        """Calculate PPO Signal Line.

        The signal line is an EMA of the PPO, used to generate trading signals.
        Crossovers between PPO and its signal line indicate momentum shifts.

        Formula: PPO Signal = EMA(PPO, smooth_window)

        Args:
            data (pd.Series): Price data series (typically closing prices).
            short_window (int): Short-term EMA period for PPO. Default is 12.
            long_window (int): Long-term EMA period for PPO. Default is 26.
            smooth_window (int): Signal line smoothing period. Default is 9.

        Returns:
            pd.Series: PPO signal line values as percentages.

        Raises:
            MarketDataError: If windows are invalid or data is insufficient.

        Example:
            >>> prices = pd.Series([100, 102, 101, 103, 105, 104, 106, 108])
            >>> signal = TechnicalIndicators.percentage_price_oscillator_signal(
            ...     prices, 3, 5, 2
            ... )
            >>> print(f"Latest PPO Signal: {signal.iloc[-1]:.2f}%")
            Latest PPO Signal: 0.98%

        Note:
            Buy signal: PPO crosses above signal line
            Sell signal: PPO crosses below signal line

        """
        # Input validation for smooth_window
        if smooth_window <= 0:
            msg = f"PPO signal smooth window must be positive, got {smooth_window}"
            logger.error(msg)
            raise MarketDataError(msg)

        if len(data) == 0:
            logger.warning(
                "Empty data series provided to percentage_price_oscillator_signal calculation"
            )
            return pd.Series(dtype=float)

        min_required = long_window + smooth_window
        if len(data) < min_required:
            logger.warning(
                f"Insufficient data for PPO signal: {len(data)} < {min_required}, "
                "returning zero series"
            )
            return pd.Series([0] * len(data), index=data.index)

        try:
            # Calculate PPO first
            ppo = TechnicalIndicators.percentage_price_oscillator(data, short_window, long_window)

            # Signal line is EMA of PPO
            signal = ppo.ewm(span=smooth_window, adjust=False).mean()

            # Mask early values with insufficient data
            signal.iloc[: long_window + smooth_window - 2] = pd.NA

            return signal
        except (ValueError, TypeError, KeyError) as e:
            logger.error(f"Error calculating PPO signal: {e}", exc_info=True)
            raise MarketDataError(f"Failed to calculate PPO signal: {e}") from e
