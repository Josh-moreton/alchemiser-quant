# Exception System Documentation

## Executive Summary

**Question 1: Does the codebase have two parallel exception systems?**
**Answer: NO - There is ONE active exception system**

The codebase uses a single, production-ready exception system in `shared/types/exceptions.py`.

**Question 2: Which one should we use?**
**Answer: Use `shared/types/exceptions.py` - the active exception system**

---

## The Exception System

### Location: `shared/types/exceptions.py`

**Status**: ✅ Active and production-ready

**Key Characteristics**:
- Base class: `AlchemiserError(Exception)`
- 25+ specialized exception types covering all use cases
- Production-tested design with context tracking
- Widely integrated across 17 production files

**Exception Hierarchy**:
```
AlchemiserError (base)
├── ConfigurationError
├── DataProviderError
│   ├── MarketDataError
│   │   └── DataUnavailableError
│   ├── WebSocketError
│   └── StreamingError
├── TradingClientError
│   ├── OrderExecutionError
│   │   ├── OrderPlacementError
│   │   ├── OrderTimeoutError
│   │   ├── BuyingPowerError
│   │   └── InsufficientFundsError
│   ├── PositionValidationError
│   └── MarketClosedError
├── PortfolioError
│   └── NegativeCashBalanceError
├── StrategyExecutionError
│   └── StrategyValidationError
├── ValidationError
├── NotificationError
├── S3OperationError
├── RateLimitError
├── IndicatorCalculationError
├── FileOperationError
├── DatabaseError
├── SecurityError
└── LoggingError
```

**Production Usage**: 17 files import from this module
the_alchemiser/execution_v2/core/smart_execution_strategy/repeg.py
the_alchemiser/main.py
the_alchemiser/strategy_v2/handlers/signal_generation_handler.py
the_alchemiser/shared/types/trading_errors.py
the_alchemiser/shared/utils/decorators.py
the_alchemiser/shared/utils/error_reporter.py
the_alchemiser/shared/services/market_data_service.py
the_alchemiser/shared/errors/error_handler.py
the_alchemiser/shared/errors/error_utils.py
the_alchemiser/shared/errors/catalog.py
the_alchemiser/shared/errors/error_details.py
the_alchemiser/orchestration/system.py
the_alchemiser/portfolio_v2/core/planner.py
the_alchemiser/portfolio_v2/core/state_reader.py
the_alchemiser/portfolio_v2/core/portfolio_service.py
the_alchemiser/lambda_handler.py

### Integration with Error Handling Infrastructure

The `shared/errors/` package provides rich error handling support for the exception system:
- `error_handler.py`: Main error handling facade
- `error_details.py`: Error detail tracking
- `error_reporter.py`: Error reporting and notifications
- `error_utils.py`: Retry decorators and circuit breakers
- `catalog.py`: Error code mapping

All these modules work with exceptions from `shared/types/exceptions.py`.

---

## Usage Guidelines

### Importing Exceptions

Always import from `the_alchemiser.shared.errors.exceptions`:

```python
from the_alchemiser.shared.errors.exceptions import (
    AlchemiserError,           # Base exception
    OrderExecutionError,       # Trading errors
    PortfolioError,           # Portfolio errors  
    DataProviderError,        # Data errors
    ConfigurationError,       # Config errors
    ValidationError,          # Validation errors
)
```

### Raising Exceptions

Provide context via constructor parameters for better debugging:

```python
raise OrderExecutionError(
    "Order failed",
    symbol="AAPL",
    order_id="order-123",
    quantity=100.0,
)
```

### Catching Exceptions

Catch specific exception types for targeted error handling:

```python
try:
    # Trading logic
    pass
except OrderExecutionError as e:
    # Handle order-specific errors
    logger.error(f"Order failed: {e.symbol}, {e.order_id}")
except PortfolioError as e:
    # Handle portfolio errors
    logger.error(f"Portfolio error: {e.module}")
except AlchemiserError as e:
    # Catch-all for application errors
    logger.error(f"Application error: {e}")
```

---

## Best Practices

### 1. Use Specific Exception Types

Always use the most specific exception type available:

✅ **Good**:
```python
raise OrderExecutionError("Order timed out", symbol="AAPL")
```

❌ **Bad**:
```python
raise AlchemiserError("Order timed out")  # Too generic
```

### 2. Provide Context

Include relevant context for debugging:

✅ **Good**:
```python
raise PortfolioError(
    "Rebalance failed",
    module="portfolio_v2",
    operation="create_plan",
    correlation_id="abc-123",
)
```

❌ **Bad**:
```python
raise PortfolioError("Rebalance failed")  # Missing context
```

### 3. Use the Error Handling Infrastructure

Leverage the `shared/errors/` package for consistent error handling:

```python
from the_alchemiser.shared.errors import (
    TradingSystemErrorHandler,
    handle_trading_error,
)

# Use the error handler
error_handler = TradingSystemErrorHandler()
try:
    # Trading logic
    pass
except OrderExecutionError as e:
    error_handler.handle_error(
        error=e,
        context="order_execution",
        component="execution_v2",
    )
```

---

## Exception Reference

### Trading Exceptions

- `OrderExecutionError` - Order placement or execution failures
- `OrderPlacementError` - Order placement with None ID
- `OrderTimeoutError` - Order execution timeouts
- `BuyingPowerError` - Insufficient buying power
- `InsufficientFundsError` - Insufficient funds
- `PositionValidationError` - Position validation failures
- `MarketClosedError` - Trading while markets closed

### Portfolio Exceptions

- `PortfolioError` - Portfolio operation failures
- `NegativeCashBalanceError` - Negative or zero cash balance

### Data Exceptions

- `DataProviderError` - Data provider operation failures
- `MarketDataError` - Market data retrieval failures
- `DataUnavailableError` - Historical data unavailable
- `SpreadAnalysisError` - Spread analysis failures
- `WebSocketError` - WebSocket connection issues
- `StreamingError` - Streaming data issues

### Configuration Exceptions

- `ConfigurationError` - Configuration issues
- `EnvironmentError` - Environment setup issues

### Strategy Exceptions

- `StrategyExecutionError` - Strategy execution failures
- `StrategyValidationError` - Strategy validation failures
- `IndicatorCalculationError` - Technical indicator calculation failures

### System Exceptions

- `ValidationError` - Data validation failures
- `NotificationError` - Notification sending failures
- `S3OperationError` - S3 operation failures
- `RateLimitError` - API rate limit exceeded
- `FileOperationError` - File operation failures
- `DatabaseError` - Database operation failures
- `SecurityError` - Security-related issues
- `LoggingError` - Logging infrastructure failures

---

## Conclusion

The codebase uses a single, well-designed exception system in `shared/types/exceptions.py`:

- ✅ Production-ready with 17 active imports
- ✅ Complete hierarchy with 25+ exception types
- ✅ Context tracking and structured logging support
- ✅ Integrated with error handling infrastructure

**For developers**: Always import from `the_alchemiser.shared.errors.exceptions` and use the most specific exception type available.
