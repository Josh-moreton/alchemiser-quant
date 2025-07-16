import pandas as pd
import pandas_ta as ta

class TechnicalIndicators:
    """Calculate technical indicators"""

    @staticmethod
    def rsi(data, window=14):
        """Calculate RSI using pandas_ta"""
        try:
            rsi_series = ta.rsi(data, length=window)
            return rsi_series
        except Exception:
            return pd.Series([50] * len(data), index=data.index)

    @staticmethod
    def moving_average(data, window):
        """Calculate moving average using pandas_ta"""
        try:
            ma_series = ta.sma(data, length=window)
            return ma_series
        except Exception:
            return data

    @staticmethod
    def moving_average_return(data, window):
        """Calculate moving average return using pandas_ta"""
        try:
            returns = data.pct_change()
            ma_return = returns.rolling(window=window).mean() * 100
            return ma_return
        except Exception:
            return pd.Series([0] * len(data), index=data.index)

    @staticmethod
    def cumulative_return(data, window):
        """Calculate cumulative return over window"""
        try:
            cum_return = ((data / data.shift(window)) - 1) * 100
            return cum_return
        except Exception:
            return pd.Series([0] * len(data), index=data.index)
