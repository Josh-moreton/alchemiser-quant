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

```python
from the_alchemiser.strategy_v2.core.orchestrator import SingleStrategyOrchestrator
from the_alchemiser.strategy_v2.models.context import StrategyContext
from datetime import datetime

# Create strategy context
context = StrategyContext(
    symbols=["SPY", "QQQ"],
    timeframe="1D",
    as_of=datetime.utcnow()
)

# Run strategy
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

## Error Handling

Strategy_v2 uses typed exceptions with module context:

- `StrategyError`: Strategy execution failures
- `ConfigurationError`: Invalid configuration or context
- All errors include `module="strategy_v2.*"` metadata

## Performance

- O(n * lookback) complexity with batched data fetching
- Zero I/O inside inner loops
- Deterministic outputs for same inputs
- Correlation ID propagation for observability