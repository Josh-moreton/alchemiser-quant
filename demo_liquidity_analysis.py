#!/usr/bin/env python3
"""
Demonstration of the new liquidity-aware smart execution strategy.

This script shows how the enhanced execution logic analyzes volume data
and makes intelligent pricing decisions based on actual market liquidity.
"""

import logging
from datetime import UTC, datetime
from decimal import Decimal

# Mock QuoteModel for demonstration
class MockQuoteModel:
    def __init__(self, symbol: str, bid_price: float, ask_price: float, 
                 bid_size: float, ask_size: float):
        self.symbol = symbol
        self.bid_price = bid_price
        self.ask_price = ask_price
        self.bid_size = bid_size
        self.ask_size = ask_size
        self.timestamp = datetime.now(UTC)
    
    @property
    def spread(self) -> float:
        return self.ask_price - self.bid_price
    
    @property
    def mid_price(self) -> float:
        return (self.bid_price + self.ask_price) / 2

def demo_liquidity_analysis():
    """Demonstrate the liquidity analysis with different market scenarios."""
    
    # Import here to avoid the pandas issue
    import sys
    import os
    sys.path.append(os.path.dirname(__file__))
    
    from the_alchemiser.execution_v2.utils.liquidity_analysis import LiquidityAnalyzer
    
    print("🧠 Liquidity-Aware Smart Execution Demo")
    print("=" * 50)
    
    analyzer = LiquidityAnalyzer(min_volume_threshold=100.0, tick_size=0.01)
    
    # Scenario 1: High liquidity, small order
    print("\n📊 Scenario 1: High Liquidity, Small Order")
    quote1 = MockQuoteModel("AAPL", 150.00, 150.02, 5000, 4800)  # Good liquidity
    order_size1 = 100  # Small order
    
    analysis1 = analyzer.analyze_liquidity(quote1, order_size1)
    print(f"Symbol: {analysis1.symbol}")
    print(f"Liquidity Score: {analysis1.liquidity_score:.1f}/100")
    print(f"Volume Imbalance: {analysis1.volume_imbalance:.3f}")
    print(f"Confidence: {analysis1.confidence:.2f}")
    print(f"Recommended Buy Price: ${analysis1.recommended_bid_price:.3f}")
    print(f"Recommended Sell Price: ${analysis1.recommended_ask_price:.3f}")
    
    strategy1 = analyzer.get_execution_strategy_recommendation(analysis1, "buy", order_size1)
    print(f"Execution Strategy: {strategy1}")
    
    # Scenario 2: Low liquidity, large order
    print("\n📊 Scenario 2: Low Liquidity, Large Order")
    quote2 = MockQuoteModel("TSLA", 200.00, 200.10, 200, 180)  # Lower liquidity
    order_size2 = 500  # Large order relative to liquidity
    
    analysis2 = analyzer.analyze_liquidity(quote2, order_size2)
    print(f"Symbol: {analysis2.symbol}")
    print(f"Liquidity Score: {analysis2.liquidity_score:.1f}/100")
    print(f"Volume Imbalance: {analysis2.volume_imbalance:.3f}")
    print(f"Confidence: {analysis2.confidence:.2f}")
    print(f"Recommended Buy Price: ${analysis2.recommended_bid_price:.3f}")
    print(f"Recommended Sell Price: ${analysis2.recommended_ask_price:.3f}")
    
    strategy2 = analyzer.get_execution_strategy_recommendation(analysis2, "buy", order_size2)
    print(f"Execution Strategy: {strategy2}")
    
    # Scenario 3: Volume imbalanced market
    print("\n📊 Scenario 3: Volume Imbalanced Market (Heavy Ask Side)")
    quote3 = MockQuoteModel("NVDA", 400.00, 400.05, 500, 2000)  # Heavy ask side
    order_size3 = 300
    
    analysis3 = analyzer.analyze_liquidity(quote3, order_size3)
    print(f"Symbol: {analysis3.symbol}")
    print(f"Liquidity Score: {analysis3.liquidity_score:.1f}/100")
    print(f"Volume Imbalance: {analysis3.volume_imbalance:.3f} (negative=heavy bid, positive=heavy ask)")
    print(f"Confidence: {analysis3.confidence:.2f}")
    print(f"Recommended Buy Price: ${analysis3.recommended_bid_price:.3f}")
    print(f"Recommended Sell Price: ${analysis3.recommended_ask_price:.3f}")
    
    strategy3 = analyzer.get_execution_strategy_recommendation(analysis3, "buy", order_size3)
    print(f"Execution Strategy: {strategy3}")
    
    # Comparison with old simple approach
    print("\n🔄 Comparison with Old Simple Approach:")
    print("Old approach: bid + $0.01 = $150.01 (regardless of volume)")
    print(f"New approach: ${analysis1.recommended_bid_price:.3f} (volume-aware)")
    print(f"New approach considers: order size, volume distribution, market imbalance")
    
    print("\n✅ Demonstration complete!")
    print("\nKey improvements:")
    print("- Analyzes actual volume at price levels")
    print("- Adjusts pricing based on order size vs available liquidity")
    print("- Considers volume imbalance for optimal timing")
    print("- Provides confidence scores and strategy recommendations")
    print("- Goes beyond simple bid/ask + offset pricing")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    demo_liquidity_analysis()