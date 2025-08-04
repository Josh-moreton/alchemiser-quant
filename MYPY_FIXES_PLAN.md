# MyPy Final Phase Fix Plan

## Current Status (4 August 2025)

🎉 **MAJOR SUCCESS!** Phase 1 & 2 complete: **214 errors fixed** (from 233 → 19)  
**92% Complete** - Only 19 complex errors remain across 7 files

## Progress Summary

- **Original State:** 233 errors in 48 files (out of 98 source files)
- **Phase 1 Complete:** ✅ Missing type parameters (~150 errors) - ALL FIXED
- **Phase 2 Complete:** ✅ Variable annotations, assignments (~64 errors) - ALL FIXED  
- **Current State:** 19 complex errors in 7 files requiring advanced type techniques

## Remaining Errors (Final Phase)

### Error Type Breakdown

| Error Type | Count | Complexity | Priority |
|------------|-------|------------|----------|
| `var-annotated` | 3 | Medium | High |
| `index` | 5 | High | Critical |
| `no-any-return` | 2 | Low | Medium |
| `attr-defined` | 2 | Medium | High |
| `assignment` | 2 | Medium | High |
| `return-value` | 1 | High | Critical |
| `arg-type` | 1 | Medium | High |
| `misc` | 1 | Low | Low |

## File-Specific Fix Plan

### 🔥 **Critical: strategy_manager.py** (9 errors)

**Location:** `the_alchemiser/core/trading/strategy_manager.py`  
**Issues:** Complex StrategyType literal typing and generic dictionaries

```python
# Current Issues:
# 1. var-annotated: consolidated_portfolio = {}
# 2. var-annotated: strategy_attribution = {}  
# 3. index: Invalid index type "Literal[StrategyType.TECL]" for "dict[Literal[StrategyType.NUCLEAR], ...]"
# 4. index: Invalid index type "Literal[StrategyType.KLM]" for "dict[Literal[StrategyType.NUCLEAR], ...]"
# 5. index: Invalid index type "StrategyType" for "dict[Literal[StrategyType.NUCLEAR], ...]"
# 6. return-value: Incompatible return tuple types
# 7. var-annotated: new_positions = {strategy: [] for strategy in StrategyType}
# 8. var-annotated: positions = {strategy: [] for strategy in StrategyType}
# 9. index: Unsupported target for indexed assignment ("Collection[str]")

# Fixes Required:
consolidated_portfolio: dict[str, float] = {}
strategy_attribution: dict[str, list[StrategyType]] = {}

# Fix strategy_signals typing - the issue is it's being typed as only NUCLEAR
strategy_signals: dict[StrategyType, dict[str, Any]] = {
    StrategyType.NUCLEAR: {},
    StrategyType.TECL: {},
    StrategyType.KLM: {}
}

# Fix return type annotation
def get_strategy_signals(...) -> tuple[dict[StrategyType, dict[str, Any]], dict[str, float], dict[str, list[StrategyType]]]:

# Fix comprehensions with explicit typing
new_positions: dict[StrategyType, list[Any]] = {strategy: [] for strategy in StrategyType}
positions: dict[StrategyType, list[Any]] = {strategy: [] for strategy in StrategyType}

# Fix summary dict typing
summary: dict[str, Any] = {...}
```

### 🔥 **Critical: strategy_order_tracker.py** (2 errors)

**Location:** `the_alchemiser/tracking/strategy_order_tracker.py`

```python
# Current Issues:
# 1. var-annotated: summary = {
# 2. index: Unsupported target for indexed assignment

# Fixes Required:
summary: dict[str, Any] = {
    "total_orders": len(orders),
    "strategies": {}
}

# Ensure strategies is properly typed as dict
if "strategies" not in summary:
    summary["strategies"] = {}
summary["strategies"][strategy.value] = {...}
```

### 🔥 **Critical: backtest/engine.py** (4 errors)

**Location:** `the_alchemiser/backtest/engine.py`

```python
# Current Issues:
# 1. attr-defined: "MultiStrategyManager" has no attribute "nuclear_engine"
# 2. attr-defined: "MultiStrategyManager" has no attribute "tecl_engine"  
# 3. no-any-return: Returning Any from function declared to return "bool"
# 4. no-any-return: Returning Any from function declared to return "bool"

# Fixes Required:
# Option 1: Add proper attributes to MultiStrategyManager
# Option 2: Use hasattr() checks with proper typing

if hasattr(manager, 'nuclear_engine'):
    symbols.extend(manager.nuclear_engine.all_symbols)
if hasattr(manager, 'tecl_engine'):  
    symbols.extend(manager.tecl_engine.all_symbols)

# Fix return types
return bool(date.day == deposit_day)
return bool(date.weekday() == (deposit_day - 1) % 7)
```

### 🔥 **Medium: execution/reporting.py** (1 error)

**Location:** `the_alchemiser/execution/reporting.py`

```python
# Current Issue:
# arg-type: Argument 1 has incompatible type "dict[StrategyType, Any]"; expected "dict[str, Any]"

# Fix Required: Convert StrategyType keys to strings
strategy_signals_str = {k.value: v for k, v in strategy_signals.items()}
build_strategy_summary(strategy_signals_str, ...)
```

### 🔥 **Medium: execution/trading_engine.py** (1 error)

**Location:** `the_alchemiser/execution/trading_engine.py`

```python
# Current Issue:
# assignment: Incompatible types (expression has type "Panel", variable has type "Table")

# Fix Required:
from rich.panel import Panel
orders_table: Panel = Panel(...)
# OR
orders_table = Panel(...)  # Let type inference handle it
```

### 🔥 **Medium: main.py** (1 error)

**Location:** `the_alchemiser/main.py`

```python
# Current Issue:
# assignment: Incompatible types (expression has type "bool | str", variable has type "bool")

# Fix Required:
success: bool | str = result
# OR
success = bool(result) if isinstance(result, str) else result
```

### 🔥 **Low: symbol_lookback_calculator.py** (1 error)

**Location:** `the_alchemiser/utils/symbol_lookback_calculator.py`

```python
# Current Issue:
# misc: Generator has incompatible item type "str"; expected "bool"

# Fix Required: Check the generator expression type
# The generator is producing strings but bool is expected
```

## Implementation Order

### Phase 3A: Quick Type Annotations (30 minutes)

1. Fix all `var-annotated` errors (3 total)
2. Fix `no-any-return` errors (2 total)  
3. Fix simple `assignment` errors (2 total)

### Phase 3B: Complex Index & Type Issues (1-2 hours)

1. **strategy_manager.py:** Fix StrategyType literal dictionary typing
2. **strategy_order_tracker.py:** Fix dynamic dictionary access
3. **execution/reporting.py:** Fix StrategyType to string conversion

### Phase 3C: Attribute & Return Type Issues (1 hour)

1. **backtest/engine.py:** Fix missing attributes and return types
2. **execution/trading_engine.py:** Fix Panel vs Table assignment
3. **main.py:** Fix bool/str union type

### Phase 3D: Final Edge Cases (30 minutes)

1. **symbol_lookback_calculator.py:** Fix generator type mismatch

## Advanced Type Techniques Required

### 1. Literal Type Unions for StrategyType

```python
from typing import Literal, Union
StrategyTypeDict = dict[Union[Literal[StrategyType.NUCLEAR], Literal[StrategyType.TECL], Literal[StrategyType.KLM]], dict[str, Any]]
# OR simpler:
StrategyTypeDict = dict[StrategyType, dict[str, Any]]
```

### 2. Conditional Attribute Access

```python
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    # Type-only imports for mypy
    pass

# Runtime attribute checks
if hasattr(obj, 'attr'):
    result = obj.attr  # type: ignore[attr-defined]
```

### 3. Union Type Handling

```python
from typing import Union
success: Union[bool, str] = result
if isinstance(success, str):
    success = bool(success)
```

## Expected Timeline

- **Phase 3A:** 30 minutes → Down to ~14 errors
- **Phase 3B:** 1-2 hours → Down to ~6 errors  
- **Phase 3C:** 1 hour → Down to ~2 errors
- **Phase 3D:** 30 minutes → **0 ERRORS** 🎉

**Total Time:** 3-4 hours to achieve **100% MyPy compliance**

## Validation Commands

```bash
# Test individual files as we fix them
python -m mypy the_alchemiser/core/trading/strategy_manager.py --show-error-codes --pretty --ignore-missing-imports

# Full project scan (after clearing cache)
rm -rf .mypy_cache && python -m mypy the_alchemiser --show-error-codes --pretty --ignore-missing-imports

# Success metric: "Success: no issues found in 98 source files"
```

## Success Criteria

🎯 **Target:** `Success: no issues found in 98 source files`

✅ **Achievement Unlocked:**

- 233 → 0 errors (100% reduction)
- 48 → 0 problematic files
- Full type safety across entire codebase
- Ready for production CI/CD integration

---

**Next Step:** Begin Phase 3A with the 3 simple `var-annotated` fixes!
