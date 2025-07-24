#!/usr/bin/env python3
"""
TECL Strategy Test Script

This script tests and debugs the TECL strategy engine by running it
and showing all technical indicators and decision logic.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import logging
from datetime import datetime

# Set up detailed logging for debugging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

from the_alchemiser.core.tecl_strategy_engine import TECLStrategyEngine
from the_alchemiser.core.data_provider import UnifiedDataProvider

def test_tecl_strategy():
    """Test the TECL strategy and show all indicators"""
    
    print("🚀 TECL STRATEGY DEBUG TEST")
    print("=" * 70)
    print(f"Test run at: {datetime.now()}")
    print()
    
    try:
        # Initialize data provider and strategy engine
        print("📊 Step 1: Initializing data provider and strategy engine...")
        data_provider = UnifiedDataProvider(paper_trading=True)
        engine = TECLStrategyEngine(data_provider=data_provider)
        print("✅ Strategy engine initialized")
        print()
        
        # Get market data
        print("📈 Step 2: Fetching market data...")
        market_data = engine.get_market_data()
        print(f"✅ Fetched data for {len(market_data)} symbols: {list(market_data.keys())}")
        print()
        
        # Calculate indicators
        print("🔬 Step 3: Calculating technical indicators...")
        indicators = engine.calculate_indicators(market_data)
        print(f"✅ Calculated indicators for {len(indicators)} symbols")
        print()
        
        # Show all technical indicators
        print("📋 DETAILED TECHNICAL INDICATORS:")
        print("-" * 50)
        
        # Market regime detection
        if 'SPY' in indicators:
            spy_price = indicators['SPY']['current_price']
            spy_ma_200 = indicators['SPY']['ma_200']
            spy_rsi_10 = indicators['SPY']['rsi_10']
            market_regime = "BULL" if spy_price > spy_ma_200 else "BEAR"
            
            print(f"🎯 MARKET REGIME: {market_regime} MARKET")
            print(f"   SPY Price: ${spy_price:.2f}")
            print(f"   SPY 200-MA: ${spy_ma_200:.2f}")
            print(f"   SPY RSI(10): {spy_rsi_10:.2f}")
            print()
        
        # Show all indicators for each symbol
        key_symbols = ['SPY', 'TQQQ', 'SPXL', 'XLK', 'KMLM', 'TECL', 'UVXY', 'BIL', 'BSV', 'SQQQ']
        
        for symbol in key_symbols:
            if symbol in indicators:
                ind = indicators[symbol]
                print(f"📊 {symbol}:")
                print(f"   Price: ${ind['current_price']:.2f}")
                print(f"   RSI(9): {ind.get('rsi_9', 'N/A'):.2f}" if 'rsi_9' in ind else f"   RSI(9): N/A")
                print(f"   RSI(10): {ind['rsi_10']:.2f}")
                if 'ma_200' in ind:
                    print(f"   200-MA: ${ind['ma_200']:.2f}")
                print()
        
        # Run strategy evaluation with detailed logging
        print("⚡ Step 4: Evaluating TECL strategy (with detailed logging)...")
        print("-" * 50)
        
        symbol_or_allocation, action, reason = engine.evaluate_tecl_strategy(indicators, market_data)
        
        print()
        print("🎯 TECL STRATEGY RESULT:")
        print("=" * 30)
        print(f"Action: {action}")
        
        if isinstance(symbol_or_allocation, dict):
            print("Multi-Asset Allocation:")
            for asset, weight in symbol_or_allocation.items():
                print(f"  {asset}: {weight:.1%}")
        else:
            print(f"Single Asset: {symbol_or_allocation}")
        
        print(f"Reason: {reason}")
        print()
        
        # Show strategy decision path analysis
        print("🔍 DECISION PATH ANALYSIS:")
        print("-" * 30)
        
        if 'SPY' in indicators:
            spy_price = indicators['SPY']['current_price']
            spy_ma_200 = indicators['SPY']['ma_200']
            
            if spy_price > spy_ma_200:
                print("✅ Bull Market Path (SPY > 200-MA)")
                
                # Check bull market conditions in order
                if 'TQQQ' in indicators:
                    tqqq_rsi = indicators['TQQQ']['rsi_10']
                    print(f"   TQQQ RSI(10): {tqqq_rsi:.2f} {'> 79 (OVERBOUGHT)' if tqqq_rsi > 79 else '≤ 79 (OK)'}")
                
                spy_rsi = indicators['SPY']['rsi_10']
                print(f"   SPY RSI(10): {spy_rsi:.2f} {'> 80 (OVERBOUGHT)' if spy_rsi > 80 else '≤ 80 (OK)'}")
                
                if 'XLK' in indicators and 'KMLM' in indicators:
                    xlk_rsi = indicators['XLK']['rsi_10']
                    kmlm_rsi = indicators['KMLM']['rsi_10']
                    
                    print(f"   XLK RSI(10): {xlk_rsi:.2f}")
                    print(f"   KMLM RSI(10): {kmlm_rsi:.2f}")
                    
                    if xlk_rsi > kmlm_rsi:
                        print(f"   → XLK stronger than KMLM ({xlk_rsi:.2f} > {kmlm_rsi:.2f})")
                        if xlk_rsi > 81:
                            print(f"   → XLK EXTREMELY OVERBOUGHT ({xlk_rsi:.2f} > 81) → BIL")
                        else:
                            print(f"   → XLK strong but not extreme → TECL")
                    else:
                        print(f"   → KMLM stronger than XLK ({kmlm_rsi:.2f} > {xlk_rsi:.2f})")
                        if xlk_rsi < 29:
                            print(f"   → XLK OVERSOLD ({xlk_rsi:.2f} < 29) → TECL")
                        else:
                            print(f"   → XLK weak → BIL (defensive)")
                
            else:
                print("⚠️  Bear Market Path (SPY < 200-MA)")
                
                # Check bear market conditions in order
                if 'TQQQ' in indicators:
                    tqqq_rsi = indicators['TQQQ']['rsi_10']
                    print(f"   TQQQ RSI(10): {tqqq_rsi:.2f} {'< 31 (OVERSOLD)' if tqqq_rsi < 31 else '≥ 31'}")
                
                if 'SPXL' in indicators:
                    spxl_rsi = indicators['SPXL']['rsi_10']
                    print(f"   SPXL RSI(10): {spxl_rsi:.2f} {'< 29 (OVERSOLD)' if spxl_rsi < 29 else '≥ 29'}")
                
                if 'UVXY' in indicators:
                    uvxy_rsi = indicators['UVXY']['rsi_10']
                    print(f"   UVXY RSI(10): {uvxy_rsi:.2f}")
                    if uvxy_rsi > 84:
                        print(f"   → UVXY EXTREMELY HIGH ({uvxy_rsi:.2f} > 84)")
                    elif uvxy_rsi > 74:
                        print(f"   → UVXY HIGH ({uvxy_rsi:.2f} > 74)")
        
        print()
        print("✅ TECL Strategy test completed successfully!")
        
    except Exception as e:
        print(f"❌ Error running TECL strategy test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_tecl_strategy()
