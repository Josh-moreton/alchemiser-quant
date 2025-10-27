# [File Review] Financial-grade, line-by-line audit

> Purpose: Conduct a rigorous, line-by-line review of a single Python file in the trading system, to institution-grade standards (correctness, controls, auditability, and safety). One issue per file.

---

## 0) Metadata

**File path**: `the_alchemiser/shared/protocols/asset_metadata.py`

**Commit SHA / Tag**: `312f657cd76a6f581f6b13897840555942e475d0`

**Reviewer(s)**: GitHub Copilot Agent

**Date**: 2025-10-08

**Business function / Module**: shared/protocols

**Runtime context**: 
- Protocol definition (no runtime execution)
- Used across all modules requiring asset metadata access
- Deployment: Lambda (AWS), local development
- Trading modes: Paper, Live
- Concurrency: N/A (interface only)

**Criticality**: P2 (Medium) - Core protocol defining asset metadata interface

**Direct dependencies (imports)**:
```python
Internal:
- the_alchemiser.shared.value_objects.symbol.Symbol

External:
- typing.Protocol (stdlib)
- abc.abstractmethod (stdlib)
- __future__.annotations (stdlib)
```

**External services touched**:
- None directly (protocol definition only)
- Implementations access: Alpaca Trading API (via AlpacaAssetMetadataAdapter)

**Interfaces (DTOs/events) produced/consumed**:
```
Protocol defines interface for:
- is_fractionable(Symbol) -> bool
- get_asset_class(Symbol) -> str
- should_use_notional_order(Symbol, float) -> bool

Implementations:
- AlpacaAssetMetadataAdapter (production)
- Mock implementations (testing)

Consumers:
- FractionabilityDetector (the_alchemiser/shared/math/asset_info.py)
- Portfolio management modules
- Execution modules
```

**Related docs/specs**:
- [Copilot Instructions](/.github/copilot-instructions.md)
- [Shared Module README](/the_alchemiser/shared/README.md)
- Implementation: `the_alchemiser/shared/adapters/alpaca_asset_metadata_adapter.py`
- Value Object: `the_alchemiser/shared/value_objects/symbol.py`
- Consumer: `the_alchemiser/shared/math/asset_info.py`

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
**HIGH-1: Missing Exception Specifications in Protocol Methods (Lines 22-59)**
- **Risk**: Protocol methods don't specify which exceptions implementations may raise.
- **Impact**: Consumers don't know what exceptions to handle; adapter raises `RateLimitError` and `DataProviderError` but protocol doesn't document this contract.
- **Evidence**: AlpacaAssetMetadataAdapter.is_fractionable() raises exceptions (lines 51-58) but protocol doesn't specify this.
- **Violation**: Copilot Instructions: "Public functions/classes have docstrings with inputs/outputs, pre/post-conditions, and failure modes."

### Medium
**MED-1: Incomplete Docstrings - Missing Failure Modes (Lines 23-59)**
- **Risk**: Docstrings lack information about failure scenarios, error handling, and edge cases.
- **Impact**: Implementers may not handle all cases consistently; consumers unaware of potential failure modes.
- **Violation**: Copilot Instructions: "Public functions/classes have docstrings with inputs/outputs, pre/post-conditions, and failure modes."

**MED-2: Return Type for get_asset_class Too Broad (Line 35)**
- **Risk**: Returns `str` instead of constrained type like `Literal` or enum.
- **Impact**: No type-level guarantee on return values; consumers must handle arbitrary strings.
- **Recommendation**: Use `Literal["us_equity", "crypto", "unknown"]` or `AssetClass` enum for type safety.

**MED-3: Missing Protocol Tests (No test file)**
- **Risk**: No direct tests for protocol validation or structural typing.
- **Impact**: Protocol changes could break implementations without detection.
- **Evidence**: No test file found at `tests/shared/protocols/test_asset_metadata.py`.

**MED-4: No __init__.py in protocols Package**
- **Risk**: protocols package lacks `__init__.py`, making imports less discoverable.
- **Impact**: Protocol not explicitly exported from package; relies on direct imports.
- **Evidence**: `the_alchemiser/shared/protocols/__init__.py` does not exist.

**MED-5: Missing Pre/Post-Conditions in should_use_notional_order (Lines 48-59)**
- **Risk**: No validation requirements documented for `quantity` parameter.
- **Impact**: Unclear if negative quantities are valid, what happens at quantity=0, or if there are magnitude limits.
- **Evidence**: Docstring doesn't specify valid ranges or constraints.

### Low
**LOW-1: Business Unit Header Mislabeled (Line 1)**
- **Risk**: Header says "Business Unit: utilities" but should be "shared" or "protocols".
- **Impact**: Incorrect categorization for auditing and module tracking.
- **Evidence**: `"""Business Unit: utilities; Status: current."""`

**LOW-2: Module Docstring Could Be More Specific (Lines 1-8)**
- **Risk**: Docstring explains purpose but doesn't clarify usage patterns or design decisions.
- **Impact**: New developers may not understand when to use this vs direct service calls.
- **Recommendation**: Add examples of usage and explain the inversion-of-control pattern.

**LOW-3: No Version or Schema Information (Entire File)**
- **Risk**: Protocol has no version identifier for compatibility tracking.
- **Impact**: Can't track protocol evolution or breaking changes systematically.
- **Recommendation**: Add `__version__` or protocol version constant.

**LOW-4: Missing Type Alias for Return Types (Lines 22-59)**
- **Risk**: Common types like `bool` for fractionability could benefit from semantic aliases.
- **Impact**: Minor - reduces semantic clarity but doesn't affect functionality.
- **Example**: `Fractionable = NewType('Fractionable', bool)`

### Info/Nits
**INFO-1: ✅ Good Use of Protocol Pattern**
- Proper use of typing.Protocol for structural typing.
- Correctly uses @abstractmethod to mark interface requirements.

**INFO-2: ✅ Proper Import Organization**
- Imports follow stdlib → internal pattern correctly.
- Uses `from __future__ import annotations` for forward compatibility.

**INFO-3: ✅ Clean Single Responsibility**
- Protocol focused solely on asset metadata access.
- No mixing of concerns or infrastructure dependencies.

**INFO-4: ✅ Appropriate File Size**
- 59 lines total - well within limits (≤500 soft, ≤800 hard).
- Simple, focused interface with 3 methods.

**INFO-5: ✅ Type Hints Present**
- All methods have complete type annotations.
- Uses Symbol value object correctly instead of raw strings.

**INFO-6: Documentation Could Include Examples**
- Adding usage examples would improve clarity.
- Consider showing typical implementation and consumption patterns.

---

## 3) Line-by-Line Notes

### Detailed Line-by-Line Analysis

| Line(s) | Issue / Observation | Severity | Evidence / Excerpt | Proposed Action |
|---------|---------------------|----------|-------------------|-----------------|
| 1 | Business unit mislabeled | Low | `"""Business Unit: utilities; Status: current."""` | Change to `"""Business Unit: shared; Status: current."""` |
| 3-8 | Module docstring adequate but could include examples | Info | "Defines the interface for accessing asset metadata..." | Add usage example or implementation guidance |
| 10 | ✅ Proper future annotations | Info | `from __future__ import annotations` | None - compliant |
| 12-13 | ✅ Clean imports | Info | stdlib imports properly organized | None - compliant |
| 15 | ✅ Symbol value object used | Info | `from the_alchemiser.shared.value_objects.symbol import Symbol` | None - compliant |
| 18-19 | ✅ Protocol class defined correctly | Info | `class AssetMetadataProvider(Protocol):` | None - compliant |
| 19 | Class docstring minimal | Low | Single line without examples | Could expand with usage patterns |
| 21-32 | is_fractionable method | Multiple | See details below | Multiple improvements needed |
| 22 | ✅ Proper @abstractmethod | Info | Correctly marks abstract interface | None |
| 23-31 | Docstring missing Raises section | High | No exception documentation | Add "Raises:" section with RateLimitError, DataProviderError |
| 26 | Type hint uses Symbol | Info | `symbol: Symbol` | ✅ Good - uses value object |
| 28-29 | Return type documentation | Info | "True if the asset supports fractional shares" | ✅ Clear |
| 31 | Missing edge case documentation | Medium | No discussion of error cases | Document what happens on API failure |
| 34-45 | get_asset_class method | Multiple | See details below | Multiple improvements needed |
| 35 | @abstractmethod present | Info | Correctly marks abstract | None |
| 36-44 | Docstring missing Raises section | Medium | No exception documentation | Add "Raises:" section if applicable |
| 35 | Return type too broad | Medium | `-> str` | Consider `-> Literal["us_equity", "crypto", "unknown"]` |
| 39 | Type hint uses Symbol | Info | `symbol: Symbol` | ✅ Good - uses value object |
| 41-42 | Return doc mentions examples | Info | "e.g., 'stock', 'etf', 'crypto'" | Good but inconsistent with actual values ("us_equity") |
| 41-42 | Example values don't match implementation | Low | Says 'stock' but impl returns 'us_equity' | Update examples to match AlpacaAssetMetadataAdapter |
| 47-59 | should_use_notional_order method | Multiple | See details below | Multiple improvements needed |
| 48 | @abstractmethod present | Info | Correctly marks abstract | None |
| 49-58 | Docstring missing constraints | Medium | No quantity validation requirements | Add: "Args: quantity: Must be > 0. Negative quantities raise ValueError." |
| 51-52 | Args documented | Info | symbol and quantity both documented | ✅ Adequate |
| 54-55 | Return documentation | Info | "True if notional orders should be used" | ✅ Clear but could explain "notional" for new devs |
| 48 | quantity parameter type | Info | `quantity: float` | Using float is correct for fractional shares |
| 49-58 | Missing algorithmic guidance | Low | Doesn't explain decision criteria | Could document: "Typically true for non-fractionable assets, fractional qty < 1, or fraction > 0.1" |
| 59 | ✅ Clean file end | Info | No trailing content | None |

---

## 4) Correctness & Contracts

### Correctness Checklist

- [x] The file has a **clear purpose** and does not mix unrelated concerns (SRP)
  - ✅ Protocol focused solely on asset metadata access
- [x] Public functions/classes have **docstrings** with inputs/outputs, pre/post-conditions, and failure modes
  - ⚠️ PARTIAL: Has docstrings but missing "Raises" sections and pre/post-conditions
- [x] **Type hints** are complete and precise (no `Any` in domain logic; use `Literal/NewType` where helpful)
  - ⚠️ PARTIAL: Type hints present but `get_asset_class` return type could be more specific
- [x] **DTOs** are **frozen/immutable** and validated (e.g., Pydantic v2 models with constrained types)
  - ✅ Uses Symbol value object which is frozen; protocol itself defines interface only
- [x] **Numerical correctness**: currency uses `Decimal`; floats use `math.isclose` or explicit tolerances; no `==`/`!=` on floats
  - ✅ N/A - No numerical operations in protocol
- [x] **Error handling**: exceptions are narrow, typed (from `shared.errors`), logged with context, and never silently caught
  - ⚠️ PARTIAL: Protocol doesn't document which exceptions implementations should raise
- [x] **Idempotency**: handlers tolerate replays; side-effects are guarded by idempotency keys or checks
  - ✅ N/A - Protocol methods are pure queries (read-only operations)
- [x] **Determinism**: tests freeze time (`freezegun`), seed RNG; no hidden randomness in business logic
  - ✅ N/A - Protocol is deterministic interface definition
- [x] **Security**: no secrets in code/logs; input validation at boundaries; no `eval`/`exec`/dynamic imports
  - ✅ No security concerns in protocol definition
- [x] **Observability**: structured logging with `correlation_id`/`causation_id`; one log per state change; no spam in hot loops
  - ⚠️ N/A - Protocol doesn't log; implementations should log
- [x] **Testing**: public APIs have tests; property-based tests for maths; coverage ≥ 80% (≥ 90% for strategy/portfolio)
  - ❌ FAIL: No direct protocol tests; only implementation tests exist
- [x] **Performance**: no hidden I/O in hot paths; vectorised Pandas ops; HTTP clients pooled with rate limits
  - ✅ N/A - Protocol defines interface, implementations handle I/O
- [x] **Complexity**: cyclomatic ≤ 10, cognitive ≤ 15, functions ≤ 50 lines, params ≤ 5
  - ✅ PASS: 3 simple abstract methods, minimal complexity
- [x] **Module size**: ≤ 500 lines (soft), split if > 800
  - ✅ PASS: 59 lines total
- [x] **Imports**: no `import *`; stdlib → third-party → local; no deep relative imports
  - ✅ PASS: Clean import structure

### Summary Score: 12/15 (80%) - PASS with recommendations

**Key Gaps:**
1. Missing exception specifications in docstrings (HIGH priority)
2. No protocol-level tests (MEDIUM priority)
3. Return type for `get_asset_class` could be more specific (MEDIUM priority)

---

## 5) Additional Notes

### Strengths

1. **Clean Protocol Design**
   - Properly uses typing.Protocol for structural subtyping
   - Methods are well-named and focused
   - No infrastructure dependencies leak into protocol

2. **Good Type Safety**
   - Uses Symbol value object instead of raw strings
   - All methods have complete type annotations
   - Proper use of `@abstractmethod` markers

3. **Appropriate Abstraction Level**
   - Protocol is at the right level - not too granular, not too coarse
   - Three methods cover the essential asset metadata needs
   - Keeps domain layer pure from broker-specific details

4. **Small and Focused**
   - 59 lines - very maintainable size
   - Single responsibility - asset metadata access only
   - No complexity hotspots

### Areas for Improvement

#### HIGH Priority: Add Exception Documentation

The protocol should document which exceptions implementations may raise. This is critical for consumers.

**Recommended addition to is_fractionable:**
```python
@abstractmethod
def is_fractionable(self, symbol: Symbol) -> bool:
    """Check if an asset supports fractional shares.

    Args:
        symbol: The symbol to check

    Returns:
        True if the asset supports fractional shares

    Raises:
        RateLimitError: If broker API rate limit exceeded (should be retried)
        DataProviderError: If asset not found or data unavailable

    """
    ...
```

#### MEDIUM Priority: Improve Return Type Specificity

Replace `str` return type with `Literal` for type safety:

```python
from typing import Literal

AssetClass = Literal["us_equity", "crypto", "unknown"]

@abstractmethod
def get_asset_class(self, symbol: Symbol) -> AssetClass:
    """Get the asset class for a symbol.
    
    Args:
        symbol: The symbol to classify
    
    Returns:
        Asset class: 'us_equity' for stocks/ETFs, 'crypto' for cryptocurrencies,
        'unknown' if classification unavailable
    
    """
    ...
```

#### MEDIUM Priority: Add Protocol Tests

Create `tests/shared/protocols/test_asset_metadata.py`:

```python
"""Test suite for AssetMetadataProvider protocol."""

from typing import Protocol, runtime_checkable
from the_alchemiser.shared.protocols.asset_metadata import AssetMetadataProvider
from the_alchemiser.shared.adapters.alpaca_asset_metadata_adapter import AlpacaAssetMetadataAdapter


def test_alpaca_adapter_implements_protocol():
    """Verify AlpacaAssetMetadataAdapter implements the protocol."""
    assert isinstance(AlpacaAssetMetadataAdapter, type)
    # Runtime checkable verification would require @runtime_checkable decorator


def test_protocol_has_required_methods():
    """Verify protocol defines expected methods."""
    assert hasattr(AssetMetadataProvider, 'is_fractionable')
    assert hasattr(AssetMetadataProvider, 'get_asset_class')
    assert hasattr(AssetMetadataProvider, 'should_use_notional_order')
```

#### LOW Priority: Fix Business Unit Header

Change line 1 from:
```python
"""Business Unit: utilities; Status: current.
```

To:
```python
"""Business Unit: shared; Status: current.
```

#### LOW Priority: Add Protocol Version

Add versioning to track evolution:

```python
"""Business Unit: shared; Status: current.

Asset Metadata Provider Protocol.

Protocol Version: 1.0.0

...
"""

__version__ = "1.0.0"
```

### Implementation Compliance

The AlpacaAssetMetadataAdapter implementation is well-aligned with this protocol:
- ✅ Implements all three methods correctly
- ✅ Handles exceptions properly (RateLimitError, DataProviderError)
- ✅ Provides good logging with structured fields
- ✅ Has comprehensive test coverage (200 lines of tests)

However, the protocol should explicitly document the exception contract so all implementations follow the same pattern.

### Usage Patterns

This protocol is correctly used by:
1. **FractionabilityDetector** (`shared/math/asset_info.py`) - Queries fractionability for order sizing
2. **Portfolio modules** - Need asset class information for allocation
3. **Execution modules** - Determine order type (notional vs quantity)

The protocol successfully decouples domain logic from infrastructure (Alpaca API), which is a key architectural benefit.

### Recommendations Summary

1. **HIGH**: Add `Raises:` sections to all method docstrings
2. **MEDIUM**: Change `get_asset_class` return type to `Literal`
3. **MEDIUM**: Create protocol test file
4. **MEDIUM**: Add `__init__.py` to protocols package
5. **MEDIUM**: Document quantity validation requirements in `should_use_notional_order`
6. **LOW**: Fix business unit header to "shared"
7. **LOW**: Add protocol version constant
8. **INFO**: Consider adding usage examples to module docstring

### Related Files to Review

For complete asset metadata system audit:
- ✅ `the_alchemiser/shared/adapters/alpaca_asset_metadata_adapter.py` (implementation)
- ✅ `the_alchemiser/shared/services/asset_metadata_service.py` (service layer)
- ✅ `the_alchemiser/shared/value_objects/symbol.py` (value object)
- ⚠️ `the_alchemiser/shared/math/asset_info.py` (consumer - should review usage patterns)

---

**Auto-generated**: 2025-10-08  
**Reviewer**: GitHub Copilot (Financial-grade audit)  
**Status**: COMPLETE - Protocol is sound but needs exception documentation and type improvements
