#!/usr/bin/env python3
"""
Variable Allocation Strategy - Final Implementation
Simple script to check current signal status and allocation recommendation

Strategy Rules:
- Both signals SELL: 33% LQQ3, 67% Cash
- One signal BUY: 66% LQQ3, 34% Cash  
- Both signals BUY: 100% LQQ3
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

def get_current_signals():
    """Fetch current data and calculate MACD and SMA signals"""
    # Fetch recent TQQQ data (need enough for 200-day SMA)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=300)
    
    print("Fetching TQQQ data for signal analysis...")
    tqqq = yf.download('TQQQ', start=start_date, end=end_date, progress=False)
    
    if tqqq.empty:
        raise ValueError("Failed to fetch TQQQ data")
    
    # Handle multi-level columns
    if tqqq.columns.nlevels > 1:
        tqqq.columns = tqqq.columns.get_level_values(0)
    
    # Calculate MACD
    ema_12 = tqqq['Close'].ewm(span=12).mean()
    ema_26 = tqqq['Close'].ewm(span=26).mean()
    tqqq['MACD'] = ema_12 - ema_26
    tqqq['MACD_Signal'] = tqqq['MACD'].ewm(span=9).mean()
    tqqq['MACD_Histogram'] = tqqq['MACD'] - tqqq['MACD_Signal']
    
    # Calculate 200-day SMA
    tqqq['SMA_200'] = tqqq['Close'].rolling(window=200).mean()
    
    # Generate signals
    tqqq['MACD_Bullish'] = (tqqq['MACD'] > tqqq['MACD_Signal']).astype(int)
    tqqq['SMA_Bullish'] = (tqqq['Close'] > tqqq['SMA_200']).astype(int)
    
    # Get latest data
    latest = tqqq.iloc[-1]
    
    return {
        'date': latest.name,
        'price': latest['Close'],
        'sma_200': latest['SMA_200'],
        'macd': latest['MACD'],
        'macd_signal': latest['MACD_Signal'],
        'macd_histogram': latest['MACD_Histogram'],
        'macd_bullish': bool(latest['MACD_Bullish']),
        'sma_bullish': bool(latest['SMA_Bullish']),
        'price_vs_sma_pct': (latest['Close'] / latest['SMA_200'] - 1) * 100
    }

def calculate_allocation(macd_bullish, sma_bullish):
    """Calculate portfolio allocation based on signal combination"""
    bullish_signals = int(macd_bullish) + int(sma_bullish)
    
    if bullish_signals == 0:
        # Both bearish
        lqq3_allocation = 33
        cash_allocation = 67
        signal_strength = "BEARISH"
        action = "DEFENSIVE"
    elif bullish_signals == 1:
        # One bullish
        lqq3_allocation = 66
        cash_allocation = 34
        signal_strength = "MIXED"
        action = "CAUTIOUS"
    else:
        # Both bullish
        lqq3_allocation = 100
        cash_allocation = 0
        signal_strength = "BULLISH"
        action = "AGGRESSIVE"
    
    return {
        'lqq3_pct': lqq3_allocation,
        'cash_pct': cash_allocation,
        'signal_strength': signal_strength,
        'action': action,
        'bullish_signals': bullish_signals
    }

def print_signal_status():
    """Print current signal status and allocation recommendation"""
    try:
        # Get current signals
        signals = get_current_signals()
        allocation = calculate_allocation(signals['macd_bullish'], signals['sma_bullish'])
        
        # Header
        print("="*60)
        print("LQQ3 VARIABLE ALLOCATION STRATEGY")
        print("="*60)
        print(f"📅 Date: {signals['date'].strftime('%Y-%m-%d')}")
        print(f"📊 TQQQ Price: ${signals['price']:.2f}")
        print("-"*60)
        
        # Individual signals
        print("INDIVIDUAL SIGNALS:")
        
        # SMA Signal
        sma_emoji = "🟢" if signals['sma_bullish'] else "🔴"
        sma_status = "BULLISH" if signals['sma_bullish'] else "BEARISH"
        print(f"  📈 200-day SMA: {sma_emoji} {sma_status}")
        print(f"      Level: ${signals['sma_200']:.2f}")
        print(f"      Distance: {signals['price_vs_sma_pct']:+.1f}%")
        
        # MACD Signal
        macd_emoji = "🟢" if signals['macd_bullish'] else "🔴"
        macd_status = "BULLISH" if signals['macd_bullish'] else "BEARISH"
        print(f"  ⚡ MACD: {macd_emoji} {macd_status}")
        print(f"      MACD: {signals['macd']:.4f}")
        print(f"      Signal: {signals['macd_signal']:.4f}")
        print(f"      Histogram: {signals['macd_histogram']:+.4f}")
        
        print("-"*60)
        
        # Combined assessment
        print("COMBINED ASSESSMENT:")
        print(f"  Bullish Signals: {allocation['bullish_signals']}/2")
        print(f"  Signal Strength: {allocation['signal_strength']}")
        print(f"  Market Stance: {allocation['action']}")
        
        print("-"*60)
        
        # Allocation recommendation
        print("PORTFOLIO ALLOCATION:")
        print(f"  🏦 LQQ3: {allocation['lqq3_pct']}%")
        print(f"  💰 Cash: {allocation['cash_pct']}%")
        
        # Action guidance
        print("-"*60)
        print("RECOMMENDATION:")
        
        if allocation['bullish_signals'] == 2:
            print("  🚀 FULLY INVESTED - Both signals bullish")
            print("     Deploy all available capital to LQQ3")
        elif allocation['bullish_signals'] == 1:
            print("  ⚖️  BALANCED APPROACH - Mixed signals")
            print("     Maintain 66% LQQ3 exposure with cash buffer")
            if signals['macd_bullish'] and not signals['sma_bullish']:
                print("     📊 MACD bullish but price below trend line")
            elif signals['sma_bullish'] and not signals['macd_bullish']:
                print("     📈 Trend positive but momentum weakening")
        else:
            print("  🛡️  DEFENSIVE MODE - Both signals bearish")
            print("     Reduce to minimum 33% LQQ3 exposure")
        
        print("="*60)
        
        return signals, allocation
        
    except Exception as e:
        print(f"Error fetching signals: {e}")
        return None, None

def main():
    """Run the variable allocation signal check"""
    print("Variable Allocation Strategy - Current Signal Status")
    print()
    
    signals, allocation = print_signal_status()
    
    if signals and allocation:
        # Additional context
        print("\nSTRATEGY SUMMARY:")
        print("• 33% LQQ3 when both signals bearish (defensive)")
        print("• 66% LQQ3 when one signal bullish (balanced)")
        print("• 100% LQQ3 when both signals bullish (aggressive)")
        print("\nOptimized for risk-adjusted returns and reduced drawdown")
    
    return signals, allocation

if __name__ == "__main__":
    signals, allocation = main()
