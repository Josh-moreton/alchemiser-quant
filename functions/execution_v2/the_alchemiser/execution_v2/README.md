# Execution_v2 Module

**Business Unit: execution | Status: current**

## Overview

The Execution_v2 module provides a unified order placement system for trade execution. It uses the **Unified Order Placement Service** as the single entry point for all order execution, with streaming-first quote acquisition and walk-the-book price improvement.

## Core Responsibilities

- **Unified Order Placement**: Single entry point for ALL order execution via `UnifiedOrderPlacementService`
- **Walk-the-Book Execution**: Progressive price improvement (75% → 85% → 95% → market)
- **Streaming-First Quotes**: WebSocket quotes with REST fallback
- **Portfolio Validation**: Verify position changes after execution
- **Trade Monitoring**: Track order status and settlement
- **Execution Results**: Report execution outcomes with detailed audit trail

## Architecture

```
execution_v2/
├── __init__.py                    # Public API and handler registration
├── handlers/                      # Event-driven handlers
│   └── trading_execution_handler.py
├── core/                          # Core execution logic
│   ├── executor.py               # Core execution orchestrator (uses unified service)
│   ├── execution_manager.py      # Main facade
│   ├── market_order_executor.py  # Fallback market order execution
│   ├── phase_executor.py         # Multi-phase execution coordinator
│   ├── order_monitor.py          # Order status tracking
│   ├── settlement_monitor.py     # Settlement verification
│   ├── order_finalizer.py        # Order completion logic
│   └── smart_execution_strategy/ # Configuration models (strategy removed)
│       └── models.py             # ExecutionConfig, SmartOrderRequest, etc.
├── unified/                       # NEW: Unified order placement system
│   ├── order_intent.py           # Type-safe order intent abstraction
│   ├── quote_service.py          # Unified quote acquisition
│   ├── walk_the_book.py          # Walk-the-book execution strategy
│   ├── portfolio_validator.py    # Post-execution validation
│   └── placement_service.py      # Single entry point for all orders
├── services/                      # Business services
│   └── trade_ledger.py           # Trade recording service
├── models/                        # Data models
│   └── execution_result.py       # Execution result DTO
└── utils/                         # Utilities
    ├── execution_validator.py    # Pre-execution validation
    ├── liquidity_analysis.py     # Liquidity assessment
    └── position_utils.py         # Position helpers
```

## Unified Order Placement (Primary Execution Path)

All order execution now flows through the **Unified Order Placement Service**:

```python
from the_alchemiser.execution_v2.unified import (
    UnifiedOrderPlacementService,
    OrderIntent,
    OrderSide,
    CloseType,
    Urgency,
)

# Initialize service
service = UnifiedOrderPlacementService(
    alpaca_manager=alpaca_manager,
    pricing_service=pricing_service,
    enable_validation=True,
)

# Create order intent
intent = OrderIntent(
    side=OrderSide.BUY,
    close_type=CloseType.NONE,
    symbol="AAPL",
    quantity=Decimal("10"),
    urgency=Urgency.MEDIUM,
    correlation_id="trade-123",
)

# Place order
result = await service.place_order(intent)
```

### Order Intent Types

| Side | CloseType | Description |
|------|-----------|-------------|
| `BUY` | `NONE` | Buy shares (open or add to position) |
| `SELL` | `PARTIAL` | Reduce position size |
| `SELL` | `FULL` | Fully close position |

### Urgency Levels

| Urgency | Behavior |
|---------|----------|
| `HIGH` | Market order immediately |
| `MEDIUM` | Walk-the-book (default) |
| `LOW` | Walk-the-book with longer waits |

### Walk-the-Book Strategy

The unified service uses progressive price improvement:

```
Step 1: Limit order @ 75% toward aggressive side → Wait 30s
Step 2: Replace @ 85% toward aggressive side → Wait 30s
Step 3: Replace @ 95% toward aggressive side → Wait 30s
Step 4: Market order (if still not filled)
```

**For BUY orders**: "Aggressive side" = toward the ask price
**For SELL orders**: "Aggressive side" = toward the bid price

### Quote Acquisition

The unified quote service handles Alpaca's 0 bid/ask issue:

| Condition | Action |
|-----------|--------|
| `bid > 0` and `ask > 0` | Use actual bid/ask |
| `bid = 0` and `ask > 0` | Use `ask` for both sides |
| `bid > 0` and `ask = 0` | Use `bid` for both sides |
| `bid = 0` and `ask = 0` | Quote unusable (try REST fallback) |

### Portfolio Validation

After execution, the service validates that position changes match expectations:

```python
result = await service.place_order(intent)

# Validation result included
print(result.validation_result.describe())
# "Position change validated: expected +10 AAPL, actual +10 AAPL"
```

## Execution Flow

```
User Code
    ↓
Executor.execute_order(symbol, side, quantity)
    ↓
UnifiedOrderPlacementService.place_order(intent)  [async]
    ↓
    ├─→ Preflight Validation (quantity, asset info)
    ├─→ Pre-execution Validation (get current position)
    ├─→ await UnifiedQuoteService.get_best_quote()  [async]
    │       ├─→ Try streaming (WebSocket) with async wait
    │       ├─→ Handle 0 bids/asks
    │       └─→ Fallback to REST API
    ↓
    ├─→ Route by Urgency:
    │       ├─→ HIGH: Market order immediately
    │       └─→ MEDIUM/LOW: WalkTheBookStrategy
    │               ├─→ Step 1: Limit @ 75%
    │               ├─→ Step 2: Limit @ 85%
    │               ├─→ Step 3: Limit @ 95%
    │               └─→ Step 4: Market order
    ↓
    ├─→ PortfolioValidator.validate_execution()
    ↓
    └─→ Return ExecutionResult
```

## Usage

### Event-Driven (Preferred)

The execution module integrates with the project's event bus to respond to
`RebalancePlanned` events and execute rebalance plans. Handlers and services
are registered via the application container at startup.

### Direct Access

```python
from the_alchemiser.execution_v2 import ExecutionManager
from the_alchemiser.shared.brokers.alpaca_manager import AlpacaManager
from the_alchemiser.shared.schemas.rebalance_plan import RebalancePlan

# Initialize manager
alpaca_manager = AlpacaManager(api_key="...", secret_key="...", paper=True)
execution_manager = ExecutionManager(alpaca_manager)

# Execute rebalance plan
plan = RebalancePlan(
    items=[...],
    correlation_id="exec-123",
    plan_id="plan-456"
)

result = await execution_manager.execute_rebalance_plan(plan)
```

## Configuration

### Execution Configuration

```python
from the_alchemiser.execution_v2.core.smart_execution_strategy import ExecutionConfig

config = ExecutionConfig(
    max_spread_percent=Decimal("0.50"),       # Max acceptable spread (0.50%)
    repeg_threshold_percent=Decimal("0.10"),  # Re-peg if market moves >0.1%
    max_repegs_per_order=2,                   # Maximum re-pegs before escalation
    fill_wait_seconds=10,                     # Wait time before re-peg
    quote_freshness_seconds=5,                # Require quote within 5 seconds
)

execution_manager = ExecutionManager(alpaca_manager, execution_config=config)
```

### Walk-the-Book Configuration

```python
from the_alchemiser.execution_v2.unified import WalkTheBookStrategy

strategy = WalkTheBookStrategy(
    alpaca_manager=alpaca_manager,
    step_wait_seconds=20,                    # Wait 20s at each step (default: 30s)
    price_steps=[0.70, 0.80, 0.90, 0.95],   # Custom progression
)
```

## Error Handling

```python
from the_alchemiser.shared.errors import (
    OrderExecutionError,
    InsufficientFundsError,
    PositionValidationError
)

try:
    result = await execution_manager.execute_rebalance_plan(plan)
except OrderExecutionError as e:
    logger.error(f"Order execution failed: {e}", extra=e.context)
except InsufficientFundsError as e:
    logger.error(f"Insufficient buying power: {e}", extra=e.context)
except PositionValidationError as e:
    logger.error(f"Position validation failed: {e}", extra=e.context)
```

## Metrics and Observability

### Quote Metrics
- `streaming_success_count`: Quotes obtained from WebSocket
- `rest_fallback_count`: Quotes obtained from REST API
- `zero_bid_count`: Quotes with 0 bid (substituted)
- `zero_ask_count`: Quotes with 0 ask (substituted)
- `both_zero_count`: Quotes with both 0 (unusable)

### Execution Metrics
- Execution time per order
- Steps used in walk-the-book
- Fill rates at each price level
- Validation success/failure rates

## Testing

```bash
# Run execution module tests
poetry run pytest tests/execution_v2/ -v

# Test with coverage
poetry run pytest tests/execution_v2/ --cov=the_alchemiser.execution_v2

# Type checking
make type-check
```

## Trade Ledger

Trade entries are automatically recorded with:
- Order details (ID, symbol, direction, quantity, price)
- Market data (bid/ask spreads at fill time)
- Strategy attribution (which strategies contributed)
- Timing information

Persisted to DynamoDB: `alchemiser-{stage}-trade-ledger`

## Module Boundaries

- **Imports from**: `shared/` only (brokers, events, schemas, logging, errors)
- **No imports from**: `strategy_v2/`, `portfolio_v2/`, `orchestration/`
- **Communication**: Event-driven only; no direct cross-module calls

## See Also

- [Unified Order Placement Service](./unified/README.md) - Detailed documentation
- [Order Handling Guide](./unified/ORDER_HANDLING_GUIDE.md) - How to handle each order type
