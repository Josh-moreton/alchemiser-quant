#!/usr/bin/env python3
"""
LQQ3 Daily Signal Check - Optimal Binary Exit Strategy
Desktop app for daily trading decisions using TQQQ signals
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

def fetch_current_signals():
    """Fetch current TQQQ data and calculate signals"""
    try:
        # Fetch recent TQQQ data (need enough for 200-day SMA)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=300)
        
        print("Fetching TQQQ market data...")
        tqqq = yf.download('TQQQ', start=start_date, end=end_date, progress=False)
        
        if tqqq.empty:
            raise ValueError("Failed to fetch TQQQ data")
        
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
        
        # Calculate signal changes (compare to previous day)
        tqqq['MACD_Bullish'] = (tqqq['MACD'] > tqqq['MACD_Signal']).astype(int)
        tqqq['SMA_Bullish'] = (tqqq['Close'] > tqqq['SMA_200']).astype(int)
        tqqq['MACD_Changed'] = tqqq['MACD_Bullish'].diff() != 0
        tqqq['SMA_Changed'] = tqqq['SMA_Bullish'].diff() != 0
        
        # Latest values
        latest = tqqq.iloc[-1]
        previous = tqqq.iloc[-2] if len(tqqq) > 1 else latest
        
        return {
            'date': latest.name,
            'tqqq_price': latest['Close'],
            'sma_200': latest['SMA_200'],
            'price_vs_sma_pct': (latest['Close'] / latest['SMA_200'] - 1) * 100,
            'macd': latest['MACD'],
            'macd_signal': latest['MACD_Signal'],
            'macd_histogram': latest['MACD_Histogram'],
            'macd_bullish': bool(latest['MACD_Bullish']),
            'sma_bullish': bool(latest['SMA_Bullish']),
            'macd_changed': bool(latest['MACD_Changed']),
            'sma_changed': bool(latest['SMA_Changed']),
            'previous_macd_bullish': bool(previous['MACD_Bullish']),
            'previous_sma_bullish': bool(previous['SMA_Bullish'])
        }
        
    except Exception as e:
        raise Exception(f"Data fetch error: {e}")

def calculate_optimal_allocation(signals):
    """Calculate allocation using optimal binary exit strategy"""
    macd_bullish = signals['macd_bullish']
    sma_bullish = signals['sma_bullish']
    bullish_count = int(macd_bullish) + int(sma_bullish)
    
    # Optimal allocation based on signal strength
    if bullish_count == 0:
        allocation_pct = 33
        cash_pct = 67
        stance = "DEFENSIVE"
        emoji = "🛡️"
        recommendation = "Minimum exposure - both signals bearish"
    elif bullish_count == 1:
        allocation_pct = 66
        cash_pct = 34
        stance = "BALANCED"
        emoji = "⚖️"
        if macd_bullish and not sma_bullish:
            recommendation = "Momentum positive, trend neutral"
        else:
            recommendation = "Trend positive, momentum weak"
    else:  # bullish_count == 2
        allocation_pct = 100
        cash_pct = 0
        stance = "AGGRESSIVE"
        emoji = "🚀"
        recommendation = "Maximum exposure - both signals bullish"
    
    return {
        'allocation_pct': allocation_pct,
        'cash_pct': cash_pct,
        'stance': stance,
        'emoji': emoji,
        'recommendation': recommendation,
        'bullish_count': bullish_count
    }

def detect_signal_changes(signals):
    """Detect any signal changes from previous day"""
    changes = []
    
    if signals['macd_changed']:
        old_status = "bullish" if signals['previous_macd_bullish'] else "bearish"
        new_status = "bullish" if signals['macd_bullish'] else "bearish"
        changes.append(f"MACD: {old_status} → {new_status}")
    
    if signals['sma_changed']:
        old_status = "bullish" if signals['previous_sma_bullish'] else "bearish"
        new_status = "bullish" if signals['sma_bullish'] else "bearish"
        changes.append(f"SMA: {old_status} → {new_status}")
    
    return changes

def print_daily_report():
    """Print comprehensive daily trading report"""
    try:
        # Get current signals
        signals = fetch_current_signals()
        allocation = calculate_optimal_allocation(signals)
        changes = detect_signal_changes(signals)
        
        # Header
        print("="*60)
        print("LQQ3 DAILY TRADING SIGNAL")
        print("="*60)
        print(f"📅 {signals['date'].strftime('%A, %B %d, %Y')}")
        print(f"📊 TQQQ Price: ${signals['tqqq_price']:.2f}")
        print("-"*60)
        
        # Individual signals with details
        print("SIGNAL STATUS:")
        
        # SMA Signal
        sma_emoji = "🟢" if signals['sma_bullish'] else "🔴"
        sma_status = "BULLISH" if signals['sma_bullish'] else "BEARISH"
        print(f"  📈 200-day SMA: {sma_emoji} {sma_status}")
        print(f"      SMA Level: ${signals['sma_200']:.2f}")
        print(f"      Distance: {signals['price_vs_sma_pct']:+.1f}%")
        
        # MACD Signal
        macd_emoji = "🟢" if signals['macd_bullish'] else "🔴"
        macd_status = "BULLISH" if signals['macd_bullish'] else "BEARISH"
        print(f"  ⚡ MACD: {macd_emoji} {macd_status}")
        print(f"      MACD: {signals['macd']:.4f}")
        print(f"      Signal: {signals['macd_signal']:.4f}")
        print(f"      Histogram: {signals['macd_histogram']:+.4f}")
        
        print("-"*60)
        
        # Signal changes alert
        if changes:
            print("🚨 SIGNAL CHANGES:")
            for change in changes:
                print(f"   {change}")
            print("-"*60)
        
        # Current recommendation
        print("PORTFOLIO ALLOCATION:")
        print(f"  {allocation['emoji']} {allocation['stance']}")
        print(f"  🏦 LQQ3: {allocation['allocation_pct']}%")
        print(f"  💰 Cash: {allocation['cash_pct']}%")
        print(f"  Signal Strength: {allocation['bullish_count']}/2")
        
        print("-"*60)
        
        # Action guidance
        print("RECOMMENDATION:")
        print(f"  {allocation['recommendation']}")
        
        if changes:
            print(f"\n  ACTION REQUIRED: Rebalance portfolio due to signal changes")
        else:
            print(f"\n  ACTION: Maintain current allocation")
        
        # Next signals to watch
        print(f"\nNEXT SIGNALS TO WATCH:")
        if not signals['macd_bullish']:
            print(f"  • MACD crossover above signal line (currently {signals['macd']:.4f} vs {signals['macd_signal']:.4f})")
        if not signals['sma_bullish']:
            print(f"  • TQQQ price above 200 SMA (currently ${signals['tqqq_price']:.2f} vs ${signals['sma_200']:.2f})")
        if signals['macd_bullish'] and signals['sma_bullish']:
            print(f"  • Watch for any signal deterioration")
        
        print("="*60)
        
        return {
            'signals': signals,
            'allocation': allocation,
            'changes': changes
        }
        
    except Exception as e:
        print(f"❌ Error generating report: {e}")
        return None

if __name__ == "__main__":
    result = print_daily_report()
