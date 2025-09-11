# 🚨 LEGACY EXECUTION MODULE - DEPRECATED

**⚠️ WARNING: This execution module is deprecated and will be removed in a future release.**

## Migration Notice

This legacy execution module has been replaced by the new **`execution_v2/`** module which provides:

- ✅ **Clean DTO-driven architecture**: Consumes `RebalancePlanDTO` without recalculation
- ✅ **Simplified codebase**: ~200 lines vs 10,000+ lines  
- ✅ **Better reliability**: Direct delegation to `AlpacaManager`
- ✅ **Strict module boundaries**: Only depends on `shared/` module
- ✅ **Comprehensive logging**: Clear execution tracking and error reporting

## Issues with Legacy Module

The current execution module has several architectural violations:

1. **Trade Recalculation**: Attempts to recalculate trades instead of consuming portfolio DTOs
2. **Position Dependencies**: Fetches additional position data violating module boundaries  
3. **Complex Filtering**: Applies complex business logic that belongs in portfolio module
4. **Scattered Responsibilities**: Mixing order placement with portfolio calculations
5. **Hard to Test**: Complex interdependencies make unit testing difficult

## Migration Path

### For New Development
Use `execution_v2.ExecutionManager` instead:

```python
# OLD (deprecated)
from the_alchemiser.execution.core.manager import ExecutionManager

# NEW (recommended) 
from the_alchemiser.execution_v2.core.execution_manager import ExecutionManager
```

### Current Integration
The trading engine automatically detects and uses `execution_v2` when available, with graceful fallback to this legacy module.

### API Changes
- **Input**: Now consumes `RebalancePlanDTO` directly from portfolio module
- **Output**: Returns `ExecutionResultDTO` with order details and success metrics
- **Simplicity**: No position fetching, no trade recalculation, no complex filtering

## Deprecation Timeline

- **Current**: Legacy module available with deprecation warnings
- **Next Release**: Legacy module marked for removal with migration guide
- **Future Release**: Legacy module removed entirely

## Getting Help

For migration assistance or questions:
1. Review `EXECUTION_MODULE_REBUILD_PLAN.md` for detailed architecture
2. See `execution_v2/` examples and documentation
3. Check trading engine integration patterns

## Technical Details

The new execution module follows the core principle:
> **Iterate through RebalancePlanDTO items and place orders - nothing more.**

This eliminates architectural violations and creates a focused, reliable execution system that does exactly what it should: execute trades as specified by the portfolio module.