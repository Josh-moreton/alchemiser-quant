#!/usr/bin/env python3
"""
Debug script to compare pandas-ta vs TA-Lib indicator outputs
"""

import pandas as pd
import numpy as np
import yfinance as yf
import talib
import pandas_ta as ta

def get_sample_data():
    """Get sample stock data for testing"""
    try:
        # Get recent data for TQQQ (common in nuclear strategy)
        ticker = yf.Ticker("TQQQ")
        data = ticker.history(period="60d")
        return data['Close']
    except:
        # Fallback to dummy data
        dates = pd.date_range('2025-01-01', periods=60, freq='D')
        np.random.seed(42)
        prices = 100 + np.cumsum(np.random.randn(60) * 0.5)
        return pd.Series(prices, index=dates)

def compare_rsi(data, window=14):
    """Compare RSI calculations"""
    print(f"\n=== RSI Comparison (window={window}) ===")
    
    # pandas-ta version
    try:
        rsi_pandas_ta = ta.rsi(data, length=window)
        print(f"pandas-ta RSI: Available")
    except Exception as e:
        print(f"pandas-ta RSI Error: {e}")
        rsi_pandas_ta = None
    
    # TA-Lib version (current implementation)
    try:
        rsi_talib = talib.RSI(data.values, timeperiod=window)
        rsi_talib_series = pd.Series(rsi_talib, index=data.index)
        print(f"TA-Lib RSI: Available")
    except Exception as e:
        print(f"TA-Lib RSI Error: {e}")
        rsi_talib_series = None
    
    # Compare last 10 values
    if rsi_pandas_ta is not None and rsi_talib_series is not None:
        comparison = pd.DataFrame({
            'pandas_ta': rsi_pandas_ta.tail(10),
            'talib': rsi_talib_series.tail(10)
        })
        comparison['diff'] = comparison['pandas_ta'] - comparison['talib']
        print(comparison)
        
        # Check for significant differences
        max_diff = abs(comparison['diff']).max()
        print(f"Max difference: {max_diff:.6f}")
        
        # Check NaN handling
        print(f"pandas-ta NaN count: {rsi_pandas_ta.isna().sum()}")
        print(f"TA-Lib NaN count: {rsi_talib_series.isna().sum()}")

def compare_sma(data, window=20):
    """Compare SMA calculations"""
    print(f"\n=== SMA Comparison (window={window}) ===")
    
    # pandas-ta version
    try:
        sma_pandas_ta = ta.sma(data, length=window)
        print(f"pandas-ta SMA: Available")
    except Exception as e:
        print(f"pandas-ta SMA Error: {e}")
        sma_pandas_ta = None
    
    # TA-Lib version (current implementation)
    try:
        sma_talib = talib.SMA(data.values, timeperiod=window)
        sma_talib_series = pd.Series(sma_talib, index=data.index)
        print(f"TA-Lib SMA: Available")
    except Exception as e:
        print(f"TA-Lib SMA Error: {e}")
        sma_talib_series = None
    
    # Compare last 10 values
    if sma_pandas_ta is not None and sma_talib_series is not None:
        comparison = pd.DataFrame({
            'pandas_ta': sma_pandas_ta.tail(10),
            'talib': sma_talib_series.tail(10)
        })
        comparison['diff'] = comparison['pandas_ta'] - comparison['talib']
        print(comparison)
        
        max_diff = abs(comparison['diff']).max()
        print(f"Max difference: {max_diff:.6f}")
        
        print(f"pandas-ta NaN count: {sma_pandas_ta.isna().sum()}")
        print(f"TA-Lib NaN count: {sma_talib_series.isna().sum()}")

def compare_moving_average_return(data, window=5):
    """Compare moving average return calculations"""
    print(f"\n=== Moving Average Return Comparison (window={window}) ===")
    
    # pandas-ta version (old way)
    try:
        returns_pandas = data.pct_change()
        ma_return_pandas = returns_pandas.rolling(window=window).mean() * 100
        print(f"pandas version: Available")
    except Exception as e:
        print(f"pandas version Error: {e}")
        ma_return_pandas = None
    
    # TA-Lib version (current implementation)
    try:
        returns_talib = data.pct_change()
        # Handle NaN values by dropping them first
        returns_clean = returns_talib.dropna()
        
        if len(returns_clean) < window:
            # Not enough data for calculation
            ma_return_talib_series = pd.Series([0] * len(data), index=data.index)
        else:
            # Calculate SMA on clean returns
            ma_return_talib = talib.SMA(returns_clean.values, timeperiod=window)
            
            # Create result series aligned with original data index
            result = pd.Series(index=data.index, dtype=float)
            result.iloc[:len(returns_clean)] = ma_return_talib
            
            ma_return_talib_series = result * 100
        
        print(f"TA-Lib version: Available")
    except Exception as e:
        print(f"TA-Lib version Error: {e}")
        ma_return_talib_series = None
    
    # Compare last 10 values
    if ma_return_pandas is not None and ma_return_talib_series is not None:
        comparison = pd.DataFrame({
            'pandas_rolling': ma_return_pandas.tail(10),
            'talib': ma_return_talib_series.tail(10)
        })
        comparison['diff'] = comparison['pandas_rolling'] - comparison['talib']
        print(comparison)
        
        max_diff = abs(comparison['diff']).max()
        print(f"Max difference: {max_diff:.6f}")
        
        print(f"pandas NaN count: {ma_return_pandas.isna().sum()}")
        print(f"TA-Lib NaN count: {ma_return_talib_series.isna().sum()}")
        
        # Check first window values specifically
        print("\nFirst 10 values comparison:")
        first_10_comparison = pd.DataFrame({
            'pandas_rolling': ma_return_pandas.head(10),
            'talib': ma_return_talib_series.head(10)
        })
        first_10_comparison['diff'] = first_10_comparison['pandas_rolling'] - first_10_comparison['talib']
        print(first_10_comparison)
    
    # pandas-ta version (old way)
    try:
        returns_pandas = data.pct_change()
        ma_return_pandas = returns_pandas.rolling(window=window).mean() * 100
        print(f"pandas version: Available")
    except Exception as e:
        print(f"pandas version Error: {e}")
        ma_return_pandas = None
    
    # TA-Lib version (current implementation)
    try:
        returns_talib = data.pct_change()
        ma_return_talib = talib.SMA(returns_talib.values, timeperiod=window)
        ma_return_talib_series = pd.Series(ma_return_talib * 100, index=data.index)
        print(f"TA-Lib version: Available")
    except Exception as e:
        print(f"TA-Lib version Error: {e}")
        ma_return_talib_series = None
    
    # Compare last 10 values
    if ma_return_pandas is not None and ma_return_talib_series is not None:
        comparison = pd.DataFrame({
            'pandas_rolling': ma_return_pandas.tail(10),
            'talib': ma_return_talib_series.tail(10)
        })
        comparison['diff'] = comparison['pandas_rolling'] - comparison['talib']
        print(comparison)
        
        max_diff = abs(comparison['diff']).max()
        print(f"Max difference: {max_diff:.6f}")
        
        print(f"pandas NaN count: {ma_return_pandas.isna().sum()}")
        print(f"TA-Lib NaN count: {ma_return_talib_series.isna().sum()}")

def check_data_quality(data):
    """Check data quality issues that might affect indicators"""
    print("\n=== Data Quality Check ===")
    print(f"Data shape: {data.shape}")
    print(f"Data type: {data.dtype}")
    print(f"NaN count: {data.isna().sum()}")
    print(f"Infinite count: {np.isinf(data).sum()}")
    print(f"First 5 values: {data.head().tolist()}")
    print(f"Last 5 values: {data.tail().tolist()}")

def main():
    print("TA-Lib vs pandas-ta Indicator Comparison")
    print("=" * 50)
    
    # Get sample data
    data = get_sample_data()
    check_data_quality(data)
    
    # Compare indicators
    compare_rsi(data)
    compare_sma(data)
    compare_moving_average_return(data)
    
    print("\n" + "=" * 50)
    print("Analysis complete!")

if __name__ == "__main__":
    main()
