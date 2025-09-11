# DEPRECATED STRATEGY MODULE

⚠️ **This module is deprecated in favor of `strategy_v2`** ⚠️

## Migration Path

The strategy module has been replaced by `strategy_v2` which provides:
- ✅ Strict boundary enforcement (no portfolio/execution coupling)
- ✅ Clean DTO contracts using `StrategyAllocationDTO`
- ✅ Deterministic signal generation
- ✅ Batched market data access
- ✅ Comprehensive error handling and observability

### Old Usage (Deprecated)
```python
# OLD - Don't use this
from the_alchemiser.strategy.engines.nuclear import NuclearEngine
```

### New Usage (Recommended)
```python
# NEW - Use this instead
from the_alchemiser.strategy_v2 import StrategyOrchestrator, StrategyContext
from the_alchemiser.strategy_v2.core import create_orchestrator

# Example usage
context = StrategyContext(symbols=["SPY", "QQQ"], timeframe="1D")
orchestrator = create_orchestrator(api_key="...", secret_key="...")
allocation = orchestrator.run("nuclear", context)
```

## Migration Timeline

- **Phase 1**: ✅ strategy_v2 available alongside legacy (current)
- **Phase 2**: 🔄 Default to strategy_v2 behind feature flag
- **Phase 3**: 📅 Remove legacy module after stability window

## Strategy Engines

The following strategy engines have been moved to `strategy_v2`:

| Legacy Location | New Location | Status |
|----------------|--------------|---------|
| `strategy.engines.nuclear` | `strategy_v2.engines.nuclear` | ✅ Moved |
| `strategy.engines.klm` | `strategy_v2.engines.klm` | ✅ Moved |
| `strategy.engines.tecl` | `strategy_v2.engines.tecl` | ✅ Moved |
| `strategy.indicators` | `strategy_v2.indicators` | ✅ Moved |

## Compatibility

Temporary compatibility shims are in place to maintain backward compatibility,
but these will be removed in a future release. Please migrate to `strategy_v2`
as soon as possible.

## Questions?

For questions about migration, see the `strategy_v2/README.md` documentation
or the validation script in `scripts/validate_strategy_v2.py`.