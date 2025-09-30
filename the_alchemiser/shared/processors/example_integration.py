#!/usr/bin/env python3
"""Example integration of RealTimeDataProcessor with RealTimePricingService.

This example demonstrates how to integrate the real-time data processor
with the WebSocket pricing service to process and aggregate market data.
"""

from datetime import UTC, datetime

from the_alchemiser.shared.processors import RealTimeDataProcessor
from the_alchemiser.shared.types.market_data import QuoteModel


def main() -> None:
    """Demonstrate real-time data processor usage."""
    print("📊 Real-Time Data Processor Integration Example\n")

    # Initialize processor with custom configuration
    from the_alchemiser.shared.processors.real_time_data_processor import ProcessingConfig

    config = ProcessingConfig(
        max_quote_history=50,
        max_trade_history=50,
        vwap_window_seconds=300,  # 5 minutes
        max_spread_threshold=0.05,  # 5% spread threshold
        min_quote_age_seconds=30,  # 30 second stale threshold
    )

    processor = RealTimeDataProcessor(config=config)
    print("✓ Initialized processor with custom configuration\n")

    # Simulate processing quotes for multiple symbols
    symbols = ["AAPL", "MSFT", "GOOGL"]

    print("Processing quotes for multiple symbols...")
    for i, symbol in enumerate(symbols):
        quote = QuoteModel(
            symbol=symbol,
            bid_price=150.0 + i * 50.0,
            ask_price=150.10 + i * 50.0,
            bid_size=100.0,
            ask_size=100.0,
            timestamp=datetime.now(UTC),
        )
        result = processor.process_quote(quote)
        print(f"  {symbol}: mid=${result['mid_price']:.2f}, spread=${result['spread']:.2f}")

    print()

    # Simulate processing trades
    print("Processing trades...")
    for symbol in symbols:
        for j in range(3):
            price = 150.0 + symbols.index(symbol) * 50.0 + j * 0.50
            result = processor.process_trade(
                symbol=symbol, price=price, size=100.0, timestamp=datetime.now(UTC)
            )
        print(
            f"  {symbol}: vwap=${result['vwap']:.2f}, "
            f"volume={result['total_volume']:.0f} shares"
        )

    print()

    # Display aggregated metrics
    print("Symbol Metrics Summary:")
    print("-" * 70)
    all_metrics = processor.get_all_metrics()
    for symbol, metrics in all_metrics.items():
        print(f"\n{symbol}:")
        print(f"  Quotes processed: {metrics.quote_count}")
        print(f"  Trades processed: {metrics.trade_count}")
        print(f"  Total volume: {metrics.total_volume:.0f} shares")
        print(f"  VWAP: ${metrics.vwap:.2f}")
        print(f"  Avg spread: ${metrics.avg_spread:.4f}")
        print(f"  Min spread: ${metrics.min_spread:.4f}")
        print(f"  Max spread: ${metrics.max_spread:.4f}")

    print("\n" + "=" * 70)
    print("✅ Integration example completed successfully!")


if __name__ == "__main__":
    main()
