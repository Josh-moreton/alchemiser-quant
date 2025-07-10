#!/usr/bin/env python3
"""
LSE Portfolio Analysis - Summary and Quick Start Guide

This script provides a comprehensive analysis of all tradeable LSE instruments
to find the optimal portfolio alongside LQQ3.
"""

def print_usage_guide():
    print("=" * 80)
    print("LSE PORTFOLIO OPTIMIZER - QUICK START GUIDE")
    print("=" * 80)
    
    print("\n🎯 OBJECTIVE:")
    print("Find the best 2-3 stock portfolio with 66% LQQ3 + other LSE instruments")
    print("Optimizing for Calmar ratio (CAGR / Max Drawdown)")
    
    print("\n📊 WHAT GETS TESTED:")
    print("✓ ALL LSE stocks (FTSE 100, FTSE 250, AIM, etc.)")
    print("✓ ALL ETFs (equity, bond, commodity, currency, sector)")
    print("✓ Investment trusts and REITs")
    print("✓ Bond and fixed income instruments")
    print("✓ Commodities (gold, silver, oil, gas, etc.)")
    print("✓ Currency hedged products")
    print("✓ Leveraged and inverse products")
    print("✓ Alternative investments")
    
    print("\n🚀 HOW TO RUN:")
    print("1. Test the discovery system first:")
    print("   python test_lse_discovery.py")
    
    print("\n2. Run the full analysis:")
    print("   python lse_portfolio_optimizer.py           # Comprehensive (15-20 min)")
    print("   python lse_portfolio_optimizer.py --fallback   # Fast mode (5-10 min)")
    
    print("\n3. Results will be saved as:")
    print("   - lse_2stock_portfolio_results_YYYYMMDD_HHMMSS.csv")
    print("   - lse_3stock_portfolio_results_YYYYMMDD_HHMMSS.csv")
    print("   - discovered_lse_tickers_YYYYMMDD_HHMMSS.txt")
    
    print("\n⚡ PERFORMANCE NOTES:")
    print("- First run: Discovers all LSE tickers (slow but comprehensive)")
    print("- Later runs: Reuses discovered tickers (much faster)")
    print("- Delete discovery files to force re-discovery")
    
    print("\n📈 OUTPUT METRICS:")
    print("- Calmar Ratio (primary optimization target)")
    print("- CAGR (Compound Annual Growth Rate)")
    print("- Maximum Drawdown")
    print("- Sharpe Ratio")
    print("- Sortino Ratio")
    print("- Volatility")
    
    print("\n🎮 EXAMPLE USAGE:")
    print("# Test discovery system")
    print("python test_lse_discovery.py")
    print()
    print("# Run comprehensive analysis")
    print("python lse_portfolio_optimizer.py")
    print()
    print("# Quick analysis with curated list")
    print("python lse_portfolio_optimizer.py --fallback")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    print_usage_guide()
