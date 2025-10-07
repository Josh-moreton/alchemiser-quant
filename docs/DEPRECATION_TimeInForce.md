# TimeInForce Deprecation Notice

## Status: DEPRECATED as of v2.10.7

**Effective Date**: 2025-01-06
**Removal Target**: v3.0.0
**Replacement**: Use Alpaca SDK enums directly (`TimeInForce` from `alpaca.trading.enums`)

---

## Summary

The `TimeInForce` class in `the_alchemiser/shared/types/time_in_force.py` has been officially deprecated following the financial-grade audit that identified it as dead code with no production usage.

## Reason for Deprecation

1. **Dead Code**: Zero production usage detected across the entire codebase
2. **Unnecessary Abstraction**: Alpaca SDK provides native enum support
3. **Validation Redundancy**: `__post_init__` validation is unreachable due to `Literal` type constraint
4. **YAGNI Violation**: Built for multi-broker future that never materialized

## What Changed in v2.10.7

### 1. Module Status Updated
- Module docstring marked as `Status: deprecated`
- Added `.. deprecated::` directive for documentation tools

### 2. Deprecation Warning Added
Every instantiation of `TimeInForce` now raises a `DeprecationWarning`:
```python
warnings.warn(
    "TimeInForce is deprecated as of version 2.10.7 and will be removed in "
    "version 3.0.0. Use Alpaca SDK enums (TimeInForce from alpaca.trading.enums) directly.",
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
from alpaca.trading.enums import TimeInForce, OrderSide

# Use Alpaca SDK enums directly
tif = TimeInForce.DAY
order_side = OrderSide.BUY
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
- Production code uses Alpaca SDK enums directly
- Deprecation period provides time to migrate

## Benefits of Migration

### Using Alpaca SDK Enums Directly Provides:
1. **Native Support**: Built-in enum support from broker SDK
2. **No Abstraction Layer**: Direct access without wrapper overhead
3. **Active Maintenance**: Maintained by Alpaca team
4. **Standard API**: Follows Alpaca's official patterns
5. **Better IDE Support**: Full enum support with autocomplete

## Related Documentation

- **Audit Report**: `FILE_REVIEW_time_in_force.md`
- **Audit Summary**: `AUDIT_COMPLETION_time_in_force.md`
- **Alpaca SDK**: https://alpaca.markets/docs/python-sdk/

## Contact

For questions or concerns about this deprecation:
- Review the audit reports in the repository
- Open an issue on GitHub
- Tag @copilot or @Josh-moreton

---

**Last Updated**: 2025-10-07
**Version**: 2.16.2
