"""
Example usage of TypedStrategyManager

This demonstrates how to use the new TypedStrategyManager for orchestrating
typed strategy engines and aggregating their signals.
"""

from datetime import UTC, datetime
from decimal import Decimal

from the_alchemiser.domain.registry.strategy_registry import StrategyType
from the_alchemiser.domain.strategies.protocols.market_data_port import MarketDataPort
from the_alchemiser.domain.strategies.typed_strategy_manager import TypedStrategyManager


def example_usage():
    """Example showing how to use TypedStrategyManager."""
    
    # 1. Create or obtain a MarketDataPort implementation
    # In real usage, this would be your actual market data provider
    market_data_port: MarketDataPort = get_market_data_port()
    
    # 2. Define strategy allocations (optional - uses registry defaults if not provided)
    strategy_allocations = {
        StrategyType.NUCLEAR: 0.4,  # 40% allocation to Nuclear strategy
        StrategyType.TECL: 0.6,     # 60% allocation to TECL strategy
        # StrategyType.KLM: 0.2     # Could add KLM if desired
    }
    
    # 3. Initialize the TypedStrategyManager
    strategy_manager = TypedStrategyManager(
        market_data_port=market_data_port,
        strategy_allocations=strategy_allocations
    )
    
    # 4. Generate signals from all strategies
    timestamp = datetime.now(UTC)
    aggregated_signals = strategy_manager.generate_all_signals(timestamp)
    
    # 5. Access individual strategy signals
    print("Signals by strategy:")
    for strategy_type, signals in aggregated_signals.get_signals_by_strategy().items():
        print(f"  {strategy_type.value}: {len(signals)} signals")
        for signal in signals:
            print(f"    {signal.symbol.value}: {signal.action} "
                  f"(confidence: {signal.confidence.value:.2f})")
    
    # 6. Access consolidated signals (after conflict resolution)
    print(f"\nConsolidated signals: {len(aggregated_signals.consolidated_signals)}")
    for signal in aggregated_signals.consolidated_signals:
        print(f"  {signal.symbol.value}: {signal.action} "
              f"(confidence: {signal.confidence.value:.2f})")
        print(f"    Reasoning: {signal.reasoning[:100]}...")
    
    # 7. Check for conflicts that were resolved
    if aggregated_signals.conflicts:
        print(f"\nConflicts resolved: {len(aggregated_signals.conflicts)}")
        for conflict in aggregated_signals.conflicts:
            print(f"  {conflict['symbol']}: {conflict['strategies']} -> {conflict['resolution']}")
    
    # 8. Get all signals for further processing
    all_signals = aggregated_signals.get_all_signals()
    print(f"\nTotal signals generated: {len(all_signals)}")
    
    return aggregated_signals


def get_market_data_port() -> MarketDataPort:
    """
    Get a MarketDataPort implementation.
    
    In real usage, this would return your actual market data provider
    that implements the MarketDataPort protocol.
    """
    # This is just a placeholder - in real usage you'd return something like:
    # return AlpacaMarketDataAdapter(api_key, secret_key)
    # or 
    # return YahooFinanceAdapter()
    raise NotImplementedError("Implement your MarketDataPort provider here")


def demonstrate_conflict_resolution():
    """Example showing how conflict resolution works."""
    
    print("TypedStrategyManager Conflict Resolution Example")
    print("=" * 50)
    
    print("\nWhen strategies agree:")
    print("- Nuclear strategy: BUY AAPL (confidence: 0.8)")
    print("- TECL strategy: BUY AAPL (confidence: 0.6)")
    print("- Result: BUY AAPL (weighted confidence: 0.72)")
    print("  (0.8 * 0.4 + 0.6 * 0.6 = 0.72 with 40/60 allocation)")
    
    print("\nWhen strategies disagree:")
    print("- Nuclear strategy: BUY AAPL (confidence: 0.9, weight: 0.4, score: 0.36)")
    print("- TECL strategy: SELL AAPL (confidence: 0.7, weight: 0.6, score: 0.42)")
    print("- Result: SELL AAPL (TECL wins with higher weighted score)")
    
    print("\nBenefits:")
    print("- Automatic conflict detection and resolution")
    print("- Transparent reasoning for all decisions")
    print("- Strategy allocation weighting")
    print("- Comprehensive audit trail")


if __name__ == "__main__":
    # Run the conflict resolution demonstration
    demonstrate_conflict_resolution()
    
    # To run the full example, implement get_market_data_port() first
    # aggregated_signals = example_usage()