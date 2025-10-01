# Structlog Integration for Alchemiser

This document describes the new structlog integration for enhanced structured logging in the Alchemiser trading platform.

## Overview

The logging system now supports both the traditional Python stdlib logging and the modern [structlog](https://www.structlog.org/) library. A feature flag (`ALCHEMISER_USE_STRUCTLOG`) enables gradual migration between the two systems.

## Why Structlog?

### Benefits

1. **Better Structured Logging**: Automatic serialization of complex types (including Decimal for financial data)
2. **Cleaner APIs**: More intuitive logging with keyword arguments
3. **Context Propagation**: Built-in support for binding context that persists across log calls
4. **Performance**: More efficient than custom formatting
5. **Industry Standard**: Battle-tested library used in production systems

### Trading System Benefits

- **Decimal Support**: Native handling of `Decimal` types for precise financial calculations
- **Context Binding**: Easily attach symbol, strategy, or order_id to all logs in a scope
- **Better Analytics**: Structured output makes log analysis and querying easier
- **Enhanced Debugging**: Rich context automatically included in all log entries

## Feature Flag

Control structlog usage via environment variable:

```bash
# Use stdlib logging (default)
export ALCHEMISER_USE_STRUCTLOG=false

# Use structlog
export ALCHEMISER_USE_STRUCTLOG=true
```

Values recognized as "enabled": `true`, `1`, `yes` (case-insensitive)

## Usage

### Basic Logging

```python
from the_alchemiser.shared.logging import get_logger

logger = get_logger(__name__)
logger.info("Order placed", symbol="AAPL", quantity=100, price=Decimal("150.25"))
```

### Structlog-Specific Features

When `ALCHEMISER_USE_STRUCTLOG=true`:

```python
from the_alchemiser.shared.logging import (
    get_structlog_logger,
    bind_trading_context,
)

# Get a structlog logger
logger = get_structlog_logger(__name__)

# Bind persistent context
logger = bind_trading_context(
    logger,
    symbol="AAPL",
    strategy="momentum"
)

# All subsequent logs include bound context
logger.info("Signal generated", confidence=0.85)
# Output includes symbol="AAPL" and strategy="momentum"

logger.info("Order placed", order_id="ord-123")
# Output includes symbol="AAPL", strategy="momentum", and order_id="ord-123"
```

### Trading-Specific Helpers

These helpers work with both stdlib and structlog through the migration bridge:

```python
from the_alchemiser.shared.logging import (
    get_logger,
    log_order_flow,
    log_repeg_operation,
    log_data_integrity_checkpoint,
)

logger = get_logger(__name__)

# Log order flow events (automatically delegates to structlog or stdlib)
log_order_flow(
    logger,
    stage="submission",
    symbol="TSLA",
    quantity=Decimal("50"),
    price=Decimal("250.00"),
    order_id="ord-123",
    execution_strategy="smart_limit"
)

# Log repeg operations with automatic price improvement calculation
log_repeg_operation(
    logger,
    operation="replace_order",
    symbol="NVDA",
    old_price=Decimal("500.00"),
    new_price=Decimal("505.00"),
    quantity=Decimal("10"),
    reason="market_movement",
    repeg_attempt=2,
    max_repegs=5
)

# Log data integrity checkpoints with validation
log_data_integrity_checkpoint(
    logger,
    stage="portfolio_allocation",
    data={"AAPL": 0.3, "MSFT": 0.3, "GOOG": 0.4},
    context="rebalance"
)
```

**Benefits of using these helpers:**
- Works with both logging systems (controlled by feature flag)
- Consistent structure across all logs
- Automatic calculations (e.g., price improvement for repegs)
- Type-safe with proper Decimal handling
- Easy to migrate - no code changes needed when enabling structlog

## Configuration

### Structlog Setup

```python
from the_alchemiser.shared.logging import configure_structlog

# JSON output (production)
configure_structlog(structured_format=True, log_level=logging.INFO)

# Console output (development)
configure_structlog(structured_format=False, log_level=logging.DEBUG)
```

### Migration Bridge

The migration bridge provides backward compatibility:

```python
from the_alchemiser.shared.logging import (
    setup_application_logging,
    is_structlog_enabled,
)

# Setup delegates to appropriate system
setup_application_logging(
    structured_format=True,
    log_level=logging.INFO
)

# Check which system is active
if is_structlog_enabled():
    print("Using structlog")
else:
    print("Using stdlib logging")
```

## Output Formats

### Stdlib Logging (Default)

```
2025-10-01 15:11:21,149 - INFO - __main__ - Trading event: order_placed for AAPL
```

### Structlog (JSON Format)

```json
{
  "event": "Order placed",
  "symbol": "AAPL",
  "quantity": 100,
  "price": "150.25",
  "system": "alchemiser",
  "timestamp": "2025-10-01T15:11:21.151071Z",
  "level": "info"
}
```

### Structlog (Console Format)

```
2025-10-01T15:11:21.151071Z [info] Order placed symbol=AAPL quantity=100 price=150.25 system=alchemiser
```

## Context Variables

Both systems support context variables via `contextvars`:

```python
from the_alchemiser.shared.logging import set_request_id, set_error_id

set_request_id("req-123")
set_error_id("err-456")

logger.info("Processing request")
# Automatically includes request_id and error_id in output
```

## Decimal Handling

Structlog automatically serializes `Decimal` values correctly:

```python
from decimal import Decimal

logger.info(
    "Trade executed",
    price=Decimal("150.25"),
    quantity=Decimal("100"),
    total=Decimal("15025.00")
)
# All Decimal values are properly serialized in JSON
```

## Testing

Comprehensive tests cover all functionality:

```bash
# Run all logging tests
poetry run pytest tests/shared/logging/ -v

# Run specific test suites
poetry run pytest tests/shared/logging/test_structlog_config.py -v
poetry run pytest tests/shared/logging/test_structlog_trading.py -v
poetry run pytest tests/shared/logging/test_migration_bridge.py -v
```

## Migration Strategy

### Phase 1: Core Infrastructure (✅ COMPLETED)
- ✅ Add structlog dependency
- ✅ Create structlog configuration module
- ✅ Create trading-specific helpers
- ✅ Create migration bridge with feature flag
- ✅ Add comprehensive tests

### Phase 2: Module Migration (🔄 IN PROGRESS)
- ✅ Extended migration bridge with `log_repeg_operation()` and `log_order_flow()` helpers
- ✅ Update execution_v2 repeg logic to use `log_repeg_operation()`
- ✅ Update execution_v2 order execution to use `log_order_flow()`
- [ ] Update execution_v2 validation logging to use `log_data_integrity_checkpoint()`
- [ ] Migrate portfolio_v2 logging
- [ ] Update strategy_v2 logging
- [ ] Convert orchestration logging

### Phase 3: Production Rollout
- [ ] Enable in development environment
- [ ] Gradual production rollout
- [ ] Performance analysis
- [ ] Monitor and optimize

### Phase 4: Cleanup
- [ ] Remove migration bridge
- [ ] Remove stdlib logging code
- [ ] Update documentation
- [ ] Mark migration complete

## Performance Considerations

Structlog is designed for production use and provides:

- **Efficient Processing**: Lazy evaluation of log formatting
- **Better Caching**: Logger instances are cached
- **Optimized JSON**: Native JSON serialization is faster than custom formatters

## Backward Compatibility

All existing logging code continues to work unchanged:

```python
# This works with both systems
from the_alchemiser.shared.logging import get_logger, log_trade_event

logger = get_logger(__name__)
log_trade_event(logger, "order_placed", "AAPL", quantity=100)
```

The migration bridge automatically delegates to the appropriate backend.

## Examples

### Before and After Migration

**Before (stdlib logging):**
```python
logger.info(
    f"✅ Re-peg successful: new order {executed_order.order_id} "
    f"at ${new_price} (attempt {new_repeg_count}/{self.config.max_repegs_per_order}) "
    f"quantity: {remaining_qty}"
)
```

**After (migration bridge with structlog support):**
```python
log_repeg_operation(
    logger,
    operation="replace_order",
    symbol=request.symbol,
    old_price=original_anchor if original_anchor else new_price,
    new_price=new_price,
    quantity=remaining_qty,
    reason="unfilled_order",
    new_order_id=str(executed_order.order_id),
    original_order_id=order_id,
    repeg_attempt=new_repeg_count,
    max_repegs=self.config.max_repegs_per_order,
)
```

**Benefits:**
- ✅ Structured data instead of formatted strings
- ✅ Automatic price improvement calculation
- ✅ Works with both logging systems
- ✅ Easy to query and analyze in log aggregation tools
- ✅ Type-safe with Decimal values

### Real Migration Examples

See the following files for real-world migration examples:
- `the_alchemiser/execution_v2/core/smart_execution_strategy/repeg.py` - Repeg operation logging
- `the_alchemiser/execution_v2/core/executor.py` - Smart order execution logging
- `the_alchemiser/execution_v2/core/market_order_executor.py` - Market order logging

## Additional Resources

- [Structlog Documentation](https://www.structlog.org/)
- [Python Logging Best Practices](https://docs.python.org/3/howto/logging.html)
- [Issue #1434](https://github.com/Josh-moreton/alchemiser-quant/issues/1434) - This migration
