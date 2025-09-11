# Strategy_v2 Rebuild Plan

## Executive summary

The Strategy module will be rebuilt as Strategy_v2 with one immutable rule: the current strategy and indicator source files (Nuclear, KLM, TECL, and the indicators they rely on) must be moved verbatim (git mv preserving history) into the new structure—no edits to their logic. Strategy_v2 consumes market data from shared Alpaca capabilities and outputs pure strategy signal DTOs (StrategyAllocationDTO) for Portfolio_v2 to transform into a RebalancePlanDTO.

Outcomes:

- Strict, minimal responsibilities (signal generation only)
- Clean contracts using shared DTOs
- Zero execution/portfolio coupling
- Complete preservation of existing strategy behavior via file moves, not rewrites

## Problem statement

### Current issues

1. Mixed concerns inside strategy code (ad-hoc data access, portfolio or execution hints)
2. Architectural violations (pulling in portfolio/execution behavior)
3. Fragile contracts (no single authoritative Strategy DTO)
4. Risk to signal integrity when refactoring code

### Root cause

The module lacks a crisp boundary and contract. Strategies should strictly transform market data into signals; downstream planning and execution must be completely decoupled.

## Immutable migration rule (non-negotiable)

- The strategy engines (Nuclear, KLM, TECL) and any indicator code they rely on MUST be moved with `git mv` into Strategy_v2 without content changes.
- Preserve history and file paths with a 1:1 mapping; do not reformat, rename symbols, or optimize internals.
- If adaptation is needed (e.g., import paths), create thin adapters/wrappers in Strategy_v2 around the moved files; DO NOT edit the originals’ logic.

Note: The actual `git mv` steps should be executed in a branch with a dedicated commit that contains only renames to preserve blame and reduce review noise.

## Core design principle

- Inputs: Market data (prices/bars/features) via shared Alpaca capabilities and helpers.
- Outputs: StrategyAllocationDTO (shared.dto) expressing target weights and metadata (correlation_id, as_of).
- No side effects: No order placement, no portfolio sizing, no execution hints, no position fetching.

## Architecture vision

```mermaid
flowchart LR
  D[shared.brokers.AlpacaManager] --> B
  E[shared.data/* (if needed)] --> B
  A[Strategy_v2 engines (Nuclear/KLM/TECL)] --> B[Signal Orchestrator]
  B --> C[StrategyAllocationDTO]
```markdown

- Dependencies: strategy_v2 → shared only (dto, types, brokers/data adapters, config)
- Isolation: No imports from portfolio/ or execution/
- Determinism: Same inputs → same signals

## New module structure

```text
strategy_v2/
├── __init__.py
├── engines/                         # MOVED: existing strategy engines (verbatim)
│   ├── nuclear/                     # e.g., moved package or files for Nuclear
│   ├── klm/
│   └── tecl/
├── indicators/                      # MOVED: indicator code used by engines
│   └── ...
├── core/
│   ├── orchestrator.py              # Thin orchestrator to run a strategy and emit DTOs
│   └── registry.py                  # Strategy registry/factory by name/id
├── adapters/
│   ├── market_data_adapter.py       # Thin wrapper for shared Alpaca (bars, prices)
│   └── feature_pipeline.py          # Optional: computed features wrapper (if needed)
├── models/
│   └── context.py                   # StrategyContext (symbols, timeframe, params)
└── README.md                        # Scope, contract, examples
```

Each new Python file begins with:
"""Business Unit: strategy | Status: current

Signal generation and indicator calculation for trading strategies.
"""

## DTO contracts

- Output: StrategyAllocationDTO (NEW or EXISTING in shared/dto)
  - target_weights: dict[str, Decimal]
  - correlation_id: str
  - as_of: datetime | None
  - metadata?: mapping (free-form)
- Expose via `shared/dto/__init__.py`.
- If a separate StrategySignalDTO is desired for non-allocation signals, define it in shared/dto and keep Portfolio_v2 consuming StrategyAllocationDTO (or an adapter converts Signal → Allocation in Strategy_v2).

Decimal policy: Financial amounts must be Decimal. Statistical features may be float; compare with math.isclose.

## What Strategy_v2 SHOULD do

- Read required market data via shared Alpaca adapters (price bars, quotes, etc.)
- Build any computed features in adapters/pipelines (outside engine logic)
- Execute the moved strategy engine code unchanged
- Map the engine’s output into StrategyAllocationDTO (weights sum ~1.0)

## What Strategy_v2 SHOULD NOT do

- Read positions or account state
- Size orders or create RebalancePlanDTO
- Interact with portfolio or execution modules
- Mutate shared state or rely on side effects

## Git move plan (preserve history)

1. Identify all source files for Nuclear, KLM, TECL, and their indicators.
2. Create a branch `feature/strategy_v2-migration`.
3. Commit 1: Pure `git mv` of strategy and indicator files into `strategy_v2/engines/` and `strategy_v2/indicators/` maintaining sub-structure.
4. Commit 2: Add new adapters/orchestrator/registry (no edits to moved files).
5. Commit 3: Wire public API and update import paths via thin wrappers (adapters), not by editing moved files.
6. Commit 4: Add README and deprecation notes for legacy strategy.

Note: Keep the `git mv` commit isolated to show 100% rename-only.

## Implementation plan

### Phase 1: Contracts and scaffolding (Week 1)

- Ensure `StrategyAllocationDTO` exists in `shared/dto/strategy_allocation_dto.py` (or create it) and expose it publicly.
- Create `strategy_v2/` skeleton with business unit docstrings and strict typing.
- Add a simple `registry.py` that maps strategy names to callables.

### Phase 2: Market data adapters (Week 2)

- `adapters/market_data_adapter.py`:
  - Wrap `shared.brokers.AlpacaManager` for bars and prices.
  - Provide `get_bars(symbols, timeframe, lookback)` and `get_current_prices(symbols)`.
  - No network calls inside tight loops; batch where possible.
- Optional `adapters/feature_pipeline.py` for non-financial feature computation (floats; compare with tolerances).

### Phase 3: Git move engines and indicators (Week 3)

- Perform the `git mv` for Nuclear, KLM, TECL, and all indicator dependencies into `strategy_v2/engines/` and `strategy_v2/indicators/`.
- Do not alter the content. If Python packaging or imports need alignment, implement thin wrapper modules without touching the moved files.

### Phase 4: Orchestrator and mapping (Week 4)

- `core/orchestrator.py`:
  - `run(strategy_id, context) -> StrategyAllocationDTO`
  - Internals: fetch data via adapter → run engine → normalize to weights → build DTO.
- `core/registry.py`: expose `get_strategy(strategy_id)` returning the function/class to run.
- Ensure weights normalization; if sum not ~1.0, normalize (documented) or raise per config.

### Phase 5: Integration and migration (Week 5)

- Add feature flag `USE_STRATEGY_V2=true` in the trading engine path.
- Orchestrator translates `strategy_id` to engine and returns StrategyAllocationDTO.
- Keep legacy strategy paths intact initially; log and compare outputs offline if needed.

### Phase 6: Validation (Week 6)

- Provide a minimal manual validation script (no test framework):

```python
# scripts/validate_strategy_v2.py (manual)
from decimal import Decimal
from datetime import datetime
from the_alchemiser.shared.dto.strategy_allocation_dto import StrategyAllocationDTO
from the_alchemiser.strategy_v2.core.orchestrator import StrategyOrchestrator
from the_alchemiser.strategy_v2.models.context import StrategyContext

ctx = StrategyContext(symbols=["SPY", "QQQ"], timeframe="1D", as_of=datetime.utcnow())
alloc: StrategyAllocationDTO = StrategyOrchestrator().run("nuclear", ctx)
print(alloc)
```

- Paper checks: DTO shape, weights sum ~ 1.0, deterministic outputs given same data.

### Phase 7: Hardening (Week 7)

- Error types: `StrategyError`, `ConfigurationError` with metadata `module="strategy_v2.core.orchestrator"`.
- Observability: correlation_id propagation, input data window logged, version of engine file.
- Performance: O(n * lookback) with batched data fetch; zero IO inside inner loops.

## Algorithmic contract

- Inputs:
  - StrategyContext: symbols: list[str], timeframe: str, as_of: datetime | None, params?: mapping
  - Market data (bars/prices) via adapters
- Output:
  - StrategyAllocationDTO: target_weights: dict[str, Decimal], correlation_id, as_of
- Error modes:
  - Missing data: `StrategyError`
  - Invalid weights: normalization or error per config
- Success criteria:
  - Stable/deterministic output for same inputs
  - No float arithmetic for money; non-financial floats with tolerances

## Edge cases

- Symbol data gaps: interpolate or drop per policy; log decision
- Zero or near-zero volatility windows: ensure engine guards are preserved (unchanged)
- Strategy requiring indicators: indicators are moved verbatim; adapter computes prerequisites if needed
- Time alignment: all timestamps aligned to `as_of` and timeframe boundaries

## Acceptance criteria

- Engines and indicators are `git mv`-ed verbatim; no content changes
- Strategy_v2 produces StrategyAllocationDTO only; no Portfolio/Execution imports
- Uses shared adapters for data; no direct broker calls in engines
- Business unit docstrings present; mypy clean; ruff clean
- `BUSINESS_UNITS_REPORT.md` updated when adding/moving files

## Constraints and rules

- Follow `.github/copilot-instructions.md`:
  - Module boundaries enforced (strategy → shared only)
  - Use Decimal for money; floats only for non-financial stats with tolerances
  - Protocols preferred for adapter interfaces
  - No tests added by AI agent; provide manual validation script only
  - Public API via `strategy_v2.__init__`
- Security: no secrets embedded; use shared/config for env

## File-by-file sketch

- `strategy_v2/core/orchestrator.py`
  - `class StrategyOrchestrator`
  - `run(strategy_id: str, context: StrategyContext) -> StrategyAllocationDTO`
- `strategy_v2/core/registry.py`
  - Registry for `{"nuclear": engine_callable, "klm": ..., "tecl": ...}`
- `strategy_v2/adapters/market_data_adapter.py`
  - Thin wrapper to `shared.brokers.AlpacaManager` or shared data services
- `strategy_v2/adapters/feature_pipeline.py` (optional)
  - Feature computation utilities (non-financial float domain)
- `strategy_v2/models/context.py`
  - Immutable dataclass holding inputs for an engine
- `strategy_v2/engines/*` and `strategy_v2/indicators/*`
  - MOVED verbatim via `git mv`

## Deprecation plan (legacy strategy)

- Add `strategy/README_DEPRECATED.md`:

```markdown
# DEPRECATED STRATEGY MODULE

This module is deprecated in favor of `strategy_v2`.

Use:

```python
# OLD (deprecated)
from the_alchemiser.strategy.engines.nuclear import run

# NEW (recommended)
from the_alchemiser.strategy_v2.core.orchestrator import StrategyOrchestrator
```

Timeline:

- Phase 1: strategy_v2 available alongside legacy
- Phase 2: default to strategy_v2 behind feature flag
- Phase 3: remove legacy module after stability window

```

## Timeline

| Week | Phase                | Deliverables                                       |
|------|----------------------|----------------------------------------------------|
| 1    | Contracts/Scaffold   | DTO check, skeleton, registry                      |
| 2    | Data Adapters        | Market data adapter + optional feature pipeline     |
| 3    | Git Move             | Engines + indicators moved verbatim (rename-only)   |
| 4    | Orchestrator/Mapping | Orchestrator + DTO mapping + normalization          |
| 5    | Integration/Migration| Engine toggle + legacy deprecation doc              |
| 6    | Validation           | Manual validation script + paper checks             |
| 7    | Hardening            | Errors, observability, performance pass             |

## References

- `PORTFOLIO_MODULE_REBUILD_PLAN.md` (consuming StrategyAllocationDTO)
- `EXECUTION_MODULE_REBUILD_PLAN.md` (DTO boundary pattern)
- `shared/brokers/alpaca_manager.py` (market data access)
- `.github/copilot-instructions.md` (module boundaries, Decimal policy, typing)
