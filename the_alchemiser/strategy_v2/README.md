# Strategy_v2 Module

**Business Unit: strategy | Status: current**

## Overview

The Strategy_v2 module provides a clean, boundary-enforcing strategy system for signal generation. It maintains strict separation of concerns by consuming market data via shared adapters and outputting pure strategy allocation DTOs.

## Core Responsibilities

- **Signal Generation**: Transform market data into trading signals
- **Indicator Calculation**: Compute technical indicators and features
- **Strategy Orchestration**: Coordinate strategy execution workflow
- **Boundary Enforcement**: No portfolio sizing or execution concerns

## Architecture

```
strategy_v2/
├── core/           # Orchestration and registry
├── engines/        # Strategy implementations (Nuclear, KLM, TECL)
├── indicators/     # Technical indicators and calculations
├── adapters/       # Market data adapters
├── models/         # Context and data models
└── README.md       # This file
```

## Design Principles

### Inputs
- Market data (prices/bars/features) via shared Alpaca capabilities
- StrategyContext containing symbols, timeframe, and parameters

### Outputs
- StrategyAllocationDTO with target weights and metadata
- Correlation IDs for tracking and observability

### Constraints
- Dependencies: strategy_v2 → shared only
- No imports from portfolio/ or execution/ modules
- Deterministic: same inputs → same signals
- No side effects: no order placement or position fetching

## Usage

### Event-Driven (Preferred)

The strategy module integrates with the event-driven architecture via the project's
event bus and handler entrypoints; handlers respond to workflow events such as
`StartupEvent` and `WorkflowStarted`. Strategies emit `SignalGenerated` events
containing `StrategyAllocationDTO` with target weights, correlation IDs, and metadata.

### Direct Access (Legacy - Being Phased Out)

For migration and testing purposes only:

```python
from the_alchemiser.strategy_v2.core.orchestrator import SingleStrategyOrchestrator
from the_alchemiser.strategy_v2.models.context import StrategyContext
from datetime import datetime, timezone

# Create strategy context
context = StrategyContext(
    symbols=["SPY", "QQQ"],
    timeframe="1D",
    as_of=datetime.now(timezone.utc)
)

# Run strategy directly
orchestrator = SingleStrategyOrchestrator()
allocation = orchestrator.run("nuclear", context)

print(f"Target weights: {allocation.target_weights}")
```

## Migration Status

- ✅ **Phase 1**: Contracts and scaffolding (current)
- ⏳ **Phase 2**: Market data adapters
- ⏳ **Phase 3**: Git move engines and indicators
- ⏳ **Phase 4**: Orchestrator and mapping
- ⏳ **Phase 5**: Integration and migration
- ⏳ **Phase 6**: Validation
- ⏳ **Phase 7**: Hardening

## File Movement Plan

Strategy engines and indicators will be moved verbatim from the legacy strategy module using `git mv` to preserve history:

- `strategy/engines/nuclear/` → `strategy_v2/engines/nuclear/`
- `strategy/engines/klm/` → `strategy_v2/engines/klm/`
- `strategy/engines/tecl/` → `strategy_v2/engines/tecl/`
- `strategy/indicators/` → `strategy_v2/indicators/`

## Integration Points

### Dependencies
- **shared/brokers**: AlpacaManager for market data access
- **shared/events**: EventBus for event-driven communication
- **shared/schemas**: StrategyAllocationDTO and related DTOs

### Outputs
- Publishes `SignalGenerated` events to the event bus
- Events consumed by portfolio_v2 for rebalance planning

### Module Boundaries
- **Imports from**: `shared/` only (brokers, events, schemas, logging, errors)
- **No imports from**: `portfolio_v2/`, `execution_v2/`, `orchestration/`
- **Communication**: Event-driven only; no direct cross-module calls

## Error Handling

Strategy_v2 uses typed exceptions with module context:

```python
from the_alchemiser.shared.errors import StrategyError, ConfigurationError

try:
    allocation = orchestrator.run("nuclear", context)
except StrategyError as e:
    logger.error(f"Strategy execution failed: {e}", extra=e.context)
except ConfigurationError as e:
    logger.error(f"Invalid configuration: {e}", extra=e.context)
```

All errors include:
- `module="strategy_v2.*"` metadata for filtering
- Correlation IDs for tracking across workflow
- Contextual information (strategy name, symbols, timeframe)

## Performance

- **O(n * lookback)** complexity with batched data fetching
- **Zero I/O** inside inner loops (data fetched once at start)
- **Deterministic**: Same inputs → same signals
- **Correlation ID** propagation for end-to-end observability
- **Batched API calls**: Minimize Alpaca API requests
- **Live bar caching**: Today's bar fetched once per symbol, cached for Lambda duration

## Market Data: Live Bar Injection

The strategy module supports **live bar injection** to ensure indicators use the most
recent price data when trading at end-of-day (3:30 PM ET).

### How It Works

1. **Historical bars** (through yesterday) are read from S3 Parquet cache (nightly refresh)
2. **Today's bar** is fetched from Alpaca Snapshot API with current OHLCV
3. **Combined series** is passed to indicators (e.g., 199 historical + 1 live = 200 bars)

Live bar injection is enabled by default in `CachedMarketDataAdapter`.

### Data Flow

```
S3 Parquet (historical)  +  Alpaca Snapshot API (today)
         ↓                           ↓
   249 bars (past)            1 bar (today's live OHLCV)
                 ↘           ↙
           CachedMarketDataAdapter
                     ↓
             250 bars total
                     ↓
            IndicatorService
                     ↓
              DSL Strategy
```

### Benefits

- **Fresh signals**: 200-day SMA uses today's current price, not yesterday's close
- **Volume data**: Today's cumulative volume available for volume-based indicators
- **Efficient**: Live bar cached per-symbol for duration of Lambda run

## Logging

All strategy operations include structured logging with correlation IDs:

```json
{
  "timestamp": "2024-01-01T10:00:00Z",
  "level": "INFO",
  "message": "Strategy execution started",
  "correlation_id": "signal-123",
  "strategy_name": "nuclear",
  "symbols": ["SPY", "QQQ"],
  "module": "strategy_v2.core.orchestrator"
}
```

Key log points:
- Strategy execution start/completion
- Signal generation (per strategy)
- Indicator calculations
- Error conditions
- Data fetching operations

## Testing and Validation

### Unit Tests
```bash
# Run strategy module tests
poetry run pytest tests/strategy_v2/ -v

# Test with coverage
poetry run pytest tests/strategy_v2/ --cov=the_alchemiser.strategy_v2
```

### Integration Testing
```bash
# Validate with real market data (paper trading)
poetry run python scripts/validate_strategy_v2.py
```

### Type Checking
```bash
# Verify type correctness
make type-check
```
