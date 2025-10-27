# [File Review] strategy_protocol.py - Financial-grade, line-by-line audit

> Purpose: Conduct a rigorous, line-by-line review of a single Python file in the trading system, to institution-grade standards (correctness, controls, auditability, and safety). One issue per file.

---

## 0) Metadata

**File path**: `the_alchemiser/shared/types/strategy_protocol.py`

**Commit SHA / Tag**: `802cf268358e3299fb6b80a4b7cf3d4bda2994f4`

**Reviewer(s)**: Copilot (automated review)

**Date**: 2025-10-06

**Business function / Module**: shared/types (Protocol definitions)

**Runtime context**: Design-time protocol definition used across strategy implementations

**Criticality**: P1 (High) - Core protocol definition affecting all strategy implementations

**Direct dependencies (imports)**:
```
Internal: 
  - shared.types.market_data_port (MarketDataPort)
  - shared.types.strategy_value_objects (StrategySignal)
External: 
  - typing (Protocol, runtime_checkable)
  - datetime (datetime)
```

**External services touched**:
```
None - Pure protocol definition
```

**Interfaces (DTOs/events) produced/consumed**:
```
Defines: StrategyEngine protocol
Consumes: MarketDataPort, StrategySignal
Produces: N/A (protocol only)
```

**Related docs/specs**:
- Copilot Instructions (.github/copilot-instructions.md)
- Strategy v2 Architecture (the_alchemiser/strategy_v2/README.md)
- DSL Strategy Engine (the_alchemiser/strategy_v2/engines/dsl/strategy_engine.py)

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

1. **Protocol defines `__init__` method** (Lines 21-23)
   - Protocols should not define `__init__` with implementation details
   - Python Protocols with runtime checking don't support `__init__` signature checking properly
   - This creates confusion about protocol implementation requirements
   - **Impact**: Implementations may not properly implement initialization, leading to runtime errors

2. **Duplicate StrategyEngine protocol exists** (Different file: `strategy_v2/core/registry.py`)
   - Two different protocols with same name but incompatible signatures
   - Registry protocol has `__call__` method, this one has `generate_signals`
   - **Impact**: Type confusion, incorrect implementations, maintenance burden

### High

1. **Missing timezone awareness requirement** (Line 25)
   - `timestamp: datetime` parameter lacks timezone constraint
   - Trading systems require explicit timezone handling (UTC)
   - **Impact**: Could lead to timezone-related trading errors

2. **Missing comprehensive error documentation** (Line 37-46)
   - `validate_signals` only documents ValueError, but implementations may raise other exceptions
   - No documentation about idempotency requirements
   - No documentation about thread-safety expectations
   - **Impact**: Unclear contract for implementers

### Medium

1. **No test coverage** 
   - Protocol has no dedicated test file (tests/shared/types/test_strategy_protocol.py does not exist)
   - No validation that implementations conform to protocol
   - **Impact**: Protocol violations not caught early

2. **Missing pre/post-conditions** (Lines 25-35, 37-46)
   - Docstrings lack formal pre/post-conditions
   - No specification of what constitutes a "valid" signal
   - No specification of empty list behavior
   - **Impact**: Ambiguous contract implementation

3. **Missing schema version** 
   - Protocol interface not versioned
   - Breaking changes to protocol could silently break implementations
   - **Impact**: Difficult to manage protocol evolution

4. **Missing correlation_id/causation_id tracing** (Line 25)
   - Event-driven architecture requirement from copilot instructions not reflected
   - No way to track signal generation through system
   - **Impact**: Reduced observability and traceability

### Low

1. **No examples in docstrings** (Lines 25-35, 37-46)
   - Would help implementers understand expected usage
   - **Impact**: Developer experience

2. **Incomplete module docstring** (Lines 1-6)
   - Missing information about protocol evolution strategy
   - Missing information about implementations
   - **Impact**: Documentation quality

3. **Generic return type** (Line 25)
   - Returns `list[StrategySignal]` but doesn't specify if empty lists are allowed
   - **Impact**: Ambiguous behavior specification

### Info/Nits

1. **Uses ellipsis for method bodies** (Lines 23, 35, 47)
   - Standard for protocols but could use `pass` for clarity
   - **Impact**: None (stylistic)

---

## 3) Line-by-Line Notes

### Detailed Line-by-Line Analysis

| Line(s) | Issue / Observation | Severity | Evidence / Excerpt | Proposed Action |
|---------|---------------------|----------|-------------------|-----------------|
| 1-6 | Module header follows standards | ✅ Pass | `"""Business Unit: shared \| Status: current.` | None - compliant |
| 8 | Future annotations import | ✅ Pass | `from __future__ import annotations` | None - required for Python 3.9+ forward refs |
| 10 | datetime import | ⚠️ Info | `from datetime import datetime` | Consider importing `timezone` as well for docs |
| 11 | Protocol imports | ✅ Pass | `from typing import Protocol, runtime_checkable` | None - correct usage |
| 13 | MarketDataPort import | ✅ Pass | Relative import from same package | None - correct |
| 14 | StrategySignal import | ✅ Pass | Relative import from same package | None - correct |
| 17 | runtime_checkable decorator | ⚠️ Medium | `@runtime_checkable` | Incompatible with `__init__` signature checking |
| 18-19 | Class definition | ✅ Pass | Protocol class with docstring | None - correct |
| 21-23 | **`__init__` in Protocol** | 🔴 Critical | Protocols should not define `__init__` | Remove `__init__` or convert to abstract base class |
| 25 | generate_signals signature | 🟡 High | `timestamp: datetime` lacks timezone constraint | Add type constraint or document UTC requirement |
| 25-35 | generate_signals method | 🟡 Medium | Missing examples, pre/post-conditions | Add comprehensive docstring with examples |
| 26-34 | Docstring structure | ⚠️ Low | Basic Args/Returns, missing Raises | Add Raises section for potential exceptions |
| 37-46 | validate_signals method | 🟡 High | Only documents ValueError | Document all possible exceptions |
| 38-45 | Docstring | ⚠️ Medium | Missing examples of what constitutes "invalid" | Add examples of validation failures |
| 47 | Ellipsis for method body | ℹ️ Info | Standard protocol pattern | No change needed |

---

## 4) Correctness & Contracts

### Correctness Checklist

- [x] The file has a **clear purpose** and does not mix unrelated concerns (SRP)
  - ✅ Focused on defining strategy engine protocol
  
- [x] Public functions/classes have **docstrings** with inputs/outputs
  - ⚠️ Docstrings present but incomplete (missing pre/post-conditions, examples)
  
- [x] **Type hints** are complete and precise
  - ⚠️ Type hints present but lack constraints (timezone-aware datetime)
  
- [ ] **DTOs** are **frozen/immutable** and validated
  - ❌ N/A for Protocol, but referenced DTOs should be validated
  
- [x] **Numerical correctness**: N/A for this file
  
- [ ] **Error handling**: exceptions are narrow, typed, logged with context
  - ⚠️ Only ValueError documented, unclear what other exceptions may be raised
  
- [ ] **Idempotency**: handlers tolerate replays
  - ❌ Not documented whether `generate_signals` should be idempotent
  
- [x] **Determinism**: N/A for protocol definition
  
- [x] **Security**: no secrets in code/logs
  - ✅ No security concerns in protocol definition
  
- [ ] **Observability**: structured logging with correlation_id/causation_id
  - ❌ Protocol doesn't include tracing parameters required by architecture
  
- [ ] **Testing**: public APIs have tests
  - ❌ No test file exists for this protocol
  
- [x] **Performance**: N/A for protocol definition
  
- [x] **Complexity**: cyclomatic ≤ 10, cognitive ≤ 15, functions ≤ 50 lines
  - ✅ Simple protocol definition, no complexity issues
  
- [x] **Module size**: ≤ 500 lines (soft)
  - ✅ 47 lines total
  
- [x] **Imports**: no `import *`; stdlib → third-party → local
  - ✅ Imports correctly organized

### Specific Contract Issues

1. **`__init__` in Protocol is problematic**
   - Python's `Protocol` with `runtime_checkable` doesn't properly check `__init__` signatures
   - The `DslStrategyEngine` implementation has additional parameters (`strategy_file: str | None = None`) beyond what the protocol defines
   - This creates a mismatch where runtime checks may pass but the protocol isn't truly enforced

2. **Missing correlation/causation IDs**
   - Architecture requires event-driven handlers to be idempotent and traceable
   - `generate_signals` should accept `correlation_id` and `causation_id` parameters
   - Current implementations work around this by generating IDs internally

3. **Timezone ambiguity**
   - Trading system must use timezone-aware timestamps (UTC)
   - Protocol doesn't enforce this, allowing naive datetime objects
   - Could lead to subtle timezone bugs in production

4. **Duplicate protocol definition**
   - `strategy_v2/core/registry.py` defines a different `StrategyEngine` protocol
   - Registry version: `def __call__(context: ...) -> StrategyAllocation`
   - This version: `def generate_signals(timestamp: ...) -> list[StrategySignal]`
   - **This is a critical architectural issue requiring resolution**

---

## 5) Additional Notes

### Architectural Concerns

1. **Protocol vs ABC Choice**
   - Current use of `Protocol` may not be appropriate given the `__init__` requirement
   - Consider converting to `ABC` (Abstract Base Class) if initialization contract is important
   - Or remove `__init__` from protocol and document initialization separately

2. **Protocol Duplication Resolution**
   - Two protocols exist with same name but different interfaces
   - Need to determine which is canonical
   - Options:
     - Rename one protocol to clarify purpose
     - Merge protocols if they serve similar purposes
     - Keep separate but document their different use cases

3. **Event-Driven Architecture Integration**
   - Current protocol doesn't align with event-driven architecture requirements
   - Consider adding:
     - `correlation_id: str` parameter to `generate_signals`
     - `causation_id: str | None = None` parameter
     - Idempotency guarantees in docstring

### Implementation Analysis

The `DslStrategyEngine` implementation (primary user of this protocol):
- ✅ Implements `generate_signals` with correct signature (plus optional `max_workers`)
- ✅ Implements `validate_signals` 
- ⚠️ Has extra `__init__` parameters not in protocol (`strategy_file: str | None`)
- ⚠️ Generates `correlation_id` internally rather than receiving it
- ✅ Returns `list[StrategySignal]` as specified

### Recommendations

**Immediate (Critical):**
1. Resolve protocol duplication - choose one canonical definition
2. Remove `__init__` from protocol or convert to ABC
3. Add timezone-aware datetime type constraint or documentation

**Short-term (High):**
1. Add comprehensive docstrings with examples
2. Document all possible exceptions
3. Add test coverage for protocol conformance
4. Add correlation_id/causation_id to protocol signature

**Medium-term (Medium):**
1. Version the protocol interface
2. Add protocol evolution strategy to documentation
3. Create protocol validation tests
4. Document thread-safety expectations

**Long-term (Low):**
1. Consider protocol registry pattern for version management
2. Add protocol compliance checking in CI
3. Create example implementations for documentation

### Testing Recommendations

Create `tests/shared/types/test_strategy_protocol.py`:
```python
"""Tests for StrategyEngine protocol conformance."""

from datetime import datetime, timezone
from typing import TYPE_CHECKING

import pytest

from the_alchemiser.shared.types import StrategyEngine, StrategySignal
from the_alchemiser.shared.types.market_data_port import MarketDataPort


class MockMarketDataPort:
    """Mock implementation for testing."""
    pass


class ConformingEngine:
    """Test implementation that conforms to protocol."""
    
    def __init__(self, market_data_port: MarketDataPort) -> None:
        self.market_data_port = market_data_port
    
    def generate_signals(self, timestamp: datetime) -> list[StrategySignal]:
        return []
    
    def validate_signals(self, signals: list[StrategySignal]) -> None:
        pass


def test_protocol_conformance():
    """Test that conforming implementation is recognized."""
    engine = ConformingEngine(MockMarketDataPort())  # type: ignore[arg-type]
    assert isinstance(engine, StrategyEngine)


def test_generate_signals_timezone_awareness():
    """Test that implementations handle timezone-aware timestamps."""
    engine = ConformingEngine(MockMarketDataPort())  # type: ignore[arg-type]
    
    # Should work with timezone-aware datetime
    aware_ts = datetime.now(timezone.utc)
    signals = engine.generate_signals(aware_ts)
    assert isinstance(signals, list)
```

---

## 6) Compliance Summary

| Category | Status | Notes |
|----------|--------|-------|
| **Single Responsibility** | ✅ Pass | Protocol definition only |
| **Type Safety** | ⚠️ Partial | Types present but constraints missing |
| **Documentation** | ⚠️ Partial | Basic docs, missing examples and details |
| **Testing** | ❌ Fail | No test coverage |
| **Error Handling** | ⚠️ Partial | Basic error docs, incomplete |
| **Observability** | ❌ Fail | No tracing support |
| **Security** | ✅ Pass | No security concerns |
| **Architecture** | ❌ Fail | Protocol duplication, __init__ issue |
| **Complexity** | ✅ Pass | Simple, well-structured |
| **File Size** | ✅ Pass | 47 lines |

**Overall Assessment**: ⚠️ **NEEDS ATTENTION**

The file defines a clear protocol but has critical architectural issues (protocol duplication, `__init__` in Protocol) and missing observability/tracing requirements. Immediate action required to resolve protocol conflicts and align with event-driven architecture.

---

**Auto-generated**: 2025-10-06  
**Review Tool**: Copilot Workspace Agent  
**Files Analyzed**: 1  
**Issues Found**: 15 (2 Critical, 2 High, 4 Medium, 4 Low, 3 Info)
