# [File Review] Financial-grade, line-by-line audit

> Purpose: Conduct a rigorous, line-by-line review of a single Python file in the trading system, to institution-grade standards (correctness, controls, auditability, and safety). One issue per file.

---

## 0) Metadata

**File path**: `the_alchemiser/shared/services/tick_size_service.py`

**Commit SHA / Tag**: `802cf268358e3299fb6b80a4b7cf3d4bda2994f4`

**Reviewer(s)**: Josh, GitHub Copilot

**Date**: 2025-01-07

**Business function / Module**: shared/services

**Runtime context**: Synchronous service called during limit price calculations in order execution flow. No I/O operations. Pure computation based on price and symbol inputs.

**Criticality**: P2 (Medium) - Used in execution path for limit price calculations; incorrect tick sizes could result in rejected orders or suboptimal fills.

**Direct dependencies (imports)**:
```
Internal: None (standalone service)
External: decimal.Decimal (Python stdlib)
```

**External services touched**:
```
None - Pure computation service with no external I/O
```

**Interfaces (DTOs/events) produced/consumed**:
```
Consumed: symbol (str), price (Decimal)
Produced: tick_size (Decimal)
Used by: trading_math.calculate_dynamic_limit_price_with_symbol via TickSizeProvider protocol
```

**Related docs/specs**:
- [Copilot Instructions](/.github/copilot-instructions.md)
- [Trading Math Module](the_alchemiser/shared/math/trading_math.py)
- [Market Data Migration Guide](docs/file_reviews/market_data_adapter_MIGRATION_GUIDE.md)

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
None - No critical issues found

### High
1. **Missing tests** - No test coverage for TickSizeService despite being used in execution path
2. **Missing input validation** - No validation for negative or zero prices, which could cause logic errors

### Medium
1. **Missing docstring completeness** - Class docstring doesn't document public methods, pre/post-conditions, or failure modes
2. **Missing error handling** - No explicit error handling for edge cases (None, negative, NaN, infinity)
3. **Missing observability** - No logging for service usage or edge cases
4. **Incomplete implementation** - Comments acknowledge symbol-specific logic is not implemented (line 29-31)

### Low
1. **Parameter naming** - Leading underscore on `_symbol` parameter suggests unused parameter (line 16, 20)
2. **Missing type annotation** - Return type could benefit from explicit documentation of precision expectations

### Info/Nits
1. **Alias naming** - `DynamicTickSizeService` alias (line 41) suggests future extensibility but current implementation is static
2. **Magic numbers** - Hardcoded tick size values (lines 33, 35, 37) could be named constants for clarity
3. **Module size** - File is very small (41 lines), well under limits

---

## 3) Line-by-Line Notes

### Detailed Line-by-Line Analysis

| Line(s) | Issue / Observation | Severity | Evidence / Excerpt | Proposed Action |
|---------|---------------------|----------|-------------------|-----------------|
| 1 | ✅ Module header present and correct | Info | `"""Business Unit: shared \| Status: current.` | No action - compliant |
| 3-5 | ✅ Clear module docstring | Info | Describes purpose adequately | No action - compliant |
| 8 | ✅ Future annotations import | Info | Enables forward references | No action - compliant |
| 10 | ✅ Decimal import for financial precision | Info | Correctly uses Decimal for money | No action - compliant |
| 13-14 | ⚠️ Class docstring minimal | Medium | Only one-line description, no method documentation | Add comprehensive docstring with public API, pre/post-conditions, examples |
| 16 | ⚠️ Leading underscore on parameter | Low | `_symbol: str` suggests unused parameter | Either use symbol or document why it's reserved for future use |
| 16 | ❌ Missing input validation | High | No check for None, negative, zero, NaN, infinity | Add input validation with appropriate exceptions |
| 17 | ✅ Good docstring structure | Info | Clear Args/Returns sections | No action - compliant |
| 20 | ℹ️ Parameter documented as unused | Info | "currently unused, using simple price-based rules" | Acceptable for phase 1; document future plans |
| 27-31 | ℹ️ Implementation notes | Info | Comments document future requirements | Acceptable - shows awareness of limitations |
| 33 | ❌ No validation for edge case | High | `if price < Decimal("1.00")` - what if price is 0 or negative? | Add validation before this check |
| 33, 35, 37 | ℹ️ Magic numbers | Low | Hardcoded "1.00", "0.0001", "0.01" | Consider named constants: DOLLAR_THRESHOLD, SUB_DOLLAR_TICK, PENNY_TICK |
| 33-35 | ✅ Correct Decimal usage | Info | String literals for Decimal construction | No action - follows best practices |
| 37 | ✅ Default return value | Info | Penny increment is reasonable default | No action - compliant |
| 41 | ℹ️ Backward compatibility alias | Info | `DynamicTickSizeService = TickSizeService` | Document when this alias can be removed |
| All | ❌ No test coverage | High | No tests found in tests/shared/services/ | Create comprehensive test suite |
| All | ⚠️ No error handling | Medium | No try/except or explicit error paths | Add error handling for invalid inputs |
| All | ⚠️ No logging/observability | Medium | No structured logging | Add logging for edge cases and validation failures |

---

## 4) Correctness & Contracts

### Correctness Checklist

- [x] The file has a **clear purpose** and does not mix unrelated concerns (SRP)
  - ✅ Single responsibility: Provide tick sizes for trading calculations
- [x] Public functions/classes have **docstrings** with inputs/outputs
  - ⚠️ Has docstrings but missing pre/post-conditions and failure modes
- [x] **Type hints** are complete and precise (no `Any` in domain logic; use `Literal/NewType` where helpful)
  - ✅ Complete type hints for all parameters and returns
- [x] **DTOs** are **frozen/immutable** and validated (e.g., Pydantic v2 models with constrained types)
  - ✅ N/A - No DTOs, pure function service
- [x] **Numerical correctness**: currency uses `Decimal`; floats use `math.isclose` or explicit tolerances; no `==`/`!=` on floats
  - ✅ Uses Decimal correctly for tick sizes
  - ✅ Uses Decimal comparison (`<`) which is safe
- [ ] **Error handling**: exceptions are narrow, typed (from `shared.errors`), logged with context, and never silently caught
  - ❌ No error handling present - should validate inputs
- [x] **Idempotency**: handlers tolerate replays; side-effects are guarded by idempotency keys or checks
  - ✅ Pure function, no side effects, naturally idempotent
- [x] **Determinism**: tests freeze time (`freezegun`), seed RNG; no hidden randomness in business logic
  - ✅ Fully deterministic - no randomness, no time dependencies
- [x] **Security**: no secrets in code/logs; input validation at boundaries; no `eval`/`exec`/dynamic imports
  - ⚠️ Missing input validation at boundary (should validate price parameter)
  - ✅ No secrets, eval, exec, or dynamic imports
- [ ] **Observability**: structured logging with `correlation_id`/`causation_id`; one log per state change; no spam in hot loops
  - ❌ No logging present - should log validation failures and edge cases
- [ ] **Testing**: public APIs have tests; property-based tests for maths; coverage ≥ 80% (≥ 90% for strategy/portfolio)
  - ❌ No tests present - critical gap
- [x] **Performance**: no hidden I/O in hot paths; vectorised Pandas ops; HTTP clients pooled with rate limits
  - ✅ No I/O, pure computation, fast operation
- [x] **Complexity**: cyclomatic ≤ 10, cognitive ≤ 15, functions ≤ 50 lines, params ≤ 5
  - ✅ Cyclomatic complexity: 2 (very simple)
  - ✅ Function lines: ~22 lines
  - ✅ Parameters: 3 (self, symbol, price)
- [x] **Module size**: ≤ 500 lines (soft), split if > 800
  - ✅ 41 lines total
- [x] **Imports**: no `import *`; stdlib → third-party → local; no deep relative imports
  - ✅ Clean imports, correct order

### Compliance Summary

**Satisfied**: 11/15 checklist items (73%)

**Gaps**:
1. Error handling (High priority)
2. Input validation (High priority)
3. Testing coverage (High priority)
4. Observability/logging (Medium priority)

---

## 5) Additional Notes

### Architecture & Design

**Purpose**: TickSizeService provides the minimum price increment (tick size) for a given trading symbol at a specific price point. This is critical for limit order pricing to ensure orders are placed at valid price points that the exchange will accept.

**Implementation Status**: Phase 1 - Simple price-based rules
- Current: Single threshold at $1.00
- Sub-dollar stocks: 0.0001 tick size (0.01 cents)
- Regular stocks: 0.01 tick size (1 cent)
- Future: Symbol-specific and market-specific rules

**Protocol Compliance**: 
- ✅ Implements `TickSizeProvider` protocol from `trading_math.py`
- ✅ Interface: `get_tick_size(symbol: str, price: Decimal) -> Decimal`
- ✅ Used via dependency injection in `calculate_dynamic_limit_price_with_symbol`

**Numerical Correctness**:
- ✅ Uses `Decimal` throughout for financial precision
- ✅ String literals for Decimal construction (no float conversion)
- ✅ Safe comparison operators on Decimal (< is well-defined)

### Known Limitations

1. **Simplified Implementation**: Comments (lines 27-31) acknowledge missing features:
   - No symbol-specific rules (e.g., ETF vs stock differences)
   - No price-tier rules (e.g., Nasdaq has different rules for different price ranges)
   - No market-specific rules (NYSE vs Nasdaq differences)
   
2. **Phase 1 Accuracy**: Current implementation may not reflect actual market tick size rules:
   - Actual sub-dollar rules vary by exchange and price tier
   - Some securities have nickel or dime tick sizes
   - Options and futures have different tick size rules

### Risk Assessment

**Execution Risk**: Medium
- Incorrect tick sizes could lead to rejected orders
- Orders may not execute at expected prices if tick size is wrong
- However, most modern stocks do use penny increments, so risk is limited

**Mitigation**:
1. Add comprehensive tests to validate current behavior
2. Add input validation to prevent invalid usage
3. Document known limitations clearly
4. Add logging to track edge cases in production

### Testing Requirements

Based on analysis of similar files (test_trading_math.py), tests should include:

1. **Unit Tests**:
   - Penny tick size for prices ≥ $1.00
   - Sub-penny tick size for prices < $1.00
   - Boundary cases (exactly $1.00, $0.99, $1.01)
   - Edge cases (very small prices, very large prices)
   - Decimal precision preservation
   
2. **Property-Based Tests** (Hypothesis):
   - Return value always positive
   - Return value is valid Decimal
   - Monotonicity properties (if needed)
   - Output precision matches input context
   
3. **Error Cases**:
   - Negative price (should raise ValueError)
   - Zero price (should raise ValueError)
   - None price (type system should prevent, but test runtime)
   - NaN/Infinity (should raise ValueError)

### Recommendations

#### High Priority (Must Fix)
1. **Add comprehensive test suite** - See testing requirements above
2. **Add input validation** - Validate price is positive, non-zero, finite Decimal
3. **Add error handling** - Raise typed exceptions from `shared.errors` for invalid inputs

#### Medium Priority (Should Fix)
4. **Add structured logging** - Log validation failures and edge cases
5. **Enhance class docstring** - Document public API, pre/post-conditions, examples
6. **Consider named constants** - Replace magic numbers with named constants

#### Low Priority (Nice to Have)
7. **Document symbol parameter** - Clarify it's reserved for future use
8. **Add usage examples** - Docstring examples showing typical usage
9. **Document alias lifecycle** - When can `DynamicTickSizeService` alias be removed?

### Performance Characteristics

- **Time Complexity**: O(1) - Single conditional check
- **Space Complexity**: O(1) - No allocations
- **Hot Path**: Yes - Called during every limit order calculation
- **Optimization**: Already optimal - pure computation with minimal branching

### Integration Points

**Upstream Dependencies**: None - standalone service

**Downstream Consumers**:
1. `trading_math.calculate_dynamic_limit_price_with_symbol` - Primary consumer
2. Injected via `TickSizeProvider` protocol for testability

**Event Flow**: None - synchronous function call

### Compliance with Alchemiser Guardrails

#### ✅ Satisfied
- [x] Module has Business Unit header
- [x] Uses Decimal for financial calculations (no float comparisons)
- [x] Type hints are complete
- [x] Module size well under limits (41 lines)
- [x] Function complexity low (cyclomatic = 2)
- [x] Imports follow stdlib → third-party → local order
- [x] No security issues (no secrets, eval, exec)
- [x] Pure computation, no hidden I/O
- [x] Naturally deterministic and idempotent

#### ❌ Gaps
- [ ] **Testing**: No tests present (High priority)
- [ ] **Error handling**: No validation or error handling (High priority)
- [ ] **Observability**: No structured logging (Medium priority)
- [ ] **Docstrings**: Missing pre/post-conditions and failure modes (Medium priority)

---

**Audit completed**: 2025-01-07  
**Auditor**: GitHub Copilot  
**Status**: Review complete - Recommendations documented
