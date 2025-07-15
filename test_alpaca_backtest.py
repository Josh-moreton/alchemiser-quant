#!/usr/bin/env python3
"""
Test script for Alpaca-based Nuclear Strategy Backtest
"""

import logging
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.backtest.nuclear_backtest_framework import (
    AlpacaBacktestDataProvider, 
    BacktestNuclearStrategy, 
    PortfolioBuilder,
    SignalTracker
)

def test_alpaca_backtest():
    """Test the Alpaca-based backtest framework"""
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    logger = logging.getLogger(__name__)
    
    print("🚀 TESTING ALPACA-BASED NUCLEAR STRATEGY BACKTEST")
    print("=" * 60)
    
    # Setup
    start_date = '2024-10-01'
    end_date = '2024-12-31'
    
    try:
        # Initialize Alpaca data provider
        print("📡 Initializing Alpaca Data Provider...")
        data_provider = AlpacaBacktestDataProvider(start_date, end_date)
        
        # Initialize strategy
        print("🧠 Initializing Nuclear Strategy...")
        strategy = BacktestNuclearStrategy(data_provider)
        
        # Initialize other components
        signal_tracker = SignalTracker()
        portfolio_builder = PortfolioBuilder(strategy)
        
        # Download data from Alpaca
        print("📊 Downloading data from Alpaca API...")
        all_data = data_provider.download_all_data(strategy.all_symbols)
        
        if not all_data:
            print("❌ No data downloaded! Check your Alpaca API credentials.")
            return False
        
        print(f"✅ Downloaded data for {len(all_data)} symbols")
        
        # Show data coverage
        coverage = data_provider.validate_data_coverage(strategy.all_symbols)
        print("\n📈 Data Coverage Report:")
        for symbol, info in coverage.items():
            if info['status'] == 'available':
                print(f"  ✅ {symbol}: {info['bars']} bars, {info['date_range']}")
            else:
                print(f"  ❌ {symbol}: {info['status']}")
        
        # Test strategy evaluation at specific date
        test_date = pd.Timestamp('2024-11-15')
        print(f"\n🧪 Testing strategy evaluation on {test_date.date()}...")
        
        # Check if we have data for this date
        spy_data = data_provider.get_data_up_to_date('SPY', test_date)
        print(f"SPY data available up to {test_date.date()}: {len(spy_data)} records")
        
        if not spy_data.empty:
            print(f"SPY data range: {spy_data.index[0].date()} to {spy_data.index[-1].date()}")
            
            # Test strategy evaluation
            signal, action, reason, indicators, market_data = strategy.evaluate_strategy_at_time(test_date)
            
            print(f"\n📊 Strategy Results for {test_date.date()}:")
            print(f"  Signal: {signal}")
            print(f"  Action: {action}")
            print(f"  Reason: {reason}")
            print(f"  Indicators calculated for: {len(indicators)} symbols")
            print(f"  Market data available for: {len(market_data)} symbols")
            
            # Test portfolio building
            if indicators:
                print(f"\n💼 Building target portfolio...")
                target_portfolio = portfolio_builder.build_target_portfolio(
                    signal, action, reason, indicators, 100000
                )
                
                if target_portfolio:
                    print(f"Target Portfolio ({len(target_portfolio)} positions):")
                    total_value = 0
                    for symbol, shares in target_portfolio.items():
                        if shares > 0:
                            price = indicators[symbol]['current_price']
                            value = shares * price
                            total_value += value
                            weight = (value / 100000) * 100
                            print(f"  📊 {symbol}: {shares:.2f} shares @ ${price:.2f} = ${value:,.0f} ({weight:.1f}%)")
                    print(f"  💰 Total Portfolio Value: ${total_value:,.0f}")
                else:
                    print("  📋 No positions in target portfolio (HOLD signal)")
            
        print("\n✅ Alpaca backtest framework test completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import pandas as pd
    success = test_alpaca_backtest()
    if success:
        print("\n🎉 All tests passed! Alpaca backtest framework is ready to use.")
    else:
        print("\n💥 Tests failed! Check your Alpaca API credentials and dependencies.")
        sys.exit(1)
