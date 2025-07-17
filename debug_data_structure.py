#!/usr/bin/env python3
"""
Debug script to understand data structure issues
"""

import sys
sys.path.append('/Users/joshua.moreton/Documents/GitHub/LQQ3')

from core.nuclear_trading_bot import NuclearTradingBot
import pandas as pd

def debug_data_structure():
    """Debug data structure"""
    print("=== DEBUGGING DATA STRUCTURE ===")
    
    # Create bot instance
    bot = NuclearTradingBot()
    
    # Get market data
    market_data = bot.strategy.get_market_data()
    
    # Check SMR specifically
    symbol = 'SMR'
    if symbol in market_data:
        df = market_data[symbol]
        print(f"\n{symbol} DataFrame:")
        print(f"  Type: {type(df)}")
        print(f"  Shape: {df.shape}")
        print(f"  Columns: {list(df.columns)}")
        print(f"  Index type: {type(df.index)}")
        print(f"  First few rows:")
        print(df.head())
        
        # Try to extract Close column
        print(f"\nExtracting Close column:")
        try:
            close = df['Close']
            print(f"  Close type: {type(close)}")
            print(f"  Close shape: {close.shape if hasattr(close, 'shape') else 'No shape'}")
            print(f"  Close last value: {close.iloc[-1]}")
            print(f"  Close last value type: {type(close.iloc[-1])}")
        except Exception as e:
            print(f"  Error extracting Close: {e}")
            
        # Try alternative extraction methods
        print(f"\nAlternative extraction methods:")
        try:
            # Method 1: Direct column access
            close1 = df.loc[:, 'Close']
            print(f"  df.loc[:, 'Close'] type: {type(close1)}")
            
            # Method 2: Using squeeze() to ensure Series
            close2 = df['Close'].squeeze()
            print(f"  df['Close'].squeeze() type: {type(close2)}")
            
            # Method 3: Using values and creating Series
            close3 = pd.Series(df['Close'].values, index=df.index)
            print(f"  pd.Series(df['Close'].values, index=df.index) type: {type(close3)}")
            
        except Exception as e:
            print(f"  Error in alternative methods: {e}")

if __name__ == "__main__":
    debug_data_structure()
