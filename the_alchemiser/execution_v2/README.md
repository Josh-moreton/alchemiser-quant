# Execution_v2 Module

**Business Unit: execution | Status: current**

## Overview

The Execution_v2 module provides a clean, minimal execution system for order placement and trade execution. It consumes `RebalancePlanDTO` from the portfolio module and executes trades via the shared Alpaca broker interface, maintaining strict separation of concerns and clean module boundaries.

## Core Responsibilities

- **Order Execution**: Place market and limit orders via Alpaca API
- **Smart Execution**: Adaptive limit order placement with repricing strategies
- **Trade Monitoring**: Track order status and settlement
- **Execution Results**: Report execution outcomes with detailed metadata
- **Boundary Enforcement**: No portfolio calculation or strategy logic

## Architecture

```
execution_v2/
├── __init__.py                    # Public API and handler registration
├── handlers/                      # Event-driven handlers
│   └── trading_execution_handler.py
├── core/                          # Core execution logic
│   ├── execution_manager.py      # Main facade (legacy)
│   ├── executor.py               # Core execution orchestrator
│   ├── market_order_executor.py  # Market order execution
│   ├── phase_executor.py         # Multi-phase execution coordinator
│   ├── order_monitor.py          # Order status tracking
│   ├── settlement_monitor.py     # Settlement verification
│   ├── order_finalizer.py        # Order completion logic
│   └── smart_execution_strategy/ # Smart limit order execution
│       ├── strategy.py           # Main strategy orchestrator
│       ├── pricing.py            # Price calculation and bounds
│       ├── repeg.py              # Repricing logic
│       ├── quotes.py             # Quote data access
│       └── tracking.py           # Order tracking
├── services/                      # Business services
│   └── trade_ledger.py           # Trade recording service
├── models/                        # Data models
│   └── execution_result.py       # Execution result DTO
├── utils/                         # Utilities
│   ├── execution_validator.py    # Pre-execution validation
│   ├── liquidity_analysis.py     # Liquidity assessment
│   └── position_utils.py         # Position helpers
└── config/                        # Configuration
    └── execution_config.py       # Smart execution settings
```

## Core Design Principles

### Inputs
- **RebalancePlanDTO**: Plan from portfolio_v2 with trade items (symbol, action, trade_amount)
- **ExecutionConfig**: Optional configuration for smart execution strategies
- Correlation IDs for tracking and observability

### Outputs
- **TradeExecuted** events: Emitted per order with execution details
- **WorkflowCompleted/Failed** events: Final workflow status
- **ExecutionResult**: DTO containing order outcomes and summary (legacy API)

### Constraints
- **Dependencies**: execution_v2 → shared only (brokers, events, schemas)
- **No imports** from strategy/ or portfolio/ modules
- **Stateless handlers**: No shared mutable state
- **Idempotent**: Can safely replay events

## Usage

### Event-Driven (Preferred)

The execution module integrates with the event-driven architecture through handler registration:

```python
from the_alchemiser.execution_v2 import register_execution_handlers
from the_alchemiser.shared.config.container import ApplicationContainer

# Register handlers with the event bus
container = ApplicationContainer()
register_execution_handlers(container)

# Handlers automatically respond to:
# - RebalancePlanned: Execute the rebalance plan
```

The handler consumes `RebalancePlanned` events and:
1. Validates the rebalance plan
2. Executes trades via Alpaca
3. Emits `TradeExecuted` events for each order
4. Emits `WorkflowCompleted` or `WorkflowFailed` when done

### Direct Access (Legacy - Being Phased Out)

For migration and testing purposes only:

```python
from the_alchemiser.execution_v2 import ExecutionManager
from the_alchemiser.shared.brokers.alpaca_manager import AlpacaManager
from the_alchemiser.shared.schemas.rebalance_plan import RebalancePlan
from decimal import Decimal

# Initialize manager
alpaca_manager = AlpacaManager(api_key="...", secret_key="...", paper=True)
execution_manager = ExecutionManager(alpaca_manager)

# Execute rebalance plan
plan = RebalancePlan(
    items=[...],  # Trade items from portfolio
    correlation_id="exec-123",
    plan_id="plan-456"
)

result = execution_manager.execute_rebalance_plan(plan)

# Check results
print(f"Status: {result.status}")
print(f"Orders placed: {len(result.orders_placed)}")
print(f"Orders filled: {len(result.orders_filled)}")
```

## Smart Execution Strategy

Execution_v2 includes an adaptive smart execution system for limit orders:

### Features
- **Adaptive pricing**: Start near mid-price, widen to bid/ask
- **Dynamic repricing**: Adjust prices if not filled
- **Liquidity analysis**: Assess market depth before execution
- **Multiple phases**: BUY first, SELL after settlement
- **Settlement monitoring**: Verify trades settle before continuing

### Configuration

```python
from the_alchemiser.execution_v2.core.smart_execution_strategy import ExecutionConfig

config = ExecutionConfig(
    max_repeg_attempts=3,           # Max repricing attempts
    repeg_interval_seconds=30,       # Seconds between repeg attempts
    initial_aggressiveness=0.3,      # Start 30% toward bid/ask
    final_aggressiveness=0.9,        # End 90% toward bid/ask
    min_liquidity_ratio=0.05,        # Minimum 5% of avg volume
)

execution_manager = ExecutionManager(alpaca_manager, execution_config=config)
```

### Execution Flow

1. **Validation**: Check positions, buying power, market hours
2. **Phase 1 (BUY)**: Place and monitor BUY orders
3. **Settlement**: Wait for BUY orders to settle
4. **Phase 2 (SELL)**: Place and monitor SELL orders
5. **Finalization**: Report results via events

## Integration Points

### Dependencies
- **shared/brokers**: AlpacaManager for order placement and data access
- **shared/events**: EventBus for event-driven communication
- **shared/schemas**: RebalancePlan, trade item DTOs

### Inputs
- Consumes `RebalancePlanned` events from portfolio_v2
- Events contain complete rebalance plan with all trade details

### Outputs
- Publishes `TradeExecuted` events (one per order)
- Publishes `WorkflowCompleted` or `WorkflowFailed` at end
- Events consumed by orchestration for monitoring

### Module Boundaries
- **Imports from**: `shared/` only (brokers, events, schemas, logging, errors)
- **No imports from**: `strategy_v2/`, `portfolio_v2/`, `orchestration/`
- **Communication**: Event-driven only; no direct cross-module calls

## Error Handling

Execution_v2 uses typed exceptions with contextual information:

```python
from the_alchemiser.shared.errors import (
    OrderExecutionError,
    InsufficientFundsError,
    PositionValidationError
)

try:
    result = execution_manager.execute_rebalance_plan(plan)
except OrderExecutionError as e:
    logger.error(f"Order execution failed: {e}", extra=e.context)
    # Handle order failure (retry, alert, etc.)
except InsufficientFundsError as e:
    logger.error(f"Insufficient buying power: {e}", extra=e.context)
    # Handle insufficient funds
except PositionValidationError as e:
    logger.error(f"Position validation failed: {e}", extra=e.context)
    # Handle position mismatch
```

### Error Categories
- **OrderExecutionError**: Order placement or fill failures
- **InsufficientFundsError**: Not enough buying power
- **PositionValidationError**: Position data inconsistencies
- **ValidationError**: Pre-execution validation failures

All errors include:
- `module="execution_v2.*"` metadata
- Correlation IDs for end-to-end tracking
- Contextual details (symbol, quantity, order type, etc.)

## Performance

### Execution Characteristics
- **Async I/O**: Non-blocking order placement and monitoring
- **Batched operations**: Group orders by phase (BUY/SELL)
- **Streaming data**: WebSocket for real-time order updates
- **Settlement monitoring**: Efficient polling with backoff

### Timing Considerations
- **Market orders**: Typically fill within seconds
- **Limit orders**: May take 30-90 seconds with repricing
- **Settlement**: T+1 for equities (orders settle next business day)
- **Total workflow**: 2-5 minutes typical for full rebalance

### Resource Usage
- **Memory**: O(n) where n = number of orders
- **Network**: WebSocket connection + REST API calls
- **CPU**: Minimal (mostly I/O bound)

## Logging

All execution operations include structured logging:

```json
{
  "timestamp": "2024-01-01T10:00:00Z",
  "level": "INFO",
  "message": "🚀 NEW EXECUTION: 5 items (using execution_v2)",
  "correlation_id": "exec-123",
  "plan_id": "plan-456",
  "module": "execution_v2.core.execution_manager"
}
```

Key log points:
- Execution start/completion
- Order placement (per symbol)
- Order fills and rejections
- Repricing attempts
- Settlement verification
- Error conditions

## Testing and Validation

### Unit Tests
```bash
# Run execution module tests
poetry run pytest tests/execution_v2/ -v

# Test with coverage
poetry run pytest tests/execution_v2/ --cov=the_alchemiser.execution_v2
```

### Integration Testing
```bash
# Validate with paper trading
poetry run python scripts/validate_execution_v2.py
```

### Manual Testing
```python
# Test with small position
from the_alchemiser.execution_v2 import ExecutionManager
from the_alchemiser.shared.schemas.rebalance_plan import RebalancePlan, TradeItem
from decimal import Decimal

alpaca = AlpacaManager(paper=True)
manager = ExecutionManager(alpaca)

plan = RebalancePlan(
    items=[
        TradeItem(
            symbol="SPY",
            action="BUY",
            trade_amount=Decimal("100.00"),
            current_position=Decimal("0")
        )
    ],
    correlation_id="test-123"
)

result = manager.execute_rebalance_plan(plan)
print(f"Execution completed: {result.status}")
```

### Type Checking
```bash
# Verify type correctness
make type-check
```

## Migration Status

Execution_v2 is fully operational and is the current execution implementation.

### Completed
- ✅ Event-driven architecture integration
- ✅ Smart execution strategy with repricing
- ✅ Settlement monitoring and verification
- ✅ Comprehensive error handling
- ✅ Liquidity analysis
- ✅ Position validation
- ✅ Trade ledger for order tracking with strategy attribution

### Future Enhancements
- ⏳ Support for additional order types (stop-loss, trailing stop)
- ⏳ Advanced execution algorithms (VWAP, TWAP)

## Trade Ledger

The execution module includes a trade ledger service that records all filled orders with comprehensive details:

### Recorded Information
- **Order Details**: Order ID, symbol, direction (BUY/SELL), quantity, fill price
- **Market Data**: Bid/ask spreads at fill time (when available)
- **Timing**: Timestamp of fill
- **Order Type**: MARKET, LIMIT, etc.
- **Strategy Attribution**: Which strategies contributed to the order

### Strategy Attribution

The trade ledger supports multi-strategy attribution where multiple strategies suggest the same symbol. Strategy attribution is stored in the rebalance plan metadata:

```python
# Example: Two strategies both suggest AAPL
plan = RebalancePlan(
    # ... other fields ...
    metadata={
        "strategy_attribution": {
            "AAPL": {
                "momentum_strategy": 0.6,  # 60% weight
                "mean_reversion_strategy": 0.4,  # 40% weight
            }
        }
    }
)
```

### Usage

The trade ledger is automatically populated during execution:

```python
executor = Executor(alpaca_manager, execution_config)

# Execute rebalance plan (ledger recording happens automatically)
result = await executor.execute_rebalance_plan(plan)

# Access the ledger
ledger = executor.trade_ledger.get_ledger()
print(f"Total trades: {ledger.total_entries}")
print(f"Total buy value: ${ledger.total_buy_value}")
print(f"Total sell value: ${ledger.total_sell_value}")

# Filter by symbol
aapl_trades = executor.trade_ledger.get_entries_for_symbol("AAPL")

# Filter by strategy
strategy_trades = executor.trade_ledger.get_entries_for_strategy("momentum_strategy")
```

### Missing Data Handling

The trade ledger is designed to handle cases where data may not be fully available:
- Missing bid/ask data: Fields set to `None`
- Missing order type: Defaults to "MARKET"
- Missing strategy attribution: Empty lists/None
- Failed orders: Not recorded (only successful fills are tracked)
- ⏳ Multi-venue execution support
- ⏳ Execution cost analysis and reporting
