# [File Review] order_like.py - Financial-grade, line-by-line audit

> Purpose: Conduct a rigorous, line-by-line review of a single Python file in the trading system, to institution-grade standards (correctness, controls, auditability, and safety). One issue per file.

---

## 0) Metadata

**File path**: `the_alchemiser/shared/protocols/order_like.py`

**Commit SHA / Tag**: `802cf268358e3299fb6b80a4b7cf3d4bda2994f4`

**Reviewer(s)**: Copilot (automated review)

**Date**: 2025-10-06

**Business function / Module**: shared/protocols (Protocol definitions)

**Runtime context**: Design-time protocol definition used across execution and portfolio modules for type safety

**Criticality**: P2 (Medium) - Shared protocol affecting order and position handling, but not directly trading logic

**Direct dependencies (imports)**:
```
Internal: None (standalone protocol definitions)
External: 
  - typing (Protocol, runtime_checkable)
  - __future__ (annotations)
```

**External services touched**:
```
None - Pure protocol definitions
```

**Interfaces (DTOs/events) produced/consumed**:
```
Defines: 
  - OrderLikeProtocol: Protocol for order-like objects
  - PositionLikeProtocol: Protocol for position-like objects
Consumed by:
  - Execution module (order normalization)
  - Portfolio module (position tracking)
  - Mapping functions (SDK object normalization)
Produces: N/A (protocol only)
```

**Related docs/specs**:
- Copilot Instructions (.github/copilot-instructions.md)
- Alpaca Architecture (docs/ALPACA_ARCHITECTURE.md)
- Related protocols: `alpaca.py`, `strategy_tracking.py`

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
None - Protocol definitions are structurally sound.

### High

1. **Overly permissive type hints for quantities** (Lines 34, 54, 75, 83)
   - `qty: float | int | str | None` allows string types without validation
   - `filled_qty: float | int | str | None` same issue
   - No guidance on when string vs numeric types should be used
   - **Impact**: Type safety is weakened; implementations may pass invalid string values
   - **Recommendation**: Document when strings are acceptable (e.g., SDK raw responses) and add validation examples

2. **Missing error handling documentation**
   - No documentation about what exceptions may be raised when accessing properties
   - No guidance on handling None values vs missing attributes
   - **Impact**: Implementers don't know when to expect failures
   - **Recommendation**: Add comprehensive error handling section to docstrings

3. **Loose type constraint on `side` parameter** (Lines 39, 69)
   - `side: str` allows any string, not just "buy" or "sell"
   - No validation contract specified
   - **Impact**: Invalid side values could propagate to broker APIs
   - **Recommendation**: Document expected values or use Literal["buy", "sell"] if appropriate

### Medium

1. **No test coverage**
   - Protocol has no dedicated test file
   - No validation that mock implementations conform to protocol
   - No runtime_checkable verification tests
   - **Impact**: Protocol violations not caught during development
   - **Recommendation**: Create `tests/shared/protocols/test_order_like.py`

2. **Minimal docstrings lack examples** (Lines 17-21, 60-65)
   - Class docstrings explain purpose but lack usage examples
   - No examples showing how to implement or use protocols
   - No examples of valid vs invalid implementations
   - **Impact**: Reduced developer experience, slower onboarding
   - **Recommendation**: Add comprehensive examples with both Alpaca SDK and domain objects

3. **Missing pre/post-conditions** (All property docstrings)
   - Property docstrings are single-line with no detail
   - No specification of valid value ranges or formats
   - No specification of None-handling behavior
   - **Impact**: Unclear contracts for implementers
   - **Recommendation**: Expand docstrings with constraints and behavior

4. **No version tracking for protocols**
   - Protocol interface could change over time
   - No mechanism to track protocol evolution
   - **Impact**: Breaking changes to protocol could affect multiple modules
   - **Recommendation**: Add version info to module docstring

### Low

1. **Generic property names** (Lines 24, 29, 68, 73)
   - `id` could conflict with Python built-in
   - `qty` abbreviation is less clear than `quantity`
   - **Impact**: Minor readability issue, but consistent with SDK naming
   - **Note**: Keeping consistent with Alpaca SDK is intentional design choice

2. **Inconsistent None-handling patterns**
   - Some properties allow None (id, order_type, status), others don't (symbol, side)
   - Pattern is implicit rather than documented
   - **Impact**: Unclear which fields are truly optional
   - **Recommendation**: Document optionality rationale

3. **PositionLikeProtocol qty doesn't allow None** (Line 75)
   - OrderLikeProtocol.qty allows None, PositionLikeProtocol.qty doesn't
   - Inconsistent design between related protocols
   - **Impact**: Slight confusion, but positions always have quantities
   - **Note**: Design is correct; document rationale

### Info/Nits

1. **Module docstring could be more detailed** (Lines 1-8)
   - Good structure and clarity
   - Could benefit from examples of when to use each protocol
   - Could document relationship with AlpacaOrderProtocol

2. **@runtime_checkable decorator** (Lines 15, 59)
   - Good: Enables isinstance() checks
   - Could document why runtime checking is needed

---

## 3) Line-by-Line Notes

### Detailed Line-by-Line Analysis

| Line(s) | Issue / Observation | Severity | Evidence / Excerpt | Proposed Action |
|---------|---------------------|----------|-------------------|-----------------|
| 1 | Module header | Info | `"""Business Unit: shared \| Status: current.` | ✅ Correct format per Copilot Instructions |
| 3-8 | Module docstring | Medium | Basic description, lacks examples | Add usage examples and relationship to other protocols |
| 10 | Future annotations import | Info | `from __future__ import annotations` | ✅ Good: Enables modern type hint syntax |
| 12 | Typing imports | Info | `from typing import Protocol, runtime_checkable` | ✅ Correct imports, minimal |
| 15 | @runtime_checkable decorator | Info | Enables isinstance() checks | ✅ Good for duck typing validation |
| 16 | OrderLikeProtocol class | Info | Main protocol definition | ✅ Clear naming |
| 17-21 | Class docstring | Medium | "Used in mapping functions..." | Expand with examples (Alpaca Order, domain entities, dicts) |
| 23-26 | `id` property | Low | `id: str \| None` | Document when None is acceptable (new orders?) |
| 28-31 | `symbol` property | Info | `symbol: str` (required) | ✅ Correct: always required |
| 33-36 | `qty` property | High | `qty: float \| int \| str \| None` | ⚠️ Over-permissive. Document string format expectations |
| 38-41 | `side` property | High | `side: str` | ⚠️ Should document expected values ("buy", "sell") or use Literal |
| 43-46 | `order_type` property | Low | `order_type: str \| None` | Document expected values ("market", "limit") |
| 48-51 | `status` property | Low | `status: str \| None` | Document possible status values |
| 53-56 | `filled_qty` property | High | `filled_qty: float \| int \| str \| None` | ⚠️ Same over-permissive issue as qty |
| 59 | @runtime_checkable | Info | Same as line 15 | ✅ Consistent usage |
| 60 | PositionLikeProtocol class | Info | Related protocol for positions | ✅ Clear naming |
| 61-65 | Class docstring | Medium | Basic description | Add examples of position sources (Alpaca, tracking) |
| 67-70 | `symbol` property | Info | Required field | ✅ Consistent with OrderLikeProtocol |
| 72-75 | `qty` property | Low | `qty: float \| int \| str` (no None) | Note: Intentionally different from Order (positions always have qty) |
| 77-80 | `market_value` property | Info | `market_value: float \| int \| str \| None` | Consistent with other monetary fields |
| 82-85 | `avg_entry_price` property | Info | `avg_entry_price: float \| int \| str \| None` | Consistent pattern |
| 85 | Empty line at EOF | Info | File ends with newline | ✅ POSIX compliance |

---

## 4) Correctness & Contracts

### Correctness Checklist

- [x] The file has a **clear purpose** and does not mix unrelated concerns (SRP)
  - ✅ Focused on defining minimal order and position protocols
  
- [x] Public functions/classes have **docstrings** with inputs/outputs
  - ⚠️ Docstrings present but minimal (single line per property)
  - ❌ Missing: examples, pre/post-conditions, valid value ranges
  
- [x] **Type hints** are complete and precise (no `Any` in domain logic; use `Literal/NewType` where helpful)
  - ⚠️ Type hints present but overly permissive
  - Issue: `float | int | str | None` weakens type safety
  - Could use: `Literal` for side/status, or document string formats
  
- [x] **DTOs** are **frozen/immutable** and validated
  - ⚠️ N/A for Protocol, but implementers should use frozen DTOs
  - Missing: Documentation that implementations should be immutable
  
- [x] **Numerical correctness**: currency uses `Decimal`; floats use `math.isclose` or explicit tolerances; no `==`/`!=` on floats
  - ⚠️ Protocols allow float, int, or str without guidance
  - Missing: Documentation on when to use each type
  - Missing: Guidance on Decimal usage for monetary values
  
- [ ] **Error handling**: exceptions are narrow, typed (from `shared.errors`), logged with context, and never silently caught
  - ❌ No error handling documentation
  - Missing: What exceptions property access may raise
  - Missing: How to handle None values
  
- [x] **Idempotency**: handlers tolerate replays; side-effects are guarded by idempotency keys or checks
  - ✅ N/A for protocols (read-only properties)
  
- [x] **Determinism**: tests freeze time (`freezegun`), seed RNG; no hidden randomness in business logic
  - ✅ N/A for protocols (no logic)
  
- [x] **Security**: no secrets in code/logs; input validation at boundaries; no `eval`/`exec`/dynamic imports
  - ✅ No security concerns (pure protocol)
  
- [x] **Observability**: structured logging with `correlation_id`/`causation_id`; one log per state change; no spam in hot loops
  - ✅ N/A for protocols (no logging)
  
- [ ] **Testing**: public APIs have tests; property-based tests for maths; coverage ≥ 80% (≥ 90% for strategy/portfolio)
  - ❌ No dedicated test file
  - Missing: Protocol conformance tests
  - Missing: Runtime checking validation
  
- [x] **Performance**: no hidden I/O in hot paths; vectorised Pandas ops; HTTP clients pooled with rate limits
  - ✅ N/A for protocols (no I/O)
  
- [x] **Complexity**: cyclomatic ≤ 10, cognitive ≤ 15, functions ≤ 50 lines, params ≤ 5
  - ✅ Protocols have no logic (complexity = 0)
  
- [x] **Module size**: ≤ 500 lines (soft), split if > 800
  - ✅ 85 lines (well under limit)
  
- [x] **Imports**: no `import *`; stdlib → third-party → local; no deep relative imports
  - ✅ Minimal, clean imports

### Specific Contract Issues

1. **Quantity Type Flexibility**
   - Current: `qty: float | int | str | None`
   - Rationale: Supports Alpaca SDK (returns strings), domain models (use Decimal/float), and dicts
   - Issue: No validation or documentation of string format
   - Recommendation: Document when strings are acceptable and their expected format

2. **Side Parameter Constraints**
   - Current: `side: str` (any string)
   - Issue: No constraint on valid values
   - Expected: "buy" or "sell" (possibly "sell_short")
   - Recommendation: Add to docstring or consider `Literal["buy", "sell"]` if all sources align

3. **Optional vs Required Fields**
   - `id`: Optional (None for new orders before submission)
   - `symbol`: Required (all orders/positions have symbols)
   - `qty`: Optional for orders (None before submission?), required for positions
   - `side`: Required for orders
   - `order_type`: Optional (default to market?)
   - `status`: Optional (None before submission)
   - `filled_qty`: Optional (None for pending orders)
   - Recommendation: Document optionality rationale in class docstring

---

## 5) Additional Notes

### Architecture & Design

**Strengths:**
1. Clean separation of concerns - protocols are minimal and focused
2. Runtime checkable protocols enable duck typing validation
3. Flexibility to work with Alpaca SDK, domain entities, and dicts
4. Minimal coupling (no imports from other modules)
5. Good use of Python 3.10+ union syntax (`str | None`)

**Design Tradeoffs:**
1. **Type Permissiveness**: `float | int | str` sacrifices some type safety for flexibility
   - Rationale: Must support Alpaca SDK (strings), domain models (Decimal), and legacy code (float)
   - Acceptable: This is the correct tradeoff for a protocol used across boundaries
   - Mitigation: Document expectations and rely on runtime validation at boundaries

2. **Protocol vs ABC**: Using Protocol instead of ABC
   - Rationale: Structural typing allows any object with matching properties to conform
   - Benefit: No explicit inheritance required; more flexible
   - Acceptable: Good choice for adapter pattern

3. **Minimal Docstrings**: Single-line property descriptions
   - Rationale: Keep protocols lightweight and readable
   - Issue: Reduces discoverability and increases learning curve
   - Recommendation: Expand without bloating

### Relationship to Other Files

1. **AlpacaOrderProtocol** (`alpaca.py`):
   - More specific than OrderLikeProtocol
   - Adds Alpaca-specific fields: `time_in_force`, `created_at`, `updated_at`
   - Types are all `str` (matches Alpaca SDK)
   - Note: Module docstring references OrderLikeProtocol

2. **StrategyOrderProtocol** (`strategy_tracking.py`):
   - Another order protocol for strategy-level tracking
   - Currently empty stub (line 59: `# Basic order-like interface`)
   - May duplicate OrderLikeProtocol

3. **Usage Pattern**:
   - Protocols are used in mapping/normalization functions
   - Convert from Alpaca SDK → DTOs → Domain entities
   - Enables testing with mocks without SDK dependency

### Recommendations

**Immediate (P0 - This Review):**
1. ✅ Create comprehensive docstrings with examples and constraints
2. ✅ Add test suite with protocol conformance validation
3. ✅ Document error handling expectations
4. ✅ Document quantity type usage patterns (when string vs numeric)
5. ✅ Add usage examples to class docstrings

**Short-term (P1 - Next Sprint):**
1. Consider adding validator examples for common cases
2. Document relationship with AlpacaOrderProtocol explicitly
3. Add examples of common mapping functions using these protocols
4. Consider adding type guards or validation utilities

**Medium-term (P2 - Future):**
1. Evaluate if `Literal` types are appropriate for side/status once all adapters align
2. Version the protocol interface if breaking changes are needed
3. Consider protocol evolution strategy
4. Add integration tests showing real Alpaca objects conforming

**Long-term (P3 - Nice to Have):**
1. Protocol registry pattern for version management
2. Runtime validation utilities for protocol conformance
3. Automatic SDK object → Protocol adapter generation

### Testing Strategy

**Required Tests:**
1. Runtime checkable verification (isinstance checks work)
2. Mock implementations satisfying protocols
3. Alpaca SDK objects satisfying protocols (integration)
4. Property access patterns (all properties accessible)
5. Type hint validation (mypy/pyright compatibility)

**Test File Structure:**
```python
tests/shared/protocols/test_order_like.py
- TestOrderLikeProtocol
  - test_runtime_checkable
  - test_mock_order_conforms
  - test_alpaca_order_conforms
  - test_required_properties
  - test_optional_properties
- TestPositionLikeProtocol
  - (similar structure)
```

---

## 6) Action Items

### P0 - Critical (Complete in this review)
- [x] Create comprehensive FILE_REVIEW document
- [x] Enhance module docstring with examples
- [x] Enhance class docstrings with usage examples
- [x] Expand property docstrings with constraints
- [x] Add error handling documentation
- [x] Create test suite (12+ tests)
- [x] Bump version (patch)

### P1 - High (Next sprint)
- [ ] Add validator examples to module
- [ ] Document relationship with AlpacaOrderProtocol
- [ ] Add mapping function examples

### P2 - Medium (Future)
- [ ] Consider Literal types for constrained strings
- [ ] Add protocol versioning
- [ ] Integration tests with real SDK objects

### P3 - Low (Nice to have)
- [ ] Protocol registry pattern
- [ ] Runtime validation utilities

---

**Auto-generated**: 2025-10-06  
**Script**: Manual Copilot agent execution  
**Reviewer**: Copilot AI Agent  
**Status**: ✅ COMPLETE - Ready for implementation
