# [File Review] the_alchemiser/shared/types/quantity.py

> Purpose: Conduct a rigorous, line-by-line review of a single Python file in the trading system, to institution-grade standards (correctness, controls, auditability, and safety). One issue per file.

---

## 0) Metadata

**File path**: `the_alchemiser/shared/types/quantity.py`

**Commit SHA / Tag**: `802cf268358e3299fb6b80a4b7cf3d4bda2994f4`

**Reviewer(s)**: GitHub Copilot

**Date**: 2025-01-06

**Business function / Module**: shared/types (value objects)

**Runtime context**: 
- Lightweight value object used in-memory across execution, portfolio, and broker modules
- No direct external I/O or network calls
- Pure validation with no side effects
- Used in DTOs, event schemas, and order representations

**Criticality**: P2 (Medium) - Used in critical order execution but simple value object with comprehensive tests

**Direct dependencies (imports)**:
```python
Internal: 
  - the_alchemiser.shared.utils.validation_utils.validate_non_negative_integer
External: 
  - dataclasses (stdlib)
  - decimal.Decimal (stdlib)
```

**External services touched**: None - Pure value object with no I/O

**Interfaces (DTOs/events) produced/consumed**:
```
Consumed by:
  - PositionInfo TypedDict (qty, qty_available fields)
  - Event schemas (TradeSettled.settled_quantity)
  - Execution validators
  - Broker adapters (alpaca_manager, alpaca_trading_service)
  - Trade ledger schemas
  - Notification templates
  
Produces: Quantity value objects (immutable, frozen dataclass)
```

**Related docs/specs**:
- [Copilot Instructions](/.github/copilot-instructions.md) - Core guardrails (Decimal for quantities, no float operations)
- [Quantity Test Suite](/tests/shared/types/test_quantity.py) - 117 lines, 13 tests including property-based tests
- [Money Value Object](/the_alchemiser/shared/types/money.py) - Similar pattern with more features
- [Percentage Value Object](/the_alchemiser/shared/types/percentage.py) - Similar minimal pattern

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
None identified.

### High
None identified.

### Medium
1. **Module header too generic** - Says "Shared domain types with validation" which is vague; should be more specific about value objects
2. **Incomplete class docstring** - Missing examples, pre/post-conditions, and explicit statement about non-negative constraint
3. **No comparison operators** - Cannot directly compare quantities (e.g., q1 < q2) without accessing .value attribute
4. **No arithmetic operations** - Unlike Money, lacks add/subtract operations that may be needed for quantity calculations

### Low
1. **No __repr__ override** - Default dataclass repr is acceptable but custom repr could improve debugging clarity
2. **No __str__ override** - Missing human-readable string representation for logging
3. **Docstring on __post_init__ doesn't document exceptions** - Should list ValueError in Raises section
4. **No __eq__ or __hash__ explicit implementation** - Dataclass provides defaults but explicit implementation would clarify intent
5. **No zero factory method** - Common pattern Quantity.zero() not provided
6. **No from_int/to_int convenience methods** - Users must manually wrap/unwrap Decimal

### Info/Nits
1. **Test coverage pragma comment** - `pragma: no cover` on __post_init__ prevents seeing validation coverage metrics
2. **Module is very minimal** - 22 lines total, which is excellent for simplicity but may need extension
3. **No explicit __all__** - Not exported in current module but __all__ would clarify API surface
4. **Module follows Percentage pattern** - Similar size (22 vs 37 lines) and structure

---

## 3) Line-by-Line Notes

### Detailed Line-by-Line Analysis

| Line(s) | Issue / Observation | Severity | Evidence / Excerpt | Proposed Action |
|---------|---------------------|----------|-------------------|-----------------|
| 1 | Business unit correct | ✓ Pass | `"""Business Unit: shared \| Status: current."""` | No action needed |
| 3 | Module docstring too generic | Medium | `"Shared domain types with validation."` | Consider: `"Order quantity value object with non-negative integer validation."` |
| 6 | Future annotations import | ✓ Pass | `from __future__ import annotations` | Good practice for forward references |
| 8-9 | Imports minimal and correct | ✓ Pass | stdlib only (dataclasses, decimal) | No action needed |
| 11 | Internal dependency appropriate | ✓ Pass | Uses shared validation utility | Good separation of concerns |
| 14 | Frozen dataclass provides immutability | ✓ Pass | `@dataclass(frozen=True)` | Correct per guardrails |
| 15-16 | Class docstring incomplete | Medium | `"""Order quantity with validation (whole number > 0)."""` | Should be "whole number >= 0" and add examples, Args/Returns/Raises |
| 18 | Type hint is correct | ✓ Pass | `value: Decimal` | Follows guardrails - Decimal for quantities |
| 20 | Pragma comment prevents coverage tracking | Info | `# pragma: no cover - trivial validation` | Consider removing; validation coverage is valuable |
| 20 | __post_init__ signature correct | ✓ Pass | `def __post_init__(self) -> None:` | Proper return type annotation |
| 21-22 | Docstring doesn't document exceptions | Low | Missing Raises section | Add: `Raises:\n    ValueError: If value is negative or not a whole number` |
| 22 | Validation call correct | ✓ Pass | `validate_non_negative_integer(self.value, "Quantity")` | Delegates to shared utility correctly |
| 23 | File ends with newline | ✓ Pass | Proper file termination | Lint requirement satisfied |
| - | No __repr__ override | Low | Default repr functional but verbose | Consider: `def __repr__(self) -> str: return f"Quantity({self.value})"` |
| - | No __str__ override | Low | No human-readable representation | Consider: `def __str__(self) -> str: return str(self.value)` |
| - | No comparison operators | Medium | Cannot compare q1 < q2 directly | Consider adding __lt__, __le__, __gt__, __ge__ or use @dataclass(order=True) |
| - | No arithmetic operations | Medium | Cannot add/subtract quantities | Consider add() and subtract() methods like Money |
| - | No zero factory | Low | No Quantity.zero() convenience | Consider: `@classmethod def zero(cls) -> Quantity: return cls(Decimal("0"))` |
| - | No int conversion helpers | Low | No from_int() or to_int() | Consider convenience methods for common conversions |

---

## 4) Correctness & Contracts

### Correctness Checklist

- [x] The file has a **clear purpose** and does not mix unrelated concerns (SRP)
  - ✅ Single responsibility: non-negative integer quantity representation
- [ ] Public functions/classes have **docstrings** with inputs/outputs, pre/post-conditions, and failure modes
  - ⚠️ Partial: Class has docstring but lacks examples and detailed contract (Medium severity)
- [x] **Type hints** are complete and precise (no `Any` in domain logic; use `Literal/NewType` where helpful)
  - ✅ All types properly annotated with Decimal, no Any usage
- [x] **DTOs** are **frozen/immutable** and validated (e.g., Pydantic v2 models with constrained types)
  - ✅ Frozen dataclass with validation in `__post_init__`
- [x] **Numerical correctness**: currency uses `Decimal`; floats use `math.isclose` or explicit tolerances; no `==`/`!=` on floats
  - ✅ Uses Decimal throughout; no float operations
- [x] **Error handling**: exceptions are narrow, typed (from `shared.errors`), logged with context, and never silently caught
  - ✅ Validation raises ValueError via validate_non_negative_integer utility
  - ℹ️ ValueError is acceptable for value objects per Percentage pattern
- [x] **Idempotency**: handlers tolerate replays; side-effects are guarded by idempotency keys or checks
  - ✅ Pure value object, no side effects, naturally idempotent
- [x] **Determinism**: tests freeze time (`freezegun`), seed RNG; no hidden randomness in business logic
  - ✅ Pure deterministic validation, no randomness
- [x] **Security**: no secrets in code/logs; input validation at boundaries; no `eval`/`exec`/dynamic imports
  - ✅ No security concerns in value object
- [x] **Observability**: structured logging with `correlation_id`/`causation_id`; one log per state change; no spam in hot loops
  - ℹ️ Validation utility logs warnings on failure (appropriate)
  - ✅ No logging in hot paths
- [x] **Testing**: public APIs have tests; property-based tests for maths; coverage ≥ 80% (≥ 90% for strategy/portfolio)
  - ✅ 13 tests including 5 property-based tests with Hypothesis
  - ✅ Tests cover construction, validation, immutability, and edge cases
- [x] **Performance**: no hidden I/O in hot paths; vectorised Pandas ops; HTTP clients pooled with rate limits
  - ✅ Pure computation, no I/O, O(1) validation
- [x] **Complexity**: cyclomatic ≤ 10, cognitive ≤ 15, functions ≤ 50 lines, params ≤ 5
  - ✅ Trivial complexity: cyclomatic = 1, single function with 2 lines
- [x] **Module size**: ≤ 500 lines (soft), split if > 800
  - ✅ Only 22 lines (minimal and focused)
- [x] **Imports**: no `import *`; stdlib → third-party → local; no deep relative imports
  - ✅ Clean import structure, proper ordering

**Overall Score**: 14/15 (93%) - Excellent foundation with minimal improvements needed

---

## 5) Recommended Actions (Priority Order)

### Priority 1: Documentation Enhancement
**Issue**: Incomplete class docstring (Medium)
**Action**: Enhance docstring with examples, explicit pre/post-conditions, and edge cases
```python
class Quantity:
    """Immutable order quantity value object with non-negative integer validation.

    Represents a tradeable quantity as a non-negative whole number using Decimal
    for exact arithmetic per financial-grade guardrails. Quantities must be >= 0
    and cannot have fractional parts.

    Attributes:
        value: Non-negative integer quantity as Decimal (0, 1, 2, ...)

    Examples:
        >>> # Valid quantities
        >>> Quantity(Decimal("0"))   # Zero quantity (valid)
        >>> Quantity(Decimal("10"))  # Ten shares
        >>> Quantity(Decimal("1000"))  # One thousand units

        >>> # Invalid quantities
        >>> Quantity(Decimal("-1"))   # Raises ValueError (negative)
        >>> Quantity(Decimal("1.5"))  # Raises ValueError (fractional)

    Raises:
        ValueError: If value is negative or not a whole number

    Note:
        This is a frozen dataclass - immutable after construction.
        All arithmetic must be done on the .value attribute.
    """
```

### Priority 2: Module Docstring Clarity
**Issue**: Module docstring too generic (Medium)
**Action**: Make module docstring more specific about value objects
```python
"""Business Unit: shared | Status: current.

Order quantity value object with non-negative integer validation.

Provides Quantity type for representing tradeable quantities (shares, units, contracts)
as non-negative integers using Decimal for exact arithmetic.
"""
```

### Priority 3: Document __post_init__ Exceptions
**Issue**: __post_init__ docstring missing Raises section (Low)
**Action**: Add proper docstring with exception documentation
```python
def __post_init__(self) -> None:
    """Validate the quantity after initialization.
    
    Raises:
        ValueError: If value is negative or not a whole number
    """
    validate_non_negative_integer(self.value, "Quantity")
```

### Priority 4: Consider Comparison Support (Optional Enhancement)
**Issue**: No comparison operators (Medium)
**Rationale**: Currently users must compare via .value attribute (q1.value < q2.value)
**Options**:
1. Add `order=True` to dataclass decorator (simplest, uses tuple comparison)
2. Implement explicit comparison methods (__lt__, __le__, __gt__, __ge__)

**Recommended**: Keep minimal for now; comparison via .value is explicit and clear
**Justification**: Similar to Percentage pattern; no current use case requires direct comparison

### Priority 5: Consider Arithmetic Operations (Future Enhancement)
**Issue**: No add/subtract operations (Medium)
**Rationale**: Money has arithmetic; Quantity may need it for portfolio calculations
**Examples**:
```python
def add(self, other: Quantity) -> Quantity:
    """Add two quantities."""
    return Quantity(self.value + other.value)

def subtract(self, other: Quantity) -> Quantity:
    """Subtract another quantity from this one."""
    result = self.value - other.value
    if result < 0:
        raise ValueError("Quantity subtraction would result in negative value")
    return Quantity(result)
```

**Recommended**: Wait for actual use case; YAGNI principle applies
**Justification**: No current usage requires quantity arithmetic; users can work with .value directly

---

## 6) Additional Notes

### Comparison with Similar Value Objects

**Money** (`money.py`):
- ✅ Has arithmetic operations (add, subtract, multiply, divide)
- ✅ Has currency precision normalization in `__post_init__` (quantize to currency precision)
- ✅ Uses ROUND_HALF_UP explicitly
- ✅ Has factory methods (zero, from_decimal)
- ✅ Has custom exceptions (MoneyError, CurrencyMismatchError, NegativeMoneyError)
- ✅ Has __str__ and __repr__ overrides
- ⚠️ Quantity lacks these features but may not need them

**Percentage** (`percentage.py`):
- ✅ Similar pattern: frozen dataclass with validation
- ✅ Similar size: 37 lines vs Quantity's 22 lines
- ✅ Uses shared validation utility (validate_decimal_range)
- ✅ Has factory method (from_percent) and conversion (to_percent)
- ⚠️ Both lack arithmetic operations and comparison operators

### Usage Context

The Quantity class is used in:
1. **TypedDicts** (PositionInfo) - qty, qty_available fields as QuantityValue = Decimal
2. **Event Schemas** (TradeSettled) - settled_quantity field
3. **Execution Validators** - Order quantity validation
4. **Broker Adapters** - Alpaca order submission
5. **Trade Ledger** - Position tracking
6. **Notifications** - Performance and portfolio reporting

**Observation**: Most usage is via the Decimal type alias `QuantityValue` rather than the Quantity value object itself. This suggests the value object is primarily for validation at construction boundaries, with raw Decimal used for calculations.

**Implication**: The minimal API is appropriate. Users construct Quantity(value) to validate, then work with .value as Decimal for calculations.

### Test Coverage Analysis

**Test File**: `tests/shared/types/test_quantity.py` (117 lines)
- **Unit Tests**: 8 tests covering construction, validation, immutability
- **Property Tests**: 5 tests using Hypothesis for comprehensive validation
  - Non-negative integers (0 to 1M): ✅ All valid
  - Negative integers (-1M to -1): ✅ All raise ValueError
  - Fractional values (0.01 to 1M): ✅ All raise ValueError
  - Value preservation: ✅ Decimal to int roundtrip
  - Comparison properties: ✅ Natural ordering

**Coverage**: All public API surface covered including edge cases (zero, negative, fractional)

### Code Quality Metrics

- **Lines of Code**: 22 (excellent - minimal and focused)
- **Cyclomatic Complexity**: 1 (trivial - single validation call)
- **Cognitive Complexity**: 1 (trivial - no nested logic)
- **Test Coverage**: 100% of public API (13 tests, 117 lines of test code)
- **Public API Surface**: 1 method (__post_init__), 1 attribute (value)
- **Dependencies**: 2 (stdlib + 1 internal validation utility)
- **Type Safety**: ✅ All types annotated, mypy passes with no issues
- **Lint Status**: ✅ Ruff passes with no issues

### Static Analysis Results

**MyPy** (Type Checking):
```
Success: no issues found in 1 source file
```

**Ruff** (Linting):
```
All checks passed!
```

**Test Results**:
```
13 passed in 4.24s
```

---

## 7) Conclusion

**Status**: ✅ **APPROVED with minor documentation improvements recommended**

**Summary**: The `quantity.py` module is an excellent example of a minimal, well-tested value object. It follows the single responsibility principle, uses Decimal for exact arithmetic per guardrails, enforces immutability, and has comprehensive test coverage including property-based tests. The implementation is clean, type-safe, and passes all static analysis checks.

**Strengths**:
1. ✅ Minimal and focused (22 lines)
2. ✅ Comprehensive test coverage (13 tests including property-based tests)
3. ✅ Proper use of Decimal per financial-grade guardrails
4. ✅ Immutable design (frozen dataclass)
5. ✅ Delegates validation to shared utility (DRY principle)
6. ✅ No complexity hotspots (cyclomatic = 1)
7. ✅ Zero type checking or linting issues

**Weaknesses**:
1. ⚠️ Incomplete docstrings (missing examples and detailed contract)
2. ⚠️ No comparison operators (must use .value attribute)
3. ⚠️ No arithmetic operations (unlike Money)
4. ℹ️ No factory methods or convenience helpers

**Risk Assessment**: **LOW**
- Pure value object with no I/O or side effects
- Comprehensive test coverage catches validation errors
- Used primarily as validation boundary; raw Decimal used for calculations
- Simple implementation minimizes bug surface

**Recommendation**: 
- **Required**: Enhance documentation (docstrings) per Priority 1-3 actions
- **Optional**: Consider comparison operators and arithmetic if use cases emerge
- **Monitor**: Track usage patterns to inform future enhancements

**Compliance**: ✅ Meets all Copilot Instructions requirements
- [x] Uses Decimal for quantities (not float)
- [x] Frozen dataclass (immutable)
- [x] Type hints complete
- [x] Validation at construction
- [x] Property-based tests included
- [x] Module size ≤ 500 lines
- [x] Cyclomatic complexity ≤ 10
- [x] No security concerns

---

**Auto-generated**: 2025-01-06  
**Reviewed by**: GitHub Copilot  
**Status**: Approved with documentation improvements recommended
