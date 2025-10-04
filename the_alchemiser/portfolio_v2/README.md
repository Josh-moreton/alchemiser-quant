# Portfolio_v2 Module

**Business Unit: portfolio | Status: current**

## Overview

Portfolio_v2 is a minimal, DTO-first module that replaces the legacy portfolio module with clean separation of concerns and deterministic rebalancing logic.

## Architecture

```
portfolio_v2/
├── __init__.py                           # Public API exports
├── core/
│   ├── portfolio_service.py             # Main orchestration facade
│   ├── planner.py                       # Core rebalance plan calculator
│   └── state_reader.py                 # Portfolio snapshot builder
├── adapters/
│   └── alpaca_data_adapter.py          # Data access via shared AlpacaManager
└── models/
    ├── portfolio_snapshot.py           # Immutable portfolio state
    └── sizing_policy.py                # Trade sizing and rounding rules
```

## Core Design Principle

- **Inputs**: StrategyAllocationDTO (weights and constraints) + current snapshot (positions, prices, cash)
- **Output**: RebalancePlanDTO containing BUY/SELL/HOLD items and trade_amounts (Decimal)
- **No side effects**: no cross-module state; single pass O(n) over symbols

## Responsibilities

### Portfolio_v2 SHOULD
- Read current positions/prices/cash via shared Alpaca
- Compute target dollars per symbol from target weights
- Produce trade_amount = target_dollars - current_dollars
- Apply sizing/threshold policy and set action BUY/SELL/HOLD
- Emit RebalancePlanDTO only

### Portfolio_v2 SHOULD NOT
- Place or schedule orders, or suggest execution styles
- Recompute strategy logic; only translate weights → plan
- Import from strategy/ or execution/ modules
- Maintain mutable global state or caches shared across modules

## Usage

```python
from the_alchemiser.portfolio_v2 import PortfolioServiceV2
from the_alchemiser.shared.schemas.strategy_allocation import StrategyAllocationDTO
from the_alchemiser.shared.brokers.alpaca_manager import AlpacaManager
from decimal import Decimal

# Initialize service
alpaca_manager = AlpacaManager(api_key="...", secret_key="...", paper=True)
portfolio_service = PortfolioServiceV2(alpaca_manager)

# Create strategy allocation
strategy = StrategyAllocationDTO(
    target_weights={"SPY": Decimal("0.6"), "QQQ": Decimal("0.4")},
    portfolio_value=None,  # Use current portfolio value
    correlation_id="strategy-123",
)

# Generate rebalance plan
plan = portfolio_service.create_rebalance_plan_dto(strategy, "rebalance-456")

# Plan contains trade items ready for execution module
for item in plan.items:
    print(f"{item.symbol}: {item.action} ${item.trade_amount}")
```

## Key Features

### Deterministic Calculations
- Same inputs always produce same plan
- All financial calculations use Decimal precision
- Single-pass O(n) algorithm over symbols

### Clean Module Boundaries
- Only imports from shared/ module
- No dependencies on strategy/ or execution/
- Communication via typed DTOs

### Flexible Sizing Policies
- Configurable minimum trade amounts
- Support for different rounding modes
- Threshold-based BUY/SELL/HOLD decisions

### Comprehensive Error Handling
- Typed PortfolioError exceptions with context
- Structured logging with correlation IDs
- Fail-fast on missing prices or invalid data

## Validation

Run the manual validation script to verify functionality:

```bash
poetry run python scripts/validate_portfolio_v2.py
```

## Migration from Legacy Portfolio

Portfolio_v2 is designed to replace the legacy portfolio module. Key differences:

1. **DTO-first**: Consumes StrategyAllocationDTO instead of mixed parameters
2. **No execution hints**: Pure rebalancing logic, no order placement concerns
3. **Immutable snapshots**: State captured once per cycle, not mutated
4. **Decimal precision**: All financial calculations use Decimal
5. **Clean boundaries**: No cross-module imports or state sharing

## Performance

- **O(n) complexity**: Single pass over symbols
- **Batch price fetching**: Minimal API calls to data providers
- **No caching**: Recompute from fresh data each cycle
- **Memory efficient**: Immutable data structures, no state accumulation

## Error Handling

All errors are wrapped in typed exceptions with contextual information:

```python
try:
    plan = portfolio_service.create_rebalance_plan_dto(strategy, correlation_id)
except PortfolioError as e:
    print(f"Portfolio operation failed: {e.message}")
    print(f"Context: {e.context}")
```

## Logging

All operations include structured logging with correlation IDs:

```
2024-01-01 10:00:00 - INFO - Building rebalance plan [correlation_id=abc123] [module=portfolio_v2.core.planner]
```

## Strategy Attribution Metadata

When creating rebalance plans, you can include strategy attribution metadata to track which strategies contributed to each order. This metadata is consumed by the execution module's trade ledger for recording filled orders.

### Single Strategy

For a single strategy, no special metadata is needed:

```python
strategy = StrategyAllocation(
    target_weights={"AAPL": Decimal("0.5"), "TSLA": Decimal("0.5")},
    correlation_id="corr-123",
)
plan = portfolio_service.create_rebalance_plan(strategy, "corr-123")
```

### Multi-Strategy Aggregation

When multiple strategies suggest the same symbols and you aggregate their weights, include strategy attribution in the rebalance plan metadata:

```python
# Example: Aggregate signals from two strategies
# Strategy 1 wants 30% AAPL, Strategy 2 wants 20% AAPL
# Combined target: 50% AAPL (30% from strategy1, 20% from strategy2)

# Create the allocation
strategy = StrategyAllocation(
    target_weights={"AAPL": Decimal("0.5")},
    correlation_id="corr-123",
)

# Build the rebalance plan
plan = portfolio_service.create_rebalance_plan(strategy, "corr-123")

# Add strategy attribution to plan metadata
plan.metadata = {
    "strategy_attribution": {
        "AAPL": {
            "momentum_strategy": 0.6,  # 30/50 = 60% contribution
            "mean_reversion_strategy": 0.4,  # 20/50 = 40% contribution
        }
    }
}
```

The execution module will use this metadata to record which strategies contributed to each filled order in the trade ledger.
