"""
Technical indicators for trading strategies using vectorbt.
Provides RSI, moving averages, and return calculations.
"""
import pandas as pd
import vectorbt as vbt

class TechnicalIndicators:
    """
    Calculate technical indicators for trading strategies.
    Uses vectorbt for efficient computation.
    """

    @staticmethod
    def rsi(data, window=14):
        """
        Calculate RSI using vectorbt.
        Returns a pandas Series of RSI values.
        """
        try:
            rsi_series = vbt.RSI.run(data, window=window).rsi
            return pd.Series(rsi_series.values, index=data.index)
        except Exception:
            return pd.Series([50] * len(data), index=data.index)

    @staticmethod
    def moving_average(data, window):
        """
        Calculate moving average using vectorbt.
        Returns a pandas Series of moving average values.
        """
        try:
            ma_series = vbt.MA.run(data, window=window).ma
            return pd.Series(ma_series.values, index=data.index)
        except Exception:
            return data

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
