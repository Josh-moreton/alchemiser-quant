#!/usr/bin/env python3
"""
Combined MACD + SMA Signal Strategy Guide
How to read and act on both signals together for optimal trading decisions
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

class CombinedSignalStrategy:
    def __init__(self):
        self.data = {}
        self.signals = pd.DataFrame()
        
    def fetch_current_data(self, days_back=300):
        """Fetch recent data for signal analysis"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        print("Fetching current market data...")
        
        # Fetch TQQQ data
        tqqq = yf.download('TQQQ', start=start_date, end=end_date, progress=False)
        
        # Handle multi-level columns
        if tqqq.columns.nlevels > 1:
            tqqq.columns = tqqq.columns.get_level_values(0)
        
        self.data['TQQQ'] = tqqq
        print(f"Fetched {len(tqqq)} days of TQQQ data")
        
        return self.data
    
    def calculate_signals(self):
        """Calculate both MACD and SMA signals"""
        tqqq_data = self.data['TQQQ'].copy()
        
        # Calculate MACD components
        ema_12 = tqqq_data['Close'].ewm(span=12).mean()
        ema_26 = tqqq_data['Close'].ewm(span=26).mean()
        tqqq_data['MACD'] = ema_12 - ema_26
        tqqq_data['MACD_Signal'] = tqqq_data['MACD'].ewm(span=9).mean()
        tqqq_data['MACD_Histogram'] = tqqq_data['MACD'] - tqqq_data['MACD_Signal']
        
        # Calculate 200-day SMA
        tqqq_data['SMA_200'] = tqqq_data['Close'].rolling(window=200).mean()
        
        # Calculate signal strength
        tqqq_data['Price_vs_SMA'] = (tqqq_data['Close'] / tqqq_data['SMA_200'] - 1) * 100
        tqqq_data['MACD_Strength'] = tqqq_data['MACD_Histogram'] / tqqq_data['Close'] * 1000
        
        # Individual signals
        tqqq_data['MACD_Bullish'] = (tqqq_data['MACD'] > tqqq_data['MACD_Signal']).astype(int)
        tqqq_data['SMA_Bullish'] = (tqqq_data['Close'] > tqqq_data['SMA_200']).astype(int)
        
        # Combined signal (OR Logic - our optimal strategy)
        tqqq_data['Combined_Signal'] = ((tqqq_data['MACD_Bullish'] == 1) | 
                                       (tqqq_data['SMA_Bullish'] == 1)).astype(int)
        
        # Signal confidence levels
        conditions = [
            # Strong bullish: Both signals bullish + strong momentum
            (tqqq_data['MACD_Bullish'] == 1) & (tqqq_data['SMA_Bullish'] == 1) & 
            (tqqq_data['MACD_Histogram'] > 0.1) & (tqqq_data['Price_vs_SMA'] > 2),
            
            # Bullish: Both signals bullish
            (tqqq_data['MACD_Bullish'] == 1) & (tqqq_data['SMA_Bullish'] == 1),
            
            # Cautious bullish: Only one signal bullish
            ((tqqq_data['MACD_Bullish'] == 1) & (tqqq_data['SMA_Bullish'] == 0)) |
            ((tqqq_data['MACD_Bullish'] == 0) & (tqqq_data['SMA_Bullish'] == 1)),
            
            # Neutral/Bearish: Both signals bearish
            (tqqq_data['MACD_Bullish'] == 0) & (tqqq_data['SMA_Bullish'] == 0)
        ]
        
        choices = ['Strong_Bullish', 'Bullish', 'Cautious_Bullish', 'Bearish']
        tqqq_data['Signal_Strength'] = np.select(conditions, choices, default='Neutral')
        
        self.signals = tqqq_data
        return self.signals
    
    def get_current_signal_status(self):
        """Get current signal status with detailed analysis"""
        latest = self.signals.iloc[-1]
        previous = self.signals.iloc[-2]
        
        current_date = self.signals.index[-1]
        
        # Current values
        tqqq_price = latest['Close']
        sma_200 = latest['SMA_200']
        macd = latest['MACD']
        macd_signal = latest['MACD_Signal']
        macd_histogram = latest['MACD_Histogram']
        
        # Signal status
        macd_bullish = latest['MACD_Bullish'] == 1
        sma_bullish = latest['SMA_Bullish'] == 1
        combined_signal = latest['Combined_Signal'] == 1
        signal_strength = latest['Signal_Strength']
        
        # Changes from previous day
        macd_changed = latest['MACD_Bullish'] != previous['MACD_Bullish']
        sma_changed = latest['SMA_Bullish'] != previous['SMA_Bullish']
        
        return {
            'date': current_date,
            'tqqq_price': tqqq_price,
            'sma_200': sma_200,
            'price_vs_sma_pct': latest['Price_vs_SMA'],
            'macd': macd,
            'macd_signal': macd_signal,
            'macd_histogram': macd_histogram,
            'macd_bullish': macd_bullish,
            'sma_bullish': sma_bullish,
            'combined_signal': combined_signal,
            'signal_strength': signal_strength,
            'macd_changed': macd_changed,
            'sma_changed': sma_changed
        }
    
    def generate_trading_recommendation(self, current_status):
        """Generate specific trading recommendation based on current signals"""
        
        macd_bullish = current_status['macd_bullish']
        sma_bullish = current_status['sma_bullish']
        signal_strength = current_status['signal_strength']
        price_vs_sma = current_status['price_vs_sma_pct']
        macd_histogram = current_status['macd_histogram']
        
        recommendations = []
        
        # Primary recommendation based on OR logic
        if current_status['combined_signal']:
            primary_action = "BUY/HOLD LQQ3"
            confidence = "Medium"
            
            # Adjust confidence based on signal strength
            if signal_strength == "Strong_Bullish":
                confidence = "High"
                recommendations.append("🟢 STRONG BUY: Both signals strongly bullish with good momentum")
            elif signal_strength == "Bullish":
                confidence = "High"
                recommendations.append("🟢 BUY: Both MACD and SMA signals are bullish")
            elif signal_strength == "Cautious_Bullish":
                if macd_bullish and not sma_bullish:
                    confidence = "Medium"
                    recommendations.append("🟡 CAUTIOUS BUY: MACD bullish but price below 200 SMA")
                    recommendations.append("   Consider waiting for price to break above SMA for confirmation")
                elif sma_bullish and not macd_bullish:
                    confidence = "Medium"
                    recommendations.append("🟡 CAUTIOUS BUY: Price above 200 SMA but MACD bearish")
                    recommendations.append("   Trend is positive but momentum is weak")
        else:
            primary_action = "SELL/REDUCE POSITION"
            confidence = "High"
            recommendations.append("🔴 SELL: Both MACD and SMA signals are bearish")
            recommendations.append("   Consider reducing position by 66% as per strategy")
        
        # Additional context
        if abs(price_vs_sma) < 1:
            recommendations.append(f"📊 Price is {price_vs_sma:.1f}% from 200 SMA - near critical level")
        elif price_vs_sma > 5:
            recommendations.append(f"📈 Price is {price_vs_sma:.1f}% above 200 SMA - strong uptrend")
        elif price_vs_sma < -5:
            recommendations.append(f"📉 Price is {price_vs_sma:.1f}% below 200 SMA - strong downtrend")
        
        if abs(macd_histogram) > 1:
            if macd_histogram > 0:
                recommendations.append("⚡ Strong positive MACD momentum")
            else:
                recommendations.append("⚡ Strong negative MACD momentum")
        
        # Signal change alerts
        if current_status['macd_changed']:
            new_direction = "bullish" if macd_bullish else "bearish"
            recommendations.append(f"🚨 MACD signal just changed to {new_direction}")
        
        if current_status['sma_changed']:
            new_direction = "bullish" if sma_bullish else "bearish"
            recommendations.append(f"🚨 SMA signal just changed to {new_direction}")
        
        return {
            'primary_action': primary_action,
            'confidence': confidence,
            'recommendations': recommendations
        }
    
    def print_signal_dashboard(self):
        """Print a comprehensive signal dashboard"""
        current_status = self.get_current_signal_status()
        recommendation = self.generate_trading_recommendation(current_status)
        
        print("="*80)
        print("COMBINED MACD + SMA SIGNAL DASHBOARD")
        print("="*80)
        print(f"📅 Date: {current_status['date'].strftime('%Y-%m-%d')}")
        print(f"📊 TQQQ Price: ${current_status['tqqq_price']:.2f}")
        print("-"*80)
        
        # Individual Signals
        print("INDIVIDUAL SIGNALS:")
        
        # SMA Signal
        sma_status = "🟢 BULLISH" if current_status['sma_bullish'] else "🔴 BEARISH"
        print(f"  📈 SMA (200-day): {sma_status}")
        print(f"      200 SMA Level: ${current_status['sma_200']:.2f}")
        print(f"      Price vs SMA: {current_status['price_vs_sma_pct']:+.1f}%")
        
        # MACD Signal
        macd_status = "🟢 BULLISH" if current_status['macd_bullish'] else "🔴 BEARISH"
        print(f"  ⚡ MACD (12,26,9): {macd_status}")
        print(f"      MACD Line: {current_status['macd']:.4f}")
        print(f"      Signal Line: {current_status['macd_signal']:.4f}")
        print(f"      Histogram: {current_status['macd_histogram']:.4f}")
        
        print("-"*80)
        
        # Combined Signal
        combined_status = "🟢 BUY" if current_status['combined_signal'] else "🔴 SELL"
        print(f"COMBINED SIGNAL (OR Logic): {combined_status}")
        print(f"Signal Strength: {current_status['signal_strength']}")
        
        print("-"*80)
        
        # Recommendation
        print("TRADING RECOMMENDATION:")
        print(f"📋 Action: {recommendation['primary_action']}")
        print(f"🎯 Confidence: {recommendation['confidence']}")
        print()
        
        for rec in recommendation['recommendations']:
            print(f"   {rec}")
        
        print("-"*80)
        
        # Strategy Summary
        print("STRATEGY SUMMARY:")
        print("• BUY LQQ3 with 100% capital when either signal is bullish")
        print("• SELL 66% of position when both signals are bearish")
        print("• MACD provides momentum signals (faster, more trades)")
        print("• SMA provides trend signals (slower, fewer trades)")
        print("• OR Logic captures maximum bull market participation")
        
        print("="*80)
        
        return current_status, recommendation
    
    def get_recent_signal_history(self, days=30):
        """Get recent signal history for context"""
        recent = self.signals.tail(days)
        
        signal_changes = []
        for i in range(1, len(recent)):
            current = recent.iloc[i]
            previous = recent.iloc[i-1]
            
            changes = []
            if current['MACD_Bullish'] != previous['MACD_Bullish']:
                direction = "BULLISH" if current['MACD_Bullish'] else "BEARISH"
                changes.append(f"MACD → {direction}")
            
            if current['SMA_Bullish'] != previous['SMA_Bullish']:
                direction = "BULLISH" if current['SMA_Bullish'] else "BEARISH"
                changes.append(f"SMA → {direction}")
            
            if changes:
                signal_changes.append({
                    'date': current.name,
                    'changes': changes,
                    'combined_signal': current['Combined_Signal'],
                    'strength': current['Signal_Strength']
                })
        
        return signal_changes
    
    def print_recent_history(self, days=30):
        """Print recent signal changes for context"""
        changes = self.get_recent_signal_history(days)
        
        if changes:
            print(f"\nRECENT SIGNAL CHANGES (Last {days} days):")
            print("-"*80)
            
            for change in changes[-10:]:  # Show last 10 changes
                date_str = change['date'].strftime('%Y-%m-%d')
                combined = "BUY" if change['combined_signal'] else "SELL"
                changes_str = " & ".join(change['changes'])
                
                print(f"{date_str}: {changes_str} → Combined: {combined} ({change['strength']})")
        else:
            print(f"\nNo signal changes in the last {days} days")

def main():
    """Run the combined signal analysis"""
    print("MACD + SMA COMBINED SIGNAL STRATEGY")
    print("Real-time signal analysis and trading recommendations")
    print()
    
    strategy = CombinedSignalStrategy()
    
    try:
        # Fetch data and calculate signals
        strategy.fetch_current_data(days_back=400)  # Need enough data for 200 SMA
        strategy.calculate_signals()
        
        # Display dashboard
        current_status, recommendation = strategy.print_signal_dashboard()
        
        # Show recent history
        strategy.print_recent_history(days=30)
        
        # Additional insights
        print(f"\n💡 KEY INSIGHTS:")
        
        # Calculate signal statistics
        recent_signals = strategy.signals.tail(252)  # Last year
        macd_signals = recent_signals['MACD_Bullish'].sum()
        sma_signals = recent_signals['SMA_Bullish'].sum()
        combined_signals = recent_signals['Combined_Signal'].sum()
        
        print(f"   • Last 252 days: MACD bullish {macd_signals} days ({macd_signals/252*100:.1f}%)")
        print(f"   • Last 252 days: SMA bullish {sma_signals} days ({sma_signals/252*100:.1f}%)")
        print(f"   • Last 252 days: Combined signal active {combined_signals} days ({combined_signals/252*100:.1f}%)")
        
        # Volatility context
        price_volatility = recent_signals['Close'].pct_change().std() * np.sqrt(252) * 100
        print(f"   • TQQQ 1-year volatility: {price_volatility:.1f}%")
        
        return strategy
        
    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    strategy = main()
