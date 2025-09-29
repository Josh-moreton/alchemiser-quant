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

### As a Module (NEW)

You can now run the strategy module directly to generate current signals without triggering trading:

```bash
# List all available strategies
python -m the_alchemiser.strategy_v2 --list

# Run a specific strategy
python -m the_alchemiser.strategy_v2 --strategy Nuclear

# Run all configured strategies (default)
python -m the_alchemiser.strategy_v2

# Output signals in JSON format
python -m the_alchemiser.strategy_v2 --strategy TECL --format json

# Enable verbose logging
python -m the_alchemiser.strategy_v2 --strategy Nuclear --verbose
```

This CLI mode runs in test mode with mock credentials and gracefully falls back to CASH signals when market data is unavailable, making it perfect for signal analysis without requiring live API credentials.

### CLI Examples

```bash
# See what strategies are available
$ python -m the_alchemiser.strategy_v2 --list
Available strategies:
  1-KMLM
  2-Nuclear
  3-Starburst
  4-What
  5-Coin
  6-TQQQ-FLT
  7-Phoenix
  TECL
  Ult

# Run the Nuclear strategy and see current signals
$ python -m the_alchemiser.strategy_v2 --strategy Nuclear
🔄 Running strategy: 2-Nuclear

📊 Generated Signals:
================================================================================
Symbol     Action Strategy        Reasoning
--------------------------------------------------------------------------------
CASH       BUY    UNKNOWN         2-Nuclear evaluation failed, fallback to c...
================================================================================
Total signals: 1

# Get signals in JSON format for programmatic use
$ python -m the_alchemiser.strategy_v2 --strategy TECL --format json
[
  {
    "symbol": "CASH",
    "action": "BUY", 
    "strategy": "UNKNOWN",
    "reasoning": "TECL evaluation failed, fallback to cash position",
    "timestamp": "2025-09-29T20:28:22.643214+00:00",
    "data_source": "unknown",
    "fallback": true
  }
]
```

**Note:** Currently the CLI runs in test mode and falls back to CASH signals when market data is unavailable. This provides a safe way to test strategy logic without requiring live API credentials. In a production environment with proper credentials, the strategies would generate actual buy/sell signals based on real market data.

### As a Library

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