#!/usr/bin/env python3
"""
Test script to verify nuclear portfolio allocation matches Composer.trade
"""

import sys
sys.path.append('.')

from nuclear_trading_bot import NuclearTradingBot

def test_nuclear_portfolio():
    print("🧪 Testing Nuclear Portfolio Allocation")
    print("=" * 50)
    
    # Create bot
    bot = NuclearTradingBot()
    
    # Get market data
    market_data = bot.strategy.get_market_data()
    indicators = bot.strategy.calculate_indicators(market_data)
    
    # Show nuclear stock performance
    print("\n📊 Nuclear Stock Performance (90-day MA return):")
    nuclear_symbols = ['SMR', 'BWXT', 'LEU', 'EXC', 'NLR', 'OKLO']
    nuclear_performance = []
    
    for symbol in nuclear_symbols:
        if symbol in indicators:
            performance = indicators[symbol]['ma_return_90']
            price = indicators[symbol]['current_price']
            nuclear_performance.append((symbol, performance, price))
            print(f"   {symbol}: {performance:.2f}% return, ${price:.2f}")
    
    # Sort by performance
    nuclear_performance.sort(key=lambda x: x[1], reverse=True)
    
    print(f"\n🏆 Top 3 Nuclear Stocks by 90-day MA Return:")
    for i, (symbol, performance, price) in enumerate(nuclear_performance[:3]):
        print(f"   {i+1}. {symbol}: {performance:.2f}% return, ${price:.2f}")
    
    # Get portfolio allocation
    portfolio = bot.get_current_portfolio_allocation()
    
    if portfolio:
        print(f"\n💼 Current Portfolio Allocation (Equal Weight):")
        for symbol, data in portfolio.items():
            print(f"   {symbol}: {data['weight']:.1%} = ${data['market_value']:.2f} ({data['shares']:.1f} shares @ ${data['current_price']:.2f})")
    else:
        print("\n❌ No nuclear portfolio allocation (not in bull market)")
    
    # Check market conditions
    print(f"\n🌡️  Market Conditions:")
    if 'SPY' in indicators:
        spy_price = indicators['SPY']['current_price']
        spy_ma_200 = indicators['SPY']['ma_200']
        spy_rsi = indicators['SPY']['rsi_10']
        
        print(f"   SPY Price: ${spy_price:.2f}")
        print(f"   SPY 200-day MA: ${spy_ma_200:.2f}")
        print(f"   SPY RSI(10): {spy_rsi:.1f}")
        print(f"   Market Regime: {'Bull' if spy_price > spy_ma_200 else 'Bear'}")
    
    print(f"\n🔍 Composer.trade shows: LEU, OKLO, SMR (33.3% each)")
    print(f"   Our analysis should match this if market conditions are the same")

if __name__ == "__main__":
    test_nuclear_portfolio()
