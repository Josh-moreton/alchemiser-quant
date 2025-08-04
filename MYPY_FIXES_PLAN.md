# MyPy Type Errors Fix Plan

## Overview

MyPy analysis found **233 errors in 48 files** (out of 98 source files checked). This document provides a comprehensive plan to fix all type-related issues systematically.

## Error Categories Summary

### 1. Missing Type Parameters (Most Common - ~150 errors)

- `dict` without type parameters → `dict[str, Any]`
- `list` without type parameters → `list[Any]` or specific types
- `tuple` without type parameters → `tuple[type1, type2, ...]`
- Generic classes missing type parameters

### 2. Missing Variable Type Annotations (~25 errors)

- Variables need explicit type hints
- Dictionary and list initializations

### 3. Incompatible Type Assignments (~20 errors)  

- `float` assigned to `int` variables
- Type mismatches in complex expressions

### 4. Return Type Issues (~15 errors)

- Functions returning `Any` when specific types expected
- Missing return type annotations

### 5. Protocol/Class Definition Issues (~10 errors)

- Generic class inheritance
- Protocol definitions

### 6. Complex Type Issues (~13 errors)

- Union type mismatches
- Invalid index types
- Attribute access errors

## Detailed Fix Plan by File Category

### A. Email Templates (`core/ui/email/templates/`)

**Files affected:**

- `base.py` (1 error)
- `signals.py` (1 error)
- `portfolio.py` (5 errors)
- `performance.py` (4 errors)
- `trading_report.py` (10 errors)
- `__init__.py` (3 errors)

**Issues & Fixes:**

```python
# Before
def create_table(headers: list, rows: list, table_id: str = "") -> str:

# After  
def create_table(headers: list[str], rows: list[list[str]], table_id: str = "") -> str:

# Before
def build_positions_table(open_positions: list[dict]) -> str:

# After
def build_positions_table(open_positions: list[dict[str, Any]]) -> str:

# Before
total_unrealized_pl += unrealized_pl  # int += float

# After
total_unrealized_pl: float = 0.0
total_unrealized_pl += unrealized_pl
```

### B. Utils Module (`utils/`)

**Files affected:**

- `symbol_lookback_calculator.py` (1 error)
- `smart_pricing_handler.py` (2 errors)
- `position_manager.py` (1 error)
- `math_utils.py` (2 errors)
- `dashboard_utils.py` (4 errors)
- `account_utils.py` (3 errors)
- `limit_order_handler.py` (1 error)
- `websocket_order_monitor.py` (2 errors)
- `portfolio_pnl_utils.py` (2 errors)

**Common Issues & Fixes:**

```python
# Before
lookback_groups = {}

# After
lookback_groups: dict[str, Any] = {}

# Before
def get_pending_orders(self) -> list:

# After
def get_pending_orders(self) -> list[dict[str, Any]]:

# Before
return round(price, 2)  # Any return type

# After
return round(float(price), 2)  # Explicit float conversion
```

### C. Core Module (`core/`)

**Files affected:**

- `core/utils/s3_utils.py` (3 errors)
- `core/logging/logging_utils.py` (3 errors)  
- `core/ui/cli_formatter.py` (5 errors)
- `core/validation/indicator_validator.py` (2 errors)
- `core/secrets/secrets_manager.py` (7 errors)
- `core/ui/email/config.py` (1 error)
- `core/ui/email/client.py` (1 error)
- `core/data/real_time_pricing.py` (11 errors)
- `core/data/data_provider.py` (6 errors)

**Complex Issues & Fixes:**

```python
# Before
class AlchemiserLoggerAdapter(logging.LoggerAdapter):

# After  
class AlchemiserLoggerAdapter(logging.LoggerAdapter[logging.Logger]):

# Before
self._stats["last_heartbeat"] = datetime.now()  # datetime to int|None

# After
self._stats["last_heartbeat"]: datetime | None = datetime.now()

# Before
self._stats["connection_errors"] += 1  # None + int

# After
if self._stats["connection_errors"] is None:
    self._stats["connection_errors"] = 0
self._stats["connection_errors"] += 1
```

### D. Trading/KLM Workers (`core/trading/klm_workers/`)

**Files affected (19 files with ~65 errors):**

- `base_klm_variant.py` (14 errors)
- `variant_nova.py` (7 errors)
- `variant_830_21.py` (7 errors)
- `variant_530_18.py` (15 errors)
- `variant_520_22.py` (6 errors)
- `variant_506_38.py` (6 errors)
- `variant_1280_26.py` (6 errors)
- `variant_1200_28.py` (6 errors)
- `variant_410_38.py` (1 error)

**Pattern & Fixes:**

```python
# Before
def evaluate_bsc_strategy(self, indicators: dict) -> tuple[str, str, str]:

# After
def evaluate_bsc_strategy(self, indicators: dict[str, Any]) -> tuple[str, str, str]:

# Before
def get_required_symbols(self) -> list:

# After  
def get_required_symbols(self) -> list[str]:

# Before
result = self._evaluate_holy_grail_pop_bot(indicators)  # Type mismatch

# After
result: tuple[dict[str, float], str, str] = self._evaluate_holy_grail_pop_bot(indicators)
```

### E. Execution Module (`execution/`)

**Files affected:**

- `account_service.py` (4 errors)
- `alpaca_client.py` (1 error)
- `smart_execution.py` (3 errors)
- `portfolio_rebalancer.py` (4 errors)
- `reporting.py` (6 errors)
- `trading_engine.py` (11 errors)
- `types.py` (5 errors)

**Fixes:**

```python
# Before
def get_account_info(self) -> dict:

# After
def get_account_info(self) -> dict[str, Any]:

# Before
position_dict = {}

# After
position_dict: dict[str, dict[str, Any]] = {}

# Before
class TradingClient(Protocol):  # Redefinition

# After
class TradingClientProtocol(Protocol):  # Rename to avoid conflict
```

### F. Backtest Module (`backtest/`)

**Files affected:**

- `strategies/__init__.py` (1 error)
- `data_loader.py` (1 error)
- `engine.py` (3 errors)
- `cli.py` (1 error)

**Fixes:**

```python
# Before
combined_signals = {}

# After
combined_signals: dict[str, Any] = {}

# Before
return date.day == deposit_day  # Any return

# After
return bool(date.day == deposit_day)
```

### G. Strategy Management (`core/trading/`)

**Files affected:**

- `strategy_manager.py` (8 errors)
- `klm_ensemble_engine.py` (1 error)

**Complex Type Issues:**

```python
# Before
consolidated_portfolio = {}
strategy_attribution = {}

# After
consolidated_portfolio: dict[str, float] = {}
strategy_attribution: dict[str, list[StrategyType]] = {}

# Before
strategy_signals[strategy_type] = {...}  # Index type mismatch

# After
strategy_signals: dict[StrategyType, dict[str, Any]] = {}
strategy_signals[strategy_type] = {...}
```

### H. Other Modules

**Tracking:**

- `tracking/strategy_order_tracker.py` (3 errors)

**Main:**

- `main.py` (2 errors)

## Implementation Strategy

### Phase 1: Quick Wins (1-2 hours)

1. **Missing Type Parameters** - Add `[str, Any]`, `[Any]` to generic types
2. **Simple Variable Annotations** - Add type hints to dictionary/list initializations

### Phase 2: Medium Complexity (2-3 hours)  

1. **Function Return Types** - Fix return type annotations
2. **Assignment Type Issues** - Fix int/float mismatches
3. **Protocol/Class Issues** - Fix inheritance and redefinitions

### Phase 3: Complex Issues (3-4 hours)

1. **Union Type Mismatches** - Fix complex type relationships
2. **Generic Class Parameters** - Fix LoggerAdapter and similar
3. **Statistics Type Issues** - Fix real-time pricing stats handling
4. **Strategy Manager Types** - Fix complex dictionary typing

### Phase 4: Testing & Validation (1 hour)

1. Run MyPy after each phase
2. Ensure no new errors introduced
3. Run existing tests to ensure functionality preserved

## File-by-File Action Items

### High Priority Files (Most Errors)

1. `variant_530_18.py` (15 errors) - KLM trading logic
2. `base_klm_variant.py` (14 errors) - Base trading class
3. `real_time_pricing.py` (11 errors) - Data handling
4. `trading_engine.py` (11 errors) - Core execution
5. `trading_report.py` (10 errors) - Reporting

### Medium Priority Files (5-8 errors)

6. `strategy_manager.py` (8 errors)
7. `secrets_manager.py` (7 errors)
8. `variant_nova.py` (7 errors)
9. `variant_830_21.py` (7 errors)
10. `data_provider.py` (6 errors)

### Low Priority Files (1-4 errors)

- All remaining files with 1-4 errors each

## Automation Script Template

```bash
#!/bin/bash
# mypy-fix-automation.sh

echo "Starting MyPy fixes..."

# Phase 1: Simple type parameter additions
find the_alchemiser -name "*.py" -exec sed -i 's/: dict)/: dict[str, Any])/g' {} \;
find the_alchemiser -name "*.py" -exec sed -i 's/: list)/: list[Any])/g' {} \;

# Run mypy after each phase
echo "Running MyPy check..."
python -m mypy the_alchemiser --show-error-codes > mypy_phase1.txt

echo "Phase 1 complete. Check mypy_phase1.txt for remaining errors."
```

## Expected Results

- **Before:** 233 errors in 48 files
- **After Phase 1:** ~150 errors (83 fixed)
- **After Phase 2:** ~80 errors (153 fixed)
- **After Phase 3:** ~20 errors (213 fixed)
- **After Phase 4:** 0 errors (233 fixed)

## Notes

1. **Backward Compatibility:** All fixes maintain Python 3.9+ compatibility
2. **Type Imports:** May need to add `from typing import Any, Dict, List` in some files
3. **Testing:** Run existing test suite after major phases
4. **Documentation:** Update docstrings with proper type information where beneficial

## Maintenance

After fixing all errors:

1. Add MyPy to CI/CD pipeline
2. Configure pre-commit hooks for type checking
3. Add MyPy configuration file (`mypy.ini`) with project-specific settings
4. Consider gradual typing for new features

---

*This plan provides a systematic approach to achieving 100% MyPy compliance for the The-Alchemiser project.*
