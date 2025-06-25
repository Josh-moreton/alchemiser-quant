#!/usr/bin/env python3
"""
Create visualization comparing Variable Allocation vs OR Logic strategies
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from datetime import datetime

def create_strategy_comparison_charts():
    """Create comprehensive comparison charts"""
    
    try:
        # Load data
        var_alloc = pd.read_csv('variable_allocation_variable_allocation_33_66_100%_detailed.csv', index_col=0, parse_dates=True)
        or_logic = pd.read_csv('variable_allocation_or_logic_current_strategy_detailed.csv', index_col=0, parse_dates=True)
        comparison = pd.read_csv('variable_allocation_comparison.csv', index_col=0)
    except FileNotFoundError:
        print("Results files not found. Please run variable_allocation_strategy.py first.")
        return
    
    # Set up the plotting style
    plt.style.use('default')
    fig = plt.figure(figsize=(20, 16))
    
    # 1. Portfolio Value Comparison
    ax1 = plt.subplot(3, 3, 1)
    ax1.plot(var_alloc.index, var_alloc['Portfolio_Value'], label='Variable Allocation', color='green', linewidth=2)
    ax1.plot(or_logic.index, or_logic['Portfolio_Value'], label='OR Logic', color='blue', linewidth=2)
    ax1.plot(var_alloc.index, var_alloc['BuyHold_Value'], label='Buy & Hold', color='gray', linewidth=1, alpha=0.7)
    ax1.set_title('Portfolio Value Comparison', fontsize=14, fontweight='bold')
    ax1.set_ylabel('Portfolio Value (£)')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    ax1.set_yscale('log')
    
    # 2. Drawdown Comparison
    ax2 = plt.subplot(3, 3, 2)
    var_alloc['Rolling_Max'] = var_alloc['Portfolio_Value'].expanding().max()
    var_alloc['Drawdown'] = (var_alloc['Portfolio_Value'] - var_alloc['Rolling_Max']) / var_alloc['Rolling_Max'] * 100
    or_logic['Rolling_Max'] = or_logic['Portfolio_Value'].expanding().max()
    or_logic['Drawdown'] = (or_logic['Portfolio_Value'] - or_logic['Rolling_Max']) / or_logic['Rolling_Max'] * 100
    
    ax2.fill_between(var_alloc.index, var_alloc['Drawdown'], 0, alpha=0.7, color='green', label='Variable Allocation')
    ax2.fill_between(or_logic.index, or_logic['Drawdown'], 0, alpha=0.5, color='blue', label='OR Logic')
    ax2.set_title('Drawdown Comparison', fontsize=14, fontweight='bold')
    ax2.set_ylabel('Drawdown (%)')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # 3. Allocation Levels
    ax3 = plt.subplot(3, 3, 3)
    allocation_bins = [0.3, 0.6, 0.9, 1.1]
    var_allocation_hist = np.histogram(var_alloc['Target_Allocation'], bins=allocation_bins)
    or_allocation_hist = np.histogram(or_logic['Actual_Allocation'], bins=allocation_bins)
    
    x_labels = ['33%', '66%', '100%']
    x_pos = np.arange(len(x_labels))
    
    var_counts = var_allocation_hist[0] / len(var_alloc) * 100
    or_counts = or_allocation_hist[0] / len(or_logic) * 100
    
    width = 0.35
    ax3.bar(x_pos - width/2, var_counts, width, label='Variable Allocation', color='green', alpha=0.7)
    ax3.bar(x_pos + width/2, or_counts, width, label='OR Logic', color='blue', alpha=0.7)
    ax3.set_title('Allocation Distribution', fontsize=14, fontweight='bold')
    ax3.set_ylabel('Percentage of Time (%)')
    ax3.set_xlabel('Allocation Level')
    ax3.set_xticks(x_pos)
    ax3.set_xticklabels(x_labels)
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # 4. Rolling Sharpe Ratio (1-year window)
    ax4 = plt.subplot(3, 3, 4)
    var_returns = var_alloc['Portfolio_Value'].pct_change()
    or_returns = or_logic['Portfolio_Value'].pct_change()
    
    var_rolling_sharpe = var_returns.rolling(252).mean() / var_returns.rolling(252).std() * np.sqrt(252)
    or_rolling_sharpe = or_returns.rolling(252).mean() / or_returns.rolling(252).std() * np.sqrt(252)
    
    ax4.plot(var_alloc.index, var_rolling_sharpe, label='Variable Allocation', color='green', linewidth=2)
    ax4.plot(or_logic.index, or_rolling_sharpe, label='OR Logic', color='blue', linewidth=2)
    ax4.set_title('Rolling 1-Year Sharpe Ratio', fontsize=14, fontweight='bold')
    ax4.set_ylabel('Sharpe Ratio')
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    ax4.axhline(y=0, color='black', linestyle='--', alpha=0.5)
    
    # 5. Risk-Return Scatter
    ax5 = plt.subplot(3, 3, 5)
    strategies = ['Variable Allocation (33/66/100%)', 'OR Logic (Current Strategy)', 'Buy & Hold']
    returns = [comparison.loc[s, 'Total Return (%)'] for s in strategies]
    volatilities = [comparison.loc[s, 'Volatility (%)'] for s in strategies]
    colors = ['green', 'blue', 'gray']
    
    for i, (ret, vol, color, strategy) in enumerate(zip(returns, volatilities, colors, strategies)):
        ax5.scatter(vol, ret, c=color, s=200, alpha=0.7, label=strategy.split(' (')[0])
        ax5.annotate(f'{ret:.0f}%', (vol, ret), xytext=(5, 5), textcoords='offset points', fontsize=10)
    
    ax5.set_title('Risk-Return Profile', fontsize=14, fontweight='bold')
    ax5.set_xlabel('Volatility (%)')
    ax5.set_ylabel('Total Return (%)')
    ax5.legend()
    ax5.grid(True, alpha=0.3)
    
    # 6. Signal States Over Time
    ax6 = plt.subplot(3, 3, 6)
    
    # Create signal state timeline
    signal_colors = {0: 'red', 1: 'orange', 2: 'green'}
    signal_labels = {0: 'Both Bearish (33%)', 1: 'One Bullish (66%)', 2: 'Both Bullish (100%)'}
    
    for state in [0, 1, 2]:
        mask = var_alloc['Signal_Count'] == state
        if mask.any():
            ax6.scatter(var_alloc.index[mask], [state] * mask.sum(), 
                       c=signal_colors[state], alpha=0.6, s=1, label=signal_labels[state])
    
    ax6.set_title('Signal States Timeline', fontsize=14, fontweight='bold')
    ax6.set_ylabel('Signal Count')
    ax6.set_yticks([0, 1, 2])
    ax6.set_yticklabels(['Both\nBearish', 'One\nBullish', 'Both\nBullish'])
    ax6.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    ax6.grid(True, alpha=0.3)
    
    # 7. Performance Metrics Comparison
    ax7 = plt.subplot(3, 3, 7)
    metrics = ['Total Return (%)', 'Sharpe Ratio', 'Sortino Ratio', 'Max Drawdown (%)']
    var_values = [comparison.loc['Variable Allocation (33/66/100%)', m] for m in metrics]
    or_values = [comparison.loc['OR Logic (Current Strategy)', m] for m in metrics]
    
    # Normalize for better comparison (except drawdown which should be inverted)
    var_normalized = []
    or_normalized = []
    for i, (v, o) in enumerate(zip(var_values, or_values)):
        if 'Drawdown' in metrics[i]:
            # For drawdown, less negative is better, so invert
            var_normalized.append(-v)
            or_normalized.append(-o)
        else:
            var_normalized.append(v)
            or_normalized.append(o)
    
    x = np.arange(len(metrics))
    width = 0.35
    
    ax7.bar(x - width/2, var_normalized, width, label='Variable Allocation', color='green', alpha=0.7)
    ax7.bar(x + width/2, or_normalized, width, label='OR Logic', color='blue', alpha=0.7)
    
    ax7.set_title('Performance Metrics Comparison', fontsize=14, fontweight='bold')
    ax7.set_ylabel('Metric Value')
    ax7.set_xticks(x)
    ax7.set_xticklabels([m.replace(' (%)', '') for m in metrics], rotation=45, ha='right')
    ax7.legend()
    ax7.grid(True, alpha=0.3)
    
    # Add value labels on bars
    for i, (v, o) in enumerate(zip(var_normalized, or_normalized)):
        ax7.text(i - width/2, v + max(var_normalized + or_normalized) * 0.01, f'{var_values[i]:.1f}', 
                ha='center', va='bottom', fontsize=9)
        ax7.text(i + width/2, o + max(var_normalized + or_normalized) * 0.01, f'{or_values[i]:.1f}', 
                ha='center', va='bottom', fontsize=9)
    
    # 8. Monthly Returns Heatmap
    ax8 = plt.subplot(3, 3, 8)
    
    # Calculate monthly returns for variable allocation
    var_monthly = var_alloc['Portfolio_Value'].resample('M').last().pct_change() * 100
    var_monthly_pivot = var_monthly.groupby([var_monthly.index.year, var_monthly.index.month]).mean().unstack(level=1)
    
    # Only show recent years for clarity
    recent_years = var_monthly_pivot.tail(8)
    
    sns.heatmap(recent_years, annot=True, fmt='.1f', cmap='RdYlGn', center=0, 
                ax=ax8, cbar_kws={'label': 'Monthly Return (%)'})
    ax8.set_title('Variable Allocation Monthly Returns', fontsize=14, fontweight='bold')
    ax8.set_xlabel('Month')
    ax8.set_ylabel('Year')
    
    # 9. Cumulative Return Comparison
    ax9 = plt.subplot(3, 3, 9)
    
    var_cumret = (var_alloc['Portfolio_Value'] / var_alloc['Portfolio_Value'].iloc[0] - 1) * 100
    or_cumret = (or_logic['Portfolio_Value'] / or_logic['Portfolio_Value'].iloc[0] - 1) * 100
    buyhold_cumret = (var_alloc['BuyHold_Value'] / var_alloc['BuyHold_Value'].iloc[0] - 1) * 100
    
    ax9.plot(var_alloc.index, var_cumret, label='Variable Allocation', color='green', linewidth=2)
    ax9.plot(or_logic.index, or_cumret, label='OR Logic', color='blue', linewidth=2)
    ax9.plot(var_alloc.index, buyhold_cumret, label='Buy & Hold', color='gray', linewidth=1, alpha=0.7)
    
    ax9.set_title('Cumulative Returns Comparison', fontsize=14, fontweight='bold')
    ax9.set_ylabel('Cumulative Return (%)')
    ax9.legend()
    ax9.grid(True, alpha=0.3)
    ax9.set_yscale('log')
    
    # Add final values as text
    ax9.text(0.02, 0.98, f'Variable: {var_cumret.iloc[-1]:.0f}%', transform=ax9.transAxes, 
             verticalalignment='top', bbox=dict(boxstyle='round', facecolor='green', alpha=0.3))
    ax9.text(0.02, 0.90, f'OR Logic: {or_cumret.iloc[-1]:.0f}%', transform=ax9.transAxes, 
             verticalalignment='top', bbox=dict(boxstyle='round', facecolor='blue', alpha=0.3))
    ax9.text(0.02, 0.82, f'Buy & Hold: {buyhold_cumret.iloc[-1]:.0f}%', transform=ax9.transAxes, 
             verticalalignment='top', bbox=dict(boxstyle='round', facecolor='gray', alpha=0.3))
    
    plt.suptitle('Variable Allocation vs OR Logic Strategy - Comprehensive Comparison', 
                 fontsize=18, fontweight='bold', y=0.98)
    plt.tight_layout()
    plt.subplots_adjust(top=0.94)
    
    # Save the plot
    plt.savefig('variable_allocation_comprehensive_comparison.png', dpi=300, bbox_inches='tight')
    print("Comprehensive comparison chart saved as 'variable_allocation_comprehensive_comparison.png'")
    plt.show()
    
    # Create summary table
    print("\n" + "="*80)
    print("STRATEGY COMPARISON SUMMARY TABLE")
    print("="*80)
    
    summary_data = {
        'Metric': [
            'Total Return (%)',
            'Annual Return (%)', 
            'Volatility (%)',
            'Sharpe Ratio',
            'Sortino Ratio',
            'Max Drawdown (%)',
            'Calmar Ratio',
            'Average Allocation (%)',
            'Number of Trades'
        ]
    }
    
    for strategy in ['Variable Allocation (33/66/100%)', 'OR Logic (Current Strategy)', 'Buy & Hold']:
        summary_data[strategy.split(' (')[0]] = [
            comparison.loc[strategy, 'Total Return (%)'],
            comparison.loc[strategy, 'Annual Return (%)'],
            comparison.loc[strategy, 'Volatility (%)'],
            comparison.loc[strategy, 'Sharpe Ratio'],
            comparison.loc[strategy, 'Sortino Ratio'],
            comparison.loc[strategy, 'Max Drawdown (%)'],
            comparison.loc[strategy, 'Calmar Ratio'],
            comparison.loc[strategy, 'Average Allocation (%)'],
            comparison.loc[strategy, 'Number of Trades']
        ]
    
    summary_df = pd.DataFrame(summary_data)
    print(summary_df.round(2).to_string(index=False))
    
    return summary_df

if __name__ == "__main__":
    summary = create_strategy_comparison_charts()
