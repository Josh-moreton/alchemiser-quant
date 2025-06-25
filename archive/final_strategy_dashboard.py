#!/usr/bin/env python3
"""
Final Strategy Dashboard - All Three Approaches
Real-time comparison and recommendations
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

class FinalStrategyDashboard:
    def __init__(self):
        self.data = {}
        self.signals = pd.DataFrame()
        
    def fetch_current_data(self, days_back=300):
        """Fetch recent data for current analysis"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        print("Fetching current market data for strategy dashboard...")
        
        # Fetch TQQQ data
        tqqq = yf.download('TQQQ', start=start_date, end=end_date, progress=False)
        
        # Handle multi-level columns
        if tqqq.columns.nlevels > 1:
            tqqq.columns = tqqq.columns.get_level_values(0)
        
        self.data['TQQQ'] = tqqq
        print(f"Fetched {len(tqqq)} days of TQQQ data")
        
        return self.data
    
    def calculate_current_signals(self):
        """Calculate all signals for current analysis"""
        tqqq_data = self.data['TQQQ'].copy()
        
        # Calculate MACD components
        ema_12 = tqqq_data['Close'].ewm(span=12).mean()
        ema_26 = tqqq_data['Close'].ewm(span=26).mean()
        tqqq_data['MACD'] = ema_12 - ema_26
        tqqq_data['MACD_Signal'] = tqqq_data['MACD'].ewm(span=9).mean()
        
        # Calculate 200-day SMA
        tqqq_data['SMA_200'] = tqqq_data['Close'].rolling(window=200).mean()
        
        # Individual signals
        tqqq_data['MACD_Bullish'] = (tqqq_data['MACD'] > tqqq_data['MACD_Signal']).astype(int)
        tqqq_data['SMA_Bullish'] = (tqqq_data['Close'] > tqqq_data['SMA_200']).astype(int)
        
        # Strategy signals
        tqqq_data['Original_SMA_Signal'] = tqqq_data['SMA_Bullish']
        tqqq_data['OR_Logic_Signal'] = ((tqqq_data['MACD_Bullish'] == 1) | 
                                       (tqqq_data['SMA_Bullish'] == 1)).astype(int)
        tqqq_data['Signal_Count'] = tqqq_data['MACD_Bullish'] + tqqq_data['SMA_Bullish']
        
        self.signals = tqqq_data
        return self.signals
    
    def get_current_recommendations(self):
        """Get current recommendations for all strategies"""
        latest = self.signals.iloc[-1]
        current_date = self.signals.index[-1]
        
        # Current values
        tqqq_price = latest['Close']
        sma_200 = latest['SMA_200']
        macd = latest['MACD']
        macd_signal = latest['MACD_Signal']
        
        # Signal status
        macd_bullish = latest['MACD_Bullish'] == 1
        sma_bullish = latest['SMA_Bullish'] == 1
        signal_count = latest['Signal_Count']
        
        # Strategy recommendations
        strategies = {
            'Original_SMA': {
                'signal': latest['Original_SMA_Signal'] == 1,
                'position': 'BUY (100% LQQ3)' if latest['Original_SMA_Signal'] == 1 else 'SELL (34% LQQ3)',
                'logic': 'Price above/below 200-day SMA',
                'confidence': 'Medium' if sma_bullish else 'High'
            },
            'OR_Logic': {
                'signal': latest['OR_Logic_Signal'] == 1,
                'position': 'BUY (100% LQQ3)' if latest['OR_Logic_Signal'] == 1 else 'SELL (34% LQQ3)',
                'logic': 'Either MACD OR SMA bullish',
                'confidence': 'High' if (macd_bullish and sma_bullish) else 'Medium' if (macd_bullish or sma_bullish) else 'High'
            },
            'Variable_Allocation': {
                'signal': signal_count,
                'position': f'{33 + (signal_count * 33.5):.0f}% LQQ3' if signal_count < 2 else '100% LQQ3',
                'logic': 'Graduated allocation based on signal count',
                'confidence': 'Low' if signal_count == 0 else 'Medium' if signal_count == 1 else 'High'
            }
        }
        
        return {
            'date': current_date,
            'market_data': {
                'tqqq_price': tqqq_price,
                'sma_200': sma_200,
                'price_vs_sma_pct': (tqqq_price / sma_200 - 1) * 100,
                'macd': macd,
                'macd_signal': macd_signal,
                'macd_histogram': macd - macd_signal
            },
            'individual_signals': {
                'macd_bullish': macd_bullish,
                'sma_bullish': sma_bullish,
                'signal_count': signal_count
            },
            'strategies': strategies
        }
    
    def print_strategy_dashboard(self):
        """Print comprehensive strategy dashboard"""
        current = self.get_current_recommendations()
        
        print("="*100)
        print("COMPREHENSIVE STRATEGY DASHBOARD")
        print("="*100)
        print(f"📅 Date: {current['date'].strftime('%Y-%m-%d')}")
        print(f"📊 TQQQ Price: ${current['market_data']['tqqq_price']:.2f}")
        print("-"*100)
        
        # Market Status
        print("MARKET STATUS:")
        print(f"  💹 TQQQ Price: ${current['market_data']['tqqq_price']:.2f}")
        print(f"  📈 200-day SMA: ${current['market_data']['sma_200']:.2f}")
        print(f"  📏 Price vs SMA: {current['market_data']['price_vs_sma_pct']:+.1f}%")
        print(f"  ⚡ MACD: {current['market_data']['macd']:.4f}")
        print(f"  📶 MACD Signal: {current['market_data']['macd_signal']:.4f}")
        print(f"  📊 MACD Histogram: {current['market_data']['macd_histogram']:+.4f}")
        
        print("-"*100)
        
        # Individual Signals
        print("INDIVIDUAL SIGNALS:")
        macd_status = "🟢 BULLISH" if current['individual_signals']['macd_bullish'] else "🔴 BEARISH"
        sma_status = "🟢 BULLISH" if current['individual_signals']['sma_bullish'] else "🔴 BEARISH"
        
        print(f"  MACD (12,26,9): {macd_status}")
        print(f"  SMA (200-day): {sma_status}")
        print(f"  Signal Count: {current['individual_signals']['signal_count']}/2")
        
        print("-"*100)
        
        # Strategy Comparison Table
        print("STRATEGY RECOMMENDATIONS:")
        print()
        print(f"{'Strategy':<20} {'Signal':<15} {'Position':<20} {'Confidence':<10} {'Logic'}")
        print("-" * 100)
        
        for strategy, details in current['strategies'].items():
            strategy_name = strategy.replace('_', ' ')
            
            if strategy == 'Variable_Allocation':
                signal_text = f"{details['signal']}/2 signals"
            else:
                signal_text = "🟢 BUY" if details['signal'] else "🔴 SELL"
            
            print(f"{strategy_name:<20} {signal_text:<15} {details['position']:<20} "
                  f"{details['confidence']:<10} {details['logic']}")
        
        print("-"*100)
        
        # Performance Summary (from previous analysis)
        print("HISTORICAL PERFORMANCE SUMMARY:")
        print()
        performance_data = {
            'Original SMA': {'return': '4,786%', 'sharpe': '0.95', 'drawdown': '-52.0%'},
            'OR Logic': {'return': '11,909%', 'sharpe': '1.03', 'drawdown': '-59.2%'},
            'Variable Allocation': {'return': '8,415%', 'sharpe': '1.12', 'drawdown': '-50.0%'}
        }
        
        print(f"{'Strategy':<20} {'Total Return':<12} {'Sharpe Ratio':<12} {'Max Drawdown':<12}")
        print("-" * 60)
        for strategy, metrics in performance_data.items():
            print(f"{strategy:<20} {metrics['return']:<12} {metrics['sharpe']:<12} {metrics['drawdown']:<12}")
        
        print("-"*100)
        
        # Current Recommendation
        print("CURRENT RECOMMENDATION ANALYSIS:")
        
        signal_count = current['individual_signals']['signal_count']
        
        if signal_count == 0:
            print("🔴 BOTH SIGNALS BEARISH - DEFENSIVE POSTURE")
            print("   • Original SMA: 34% LQQ3 (following SMA sell signal)")
            print("   • OR Logic: 34% LQQ3 (both signals bearish)")
            print("   • Variable Allocation: 33% LQQ3 (minimum allocation)")
            print("   💡 All strategies suggest defensive positioning")
            
        elif signal_count == 1:
            if current['individual_signals']['macd_bullish']:
                print("🟡 MIXED SIGNALS - MACD BULLISH, SMA BEARISH")
                print("   • Momentum positive but trend uncertain")
            else:
                print("🟡 MIXED SIGNALS - SMA BULLISH, MACD BEARISH")
                print("   • Trend positive but momentum weak")
            
            print("   • Original SMA: Depends on which signal")
            print("   • OR Logic: 100% LQQ3 (one bullish signal is enough)")
            print("   • Variable Allocation: 66% LQQ3 (moderate allocation)")
            print("   💡 Variable allocation provides balanced approach")
            
        else:
            print("🟢 BOTH SIGNALS BULLISH - FULL PARTICIPATION")
            print("   • Original SMA: 100% LQQ3")
            print("   • OR Logic: 100% LQQ3")
            print("   • Variable Allocation: 100% LQQ3")
            print("   💡 All strategies suggest maximum allocation")
        
        print("-"*100)
        
        # Strategy Selection Guide
        print("STRATEGY SELECTION GUIDE:")
        print()
        print("🎯 For MAXIMUM RETURNS:")
        print("   Choose: OR Logic Strategy")
        print("   • Highest historical returns (11,909%)")
        print("   • Maximum bull market participation")
        print("   • Accept higher volatility and drawdowns")
        print()
        print("⚖️ For BEST RISK-ADJUSTED RETURNS:")
        print("   Choose: Variable Allocation Strategy ⭐ RECOMMENDED")
        print("   • Best Sharpe ratio (1.12) and Sortino ratio")
        print("   • Lowest maximum drawdown (-50%)")
        print("   • Intelligent graduated allocation")
        print()
        print("🛡️ For CONSERVATIVE APPROACH:")
        print("   Choose: Original SMA Strategy")
        print("   • Simplest implementation")
        print("   • Fewer trades but lower returns")
        print("   • Good for beginners")
        
        print("="*100)
        
        return current
    
    def get_recent_signal_changes(self, days=30):
        """Get recent signal changes for context"""
        recent = self.signals.tail(days)
        
        changes = []
        for i in range(1, len(recent)):
            current = recent.iloc[i]
            previous = recent.iloc[i-1]
            
            change_list = []
            if current['MACD_Bullish'] != previous['MACD_Bullish']:
                direction = "BULLISH" if current['MACD_Bullish'] else "BEARISH"
                change_list.append(f"MACD → {direction}")
            
            if current['SMA_Bullish'] != previous['SMA_Bullish']:
                direction = "BULLISH" if current['SMA_Bullish'] else "BEARISH"
                change_list.append(f"SMA → {direction}")
            
            if change_list:
                changes.append({
                    'date': current.name,
                    'changes': change_list,
                    'signal_count': current['Signal_Count']
                })
        
        return changes
    
    def print_recent_activity(self, days=30):
        """Print recent signal activity"""
        changes = self.get_recent_signal_changes(days)
        
        if changes:
            print(f"\nRECENT SIGNAL ACTIVITY (Last {days} days):")
            print("-"*80)
            
            for change in changes[-10:]:  # Last 10 changes
                date_str = change['date'].strftime('%Y-%m-%d')
                changes_str = " & ".join(change['changes'])
                signal_count = change['signal_count']
                
                print(f"{date_str}: {changes_str} → Signal Count: {signal_count}")
        else:
            print(f"\nNo signal changes in the last {days} days")

def main():
    """Run the final strategy dashboard"""
    print("FINAL STRATEGY DASHBOARD")
    print("Comprehensive comparison of all three trading approaches")
    print()
    
    dashboard = FinalStrategyDashboard()
    
    try:
        # Fetch data and calculate signals
        dashboard.fetch_current_data(days_back=400)
        dashboard.calculate_current_signals()
        
        # Display comprehensive dashboard
        current_status = dashboard.print_strategy_dashboard()
        
        # Show recent activity
        dashboard.print_recent_activity(days=30)
        
        return dashboard, current_status
        
    except Exception as e:
        print(f"Error: {e}")
        return None, None

if __name__ == "__main__":
    dashboard, status = main()
