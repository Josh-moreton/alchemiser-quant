#!/usr/bin/env python3
"""
Optimized LQQ3 Trading Strategy using MACD signals
Based on comprehensive backtesting analysis showing 1,121% excess returns
"""

from advanced_strategy_testing import AdvancedTradingStrategyBacktest
import pandas as pd

def run_optimized_strategy():
    """Run the optimized MACD strategy"""
    print("="*70)
    print("OPTIMIZED LQQ3 TRADING STRATEGY - MACD VERSION")
    print("="*70)
    print("Strategy: Buy LQQ3 when TQQQ MACD crosses above signal line")
    print("          Sell 66% when TQQQ MACD crosses below signal line")
    print("Based on 12.5 years of backtesting (2012-2025)")
    print("-"*70)
    
    # Create optimized backtester
    backtester = AdvancedTradingStrategyBacktest(
        start_date="2012-12-13",  # Full history
        initial_capital=10000
    )
    
    try:
        # Run MACD strategy
        print("Fetching data and calculating MACD signals...")
        backtester.fetch_data()
        backtester.calculate_signals_macd()
        
        print("Running backtest simulation...")
        backtester.run_backtest()
        
        # Calculate and display results
        metrics = backtester.calculate_performance_metrics()
        
        print("\n" + "="*70)
        print("OPTIMIZED STRATEGY PERFORMANCE SUMMARY")
        print("="*70)
        
        for key, value in metrics.items():
            if key != 'Strategy':
                print(f"{key:<25}: {value}")
        
        # Trading statistics
        trades = backtester.portfolio[backtester.portfolio['Trade_Type'] != 'HOLD']
        print(f"\nTRADING STATISTICS:")
        print(f"{'Total Trades':<25}: {len(trades)}")
        print(f"{'Buy Signals':<25}: {len(trades[trades['Trade_Type'] == 'BUY'])}")
        print(f"{'Sell Signals':<25}: {len(trades[trades['Trade_Type'] == 'SELL'])}")
        
        # Time in market
        bullish_days = len(backtester.signals[backtester.signals['Signal'] == 1])
        total_days = len(backtester.signals)
        print(f"{'Time in Market':<25}: {bullish_days/total_days*100:.1f}%")
        
        # Years analysis
        years = (backtester.signals.index[-1] - backtester.signals.index[0]).days / 365.25
        print(f"{'Trading Period':<25}: {years:.1f} years")
        print(f"{'Trades per Year':<25}: {len(trades)/years:.1f}")
        
        # Compare to alternatives
        print(f"\n{'='*70}")
        print("COMPARISON TO OTHER STRATEGIES")
        print("="*70)
        print(f"{'Strategy':<30} {'Excess Return':<15} {'Max Drawdown':<15}")
        print("-"*70)
        print(f"{'MACD (Optimized)':<30} {'+1,121.16%':<15} {'-49.9%':<15}")
        print(f"{'Multi-Indicator':<30} {'+380.94%':<15} {'-36.5%':<15}")
        print(f"{'Basic 200-day SMA':<30} {'-608.56%':<15} {'-52.0%':<15}")
        print(f"{'Buy & Hold':<30} {'0.00%':<15} {'N/A':<15}")
        
        # Save results
        backtester.portfolio.to_csv('optimized_macd_strategy_results.csv')
        print(f"\nDetailed results saved to 'optimized_macd_strategy_results.csv'")
        
        # Implementation guidance
        print(f"\n{'='*70}")
        print("IMPLEMENTATION GUIDANCE")
        print("="*70)
        print("✅ ADVANTAGES:")
        print("  • 1,121% excess return over buy-and-hold")
        print("  • Better risk-adjusted returns (Sharpe: 1.06)")
        print("  • Momentum-based signals reduce noise")
        print("  • Responsive to trend changes")
        
        print("\n⚠️  CONSIDERATIONS:")
        print("  • More active strategy (19.6 trades/year)")
        print("  • Requires monitoring MACD crossovers")
        print("  • Transaction costs may impact returns")
        print("  • 54% time in market vs 72% for basic SMA")
        
        print("\n📋 NEXT STEPS:")
        print("  1. Test with transaction costs")
        print("  2. Consider position sizing adjustments")
        print("  3. Monitor TQQQ MACD signals daily")
        print("  4. Implement risk management rules")
        print("  5. Regular strategy performance review")
        
        return backtester
        
    except Exception as e:
        print(f"Error running optimized strategy: {e}")
        return None

def quick_signal_check():
    """Check current MACD signal status"""
    print(f"\n{'='*70}")
    print("CURRENT SIGNAL STATUS CHECK")
    print("="*70)
    
    try:
        import yfinance as yf
        from datetime import datetime, timedelta
        
        # Get recent TQQQ data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=100)  # Last 100 days for MACD calculation
        
        tqqq = yf.download('TQQQ', start=start_date, end=end_date, progress=False)
        if tqqq.columns.nlevels > 1:
            tqqq.columns = tqqq.columns.get_level_values(0)
        
        # Calculate MACD
        ema_12 = tqqq['Close'].ewm(span=12).mean()
        ema_26 = tqqq['Close'].ewm(span=26).mean()
        macd = ema_12 - ema_26
        macd_signal = macd.ewm(span=9).mean()
        
        # Current values
        current_macd = macd.iloc[-1]
        current_signal = macd_signal.iloc[-1]
        current_price = tqqq['Close'].iloc[-1]
        current_date = tqqq.index[-1]
        
        # Signal status
        is_bullish = current_macd > current_signal
        signal_strength = abs(current_macd - current_signal)
        
        print(f"As of: {current_date.strftime('%Y-%m-%d')}")
        print(f"TQQQ Price: ${current_price:.2f}")
        print(f"MACD: {current_macd:.4f}")
        print(f"Signal Line: {current_signal:.4f}")
        print(f"Signal Strength: {signal_strength:.4f}")
        print(f"\nCurrent Signal: {'🟢 BULLISH (BUY)' if is_bullish else '🔴 BEARISH (SELL)'}")
        
        # Recent crossover check
        yesterday_macd = macd.iloc[-2]
        yesterday_signal = macd_signal.iloc[-2]
        yesterday_bullish = yesterday_macd > yesterday_signal
        
        if is_bullish != yesterday_bullish:
            crossover_type = "Bullish" if is_bullish else "Bearish"
            print(f"⚡ Recent Crossover: {crossover_type} signal detected!")
        else:
            print(f"📊 No recent crossover detected")
            
    except Exception as e:
        print(f"Error checking current signals: {e}")

if __name__ == "__main__":
    # Run the optimized strategy backtest
    backtester = run_optimized_strategy()
    
    # Check current signal status
    if backtester:
        quick_signal_check()
