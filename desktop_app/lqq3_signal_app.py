#!/usr/bin/env python3
"""
LQQ3 Trading Signal Desktop App
Clean, simple daily signal checker for optimal allocation strategy

STRATEGY: Binary Exit with Laddered Entry
- 0 bullish signals → 33% LQQ3
- 1 bullish signal  → 66% LQQ3  
- 2 bullish signals → 100% LQQ3
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import sys
import warnings
warnings.filterwarnings('ignore')

class LQQ3SignalApp:
    def __init__(self):
        self.version = "1.0"
        self.strategy_name = "Binary Exit with Laddered Entry"
        
    def fetch_signals(self):
        """Fetch current TQQQ data and calculate signals"""
        try:
            # Fetch recent TQQQ data (need enough for 200-day SMA)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=300)
            
            print("🔄 Fetching market data...")
            tqqq = yf.download('TQQQ', start=start_date, end=end_date, progress=False)
            
            if tqqq.empty:
                raise ValueError("No data received from Yahoo Finance")
            
            if tqqq.columns.nlevels > 1:
                tqqq.columns = tqqq.columns.get_level_values(0)
            
            # Calculate MACD (12, 26, 9)
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
            
            # Detect changes
            tqqq['MACD_Changed'] = tqqq['MACD_Bullish'].diff().fillna(0) != 0
            tqqq['SMA_Changed'] = tqqq['SMA_Bullish'].diff().fillna(0) != 0
            
            # Get latest and previous
            latest = tqqq.iloc[-1]
            previous = tqqq.iloc[-2] if len(tqqq) > 1 else latest
            
            return {
                'success': True,
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
                'prev_macd_bullish': bool(previous['MACD_Bullish']),
                'prev_sma_bullish': bool(previous['SMA_Bullish'])
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def calculate_allocation(self, signals):
        """Calculate optimal allocation based on signal strength"""
        if not signals['success']:
            return None
            
        macd_bullish = signals['macd_bullish']
        sma_bullish = signals['sma_bullish']
        bullish_count = int(macd_bullish) + int(sma_bullish)
        
        # Allocation rules
        if bullish_count == 0:
            return {
                'lqq3_pct': 33,
                'cash_pct': 67,
                'stance': 'DEFENSIVE',
                'emoji': '🛡️',
                'color': 'RED',
                'description': 'Minimum exposure - both signals bearish',
                'action': 'Maintain defensive position'
            }
        elif bullish_count == 1:
            desc = "Momentum positive, trend neutral" if macd_bullish else "Trend positive, momentum weak"
            return {
                'lqq3_pct': 66,
                'cash_pct': 34,
                'stance': 'BALANCED',
                'emoji': '⚖️',
                'color': 'YELLOW',
                'description': desc,
                'action': 'Moderate exposure with cash buffer'
            }
        else:  # bullish_count == 2
            return {
                'lqq3_pct': 100,
                'cash_pct': 0,
                'stance': 'AGGRESSIVE',
                'emoji': '🚀',
                'color': 'GREEN',
                'description': 'Maximum exposure - both signals strongly bullish',
                'action': 'Full investment recommended'
            }
    
    def detect_changes(self, signals):
        """Detect signal changes and trading actions"""
        if not signals['success']:
            return []
            
        changes = []
        
        if signals['macd_changed']:
            old_state = "bullish" if signals['prev_macd_bullish'] else "bearish"
            new_state = "bullish" if signals['macd_bullish'] else "bearish"
            changes.append(f"MACD signal changed: {old_state} → {new_state}")
        
        if signals['sma_changed']:
            old_state = "bullish" if signals['prev_sma_bullish'] else "bearish"
            new_state = "bullish" if signals['sma_bullish'] else "bearish"
            changes.append(f"SMA signal changed: {old_state} → {new_state}")
        
        return changes
    
    def print_header(self):
        """Print app header"""
        print("=" * 65)
        print(f"🏦 LQQ3 TRADING SIGNAL APP v{self.version}")
        print("=" * 65)
        print(f"Strategy: {self.strategy_name}")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("-" * 65)
    
    def print_signals(self, signals):
        """Print signal status"""
        if not signals['success']:
            print(f"❌ Error: {signals['error']}")
            return
            
        print("📊 MARKET DATA:")
        print(f"   TQQQ Price: ${signals['tqqq_price']:.2f}")
        print(f"   Date: {signals['date'].strftime('%A, %B %d, %Y')}")
        print()
        
        print("📈 SIGNAL STATUS:")
        
        # SMA Signal
        sma_emoji = "🟢" if signals['sma_bullish'] else "🔴"
        sma_status = "BULLISH" if signals['sma_bullish'] else "BEARISH"
        print(f"   200-day SMA: {sma_emoji} {sma_status}")
        print(f"   └─ Level: ${signals['sma_200']:.2f} ({signals['price_vs_sma_pct']:+.1f}%)")
        
        # MACD Signal  
        macd_emoji = "🟢" if signals['macd_bullish'] else "🔴"
        macd_status = "BULLISH" if signals['macd_bullish'] else "BEARISH"
        print(f"   MACD (12,26,9): {macd_emoji} {macd_status}")
        print(f"   └─ MACD: {signals['macd']:.4f} | Signal: {signals['macd_signal']:.4f}")
        print()
    
    def print_allocation(self, allocation):
        """Print allocation recommendation"""
        if not allocation:
            return
            
        print("💼 PORTFOLIO ALLOCATION:")
        print(f"   {allocation['emoji']} {allocation['stance']} STANCE")
        print(f"   🏦 LQQ3: {allocation['lqq3_pct']}%")
        print(f"   💰 Cash: {allocation['cash_pct']}%")
        print()
        
        print("🎯 RECOMMENDATION:")
        print(f"   {allocation['description']}")
        print(f"   Action: {allocation['action']}")
        print()
    
    def print_changes(self, changes):
        """Print signal changes and alerts"""
        if changes:
            print("🚨 SIGNAL CHANGES DETECTED:")
            for change in changes:
                print(f"   • {change}")
            print(f"   ⚠️  REBALANCING MAY BE REQUIRED")
            print()
        else:
            print("✅ No signal changes - maintain current allocation")
            print()
    
    def print_next_levels(self, signals):
        """Print key levels to watch"""
        if not signals['success']:
            return
            
        print("👀 NEXT LEVELS TO WATCH:")
        
        if not signals['macd_bullish']:
            gap = signals['macd_signal'] - signals['macd']
            print(f"   📈 MACD bullish crossover (need {gap:.4f} improvement)")
        
        if not signals['sma_bullish']:
            gap = signals['sma_200'] - signals['tqqq_price']
            print(f"   📊 Price above 200 SMA (need ${gap:.2f} gain)")
        
        if signals['macd_bullish'] and signals['sma_bullish']:
            print(f"   🎯 Both signals bullish - watch for any deterioration")
        
        print()
    
    def print_footer(self):
        """Print app footer"""
        print("-" * 65)
        print("📋 STRATEGY RULES:")
        print("   • 0 bullish signals → 33% LQQ3 (Defensive)")
        print("   • 1 bullish signal  → 66% LQQ3 (Balanced)")
        print("   • 2 bullish signals → 100% LQQ3 (Aggressive)")
        print("=" * 65)
    
    def run(self):
        """Run the complete signal check"""
        try:
            # Print header
            self.print_header()
            
            # Fetch and analyze signals
            signals = self.fetch_signals()
            allocation = self.calculate_allocation(signals)
            changes = self.detect_changes(signals)
            
            # Print results
            self.print_signals(signals)
            self.print_allocation(allocation)
            self.print_changes(changes)
            self.print_next_levels(signals)
            self.print_footer()
            
            return {
                'signals': signals,
                'allocation': allocation,
                'changes': changes
            }
            
        except Exception as e:
            print(f"❌ Application Error: {e}")
            return None

def main():
    """Main entry point"""
    app = LQQ3SignalApp()
    return app.run()

if __name__ == "__main__":
    result = main()
    
    # Optional: Exit code based on result
    if result and result['signals']['success']:
        sys.exit(0)  # Success
    else:
        sys.exit(1)  # Error
