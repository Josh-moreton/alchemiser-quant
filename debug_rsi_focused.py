#!/usr/bin/env python3
"""
Debug IOO RSI calculation by comparing multiple data fetches
"""

import sys
import os
sys.path.append('/Users/joshmoreton/GitHub/LQQ3')

from core.data_provider import DataProvider
from core.indicators import TechnicalIndicators
import pandas as pd
import time
from datetime import datetime

def debug_ioo_rsi():
    """Debug IOO RSI by fetching data multiple times"""
    print("🔍 DEBUGGING IOO RSI VOLATILITY")
    print("=" * 50)
    
    provider = DataProvider()
    indicators = TechnicalIndicators()
    
    results = []
    
    # Fetch data 3 times with 15 seconds between
    for i in range(3):
        print(f"\n📊 Fetch #{i+1} at {datetime.now().strftime('%H:%M:%S')}")
        print("-" * 30)
        
        # Fetch fresh data
        data = provider.get_data('IOO')
        
        if data.empty:
            print("❌ No data")
            continue
        
        # Calculate RSI
        close_prices = data['Close']
        rsi_series = indicators.rsi(close_prices, window=10)
        current_rsi = rsi_series.iloc[-1]
        
        # Get recent price data
        last_5_close = close_prices.tail(5)
        
        print(f"Data range: {data.index[0].date()} to {data.index[-1].date()}")
        print(f"Current RSI(10): {current_rsi:.8f}")
        print("Last 5 close prices:")
        for date, price in last_5_close.items():
            print(f"  {str(date.date())}: ${price:.4f}")
        
        # Calculate price changes for RSI calculation
        price_changes = close_prices.diff().tail(10)
        print("\\nLast 10 price changes (for RSI calc):")
        for date, change in price_changes.items():
            if not pd.isna(change):
                print(f"  {str(date.date())}: {change:+.4f}")
        
        results.append({
            'time': datetime.now(),
            'rsi': current_rsi,
            'last_close': close_prices.iloc[-1],
            'last_date': data.index[-1],
            'data_hash': hash(tuple(close_prices.tail(20)))  # Hash of recent prices
        })
        
        if i < 2:
            print("⏳ Waiting 15 seconds...")
            time.sleep(15)
    
    # Analysis
    print("\\n📈 ANALYSIS")
    print("=" * 50)
    
    if len(results) >= 2:
        rsi_values = [r['rsi'] for r in results]
        data_hashes = [r['data_hash'] for r in results]
        
        print("RSI Values:")
        for i, r in enumerate(results):
            print(f"  Fetch {i+1}: {r['rsi']:.8f} at {r['time'].strftime('%H:%M:%S')}")
        
        rsi_range = max(rsi_values) - min(rsi_values)
        print(f"\\nRSI Range: {rsi_range:.8f}")
        
        # Check if underlying data is changing
        if len(set(data_hashes)) == 1:
            print("✅ Underlying price data is IDENTICAL")
            if rsi_range > 1e-10:
                print("⚠️  But RSI still varies - calculation issue!")
        else:
            print("⚠️  Underlying price data is CHANGING between fetches")
            print("This explains the RSI variation")
    
if __name__ == "__main__":
    debug_ioo_rsi()
