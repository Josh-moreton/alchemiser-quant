# [File Review] Financial-grade, line-by-line audit

> Purpose: Conduct a rigorous, line-by-line review of a single Python file in the trading system, to institution-grade standards (correctness, controls, auditability, and safety). One issue per file.

---

## 0) Metadata

**File path**: `the_alchemiser/strategy_v2/core/registry.py`

**Commit SHA / Tag**: `main` (current HEAD)

**Reviewer(s)**: AI Code Review Agent

**Date**: 2025-01-23

**Business function / Module**: strategy_v2

**Runtime context**: Registry pattern for strategy engine management; used during strategy initialization and orchestration

**Criticality**: P1 (High) - Core infrastructure for strategy system

**Direct dependencies (imports)**:
```
Internal: 
- the_alchemiser.shared.schemas.strategy_allocation.StrategyAllocation
- the_alchemiser.shared.types.market_data_port.MarketDataPort

External: 
- typing.Protocol (stdlib)
- datetime.datetime (stdlib)
- __future__.annotations (stdlib)
```

**External services touched**:
```
None directly - acts as in-memory registry
```

**Interfaces (DTOs/events) produced/consumed**:
```
Produced: None (registry operations)
Consumed: StrategyAllocation (type hint only)
Protocol: StrategyEngine (Protocol definition for engine implementations)
```

**Related docs/specs**:
- [Copilot Instructions](/.github/copilot-instructions.md)
- [Strategy V2 Module README](/the_alchemiser/strategy_v2/README.md)
- Module boundary rules in Copilot Instructions

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
None identified

### High
1. **Missing error type from shared.errors** - Registry uses stdlib `KeyError` instead of typed errors from `the_alchemiser.strategy_v2.errors`
2. **No observability/logging** - Registry operations have zero logging for registration, retrieval, or errors
3. **No validation of strategy_id format** - Accepts any string including empty strings after strip (if not caught)
4. **Thread safety not addressed** - Global mutable registry without synchronization primitives for concurrent access

### Medium
1. **Missing tests** - No dedicated test file for `registry.py` found in repository
2. **Protocol mismatch** - `StrategyEngine` Protocol in this file differs from `shared.types.strategy_protocol.StrategyEngine`
3. **Incomplete docstrings** - Missing examples, raises documentation, and pre/post-conditions
4. **No idempotency guards** - `register()` silently overwrites existing strategies without warning or error

### Low
1. **Global mutable state** - `_registry` is a module-level global that could be problematic for testing
2. **No unregister/clear methods** - Registry cannot remove strategies once registered
3. **list_strategies() returns mutable list** - Caller could accidentally modify keys

### Info/Nits
1. **Underscore prefix on global** - `_registry` follows Python convention correctly
2. **Module header present** - Correctly includes "Business Unit: strategy | Status: current"
3. **Type hints complete** - All functions properly typed

---

## 3) Line-by-Line Notes

### Detailed Line-by-Line Analysis

| Line(s) | Issue / Observation | Severity | Evidence / Excerpt | Proposed Action |
|---------|---------------------|----------|-------------------|-----------------|
| 1-8 | Module header and docstring present | ✓ Info | `"""Business Unit: strategy \| Status: current.` | None - compliant |
| 10 | Future annotations import | ✓ Info | `from __future__ import annotations` | None - best practice |
| 12-17 | Imports are organized correctly | ✓ Info | stdlib → internal, no wildcards | None - compliant |
| 15 | StrategyAllocation imported but only used in type hints | Info | Could be TYPE_CHECKING guard | Consider moving to TYPE_CHECKING block |
| 20-27 | StrategyEngine Protocol definition | High | Protocol differs from shared.types.strategy_protocol | **ACTION**: Use shared protocol or document why different |
| 24 | Protocol signature too broad | Medium | `context: datetime \| MarketDataPort \| dict[str, datetime \| MarketDataPort]` | Consider narrowing or documenting why union needed |
| 26-27 | Protocol method lacks docstring details | Medium | No Args/Returns/Raises documentation | Add comprehensive docstring |
| 30-67 | StrategyRegistry class | - | Core registry implementation | See detailed items below |
| 33-35 | __init__ method | ✓ Info | Simple initialization with empty dict | None - appropriate |
| 37-45 | register() method | High | No logging, no validation, no idempotency check | **ACTION**: Add logging, validate strategy_id, warn on overwrite |
| 38-42 | register() docstring | Medium | Missing Raises section | Document no exceptions raised, or add validation |
| 45 | Silent overwrite of existing strategies | Medium | `self._strategies[strategy_id] = engine` | **ACTION**: Add warning log or error on duplicate |
| 47-63 | get_strategy() method | High | Uses stdlib KeyError instead of typed error | **ACTION**: Raise StrategyV2Error subclass |
| 47-63 | get_strategy() method | High | No logging on retrieval or error | **ACTION**: Add structured logging |
| 60-62 | Error message includes available strategies | ✓ Info | Good UX - shows alternatives | None - keep |
| 65-67 | list_strategies() returns mutable list | Low | `return list(self._strategies.keys())` | Already returns copy - no issue |
| 70-71 | Global registry instance | High | No thread safety for concurrent access | **ACTION**: Add threading.Lock or document single-threaded assumption |
| 74-76 | Module-level register_strategy() | Medium | No logging wrapper | **ACTION**: Add correlation_id support and logging |
| 74-76 | register_strategy() missing docstring details | Medium | Minimal docstring | Add Args, Examples, and integration notes |
| 79-81 | Module-level get_strategy() | Medium | No logging wrapper | **ACTION**: Add logging |
| 79-81 | get_strategy() missing docstring details | Medium | Minimal docstring | Add Args, Returns, Raises, Examples |
| 84-86 | Module-level list_strategies() | Medium | No logging | Consider debug-level log |
| 84-86 | list_strategies() missing docstring details | Medium | Minimal docstring | Add Returns and Examples |
| Overall | Module size: 86 lines | ✓ Info | Well within 500 line limit | None |
| Overall | No cyclomatic complexity issues | ✓ Info | Simple methods, no branching complexity | None |
| Overall | No tests found | High | No `tests/strategy_v2/core/test_registry.py` | **ACTION**: Create comprehensive test suite |

---

## 4) Correctness & Contracts

### Correctness Checklist

- [x] The file has a **clear purpose** and does not mix unrelated concerns (SRP)
  - ✓ Single responsibility: Strategy engine registration and retrieval
- [x] Public functions/classes have **docstrings** with inputs/outputs, pre/post-conditions, and failure modes
  - ⚠️ Partial - docstrings exist but missing examples, raises, and detailed contract
- [x] **Type hints** are complete and precise (no `Any` in domain logic; use `Literal/NewType` where helpful)
  - ✓ All functions have type hints; no `Any` usage
- [x] **DTOs** are **frozen/immutable** and validated (e.g., Pydantic v2 models with constrained types)
  - ✓ StrategyAllocation is frozen per shared schema (not defined here)
- [x] **Numerical correctness**: currency uses `Decimal`; floats use `math.isclose` or explicit tolerances; no `==`/`!=` on floats
  - ✓ N/A - no numerical operations
- [ ] **Error handling**: exceptions are narrow, typed (from `shared.errors`), logged with context, and never silently caught
  - ❌ Uses stdlib `KeyError` instead of typed error from `strategy_v2.errors`
  - ❌ No logging of errors or operations
- [ ] **Idempotency**: handlers tolerate replays; side-effects are guarded by idempotency keys or checks
  - ⚠️ Registry allows silent overwrites - not idempotent by default
- [x] **Determinism**: tests freeze time (`freezegun`), seed RNG; no hidden randomness in business logic
  - ✓ N/A - no randomness or time dependencies
- [ ] **Security**: no secrets in code/logs; input validation at boundaries; no `eval`/`exec`/dynamic imports
  - ⚠️ No input validation on strategy_id (could be empty, very long, contain special chars)
- [ ] **Observability**: structured logging with `correlation_id`/`causation_id`; one log per state change; no spam in hot loops
  - ❌ Zero logging in entire file
- [ ] **Testing**: public APIs have tests; property-based tests for maths; coverage ≥ 80% (≥ 90% for strategy/portfolio)
  - ❌ No dedicated test file found
- [x] **Performance**: no hidden I/O in hot paths; vectorised Pandas ops; HTTP clients pooled with rate limits
  - ✓ Pure in-memory operations, no I/O
- [x] **Complexity**: cyclomatic ≤ 10, cognitive ≤ 15, functions ≤ 50 lines, params ≤ 5
  - ✓ All functions simple, < 10 lines each
- [x] **Module size**: ≤ 500 lines (soft), split if > 800
  - ✓ 86 lines total
- [x] **Imports**: no `import *`; stdlib → third-party → local; no deep relative imports
  - ✓ Imports properly organized

**Overall Score: 11/15 (73%) - Needs improvement in error handling, observability, and testing**

---

## 5) Additional Notes

### Architecture Alignment

The registry follows a clean **Registry pattern** and serves as the central lookup for strategy engines. This aligns well with the event-driven architecture where strategies are decoupled from orchestration.

**Positive aspects:**
- Clear separation of concerns
- Protocol-based interface allows for flexible implementations
- No business logic leak - pure infrastructure pattern
- Module boundaries respected (uses shared types correctly)

**Areas for improvement:**

1. **Protocol Duplication**: There are two `StrategyEngine` protocols in the codebase:
   - `the_alchemiser/strategy_v2/core/registry.py` (this file)
   - `the_alchemiser/shared/types/strategy_protocol.py`
   
   These have different signatures and purposes. This should be documented or consolidated.

2. **Error Handling Strategy**: The Copilot Instructions mandate using typed errors from `shared.errors` or module-specific errors. The registry should raise `StrategyV2Error` subclasses (e.g., `StrategyNotFoundError`, `StrategyRegistrationError`).

3. **Observability Gap**: For a P1 critical component, having zero logging is a significant gap. At minimum:
   - Info-level log on strategy registration with strategy_id
   - Debug-level log on strategy retrieval
   - Error-level log with context when strategy not found

4. **Thread Safety**: The global registry uses mutable state without synchronization. If strategies can be registered dynamically at runtime (e.g., during system reconfiguration), race conditions are possible. Document the threading model or add locks.

5. **Testing Gap**: No dedicated tests found. Given this is core infrastructure, it should have:
   - Unit tests for all public methods
   - Tests for error conditions (strategy not found, empty registry)
   - Tests for edge cases (empty strategy_id, duplicate registration)
   - Integration tests showing registry usage in orchestrator

### Migration Context

The file is marked as `Status: current`, indicating it's part of the active v2 architecture. It's correctly used by:
- `the_alchemiser/strategy_v2/__init__.py` (lazy import via `__getattr__`)
- `the_alchemiser/strategy_v2/core/__init__.py` (direct export)

The lazy import pattern in `__init__.py` is good for avoiding circular dependencies, but it also means the registry might not be initialized until first use. This is acceptable for the current design.

### Recommendations (Priority Order)

**High Priority:**
1. Add typed errors (`StrategyNotFoundError` in `strategy_v2/errors.py`)
2. Add structured logging using `shared.logging.get_logger`
3. Create comprehensive test suite (`tests/strategy_v2/core/test_registry.py`)
4. Add thread safety (Lock) or document single-threaded assumption
5. Validate strategy_id input (non-empty, reasonable length)

**Medium Priority:**
6. Add warning log on duplicate registration or make it an error
7. Enhance docstrings with examples and detailed contracts
8. Resolve Protocol duplication or document the difference
9. Add correlation_id/causation_id support to module functions

**Low Priority:**
10. Consider adding `unregister()` and `clear()` methods for testing
11. Add `is_registered()` convenience method
12. Consider making registry immutable after initialization (freeze pattern)

### Compliance Summary

**Compliant with Copilot Instructions:**
- ✅ Module header format
- ✅ Single Responsibility Principle
- ✅ File size discipline (86 lines)
- ✅ Function size (all < 10 lines)
- ✅ Type hints complete
- ✅ No hardcoded values
- ✅ Import organization

**Non-Compliant with Copilot Instructions:**
- ❌ Error handling (uses stdlib exceptions, not typed errors)
- ❌ Observability (zero logging)
- ❌ Testing (no dedicated tests)
- ⚠️ Documentation (incomplete docstrings)
- ⚠️ Security (no input validation)

---

**Review Completed**: 2025-01-23
**Reviewed by**: AI Code Review Agent
**Total Issues Found**: 15 (0 Critical, 4 High, 5 Medium, 3 Low, 3 Info)
**Recommended Actions**: 12 specific improvements identified
