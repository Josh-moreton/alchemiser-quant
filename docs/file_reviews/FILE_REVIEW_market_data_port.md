# [File Review] the_alchemiser/shared/types/market_data_port.py

## Financial-grade, line-by-line audit

---

## 0) Metadata

**File path**: `the_alchemiser/shared/types/market_data_port.py`

**Commit SHA / Tag**: `latest (commit 802cf26 not found in history, using HEAD)`

**Reviewer(s)**: Copilot AI Agent

**Date**: 2025-10-06

**Business function / Module**: shared/types

**Runtime context**: 
- Used across multiple modules (strategy_v2, execution_v2, orchestration)
- Protocol definition - no direct runtime execution
- Backtesting and live trading contexts

**Criticality**: P2 (Medium) - Core abstraction for market data access

**Direct dependencies (imports)**:
```python
Internal:
- the_alchemiser.shared.types.market_data (BarModel)
- the_alchemiser.shared.types.quote (QuoteModel)  # NOTE: INCORRECT IMPORT
- the_alchemiser.shared.value_objects.symbol (Symbol)

External:
- typing.Protocol, runtime_checkable
```

**External services touched**: 
- None directly (Protocol definition)
- Implementations access: Alpaca API (via MarketDataService)

**Interfaces (DTOs/events) produced/consumed**:
```python
Consumed by implementations:
- Symbol (value object)

Produced by implementations:
- BarModel (market_data.py)
- QuoteModel (TWO CONFLICTING DEFINITIONS - CRITICAL ISSUE)

Used by:
- MarketDataService (implements protocol)
- HistoricalMarketDataPort (backtest adapter)
- StrategyMarketDataAdapter (strategy layer)
- IndicatorService (strategy indicators)
```

**Related docs/specs**:
- Copilot Instructions (.github/copilot-instructions.md)
- Alpaca Architecture docs
- Port/Adapter pattern (hexagonal architecture)

---

## 1) Scope & Objectives

✅ **Achieved**: Verify the file's **single responsibility** and alignment with intended business capability.
✅ **Achieved**: Ensure **correctness**, **numerical integrity**, **deterministic behaviour** where required.
⚠️ **Issues Found**: **error handling**, **idempotency**, **observability**, **security**, and **compliance** controls.
❌ **Critical Issue**: Confirm **interfaces/contracts** (DTOs/events) are accurate, versioned, and tested.
✅ **Achieved**: Identify **dead code**, **complexity hotspots**, and **performance risks**.

---

## 2) Summary of Findings (use severity labels)

### Critical
1. **ACKNOWLEDGED TECHNICAL DEBT - Inconsistent QuoteModel Usage**: Line 13 imports `QuoteModel` from `the_alchemiser.shared.types.quote` (3-field "legacy" model), while a richer `QuoteModel` exists in `the_alchemiser.shared.types.market_data` (6-field "enhanced" model with bid_size/ask_size). 
   
   **Current State**: MarketDataService.get_latest_quote() has an explicit NOTE (line 102-105) acknowledging use of "legacy QuoteModel" and plans to migrate to the enhanced version.
   
   - `quote.py` (CURRENT): `ts: datetime | None`, `bid: Decimal`, `ask: Decimal` (3 fields)
   - `market_data.py` (TARGET): `symbol: str`, `bid_price: float`, `ask_price: float`, `bid_size: float`, `ask_size: float`, `timestamp: datetime` (6 fields)
   
   **Impact**: The port currently matches its implementation, BUT this is documented technical debt blocking "improved spread calculations". Two QuoteModels create confusion and import ambiguity. Migration is planned but not completed.

### High
2. **Missing Error Documentation**: Methods lack `Raises:` sections in docstrings. Critical for a port that abstracts external I/O operations which can fail.

3. **Incomplete Type Hints for Failure Modes**: Methods return `| None` but don't document under what conditions `None` is returned vs when exceptions should be raised. This ambiguity violates the principle of explicit error handling.

### Medium
4. **Vague Parameter Types**: `period` and `timeframe` are typed as `str` with admission "kept as strings initially to avoid broad refactors" (line 28). No validation contract, format specification, or examples provided. Different implementations interpret these differently.

5. **Missing Pre/Post-conditions**: Docstrings don't specify:
   - Valid formats for `period` and `timeframe`
   - Whether `None` return from `get_latest_quote` means "no quote available" vs "error occurred"
   - Whether empty list from `get_bars` is valid for "no data" or indicates error

6. **No Observable Behavior Specification**: Protocol methods use `...` (ellipsis) which is correct for Protocol, but lack contracts about side effects, idempotency, or timeouts.

7. **Missing Version Information**: No schema version field or DTO versioning for evolving the contract.

### Low
8. **Inconsistent Return Type Patterns**: 
   - `get_bars` returns `list[BarModel]` (never None - empty list implies no data)
   - `get_latest_quote` returns `QuoteModel | None`
   - `get_mid_price` returns `float | None`
   
   The mixed None-handling patterns are not explained. Should follow consistent convention (e.g., always return result types, use exceptions for errors).

9. **No Input Validation Specification**: Protocol doesn't specify if implementations should validate Symbol, or if consumers must validate before calling.

10. **Missing Example Usage**: Critical port interface lacks example usage in docstring.

### Info/Nits
11. **Module docstring could be more precise**: "minimal contract strategies need" - which strategies? All strategies? Only strategy_v2?

12. **Type annotation style**: Using modern `list[BarModel]` syntax is good, consistent with project style.

---

## 3) Line-by-Line Notes

### Detailed Line-by-Line Analysis

| Line(s) | Issue / Observation | Severity | Evidence / Excerpt | Proposed Action |
|---------|---------------------|----------|-------------------|-----------------|
| 1-6 | Module header correct with business unit and status | ✅ Good | `"""Business Unit: shared \| Status: current.` | None - compliant |
| 3-5 | Module docstring minimal but adequate | Info | "Domain port for market data access" | Consider adding examples |
| 8 | Future annotations import present | ✅ Good | Standard modern Python practice | None |
| 10 | Protocol and runtime_checkable imported | ✅ Good | Proper use of structural typing | None |
| 12 | BarModel import correct | ✅ Good | `from the_alchemiser.shared.types.market_data import BarModel` | None |
| 13 | **TECH DEBT: QuoteModel from legacy quote.py** | 🟡 Medium | `from the_alchemiser.shared.types.quote import QuoteModel` - MarketDataService NOTE confirms this is "legacy" version; enhanced version in market_data.py has bid_size/ask_size | Track migration to enhanced QuoteModel |
| 14 | Symbol import correct | ✅ Good | `from the_alchemiser.shared.value_objects.symbol import Symbol` | None |
| 17 | @runtime_checkable decorator applied | ✅ Good | Enables isinstance checks at runtime | None |
| 18 | Class name clear and follows convention | ✅ Good | `MarketDataPort` follows Port naming pattern | None |
| 19-23 | Class docstring adequate but minimal | Medium | Missing usage examples, error behavior | Add examples and failure modes |
| 25 | get_bars signature adequate | Medium | `period: str, timeframe: str` - vague types | Document format/examples |
| 26-29 | get_bars docstring incomplete | High | No Raises section, no format specs | Add error docs, param specs |
| 30 | Ellipsis correctly used for Protocol | ✅ Good | Protocol methods don't need implementation | None |
| 32-34 | get_latest_quote signature adequate | Low | Returns `\| None` without explaining when | Document None semantics |
| 36-38 | get_mid_price signature adequate | Low | Returns `\| None` without explaining when | Document None semantics |
| 38 | File ends without trailing blank line | Info/Nit | PEP 8 convention | Auto-fixed by formatter |

**Total lines**: 38 (excellent - well under 500 line soft limit, far from 800 hard limit)

**Cyclomatic complexity**: N/A (Protocol definition - no logic)

**Functions/methods**: 3 (all simple, well under 50 lines each)

---

## 4) Correctness & Contracts

### Correctness Checklist

- [x] The file has a **clear purpose** and does not mix unrelated concerns (SRP)
  - ✅ Single responsibility: defines market data port interface
- [x] Public functions/classes have **docstrings** with inputs/outputs, pre/post-conditions, and failure modes
  - ⚠️ Has docstrings but missing critical details (Raises, format specs, None semantics)
- [x] **Type hints** are complete and precise (no `Any` in domain logic; use `Literal/NewType` where helpful)
  - ⚠️ Type hints present but `str` too vague for `period`/`timeframe`; could use Literal or NewType
- [x] **DTOs** are **frozen/immutable** and validated (e.g., Pydantic v2 models with constrained types)
  - ✅ BarModel is frozen dataclass (checked in market_data.py)
  - ❌ **QuoteModel import is WRONG** - references wrong class
- [x] **Numerical correctness**: currency uses `Decimal`; floats use `math.isclose` or explicit tolerances; no `==`/`!=` on floats
  - ⚠️ `get_mid_price` returns `float | None` - should document precision expectations
  - Note: This is a Protocol, implementations handle numerical correctness
- [x] **Error handling**: exceptions are narrow, typed (from `shared.errors`), logged with context, and never silently caught
  - ❌ No error documentation in Protocol; implementations must handle but contract unclear
- [x] **Idempotency**: handlers tolerate replays; side-effects are guarded by idempotency keys or checks
  - ⚠️ Protocol doesn't specify if `get_bars` calls should be idempotent/cacheable
- [x] **Determinism**: tests freeze time (`freezegun`), seed RNG; no hidden randomness in business logic
  - ✅ N/A for Protocol definition
- [x] **Security**: no secrets in code/logs; input validation at boundaries; no `eval`/`exec`/dynamic imports
  - ✅ No security issues in Protocol definition
- [x] **Observability**: structured logging with `correlation_id`/`causation_id`; one log per state change; no spam in hot loops
  - ⚠️ Protocol doesn't specify observability requirements for implementations
- [x] **Testing**: public APIs have tests; property-based tests for maths; coverage ≥ 80% (≥ 90% for strategy/portfolio)
  - ❌ No dedicated test file for this Protocol (only indirect usage in test_registry.py)
- [x] **Performance**: no hidden I/O in hot paths; vectorised Pandas ops; HTTP clients pooled with rate limits
  - ✅ Protocol defines interface only; implementations handle performance
- [x] **Complexity**: cyclomatic ≤ 10, cognitive ≤ 15, functions ≤ 50 lines, params ≤ 5
  - ✅ All methods ≤ 3 params (excluding self), no logic, trivial complexity
- [x] **Module size**: ≤ 500 lines (soft), split if > 800
  - ✅ 38 lines - excellent
- [x] **Imports**: no `import *`; stdlib → third-party → local; no deep relative imports
  - ✅ Import structure correct, proper ordering
  - ❌ **But wrong QuoteModel imported**

---

## 5) Additional Notes

### Architectural Context
This file is a **Port** in the hexagonal architecture pattern. It defines the domain's contract for market data access, allowing different adapters (live trading via Alpaca, backtesting via historical data) to implement the same interface.

### Implementation Analysis
**Known Implementations**:
1. `MarketDataService` (the_alchemiser/shared/services/market_data_service.py) - production implementation

The implementation correctly uses `QuoteModel` from `quote.py` matching the port. However, MarketDataService has an explicit NOTE (lines 102-105) stating:
> "This still relies on the legacy QuoteModel from shared.types.quote. The enhanced QuoteModel in shared.types.market_data offers bid_size/ask_size for richer depth analytics, and migrating to it will unblock improved spread calculations."

This confirms the port is technically correct TODAY but represents documented technical debt.

### Testing Gaps
- No dedicated test file `tests/shared/types/test_market_data_port.py`
- Protocol only tested indirectly via strategy registry tests
- No property-based tests for port contract adherence
- No tests verifying implementations satisfy protocol

### Migration Considerations
The comment "period/timeframe kept as strings initially to avoid broad refactors" (line 28) suggests this is technical debt. Should be tracked and prioritized for cleanup.

### Recommendations

#### Immediate Actions (MUST FIX)
1. **Add comprehensive docstrings** with:
   - Raises sections
   - Parameter format specifications
   - Return value semantics (when None is returned)
   - Usage examples
2. **Create dedicated test file** `tests/shared/types/test_market_data_port.py`

#### Short-term Improvements (SHOULD FIX)
3. **Migrate to enhanced QuoteModel** - Follow through on documented migration plan from legacy quote.py to market_data.py QuoteModel (line 13, tracked in MarketDataService NOTE)
4. **Replace vague string types** - Create typed period/timeframe enums or use Literal types
5. **Add schema versioning** - Include version metadata for DTOs returned by port
6. **Document error handling contract** - Specify when implementations should raise vs return None
7. **Add integration tests** verifying all implementations satisfy the protocol

#### Long-term Enhancements (NICE TO HAVE)
8. **Add caching/memoization contract** - Specify if/how implementations should cache
9. **Add observability requirements** - Document logging/tracing expectations
10. **Consider async variant** - Add async methods for better I/O handling

---

## Action Items by Priority

### P0 - Critical (Fix Immediately)
None - port is functionally correct but has documented technical debt

### P1 - High (Fix This Sprint)
- [ ] Add Raises sections to all method docstrings
- [ ] Document None return semantics for get_latest_quote and get_mid_price
- [ ] Create tests/shared/types/test_market_data_port.py with protocol tests
- [ ] Document valid formats for period and timeframe parameters

### P2 - Medium (Fix Next Sprint)
- [ ] **Complete QuoteModel migration** - Migrate from legacy quote.py to enhanced market_data.py QuoteModel (tracked technical debt)
- [ ] Add usage examples to class and method docstrings
- [ ] Specify error handling contract (exceptions vs None)
- [ ] Consider typing period/timeframe with Literal or NewType
- [ ] Add integration tests for all implementations

### P3 - Low (Backlog)
- [ ] Add observability requirements to docstrings
- [ ] Document idempotency/caching expectations
- [ ] Consider async methods for I/O operations
- [ ] Track technical debt for period/timeframe string types

---

**Review Status**: ✅ **PASS WITH IMPROVEMENTS RECOMMENDED**

The file is functionally correct and architecturally sound. The QuoteModel import uses the "legacy" version deliberately (confirmed by implementation NOTE), but this represents documented technical debt that should be tracked. The lack of comprehensive documentation and tests should be addressed.

**Overall Assessment**: 
- Code quality: **7/10** (good structure, critical import bug)
- Documentation: **5/10** (basic but incomplete)
- Testing: **3/10** (minimal coverage)
- Maintainability: **8/10** (clean, simple, well-named)

---

**Auto-generated by**: Copilot AI Agent  
**Review Date**: 2025-10-06  
**File Version**: 2.10.7  
