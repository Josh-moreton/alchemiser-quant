#!/usr/bin/env python3
"""
Debug script to test the exact same data and calculations the bot uses
"""

import sys
sys.path.append('/Users/joshua.moreton/Documents/GitHub/LQQ3')

from core.nuclear_trading_bot import NuclearTradingBot
import pandas as pd

def debug_exact_bot_logic():
    """Debug the exact same logic and data the bot uses"""
    print("=== DEBUGGING EXACT BOT LOGIC ===")
    
    # Create bot instance
    bot = NuclearTradingBot()
    
    # Get market data (exact same as bot)
    market_data = bot.strategy.get_market_data()
    
    # Calculate indicators (exact same as bot)
    indicators = bot.strategy.calculate_indicators(market_data)
    
    print(f"\nNuclear symbols and their ma_return_90 values:")
    nuclear_symbols = ['SMR', 'BWXT', 'LEU', 'EXC', 'NLR', 'OKLO']
    
    for symbol in nuclear_symbols:
        if symbol in indicators:
            ma_return_90 = indicators[symbol]['ma_return_90']
            print(f"  {symbol}: {ma_return_90:.4f}")
            
            # Also check the raw calculation
            if symbol in market_data:
                close = market_data[symbol]['Close']
                ma_return_raw = bot.strategy.indicators.moving_average_return(close, 90)
                
                # Handle the raw calculation value properly
                try:
                    raw_val = ma_return_raw.iloc[-1]
                    # Convert to scalar if it's a Series
                    if hasattr(raw_val, 'item'):
                        raw_val = raw_val.item()
                    
                    if pd.isna(raw_val):
                        print(f"    Raw calculation last value: NaN")
                    else:
                        print(f"    Raw calculation last value: {raw_val:.4f}")
                        
                    print(f"    Raw calculation has NaN at end: {pd.isna(raw_val)}")
                    
                    # Find last valid value
                    valid_values = ma_return_raw.dropna()
                    if len(valid_values) > 0:
                        last_valid = valid_values.iloc[-1]
                        if hasattr(last_valid, 'item'):
                            last_valid = last_valid.item()
                        print(f"    Last valid value: {last_valid:.4f}")
                    else:
                        print(f"    No valid values found")
                except Exception as e:
                    print(f"    Error processing raw calculation: {e}")
                    print(f"    Type of ma_return_raw: {type(ma_return_raw)}")
                    print(f"    Type of ma_return_raw.iloc[-1]: {type(ma_return_raw.iloc[-1])}")
                print()
        else:
            print(f"  {symbol}: Not in indicators")
    
    # Get nuclear portfolio (exact same as bot)
    nuclear_portfolio = bot.strategy.get_nuclear_portfolio(indicators, market_data)
    
    print(f"\nNuclear Portfolio from bot logic:")
    if nuclear_portfolio:
        for symbol, data in nuclear_portfolio.items():
            print(f"  {symbol}: {data['weight']:.1%} (performance: {data['performance']:.4f}%)")
    else:
        print("No nuclear portfolio generated")

if __name__ == "__main__":
    debug_exact_bot_logic()
