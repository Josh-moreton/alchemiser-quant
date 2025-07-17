#!/usr/bin/env python3
"""
Test script to verify Alpaca data provider structure
"""

import sys
sys.path.append('/Users/joshua.moreton/Documents/GitHub/LQQ3')

from core.data_provider import DataProvider
import pandas as pd

def test_alpaca_data_structure():
    """Test Alpaca data provider structure"""
    print("=== TESTING ALPACA DATA STRUCTURE ===")
    
    # Create data provider with Alpaca
    data_provider = DataProvider(use_alpaca=True)
    
    # Test with SMR
    symbol = 'SMR'
    print(f"\nTesting {symbol}:")
    
    try:
        # Get data
        df = data_provider.get_data(symbol, period="200d", interval="1d")
        
        print(f"DataFrame type: {type(df)}")
        print(f"DataFrame shape: {df.shape}")
        print(f"DataFrame columns: {list(df.columns)}")
        print(f"DataFrame index: {type(df.index)}")
        
        if not df.empty:
            print(f"First few rows:")
            print(df.head())
            print(f"Last few rows:")
            print(df.tail())
            
            # Test Close column extraction
            close = df['Close']
            print(f"\nClose column type: {type(close)}")
            print(f"Close column shape: {close.shape}")
            print(f"Close last value: {close.iloc[-1]}")
            print(f"Close last value type: {type(close.iloc[-1])}")
            
            # Test current price
            current_price = data_provider.get_current_price(symbol)
            print(f"\nCurrent price: {current_price}")
            print(f"Current price type: {type(current_price)}")
            
        else:
            print("DataFrame is empty")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_alpaca_data_structure()
