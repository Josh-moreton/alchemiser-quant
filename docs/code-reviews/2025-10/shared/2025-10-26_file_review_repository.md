# [File Review] Financial-grade, line-by-line audit

> Purpose: Conduct a rigorous, line-by-line review of a single Python file in the trading system, to institution-grade standards (correctness, controls, auditability, and safety). One issue per file.

---

## 0) Metadata

**File path**: `the_alchemiser/shared/protocols/repository.py`

**Commit SHA / Tag**: `HEAD` (commit 802cf268358e3299fb6b80a4b7cf3d4bda2994f4 not in current branch)

**Reviewer(s)**: Copilot (automated review)

**Date**: 2025-10-08

**Business function / Module**: shared/protocols (Protocol definitions for broker/trading interfaces)

**Runtime context**: Design-time protocol definitions; implemented by AlpacaManager at runtime

**Criticality**: P1 (High) - Core protocol definitions affecting all broker interactions, trading, account, and market data operations

**Direct dependencies (imports)**:
```
Internal: 
  - the_alchemiser.shared.schemas.broker (OrderExecutionResult)
  - the_alchemiser.shared.schemas.execution_report (ExecutedOrder)
  - the_alchemiser.shared.schemas.operations (OrderCancellationResult)
External: 
  - typing (TYPE_CHECKING, Any, Protocol)
  - decimal (Decimal)
  - alpaca.trading.requests (LimitOrderRequest, MarketOrderRequest, ReplaceOrderRequest) [TYPE_CHECKING only]
```

**External services touched**:
```
None directly - Pure protocol definitions
Implementations touch:
  - Alpaca Trading API (via AlpacaManager implementation)
  - Market data services (via AlpacaManager implementation)
```

**Interfaces (DTOs/events) produced/consumed**:
```
Defines three protocols:
  - AccountRepository: Account and position queries
  - MarketDataRepository: Market data and quote queries  
  - TradingRepository: Trading operations (orders, positions, liquidation)

Consumed by:
  - AlpacaManager (implements all three protocols)
  - Type hints throughout execution_v2, portfolio_v2, strategy_v2 modules

DTOs returned:
  - ExecutedOrder (order execution results)
  - OrderExecutionResult (order replacement results)
  - OrderCancellationResult (cancellation results)
```

**Related docs/specs**:
- `.github/copilot-instructions.md` - Copilot Instructions (Core guardrails, typing rules)
- `docs/ALPACA_COMPLIANCE_REPORT.md` - Alpaca architecture and boundaries
- `the_alchemiser/shared/brokers/alpaca_manager.py` - Primary implementation
- `tests/shared/types/test_strategy_protocol.py` - Example protocol test pattern

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

**NONE** - No critical issues found

### High

1. **Type inconsistency: float vs Decimal mixing** (Lines 42, 115-116)
   - `MarketDataRepository.get_current_price()` returns `float | None` (Line 42)
   - `TradingRepository.place_market_order()` accepts `qty: float | None` and `notional: float | None` (Lines 115-116)
   - **BUT** other methods correctly use `Decimal` for money/quantities (Lines 30, 34, 62, 81, 90)
   - **Impact**: Violates Copilot Instructions guardrail "Floats: Never use `==`/`!=` on floats. Use `Decimal` for money"
   - **Evidence**: Price and quantity are financial values requiring precision

2. **Missing runtime_checkable decorator** (Lines 23, 39, 51)
   - All three Protocol classes lack `@runtime_checkable` decorator
   - **Impact**: Cannot use `isinstance()` checks at runtime for protocol conformance
   - **Evidence**: Compare to `test_strategy_protocol.py` which expects runtime checking

### Medium

1. **Missing comprehensive docstrings for AccountRepository and MarketDataRepository** (Lines 23-48)
   - `AccountRepository` has minimal class docstring (Line 24)
   - `MarketDataRepository` has minimal class docstring (Line 40)
   - Neither documents: failure modes, idempotency, thread-safety, or error raising
   - **Impact**: Unclear contract for implementers

2. **Inconsistent docstring quality** (Lines 26-36 vs 63-97)
   - Methods in `AccountRepository` and `MarketDataRepository` have minimal docstrings (1 line)
   - Methods in `TradingRepository` have detailed docstrings with Args/Returns sections
   - **Impact**: Inconsistent developer experience, unclear contracts

3. **No explicit error documentation** (All methods)
   - No method documents which exceptions it may raise
   - No "Raises:" sections in any docstring
   - **Impact**: Implementers don't know what exceptions to handle or raise

4. **Backward compatibility property lacks deprecation warning** (Lines 219-233)
   - `trading_client` property marked as "for backward compatibility during migration"
   - Property should be marked with `@deprecated` or documented with timeline
   - Uses `Any` type with noqa comment (Line 222)
   - **Impact**: Property may remain indefinitely; hard to track migration progress

5. **No test coverage** 
   - No test file `tests/shared/protocols/test_repository.py` exists
   - No validation that AlpacaManager properly implements protocols
   - **Impact**: Protocol violations not caught early

### Low

1. **Generic dict return types** (Lines 26, 46, 72, 186, 195)
   - Methods return `dict[str, Any]` without structured DTOs
   - Only `get_account()` and `get_quote()` - other methods use proper DTOs
   - **Impact**: Reduced type safety, unclear data structure contracts

2. **Missing validation of symbol format** (All symbol parameters)
   - No specification of symbol format (e.g., uppercase, no spaces)
   - No validation requirements documented
   - **Impact**: May accept invalid symbols

3. **No pre/post-conditions specified** (All methods)
   - No formal specification of valid input states
   - No specification of output guarantees
   - **Impact**: Unclear contract boundaries

### Info/Nits

1. **Module docstring could be more detailed** (Lines 1-4)
   - Current docstring is generic
   - Could specify protocol design pattern rationale
   - Could reference Alpaca architecture document

2. **Import organization is correct** (Lines 6-20)
   - Proper use of `from __future__ import annotations`
   - Proper use of TYPE_CHECKING to avoid circular dependencies
   - Clean import organization

3. **File size is appropriate** (233 lines)
   - Well under 500-line soft limit
   - Well under 800-line hard limit

---

## 3) Line-by-Line Notes

### Detailed Line-by-Line Analysis

| Line(s) | Issue / Observation | Severity | Evidence / Excerpt | Proposed Action |
|---------|---------------------|----------|-------------------|-----------------|
| 1-4 | Module docstring present with Business Unit marker | ✅ Info | `"""Business Unit: shared \| Status: current...` | None - compliant |
| 6 | Correct use of future annotations | ✅ Info | `from __future__ import annotations` | None - best practice |
| 8 | Decimal imported (good for money) | ✅ Info | `from decimal import Decimal` | None - but see Line 42 |
| 9 | Proper typing imports | ✅ Info | `from typing import TYPE_CHECKING, Any, Protocol` | None |
| 11-20 | TYPE_CHECKING guard for circular deps | ✅ Info | Proper use to avoid runtime circular imports | None - excellent practice |
| 23 | **AccountRepository lacks @runtime_checkable** | High | `class AccountRepository(Protocol):` | Add `@runtime_checkable` decorator |
| 24 | Minimal class docstring | Medium | Single line description | Enhance with failure modes, thread-safety |
| 26-28 | get_account minimal docstring | Medium | Single line | Add Args, Returns, Raises sections |
| 26 | Generic dict return type | Low | `-> dict[str, Any] \| None` | Consider creating AccountInfo DTO |
| 30 | **Correct use of Decimal for buying power** | ✅ Info | `-> Decimal \| None` | None - compliant with guardrails |
| 31 | Minimal docstring | Medium | Single line | Expand documentation |
| 34 | **Correct use of Decimal for positions** | ✅ Info | `-> dict[str, Decimal]` | None - compliant |
| 35 | Minimal docstring | Medium | Single line | Expand documentation |
| 39 | **MarketDataRepository lacks @runtime_checkable** | High | `class MarketDataRepository(Protocol):` | Add `@runtime_checkable` decorator |
| 40 | Minimal class docstring | Medium | Single line | Enhance with contracts |
| 42 | **CRITICAL: float used for price** | High | `-> float \| None` | Change to `Decimal \| None` for financial precision |
| 43 | Minimal docstring | Medium | Single line | Expand with Raises section |
| 46 | Generic dict return type | Low | `-> dict[str, Any] \| None` | Consider QuoteInfo DTO |
| 47 | Minimal docstring | Medium | Single line | Expand documentation |
| 51 | **TradingRepository lacks @runtime_checkable** | High | `class TradingRepository(Protocol):` | Add `@runtime_checkable` decorator |
| 52-60 | Good comprehensive class docstring | ✅ Info | Multi-line with context | None - good practice |
| 62-70 | **Good docstring with Returns section** | ✅ Info | Proper format with details | None - follow this pattern elsewhere |
| 62 | Correct Decimal usage | ✅ Info | `-> dict[str, Decimal]` | None - compliant |
| 72-79 | Good docstring | ✅ Info | Args and Returns documented | None |
| 72 | Generic dict return (acceptable here) | Low | Account info from broker API | Consider future DTO |
| 81-88 | Good docstring | ✅ Info | Proper documentation | None |
| 81 | Correct Decimal usage | ✅ Info | `-> Decimal \| None` | None - compliant |
| 90-97 | Good docstring | ✅ Info | Proper documentation | None |
| 90 | Correct Decimal usage | ✅ Info | `-> Decimal \| None` | None - compliant |
| 99-109 | Good docstring | ✅ Info | Args, Returns documented | None |
| 99 | Proper DTO return type | ✅ Info | `-> ExecutedOrder` | None - type safe |
| 103 | Alpaca SDK type in protocol | ⚠️ Medium | `LimitOrderRequest \| MarketOrderRequest` | Acceptable in TYPE_CHECKING |
| 111-133 | Good comprehensive docstring | ✅ Info | Args, Returns with details | None |
| 115-116 | **CRITICAL: float for qty/notional** | High | `qty: float \| None`, `notional: float \| None` | Change to `Decimal \| None` |
| 119 | Proper DTO return type | ✅ Info | `-> ExecutedOrder` | None |
| 135-145 | Good docstring | ✅ Info | Args, Returns documented | None |
| 135 | Proper DTO return type | ✅ Info | `-> OrderCancellationResult` | None |
| 147-160 | Good docstring | ✅ Info | Args, Returns documented | None |
| 148 | Alpaca SDK type in signature | ⚠️ Medium | `ReplaceOrderRequest \| None` | Acceptable in TYPE_CHECKING |
| 149 | Proper DTO return type | ✅ Info | `-> OrderExecutionResult` | None |
| 162-172 | Good docstring | ✅ Info | Args, Returns documented | None |
| 174-184 | Good docstring | ✅ Info | Args, Returns documented | None |
| 186-198 | Good docstring | ✅ Info | Args, Returns documented | None |
| 195 | Generic list[dict] return | Low | `-> list[dict[str, Any]]` | Consider PositionCloseResult DTO |
| 200-207 | Good docstring | ✅ Info | Returns documented | None |
| 209-217 | Good property docstring | ✅ Info | Returns documented | None |
| 219-233 | **Backward compat property needs deprecation** | Medium | "for backward compatibility during migration" | Add @deprecated or timeline |
| 222 | Intentional Any with noqa | ⚠️ Medium | `-> Any:  # noqa: ANN401` | Acceptable for broker SDK object |
| 224-232 | Verbose deprecation note | ✅ Info | Clear explanation of temporary nature | None - but add timeline |

### Additional Observations

**Type Safety**:
- ✅ Most methods use proper type hints with DTOs
- ✅ Correct use of `Decimal` for money/quantities in 6 methods
- ❌ **Inconsistent: `float` used in 3 locations** (Lines 42, 115, 116)
- ✅ Proper use of TYPE_CHECKING to avoid circular imports
- ⚠️ Generic `dict[str, Any]` return types in 3 methods (acceptable for legacy API wrappers)

**Protocol Design**:
- ✅ Three protocols with clear separation of concerns
- ✅ `TradingRepository` is well-documented with comprehensive docstrings
- ❌ `AccountRepository` and `MarketDataRepository` lack detail
- ❌ **All three protocols missing `@runtime_checkable` decorator**
- ✅ No `__init__` methods defined (correct for protocols)

**Documentation Quality**:
- ✅ 12 out of 16 methods have good docstrings with Args/Returns
- ❌ 4 methods have minimal single-line docstrings
- ❌ **No method documents exceptions/errors (missing "Raises:" sections)**
- ⚠️ No pre/post-conditions specified
- ⚠️ No idempotency requirements documented

**Complexity & Size**:
- ✅ File: 233 lines (well within limits)
- ✅ No functions with complexity (protocols only)
- ✅ Clean protocol definitions without implementation
- ✅ No dead code

**Import Boundaries**:
- ✅ Only imports from `shared.schemas` (same module family)
- ✅ Alpaca SDK types only in TYPE_CHECKING block
- ✅ No imports from business modules (execution_v2, portfolio_v2, strategy_v2)
- ✅ Proper architectural layering maintained

---

## 4) Correctness & Contracts

### Correctness Checklist

- [x] The file has a **clear purpose** and does not mix unrelated concerns (SRP)
  - **Status**: ✅ PASS - Three related protocols for broker operations
- [x] Public functions/classes have **docstrings** with inputs/outputs, pre/post-conditions, and failure modes
  - **Status**: ⚠️ PARTIAL - `TradingRepository` well-documented; others minimal; **no "Raises:" sections**
- [ ] **Type hints** are complete and precise (no `Any` in domain logic; use `Literal/NewType` where helpful)
  - **Status**: ❌ **FAIL** - Inconsistent `float` vs `Decimal` usage for financial values (Lines 42, 115-116)
- [x] **DTOs** are **frozen/immutable** and validated (e.g., Pydantic v2 models with constrained types)
  - **Status**: ✅ PASS - Returns proper DTOs (ExecutedOrder, OrderExecutionResult, OrderCancellationResult)
- [ ] **Numerical correctness**: currency uses `Decimal`; floats use `math.isclose` or explicit tolerances; no `==`/`!=` on floats
  - **Status**: ❌ **FAIL** - `float` used for prices and quantities (Lines 42, 115-116) **violates core guardrail**
- [x] **Error handling**: exceptions are narrow, typed (from `shared.errors`), logged with context, and never silently caught
  - **Status**: ⚠️ N/A - Protocols don't implement error handling; **but should document expected exceptions**
- [x] **Idempotency**: handlers tolerate replays; side-effects are guarded by idempotency keys or checks
  - **Status**: ⚠️ N/A - Protocol level; **should document idempotency requirements for implementers**
- [x] **Determinism**: tests freeze time (`freezegun`), seed RNG; no hidden randomness in business logic
  - **Status**: ✅ N/A - Pure protocol definitions
- [x] **Security**: no secrets in code/logs; input validation at boundaries; no `eval`/`exec`/dynamic imports
  - **Status**: ✅ PASS - No security concerns in protocol definitions
- [x] **Observability**: structured logging with `correlation_id`/`causation_id`; one log per state change; no spam in hot loops
  - **Status**: ⚠️ N/A - Protocol level; **should document logging requirements**
- [ ] **Testing**: public APIs have tests; property-based tests for maths; coverage ≥ 80% (≥ 90% for strategy/portfolio)
  - **Status**: ❌ **FAIL** - No test file exists for these protocols
- [x] **Performance**: no hidden I/O in hot paths; vectorised Pandas ops; HTTP clients pooled with rate limits
  - **Status**: ✅ N/A - Pure protocol definitions
- [x] **Complexity**: cyclomatic ≤ 10, cognitive ≤ 15, functions ≤ 50 lines, params ≤ 5
  - **Status**: ✅ PASS - No implementation complexity (protocols only)
- [x] **Module size**: ≤ 500 lines (soft), split if > 800
  - **Status**: ✅ PASS - 233 lines (well within limits)
- [x] **Imports**: no `import *`; stdlib → third-party → local; no deep relative imports
  - **Status**: ✅ PASS - Clean import structure with TYPE_CHECKING guard

### Key Contract Issues

1. **Type System Inconsistency (HIGH PRIORITY)**
   - Methods use `Decimal` for money/quantities: `get_buying_power()`, `get_positions_dict()`, `get_portfolio_value()`
   - Methods use `float` for prices/quantities: `get_current_price()`, `place_market_order(qty, notional)`
   - **This violates Copilot Instructions core guardrail**
   - **Risk**: Floating-point precision errors in financial calculations

2. **Missing Runtime Checkability (HIGH PRIORITY)**
   - Protocols cannot be used with `isinstance()` checks
   - Testing protocol conformance requires manual verification
   - **Risk**: Runtime type errors not caught early

3. **Incomplete Documentation (MEDIUM PRIORITY)**
   - Inconsistent docstring quality across protocols
   - No exception documentation
   - No idempotency requirements
   - **Risk**: Unclear contracts for implementers

4. **Missing Tests (MEDIUM PRIORITY)**
   - No validation that AlpacaManager conforms to protocols
   - No tests for protocol structure
   - **Risk**: Protocol violations not caught in CI

---

## 5) Additional Notes

### Strengths

1. **Excellent Separation of Concerns**
   - Three distinct protocols: Account, MarketData, Trading
   - Clean interface boundaries
   - AlpacaManager implements all three (proper composition)

2. **Good Use of Type Hints**
   - DTOs properly returned (ExecutedOrder, OrderExecutionResult, OrderCancellationResult)
   - TYPE_CHECKING guard prevents circular dependencies
   - Proper use of Union types with None

3. **Most Methods Use Decimal Correctly**
   - `get_buying_power()`, `get_positions_dict()`, `get_portfolio_value()` all use Decimal
   - Shows awareness of financial precision requirements

4. **TradingRepository is Well-Documented**
   - Comprehensive class docstring explaining purpose
   - Detailed method docstrings with Args/Returns
   - Good example for the other protocols

### Recommendations

#### Immediate (High Priority)

1. **Fix Type Inconsistency (Breaking Change)**
   ```python
   # Change Line 42
   def get_current_price(self, symbol: str) -> Decimal | None:
   
   # Change Lines 115-116
   def place_market_order(
       self,
       symbol: str,
       side: str,
       qty: Decimal | None = None,
       notional: Decimal | None = None,
       *,
       is_complete_exit: bool = False,
   ) -> ExecutedOrder:
   ```
   - Update AlpacaManager implementation to convert float to Decimal
   - Update all callers to pass Decimal values
   - Add migration guide

2. **Add @runtime_checkable Decorators**
   ```python
   from typing import Protocol, runtime_checkable
   
   @runtime_checkable
   class AccountRepository(Protocol):
       ...
   
   @runtime_checkable
   class MarketDataRepository(Protocol):
       ...
   
   @runtime_checkable
   class TradingRepository(Protocol):
       ...
   ```

3. **Create Comprehensive Test Suite**
   - Create `tests/shared/protocols/test_repository.py`
   - Test protocol structure (methods, signatures)
   - Test AlpacaManager conforms to all three protocols
   - Test runtime isinstance checks work

#### Short-term (Medium Priority)

4. **Enhance Documentation**
   - Add comprehensive class docstrings to AccountRepository and MarketDataRepository
   - Add "Raises:" sections to all methods
   - Document idempotency requirements
   - Document thread-safety expectations
   - Add usage examples

5. **Add Deprecation Warning**
   ```python
   from warnings import warn
   from typing import deprecated  # Python 3.13+
   
   @property
   @deprecated("Use protocol methods directly; will be removed in v3.0")
   def trading_client(self) -> Any:
       ...
   ```

#### Long-term (Low Priority)

6. **Consider Structured DTOs**
   - Create `AccountInfo` DTO for `get_account()`
   - Create `QuoteInfo` DTO for `get_quote()`
   - Create `PositionCloseResult` DTO for `close_all_positions()`
   - Reduces reliance on `dict[str, Any]`

7. **Add Pre/Post-Conditions**
   - Specify valid symbol formats
   - Specify quantity constraints (positive, non-zero)
   - Specify state requirements (e.g., must be connected)

### Testing Strategy

**Unit Tests Needed** (`tests/shared/protocols/test_repository.py`):
```python
class TestAccountRepository:
    - test_protocol_has_required_methods
    - test_get_account_signature
    - test_get_buying_power_returns_decimal
    - test_get_positions_dict_returns_decimal_values
    - test_alpaca_manager_implements_protocol

class TestMarketDataRepository:
    - test_protocol_has_required_methods
    - test_get_current_price_signature
    - test_get_quote_signature
    - test_alpaca_manager_implements_protocol

class TestTradingRepository:
    - test_protocol_has_required_methods
    - test_all_method_signatures
    - test_place_market_order_parameters
    - test_alpaca_manager_implements_protocol
    - test_trading_client_property_exists

class TestProtocolConformance:
    - test_runtime_isinstance_checks_work
    - test_mock_implementations_conform
    - test_method_signatures_match_implementation
```

### Performance Considerations

**Current Behavior**:
- Pure protocol definitions - no performance impact
- Used only for type checking and interface contracts

**No Performance Issues**:
- No I/O operations
- No computation
- No memory allocations
- Import time negligible (~1ms)

### Security Considerations

**Current Status**: ✅ SECURE
- No secrets or credentials
- No dynamic code execution
- No user input handling
- No external service calls

**Implementation Concern**:
- Implementations must validate symbol input
- Implementations must sanitize error messages (AlpacaManager does this correctly)

---

## 6) Compliance Matrix

| Requirement | Status | Evidence |
|------------|--------|----------|
| Module header with Business Unit/Status | ✅ | Lines 1-4 |
| Single Responsibility | ✅ | Protocol definitions for broker interfaces |
| Type hints complete | ⚠️ | **float vs Decimal inconsistency (Lines 42, 115-116)** |
| Type checking (mypy strict) | ✅ | No mypy errors found |
| Linting (ruff) | ✅ | All checks passed |
| Import boundaries | ✅ | No cross-module imports |
| Line count ≤ 500 | ✅ | 233 lines |
| Cyclomatic complexity ≤ 10 | ✅ | N/A (protocols only) |
| Test coverage ≥ 80% | ❌ | **No test file exists** |
| Security (no eval/exec/secrets) | ✅ | Only protocol definitions |
| Documentation | ⚠️ | **Inconsistent; missing Raises sections** |
| Decimal for money | ⚠️ | **Mixed: 6 methods correct, 3 methods use float** |
| runtime_checkable | ❌ | **Missing decorator on all three protocols** |

---

## 7) Verification Results

### Type Checking
```bash
$ poetry run mypy the_alchemiser/shared/protocols/repository.py --config-file=pyproject.toml
Success: no issues found in 1 source file
```

### Linting
```bash
$ poetry run ruff check the_alchemiser/shared/protocols/repository.py
All checks passed!
```

### Import Boundaries
```bash
# Check no imports from business modules
$ grep -r "execution_v2\|portfolio_v2\|strategy_v2" the_alchemiser/shared/protocols/repository.py
# (No output - clean)
```

### Tests
```bash
$ ls tests/shared/protocols/test_repository.py
ls: cannot access 'tests/shared/protocols/test_repository.py': No such file or directory
# ❌ Test file does not exist
```

---

## 8) Risk Assessment

### High Risk Items

1. **Type System Violation (Lines 42, 115-116)**
   - **Risk**: Financial precision errors from float arithmetic
   - **Probability**: High (every price/quantity operation)
   - **Impact**: Critical (money loss, incorrect trades)
   - **Mitigation**: Change to Decimal immediately

2. **Missing runtime_checkable**
   - **Risk**: Runtime type errors not caught
   - **Probability**: Medium (during testing/mocking)
   - **Impact**: High (debugging difficulty, runtime failures)
   - **Mitigation**: Add decorator immediately

### Medium Risk Items

3. **Incomplete Documentation**
   - **Risk**: Implementers misuse protocols
   - **Probability**: Medium (new implementations)
   - **Impact**: Medium (bugs, inconsistent behavior)
   - **Mitigation**: Enhance docstrings

4. **No Test Coverage**
   - **Risk**: Protocol violations not caught
   - **Probability**: High (any implementation change)
   - **Impact**: Medium (delayed bug discovery)
   - **Mitigation**: Create test suite

### Low Risk Items

5. **Generic dict return types**
   - **Risk**: Reduced type safety
   - **Probability**: Low (stable broker APIs)
   - **Impact**: Low (minor developer friction)
   - **Mitigation**: Consider DTOs in future

---

## 9) Action Items Summary

### Must Fix (Before Production)

- [ ] **Change `float` to `Decimal` for financial values** (Lines 42, 115-116)
- [ ] **Add `@runtime_checkable` decorators** to all three protocols
- [ ] **Create comprehensive test suite** (`tests/shared/protocols/test_repository.py`)

### Should Fix (This Sprint)

- [ ] **Enhance docstrings** for AccountRepository and MarketDataRepository
- [ ] **Add "Raises:" sections** to all method docstrings
- [ ] **Document idempotency requirements** in class docstrings
- [ ] **Add deprecation warning** to `trading_client` property

### Nice to Have (Future)

- [ ] Create structured DTOs for `get_account()` and `get_quote()`
- [ ] Add pre/post-condition specifications
- [ ] Add usage examples to class docstrings
- [ ] Consider splitting into separate files if more protocols added

---

**Audit completed**: 2025-10-08  
**Auditor**: Copilot AI Agent  
**Overall Assessment**: ⚠️ **CONDITIONAL APPROVAL** - Fix type inconsistency and add tests before production use  
**Next Review**: After Decimal migration and test suite completion
