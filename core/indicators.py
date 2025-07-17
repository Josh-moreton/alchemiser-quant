import pandas as pd
import vectorbt as vbt

class TechnicalIndicators:
    """Calculate technical indicators"""

    @staticmethod
    def rsi(data, window=14):
        """Calculate RSI using vectorbt"""
        try:
            rsi_series = vbt.RSI.run(data, window=window).rsi
            return pd.Series(rsi_series.values, index=data.index)
        except Exception:
            return pd.Series([50] * len(data), index=data.index)

    @staticmethod
    def moving_average(data, window):
        """Calculate moving average using vectorbt"""
        try:
            ma_series = vbt.MA.run(data, window=window).ma
            return pd.Series(ma_series.values, index=data.index)
        except Exception:
            return data

    @staticmethod
    def moving_average_return(data, window):
        """Calculate moving average return using vectorbt"""
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
