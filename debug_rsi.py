#!/usr/bin/env python3
"""
Debug script to analyze IOO RSI calculation stability
"""

import pandas as pd
from core.data_provider import AlpacaDataProvider
from core.indicators import TechnicalIndicators
import numpy as np
import time
from datetime import datetime

def analyze_rsi_stability():
    """Analyze RSI calculation stability over multiple fetches"""
    print("🔍 DEBUGGING IOO RSI CALCULATION")
    print("=" * 60)
    
    # Initialize data provider
    data_provider = AlpacaDataProvider()
    indicators = TechnicalIndicators()
    
    results = []
    
    # Fetch IOO data multiple times to see if RSI changes
    for i in range(3):
        print(f"\n📊 Fetch #{i+1} at {datetime.now().strftime('%H:%M:%S')}")
        print("-" * 40)
        
        # Fetch data
        data = data_provider.get_data('IOO')
        
        if data.empty:
            print("❌ No data received")
            continue
            
        print(f"Data shape: {data.shape}")
        print(f"Date range: {data.index[0].date()} to {data.index[-1].date()}")
        
        # Calculate RSI
        close_prices = data['Close']
        rsi_series = indicators.rsi(close_prices, window=10)
        
        # Get last few RSI values
        last_5_rsi = rsi_series.tail(5)
        current_rsi = rsi_series.iloc[-1]
        
        print(f"Current RSI(10): {current_rsi:.10f}")
        print("Last 5 RSI values:")
        for date, rsi_val in last_5_rsi.items():
            print(f"  {date.date()}: {rsi_val:.6f}")
        
        # Check for NaN values
        nan_count = rsi_series.isna().sum()
        print(f"NaN values in RSI: {nan_count}")
        
        # Store results
        results.append({
            'fetch_time': datetime.now(),
            'rsi_current': current_rsi,
            'data_shape': data.shape,
            'last_date': data.index[-1],
            'last_close': close_prices.iloc[-1]
        })
        
        if i < 2:  # Don't wait after the last iteration
            print("⏳ Waiting 30 seconds...")
            time.sleep(30)
    
    # Analysis
    print("\n📈 RSI STABILITY ANALYSIS")
    print("=" * 60)
    
    if len(results) > 1:
        rsi_values = [r['rsi_current'] for r in results]
        rsi_std = np.std(rsi_values)
        rsi_range = max(rsi_values) - min(rsi_values)
        
        print(f"RSI Values: {[f'{rsi:.6f}' for rsi in rsi_values]}")
        print(f"RSI Standard Deviation: {rsi_std:.6f}")
        print(f"RSI Range: {rsi_range:.6f}")
        
        if rsi_range > 0.1:
            print("⚠️  WARNING: RSI showing significant variation!")
            print("This suggests data inconsistency or calculation issues")
        else:
            print("✅ RSI appears stable across fetches")
            
        # Check if data is changing
        last_dates = [r['last_date'] for r in results]
        last_closes = [r['last_close'] for r in results]
        
        if len(set(last_dates)) > 1:
            print("📅 Different last dates detected:")
            for i, date in enumerate(last_dates):
                print(f"  Fetch {i+1}: {date}")
        
        if len(set(last_closes)) > 1:
            print("💰 Different last close prices detected:")
            for i, close in enumerate(last_closes):
                print(f"  Fetch {i+1}: ${close:.4f}")

if __name__ == "__main__":
    analyze_rsi_stability()
