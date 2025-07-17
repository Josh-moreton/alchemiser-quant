import pandas as pd
import talib

class TechnicalIndicators:
    """Calculate technical indicators"""

    @staticmethod
    def rsi(data, window=14):
        """Calculate RSI using TA-Lib"""
        try:
            rsi_series = talib.RSI(data.values, timeperiod=window)
            return pd.Series(rsi_series, index=data.index)
        except Exception:
            return pd.Series([50] * len(data), index=data.index)

    @staticmethod
    def moving_average(data, window):
        """Calculate moving average using TA-Lib"""
        try:
            ma_series = talib.SMA(data.values, timeperiod=window)
            return pd.Series(ma_series, index=data.index)
        except Exception:
            return data

    @staticmethod
    def moving_average_return(data, window):
        """Calculate moving average return using TA-Lib"""
        try:
            returns = data.pct_change()
            # Use pandas rolling to match pandas-ta behavior exactly
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
