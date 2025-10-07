# TimeInForce Deprecation Notice

## Status: DEPRECATED as of v2.10.7

**Effective Date**: 2025-01-06  
**Removal Target**: v3.0.0  
**Replacement**: `BrokerTimeInForce` from `broker_enums.py`

---

## Summary

The `TimeInForce` class in `the_alchemiser/shared/types/time_in_force.py` has been officially deprecated following the financial-grade audit that identified it as dead code with architectural duplication.

## Reason for Deprecation

1. **Dead Code**: Zero production usage detected across the entire codebase
2. **Architectural Duplication**: `BrokerTimeInForce` enum in `broker_enums.py` provides identical functionality with additional features
3. **Missing Features**: Lacks `from_string()` and `to_alpaca()` conversion methods
4. **Validation Redundancy**: `__post_init__` validation is unreachable due to `Literal` type constraint

## What Changed in v2.10.7

### 1. Module Status Updated
- Module docstring marked as `Status: deprecated`
- Added `.. deprecated::` directive for documentation tools

### 2. Deprecation Warning Added
Every instantiation of `TimeInForce` now raises a `DeprecationWarning`:
```python
warnings.warn(
    "TimeInForce is deprecated as of version 2.10.7 and will be removed in "
    "version 3.0.0. Use BrokerTimeInForce from broker_enums.py instead.",
    DeprecationWarning,
    stacklevel=2,
)
```

### 3. Export Removed
`TimeInForce` has been removed from `__all__` in `shared/types/__init__.py`:
- Class can still be imported directly for backwards compatibility
- Will not appear in IDE autocomplete or `from shared.types import *`
- Import is marked with `# noqa: F401` to indicate intentional unused import

### 4. Tests Updated
All 16 tests updated to handle deprecation warnings:
- Tests that verify deprecation warning (5 tests)
- Tests that suppress warning to test functionality (11 tests)
- All tests pass (15 passed, 1 skipped)

## Migration Guide

### Before (Deprecated)
```python
from the_alchemiser.shared.types.time_in_force import TimeInForce

tif = TimeInForce(value="day")  # Raises DeprecationWarning
```

### After (Recommended)
```python
from the_alchemiser.shared.types.broker_enums import BrokerTimeInForce

# Option 1: Use enum directly
tif = BrokerTimeInForce.DAY

# Option 2: Convert from string
tif = BrokerTimeInForce.from_string("day")

# Option 3: Convert to Alpaca format
alpaca_tif = tif.to_alpaca()
```

## Deprecation Timeline

### v2.10.7 (Current - 2025-01-06)
- ✅ Module marked as deprecated
- ✅ `DeprecationWarning` raised on instantiation
- ✅ Removed from `__all__` exports
- ✅ Tests updated to handle warnings
- ✅ Documentation updated

### v2.11.0 - v2.99.x (Deprecation Period)
- Module remains available for backwards compatibility
- Deprecation warnings continue to be raised
- No new features will be added
- Bug fixes only if critical

### v3.0.0 (Planned Removal)
- ❌ Module will be completely removed
- ❌ Import will fail with `ModuleNotFoundError`
- ❌ Direct imports will break

## Impact Assessment

### Production Code
**Impact**: None - No production code uses `TimeInForce`

### Test Code
**Impact**: Minimal - Updated to suppress/verify deprecation warnings

### External Consumers
**Impact**: Minimal - Only affects code that directly imports `TimeInForce`
- Most code uses `BrokerTimeInForce` already
- Deprecation period provides time to migrate

## Benefits of Migration

### Using BrokerTimeInForce Provides:
1. **String Conversion**: `from_string()` method for parsing user input
2. **Broker Integration**: `to_alpaca()` method for Alpaca API calls
3. **Active Maintenance**: Used in production, actively maintained
4. **No Duplication**: Single source of truth for time-in-force values
5. **Better Typing**: Full enum support with IDE autocomplete

## Related Documentation

- **Audit Report**: `FILE_REVIEW_time_in_force.md`
- **Audit Summary**: `AUDIT_COMPLETION_time_in_force.md`
- **BrokerTimeInForce**: `the_alchemiser/shared/types/broker_enums.py`

## Contact

For questions or concerns about this deprecation:
- Review the audit reports in the repository
- Open an issue on GitHub
- Tag @copilot or @Josh-moreton

---

**Last Updated**: 2025-01-06  
**Version**: 2.10.7
