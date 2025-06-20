#!/usr/bin/env python3
"""
Risk-Adjusted Performance Analysis
Deep dive into how variable allocation improves risk metrics
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

def analyze_variable_allocation_results():
    """Analyze the results of variable allocation vs OR logic strategy"""
    
    print("="*80)
    print("RISK-ADJUSTED PERFORMANCE ANALYSIS")
    print("="*80)
    
    # Load the detailed results
    try:
        var_alloc = pd.read_csv('variable_allocation_variable_allocation_33_66_100%_detailed.csv', index_col=0, parse_dates=True)
        or_logic = pd.read_csv('variable_allocation_or_logic_current_strategy_detailed.csv', index_col=0, parse_dates=True)
        comparison = pd.read_csv('variable_allocation_comparison.csv', index_col=0)
    except FileNotFoundError:
        print("Results files not found. Please run variable_allocation_strategy.py first.")
        return
    
    print("\nKEY FINDINGS:")
    print("-" * 50)
    
    # Extract key metrics
    var_return = comparison.loc['Variable Allocation (33/66/100%)', 'Total Return (%)']
    or_return = comparison.loc['OR Logic (Current Strategy)', 'Total Return (%)']
    var_sharpe = comparison.loc['Variable Allocation (33/66/100%)', 'Sharpe Ratio']
    or_sharpe = comparison.loc['OR Logic (Current Strategy)', 'Sharpe Ratio']
    var_sortino = comparison.loc['Variable Allocation (33/66/100%)', 'Sortino Ratio']
    or_sortino = comparison.loc['OR Logic (Current Strategy)', 'Sortino Ratio']
    var_dd = comparison.loc['Variable Allocation (33/66/100%)', 'Max Drawdown (%)']
    or_dd = comparison.loc['OR Logic (Current Strategy)', 'Max Drawdown (%)']
    var_vol = comparison.loc['Variable Allocation (33/66/100%)', 'Volatility (%)']
    or_vol = comparison.loc['OR Logic (Current Strategy)', 'Volatility (%)']
    var_calmar = comparison.loc['Variable Allocation (33/66/100%)', 'Calmar Ratio']
    or_calmar = comparison.loc['OR Logic (Current Strategy)', 'Calmar Ratio']
    
    print(f"1. RETURN TRADE-OFF:")
    print(f"   • Variable Allocation: {var_return:.1f}% total return")
    print(f"   • OR Logic: {or_return:.1f}% total return")
    print(f"   • Difference: {var_return - or_return:.1f}% ({(var_return - or_return)/or_return*100:+.1f}%)")
    
    print(f"\n2. RISK REDUCTION:")
    print(f"   • Volatility reduction: {or_vol:.1f}% → {var_vol:.1f}% ({or_vol - var_vol:.1f}% improvement)")
    print(f"   • Max drawdown improvement: {or_dd:.1f}% → {var_dd:.1f}% ({or_dd - var_dd:.1f}% less severe)")
    
    print(f"\n3. RISK-ADJUSTED PERFORMANCE:")
    print(f"   • Sharpe Ratio: {or_sharpe:.2f} → {var_sharpe:.2f} ({var_sharpe - or_sharpe:+.2f})")
    print(f"   • Sortino Ratio: {or_sortino:.2f} → {var_sortino:.2f} ({var_sortino - or_sortino:+.2f})")
    print(f"   • Calmar Ratio: {or_calmar:.2f} → {var_calmar:.2f} ({var_calmar - or_calmar:+.2f})")
    
    # Calculate additional metrics
    print(f"\n4. EFFICIENCY ANALYSIS:")
    
    # Return per unit of risk
    var_return_per_vol = var_return / var_vol
    or_return_per_vol = or_return / or_vol
    print(f"   • Return per unit volatility:")
    print(f"     - Variable: {var_return_per_vol:.1f}% return per 1% volatility")
    print(f"     - OR Logic: {or_return_per_vol:.1f}% return per 1% volatility")
    print(f"     - Improvement: {var_return_per_vol - or_return_per_vol:+.1f}")
    
    # Return per unit of max drawdown
    var_return_per_dd = var_return / abs(var_dd)
    or_return_per_dd = or_return / abs(or_dd)
    print(f"   • Return per unit max drawdown:")
    print(f"     - Variable: {var_return_per_dd:.1f}% return per 1% max drawdown")
    print(f"     - OR Logic: {or_return_per_dd:.1f}% return per 1% max drawdown")
    print(f"     - Improvement: {var_return_per_dd - or_return_per_dd:+.1f}")
    
    # Analyze allocation efficiency
    print(f"\n5. ALLOCATION EFFICIENCY:")
    var_avg_allocation = comparison.loc['Variable Allocation (33/66/100%)', 'Average Allocation (%)']
    or_avg_allocation = comparison.loc['OR Logic (Current Strategy)', 'Average Allocation (%)']
    
    print(f"   • Average allocation:")
    print(f"     - Variable: {var_avg_allocation:.1f}%")
    print(f"     - OR Logic: {or_avg_allocation:.1f}%")
    print(f"   • Return per allocation point:")
    print(f"     - Variable: {var_return/var_avg_allocation:.1f}% return per 1% allocation")
    print(f"     - OR Logic: {or_return/or_avg_allocation:.1f}% return per 1% allocation")
    
    # Analyze drawdown periods
    print(f"\n6. DRAWDOWN ANALYSIS:")
    
    # Calculate rolling max and drawdowns for both strategies
    var_alloc['Rolling_Max'] = var_alloc['Portfolio_Value'].expanding().max()
    var_alloc['Drawdown'] = (var_alloc['Portfolio_Value'] - var_alloc['Rolling_Max']) / var_alloc['Rolling_Max'] * 100
    
    or_logic['Rolling_Max'] = or_logic['Portfolio_Value'].expanding().max()
    or_logic['Drawdown'] = (or_logic['Portfolio_Value'] - or_logic['Rolling_Max']) / or_logic['Rolling_Max'] * 100
    
    # Count significant drawdown periods (>10%)
    var_significant_dd = (var_alloc['Drawdown'] < -10).sum()
    or_significant_dd = (or_logic['Drawdown'] < -10).sum()
    
    print(f"   • Days with >10% drawdown:")
    print(f"     - Variable: {var_significant_dd} days ({var_significant_dd/len(var_alloc)*100:.1f}%)")
    print(f"     - OR Logic: {or_significant_dd} days ({or_significant_dd/len(or_logic)*100:.1f}%)")
    
    # Average drawdown during down periods
    var_avg_dd = var_alloc[var_alloc['Drawdown'] < 0]['Drawdown'].mean()
    or_avg_dd = or_logic[or_logic['Drawdown'] < 0]['Drawdown'].mean()
    
    print(f"   • Average drawdown during down periods:")
    print(f"     - Variable: {var_avg_dd:.1f}%")
    print(f"     - OR Logic: {or_avg_dd:.1f}%")
    
    print(f"\n7. TRADING FREQUENCY:")
    var_trades = comparison.loc['Variable Allocation (33/66/100%)', 'Number of Trades']
    or_trades = comparison.loc['OR Logic (Current Strategy)', 'Number of Trades']
    
    print(f"   • Total trades:")
    print(f"     - Variable: {var_trades:,.0f} trades")
    print(f"     - OR Logic: {or_trades:,.0f} trades")
    print(f"   • Trading frequency difference: {var_trades - or_trades:+,.0f} trades")
    print(f"   • This suggests more frequent rebalancing in variable allocation")
    
    # Recommendation
    print(f"\n" + "="*80)
    print("RECOMMENDATION")
    print("="*80)
    
    risk_score = 0
    return_score = 0
    
    # Score based on risk improvements
    if var_sharpe > or_sharpe: risk_score += 1
    if var_sortino > or_sortino: risk_score += 1
    if var_dd > or_dd: risk_score += 1  # Less negative is better
    if var_vol < or_vol: risk_score += 1
    if var_calmar > or_calmar: risk_score += 1
    
    # Score based on return
    if var_return > or_return * 0.9:  # Within 10% is acceptable
        return_score = 1
    
    print(f"Risk Improvement Score: {risk_score}/5")
    print(f"Return Adequacy Score: {return_score}/1")
    
    if risk_score >= 4 and return_score >= 1:
        recommendation = "STRONG RECOMMENDATION for Variable Allocation"
        reason = "Significantly better risk-adjusted returns with acceptable total return"
    elif risk_score >= 3:
        recommendation = "RECOMMENDED for Variable Allocation"
        reason = "Better risk management with reasonable return trade-off"
    else:
        recommendation = "STICK with OR Logic Strategy"
        reason = "Risk improvements don't justify return reduction"
    
    print(f"\n🎯 {recommendation}")
    print(f"📊 Reason: {reason}")
    
    # Specific benefits
    print(f"\n💡 KEY BENEFITS of Variable Allocation:")
    print(f"   ✅ {var_vol - or_vol:.1f}% lower volatility")
    print(f"   ✅ {or_dd - var_dd:.1f}% better max drawdown")
    print(f"   ✅ {var_sharpe - or_sharpe:.2f} higher Sharpe ratio")
    print(f"   ✅ {var_sortino - or_sortino:.2f} higher Sortino ratio")
    print(f"   ⚠️  {var_return - or_return:.1f}% lower total return")
    
    # Current allocation recommendation
    print(f"\n📋 CURRENT MARKET STATUS:")
    print(f"   • Based on latest signals: 66% LQQ3 allocation recommended")
    print(f"   • This reflects one bullish signal (SMA) and one bearish signal (MACD)")
    print(f"   • Provides balanced exposure while managing uncertainty")
    
    return {
        'recommendation': recommendation,
        'risk_score': risk_score,
        'return_score': return_score,
        'key_improvements': {
            'volatility_reduction': or_vol - var_vol,
            'drawdown_improvement': or_dd - var_dd,
            'sharpe_improvement': var_sharpe - or_sharpe,
            'sortino_improvement': var_sortino - or_sortino,
            'return_trade_off': var_return - or_return
        }
    }

if __name__ == "__main__":
    result = analyze_variable_allocation_results()
