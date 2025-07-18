"""
Technical indicators for trading strategies using vectorbt.
Provides RSI, moving averages, and return calculations.
"""
import pandas as pd


class TechnicalIndicators:
    """
    Calculate technical indicators for trading strategies.
    Uses vectorbt for efficient computation.
    """

    @staticmethod
    def rsi(data, window=14):
        """
        Calculate RSI manually using pandas.
        Returns a pandas Series of RSI values.
        """
        delta = data.diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        avg_gain = gain.rolling(window=window, min_periods=window).mean()
        avg_loss = loss.rolling(window=window, min_periods=window).mean()
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        rsi = rsi.fillna(50)
        return rsi

    @staticmethod
    def moving_average(data, window):
        """
        Calculate moving average using pandas.
        Returns a pandas Series of moving average values.
        """
        return data.rolling(window=window, min_periods=window).mean()

    @staticmethod
    def moving_average_return(data, window):
        """
        Calculate moving average return using vectorbt.
        Returns a pandas Series of moving average returns.
        """
        try:
            returns = data.pct_change()
            ma_return = returns.rolling(window=window).mean() * 100
            return ma_return
        except Exception:
            return pd.Series([0] * len(data), index=data.index)

    @staticmethod
    def cumulative_return(data, window):
        """
        Calculate cumulative return over a window.
        Returns a pandas Series of cumulative returns.
        """
        try:
            cum_return = ((data / data.shift(window)) - 1) * 100
            return cum_return
        except Exception:
            return pd.Series([0] * len(data), index=data.index)
