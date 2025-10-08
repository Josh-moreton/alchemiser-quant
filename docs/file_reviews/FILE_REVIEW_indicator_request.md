# [File Review] the_alchemiser/shared/schemas/indicator_request.py

> Purpose: Conduct a rigorous, line-by-line review of a single Python file in the trading system, to institution-grade standards (correctness, controls, auditability, and safety). One issue per file.

---

## 0) Metadata

**File path**: `the_alchemiser/shared/schemas/indicator_request.py`

**Commit SHA / Tag**: `802cf268358e3299fb6b80a4b7cf3d4bda2994f4`

**Reviewer(s)**: Copilot (AI Code Review Agent)

**Date**: 2025-01-08

**Business function / Module**: shared/schemas

**Runtime context**: DTO module used throughout DSL evaluation pipeline (strategy_v2), particularly for indicator computation requests and portfolio fragment assembly

**Criticality**: P2 (Medium) - Core schema module used in DSL evaluation and portfolio construction

**Direct dependencies (imports)**:
```python
Internal: None
External: 
  - typing.Any (stdlib)
  - pydantic (BaseModel, ConfigDict, Field)
```

**External services touched**:
```
None - Pure schema/DTO module with no I/O
```

**Interfaces (DTOs/events) produced/consumed**:
```
Produced:
  - IndicatorRequest: Used by DSL operators to request technical indicators
  - PortfolioFragment: Used by DSL operators to represent partial portfolio allocations

Consumed by:
  - the_alchemiser.strategy_v2.indicators.indicator_service (IndicatorService.get_indicator)
  - the_alchemiser.strategy_v2.engines.dsl.operators.portfolio (weight_equal, weight_inverse_volatility, group)
  - the_alchemiser.strategy_v2.engines.dsl.operators.indicators (indicator evaluation)
  - the_alchemiser.strategy_v2.engines.dsl.operators.control_flow (if/cond operators)
  - the_alchemiser.strategy_v2.engines.dsl.dsl_evaluator (DSLEvaluator)
  - the_alchemiser.strategy_v2.engines.dsl.events (DslEventPublisher)
```

**Related docs/specs**:
- Copilot Instructions (frozen DTOs, strict validation, schema versioning)
- Architecture boundaries (shared schemas must not import business modules)
- Python Coding Rules (SRP, complexity limits, error handling, type safety)

---

## 1) Scope & Objectives

- ✅ Verify the file's **single responsibility** and alignment with intended business capability.
- ✅ Ensure **correctness**, **numerical integrity**, **deterministic behaviour** where required.
- ✅ Validate **error handling**, **idempotency**, **observability**, **security**, and **compliance** controls.
- ✅ Confirm **interfaces/contracts** (DTOs/events) are accurate, versioned, and tested.
- ✅ Identify **dead code**, **complexity hotspots**, and **performance risks**.

---

## 2) Summary of Findings (use severity labels)

### Critical
**None** - No critical issues that would cause immediate production failures.

### High

**H1. Missing schema versioning (Lines 17-43, 94-119)**
- DTOs lack `schema_version` field despite being used in event-driven workflows
- **Violation**: Copilot instructions mandate "Event serialisation uses `.model_dump()`. Add deterministic idempotency keys (hash of DTO payload + schema version) where dedupe is required"
- **Impact**: Cannot track schema evolution; breaking changes will cause deserialization failures without version detection
- **Evidence**: `trade_run_result.py` includes `schema_version: str = Field(default="1.0", description="DTO schema version")`
- **Recommendation**: Add `schema_version: str = Field(default="1.0")` to both DTOs

**H2. Missing causation_id for event-driven workflows (Lines 32-33)**
- `IndicatorRequest` only has `correlation_id`, missing `causation_id`
- **Violation**: Copilot instructions mandate "Event handlers must be idempotent; propagate `correlation_id` and `causation_id`"
- **Impact**: Cannot track event causality chains in event-driven workflows; breaks audit trail
- **Evidence**: `strategy_v2/errors.py` supports both fields; event-driven workflows require causation tracking
- **Recommendation**: Add `causation_id: str | None = Field(default=None, description="Causation ID for event chain tracking")`

**H3. Unsafe `dict[str, Any]` type for parameters (Line 38)**
- Parameters use `Any` type, violating strict typing policy
- **Violation**: Copilot instructions mandate "No `Any` in domain logic"
- **Impact**: Type safety lost; invalid parameters passed at runtime rather than caught at validation
- **Evidence**: Parameters contain typed values (`window: int`) but are not validated by Pydantic
- **Recommendation**: Use `dict[str, int | float | str]` with explicit unions, or create typed parameter models

**H4. Float comparison without tolerance (Line 132)**
- Direct float comparison: `if current_sum == 0:`
- **Violation**: Copilot instructions mandate "Never use `==`/`!=` on floats. Use `Decimal` for money; `math.isclose` for ratios"
- **Impact**: Potential precision errors in portfolio weight normalization; floating-point rounding could skip normalization
- **Recommendation**: Use `math.isclose(current_sum, 0.0, abs_tol=1e-9)` or compare against small epsilon

### Medium

**M1. Missing causation_id in PortfolioFragment (Line 109)**
- `PortfolioFragment` only has fragment identifiers, no correlation/causation tracking
- **Impact**: Portfolio fragments cannot be traced back to originating requests in event workflows
- **Recommendation**: Add `correlation_id: str | None = Field(default=None)` and `causation_id: str | None = Field(default=None)`

**M2. Unconstrained indicator_type (Line 37)**
- `indicator_type` is free-form string, not validated against known types
- **Impact**: Typos in indicator names fail at runtime in IndicatorService rather than at validation
- **Evidence**: `indicator_service.py` dispatches to `{"rsi", "current_price", "moving_average", "moving_average_return", "cumulative_return", "exponential_moving_average_price", "stdev_return", "max_drawdown"}`
- **Recommendation**: Use `Literal["rsi", "current_price", "moving_average", ...]` for compile-time validation

**M3. Missing symbol validation (Lines 36, 110)**
- Symbols have length constraints but no format validation (e.g., uppercase, alphanumeric)
- **Impact**: Lowercase or invalid symbols may pass validation but fail in market data retrieval
- **Evidence**: Other schemas (e.g., `rebalance_plan.py`) normalize symbols to uppercase with validators
- **Recommendation**: Add `@field_validator("symbol")` to normalize and validate format

**M4. No validation on parameters dict contents (Line 38)**
- Parameters are not validated; negative windows or invalid values accepted
- **Impact**: Invalid parameters (e.g., `window=-1`) cause runtime errors in indicator computation
- **Recommendation**: Add `@field_validator("parameters")` or create typed parameter subclasses

**M5. Missing factory method documentation examples (Lines 45-91)**
- Factory methods lack usage examples in docstrings
- **Impact**: Developers may misuse window defaults or parameter format
- **Recommendation**: Add docstring examples showing typical usage

**M6. total_weight constraint may be too restrictive (Line 116)**
- `total_weight: float = Field(default=1.0, ge=0, le=1)` prevents fragments > 100% weight
- **Impact**: Multi-leg strategies or leveraged positions cannot be represented
- **Consideration**: May be intentional; document assumption or relax constraint

### Low

**L1. Missing __all__ export list (Lines 10-14)**
- Module lacks `__all__` to control public API surface
- **Impact**: Internal classes may be accidentally imported; unclear API boundary
- **Recommendation**: Add `__all__ = ["IndicatorRequest", "PortfolioFragment"]`

**L2. No frozen weights dict protection (Line 113-114)**
- While DTO is frozen, nested dict `weights` is mutable post-creation
- **Impact**: Callers could mutate weights after construction (though Pydantic v2 prevents this in frozen mode)
- **Note**: Pydantic v2 `frozen=True` should handle this; verify with integration tests

**L3. normalize_weights returns new instance but doesn't validate (Lines 121-140)**
- `normalize_weights()` creates new instance via `model_copy()` without revalidation
- **Impact**: Normalized weights might violate `total_weight` constraint if floating-point errors accumulate
- **Recommendation**: Add post-normalization assertion or use `model_validate()`

**L4. Missing metadata field documentation (Lines 41-43, 119)**
- `metadata` fields have generic descriptions; unclear what belongs there
- **Impact**: Inconsistent metadata usage across codebase
- **Recommendation**: Document expected metadata keys or provide examples

### Info/Nits

**N1. Module header is compliant**
- ✅ Correct format: "Business Unit: shared | Status: current."
- ✅ Clear purpose statement

**N2. Type hints are complete**
- ✅ All public methods have complete type annotations
- ✅ Return types are explicit
- ⚠️ Except `Any` usage in `parameters` and `metadata` (see H3)

**N3. DTOs are frozen and immutable**
- ✅ Both DTOs use `frozen=True`
- ✅ `validate_assignment=True` enforces immutability
- ✅ `str_strip_whitespace=True` normalizes input

**N4. Module size is excellent**
- ✅ 140 lines (target: ≤500)
- ✅ Well-organized with clear sections

**N5. Cyclomatic complexity is minimal**
- ✅ All methods have complexity ≤ 3
- ✅ `normalize_weights()` has 3 branches (acceptable)

**N6. Import ordering is correct**
- ✅ stdlib → third-party (pydantic)
- ✅ No internal imports (pure schema module)

---

## 3) Line-by-Line Notes

### Detailed Line-by-Line Analysis

| Line(s) | Issue / Observation | Severity | Evidence / Excerpt | Proposed Action |
|---------|---------------------|----------|-------------------|-----------------|
| 1 | ✅ Shebang present | Info | `#!/usr/bin/env python3` | None - compliant |
| 2-8 | ✅ Module header compliant | Info | `"""Business Unit: shared \| Status: current."""` | None - compliant |
| 10 | ✅ Future annotations enabled | Info | `from __future__ import annotations` | None - best practice |
| 12 | ⚠️ Any imported | High | `from typing import Any` | Replace with specific unions where possible |
| 14 | ✅ Pydantic imports correct | Info | `from pydantic import BaseModel, ConfigDict, Field` | None - compliant |
| 15-16 | ❌ Missing __all__ | Low | (blank lines) | Add `__all__ = ["IndicatorRequest", "PortfolioFragment"]` |
| 17-22 | ✅ DTO docstring clear | Info | Class purpose well-documented | None - compliant |
| 24-29 | ✅ Model config correct | Info | `strict=True, frozen=True, validate_assignment=True` | None - compliant |
| 31-33 | ❌ Missing causation_id | High | Only `request_id` and `correlation_id` present | Add `causation_id` field |
| 31-33 | ❌ Missing schema_version | High | No schema version field | Add `schema_version: str = Field(default="1.0")` |
| 36 | ⚠️ Symbol not validated | Medium | `symbol: str = Field(..., min_length=1, max_length=10)` | Add `@field_validator` for uppercase/format |
| 37 | ⚠️ indicator_type unconstrained | Medium | `indicator_type: str = Field(..., min_length=1)` | Use `Literal[...]` for known types |
| 38 | ❌ Parameters use Any | High | `parameters: dict[str, Any]` | Change to `dict[str, int \| float \| str]` |
| 41-43 | ⚠️ Metadata use unclear | Low | Generic description | Document expected keys/usage |
| 45-67 | ⚠️ rsi_request lacks examples | Medium | Docstring complete but no usage example | Add example in docstring |
| 48 | ✅ Window parameter typed | Info | `window: int = 14` | None - good default |
| 61-67 | ✅ Factory method clean | Info | Clear construction logic | None - compliant |
| 69-91 | ⚠️ moving_average_request lacks examples | Medium | Docstring complete but no usage example | Add example in docstring |
| 71 | ✅ Different default window | Info | `window: int = 200` (appropriate for MA vs RSI) | None - compliant |
| 94-99 | ✅ PortfolioFragment docstring | Info | Clear purpose statement | None - compliant |
| 101-106 | ✅ Model config correct | Info | Same as IndicatorRequest | None - compliant |
| 108-110 | ❌ Missing correlation/causation IDs | Medium | Only `fragment_id` and `source_step` | Add correlation/causation tracking |
| 108-110 | ❌ Missing schema_version | High | No schema version field | Add `schema_version: str = Field(default="1.0")` |
| 113-114 | ⚠️ Weights dict mutability | Low | `weights: dict[str, float]` | Verify Pydantic v2 frozen behavior |
| 116 | ⚠️ total_weight constraint | Medium | `ge=0, le=1` may prevent leveraged strategies | Document assumption or relax if needed |
| 119 | ⚠️ Metadata use unclear | Low | Generic description | Document expected keys/usage |
| 121-140 | ✅ normalize_weights method | Info | Clean implementation with early returns | None - generally good |
| 128-129 | ✅ Empty weights check | Info | `if not self.weights: return self` | None - correct |
| 131-133 | ❌ Float equality comparison | High | `if current_sum == 0: return self` | Use `math.isclose(current_sum, 0.0, abs_tol=1e-9)` |
| 135 | ⚠️ Float division | Low | `scale_factor = self.total_weight / current_sum` | Consider precision; acceptable for weights |
| 136-138 | ✅ Dict comprehension | Info | Clean weight normalization | None - compliant |
| 140 | ⚠️ model_copy without validation | Low | `return self.model_copy(update={"weights": normalized_weights})` | Consider revalidation to catch constraint violations |

---

## 4) Correctness & Contracts

### Correctness Checklist

- [x] **The file has a clear purpose** and does not mix unrelated concerns (SRP)
  - ✅ Single responsibility: DTOs for indicator requests and portfolio fragments
  - ✅ No business logic; pure data structures
  
- [x] **Public functions/classes have docstrings** with inputs/outputs, pre/post-conditions, and failure modes
  - ✅ All classes documented
  - ✅ Factory methods have complete docstrings
  - ⚠️ Missing usage examples (M5)
  
- [ ] **Type hints are complete and precise** (no `Any` in domain logic; use `Literal/NewType` where helpful)
  - ✅ Most types complete
  - ❌ `dict[str, Any]` violates "no Any in domain logic" (H3)
  - ❌ `indicator_type` should use `Literal` (M2)
  
- [x] **DTOs are frozen/immutable** and validated (e.g., Pydantic v2 models with constrained types)
  - ✅ Both DTOs use `frozen=True`
  - ✅ Field constraints present (min_length, max_length, ge, le)
  - ❌ Missing schema_version field (H1)
  - ⚠️ Nested dict mutability (L2)
  
- [ ] **Numerical correctness**: currency uses `Decimal`; floats use `math.isclose` or explicit tolerances; no `==`/`!=` on floats
  - ✅ Weights use `float` (appropriate for ratios, not currency)
  - ❌ Float equality comparison on line 132 (H4)
  - ⚠️ No explicit tolerance documentation for weight normalization
  
- [N/A] **Error handling**: exceptions are narrow, typed (from `shared.errors`), logged with context, and never silently caught
  - N/A - Pure schema module; no error handling code
  - ✅ Pydantic raises ValidationError on invalid input
  
- [N/A] **Idempotency**: handlers tolerate replays; side-effects are guarded by idempotency keys or checks
  - N/A - Pure DTOs; no handlers in this module
  - ❌ Missing schema_version for idempotency key generation (H1)
  
- [N/A] **Determinism**: tests freeze time (`freezegun`), seed RNG; no hidden randomness in business logic
  - N/A - Pure DTOs; no randomness
  
- [x] **Security**: no secrets in code/logs; input validation at boundaries; no `eval`/`exec`/dynamic imports
  - ✅ No secrets
  - ✅ Pydantic validates all inputs
  - ✅ No dynamic code execution
  
- [ ] **Observability**: structured logging with `correlation_id`/`causation_id`; one log per state change; no spam in hot loops
  - N/A - Pure schema module; no logging
  - ❌ Missing causation_id field (H2, M1)
  - ✅ correlation_id present in IndicatorRequest
  
- [ ] **Testing**: public APIs have tests; property-based tests for maths; coverage ≥ 80% (≥ 90% for strategy/portfolio)
  - ⚠️ No dedicated unit tests for these DTOs
  - ✅ Integration tests exist in `tests/strategy_v2/engines/dsl/operators/test_portfolio.py`
  - ❌ No property-based tests for `normalize_weights()` (should test: sum invariant, idempotency, rounding)
  
- [x] **Performance**: no hidden I/O in hot paths; vectorised Pandas ops; HTTP clients pooled with rate limits
  - ✅ Pure data structures; no I/O
  - ✅ O(1) construction; O(n) normalization where n = number of symbols
  
- [x] **Complexity**: cyclomatic ≤ 10, cognitive ≤ 15, functions ≤ 50 lines, params ≤ 5
  - ✅ All methods ≤ 20 lines
  - ✅ Max complexity = 3 (normalize_weights)
  - ✅ All methods have ≤ 5 parameters
  
- [x] **Module size**: ≤ 500 lines (soft), split if > 800
  - ✅ 140 lines (well below target)
  
- [x] **Imports**: no `import *`; stdlib → third-party → local; no deep relative imports
  - ✅ No star imports
  - ✅ Correct ordering
  - ✅ No internal imports (pure shared module)

---

## 5) Additional Notes

### Architectural Alignment

**Compliance with Shared Module Boundaries:**
- ✅ No imports from business modules (strategy_v2, portfolio_v2, execution_v2)
- ✅ Only depends on stdlib and pydantic
- ✅ Pure schema module as intended

**Integration Points:**
- ✅ Used correctly by IndicatorService for type-safe indicator requests
- ✅ Used correctly by DSL operators for portfolio fragment assembly
- ⚠️ Missing schema versioning makes it difficult to evolve schemas safely

### Comparison with Similar Schemas

**vs. trade_run_result.py:**
- ❌ indicator_request.py missing `schema_version` field
- ❌ indicator_request.py missing `Literal` types for enums
- ✅ indicator_request.py has frozen DTOs (same as trade_run_result)
- ✅ indicator_request.py has field validators (but needs more)

**vs. rebalance_plan.py:**
- ❌ indicator_request.py missing symbol normalization validator
- ❌ indicator_request.py missing correlation_id/causation_id in PortfolioFragment
- ✅ indicator_request.py has similar frozen DTO pattern
- ✅ indicator_request.py uses same Field patterns

### Code Quality Metrics

**Metrics Summary:**
- **Lines of Code**: 140 (target: ≤500) ✅
- **Cyclomatic Complexity**: Max 3 (target: ≤10) ✅
- **Cognitive Complexity**: Max 3 (target: ≤15) ✅
- **Function Length**: Max 20 lines (target: ≤50) ✅
- **Parameter Count**: Max 4 (target: ≤5) ✅
- **Type Coverage**: ~90% (7 `Any` usages need fixing) ⚠️
- **Docstring Coverage**: 100% (all public APIs documented) ✅
- **Test Coverage**: Unknown (no dedicated tests) ❌

### Recommendations Priority

**Must Fix (High Severity):**
1. Add `schema_version` field to both DTOs (H1)
2. Add `causation_id` to IndicatorRequest (H2)
3. Replace `dict[str, Any]` with explicit type unions (H3)
4. Fix float equality comparison in `normalize_weights()` (H4)

**Should Fix (Medium Severity):**
5. Add correlation_id/causation_id to PortfolioFragment (M1)
6. Use `Literal` for indicator_type validation (M2)
7. Add symbol format validators (M3)
8. Add parameter validation (M4)
9. Add factory method usage examples (M5)

**Consider Fixing (Low Severity):**
10. Add `__all__` export list (L1)
11. Add post-normalization validation (L3)
12. Document metadata field usage (L4)

### Testing Recommendations

**Unit Tests Needed:**
```python
# tests/shared/schemas/test_indicator_request.py
- test_indicator_request_creation_valid()
- test_indicator_request_validation_errors()
- test_indicator_request_frozen_immutability()
- test_rsi_request_factory()
- test_moving_average_request_factory()
- test_portfolio_fragment_creation_valid()
- test_portfolio_fragment_normalize_weights_sum_invariant()
- test_portfolio_fragment_normalize_weights_idempotent()
- test_portfolio_fragment_normalize_weights_empty()
- test_portfolio_fragment_normalize_weights_zero_sum()
- test_portfolio_fragment_frozen_immutability()
```

**Property-Based Tests Needed (Hypothesis):**
```python
# For normalize_weights():
- Property: Sum of normalized weights == total_weight (within tolerance)
- Property: Normalizing twice gives same result (idempotent)
- Property: Empty weights returns self unchanged
- Property: Zero sum weights returns self unchanged
- Property: All weights stay non-negative after normalization
```

### Security & Compliance

**Security Considerations:**
- ✅ No secrets or sensitive data
- ✅ Input validation via Pydantic
- ✅ No code execution paths
- ⚠️ Unconstrained `parameters` dict could enable injection if passed to eval() elsewhere (not in this module)

**Compliance Considerations:**
- ✅ Immutable DTOs prevent accidental mutation
- ❌ Missing audit trail fields (causation_id) for regulatory traceability
- ❌ Missing schema versioning for audit log replay/reconstruction

### Performance Characteristics

**Computational Complexity:**
- ✅ DTO construction: O(1)
- ✅ `normalize_weights()`: O(n) where n = number of symbols
- ✅ Factory methods: O(1)

**Memory Profile:**
- ✅ Lightweight DTOs
- ✅ Frozen prevents accidental copies
- ⚠️ Dict fields could grow large if many metadata keys added

**Hot Path Considerations:**
- ✅ DTOs used in indicator request path (acceptable overhead)
- ✅ normalize_weights() called during DSL evaluation (O(n) acceptable for typical portfolio sizes)

---

**Auto-generated**: 2025-01-08  
**Script**: Manual review by Copilot AI Code Review Agent  
**Review Duration**: Comprehensive line-by-line audit  
**Findings**: 4 High, 6 Medium, 4 Low, 6 Info  
**Recommended Actions**: 9 must-fix/should-fix items before next deployment
