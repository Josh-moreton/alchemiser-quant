#!/usr/bin/env python3
"""
Debug script to test the actual indicator calculations that the bot uses
"""

import sys
sys.path.append('/Users/joshua.moreton/Documents/GitHub/LQQ3')

from core.nuclear_trading_bot import NuclearTradingBot
from core.indicators import TechnicalIndicators
import pandas as pd

def debug_bot_indicators():
    """Debug the actual indicators the bot calculates"""
    print("=== DEBUGGING BOT INDICATOR CALCULATIONS ===")
    
    # Create bot instance
    bot = NuclearTradingBot()
    
    # Get market data (same as bot does)
    market_data = bot.strategy.get_market_data()
    
    # Calculate indicators (same as bot does)
    indicators = bot.strategy.calculate_indicators(market_data)
    
    print(f"\nSPY indicators:")
    if 'SPY' in indicators:
        spy_indicators = indicators['SPY']
        print(f"  current_price: ${spy_indicators['current_price']:.2f}")
        print(f"  ma_200: ${spy_indicators['ma_200']:.2f}")
        print(f"  rsi_10: {spy_indicators['rsi_10']:.2f}")
        print(f"  rsi_20: {spy_indicators['rsi_20']:.2f}")
        print(f"  ma_20: ${spy_indicators['ma_20']:.2f}")
        print(f"  ma_return_90: {spy_indicators['ma_return_90']:.4f}")
        print(f"  cum_return_60: {spy_indicators['cum_return_60']:.4f}")
        
        # Key bull/bear decision
        bull_market = spy_indicators['current_price'] > spy_indicators['ma_200']
        print(f"  Bull Market (current > ma_200): {bull_market}")
    else:
        print("  SPY indicators not found!")
    
    print(f"\nTQQQ indicators:")
    if 'TQQQ' in indicators:
        tqqq_indicators = indicators['TQQQ']
        print(f"  current_price: ${tqqq_indicators['current_price']:.2f}")
        print(f"  ma_20: ${tqqq_indicators['ma_20']:.2f}")
        print(f"  rsi_10: {tqqq_indicators['rsi_10']:.2f}")
        
        # Key bear subgroup decision
        tqqq_above_ma = tqqq_indicators['current_price'] > tqqq_indicators['ma_20']
        print(f"  TQQQ above MA(20): {tqqq_above_ma}")
    else:
        print("  TQQQ indicators not found!")
    
    print(f"\nPSQ indicators:")
    if 'PSQ' in indicators:
        psq_indicators = indicators['PSQ']
        print(f"  rsi_10: {psq_indicators['rsi_10']:.2f}")
        print(f"  rsi_20: {psq_indicators['rsi_20']:.2f}")
        
        # Key bear trigger
        psq_oversold = psq_indicators['rsi_10'] < 35
        print(f"  PSQ oversold (RSI < 35): {psq_oversold}")
    else:
        print("  PSQ indicators not found!")
    
    # Now test the actual strategy evaluation
    print(f"\n=== STRATEGY EVALUATION ===")
    symbol, action, reason = bot.strategy.evaluate_nuclear_strategy(indicators, market_data)
    print(f"Strategy Result: {action} {symbol}")
    print(f"Reason: {reason}")

def debug_safe_get_indicator():
    """Debug the safe_get_indicator function specifically"""
    print("\n=== DEBUGGING SAFE_GET_INDICATOR ===")
    
    bot = NuclearTradingBot()
    market_data = bot.strategy.get_market_data()
    
    if 'SPY' in market_data:
        spy_data = market_data['SPY']['Close']
        
        # Test each indicator directly
        ti = TechnicalIndicators()
        
        print(f"SPY data length: {len(spy_data)}")
        print(f"SPY last price: ${spy_data.iloc[-1]:.2f}")
        
        # Test MA(200) calculation
        ma_200_direct = ti.moving_average(spy_data, 200)
        print(f"MA(200) direct result type: {type(ma_200_direct)}")
        print(f"MA(200) direct length: {len(ma_200_direct)}")
        print(f"MA(200) last value: {ma_200_direct.iloc[-1]:.2f}")
        print(f"MA(200) has NaN: {pd.isna(ma_200_direct.iloc[-1])}")
        
        # Test safe_get_indicator
        ma_200_safe = bot.strategy.safe_get_indicator(spy_data, ti.moving_average, 200)
        print(f"MA(200) safe result: {ma_200_safe:.2f}")
        
        # Test RSI(10)
        rsi_10_direct = ti.rsi(spy_data, 10)
        print(f"RSI(10) direct result type: {type(rsi_10_direct)}")
        print(f"RSI(10) direct length: {len(rsi_10_direct)}")
        print(f"RSI(10) last value: {rsi_10_direct.iloc[-1]:.2f}")
        print(f"RSI(10) has NaN: {pd.isna(rsi_10_direct.iloc[-1])}")
        
        rsi_10_safe = bot.strategy.safe_get_indicator(spy_data, ti.rsi, 10)
        print(f"RSI(10) safe result: {rsi_10_safe:.2f}")

if __name__ == "__main__":
    debug_bot_indicators()
    debug_safe_get_indicator()
