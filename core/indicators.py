import pandas as pd
import talib

class TechnicalIndicators:
    """Calculate technical indicators"""

    @staticmethod
    def rsi(data, window=14):
        """Calculate RSI using TA-Lib"""
        try:
            # Handle NaN values by dropping them first
            data_clean = data.dropna()
            
            if len(data_clean) < window:
                # Not enough data for calculation
                return pd.Series([50] * len(data), index=data.index)
            
            rsi_values = talib.RSI(data_clean.values, timeperiod=window)
            
            # Create result series aligned with original data index
            result = pd.Series(index=data.index, dtype=float)
            result.iloc[:len(data_clean)] = rsi_values
            
            return result
        except Exception:
            return pd.Series([50] * len(data), index=data.index)

    @staticmethod
    def moving_average(data, window):
        """Calculate moving average using TA-Lib"""
        try:
            # Handle NaN values by dropping them first
            data_clean = data.dropna()
            
            if len(data_clean) < window:
                # Not enough data for calculation
                return data
            
            ma_values = talib.SMA(data_clean.values, timeperiod=window)
            
            # Create result series aligned with original data index
            result = pd.Series(index=data.index, dtype=float)
            result.iloc[:len(data_clean)] = ma_values
            
            return result
        except Exception:
            return data

    @staticmethod
    def moving_average_return(data, window):
        """Calculate moving average return using TA-Lib"""
        try:
            returns = data.pct_change()
            # Handle NaN values by dropping them first
            returns_clean = returns.dropna()
            
            if len(returns_clean) < window:
                # Not enough data for calculation
                return pd.Series([0] * len(data), index=data.index)
            
            # Calculate SMA on clean returns
            ma_return = talib.SMA(returns_clean.values, timeperiod=window)
            
            # Create result series aligned with original data index
            result = pd.Series(index=data.index, dtype=float)
            result.iloc[:len(returns_clean)] = ma_return
            
            return result * 100
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
