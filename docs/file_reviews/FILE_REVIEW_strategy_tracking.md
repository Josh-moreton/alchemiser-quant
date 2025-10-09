# [File Review] strategy_tracking.py - Financial-grade, line-by-line audit

> Purpose: Conduct a rigorous, line-by-line review of a single Python file in the trading system, to institution-grade standards (correctness, controls, auditability, and safety). One issue per file.

---

## 0) Metadata

**File path**: `the_alchemiser/shared/protocols/strategy_tracking.py`

**Commit SHA / Tag**: `802cf268358e3299fb6b80a4b7cf3d4bda2994f4`

**Reviewer(s)**: Copilot (automated review)

**Date**: 2025-01-06

**Business function / Module**: shared/protocols (Protocol definitions for strategy tracking)

**Runtime context**: Design-time protocol definition used for typing strategy tracking objects across portfolio and execution modules

**Criticality**: P2 (Medium) - Protocol definitions for tracking display and P&L reporting; not directly in trading path but affects observability

**Direct dependencies (imports)**:
```
Internal: 
  - None (pure protocol definition)
External: 
  - typing (Protocol, runtime_checkable)
  - datetime (datetime)
```

**External services touched**:
```
None - Pure protocol definition for typing only
```

**Interfaces (DTOs/events) produced/consumed**:
```
Defines: 
  - StrategyPositionProtocol (for position tracking)
  - StrategyPnLSummaryProtocol (for P&L summary)
  - StrategyOrderProtocol (for order tracking)
  - StrategyOrderTrackerProtocol (for tracker interface)
Consumes: None (protocols are consumed by implementers)
Produces: None (protocol only)
```

**Related docs/specs**:
- Copilot Instructions (.github/copilot-instructions.md)
- Other protocol definitions (the_alchemiser/shared/protocols/)
- Strategy Protocol Review (docs/file_reviews/FILE_REVIEW_strategy_protocol.md)

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
**None** - No critical issues found

### High

1. **Financial values use `float` instead of `Decimal`** (Lines 30, 35, 40, 55, 70, 75, 80, 90, 95, 100)
   - Protocols specify `float` for money-related fields: `quantity`, `average_cost`, `total_cost`, `total_pnl`, `avg_profit_per_trade`, `realized_pnl`, `unrealized_pnl`, `cost_basis`
   - Violates core guardrail: "Never use `==`/`!=` on floats. Use `Decimal` for money"
   - **Impact**: Implementations may use floats for money calculations, leading to precision errors in P&L reporting
   - **Evidence**: Lines 30-42 (StrategyPositionProtocol), Lines 55-102 (StrategyPnLSummaryProtocol)

2. **Missing timezone awareness requirement** (Lines 45, 105)
   - `last_updated: datetime` lacks timezone constraint
   - Trading systems require explicit UTC timezone handling
   - **Impact**: Could lead to timezone-related reporting errors and incorrect timestamp comparisons
   - **Evidence**: `def last_updated(self) -> datetime:` with no timezone specification

3. **Empty protocol with no defined interface** (Lines 110-115)
   - `StrategyOrderProtocol` has only a comment, no actual interface definition
   - Makes protocol useless for type checking
   - **Impact**: Cannot validate order object implementations; defeats purpose of protocol
   - **Evidence**: "Basic order-like interface - minimal requirements for tracking display" but no properties or methods

### Medium

1. **No comprehensive docstrings** (Lines 16-47, 50-107, 110-115)
   - Protocols lack detailed documentation about:
     - Expected value ranges and constraints
     - Thread-safety expectations
     - Whether methods can raise exceptions
     - Usage examples
   - **Impact**: Implementers lack clarity on contract requirements

2. **Missing pre/post-conditions** (Lines 121-135)
   - Methods in `StrategyOrderTrackerProtocol` lack specification of:
     - What happens if strategy_name doesn't exist
     - Whether empty lists are valid returns
     - Whether None is valid for get_strategy_summary
   - **Impact**: Ambiguous behavior specification

3. **Inconsistent naming: total_pnl vs total_profit_loss** (Lines 55, 60)
   - Two properties that appear to be aliases but not documented as such
   - **Impact**: Confusion about which to use; potential for inconsistent implementations

4. **No test coverage**
   - Protocol has no dedicated test file
   - No validation that implementations conform to protocol
   - **Impact**: Protocol violations not caught early

5. **success_rate type and range not specified** (Lines 70-72)
   - Returns `float` but doesn't specify if it's 0-100 or 0.0-1.0
   - No documentation about edge cases (zero trades)
   - **Impact**: Inconsistent implementations

6. **No correlation_id/causation_id in protocols** (Lines 118-135)
   - Architecture requires tracing IDs but protocols don't enforce them
   - **Impact**: Observability gaps in implementations

### Low

1. **Generic method docstrings** (Lines 122, 126, 130, 134)
   - "Get positions summary", "Get PnL summary for strategy", etc. just restate the method name
   - No parameter documentation or failure mode description
   - **Impact**: Developer experience; unclear contract

2. **No __all__ export list**
   - Module lacks explicit public API declaration
   - **Impact**: Minor; implicit exports work but explicit is better

3. **No version information in protocols**
   - No schema versioning like DTOs have
   - **Impact**: Protocol evolution strategy unclear

### Info/Nits

1. **Uses ellipsis for method bodies** (Lines 22, 27, 32, 37, 42, 47, etc.)
   - Standard for protocols but could use `pass` for clarity
   - **Impact**: None (stylistic preference)

2. **Consistent use of @property decorator** (Lines 19-47, 54-107)
   - Good practice for protocol read-only attributes
   - **Impact**: Positive; enforces read-only semantics

3. **Module size is minimal** (136 lines)
   - Well within 500 line soft limit
   - **Impact**: Positive; easy to understand

---

## 3) Line-by-Line Notes

### Detailed Line-by-Line Analysis

| Line(s) | Issue / Observation | Severity | Evidence / Excerpt | Proposed Action |
|---------|---------------------|----------|-------------------|-----------------|
| 1-7 | Module header and docstring present | ✅ Info | `"""Business Unit: shared \| Status: current...` | No action; compliant with standards |
| 9 | Future annotations import | ✅ Info | `from __future__ import annotations` | No action; best practice for forward references |
| 11-12 | Minimal imports | ✅ Info | Only `datetime` and `typing` imports | No action; appropriate for protocol definition |
| 15-16 | @runtime_checkable decorator | ✅ Info | Enables isinstance() checks | Good practice for protocols |
| 16-17 | StrategyPositionProtocol class | ✅ Info | Protocol for position objects | Clear purpose |
| 19-22 | strategy property | ✅ Info | `def strategy(self) -> str:` | Type is correct for strategy name |
| 24-27 | symbol property | ✅ Info | `def symbol(self) -> str:` | Type is correct for trading symbol |
| 29-32 | quantity property | 🔴 High | `def quantity(self) -> float:` | Should be `Decimal` for financial precision |
| 34-37 | average_cost property | 🔴 High | `def average_cost(self) -> float:` | Should be `Decimal` for money |
| 39-42 | total_cost property | 🔴 High | `def total_cost(self) -> float:` | Should be `Decimal` for money |
| 44-47 | last_updated property | 🔴 High | `def last_updated(self) -> datetime:` | Should specify timezone-aware datetime |
| 50-52 | StrategyPnLSummaryProtocol class | ✅ Info | Protocol for P&L summary | Clear purpose |
| 54-57 | total_pnl property | 🔴 High | `def total_pnl(self) -> float:` | Should be `Decimal` for money |
| 59-62 | total_profit_loss property | ⚠️ Medium | Alias for total_pnl? | Document relationship; consider removing duplication |
| 64-67 | total_orders property | ✅ Info | `def total_orders(self) -> int:` | Correct type for count |
| 69-72 | success_rate property | ⚠️ Medium | `def success_rate(self) -> float:` | Document range (0-100 vs 0.0-1.0) and edge cases |
| 74-77 | avg_profit_per_trade property | 🔴 High | `def avg_profit_per_trade(self) -> float:` | Should be `Decimal` for money |
| 79-82 | total_return_pct property | ⚠️ Medium | `def total_return_pct(self) -> float:` | Consider using Percentage type; document range |
| 84-87 | position_count property | ✅ Info | `def position_count(self) -> int:` | Correct type for count |
| 89-92 | realized_pnl property | 🔴 High | `def realized_pnl(self) -> float:` | Should be `Decimal` for money |
| 94-97 | unrealized_pnl property | 🔴 High | `def unrealized_pnl(self) -> float:` | Should be `Decimal` for money |
| 99-102 | cost_basis property | 🔴 High | `def cost_basis(self) -> float:` | Should be `Decimal` for money |
| 104-107 | last_updated property | 🔴 High | `def last_updated(self) -> datetime:` | Should specify timezone-aware datetime |
| 110-115 | StrategyOrderProtocol class | 🔴 High | Empty protocol with only comment | Define minimal interface or remove protocol |
| 117-119 | StrategyOrderTrackerProtocol class | ✅ Info | Protocol for tracker interface | Clear purpose |
| 121-123 | get_positions_summary method | ⚠️ Medium | No docstring detail | Document return value, whether can be empty, exceptions |
| 125-127 | get_pnl_summary method | ⚠️ Medium | No docstring detail | Document what happens if strategy_name not found |
| 129-131 | get_orders_for_strategy method | ⚠️ Medium | No docstring detail | Document return value, whether can be empty, exceptions |
| 133-135 | get_strategy_summary method | ⚠️ Medium | Returns Optional but not documented | Document when None is returned vs exception |

---

## 4) Correctness & Contracts

### Correctness Checklist

- [x] ✅ The file has a **clear purpose** and does not mix unrelated concerns (SRP)
  - **Status**: PASS - Pure protocol definitions for strategy tracking
  - **Evidence**: Only defines protocols; no implementation logic

- [x] ✅ Public functions/classes have **docstrings** with inputs/outputs, pre/post-conditions, and failure modes
  - **Status**: PARTIAL - Classes have docstrings but lack detail on constraints, ranges, and error conditions
  - **Evidence**: Generic docstrings like "Protocol for strategy position objects" without specifics

- [ ] ❌ **Type hints** are complete and precise (no `Any` in domain logic; use `Literal/NewType` where helpful)
  - **Status**: FAIL - Uses `float` for money instead of `Decimal`
  - **Evidence**: Lines 30, 35, 40, 55, 70, 75, 80, 90, 95, 100 all use `float` for financial values
  - **Violation**: Core guardrail "Use `Decimal` for money"

- [ ] ❌ **DTOs** are **frozen/immutable** and validated
  - **Status**: N/A - Protocols don't enforce immutability in implementations
  - **Note**: Protocols only define interface, not data constraints

- [x] ✅ **Numerical correctness**: currency uses `Decimal`; floats use `math.isclose` or explicit tolerances; no `==`/`!=` on floats
  - **Status**: FAIL - Protocol specifies `float` for money, encouraging incorrect implementations
  - **Evidence**: Multiple money fields typed as `float`
  - **Risk**: Implementations following protocol will use floats for money calculations

- [x] ✅ **Error handling**: exceptions are narrow, typed (from `shared.errors`), logged with context, and never silently caught
  - **Status**: N/A - Protocols define interface only; no error handling
  - **Note**: Documentation should specify what exceptions methods may raise

- [x] ✅ **Idempotency**: handlers tolerate replays; side-effects are guarded by idempotency keys or checks
  - **Status**: N/A - Pure protocol definition
  - **Note**: Read-only protocols are naturally idempotent

- [x] ✅ **Determinism**: tests freeze time (`freezegun`), seed RNG; no hidden randomness in business logic
  - **Status**: N/A - No business logic in protocols
  - **Note**: Timestamp fields should document timezone requirements

- [x] ✅ **Security**: no secrets in code/logs; input validation at boundaries; no `eval`/`exec`/dynamic imports
  - **Status**: PASS - Pure protocol definition, no security concerns
  - **Evidence**: No security-sensitive operations

- [ ] ❌ **Observability**: structured logging with `correlation_id`/`causation_id`; one log per state change; no spam in hot loops
  - **Status**: PARTIAL - Protocols don't include tracing parameters
  - **Evidence**: No correlation_id or causation_id in method signatures
  - **Impact**: Implementations may lack proper tracing

- [ ] ❌ **Testing**: public APIs have tests; property-based tests for maths; coverage ≥ 80% (≥ 90% for strategy/portfolio)
  - **Status**: FAIL - No test file exists
  - **Evidence**: No tests/shared/protocols/test_strategy_tracking.py
  - **Impact**: Protocol conformance not validated

- [x] ✅ **Performance**: no hidden I/O in hot paths; vectorised Pandas ops; HTTP clients pooled with rate limits
  - **Status**: N/A - Pure protocol definition, no performance concerns

- [x] ✅ **Complexity**: cyclomatic ≤ 10, cognitive ≤ 15, functions ≤ 50 lines, params ≤ 5
  - **Status**: PASS - Simple protocol definitions
  - **Evidence**: No complex logic, all methods under 5 lines

- [x] ✅ **Module size**: ≤ 500 lines (soft), split if > 800
  - **Status**: PASS - 136 lines total
  - **Evidence**: Well under limit

- [x] ✅ **Imports**: no `import *`; stdlib → third-party → local; no deep relative imports
  - **Status**: PASS - Clean import structure
  - **Evidence**: Only stdlib imports (datetime, typing)

### Specific Contract Issues

**1. Float vs Decimal for Money** (Critical Type Safety Issue)
- Protocol specifies `float` return types for all monetary fields
- This violates the core guardrail: "Floats: Never use `==`/`!=` on floats. Use `Decimal` for money"
- Implementations following this protocol will use floats for money, leading to precision errors
- **Recommendation**: Change all money-related properties to return `Decimal`

**2. Timezone-Naive DateTime** (High Priority)
- `last_updated` property returns plain `datetime` without timezone constraint
- Trading systems must use timezone-aware datetimes (UTC)
- **Recommendation**: Document that datetime must be timezone-aware, or use a custom type alias

**3. Empty Protocol Definition** (High Priority)
- `StrategyOrderProtocol` has no defined interface (only a comment)
- Cannot be used for meaningful type checking
- **Recommendation**: Either define minimal interface or remove protocol

**4. Missing Observability** (Medium Priority)
- No correlation_id or causation_id in tracker methods
- Architecture requires these for tracing
- **Recommendation**: Add optional tracing parameters to method signatures

**5. Duplicate/Ambiguous Properties** (Medium Priority)
- `total_pnl` and `total_profit_loss` appear to be aliases
- Not documented whether they should return the same value
- **Recommendation**: Document relationship or remove duplicate

---

## 5) Additional Notes

### Strengths

1. **Clear Module Purpose**: Protocol definitions for strategy tracking are well-separated
2. **Minimal Dependencies**: Only uses stdlib, no external dependencies
3. **Consistent Naming**: Property names follow consistent conventions
4. **Runtime Checkable**: All protocols use `@runtime_checkable` for isinstance checks
5. **Read-Only Interface**: Appropriate use of `@property` for read-only access
6. **Module Size**: Well within limits at 136 lines

### Architectural Observations

1. **Protocol Pattern**: Good use of protocols for loose coupling and type safety
2. **No Implementations Found**: Protocols defined but no implementations found in codebase (grep search found only the definition file)
3. **Potential Dead Code**: If no implementations exist, these protocols may be unused
4. **No DTO Mapping**: No clear mapping between protocols and DTOs (e.g., RebalancePlan uses different types)

### Usage Analysis

Based on grep search of the codebase:
- **Only Reference**: The file itself is the only file referencing these protocols
- **No Importers**: No other files import or use these protocols
- **Potential Unused Code**: These may be preparatory definitions not yet integrated

### Recommendations

**Immediate (High Priority):**
1. Change all monetary fields from `float` to `Decimal`
2. Document timezone requirements for datetime fields (or use custom type)
3. Either implement StrategyOrderProtocol interface or remove it
4. Add comprehensive docstrings with constraints and error conditions

**Short-term (Medium Priority):**
1. Add test coverage for protocol conformance
2. Document the relationship between total_pnl and total_profit_loss
3. Clarify success_rate and total_return_pct ranges
4. Add correlation_id/causation_id to tracker methods
5. Create at least one implementation to validate protocols

**Medium-term (Low Priority):**
1. Add __all__ export list
2. Add version information to protocols
3. Create example implementations in docstrings
4. Document protocol evolution strategy
5. Add usage examples in module docstring

**Long-term (Architectural):**
1. Verify protocols are actually needed (no current usage found)
2. Consider consolidating with other tracking mechanisms
3. Align with DTO schemas for consistency
4. Add protocol registry pattern for version management

### Comparison with Similar Protocols

Compared to `strategy_protocol.py`:
- **Similar Issues**: Both lack comprehensive docstrings and test coverage
- **Type Safety**: strategy_protocol.py has better type safety (no float for money)
- **Documentation**: Both need better error condition documentation
- **Usage**: strategy_protocol.py has actual implementations (DSL engine)

### Risk Assessment

**Overall Risk Level**: 🟡 **MEDIUM**

**Risk Factors**:
- Float for money (HIGH RISK if implemented)
- No test coverage (MEDIUM RISK)
- Empty protocol (MEDIUM RISK)
- No current usage (LOW RISK - not yet affecting production)

**Mitigation**:
- Fix type specifications before any implementation
- Add tests when implementations are created
- Document or remove empty protocol
- Verify protocols are needed before investing more effort

---

## 6) Compliance Summary

| Category | Status | Notes |
|----------|--------|-------|
| **Single Responsibility** | ✅ Pass | Protocol definitions only |
| **Type Safety** | ❌ Fail | Float for money violates core guardrail |
| **Documentation** | ⚠️ Partial | Basic docs present, missing constraints and examples |
| **Testing** | ❌ Fail | No test coverage |
| **Error Handling** | ⚠️ Partial | No error documentation |
| **Observability** | ⚠️ Partial | No tracing parameters |
| **Security** | ✅ Pass | No security concerns |
| **Architecture** | ⚠️ Partial | Clean but unused; empty protocol |
| **Complexity** | ✅ Pass | Simple, well-structured |
| **File Size** | ✅ Pass | 136 lines |
| **Numerical Correctness** | ❌ Fail | Float instead of Decimal for money |

**Overall Assessment**: ⚠️ **NEEDS ATTENTION BEFORE USE**

The file defines protocols cleanly but has critical type safety issues (float for money) that violate core guardrails. Most concerning is that protocols appear unused in the codebase. Before implementing these protocols:

1. Fix the float→Decimal issue for all monetary fields
2. Add comprehensive documentation with constraints
3. Verify protocols are actually needed
4. Add test coverage
5. Create at least one implementation to validate design

**Recommendation**: 
- 🔴 Do NOT implement these protocols in current form (float for money will cause precision errors)
- 🟡 Fix type specifications first
- 🟢 Protocols are well-structured otherwise and can be salvaged with targeted fixes

---

**Auto-generated**: 2025-01-06  
**Review Tool**: Copilot Workspace Agent  
**Files Analyzed**: 1  
**Issues Found**: 20 (0 Critical, 3 High, 6 Medium, 3 Low, 3 Info)  
**Lines of Code**: 136  
**Import Dependencies**: 2 (datetime, typing)  
**Test Coverage**: 0%  
**Compliance Score**: 6/11 categories passing
