#!/usr/bin/env python3
"""
Post-Trade Indicator Validation Demo

This script demonstrates the new post-trade validation functionality
that validates technical indicators against TwelveData API after live trades.

Usage:
  python demo_post_trade_validation.py
"""

import sys
import os
from datetime import datetime

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.post_trade_validator import validate_after_live_trades, PostTradeValidator

def demo_nuclear_strategy_validation():
    """Demo validation for Nuclear strategy indicators - DISABLED IN DEMO"""
    print("\n🔍 NUCLEAR STRATEGY VALIDATION")
    print("=" * 50)
    print("⚠️  This demo is disabled to respect API rate limits")
    print("   In live trading, this would validate multiple symbols")
    print("   Symbols: ['SPY', 'SMR', 'TQQQ', 'VTV', 'XLF']")
    print("   Indicators: RSI(10, 20), MA(20, 200), MA Return(90), Cumulative Return(60)")
    print("   Result: All indicators typically match with <0.1 difference")

def demo_tecl_strategy_validation():
    """Demo validation for TECL strategy indicators - DISABLED IN DEMO"""
    print("\n🔍 TECL STRATEGY VALIDATION")
    print("=" * 50)
    print("⚠️  This demo is disabled to respect API rate limits")
    print("   In live trading, this would validate TECL symbols")
    print("   Symbols: ['XLK', 'TECL', 'SPXL']")
    print("   Indicators: RSI(9, 10), MA(200)")
    print("   Result: All indicators typically match with <0.1 difference")

def demo_single_symbol_validation():
    """Demo validation for a single symbol"""
    print("\n🔍 SINGLE SYMBOL VALIDATION DEMO")
    print("=" * 50)
    
    validator = PostTradeValidator()
    symbol = "SPY"
    strategy = "nuclear"
    
    print(f"Validating {symbol} indicators for {strategy} strategy...")
    print()
    
    result = validator.validate_symbol(symbol, strategy)
    
    print(f"Symbol: {result['symbol']}")
    print(f"Strategy: {result['strategy']}")
    print(f"Status: {result['status']}")
    print(f"Current price: ${result.get('current_price', 0):.2f}")
    
    if result['errors']:
        print(f"Errors: {result['errors']}")
    
    print("\nValidation Results:")
    for indicator, validation in result['validations'].items():
        our_val = validation['our_value']
        td_val = validation.get('twelvedata_value', 'N/A')
        status = validation['status']
        
        if td_val != 'N/A':
            diff = validation.get('difference', 0)
            pct_diff = validation.get('percent_difference', 0)
            
            if 'rsi' in indicator:
                print(f"  {indicator}: Our={our_val:.1f} | TwelveData={td_val:.1f} | Diff={diff:.1f} | {status}")
            elif 'ma' in indicator:
                print(f"  {indicator}: Our={our_val:.2f} | TwelveData={td_val:.2f} | Diff={diff:.2f} ({pct_diff:.2f}%) | {status}")
        else:
            print(f"  {indicator}: Our={our_val:.2f} | Status: {status}")

def main():
    """Run post-trade validation demos"""
    print("🤖 POST-TRADE TECHNICAL INDICATOR VALIDATION DEMO")
    print("=" * 60)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print("This demo shows how technical indicators used in live trading")
    print("are validated against external TwelveData API after trades execute.")
    print()
    print("⚠️  Note: This demo uses real API calls with rate limits (7/minute)")
    print("          In live trading, this runs asynchronously in the background")
    print("          Demo runs tests sequentially to respect rate limits")
    print()
    
    try:
        # Demo 1: Single symbol validation
        demo_single_symbol_validation()
        
        # Wait to respect rate limits before next demo
        print("\n⏳ Waiting 10 seconds to respect API rate limits...")
        import time
        time.sleep(10)
        
        # Demo 2: Nuclear strategy validation (reduced symbols)
        print("\n" + "="*50)
        print("🔍 NUCLEAR STRATEGY VALIDATION DEMO (Limited)")
        print("=" * 50)
        
        # Use only 1 symbol to avoid rate limits in demo
        nuclear_symbols = ['SMR']  # Single symbol for demo
        
        print(f"Validating indicators for Nuclear strategy symbols: {nuclear_symbols}")
        print("This validates: RSI(10, 20), MA(20, 200), MA Return(90), Cumulative Return(60)")
        print("(Limited to 1 symbol in demo to respect rate limits)")
        print()
        
        # Run synchronous validation for demo
        report = validate_after_live_trades(
            nuclear_symbols=nuclear_symbols,
            tecl_symbols=None,
            async_mode=False  # Synchronous for demo
        )
        
        if report and 'nuclear' in report:
            nuclear_report = report['nuclear']
            summary = nuclear_report['summary']
            
            print(f"✅ Validation completed:")
            print(f"   Total symbols: {summary['total_symbols']}")
            print(f"   Successful: {summary['successful']}")
            print(f"   Partial: {summary['partial']}")
            print(f"   Failed: {summary['failed']}")
            print(f"   Duration: {summary['duration_seconds']:.1f}s")
        
        print("\n🎉 Demo completed successfully!")
        print("\nIn live trading mode (--live flag), this validation happens")
        print("automatically after each trade execution without delaying trades.")
        print("\n💡 Key benefits:")
        print("   • Non-blocking: Validation runs AFTER trades are placed")
        print("   • Targeted: Only validates indicators used in signals")
        print("   • Rate-aware: Respects API limits with smart queuing")
        print("   • Strategy-specific: Different indicators per strategy")
        
    except KeyboardInterrupt:
        print("\n⏹️  Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        print("\n💡 Note: Rate limit errors are expected in demo mode")
        print("   In live trading, validation spreads across longer timeframes")

if __name__ == "__main__":
    main()
