#!/usr/bin/env python3
"""
Standalone demonstration of the liquidity analysis logic.

This shows the core volume-aware pricing logic without external dependencies.
"""

import logging
from datetime import UTC, datetime
from typing import NamedTuple
from dataclasses import dataclass

# Local mock of QuoteModel to avoid import issues
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

@dataclass
class LiquidityAnalysis:
    """Analysis results for market liquidity."""
    
    symbol: str
    total_bid_volume: float
    total_ask_volume: float
    volume_imbalance: float  # (ask_vol - bid_vol) / (ask_vol + bid_vol)
    liquidity_score: float  # 0-100, higher = more liquid
    recommended_bid_price: float
    recommended_ask_price: float
    volume_at_recommended_bid: float
    volume_at_recommended_ask: float
    confidence: float  # 0-1, confidence in recommendations

class SimpleLiquidityAnalyzer:
    """Simplified version of the liquidity analyzer for demonstration."""
    
    def __init__(self, min_volume_threshold: float = 100.0, tick_size: float = 0.01):
        self.min_volume_threshold = min_volume_threshold
        self.tick_size = tick_size

    def analyze_liquidity(self, quote: MockQuoteModel, order_size: float) -> LiquidityAnalysis:
        """Perform comprehensive liquidity analysis."""
        
        # Calculate volume metrics
        total_bid_volume = quote.bid_size
        total_ask_volume = quote.ask_size
        
        # Calculate volume imbalance (-1 = heavy bid, +1 = heavy ask)
        total_volume = total_bid_volume + total_ask_volume
        volume_imbalance = 0.0
        if total_volume > 0:
            volume_imbalance = (total_ask_volume - total_bid_volume) / total_volume
            
        # Calculate liquidity score (0-100)
        liquidity_score = self._calculate_liquidity_score(quote, total_volume)
        
        # Determine optimal pricing based on volume analysis
        recommended_prices = self._calculate_volume_aware_prices(quote, order_size)
        
        # Calculate confidence based on data quality and volume
        confidence = self._calculate_confidence(quote, order_size, total_volume)
        
        return LiquidityAnalysis(
            symbol=quote.symbol,
            total_bid_volume=total_bid_volume,
            total_ask_volume=total_ask_volume,
            volume_imbalance=volume_imbalance,
            liquidity_score=liquidity_score,
            recommended_bid_price=recommended_prices["bid"],
            recommended_ask_price=recommended_prices["ask"],
            volume_at_recommended_bid=total_bid_volume,
            volume_at_recommended_ask=total_ask_volume,
            confidence=confidence
        )

    def _calculate_liquidity_score(self, quote: MockQuoteModel, total_volume: float) -> float:
        """Calculate overall liquidity score (0-100)."""
        # Base score from volume
        volume_score = min(total_volume / 1000.0, 50.0)  # Up to 50 points for volume
        
        # Spread score (tighter spreads = higher score)
        spread_pct = (quote.spread / quote.mid_price) * 100
        spread_score = max(0, 30 - spread_pct * 10)  # Up to 30 points for spread
        
        # Balance score (balanced book = higher score)
        if total_volume > 0:
            volume_ratio = min(quote.bid_size, quote.ask_size) / max(quote.bid_size, quote.ask_size)
            balance_score = volume_ratio * 20  # Up to 20 points for balance
        else:
            balance_score = 0
            
        return min(volume_score + spread_score + balance_score, 100.0)

    def _calculate_volume_aware_prices(self, quote: MockQuoteModel, order_size: float) -> dict[str, float]:
        """Calculate optimal prices based on volume analysis."""
        # Analyze volume sufficiency at current levels
        bid_volume_ratio = order_size / max(quote.bid_size, 1.0)
        ask_volume_ratio = order_size / max(quote.ask_size, 1.0)
        
        # Base pricing at best levels
        recommended_bid = quote.bid_price
        recommended_ask = quote.ask_price
        
        # Adjust based on order size vs available volume
        if bid_volume_ratio > 0.8:  # Order size > 80% of available volume
            # Large order relative to liquidity - be more aggressive
            recommended_bid = quote.bid_price + (self.tick_size * 2)
            print(f"  📈 Large buy order vs liquidity ({bid_volume_ratio:.1%}), pricing aggressively: {recommended_bid}")
        elif bid_volume_ratio > 0.3:  # Order size > 30% of available volume
            # Medium order - price just inside
            recommended_bid = quote.bid_price + self.tick_size
        else:
            # Small order - can be patient, price at best bid
            recommended_bid = quote.bid_price
            
        # Similar logic for ask side
        if ask_volume_ratio > 0.8:
            recommended_ask = quote.ask_price - (self.tick_size * 2)
            print(f"  📉 Large sell order vs liquidity ({ask_volume_ratio:.1%}), pricing aggressively: {recommended_ask}")
        elif ask_volume_ratio > 0.3:
            recommended_ask = quote.ask_price - self.tick_size
        else:
            recommended_ask = quote.ask_price
            
        # Additional adjustments based on volume imbalance
        total_volume = quote.bid_size + quote.ask_size
        if total_volume > 0:
            imbalance = (quote.ask_size - quote.bid_size) / total_volume
            
            # If heavy bid side (imbalance < -0.2), be more aggressive on buys
            if imbalance < -0.2:
                recommended_bid = min(recommended_bid + self.tick_size, quote.ask_price - self.tick_size)
                print(f"  ⚖️ Heavy bid side detected, adjusting buy price to {recommended_bid}")
                
            # If heavy ask side (imbalance > 0.2), be more aggressive on sells  
            elif imbalance > 0.2:
                recommended_ask = max(recommended_ask - self.tick_size, quote.bid_price + self.tick_size)
                print(f"  ⚖️ Heavy ask side detected, adjusting sell price to {recommended_ask}")
        
        return {
            "bid": recommended_bid,
            "ask": recommended_ask
        }

    def _calculate_confidence(self, quote: MockQuoteModel, order_size: float, total_volume: float) -> float:
        """Calculate confidence in the liquidity analysis."""
        confidence = 1.0
        
        # Reduce confidence if volumes are very low
        if total_volume < self.min_volume_threshold:
            volume_penalty = 1.0 - (total_volume / self.min_volume_threshold)
            confidence *= (1.0 - volume_penalty * 0.5)  # Up to 50% penalty
            
        # Reduce confidence if spread is very wide
        spread_pct = (quote.spread / quote.mid_price) * 100
        if spread_pct > 1.0:  # > 1% spread
            spread_penalty = min(spread_pct / 5.0, 0.4)  # Up to 40% penalty
            confidence *= (1.0 - spread_penalty)
            
        # Reduce confidence if order is very large relative to liquidity
        order_volume_ratio = order_size / max(total_volume, 1.0)
        if order_volume_ratio > 1.0:  # Order larger than available liquidity
            size_penalty = min((order_volume_ratio - 1.0) * 0.5, 0.6)  # Up to 60% penalty
            confidence *= (1.0 - size_penalty)
            
        return max(confidence, 0.1)  # Minimum 10% confidence

    def get_execution_strategy_recommendation(self, analysis: LiquidityAnalysis, side: str, order_size: float) -> str:
        """Recommend execution strategy based on liquidity analysis."""
        # High confidence and good liquidity = normal strategy
        if analysis.confidence > 0.8 and analysis.liquidity_score > 70:
            return "normal"
            
        # Low liquidity = patient strategy
        if analysis.liquidity_score < 30:
            return "patient"
            
        # Large order vs available volume = consider splitting
        relevant_volume = (
            analysis.volume_at_recommended_ask if side.lower() == "buy" 
            else analysis.volume_at_recommended_bid
        )
        volume_ratio = order_size / max(relevant_volume, 1.0)
        
        if volume_ratio > 1.5:
            return "split"
            
        # Volume imbalance suggests aggressive strategy
        if side.lower() == "buy" and analysis.volume_imbalance < -0.3:
            return "aggressive"  # Heavy bid side, be aggressive
        elif side.lower() == "sell" and analysis.volume_imbalance > 0.3:
            return "aggressive"  # Heavy ask side, be aggressive
            
        return "normal"

def demo_liquidity_analysis():
    """Demonstrate the liquidity analysis with different market scenarios."""
    
    print("🧠 Liquidity-Aware Smart Execution Demo")
    print("=" * 50)
    
    analyzer = SimpleLiquidityAnalyzer(min_volume_threshold=100.0, tick_size=0.01)
    
    # Scenario 1: High liquidity, small order
    print("\n📊 Scenario 1: High Liquidity, Small Order")
    print("  Market: AAPL bid=150.00(5000 shares) ask=150.02(4800 shares)")
    quote1 = MockQuoteModel("AAPL", 150.00, 150.02, 5000, 4800)  # Good liquidity
    order_size1 = 100  # Small order
    
    analysis1 = analyzer.analyze_liquidity(quote1, order_size1)
    print(f"  📈 Buy order for {order_size1} shares:")
    print(f"    - Liquidity Score: {analysis1.liquidity_score:.1f}/100")
    print(f"    - Volume Imbalance: {analysis1.volume_imbalance:.3f}")
    print(f"    - Confidence: {analysis1.confidence:.2f}")
    print(f"    - Recommended Buy Price: ${analysis1.recommended_bid_price:.3f}")
    print(f"    - OLD approach would use: ${quote1.bid_price + 0.01:.3f} (simple bid + $0.01)")
    
    strategy1 = analyzer.get_execution_strategy_recommendation(analysis1, "buy", order_size1)
    print(f"    - Execution Strategy: {strategy1}")
    
    # Scenario 2: Low liquidity, large order
    print("\n📊 Scenario 2: Low Liquidity, Large Order")
    print("  Market: TSLA bid=200.00(200 shares) ask=200.10(180 shares)")
    quote2 = MockQuoteModel("TSLA", 200.00, 200.10, 200, 180)  # Lower liquidity
    order_size2 = 500  # Large order relative to liquidity
    
    analysis2 = analyzer.analyze_liquidity(quote2, order_size2)
    print(f"  📈 Buy order for {order_size2} shares:")
    print(f"    - Liquidity Score: {analysis2.liquidity_score:.1f}/100")
    print(f"    - Volume Imbalance: {analysis2.volume_imbalance:.3f}")
    print(f"    - Confidence: {analysis2.confidence:.2f}")
    print(f"    - Recommended Buy Price: ${analysis2.recommended_bid_price:.3f}")
    print(f"    - OLD approach would use: ${quote2.bid_price + 0.01:.3f} (simple bid + $0.01)")
    
    strategy2 = analyzer.get_execution_strategy_recommendation(analysis2, "buy", order_size2)
    print(f"    - Execution Strategy: {strategy2}")
    
    # Scenario 3: Volume imbalanced market
    print("\n📊 Scenario 3: Volume Imbalanced Market (Heavy Ask Side)")
    print("  Market: NVDA bid=400.00(500 shares) ask=400.05(2000 shares)")
    quote3 = MockQuoteModel("NVDA", 400.00, 400.05, 500, 2000)  # Heavy ask side
    order_size3 = 300
    
    analysis3 = analyzer.analyze_liquidity(quote3, order_size3)
    print(f"  📈 Buy order for {order_size3} shares:")
    print(f"    - Liquidity Score: {analysis3.liquidity_score:.1f}/100")
    print(f"    - Volume Imbalance: {analysis3.volume_imbalance:.3f} (negative=heavy bid, positive=heavy ask)")
    print(f"    - Confidence: {analysis3.confidence:.2f}")
    print(f"    - Recommended Buy Price: ${analysis3.recommended_bid_price:.3f}")
    print(f"    - OLD approach would use: ${quote3.bid_price + 0.01:.3f} (simple bid + $0.01)")
    
    strategy3 = analyzer.get_execution_strategy_recommendation(analysis3, "buy", order_size3)
    print(f"    - Execution Strategy: {strategy3}")
    
    print("\n🔄 Key Improvements Over Old Approach:")
    print("✅ OLD: Always bid + $0.01 regardless of volume")
    print("✅ NEW: Analyzes actual volume at price levels")
    print("✅ NEW: Adjusts pricing based on order size vs available liquidity")
    print("✅ NEW: Considers volume imbalance for optimal timing")
    print("✅ NEW: Provides confidence scores and strategy recommendations")
    print("✅ NEW: Intelligent fallback strategies for different market conditions")
    
    print("\n🎯 This addresses the user's feedback about true liquidity awareness!")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    demo_liquidity_analysis()