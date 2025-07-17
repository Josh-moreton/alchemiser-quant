#!/usr/bin/env python3
"""
Debug script to test the safe_get_indicator function specifically
"""

import sys
sys.path.append('/Users/joshua.moreton/Documents/GitHub/LQQ3')

from core.nuclear_trading_bot import NuclearTradingBot
import pandas as pd

def debug_safe_get_indicator():
    """Debug the safe_get_indicator function"""
    print("=== DEBUGGING safe_get_indicator FUNCTION ===")
    
    # Create bot instance
    bot = NuclearTradingBot()
    
    # Get market data
    market_data = bot.strategy.get_market_data()
    
    # Test SMR specifically
    symbol = 'SMR'
    if symbol in market_data:
        close = market_data[symbol]['Close']
        print(f"\nTesting {symbol}:")
        print(f"Close data length: {len(close)}")
        print(f"Close data type: {type(close)}")
        print(f"Last close price: {close.iloc[-1]:.4f}")
        
        # Test the raw indicator function
        print(f"\nDirect indicator call:")
        try:
            raw_result = bot.strategy.indicators.moving_average_return(close, 90)
            print(f"Raw result type: {type(raw_result)}")
            print(f"Raw result length: {len(raw_result)}")
            print(f"Raw result last value: {raw_result.iloc[-1]:.4f}")
            print(f"Raw result has iloc: {hasattr(raw_result, 'iloc')}")
            print(f"Raw result length > 0: {len(raw_result) > 0}")
            
            # Test the value extraction
            value = raw_result.iloc[-1]
            print(f"Extracted value: {value:.4f}")
            print(f"Value type: {type(value)}")
            print(f"Value is NaN: {pd.isna(value)}")
            
        except Exception as e:
            print(f"Error in direct call: {e}")
            import traceback
            traceback.print_exc()
        
        # Test the safe_get_indicator function
        print(f"\nSafe get indicator call:")
        try:
            safe_result = bot.strategy.safe_get_indicator(close, bot.strategy.indicators.moving_average_return, 90)
            print(f"Safe result: {safe_result}")
            print(f"Safe result type: {type(safe_result)}")
            
        except Exception as e:
            print(f"Error in safe call: {e}")
            import traceback
            traceback.print_exc()
        
        # Test what happens in the safe_get_indicator function step by step
        print(f"\nStep-by-step safe_get_indicator simulation:")
        try:
            result = bot.strategy.indicators.moving_average_return(close, 90)
            print(f"Step 1 - indicator_func result: {type(result)}")
            
            has_iloc = hasattr(result, 'iloc')
            print(f"Step 2 - has iloc: {has_iloc}")
            
            if has_iloc:
                result_len = len(result)
                print(f"Step 3 - result length: {result_len}")
                
                if result_len > 0:
                    value = result.iloc[-1]
                    print(f"Step 4 - extracted value: {value} (type: {type(value)})")
                    
                    is_nan = pd.isna(value)
                    print(f"Step 5 - is NaN: {is_nan}")
                    
                    if is_nan:
                        print("Step 6 - Value is NaN, looking for last valid value...")
                        valid_values = result.dropna()
                        print(f"Step 7 - Valid values length: {len(valid_values)}")
                        if len(valid_values) > 0:
                            value = valid_values.iloc[-1]
                            print(f"Step 8 - Last valid value: {value}")
                        else:
                            print("Step 8 - No valid values, returning 50.0")
                            value = 50.0
                    
                    final_value = float(value)
                    print(f"Step 9 - Final value: {final_value}")
                else:
                    print("Step 3 - Result length is 0, returning 50.0")
            else:
                print("Step 2 - No iloc attribute, returning 50.0")
                
        except Exception as e:
            print(f"Error in step-by-step: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    debug_safe_get_indicator()
