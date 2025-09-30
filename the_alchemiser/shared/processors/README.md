# Real-Time Data Processors

**Business Unit:** shared | **Status:** current

## Overview

The processors module provides real-time market data processing capabilities for WebSocket streams. It transforms raw market data (quotes, trades, bars) into structured, validated, and enriched data suitable for consumption by trading strategies and other system components.

## Architecture

The module follows the event-driven architecture of the Alchemiser system:

- **Input**: Raw market data from WebSocket streams (via `RealTimePricingService`)
- **Processing**: Validation, aggregation, and enrichment
- **Output**: Structured events and metrics for downstream consumers

## Components

### RealTimeDataProcessor

Main processor class that handles:

1. **Quote Processing**
   - Validates bid/ask prices and sizes
   - Detects suspicious quotes (negative prices, inverted bid/ask, excessive spreads)
   - Calculates spread statistics (min, max, average)
   - Maintains quote history with configurable size limits

2. **Trade Processing**
   - Tracks trade executions with price and volume
   - Calculates volume-weighted average price (VWAP)
   - Maintains trade history with configurable size limits
   - Aggregates total volume per symbol

3. **Metrics Tracking**
   - Per-symbol metrics (quote count, trade count, volumes)
   - Spread statistics (min, max, average)
   - Suspicious quote detection counters
   - Last update timestamps

4. **Memory Management**
   - Automatic cleanup of stale data
   - Configurable history sizes
   - Thread-safe operations

### Configuration

```python
config = ProcessingConfig(
    max_quote_history=100,          # Max quotes per symbol
    max_trade_history=100,          # Max trades per symbol
    vwap_window_seconds=300,        # VWAP calculation window (5 min)
    cleanup_interval_seconds=300,   # Cleanup frequency (5 min)
    max_spread_threshold=0.10,      # 10% spread = suspicious
    min_quote_age_seconds=60        # Stale quote threshold (1 min)
)
```

## Usage

### Basic Usage

```python
from the_alchemiser.shared.processors import RealTimeDataProcessor
from the_alchemiser.shared.types.market_data import QuoteModel

# Initialize processor
processor = RealTimeDataProcessor()

# Process a quote
quote = QuoteModel(
    symbol="AAPL",
    bid_price=150.0,
    ask_price=150.10,
    bid_size=100.0,
    ask_size=100.0,
    timestamp=datetime.now(UTC)
)
result = processor.process_quote(quote)

# Process a trade
result = processor.process_trade(
    symbol="AAPL",
    price=150.05,
    size=100.0,
    timestamp=datetime.now(UTC)
)

# Get metrics
metrics = processor.get_symbol_metrics("AAPL")
print(f"Quote count: {metrics.quote_count}")
print(f"VWAP: {metrics.vwap}")
print(f"Avg spread: {metrics.avg_spread}")
```

### Integration with RealTimePricingService

```python
from the_alchemiser.shared.services.real_time_pricing import RealTimePricingService
from the_alchemiser.shared.processors import RealTimeDataProcessor

pricing_service = RealTimePricingService(...)
processor = RealTimeDataProcessor()

# In your quote handler:
async def on_quote(data):
    quote = create_quote_model(data)  # Convert to QuoteModel
    result = processor.process_quote(quote)
    
    if result["is_suspicious"]:
        logger.warning(f"Suspicious quote detected for {quote.symbol}")
```

## Event Integration

The processor is designed to work with the event-driven architecture:

### Events Produced

- `QuoteReceived`: Emitted when a quote is processed
- `TradeReceived`: Emitted when a trade is processed
- `BarReceived`: Emitted when a bar is aggregated

See `shared/events/schemas.py` for event definitions.

## Quality Checks

The processor performs several quality checks:

1. **Negative Prices**: Detects bid/ask prices ≤ 0
2. **Inverted Bid/Ask**: Detects bid > ask
3. **Excessive Spread**: Detects spread > configured threshold (default 10%)
4. **Stale Data**: Detects quotes older than threshold (default 60s)

## Thread Safety

All operations are thread-safe using internal locking:

- `process_quote()`: Thread-safe
- `process_trade()`: Thread-safe
- `get_symbol_metrics()`: Thread-safe
- `get_all_metrics()`: Thread-safe

## Performance Considerations

1. **Memory Efficiency**
   - Uses `deque` with `maxlen` for bounded history
   - Automatic cleanup of stale data
   - Configurable limits on history sizes

2. **Computational Efficiency**
   - Running averages for statistics
   - Efficient VWAP calculation using sliding window
   - Minimal locking for thread safety

## Module Boundaries

This module is part of `shared/` and:

- ✅ Can be imported by: strategy_v2, portfolio_v2, execution_v2, orchestration
- ❌ Must NOT import from: strategy_v2, portfolio_v2, execution_v2, orchestration
- ✅ Can import from: shared/ (types, logging, events, etc.)

## Testing

Comprehensive test suite available in `tests/shared/processors/`:

```bash
# Run processor tests
python -m pytest tests/shared/processors/ -v
```

## Development Guidelines

### Adding New Metrics

1. Add field to `SymbolMetrics` dataclass
2. Update calculation in `process_quote()` or `process_trade()`
3. Add tests for new metric
4. Update documentation

### Adding New Quality Checks

1. Add check logic to `_check_quote_quality()`
2. Update `SymbolMetrics` if tracking needed
3. Add test cases for new check
4. Update documentation

## Future Enhancements

Potential future features:

- [ ] Bar aggregation from trades
- [ ] Order book depth tracking
- [ ] Volatility calculations
- [ ] Correlation analysis between symbols
- [ ] Market microstructure metrics
- [ ] Event emission for downstream consumers
- [ ] Configurable quality thresholds per symbol
- [ ] Historical data replay for backtesting

## Migration Notes

This is a new module (v2.0.0) with no migration requirements.

## Module Compliance

✅ **Module header**: Present  
✅ **Typing**: Strict typing enforced  
✅ **File size**: < 500 lines  
✅ **Function size**: ≤ 50 lines per function  
✅ **Cyclomatic complexity**: ≤ 10  
✅ **Tests**: Comprehensive test coverage  
✅ **Documentation**: Complete docstrings and README  

## References

- [Real-Time Pricing Service](../services/real_time_pricing.py)
- [Market Data Types](../types/market_data.py)
- [Event Schemas](../events/schemas.py)
- [Architecture Documentation](../../../README.md#event-driven-workflow)
