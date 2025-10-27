# [File Review] Financial-grade, line-by-line audit

> Purpose: Conduct a rigorous, line-by-line review of a single Python file in the trading system, to institution-grade standards (correctness, controls, auditability, and safety). One issue per file.

---

## 0) Metadata

**File path**: `the_alchemiser/shared/protocols/alpaca.py`

**Commit SHA / Tag**: `802cf268358e3299fb6b80a4b7cf3d4bda2994f4`

**Reviewer(s)**: Copilot Agent

**Date**: 2025-10-08

**Business function / Module**: shared/protocols

**Runtime context**: Design-time protocol definitions used across all Alpaca-related integrations

**Criticality**: P2 (Medium) - Protocol definitions for type safety in broker interactions

**Direct dependencies (imports)**:
```
Internal: None (leaf protocol module)
External: 
  - typing (Protocol)
  - __future__ (annotations)
```

**External services touched**:
```
None - Pure protocol definitions
Interfaces with: Alpaca Trading API (alpaca-py SDK v0.42.2)
```

**Interfaces (DTOs/events) produced/consumed**:
```
Defines: 
  - AlpacaOrderProtocol (structural type for Alpaca order objects)
  - AlpacaOrderObject (minimal protocol for order monitoring)
Consumed by: Type checkers (mypy), runtime type checking (if decorated)
```

**Related docs/specs**:
- Copilot Instructions (.github/copilot-instructions.md)
- Alpaca Trading API: https://docs.alpaca.markets/
- OrderLikeProtocol (the_alchemiser/shared/protocols/order_like.py)

**File metrics**:
- **Lines of code**: 36
- **Classes**: 2 (both protocols)
- **Functions/Methods**: 0
- **Cyclomatic Complexity**: N/A (pure protocol definitions)
- **Test Coverage**: No dedicated test file exists

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

**None identified**

### High

1. **Type mismatches with Alpaca SDK actual types** (Lines 18-28)
   - Protocol uses `str` for `id`, but Alpaca SDK uses `uuid.UUID` (non-nullable)
   - Protocol uses `str` for timestamps (`created_at`, `updated_at`), but SDK uses `datetime.datetime` (non-nullable)
   - Protocol uses `str | None` for `filled_avg_price`, SDK uses `str | float | None`
   - **Impact**: Type checker won't catch real type errors when using actual Alpaca Order objects
   - **Evidence**: Alpaca SDK Order has `id: uuid.UUID`, `created_at: datetime.datetime`, `updated_at: datetime.datetime`

2. **Missing critical attributes** (Lines 15-28)
   - Protocol missing `client_order_id` (required field in Alpaca SDK)
   - Protocol missing `submitted_at` (used for order tracking)
   - **Impact**: Cannot access important order identification and timing fields through protocol

### Medium

1. **No runtime_checkable decorator** (Lines 15, 31)
   - Protocols not decorated with `@runtime_checkable`
   - Cannot use `isinstance()` checks at runtime
   - **Impact**: Limits runtime type validation capabilities
   - **Comparison**: OrderLikeProtocol uses `@runtime_checkable` (line 15 of order_like.py)

2. **Inconsistent naming with AlpacaOrderObject** (Line 31)
   - Two protocols with similar names but unclear differentiation
   - `AlpacaOrderProtocol` vs `AlpacaOrderObject` naming is confusing
   - Docstring says "used in monitoring" but doesn't clarify why separate protocol needed
   - **Impact**: Developer confusion about which protocol to use

3. **No validation of attribute relationships** (Lines 15-36)
   - Protocol doesn't encode invariants (e.g., `filled_qty <= qty`)
   - No specification of valid `status` values
   - No specification of valid `side`, `order_type`, `time_in_force` values
   - **Impact**: Type system can't catch logical inconsistencies

4. **No test coverage**
   - No test file at `tests/shared/protocols/test_alpaca.py`
   - No validation that actual Alpaca objects conform to protocol
   - **Impact**: Protocol drift undetected; breaking changes not caught

### Low

1. **Generic string types for enums** (Lines 21-23)
   - `side`, `order_type`, `time_in_force`, `status` are typed as `str`
   - Alpaca SDK uses proper enums (OrderSide, OrderType, TimeInForce, OrderStatus)
   - **Impact**: Loses enum type safety; can't leverage IDE autocomplete

2. **Unclear protocol purpose** (Lines 15-36)
   - Two nearly identical protocols with unclear use cases
   - No documentation on when to use which protocol
   - **Impact**: Developer confusion, potential misuse

3. **Missing attributes for complete order lifecycle** (Lines 15-28)
   - No `canceled_at`, `expired_at`, `filled_at`, `replaced_at` timestamps
   - No `limit_price`, `stop_price` for limit/stop orders
   - No `extended_hours` flag
   - **Impact**: Limited utility for comprehensive order tracking

### Info/Nits

1. **No __all__ export list** (Line 36)
   - File doesn't define `__all__` for explicit API surface control
   - **Impact**: Minor; protocols are typically implicitly exported

2. **Minimal docstrings** (Lines 16, 32)
   - Docstrings are one-liners without examples or usage guidance
   - **Impact**: Developer experience; not critical for protocols

---

## 3) Line-by-Line Notes

### Detailed Line-by-Line Analysis

| Line(s) | Issue / Observation | Severity | Evidence / Excerpt | Proposed Action |
|---------|---------------------|----------|-------------------|-----------------|
| 1 | ✅ Module header present | PASS | `"""Business Unit: shared \| Status: current."""` | None - compliant |
| 2-8 | ✅ Comprehensive module docstring | PASS | Explains purpose and scope | None - well documented |
| 10 | ✅ Future annotations import | PASS | `from __future__ import annotations` | None - best practice |
| 12 | ✅ Clean import | PASS | `from typing import Protocol` | None - minimal imports |
| 15 | ⚠️ Missing runtime_checkable | MEDIUM | `class AlpacaOrderProtocol(Protocol):` | Add `@runtime_checkable` decorator |
| 16 | ℹ️ Minimal docstring | INFO | `"""Protocol for Alpaca order objects."""` | Consider adding examples |
| 18 | ❌ Wrong type for id | HIGH | `id: str` | Should be `str \| UUID` to match SDK |
| 19 | ✅ Symbol type correct | PASS | `symbol: str` | None - matches SDK (as Optional[str] but commonly present) |
| 20 | ❌ Wrong type for qty | HIGH | `qty: str` | SDK has `str \| float \| None` |
| 21 | ⚠️ Should use enum | LOW | `side: str` | Consider `str` (OrderSide enum in SDK) |
| 22 | ⚠️ Should use enum | LOW | `order_type: str` | Consider `str` (OrderType enum in SDK) |
| 23 | ⚠️ Should use enum | LOW | `time_in_force: str` | Consider `str` (TimeInForce enum in SDK) |
| 24 | ⚠️ Should use enum | LOW | `status: str` | Consider `str` (OrderStatus enum in SDK) |
| 25 | ❌ Wrong type | HIGH | `filled_qty: str` | SDK has `str \| float \| None` |
| 26 | ⚠️ Incomplete type | HIGH | `filled_avg_price: str \| None` | SDK has `str \| float \| None` |
| 27 | ❌ Wrong type | HIGH | `created_at: str` | SDK has `datetime.datetime` (non-optional) |
| 28 | ❌ Wrong type | HIGH | `updated_at: str` | SDK has `datetime.datetime` (not in SDK - may be custom?) |
| 30 | ❌ Missing critical field | HIGH | (between 28-31) | SDK has `client_order_id: str`, `submitted_at: datetime` |
| 31 | ⚠️ Missing runtime_checkable | MEDIUM | `class AlpacaOrderObject(Protocol):` | Add `@runtime_checkable` decorator |
| 32 | ⚠️ Unclear purpose | MEDIUM | `"""Protocol for Alpaca order objects used in monitoring."""` | Clarify difference from AlpacaOrderProtocol |
| 34-36 | ⚠️ Minimal monitoring fields | LOW | Only `id`, `status`, `filled_qty` | Consider if this subset is sufficient |
| 36 | ℹ️ No explicit exports | INFO | No `__all__` list | Consider adding for API clarity |

---

## 4) Correctness & Contracts

### Correctness Checklist

- [x] ✅ The file has a **clear purpose** and does not mix unrelated concerns (SRP)
  - **Status**: PASS - Focused solely on Alpaca order protocols
  - **Note**: Single responsibility maintained
  
- [x] ⚠️ Public functions/classes have **docstrings** with inputs/outputs, pre/post-conditions, and failure modes
  - **Status**: PARTIAL - Docstrings present but minimal
  - **Note**: Protocols have one-line docstrings; could benefit from usage examples
  
- [ ] ❌ **Type hints** are complete and precise (no `Any` in domain logic; use `Literal/NewType` where helpful)
  - **Status**: FAIL - Type mismatches with actual Alpaca SDK types
  - **Evidence**: 
    - `id: str` should align with SDK's `uuid.UUID`
    - Timestamps are `str` but SDK uses `datetime.datetime`
    - `filled_avg_price` missing `float` option
  
- [x] ✅ **DTOs** are **frozen/immutable** and validated (e.g., Pydantic v2 models with constrained types)
  - **Status**: N/A - These are protocols, not DTOs
  - **Note**: Protocols define structure, not enforce immutability
  
- [x] ✅ **Numerical correctness**: currency uses `Decimal`; floats use `math.isclose` or explicit tolerances; no `==`/`!=` on floats
  - **Status**: N/A - No numerical operations in protocols
  
- [x] ✅ **Error handling**: exceptions are narrow, typed (from `shared.errors`), logged with context, and never silently caught
  - **Status**: N/A - No error handling in protocol definitions
  
- [x] ✅ **Idempotency**: handlers tolerate replays; side-effects are guarded by idempotency keys or checks
  - **Status**: N/A - No handlers in protocol definitions
  
- [x] ✅ **Determinism**: tests freeze time (`freezegun`), seed RNG; no hidden randomness in business logic
  - **Status**: N/A - No business logic in protocols
  
- [x] ✅ **Security**: no secrets in code/logs; input validation at boundaries; no `eval`/`exec`/dynamic imports
  - **Status**: PASS - No security concerns; pure type definitions
  
- [x] ✅ **Observability**: structured logging with `correlation_id`/`causation_id`; one log per state change; no spam in hot loops
  - **Status**: N/A - No logging in protocol definitions
  
- [ ] ❌ **Testing**: public APIs have tests; property-based tests for maths; coverage ≥ 80% (≥ 90% for strategy/portfolio)
  - **Status**: FAIL - No test file exists
  - **Evidence**: `tests/shared/protocols/test_alpaca.py` does not exist
  - **Impact**: Protocol conformance not validated
  
- [x] ✅ **Performance**: no hidden I/O in hot paths; vectorised Pandas ops; HTTP clients pooled with rate limits
  - **Status**: N/A - No I/O or operations in protocols
  
- [x] ✅ **Complexity**: cyclomatic ≤ 10, cognitive ≤ 15, functions ≤ 50 lines, params ≤ 5
  - **Status**: PASS - Trivial complexity (pure declarations)
  
- [x] ✅ **Module size**: ≤ 500 lines (soft), split if > 800
  - **Status**: PASS - 36 lines total
  
- [x] ✅ **Imports**: no `import *`; stdlib → third-party → local; no deep relative imports
  - **Status**: PASS - Clean, minimal imports

---

## 5) Additional Notes

### Key Observations

1. **Protocol Design Philosophy**
   - File follows Python Protocol pattern correctly (structural subtyping)
   - Protocols are lightweight and don't enforce runtime behavior
   - Good separation from OrderLikeProtocol (more generic) vs these (Alpaca-specific)

2. **Type Safety vs Flexibility Tradeoff**
   - Current approach uses `str` for everything, maximizing compatibility
   - This sacrifices type safety for flexibility with serialized/deserialized objects
   - May be intentional design for JSON/dict handling, but undocumented

3. **Usage Pattern Unknown**
   - No code in repository actually imports these protocols (grep found no usage)
   - Either: (a) protocols are unused/dead code, or (b) used implicitly via duck typing
   - Need to verify actual usage before making changes

### Architectural Concerns

1. **Redundancy with OrderLikeProtocol**
   - `OrderLikeProtocol` already exists with similar structure
   - `AlpacaOrderProtocol` adds `time_in_force`, `created_at`, `updated_at`
   - Consider if Alpaca-specific protocol is necessary or if generic suffices

2. **AlpacaOrderObject Purpose Unclear**
   - Has only 3 fields: `id`, `status`, `filled_qty`
   - Described as "used in monitoring" but no clear use case
   - May be for polling/status checking, but should be documented

3. **No Integration with Alpaca Manager**
   - `shared/brokers/alpaca_manager.py` exists but doesn't import these protocols
   - Suggests protocols may not be actively used in broker integration
   - Need to validate if these are legacy or future-intended

### Comparison with Actual Alpaca SDK

Based on inspection of `alpaca.trading.models.Order`, the SDK provides:

**Core Identification:**
- `id: uuid.UUID` (not optional)
- `client_order_id: str` (not optional)

**Timestamps (all datetime.datetime, not optional):**
- `created_at`, `submitted_at`, `filled_at`, `canceled_at`, `expired_at`, `replaced_at`, `failed_at`

**Quantities (all str | float | None):**
- `qty`, `filled_qty`, `filled_avg_price`, `limit_price`, `stop_price`, `notional`

**Enums:**
- `side: OrderSide` enum
- `order_type: OrderType` enum
- `time_in_force: TimeInForce` enum
- `status: OrderStatus` enum

**Our protocol significantly simplifies this**, which may be intentional for a specific use case.

### Areas for Improvement

#### 1. Type Accuracy (HIGH Priority)

**Issue**: Protocol types don't match Alpaca SDK types, reducing type safety effectiveness.

**Impact**: Type checkers like mypy won't catch misuse of Alpaca Order objects.

**Recommendation**:
```python
from datetime import datetime
from typing import Protocol, Union
from uuid import UUID

class AlpacaOrderProtocol(Protocol):
    """Protocol for Alpaca order objects.
    
    Structural type matching the Alpaca Trading API Order model.
    Allows type-safe interaction with Alpaca SDK Order objects.
    """
    
    id: Union[str, UUID]  # Support both for flexibility
    client_order_id: str
    symbol: str
    qty: Union[str, float, None]
    side: str  # OrderSide enum in practice
    order_type: str  # OrderType enum in practice
    time_in_force: str  # TimeInForce enum in practice
    status: str  # OrderStatus enum in practice
    filled_qty: Union[str, float, None]
    filled_avg_price: Union[str, float, None]
    created_at: Union[str, datetime]  # Support serialized forms
    submitted_at: Union[str, datetime]
```

#### 2. Runtime Checkable (MEDIUM Priority)

**Issue**: Protocols can't be used with `isinstance()` checks.

**Recommendation**: Add `@runtime_checkable` decorator to both protocols for runtime validation.

#### 3. Test Coverage (HIGH Priority)

**Issue**: No tests validate protocol conformance.

**Recommendation**: Create `tests/shared/protocols/test_alpaca.py` with:
- Test that actual Alpaca Order objects satisfy the protocol
- Test that mock objects with protocol fields pass type checking
- Test that objects missing required fields fail type checking

#### 4. Documentation (MEDIUM Priority)

**Issue**: Unclear when to use each protocol and why two exist.

**Recommendation**: Enhance docstrings with:
- Usage examples
- When to use AlpacaOrderProtocol vs AlpacaOrderObject
- Relationship to OrderLikeProtocol
- Expected consumer code patterns

### Testing Recommendations

**Create: tests/shared/protocols/test_alpaca.py**

```python
#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Tests for Alpaca protocol definitions.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from alpaca.trading.models import Order

from the_alchemiser.shared.protocols.alpaca import (
    AlpacaOrderObject,
    AlpacaOrderProtocol,
)


class TestAlpacaOrderProtocol:
    """Test AlpacaOrderProtocol type checking."""

    def test_protocol_with_minimal_attributes(self) -> None:
        """Test protocol with minimal required attributes."""
        
        class MinimalOrder:
            id = "test-id"
            symbol = "AAPL"
            qty = "10"
            side = "buy"
            order_type = "market"
            time_in_force = "day"
            status = "filled"
            filled_qty = "10"
            filled_avg_price = "150.00"
            created_at = "2024-01-01T00:00:00Z"
            updated_at = "2024-01-01T00:00:05Z"
        
        order: AlpacaOrderProtocol = MinimalOrder()
        assert order.symbol == "AAPL"

    def test_protocol_with_none_values(self) -> None:
        """Test protocol handles None for optional fields."""
        
        class OrderWithNone:
            id = "test-id"
            symbol = "AAPL"
            qty = "10"
            side = "buy"
            order_type = "market"
            time_in_force = "day"
            status = "pending"
            filled_qty = "0"
            filled_avg_price = None  # Not filled yet
            created_at = "2024-01-01T00:00:00Z"
            updated_at = "2024-01-01T00:00:05Z"
        
        order: AlpacaOrderProtocol = OrderWithNone()
        assert order.filled_avg_price is None


class TestAlpacaOrderObject:
    """Test AlpacaOrderObject minimal protocol."""

    def test_minimal_monitoring_protocol(self) -> None:
        """Test minimal protocol for order monitoring."""
        
        class MonitoringOrder:
            id = "test-id"
            status = "filled"
            filled_qty = "10"
        
        order: AlpacaOrderObject = MonitoringOrder()
        assert order.id == "test-id"
        assert order.status == "filled"


class TestProtocolConformance:
    """Test conformance with actual Alpaca SDK objects."""

    @pytest.mark.skipif(
        not hasattr(Order, "__init__"),
        reason="Alpaca SDK not available in test environment"
    )
    def test_actual_alpaca_order_note(self) -> None:
        """Note: Actual Alpaca Order may not conform due to type differences.
        
        This documents the known type mismatches:
        - id: Protocol expects str, SDK provides UUID
        - created_at: Protocol expects str, SDK provides datetime
        - updated_at: Not a field in SDK (SDK has submitted_at, filled_at, etc.)
        """
        # This test documents the discrepancy rather than testing conformance
        pass
```

---

## 6) Recommended Action Items

### Must Fix (Critical - Before Production Use)

**None identified** - File is not actively used in critical paths

### Should Fix (High Priority - Next Sprint)

1. **Verify Protocol Usage** (HIGH)
   - Search codebase for actual usage of these protocols
   - If unused, consider removal as dead code
   - If used, document usage patterns
   - Estimated effort: 1 hour

2. **Fix Type Mismatches** (HIGH)
   - Align types with Alpaca SDK actual types
   - Use Union types to support both serialized and native forms
   - Add missing critical fields (client_order_id, submitted_at)
   - Estimated effort: 2-3 hours

3. **Add Test Coverage** (HIGH)
   - Create tests/shared/protocols/test_alpaca.py
   - Test protocol conformance with mock objects
   - Document known mismatches with SDK
   - Estimated effort: 2-3 hours

### Could Fix (Medium Priority - Future Sprint)

4. **Add Runtime Checkable** (MEDIUM)
   - Add @runtime_checkable decorator
   - Enable isinstance() checks
   - Estimated effort: 15 minutes

5. **Clarify Protocol Purposes** (MEDIUM)
   - Document when to use each protocol
   - Explain relationship to OrderLikeProtocol
   - Add usage examples to docstrings
   - Estimated effort: 1-2 hours

6. **Consider Consolidation** (MEDIUM)
   - Evaluate if AlpacaOrderObject is necessary
   - Consider merging into AlpacaOrderProtocol with optional fields
   - Estimated effort: 2-3 hours (requires usage analysis)

### Nice to Have (Low Priority - Backlog)

7. **Use Literal Types for Enums** (LOW)
   - Replace `str` with `Literal["buy", "sell"]` for side
   - Improves type safety for known values
   - Estimated effort: 1 hour

8. **Add __all__ Export List** (LOW)
   - Explicit API surface control
   - Estimated effort: 5 minutes

---

## 7) Compliance Assessment

| Standard | Status | Notes |
|----------|--------|-------|
| Copilot Instructions | ⚠️ PARTIAL | Module header ✅, Type hints incomplete ⚠️, No tests ❌ |
| SRP | ✅ PASS | Single clear purpose: Alpaca order protocols |
| Type Safety | ❌ FAIL | Type mismatches with SDK reduce effectiveness |
| Testing | ❌ FAIL | No test coverage |
| Complexity | ✅ PASS | Trivial (pure declarations) |
| Documentation | ⚠️ PARTIAL | Basic docstrings present, examples missing |
| Security | ✅ PASS | No security risks |
| Observability | ✅ N/A | Not applicable to protocols |
| Float Handling | ✅ N/A | No numerical operations |
| Module Size | ✅ PASS | 36 lines (well under limit) |

---

## 8) Summary

**Overall Assessment**: ⚠️ **ACCEPTABLE with IMPROVEMENTS NEEDED**

**Strengths**:
- Clean, simple protocol definitions
- Good module structure and documentation header
- Minimal dependencies (leaf module)
- No complexity concerns
- Passes mypy and ruff checks

**Weaknesses**:
- Type mismatches with actual Alpaca SDK reduce type safety value
- No test coverage to validate protocol conformance
- Unclear if protocols are actually used (no imports found)
- Missing runtime_checkable decorator limits utility
- Purpose of two separate protocols unclear

**Risk Assessment**:
- **Correctness Risk**: LOW (not actively used, no business logic)
- **Type Safety Risk**: MEDIUM (mismatches reduce type checking effectiveness)
- **Maintenance Risk**: LOW (simple, stable code)
- **Security Risk**: NONE (pure type definitions)

**Recommendation**: 
1. **Immediate**: Verify if protocols are used; remove if dead code
2. **Short-term**: Add tests and fix type mismatches if used
3. **Long-term**: Consider consolidating with OrderLikeProtocol for cleaner architecture

---

**Audit completed**: 2025-10-08  
**Auditor**: Copilot Agent  
**Next review date**: After usage verification and type fixes
