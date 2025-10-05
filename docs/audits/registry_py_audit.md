# [File Review] Financial-grade, line-by-line audit

> Purpose: Conduct a rigorous, line-by-line review of a single Python file in the trading system, to institution-grade standards (correctness, controls, auditability, and safety). One issue per file.

---

## 0) Metadata

**File path**: `the_alchemiser/strategy_v2/core/registry.py`

**Commit SHA / Tag**: `802cf268358e3299fb6b80a4b7cf3d4bda2994f4`

**Reviewer(s)**: GitHub Copilot

**Date**: 2025-01-10

**Business function / Module**: strategy_v2 / core

**Runtime context**: 
- Synchronous module initialization (global registry instantiation)
- Strategy registration happens at module import time
- Accessed during strategy orchestration workflow
- No direct I/O operations
- Used in both paper and live trading modes

**Criticality**: P1 (High) - Core infrastructure for strategy engine management

**Direct dependencies (imports)**:
```
Internal: 
  - the_alchemiser.shared.schemas.strategy_allocation.StrategyAllocation
  - the_alchemiser.shared.types.market_data_port.MarketDataPort

External:
  - typing.Protocol (stdlib)
  - datetime.datetime (stdlib)
```

**External services touched**: None (pure in-memory registry)

**Interfaces (DTOs/events) produced/consumed**:
```
Consumed: None directly
Produced: StrategyEngine instances (Protocol)
Returns: StrategyAllocation (DTO v1.0)
```

**Related docs/specs**:
- [Copilot Instructions](../../.github/copilot-instructions.md)
- [Strategy V2 README](../../the_alchemiser/strategy_v2/README.md)

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
1. **Missing typed exception**: Using stdlib `KeyError` instead of module-specific error from `strategy_v2.errors` - violates error handling guidelines
2. **No thread safety**: Global registry `_registry` accessed without locks - potential race conditions in concurrent environments
3. **Missing structured logging**: No observability for registry operations (register, get, list) - violates observability requirements

### High
1. **Missing correlation_id support**: Registry operations cannot be traced in event-driven workflow
2. **Weak validation**: `strategy_id` accepts any string - no format validation, length limits, or sanitization
3. **Protocol validation**: No runtime check that `engine` actually implements `StrategyEngine` protocol correctly
4. **Missing docstring details**: Module-level functions lack "Raises" sections and examples

### Medium
1. **Global mutable state**: Global `_registry` instance is anti-pattern - no clear lifecycle management or cleanup
2. **Error message context**: `KeyError` message could include more diagnostic context (caller, timestamp)
3. **Missing idempotency check**: `register()` silently overwrites existing strategies - no warning or error
4. **Type hint precision**: `dict[str, datetime | MarketDataPort]` union could be more specific with `TypedDict` or dataclass

### Low
1. **Import organization**: Relative import `...shared.types` could use absolute path for clarity
2. **Module docstring**: Could be more specific about thread safety, lifecycle, and singleton behavior
3. **Function parameter names**: `strategy_id` vs `engine` - consider more descriptive names like `strategy_identifier`

### Info/Nits
1. Line count (86 lines) is well within guidelines (target ≤ 500)
2. Function size (all < 15 lines) is excellent (target ≤ 50)
3. Cyclomatic complexity low (≤ 3 per function, target ≤ 10)
4. No dead code detected
5. Type hints present and mostly precise

---

## 3) Line-by-Line Notes

### Detailed Line-by-Line Analysis

| Line(s) | Issue / Observation | Severity | Evidence / Excerpt | Proposed Action |
|---------|---------------------|----------|-------------------|-----------------|
| 1-8 | Module docstring is accurate but lacks thread safety and lifecycle warnings | Low | `"""Strategy registry for mapping strategy names to callables."""` | Add notes about global mutable state and thread safety |
| 10-17 | Imports are clean and organized; relative import acceptable | Info | `from ...shared.types.market_data_port` | No action needed (acceptable per guidelines) |
| 20-27 | StrategyEngine Protocol definition is clear but lacks validation | High | No runtime check that implementers are correct | Add note about `isinstance()` checks or `runtime_checkable` |
| 24 | Context parameter union is broad | Medium | `datetime \| MarketDataPort \| dict[str, ...]` | Consider TypedDict for dict variant |
| 30-35 | Class initialization is simple and correct | Info | `self._strategies: dict[str, StrategyEngine] = {}` | No action needed |
| 37-45 | `register()` lacks validation, logging, and overwrite protection | Critical/High | Silent overwrite, no logging, weak validation | Add validation, logging, optional overwrite check |
| 45 | Silent overwrite of existing strategy | Medium | `self._strategies[strategy_id] = engine` | Add optional `allow_overwrite` parameter or warning |
| 47-63 | `get_strategy()` uses stdlib KeyError | Critical | `raise KeyError(f"Strategy '{strategy_id}'...")` | Use typed exception from `strategy_v2.errors` |
| 60-62 | Error message is good but could have more context | Medium | Missing timestamp, caller info | Add correlation_id parameter, structured logging |
| 65-67 | `list_strategies()` is simple and correct | Info | Returns copy of keys | No action needed |
| 70-71 | Global registry instance - no thread safety | Critical | `_registry = StrategyRegistry()` | Add threading.Lock or document single-threaded assumption |
| 74-76 | Module function lacks correlation_id tracking | High | No observability parameter | Add optional correlation_id parameter |
| 74-76 | Missing "Raises" in docstring | High | Only has brief description | Document potential exceptions |
| 79-81 | Missing "Raises" in docstring | High | Only has brief description | Document KeyError → typed exception |
| 84-86 | Simple delegation is correct | Info | Clean wrapper pattern | No action needed |
| All | No structured logging anywhere | Critical | No import of `shared.logging` | Add structured logging for all operations |
| All | No tests found | Critical | No `tests/strategy_v2/core/test_registry.py` | Create comprehensive test suite |

---

## 4) Correctness & Contracts

### Correctness Checklist

- [x] The file has a **clear purpose** and does not mix unrelated concerns (SRP) - ✅ Registry-only responsibility
- [x] Public functions/classes have **docstrings** with inputs/outputs - ⚠️ Missing "Raises" sections and examples
- [x] **Type hints** are complete and precise - ⚠️ Some unions could be more specific
- [x] **DTOs** are **frozen/immutable** and validated - N/A (no DTOs defined here)
- [x] **Numerical correctness** - N/A (no numerical operations)
- [ ] **Error handling**: exceptions are narrow, typed (from `shared.errors`) - ❌ Uses stdlib KeyError
- [ ] **Idempotency**: handlers tolerate replays - ⚠️ Register has no overwrite protection
- [x] **Determinism**: tests freeze time - N/A (no time-dependent behavior)
- [x] **Security**: no secrets in code/logs - ✅ No secrets
- [ ] **Observability**: structured logging with `correlation_id` - ❌ Missing entirely
- [ ] **Testing**: public APIs have tests - ❌ No test file found
- [x] **Performance**: no hidden I/O in hot paths - ✅ Pure in-memory operations
- [x] **Complexity**: cyclomatic ≤ 10, cognitive ≤ 15 - ✅ Very low complexity
- [x] **Module size**: ≤ 500 lines - ✅ Only 86 lines
- [x] **Imports**: no `import *` - ✅ Clean imports

### Summary Score: 9/15 ✅ | 4/15 ⚠️ | 2/15 ❌

---

## 5) Additional Notes

### Architecture Observations

1. **Design Pattern**: The module uses a classic Registry pattern with a global singleton instance. This is appropriate for strategy engine management but should be documented more clearly.

2. **Thread Safety Concerns**: While the codebase shows minimal threading usage (only in DSL engine), the global registry could be accessed concurrently. Should either:
   - Add explicit thread safety with `threading.Lock`
   - Document assumption of single-threaded access
   - Consider using `threading.local()` if per-thread registries are needed

3. **Lifecycle Management**: The global `_registry` is created at module import time and never cleaned up. This is acceptable for a singleton but should be documented.

4. **Protocol Usage**: The `StrategyEngine` Protocol is well-defined but not marked as `@runtime_checkable`. Consider adding this decorator to enable `isinstance()` checks.

### Recommended Improvements Priority Order

**P0 (Must Fix - Blocking Issues)**:
1. Add typed exception class `StrategyRegistryError` to `strategy_v2/errors.py`
2. Replace `KeyError` with typed exception
3. Add structured logging to all operations
4. Create comprehensive test suite

**P1 (Should Fix - High Priority)**:
1. Add thread safety (Lock) or document single-threaded assumption
2. Add correlation_id parameter to all public functions
3. Add validation for strategy_id (format, length, characters)
4. Add "Raises" sections to all docstrings
5. Add runtime validation for Protocol implementation

**P2 (Nice to Have - Medium Priority)**:
1. Add overwrite protection/warning in `register()`
2. Consider more specific type for context parameter
3. Add examples to docstrings
4. Enhance error messages with more context

**P3 (Polish - Low Priority)**:
1. Update module docstring with lifecycle details
2. Consider absolute imports instead of relative
3. Add mypy strict mode checks

### Testing Recommendations

Create `tests/strategy_v2/core/test_registry.py` with:

1. **Basic functionality tests**:
   - Register and retrieve strategy
   - List strategies
   - Multiple registrations

2. **Error handling tests**:
   - Get non-existent strategy
   - Register with invalid strategy_id
   - Register with non-Protocol object

3. **Thread safety tests** (if adding locks):
   - Concurrent registrations
   - Concurrent reads
   - Mixed read/write

4. **Property-based tests** (Hypothesis):
   - Register arbitrary valid strategy_ids
   - Invariant: get(id) after register(id, engine) returns engine
   - Invariant: id in list_strategies() after register(id, ...)

5. **Edge cases**:
   - Empty string strategy_id
   - Very long strategy_id
   - Special characters in strategy_id
   - Register with None or invalid types

---

**Audit completed**: 2025-01-10  
**Auditor**: GitHub Copilot  
**File version**: 86 lines, commit 802cf268
