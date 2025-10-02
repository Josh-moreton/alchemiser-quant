# Structlog Integration for Alchemiser

This document describes the structlog-based structured logging system for the Alchemiser trading platform.

## Overview

The logging system uses [structlog](https://www.structlog.org/) for all structured logging throughout the platform. Structlog provides automatic serialization of complex types including Decimal for financial data, built-in context propagation, and better performance than custom formatters.

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

## Usage

### Basic Logging

```python
from the_alchemiser.shared.logging import get_logger

logger = get_logger(__name__)
logger.info("Order placed", symbol="AAPL", quantity=100, price=Decimal("150.25"))
```

### Trading-Specific Helpers

These helpers work throughout the codebase:

```python
from the_alchemiser.shared.logging import (
    get_logger,
    log_order_flow,
    log_repeg_operation,
    log_data_integrity_checkpoint,
)

logger = get_logger(__name__)

# Log order flow events
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
- Consistent structure across all logs
- Automatic calculations (e.g., price improvement for repegs)
- Type-safe with proper Decimal handling

### Context Binding

```python
from the_alchemiser.shared.logging import (
    get_logger,
    bind_trading_context,
)

logger = get_logger(__name__)

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

## Configuration

### Structlog Setup

```python
from the_alchemiser.shared.logging import configure_structlog
import logging

# JSON output (production)
configure_structlog(structured_format=True, console_level=logging.INFO, file_level=logging.INFO)

# Console output (development)
configure_structlog(structured_format=False, console_level=logging.DEBUG, file_level=logging.DEBUG)
```

### Application Logging

```python
from the_alchemiser.shared.logging import configure_application_logging

# Automatically selects format based on environment
# Production (Lambda): JSON format
# Development: Console format
configure_application_logging()
```

## Output Formats

### JSON Format (Production)

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

### Console Format (Development)

```
2025-10-01T15:11:21.151071Z [info] Order placed symbol=AAPL quantity=100 price=150.25 system=alchemiser
```

## Context Variables

Structlog integrates with Python's contextvars:

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
```

## Examples

### Before and After Migration

**Before (manual string formatting):**
```python
logger.info(
    f"✅ Re-peg successful: new order {executed_order.order_id} "
    f"at ${new_price} (attempt {new_repeg_count}/{self.config.max_repegs_per_order}) "
    f"quantity: {remaining_qty}"
)
```

**After (structured logging):**
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

**Advantages:**
- ✅ Structured data instead of formatted strings
- ✅ Automatic price improvement calculation
- ✅ Easy to query and analyze in log aggregation tools
- ✅ Type-safe with Decimal values

### Real Examples

See the following files for real-world usage:
- `the_alchemiser/execution_v2/core/smart_execution_strategy/repeg.py` - Repeg operation logging
- `the_alchemiser/execution_v2/core/executor.py` - Smart order execution logging
- `the_alchemiser/execution_v2/core/market_order_executor.py` - Market order logging

## Performance Considerations

Structlog is designed for production use and provides:

- **Efficient Processing**: Lazy evaluation of log formatting
- **Better Caching**: Logger instances are cached
- **Optimized JSON**: Native JSON serialization is faster than custom formatters

## Additional Resources

- [Structlog Documentation](https://www.structlog.org/)
- [Python Logging Best Practices](https://docs.python.org/3/howto/logging.html)
- [Issue #1442](https://github.com/Josh-moreton/alchemiser-quant/issues/1442) - Migration tracking
