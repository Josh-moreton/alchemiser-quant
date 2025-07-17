#!/usr/bin/env python3
"""
Debug script to test bull vs bear market indicators specifically
"""

import pandas as pd
import numpy as np
import yfinance as yf
import talib
import pandas_ta as ta

# Import our indicator functions
import sys
sys.path.append('/Users/joshua.moreton/Documents/GitHub/LQQ3')
from core.indicators import TechnicalIndicators

def get_market_data():
    """Get market data for key symbols"""
    symbols = ['SPY', 'TQQQ', 'PSQ', 'TLT', 'IEF']
    data = {}
    
    for symbol in symbols:
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="200d")  # Need enough data for 200-day MA
            data[symbol] = hist['Close']
            print(f"✅ {symbol}: {len(hist)} days of data")
        except Exception as e:
            print(f"❌ {symbol}: Error - {e}")
            
    return data

def debug_bull_bear_logic(data):
    """Debug the specific logic that determines bull vs bear market"""
    print("\n=== BULL vs BEAR MARKET LOGIC DEBUG ===")
    
    if 'SPY' not in data:
        print("❌ Missing SPY data")
        return
    
    spy_data = data['SPY']
    
    # Key indicators for bull/bear decision
    print("\n1. SPY Current Price vs 200-day MA (Bull/Bear determinant):")
    
    # pandas-ta version
    try:
        spy_ma_200_pandas = ta.sma(spy_data, length=200)
        spy_current_pandas = spy_data.iloc[-1]
        
        if spy_ma_200_pandas is not None and len(spy_ma_200_pandas) > 0:
            if hasattr(spy_ma_200_pandas, 'iloc'):
                spy_ma_200_val_pandas = spy_ma_200_pandas.iloc[-1]
            else:
                spy_ma_200_val_pandas = spy_ma_200_pandas[-1]
            
            print(f"   pandas-ta: SPY Current = ${spy_current_pandas:.2f}")
            print(f"   pandas-ta: SPY MA(200) = ${spy_ma_200_val_pandas:.2f}")
            print(f"   pandas-ta: Bull Market? {spy_current_pandas > spy_ma_200_val_pandas}")
        else:
            print("   pandas-ta: No MA(200) data available")
            spy_ma_200_val_pandas = None
        
    except Exception as e:
        print(f"   pandas-ta Error: {e}")
        spy_ma_200_val_pandas = None
    
    # TA-Lib version (our implementation)
    try:
        ti = TechnicalIndicators()
        spy_ma_200_talib = ti.moving_average(spy_data, 200)
        spy_current_talib = spy_data.iloc[-1]
        spy_ma_200_val_talib = spy_ma_200_talib.iloc[-1]
        
        print(f"   TA-Lib: SPY Current = ${spy_current_talib:.2f}")
        print(f"   TA-Lib: SPY MA(200) = ${spy_ma_200_val_talib:.2f}")
        print(f"   TA-Lib: Bull Market? {spy_current_talib > spy_ma_200_val_talib}")
        
        # Check for differences
        ma_diff = abs(spy_ma_200_val_pandas - spy_ma_200_val_talib)
        print(f"   MA(200) Difference: ${ma_diff:.6f}")
        
    except Exception as e:
        print(f"   TA-Lib Error: {e}")
        
    print("\n2. Other Key Indicators:")
    
    # Check RSI values for overbought conditions
    for symbol in ['SPY', 'TQQQ']:
        if symbol in data:
            try:
                symbol_data = data[symbol]
                
                # RSI(10) - key for overbought detection
                rsi_10_pandas = ta.rsi(symbol_data, length=10)
                rsi_10_talib = ti.rsi(symbol_data, 10)
                
                if rsi_10_pandas is not None and len(rsi_10_pandas) > 0:
                    if hasattr(rsi_10_pandas, 'iloc'):
                        rsi_10_val_pandas = rsi_10_pandas.iloc[-1]
                    else:
                        rsi_10_val_pandas = rsi_10_pandas[-1]
                else:
                    rsi_10_val_pandas = None
                    
                if rsi_10_talib is not None and len(rsi_10_talib) > 0:
                    rsi_10_val_talib = rsi_10_talib.iloc[-1]
                else:
                    rsi_10_val_talib = None
                
                if rsi_10_val_pandas is not None and rsi_10_val_talib is not None:
                    print(f"   {symbol} RSI(10) pandas-ta: {rsi_10_val_pandas:.2f}")
                    print(f"   {symbol} RSI(10) TA-Lib: {rsi_10_val_talib:.2f}")
                    print(f"   {symbol} RSI(10) Difference: {abs(rsi_10_val_pandas - rsi_10_val_talib):.6f}")
                else:
                    print(f"   {symbol} RSI(10): Data not available")
                
            except Exception as e:
                print(f"   {symbol} RSI Error: {e}")

def debug_nuclear_portfolio_selection(data):
    """Debug nuclear portfolio stock selection"""
    print("\n=== NUCLEAR PORTFOLIO SELECTION DEBUG ===")
    
    nuclear_symbols = ['SMR', 'BWXT', 'LEU', 'EXC', 'NLR', 'OKLO']
    nuclear_data = {}
    
    # Get nuclear stock data
    for symbol in nuclear_symbols:
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="200d")
            nuclear_data[symbol] = hist['Close']
            print(f"✅ {symbol}: {len(hist)} days of data")
        except Exception as e:
            print(f"❌ {symbol}: Error - {e}")
    
    print("\n90-day Moving Average Returns (for portfolio selection):")
    
    ti = TechnicalIndicators()
    nuclear_performance = []
    
    for symbol in nuclear_symbols:
        if symbol in nuclear_data:
            try:
                symbol_data = nuclear_data[symbol]
                
                # pandas-ta version
                returns_pandas = symbol_data.pct_change()
                ma_return_90_pandas = returns_pandas.rolling(window=90).mean() * 100
                ma_return_90_val_pandas = ma_return_90_pandas.iloc[-1]
                
                # TA-Lib version
                ma_return_90_talib = ti.moving_average_return(symbol_data, 90)
                ma_return_90_val_talib = ma_return_90_talib.iloc[-1]
                
                print(f"   {symbol}:")
                print(f"     pandas-ta MA Return(90): {ma_return_90_val_pandas:.4f}%")
                print(f"     TA-Lib MA Return(90): {ma_return_90_val_talib:.4f}%")
                print(f"     Difference: {abs(ma_return_90_val_pandas - ma_return_90_val_talib):.6f}%")
                
                nuclear_performance.append((symbol, ma_return_90_val_talib))
                
            except Exception as e:
                print(f"   {symbol} Error: {e}")
    
    # Show top 3 selection
    nuclear_performance.sort(key=lambda x: x[1], reverse=True)
    print(f"\nTop 3 Nuclear Stocks (TA-Lib):")
    for i, (symbol, perf) in enumerate(nuclear_performance[:3]):
        print(f"   {i+1}. {symbol}: {perf:.4f}%")

def main():
    print("BULL vs BEAR MARKET INDICATOR DEBUG")
    print("=" * 50)
    
    # Get market data
    data = get_market_data()
    
    # Debug bull/bear logic
    debug_bull_bear_logic(data)
    
    # Debug nuclear portfolio selection
    debug_nuclear_portfolio_selection(data)
    
    print("\n" + "=" * 50)
    print("Debug complete!")

if __name__ == "__main__":
    main()
