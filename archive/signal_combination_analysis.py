#!/usr/bin/env python3
"""
MACD + SMA Signal Combination Analysis
Detailed study of how MACD and SMA signals complement each other
"""

import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

class SignalCombinationAnalysis:
    def __init__(self, start_date="2012-12-13", end_date=None, initial_capital=55000):
        self.start_date = start_date
        self.end_date = end_date if end_date else datetime.now().strftime('%Y-%m-%d')
        self.initial_capital = initial_capital
        self.data = {}
        self.signals = pd.DataFrame()
        
    def fetch_data(self):
        """Fetch historical data for TQQQ and LQQ3.L"""
        print("Fetching data for signal combination analysis...")
        
        # Fetch TQQQ data (US ETF)
        tqqq = yf.download('TQQQ', start=self.start_date, end=self.end_date, progress=False)
        
        # Fetch LQQ3.L data (LSE ticker)
        lqq3 = yf.download('LQQ3.L', start=self.start_date, end=self.end_date, progress=False)
        
        if tqqq.empty or lqq3.empty:
            raise ValueError("Failed to fetch data. Please check ticker symbols and date range.")
        
        # Handle multi-level columns
        if tqqq.columns.nlevels > 1:
            tqqq.columns = tqqq.columns.get_level_values(0)
        if lqq3.columns.nlevels > 1:
            lqq3.columns = lqq3.columns.get_level_values(0)
        
        self.data['TQQQ'] = tqqq
        self.data['LQQ3'] = lqq3
        
        print(f"Data fetched: TQQQ {len(tqqq)} days, LQQ3 {len(lqq3)} days")
        return self.data
    
    def calculate_all_signals(self):
        """Calculate MACD, SMA, and combined signals"""
        print("Calculating all signal combinations...")
        
        tqqq_data = self.data['TQQQ'].copy()
        
        # Calculate MACD components
        ema_12 = tqqq_data['Close'].ewm(span=12).mean()
        ema_26 = tqqq_data['Close'].ewm(span=26).mean()
        tqqq_data['MACD'] = ema_12 - ema_26
        tqqq_data['MACD_Signal'] = tqqq_data['MACD'].ewm(span=9).mean()
        tqqq_data['MACD_Histogram'] = tqqq_data['MACD'] - tqqq_data['MACD_Signal']
        
        # Calculate 200-day SMA
        tqqq_data['SMA_200'] = tqqq_data['Close'].rolling(window=200).mean()
        
        # Individual signal components
        tqqq_data['MACD_Bullish'] = (tqqq_data['MACD'] > tqqq_data['MACD_Signal']).astype(int)
        tqqq_data['SMA_Bullish'] = (tqqq_data['Close'] > tqqq_data['SMA_200']).astype(int)
        
        # Combination signals
        tqqq_data['AND_Signal'] = ((tqqq_data['MACD_Bullish'] == 1) & 
                                  (tqqq_data['SMA_Bullish'] == 1)).astype(int)
        tqqq_data['OR_Signal'] = ((tqqq_data['MACD_Bullish'] == 1) | 
                                 (tqqq_data['SMA_Bullish'] == 1)).astype(int)
        
        # Signal state categories
        conditions = [
            (tqqq_data['MACD_Bullish'] == 0) & (tqqq_data['SMA_Bullish'] == 0),  # Both bearish
            (tqqq_data['MACD_Bullish'] == 1) & (tqqq_data['SMA_Bullish'] == 0),  # MACD only
            (tqqq_data['MACD_Bullish'] == 0) & (tqqq_data['SMA_Bullish'] == 1),  # SMA only
            (tqqq_data['MACD_Bullish'] == 1) & (tqqq_data['SMA_Bullish'] == 1)   # Both bullish
        ]
        choices = ['Both_Bearish', 'MACD_Only', 'SMA_Only', 'Both_Bullish']
        tqqq_data['Signal_State'] = np.select(conditions, choices, default='Unknown')
        
        # Calculate signal transitions
        tqqq_data['MACD_Change'] = tqqq_data['MACD_Bullish'].diff()
        tqqq_data['SMA_Change'] = tqqq_data['SMA_Bullish'].diff()
        tqqq_data['OR_Change'] = tqqq_data['OR_Signal'].diff()
        tqqq_data['AND_Change'] = tqqq_data['AND_Signal'].diff()
        
        # Align with LQQ3 data
        lqq3_data = self.data['LQQ3'].copy()
        
        # Find common date range
        start_date = max(lqq3_data.index.min(), tqqq_data.index.min())
        end_date = min(lqq3_data.index.max(), tqqq_data.index.max())
        
        # Filter to common dates
        lqq3_filtered = lqq3_data.loc[start_date:end_date].copy()
        tqqq_filtered = tqqq_data.loc[start_date:end_date].copy()
        
        # Merge data
        self.signals = pd.merge(
            lqq3_filtered[['Close']].rename(columns={'Close': 'LQQ3_Close'}),
            tqqq_filtered[['Close', 'MACD', 'MACD_Signal', 'MACD_Histogram', 'SMA_200',
                          'MACD_Bullish', 'SMA_Bullish', 'AND_Signal', 'OR_Signal',
                          'Signal_State', 'MACD_Change', 'SMA_Change', 'OR_Change', 'AND_Change']].rename(
                columns={'Close': 'TQQQ_Close'}
            ),
            left_index=True,
            right_index=True,
            how='outer'
        )
        
        # Forward fill missing data
        for col in ['MACD_Bullish', 'SMA_Bullish', 'AND_Signal', 'OR_Signal', 'Signal_State']:
            self.signals[col] = self.signals[col].fillna(method='ffill')
        
        # Drop rows without LQQ3 data
        self.signals = self.signals.dropna(subset=['LQQ3_Close'])
        
        print(f"Signals calculated for {len(self.signals)} trading days")
        return self.signals
    
    def analyze_signal_correlation(self):
        """Analyze correlation between MACD and SMA signals"""
        print("\n" + "="*80)
        print("SIGNAL CORRELATION ANALYSIS")
        print("="*80)
        
        # Calculate correlation
        macd_sma_corr = self.signals['MACD_Bullish'].corr(self.signals['SMA_Bullish'])
        print(f"MACD-SMA Signal Correlation: {macd_sma_corr:.3f}")
        
        # Signal state distribution
        state_counts = self.signals['Signal_State'].value_counts()
        state_pcts = self.signals['Signal_State'].value_counts(normalize=True) * 100
        
        print(f"\nSIGNAL STATE DISTRIBUTION:")
        for state in ['Both_Bullish', 'MACD_Only', 'SMA_Only', 'Both_Bearish']:
            count = state_counts.get(state, 0)
            pct = state_pcts.get(state, 0)
            print(f"  {state:15}: {count:4d} days ({pct:5.1f}%)")
        
        # Agreement analysis
        agreement = (self.signals['MACD_Bullish'] == self.signals['SMA_Bullish']).sum()
        agreement_pct = agreement / len(self.signals) * 100
        print(f"\nSignal Agreement: {agreement:,} days ({agreement_pct:.1f}%)")
        
        # Transition analysis
        macd_transitions = abs(self.signals['MACD_Change']).sum()
        sma_transitions = abs(self.signals['SMA_Change']).sum()
        or_transitions = abs(self.signals['OR_Change']).sum()
        and_transitions = abs(self.signals['AND_Change']).sum()
        
        print(f"\nSIGNAL TRANSITIONS:")
        print(f"  MACD transitions: {macd_transitions}")
        print(f"  SMA transitions:  {sma_transitions}")
        print(f"  OR transitions:   {or_transitions}")
        print(f"  AND transitions:  {and_transitions}")
        
        return {
            'correlation': macd_sma_corr,
            'state_distribution': state_pcts.to_dict(),
            'agreement_pct': agreement_pct,
            'transitions': {
                'MACD': macd_transitions,
                'SMA': sma_transitions,
                'OR': or_transitions,
                'AND': and_transitions
            }
        }
    
    def analyze_signal_timing(self):
        """Analyze timing differences between MACD and SMA signals"""
        print("\n" + "="*80)
        print("SIGNAL TIMING ANALYSIS")
        print("="*80)
        
        # Find signal changes
        macd_changes = self.signals[self.signals['MACD_Change'] != 0].copy()
        sma_changes = self.signals[self.signals['SMA_Change'] != 0].copy()
        
        print(f"MACD signal changes: {len(macd_changes)}")
        print(f"SMA signal changes:  {len(sma_changes)}")
        
        # Analyze which signal leads
        lead_analysis = []
        
        for idx, macd_change in macd_changes.iterrows():
            # Find nearest SMA change
            if len(sma_changes) > 0:
                time_diffs = abs((sma_changes.index - idx).days)
                nearest_sma_idx = sma_changes.index[time_diffs.argmin()]
                nearest_sma = sma_changes.loc[nearest_sma_idx]
                
                days_diff = (nearest_sma_idx - idx).days
                
                # Only consider if within reasonable timeframe (90 days)
                if abs(days_diff) <= 90:
                    lead_analysis.append({
                        'MACD_Date': idx,
                        'SMA_Date': nearest_sma_idx,
                        'Days_Diff': days_diff,
                        'MACD_Direction': 'Bullish' if macd_change['MACD_Change'] > 0 else 'Bearish',
                        'SMA_Direction': 'Bullish' if nearest_sma['SMA_Change'] > 0 else 'Bearish',
                        'Same_Direction': (macd_change['MACD_Change'] > 0) == (nearest_sma['SMA_Change'] > 0)
                    })
        
        if lead_analysis:
            lead_df = pd.DataFrame(lead_analysis)
            
            # Who leads?
            macd_leads = len(lead_df[lead_df['Days_Diff'] > 0])
            sma_leads = len(lead_df[lead_df['Days_Diff'] < 0])
            simultaneous = len(lead_df[lead_df['Days_Diff'] == 0])
            
            print(f"\nSIGNAL LEADERSHIP:")
            print(f"  MACD leads SMA: {macd_leads} times")
            print(f"  SMA leads MACD: {sma_leads} times")
            print(f"  Simultaneous:   {simultaneous} times")
            
            if len(lead_df) > 0:
                avg_lead_time = lead_df['Days_Diff'].mean()
                print(f"  Average lead time: {avg_lead_time:.1f} days (positive = MACD leads)")
                
                same_direction_pct = lead_df['Same_Direction'].mean() * 100
                print(f"  Same direction: {same_direction_pct:.1f}% of the time")
        
        return lead_analysis
    
    def analyze_performance_by_state(self):
        """Analyze LQQ3 performance in different signal states"""
        print("\n" + "="*80)
        print("PERFORMANCE BY SIGNAL STATE")
        print("="*80)
        
        # Calculate forward returns for each signal state
        self.signals['LQQ3_Forward_Return_1d'] = self.signals['LQQ3_Close'].pct_change().shift(-1)
        self.signals['LQQ3_Forward_Return_5d'] = (self.signals['LQQ3_Close'].shift(-5) / 
                                                  self.signals['LQQ3_Close'] - 1)
        self.signals['LQQ3_Forward_Return_20d'] = (self.signals['LQQ3_Close'].shift(-20) / 
                                                   self.signals['LQQ3_Close'] - 1)
        
        # Group by signal state
        state_performance = {}
        
        for state in ['Both_Bullish', 'MACD_Only', 'SMA_Only', 'Both_Bearish']:
            state_data = self.signals[self.signals['Signal_State'] == state]
            
            if len(state_data) > 0:
                state_performance[state] = {
                    'Days': len(state_data),
                    'Avg_1d_Return': state_data['LQQ3_Forward_Return_1d'].mean() * 100,
                    'Avg_5d_Return': state_data['LQQ3_Forward_Return_5d'].mean() * 100,
                    'Avg_20d_Return': state_data['LQQ3_Forward_Return_20d'].mean() * 100,
                    'Volatility_1d': state_data['LQQ3_Forward_Return_1d'].std() * 100,
                    'Win_Rate_1d': (state_data['LQQ3_Forward_Return_1d'] > 0).mean() * 100
                }
        
        # Display results
        print(f"{'State':<15} {'Days':<6} {'1d Return':<10} {'5d Return':<10} {'20d Return':<11} {'Win Rate':<9}")
        print("-" * 80)
        
        for state, metrics in state_performance.items():
            print(f"{state:<15} {metrics['Days']:<6} {metrics['Avg_1d_Return']:>8.3f}% "
                  f"{metrics['Avg_5d_Return']:>8.3f}% {metrics['Avg_20d_Return']:>9.3f}% "
                  f"{metrics['Win_Rate_1d']:>7.1f}%")
        
        return state_performance
    
    def create_signal_visualization(self):
        """Create visualization of signal combinations"""
        print("\n" + "="*80)
        print("CREATING SIGNAL VISUALIZATION")
        print("="*80)
        
        # Focus on recent data for clearer visualization
        recent_data = self.signals.tail(252 * 2)  # Last 2 years
        
        fig, axes = plt.subplots(4, 1, figsize=(15, 12))
        fig.suptitle('TQQQ Signal Analysis - MACD vs SMA (Last 2 Years)', fontsize=16, fontweight='bold')
        
        # Plot 1: TQQQ Price vs SMA
        ax1 = axes[0]
        ax1.plot(recent_data.index, recent_data['TQQQ_Close'], label='TQQQ Price', color='black', linewidth=1)
        ax1.plot(recent_data.index, recent_data['SMA_200'], label='200-day SMA', color='blue', linewidth=1)
        ax1.fill_between(recent_data.index, 
                        recent_data['TQQQ_Close'].min(), recent_data['TQQQ_Close'].max(),
                        where=recent_data['SMA_Bullish'] == 1, alpha=0.2, color='green', label='SMA Bullish')
        ax1.set_title('TQQQ Price vs 200-day SMA')
        ax1.set_ylabel('Price ($)')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Plot 2: MACD
        ax2 = axes[1]
        ax2.plot(recent_data.index, recent_data['MACD'], label='MACD', color='blue', linewidth=1)
        ax2.plot(recent_data.index, recent_data['MACD_Signal'], label='Signal Line', color='red', linewidth=1)
        ax2.bar(recent_data.index, recent_data['MACD_Histogram'], 
                color=np.where(recent_data['MACD_Histogram'] >= 0, 'green', 'red'), 
                alpha=0.3, label='Histogram')
        ax2.axhline(y=0, color='black', linestyle='-', alpha=0.3)
        ax2.fill_between(recent_data.index,
                        recent_data['MACD'].min(), recent_data['MACD'].max(),
                        where=recent_data['MACD_Bullish'] == 1, alpha=0.2, color='green', label='MACD Bullish')
        ax2.set_title('MACD Indicator')
        ax2.set_ylabel('MACD Value')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # Plot 3: Signal States
        ax3 = axes[2]
        state_colors = {'Both_Bullish': 'darkgreen', 'MACD_Only': 'lightgreen', 
                       'SMA_Only': 'orange', 'Both_Bearish': 'red'}
        
        for i, (date, row) in enumerate(recent_data.iterrows()):
            state = row['Signal_State']
            ax3.scatter(date, 0, c=state_colors.get(state, 'gray'), s=20, alpha=0.7)
        
        ax3.set_title('Signal State Timeline')
        ax3.set_ylabel('Signal State')
        ax3.set_ylim(-0.5, 0.5)
        
        # Create legend
        legend_elements = [plt.Line2D([0], [0], marker='o', color='w', markerfacecolor=color, 
                                    markersize=8, label=state.replace('_', ' ')) 
                          for state, color in state_colors.items()]
        ax3.legend(handles=legend_elements, loc='upper right')
        ax3.grid(True, alpha=0.3)
        
        # Plot 4: Combined Signals
        ax4 = axes[3]
        ax4.plot(recent_data.index, recent_data['MACD_Bullish'], label='MACD Signal', 
                color='blue', linewidth=1, alpha=0.7)
        ax4.plot(recent_data.index, recent_data['SMA_Bullish'], label='SMA Signal', 
                color='orange', linewidth=1, alpha=0.7)
        ax4.plot(recent_data.index, recent_data['OR_Signal'], label='OR Logic (Our Strategy)', 
                color='green', linewidth=2)
        ax4.plot(recent_data.index, recent_data['AND_Signal'], label='AND Logic', 
                color='red', linewidth=1, linestyle='--')
        
        ax4.set_title('Signal Combinations')
        ax4.set_ylabel('Signal (1=Buy, 0=Sell)')
        ax4.set_xlabel('Date')
        ax4.legend()
        ax4.grid(True, alpha=0.3)
        ax4.set_ylim(-0.1, 1.1)
        
        plt.tight_layout()
        plt.savefig('signal_combination_analysis.png', dpi=300, bbox_inches='tight')
        print("Signal visualization saved as 'signal_combination_analysis.png'")
        plt.show()
    
    def generate_summary_report(self):
        """Generate comprehensive summary report"""
        print("\n" + "="*80)
        print("SIGNAL COMBINATION SUMMARY REPORT")
        print("="*80)
        
        correlation_stats = self.analyze_signal_correlation()
        timing_analysis = self.analyze_signal_timing()
        performance_stats = self.analyze_performance_by_state()
        
        # Current status
        latest = self.signals.iloc[-1]
        current_date = self.signals.index[-1]
        
        print(f"\nCURRENT STATUS (as of {current_date.strftime('%Y-%m-%d')}):")
        print(f"  TQQQ Price: ${latest['TQQQ_Close']:.2f}")
        print(f"  TQQQ 200 SMA: ${latest['SMA_200']:.2f}")
        print(f"  MACD: {latest['MACD']:.4f}")
        print(f"  MACD Signal: {latest['MACD_Signal']:.4f}")
        print(f"  Current State: {latest['Signal_State']}")
        
        macd_status = "🟢 Bullish" if latest['MACD_Bullish'] else "🔴 Bearish"
        sma_status = "🟢 Bullish" if latest['SMA_Bullish'] else "🔴 Bearish"
        or_status = "🟢 BUY" if latest['OR_Signal'] else "🔴 SELL"
        and_status = "🟢 BUY" if latest['AND_Signal'] else "🔴 SELL"
        
        print(f"\n  Individual Signals:")
        print(f"    MACD: {macd_status}")
        print(f"    SMA:  {sma_status}")
        print(f"  Combined Signals:")
        print(f"    OR Logic:  {or_status}")
        print(f"    AND Logic: {and_status}")
        
        # Key insights
        print(f"\nKEY INSIGHTS:")
        print(f"  • MACD and SMA agree {correlation_stats['agreement_pct']:.1f}% of the time")
        print(f"  • OR Logic provides {correlation_stats['state_distribution'].get('Both_Bullish', 0) + correlation_stats['state_distribution'].get('MACD_Only', 0) + correlation_stats['state_distribution'].get('SMA_Only', 0):.1f}% market exposure")
        print(f"  • AND Logic provides {correlation_stats['state_distribution'].get('Both_Bullish', 0):.1f}% market exposure")
        print(f"  • MACD generates {correlation_stats['transitions']['MACD']} signals vs SMA's {correlation_stats['transitions']['SMA']}")
        
        # Save detailed results
        self.signals.to_csv('signal_combination_detailed_analysis.csv')
        print(f"\nDetailed analysis saved to 'signal_combination_detailed_analysis.csv'")
        
        return {
            'correlation_stats': correlation_stats,
            'timing_analysis': timing_analysis,
            'performance_stats': performance_stats,
            'current_status': latest.to_dict()
        }

def main():
    """Run the signal combination analysis"""
    print("="*80)
    print("MACD + SMA SIGNAL COMBINATION ANALYSIS")
    print("="*80)
    print("Analyzing how MACD momentum and SMA trend signals work together")
    print("-"*80)
    
    # Initialize analysis
    analyzer = SignalCombinationAnalysis(
        start_date="2012-12-13",
        initial_capital=55000
    )
    
    try:
        # Run complete analysis
        analyzer.fetch_data()
        analyzer.calculate_all_signals()
        analyzer.create_signal_visualization()
        report = analyzer.generate_summary_report()
        
        return analyzer, report
        
    except Exception as e:
        print(f"Error running signal combination analysis: {e}")
        return None, None

if __name__ == "__main__":
    analyzer, report = main()
