#!/usr/bin/env python3
"""
Test bear market portfolio combination logic
"""

from nuclear_trading_bot import NuclearStrategyEngine
import pandas as pd

def test_bear_market_combination():
    """Test bear market strategy combination"""
    
    strategy = NuclearStrategyEngine()
    
    # Create mock indicators that will trigger bear market conditions
    # SPY below 200-day MA to trigger bear market logic
    mock_indicators = {
        'SPY': {
            'current_price': 400.0,
            'ma_200': 450.0,  # Price below MA = bear market
            'rsi_10': 45.0,
            'rsi_20': 45.0,
            'ma_20': 410.0,
            'ma_return_90': -5.0,
            'cum_return_60': -8.0
        },
        'TQQQ': {
            'current_price': 50.0,
            'ma_20': 55.0,  # Below 20-day MA
            'rsi_10': 40.0,
            'rsi_20': 40.0,
            'ma_return_90': -10.0,
            'cum_return_60': -15.0
        },
        'QQQ': {
            'current_price': 350.0,
            'ma_20': 360.0,
            'rsi_10': 45.0,
            'rsi_20': 45.0,
            'ma_return_90': -8.0,
            'cum_return_60': -12.0  # More than -10% = triggers bear logic
        },
        'PSQ': {
            'current_price': 15.0,
            'ma_20': 14.0,
            'rsi_10': 40.0,  # Above 35, so won't trigger oversold
            'rsi_20': 38.0,
            'ma_return_90': 5.0,
            'cum_return_60': 8.0
        },
        'TLT': {
            'current_price': 95.0,
            'ma_20': 94.0,
            'rsi_10': 55.0,
            'rsi_20': 60.0,  # Higher than PSQ RSI, so bonds stronger
            'ma_return_90': 2.0,
            'cum_return_60': 3.0
        },
        'IEF': {
            'current_price': 105.0,
            'ma_20': 104.0,
            'rsi_10': 45.0,  # Lower than PSQ RSI(20), so IEF not stronger
            'rsi_20': 42.0,
            'ma_return_90': 1.0,
            'cum_return_60': 1.5
        },
        'SQQQ': {
            'current_price': 8.0,
            'ma_20': 7.5,
            'rsi_10': 50.0,
            'rsi_20': 48.0,
            'ma_return_90': 15.0,
            'cum_return_60': 20.0
        }
    }
    
    print("Testing bear market portfolio combination...")
    print("\nMock market conditions:")
    print(f"SPY: ${mock_indicators['SPY']['current_price']:.0f} (200-MA: ${mock_indicators['SPY']['ma_200']:.0f}) - BEAR MARKET")
    print(f"QQQ 60-day return: {mock_indicators['QQQ']['cum_return_60']:.1f}% (< -10%)")
    print(f"TQQQ vs 20-MA: Below (${mock_indicators['TQQQ']['current_price']:.0f} vs ${mock_indicators['TQQQ']['ma_20']:.0f})")
    print(f"TLT RSI(20): {mock_indicators['TLT']['rsi_20']:.0f} vs PSQ RSI(20): {mock_indicators['PSQ']['rsi_20']:.0f} - Bonds stronger")
    
    # Test bear subgroup evaluations
    bear1_signal = strategy._evaluate_bear_subgroup_1(mock_indicators)
    bear2_signal = strategy._evaluate_bear_subgroup_2(mock_indicators)
    
    print(f"\nBear 1 signal: {bear1_signal[0]} - {bear1_signal[2]}")
    print(f"Bear 2 signal: {bear2_signal[0]} - {bear2_signal[2]}")
    
    # Test full bear market logic (should combine if different)
    bear_result = strategy._evaluate_bear_market_logic(mock_indicators)
    
    print(f"\nFinal bear market result: {bear_result[0]} - {bear_result[2]}")
    
    # If it's a portfolio signal, show the breakdown
    if bear_result[0] == 'BEAR_PORTFOLIO':
        print("\n✅ SUCCESS: Bear market strategies are being combined!")
        print("Portfolio combination is working as expected.")
        
        # Extract allocation details
        import re
        portfolio_match = re.findall(r'(\w+) \((\d+\.?\d*)%\)', bear_result[2])
        if portfolio_match:
            print("\nPortfolio allocations:")
            for symbol, allocation in portfolio_match:
                print(f"  {symbol}: {allocation}%")
    else:
        print(f"\n⚠️  Single position selected: {bear_result[0]}")
        print("This means both bear strategies recommended the same position.")
    
    # Test the full strategy evaluation
    print("\n" + "="*50)
    print("Testing full strategy evaluation:")
    
    full_result = strategy.evaluate_nuclear_strategy(mock_indicators)
    print(f"Full strategy result: {full_result[0]} - {full_result[2]}")
    
    return bear_result

if __name__ == "__main__":
    test_bear_market_combination()
