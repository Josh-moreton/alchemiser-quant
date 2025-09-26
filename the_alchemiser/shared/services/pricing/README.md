# Pricing Service Package

This package provides real-time stock price updates via Alpaca's WebSocket streams for accurate limit order pricing. It has been modularized from the original monolithic `real_time_pricing.py` file for better maintainability and testability.

## Architecture

The package is structured with focused, single-responsibility modules:

### Core Components

- **`facade.py`** - Main `RealTimePricingService` that maintains the original public API while delegating to extracted components
- **`models.py`** - Data structures and DTOs (`RealTimeQuote`, `SubscriptionPlan`, `QuoteValues`)
- **`data_store.py`** - Thread-safe `PricingDataStore` for quote/trade storage with encapsulated locking

### Parsing & Processing

- **`quote_parser.py`** - Pure functions for converting Alpaca quote data into domain DTOs
- **`trade_parser.py`** - Pure functions for converting Alpaca trade data into domain DTOs

### Service Management

- **`stream_runner.py`** - WebSocket stream lifecycle management with retry logic and circuit breaker coordination
- **`subscription_planner.py`** - Bulk subscription planning, replacement policy, and priority management
- **`bootstrap.py`** - Credential/environment loading and feed selection logic
- **`stats.py`** - Thread-safe metrics and state accumulation
- **`cleanup.py`** - Stale quote garbage collection and memory management

### Compatibility

- **`compat.py`** - Legacy compatibility helpers for backward compatibility
- **`__init__.py`** - Package public API exports

## Usage

### Basic Usage

```python
from the_alchemiser.shared.services.pricing import RealTimePricingService

# Initialize service (same API as before)
service = RealTimePricingService(
    api_key="your_api_key",
    secret_key="your_secret_key", 
    paper_trading=True,
    max_symbols=30
)

# Start streaming
success = service.start()

# Subscribe to symbols
service.subscribe_symbol("AAPL", priority=1000.0)
service.bulk_subscribe_symbols(["MSFT", "GOOGL"], priority=500.0)

# Get real-time data
quote = service.get_quote_data("AAPL")  # New structured data (preferred)
price = service.get_real_time_price("AAPL")  # Best available price

# Legacy compatibility (with deprecation warning)
legacy_quote = service.get_real_time_quote("AAPL")  

# Stop service
service.stop()
```

### Migration from Original Module

**Old import:**
```python
from the_alchemiser.shared.services.real_time_pricing import RealTimePricingService
```

**New import:**
```python
from the_alchemiser.shared.services.pricing import RealTimePricingService
```

The old import still works but shows a deprecation warning. All public methods remain identical.

## Key Design Principles

1. **Reuse existing infrastructure** - Leverages `CircuitBreaker`, `WebSocketConnectionManager`, and domain DTOs from the shared utilities
2. **Maintain backward compatibility** - All existing public methods work identically with appropriate deprecation warnings
3. **Single responsibility** - Each module has a focused purpose and clear boundaries
4. **Thread safety** - Lock usage is encapsulated within appropriate components (`PricingDataStore`)
5. **Testability** - Pure functions and dependency injection enable focused unit testing

## Dependencies

The package reuses existing shared utilities:
- `shared.utils.circuit_breaker.ConnectionCircuitBreaker` - Connection retry/guard logic
- `shared.brokers.alpaca_utils.create_stock_data_stream` - Stream creation
- `shared.types.market_data.QuoteModel`, `PriceDataModel` - Structured data types

## Testing

Each module is designed for focused unit testing:

```python
# Test parsing functions
from the_alchemiser.shared.services.pricing.quote_parser import extract_quote_values

# Test subscription planning
from the_alchemiser.shared.services.pricing.subscription_planner import SubscriptionPlanner

# Test data storage
from the_alchemiser.shared.services.pricing.data_store import PricingDataStore
```

## Performance Considerations

- **Thread-safe storage** - All locking is encapsulated in `PricingDataStore`
- **Async processing** - Quote/trade handlers use `asyncio.to_thread` for blocking operations
- **Memory management** - `QuoteCleanupManager` handles periodic cleanup of stale data
- **Connection efficiency** - Reuses existing `WebSocketConnectionManager` patterns

## Future Enhancements

The modular structure enables easy enhancements:
- Add more sophisticated subscription algorithms in `subscription_planner.py`
- Extend parsing capabilities in `quote_parser.py`/`trade_parser.py`
- Implement different storage backends in `data_store.py`
- Add more comprehensive metrics in `stats.py`