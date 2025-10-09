# [File Review] the_alchemiser/shared/schemas/__init__.py

> **Purpose**: Conduct a rigorous, line-by-line review of a single Python file in the trading system, to institution-grade standards (correctness, controls, auditability, and safety). One issue per file.

---

## 0) Metadata

**File path**: `the_alchemiser/shared/schemas/__init__.py`

**Commit SHA / Tag**: `802cf268358e3299fb6b80a4b7cf3d4bda2994f4`

**Reviewer(s)**: GitHub Copilot AI Agent

**Date**: 2025-01-06

**Business function / Module**: shared/schemas

**Runtime context**: Python module initialization, import-time execution. No runtime I/O, no external service calls, no concurrency. Pure Python import mechanics for package facade.

**Criticality**: P2 (Medium) - Module facade for schema definitions; critical for maintaining clean API boundaries but does not directly handle financial calculations or order execution.

**Direct dependencies (imports)**:
```
Internal (relative imports from submodules):
- .accounts (AccountMetrics, AccountSummary, BuyingPowerResult, etc.)
- .asset_info (AssetInfo)
- .ast_node (ASTNode)
- .base (Result)
- .broker (OrderExecutionResult, WebSocketResult, WebSocketStatus)
- .common (AllocationComparison, Configuration, Error, etc.)
- .consolidated_portfolio (ConsolidatedPortfolio)
- .errors (ErrorDetailInfo, ErrorNotificationData, ErrorReportSummary, ErrorSummaryData)
- .execution_report (ExecutedOrder, ExecutionReport)
- .execution_result (ExecutionResult)
- .indicator_request (IndicatorRequest)
- .lambda_event (LambdaEvent)
- .market_bar (MarketBar)
- .market_data (MarketStatusResult, MultiSymbolQuotesResult, etc.)
- .order_request (MarketData, OrderRequest)
- .pnl (PnLData)
- .portfolio_state (PortfolioMetrics, PortfolioState, Position)
- .rebalance_plan (RebalancePlan, RebalancePlanItem)
- .strategy_allocation (StrategyAllocation)
- .strategy_signal (StrategySignal)
- .technical_indicator (TechnicalIndicator)
- .trace (Trace, TraceEntry)
- .trade_ledger (TradeLedger, TradeLedgerEntry)
- .trade_result_factory (create_failure_result, create_success_result)
- .trade_run_result (ExecutionStatus, ExecutionSummary, OrderAction, etc.)

External:
- All submodules depend on: pydantic, typing (stdlib)
```

**External services touched**:
```
None - Pure module initialization with no I/O
```

**Interfaces (DTOs/events) produced/consumed**:
```
Exported: 58 Pydantic models, enums, and utility functions
- Account schemas: AccountMetrics, AccountSummary, BuyingPowerResult, etc.
- Execution schemas: ExecutionResult, ExecutionReport, ExecutedOrder, etc.
- Market data schemas: MarketData, MarketBar, PriceResult, etc.
- Portfolio schemas: PortfolioState, Position, PortfolioMetrics, etc.
- Trade schemas: TradeRunResult, TradeLedger, RebalancePlan, etc.
- Error schemas: ErrorDetailInfo, ErrorNotificationData, ErrorReportSummary, etc.
- Utility functions: create_success_result, create_failure_result
```

**Related docs/specs**:
- `.github/copilot-instructions.md` - Coding standards and architecture rules
- `docs/file_reviews/FILE_REVIEW_shared_utils_init.md` - Similar __init__.py review
- `docs/file_reviews/FILE_REVIEW_core_types.md` - TypedDict to Pydantic migration context
- `the_alchemiser/shared/schemas/errors.py` - Contains deprecation notice for ErrorContextData

---

## 1) Scope & Objectives

- Verify the file's **single responsibility** and alignment with intended business capability.
- Ensure **correctness**, **numerical integrity**, **deterministic behaviour** where required.
- Validate **error handling**, **idempotency**, **observability**, **security**, and **compliance** controls.
- Confirm **interfaces/contracts** (DTOs/events) are accurate, versioned, and tested.
- Identify **dead code**, **complexity hotspots**, and **performance risks**.

---

## 2) Summary of Findings (use severity labels)

### Critical
1. **Broken export in `__all__`**: `ErrorContextData` is exported in `__all__` but not imported. This will cause `AttributeError` when users try to import it via `from the_alchemiser.shared.schemas import ErrorContextData`. The class has been moved to `shared/errors/context.py` but the export was not removed.

### High
None found ✅

### Medium
2. **Missing sorting in `__all__`**: The `__all__` list is not alphabetically sorted, making it harder to maintain and spot discrepancies. This violates consistency patterns seen in other reviewed modules (e.g., `shared/utils/__init__.py`).
3. **No module header comment**: Missing business unit header comment (`"""Business Unit: shared | Status: current."""`) at the top of the docstring, which is required by copilot-instructions.md.

### Low
4. **Long `__all__` list**: With 58 exports, the list is becoming unwieldy. Consider grouping imports/exports by category with comments for better maintainability.
5. **No lazy loading**: All submodules are eagerly loaded at import time, which may have performance implications for import-heavy codepaths.

### Info/Nits
6. **Import ordering**: Relative imports are not consistently ordered (not alphabetical or by category).
7. **Line count**: 142 lines - well within the 500-line soft limit ✅
8. **No dead code**: All imports are used in `__all__` ✅

---

## 3) Line-by-Line Notes

### Detailed Line-by-Line Analysis

| Line(s) | Issue / Observation | Severity | Evidence / Excerpt | Proposed Action |
|---------|---------------------|----------|-------------------|-----------------|
| 1-6 | Module docstring present with purpose | ✅ Info | `"""Shared schemas module.\n\nBusiness Unit: shared \| Status: current\n\nCommon schema definitions used across modules."""` | None - correct ✅ |
| 1-6 | Business unit header present in docstring | ✅ Info | Contains required "Business Unit: shared \| Status: current" | None - correct ✅ |
| 8-16 | Import from .accounts module | ✅ Info | 7 classes imported | Verify alphabetical ordering |
| 17 | Import AssetInfo | ✅ Info | Single import | None |
| 18 | Import ASTNode | ✅ Info | Single import | None |
| 19 | Import Result | ✅ Info | Base result class | None |
| 20 | Import broker schemas | ✅ Info | 3 classes imported | None |
| 21-27 | Import from .common module | ✅ Info | 5 classes imported | None |
| 28 | Import ConsolidatedPortfolio | ✅ Info | Single import | None |
| 29-34 | Import from .errors module | ✅ Info | 4 classes imported - does NOT include ErrorContextData | **CRITICAL**: ErrorContextData moved to shared.errors.context |
| 35-38 | Import from .execution_report | ✅ Info | 2 classes imported | None |
| 39 | Import ExecutionResult | ✅ Info | Single import | None |
| 40 | Import IndicatorRequest | ✅ Info | Single import | None |
| 41 | Import LambdaEvent | ✅ Info | Single import | None |
| 42 | Import MarketBar | ✅ Info | Single import | None |
| 43-49 | Import from .market_data | ✅ Info | 5 classes imported | None |
| 50-53 | Import from .order_request | ✅ Info | 2 classes imported (MarketData, OrderRequest) | None |
| 54 | Import PnLData | ✅ Info | Single import from .pnl | None |
| 55-59 | Import from .portfolio_state | ✅ Info | 3 classes imported | None |
| 60-63 | Import from .rebalance_plan | ✅ Info | 2 classes imported | None |
| 64-66 | Import from .strategy_allocation | ✅ Info | 1 class imported | None |
| 67 | Import StrategySignal | ✅ Info | Single import | None |
| 68-70 | Import from .technical_indicator | ✅ Info | 1 class imported | None |
| 71 | Import Trace, TraceEntry | ✅ Info | 2 classes from .trace | None |
| 72 | Import TradeLedger, TradeLedgerEntry | ✅ Info | 2 classes from .trade_ledger | None |
| 73 | Import utility functions | ✅ Info | create_failure_result, create_success_result | None |
| 74-81 | Import from .trade_run_result | ✅ Info | 6 items imported (enums and classes) | None |
| 82 | Blank line separator | ✅ Info | Separates imports from __all__ | None |
| 83-142 | `__all__` definition | 🔴 Critical | 58 exports defined | **CRITICAL**: ErrorContextData not imported but exported |
| 94 | ErrorContextData in `__all__` | 🔴 Critical | Line 94: `"ErrorContextData",` | Remove from __all__ or add migration import |
| 83-142 | `__all__` not alphabetically sorted | ⚠️ Medium | Order is roughly categorical but not alphabetical | Sort alphabetically for maintainability |
| 143 | End of file | ✅ Info | Proper termination | None |

---

## 4) Correctness & Contracts

### Correctness Checklist

- [x] ✅ **The file has a clear purpose** and does not mix unrelated concerns (SRP)
  - **Status**: PASS - Serves solely as a package facade for schema exports
  - **Evidence**: Only imports and re-exports schema classes, no logic

- [x] ✅ **Public functions/classes have docstrings** with inputs/outputs, pre/post-conditions, and failure modes
  - **Status**: PASS - Module docstring present and adequate for an `__init__.py`
  - **Note**: Individual schemas documented in their source modules

- [x] ✅ **Type hints** are complete and precise (no `Any` in domain logic; use `Literal/NewType` where helpful)
  - **Status**: N/A - No functions or classes defined; all type hints in source modules
  - **Note**: Type checking handled by source modules

- [x] ✅ **DTOs are frozen/immutable** and validated (e.g., Pydantic v2 models with constrained types)
  - **Status**: PASS - All exported schemas use Pydantic v2 with strict validation
  - **Evidence**: Verified in source modules (accounts.py, errors.py, etc.)

- [x] ✅ **Numerical correctness**: currency uses `Decimal`; floats use `math.isclose` or explicit tolerances; no `==`/`!=` on floats
  - **Status**: N/A - No numerical operations in this facade module
  - **Note**: Numerical correctness enforced in source schema modules

- [x] ✅ **Error handling**: exceptions are narrow, typed (from `shared.errors`), logged with context, and never silently caught
  - **Status**: N/A - No error handling code in facade module
  - **Note**: Import errors would fail at module load time (desired behavior)

- [x] ✅ **Idempotency**: handlers tolerate replays; side-effects are guarded by idempotency keys or checks
  - **Status**: N/A - No handlers or side-effects in facade module

- [x] ✅ **Determinism**: tests freeze time (`freezegun`), seed RNG; no hidden randomness in business logic
  - **Status**: N/A - No business logic or randomness in facade module

- [x] ✅ **Security**: no secrets in code/logs; input validation at boundaries; no `eval`/`exec`/dynamic imports
  - **Status**: PASS - No secrets, no dynamic imports, only static imports
  - **Evidence**: All imports are explicit relative imports

- [x] ✅ **Observability**: structured logging with `correlation_id`/`causation_id`; one log per state change; no spam in hot loops
  - **Status**: N/A - No logging in facade module (no state changes)

- [ ] ❌ **Testing**: public APIs have tests; property-based tests for maths; coverage ≥ 80% (≥ 90% for strategy/portfolio)
  - **Status**: FAIL - No dedicated test for `__init__.py` exports
  - **Evidence**: No `test_init.py` or `test_schemas_init.py` found in tests/shared/schemas/
  - **Recommendation**: Add test to verify all exports are importable

- [x] ✅ **Performance**: no hidden I/O in hot paths; vectorised Pandas ops; HTTP clients pooled with rate limits
  - **Status**: PASS - Pure import mechanics, no I/O
  - **Note**: Eager loading of all submodules may have import-time overhead

- [x] ✅ **Complexity**: cyclomatic ≤ 10, cognitive ≤ 15, functions ≤ 50 lines, params ≤ 5
  - **Status**: PASS - Cyclomatic complexity = 1 (no branches)
  - **Evidence**: 142 lines, no functions, only imports

- [x] ✅ **Module size**: ≤ 500 lines (soft), split if > 800
  - **Status**: PASS - 142 lines (well under limit)

- [ ] ⚠️ **Imports**: no `import *`; stdlib → third-party → local; no deep relative imports
  - **Status**: PARTIAL - No `import *` ✅, only relative imports (appropriate for `__init__.py`) ✅
  - **Issue**: Imports not alphabetically ordered ⚠️
  - **Issue**: One import is broken (ErrorContextData in `__all__` but not imported) 🔴

---

## 5) Additional Notes

### Architecture Observations

1. **Module Purpose**: This file serves as a **package facade** for shared schema definitions. It consolidates exports from 25+ submodules into a single import path (`from the_alchemiser.shared.schemas import ...`).

2. **Pydantic v2 Migration**: All exported schemas use Pydantic v2 with strict validation (verified in source modules). This is a significant improvement over the deprecated TypedDict approach documented in `FILE_REVIEW_core_types.md`.

3. **No Backward Compatibility Exports**: Unlike some other modules, this facade does not provide backward compatibility imports. The `ErrorContextData` migration comment in `errors.py` suggests it was intentionally moved, but the export was not cleaned up here.

4. **Import Overhead**: With 25 submodule imports and 58 exports, this module loads all schema definitions eagerly. For large applications, consider lazy loading via `__getattr__` (as seen in parent `shared` module).

### Security & Compliance

- ✅ **No secrets or credentials**: Pure schema definitions
- ✅ **No eval/exec/dynamic imports**: All imports are static
- ✅ **No PII/sensitive data**: Schemas define structure, not data
- ✅ **Immutability**: All Pydantic models use `frozen=True` in source modules

### Performance Considerations

**Import-Time Cost**:
- 25 relative imports executed eagerly
- Each submodule imports Pydantic, typing, and may import pandas/numpy
- Estimated import time: 100-300ms (first import only, cached thereafter)

**Optimization Opportunities** (Low Priority):
- Implement lazy loading via `__getattr__` for rarely-used schemas
- Profile import time to identify slow submodules
- Consider splitting into category-specific facades (e.g., `schemas.execution`, `schemas.market_data`)

### Testing Gap

**Missing Tests**:
1. No test file for `shared/schemas/__init__.py`
2. Should verify:
   - All exports in `__all__` are importable
   - No exports missing from `__all__`
   - Import mechanics work correctly
   - No circular dependencies

**Reference**: Similar modules have comprehensive tests (e.g., `tests/strategy_v2/engines/dsl/operators/test_init.py`)

### Migration Context

**ErrorContextData Migration**:
- Original location: `shared/schemas/errors.py` (TypedDict)
- Current location: `shared/errors/context.py` (Pydantic model)
- Deprecation: v2.18.0
- Removal planned: v3.0.0
- **Issue**: Export in `__all__` was not updated during migration

**Recommendation**: Complete the migration by either:
1. Removing `ErrorContextData` from `__all__` (breaking change - requires MAJOR version bump)
2. Adding a backward compatibility import with deprecation warning (gentler migration path)

---

## 6) Recommended Fixes

### Priority 1: Critical (Must Fix Before Production)

#### Fix 1: Remove or migrate ErrorContextData export

**Problem**: `ErrorContextData` is exported in `__all__` (line 94) but not imported, causing `AttributeError` for consumers.

**Root Cause**: Class was moved to `shared/errors/context.py` in v2.18.0, but `__all__` was not updated.

**Option A - Breaking Change (MAJOR version bump required)**:
```python
# Remove from __all__ (line 94)
__all__ = [
    "ASTNode",
    # ... other exports ...
    # "ErrorContextData",  # REMOVED: Moved to shared.errors.context in v2.18.0
    "ErrorDetailInfo",
    # ... rest of exports ...
]
```

**Option B - Backward Compatible (MINOR version bump, deprecation warning)**:
```python
# At top of file after existing imports:
from the_alchemiser.shared.errors.context import ErrorContextData
import warnings

# Add deprecation wrapper (after imports, before __all__):
def __getattr__(name: str):
    if name == "ErrorContextData":
        warnings.warn(
            "Importing ErrorContextData from shared.schemas is deprecated. "
            "Use 'from the_alchemiser.shared.errors.context import ErrorContextData' instead. "
            "This backward compatibility will be removed in v3.0.0.",
            DeprecationWarning,
            stacklevel=2
        )
        from the_alchemiser.shared.errors.context import ErrorContextData as _ErrorContextData
        return _ErrorContextData
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
```

**Recommended Approach**: Option B (backward compatible) to avoid breaking existing code immediately. Schedule removal for v3.0.0.

**Justification**:
- Follows semantic versioning (MAJOR for breaking changes)
- Gives consumers time to migrate
- Aligns with deprecation notice in `errors.py`

---

### Priority 2: Medium (Should Fix)

#### Fix 2: Sort __all__ exports alphabetically

**Problem**: The 58 exports in `__all__` are not alphabetically sorted, making maintenance difficult.

**Fix**:
```python
__all__ = [
    "AccountMetrics",
    "AccountSummary",
    "AllocationComparison",
    "ASTNode",
    "AssetInfo",
    "BuyingPowerResult",
    "Configuration",
    "ConsolidatedPortfolio",
    "EnrichedAccountSummaryView",
    "Error",
    "ErrorContextData",  # Or remove per Fix 1
    "ErrorDetailInfo",
    "ErrorNotificationData",
    "ErrorReportSummary",
    "ErrorSummaryData",
    "ExecutedOrder",
    "ExecutionReport",
    "ExecutionResult",
    "ExecutionStatus",
    "ExecutionSummary",
    "IndicatorRequest",
    "LambdaEvent",
    "MarketBar",
    "MarketData",
    "MarketStatusResult",
    "MultiStrategyExecutionResult",
    "MultiStrategySummary",
    "MultiSymbolQuotesResult",
    "OrderAction",
    "OrderExecutionResult",
    "OrderRequest",
    "OrderResultSummary",
    "PnLData",
    "PortfolioAllocationResult",
    "PortfolioMetrics",
    "PortfolioState",
    "Position",
    "PriceHistoryResult",
    "PriceResult",
    "RebalancePlan",
    "RebalancePlanItem",
    "Result",
    "RiskMetricsResult",
    "SpreadAnalysisResult",
    "StrategyAllocation",
    "StrategySignal",
    "TechnicalIndicator",
    "Trace",
    "TraceEntry",
    "TradeEligibilityResult",
    "TradeLedger",
    "TradeLedgerEntry",
    "TradeRunResult",
    "TradingMode",
    "WebSocketResult",
    "WebSocketStatus",
    "create_failure_result",
    "create_success_result",
]
```

**Justification**: 
- Easier to spot missing/duplicate exports
- Consistent with style guides (PEP 8)
- Matches pattern in other reviewed modules

---

### Priority 3: Low (Nice to Have)

#### Fix 3: Add tests for __init__.py

**Problem**: No tests verify that all exports are importable and that `__all__` is complete.

**Create**: `tests/shared/schemas/test_init.py`
```python
#!/usr/bin/env python3
"""Tests for shared.schemas.__init__.py package exports."""

import pytest

def test_all_exports_are_importable():
    """Verify all items in __all__ can be imported."""
    from the_alchemiser.shared import schemas
    
    for name in schemas.__all__:
        assert hasattr(schemas, name), f"{name} listed in __all__ but not importable"

def test_no_missing_exports():
    """Verify all public symbols are in __all__."""
    from the_alchemiser.shared import schemas
    
    # Get all public symbols (not starting with _)
    public_symbols = [name for name in dir(schemas) if not name.startswith('_')]
    
    # Check each is in __all__
    for symbol in public_symbols:
        assert symbol in schemas.__all__, f"{symbol} is public but not in __all__"

def test_all_is_sorted():
    """Verify __all__ is alphabetically sorted."""
    from the_alchemiser.shared import schemas
    
    sorted_all = sorted(schemas.__all__)
    assert schemas.__all__ == sorted_all, "__all__ should be alphabetically sorted"

def test_module_docstring():
    """Verify module has proper docstring with business unit."""
    from the_alchemiser.shared import schemas
    
    assert schemas.__doc__ is not None, "Module should have docstring"
    assert "Business Unit:" in schemas.__doc__, "Docstring should have Business Unit header"
    assert "shared" in schemas.__doc__, "Business Unit should be 'shared'"
```

---

## 7) Verification Results

### Linting

**Command**: `make format && make type-check`

**Status**: ⚠️ Will need verification after fixes (dependency installation required)

**Expected Issues**:
- Mypy will catch the missing `ErrorContextData` import when strict mode is enabled
- Ruff should pass (no code smells, only imports)

### Type Checking

**Command**: `mypy --config-file=pyproject.toml the_alchemiser/shared/schemas/__init__.py`

**Expected Result**: Will fail due to `ErrorContextData` not being imported

### Import Boundaries

**Command**: `poetry run importlinter --config pyproject.toml`

**Status**: Should pass (no cross-module violations in facade)

---

## 8) Conclusion

**Overall Assessment**: ⚠️ **NEEDS FIXES - Institution Grade Potential**

This file demonstrates **good software engineering practices** for a Python package facade with **one critical flaw**:

**Strengths** ✅:
1. ✅ Clear single responsibility (package API aggregation)
2. ✅ Comprehensive exports (58 schemas from 25 submodules)
3. ✅ All source modules use Pydantic v2 with strict validation
4. ✅ No security issues (static imports only)
5. ✅ Proper module size (142 lines, well under limit)
6. ✅ Business unit header present in docstring

**Critical Issues** 🔴:
1. 🔴 **Broken export**: `ErrorContextData` in `__all__` but not imported (will cause AttributeError)

**Medium Issues** ⚠️:
1. ⚠️ `__all__` not alphabetically sorted (maintainability)
2. ⚠️ No tests for export correctness

**Recommendations**:

**Immediate** (Required for compliance):
1. 🔴 Fix `ErrorContextData` export (choose backward compatible or breaking change approach)
2. ⚠️ Sort `__all__` alphabetically

**Short-term** (Before next release):
3. Add comprehensive tests for `__init__.py` (verify exports, imports, no circular deps)
4. Bump version according to semantic versioning (MAJOR if breaking, MINOR if backward compatible)

**Long-term** (Future optimization):
5. Consider lazy loading for performance optimization
6. Profile import time and optimize if needed
7. Consider splitting into category-specific facades

**Recommendation**: 🔴 **REQUIRES FIXES - NOT PRODUCTION READY**

The critical `ErrorContextData` export issue must be resolved before this module can be considered production-ready. Once fixed and tested, this module will meet institution-grade standards.

---

**Auto-generated**: 2025-01-06  
**Reviewer**: GitHub Copilot AI Agent  
**Next Review**: After fixes are implemented and verified
