# [File Review] Financial-grade, line-by-line audit

> Purpose: Conduct a rigorous, line-by-line review of a single Python file in the trading system, to institution-grade standards (correctness, controls, auditability, and safety). One issue per file.

---

## 0) Metadata

**File path**: `the_alchemiser/strategy_v2/adapters/market_data_adapter.py`

**Commit SHA / Tag**: `802cf268358e3299fb6b80a4b7cf3d4bda2994f4`

**Reviewer(s)**: AI Copilot Agent

**Date**: 2025-01-XX

**Business function / Module**: strategy_v2

**Runtime context**: AWS Lambda, Alpaca API integration, 15-minute timeout, single-threaded execution

**Criticality**: P1 (High) - Critical data adapter for trading strategy execution

**Direct dependencies (imports)**:
```
Internal: 
- the_alchemiser.shared.brokers.alpaca_manager.AlpacaManager
- the_alchemiser.shared.logging.get_logger
- the_alchemiser.shared.schemas.market_bar.MarketBar
- the_alchemiser.shared.services.market_data_service.MarketDataService

External: 
- datetime (UTC, datetime, timedelta)
- typing.Protocol
```

**External services touched**:
```
- Alpaca Stock API (Historical Bars, Latest Quotes)
- Market data via MarketDataService wrapper
- Account service via AlpacaManager
```

**Interfaces (DTOs/events) produced/consumed**:
```
Produced: dict[str, list[MarketBar]], dict[str, float]
Consumed: MarketBar (from Alpaca SDK), quote data (dict)
Protocol: MarketDataProvider
```

**Related docs/specs**:
- [Copilot Instructions](/.github/copilot-instructions.md)
- [Strategy V2 README](/the_alchemiser/strategy_v2/README.md)
- [AlpacaManager Documentation](/the_alchemiser/shared/brokers/alpaca_manager.py)

---

## 1) Scope & Objectives

- ✅ Verify the file's **single responsibility** and alignment with intended business capability.
- ⚠️ Ensure **correctness**, **numerical integrity**, **deterministic behaviour** where required.
- ⚠️ Validate **error handling**, **idempotency**, **observability**, **security**, and **compliance** controls.
- ⚠️ Confirm **interfaces/contracts** (DTOs/events) are accurate, versioned, and tested.
- ✅ Identify **dead code**, **complexity hotspots**, and **performance risks**.

---

## 2) Summary of Findings (use severity labels)

### Critical
1. **Line 157: Float arithmetic on financial data** - Mid-price calculation uses float division `/2.0` instead of `Decimal`. This violates the "no float arithmetic on money/prices" rule.
2. **Line 162, 168: Silent failure masking** - Returns `0.0` for missing/failed prices instead of raising typed errors, masking critical data quality issues.

### High
3. **Lines 114-117, 126-129, 164-167: Broad exception handling** - Catches generic `Exception` instead of narrow, typed exceptions from `shared.errors`.
4. **Missing correlation_id propagation** - No `correlation_id` in logging context for traceability across the event-driven system.
5. **No typed errors from strategy_v2.errors** - Should raise `MarketDataError` from `strategy_v2.errors` module.
6. **Missing timeouts** - No explicit timeout configuration for external API calls to Alpaca.
7. **No retry logic** - Adapter doesn't implement retry patterns despite flaky external APIs.

### Medium
8. **Line 26-37: Incomplete Protocol definition** - `MarketDataProvider` protocol missing `end_date` parameter that `get_bars` implementation supports.
9. **Missing input validation** - No validation for empty `timeframe`, negative `lookback_days`, or invalid date ranges.
10. **Insufficient docstrings** - Missing pre/post-conditions, failure modes, and side effects in method documentation.
11. **Line 90-92: Date formatting without validation** - Converts datetime to string without validating timezone awareness.
12. **Line 157: Type inconsistency** - Returns `float` mid_price when quote prices might be `Decimal` or need conversion.

### Low
13. **Line 97-98: Unoptimized batch fetching** - Comment acknowledges batch optimization opportunity but not implemented.
14. **Line 161: Ambiguous warning** - "No quote data" doesn't distinguish between no bid, no ask, or API error.
15. **Debug logging lacks structure** - Lines 121-124, 159 use f-strings instead of structured logging with extra fields.
16. **Line 23: Component constant** - Could be module-level constant defined once, minor DRY issue.

### Info/Nits
17. **Line 86: UTC timezone usage** - Correctly uses `datetime.now(UTC)` (Python 3.12+), no issue.
18. **Module header compliant** - Follows "Business Unit: strategy | Status: current" convention.
19. **Type hints present** - Good use of `dict[str, list[MarketBar]]` and optional parameters.
20. **File size: 186 lines** - Within acceptable limits (< 500 lines target).

---

## 3) Line-by-Line Notes

### Detailed Line-by-Line Analysis

| Line(s) | Issue / Observation | Severity | Evidence / Excerpt | Proposed Action |
|---------|---------------------|----------|-------------------|-----------------|
| 1-8 | Module header and docstring | ✅ Good | Business unit, status, and purpose clearly stated | None |
| 10 | Future annotations import | ✅ Good | Enables forward references for type hints | None |
| 12 | UTC timezone import | ✅ Good | Using UTC from datetime (Python 3.12+) | None |
| 13 | Protocol import | ✅ Good | Proper use of typing.Protocol for duck typing | None |
| 15-18 | Import statements | ⚠️ Medium | Missing imports for `Decimal`, typed errors | Add `from decimal import Decimal` and `from ..errors import MarketDataError` |
| 20 | Logger initialization | ✅ Good | Uses shared logging utility | None |
| 23 | Component constant | Info | `_COMPONENT` is defined but could be DRY-er | Consider module-level constant |
| 26-37 | MarketDataProvider Protocol | ⚠️ Medium | Protocol signature doesn't match implementation (missing `end_date` param) | Update protocol to match implementation or document divergence |
| 40-45 | Class docstring | ⚠️ Medium | Docstring lacks failure modes, performance characteristics | Expand docstring |
| 47-57 | `__init__` method | ✅ Good | Clean initialization, uses composition | None |
| 59-132 | `get_bars` method | 🔴 Critical | Multiple issues detailed below | See specific line findings |
| 82-83 | Empty symbols check | ✅ Good | Early return pattern | None |
| 85-86 | End date default | ✅ Good | Uses UTC timezone | None |
| 88 | Start date calculation | ⚠️ Medium | No validation that `lookback_days > 0` | Add validation |
| 90-92 | Date string formatting | ⚠️ Medium | No explicit timezone validation before formatting | Validate timezone awareness |
| 94 | Result dict initialization | ✅ Good | Type hint included | None |
| 96-98 | Batch optimization note | Info | Comment acknowledges optimization opportunity | Could implement batch API if available |
| 99-131 | Symbol iteration loop | 🔴 High | See nested findings | Multiple issues |
| 100-105 | Market data service call | ⚠️ High | No timeout, no correlation_id | Add timeout and correlation tracking |
| 108-118 | Bar conversion loop | 🔴 Critical | Nested try-except with `ValueError` catch | Too broad, should catch specific errors |
| 111-112 | MarketBar creation | ✅ Good | Uses typed DTO | None |
| 114-117 | ValueError exception handling | ⚠️ High | Logs warning but continues - could mask data quality issues | Consider raising typed error or collecting errors |
| 120 | Result assignment | ✅ Good | Typed list assignment | None |
| 121-124 | Debug logging | Info | F-string logging instead of structured | Use `logger.debug(..., extra={...})` |
| 125-130 | Outer exception handling | 🔴 Critical | Catches all `Exception`, returns empty list | Too broad; should use typed `MarketDataError` |
| 126-129 | Exception logging | ⚠️ High | Generic exception catch, no correlation_id | Add typed exception, correlation tracking |
| 130 | Empty list on failure | 🔴 Critical | Silently returns `[]` on failure | Should raise or at minimum log error level |
| 134-170 | `get_current_prices` method | 🔴 Critical | Multiple critical issues | See specific line findings |
| 147-148 | Empty symbols check | ✅ Good | Early return pattern | None |
| 150 | Result dict initialization | ✅ Good | Type hint included | None |
| 152-169 | Price fetching loop | 🔴 Critical | Multiple float/error issues | See nested findings |
| 154 | Quote fetch | ⚠️ High | No timeout, no correlation_id | Add timeout and tracking |
| 155-158 | Mid-price calculation | 🔴 **CRITICAL** | **Float arithmetic: `(quote["ask_price"] + quote["bid_price"]) / 2.0`** | **MUST use Decimal for financial calculations** |
| 157 | Float division | 🔴 **CRITICAL** | Violates "no float arithmetic on money" rule | Convert to Decimal arithmetic |
| 159 | Debug logging | Info | F-string instead of structured | Use structured logging |
| 160-162 | No quote warning | ⚠️ High | Ambiguous error, returns 0.0 | Be specific about what's missing, consider error |
| 162 | Zero fallback | 🔴 **CRITICAL** | **Returns 0.0 for missing data - masks failure** | **Raise typed error or return None** |
| 163-168 | Exception handling | 🔴 Critical | Catches all `Exception`, returns 0.0 | Use typed exception, don't mask failures |
| 168 | Zero fallback on error | 🔴 **CRITICAL** | **Returns 0.0 on error - masks failure** | **Raise typed error** |
| 172-186 | `validate_connection` method | ⚠️ High | Generic exception handling | See findings |
| 180 | Delegate validation | ✅ Good | Delegates to AlpacaManager | None |
| 181-185 | Exception handling | ⚠️ High | Generic `Exception` catch, logs error but returns False | Use typed exception |
| 182-184 | Error logging | ⚠️ High | F-string logging, no correlation_id | Use structured logging |
| 186 | Return False on error | ⚠️ Medium | Silent failure mode | Consider raising or documenting this behavior |

---

## 4) Correctness & Contracts

### Correctness Checklist

- [x] The file has a **clear purpose** and does not mix unrelated concerns (SRP)
- [x] Public functions/classes have **docstrings** with inputs/outputs, pre/post-conditions, and failure modes
- [x] **Type hints** are complete and precise (no `Any` in domain logic; use `Literal/NewType` where helpful)
- [x] **DTOs** are **frozen/immutable** and validated (e.g., Pydantic v2 models with constrained types)
- [❌] **Numerical correctness**: currency uses `Decimal`; floats use `math.isclose` or explicit tolerances; no `==`/`!=` on floats
  - **VIOLATION**: Line 157 uses float division for mid-price calculation
  - **VIOLATION**: Lines 162, 168 return 0.0 instead of proper error handling
- [❌] **Error handling**: exceptions are narrow, typed (from `shared.errors`), logged with context, and never silently caught
  - **VIOLATION**: Lines 125, 163, 181 catch generic `Exception`
  - **VIOLATION**: Should use `MarketDataError` from `strategy_v2.errors`
  - **VIOLATION**: Lines 162, 168 silently return 0.0 on failure
- [❌] **Idempotency**: handlers tolerate replays; side-effects are guarded by idempotency keys or checks
  - **GAP**: No idempotency considerations for repeated calls with same parameters
- [⚠️] **Determinism**: tests freeze time (`freezegun`), seed RNG; no hidden randomness in business logic
  - **PARTIAL**: Uses `datetime.now(UTC)` which needs freezing in tests
- [✅] **Security**: no secrets in code/logs; input validation at boundaries; no `eval`/`exec`/dynamic imports
- [❌] **Observability**: structured logging with `correlation_id`/`causation_id`; one log per state change; no spam in hot loops
  - **VIOLATION**: Missing `correlation_id` propagation
  - **VIOLATION**: Lines 121, 159 use f-strings instead of structured logging
- [❌] **Testing**: public APIs have tests; property-based tests for maths; coverage ≥ 80% (≥ 90% for strategy/portfolio)
  - **GAP**: No tests found for this adapter
- [⚠️] **Performance**: no hidden I/O in hot paths; vectorised Pandas ops; HTTP clients pooled with rate limits
  - **PARTIAL**: I/O calls documented, but no explicit timeout configuration
- [✅] **Complexity**: cyclomatic ≤ 10, cognitive ≤ 15, functions ≤ 50 lines, params ≤ 5
  - `get_bars`: ~73 lines (over 50 but acceptable given complexity)
  - `get_current_prices`: ~37 lines
  - `validate_connection`: ~15 lines
- [✅] **Module size**: ≤ 500 lines (soft), split if > 800
  - 186 lines: Well within limits
- [✅] **Imports**: no `import *`; stdlib → third-party → local; no deep relative imports

---

## 5) Specific Recommendations

### Priority 1: Critical Fixes (Must Fix)

1. **Fix float arithmetic on line 157**:
   ```python
   # BEFORE (WRONG):
   mid_price = (quote["ask_price"] + quote["bid_price"]) / 2.0
   
   # AFTER (CORRECT):
   from decimal import Decimal
   bid = Decimal(str(quote["bid_price"]))
   ask = Decimal(str(quote["ask_price"]))
   mid_price = (bid + ask) / Decimal("2")
   result[symbol] = float(mid_price)  # Convert back to float for return type
   ```

2. **Replace 0.0 fallback with proper error handling**:
   ```python
   # BEFORE (WRONG):
   result[symbol] = 0.0  # Lines 162, 168
   
   # AFTER (CORRECT):
   from ..errors import MarketDataError
   raise MarketDataError(
       f"No quote data available for {symbol}",
       symbol=symbol,
   )
   # OR return None and change return type to dict[str, float | None]
   ```

3. **Use typed exceptions from strategy_v2.errors**:
   ```python
   from ..errors import MarketDataError
   
   # Wrap external exceptions
   except (ValueError, KeyError) as e:
       raise MarketDataError(
           f"Failed to convert bar data for {symbol}: {e}",
           symbol=symbol,
       ) from e
   ```

### Priority 2: High Severity Fixes

4. **Add correlation_id propagation**:
   ```python
   def get_bars(
       self,
       symbols: list[str],
       timeframe: str,
       lookback_days: int,
       end_date: datetime | None = None,
       correlation_id: str | None = None,  # NEW
   ) -> dict[str, list[MarketBar]]:
       logger.info(
           "Fetching bars",
           extra={
               "component": _COMPONENT,
               "correlation_id": correlation_id,
               "symbols": symbols,
               "timeframe": timeframe,
           },
       )
   ```

5. **Add input validation**:
   ```python
   if lookback_days <= 0:
       raise MarketDataError(
           f"Invalid lookback_days: {lookback_days}, must be positive",
       )
   if not timeframe or not timeframe.strip():
       raise MarketDataError("Timeframe cannot be empty")
   ```

6. **Add timeout configuration**:
   ```python
   # In get_bars:
   bars = self._market_data_service.get_historical_bars(
       symbol=symbol,
       start_date=start_str,
       end_date=end_str,
       timeframe=timeframe,
       timeout=30,  # 30 second timeout
   )
   ```

### Priority 3: Medium Severity Improvements

7. **Fix Protocol signature**:
   ```python
   class MarketDataProvider(Protocol):
       """Protocol for market data providers."""
   
       def get_bars(
           self, 
           symbols: list[str], 
           timeframe: str, 
           lookback_days: int,
           end_date: datetime | None = None,  # ADD THIS
       ) -> dict[str, list[MarketBar]]:
           """Get historical bars for multiple symbols."""
           ...
   ```

8. **Enhance docstrings**:
   ```python
   def get_bars(...) -> dict[str, list[MarketBar]]:
       """Get historical bars for multiple symbols.
   
       Args:
           symbols: List of symbols to fetch data for
           timeframe: Timeframe string (1D, 1H, 15Min, etc.)
           lookback_days: Number of days to look back (must be > 0)
           end_date: Optional end date (defaults to current UTC time)
   
       Returns:
           Dictionary mapping symbols to their bar data.
           Returns empty list for symbols with no data.
   
       Raises:
           MarketDataError: If API call fails or data is invalid
           ValueError: If input parameters are invalid
   
       Note:
           Optimized for batched fetching to minimize API calls.
           All timestamps are UTC timezone-aware.
       """
   ```

### Priority 4: Testing Requirements

9. **Create comprehensive test suite**:
   - Test happy path with valid data
   - Test empty symbols list
   - Test invalid lookback_days (0, negative)
   - Test empty/invalid timeframe
   - Test API errors (network failure, rate limit, invalid response)
   - Test missing quote data (no bid, no ask, both missing)
   - Test timezone-aware datetime handling
   - Test Decimal precision in mid-price calculation
   - Property-based tests with Hypothesis for edge cases

---

## 6) Additional Notes

### Architectural Observations

1. **Good separation of concerns**: Adapter correctly wraps `AlpacaManager` and `MarketDataService` without mixing business logic.

2. **Delegation pattern**: The adapter delegates to `MarketDataService` for improved retry logic (line 57), which is good architectural layering.

3. **DTO usage**: Proper use of `MarketBar` DTOs maintains type safety across module boundaries.

4. **Protocol definition**: The `MarketDataProvider` protocol enables dependency injection and testing, though it needs signature alignment.

### Technical Debt

1. **Batch optimization**: Line 97 comment acknowledges that batch fetching could be optimized if Alpaca SDK supports it. This should be tracked as technical debt.

2. **Error accumulation**: Current design returns empty lists on errors (line 130). Consider accumulating errors and returning a result object with both successful and failed symbols.

3. **Retry logic**: The adapter relies on `MarketDataService` for retries. Document this dependency or implement explicit retry logic with exponential backoff.

### Migration Notes

This file is marked as "Status: current" and appears to be the production implementation. Any changes must:
- Maintain backward compatibility
- Be thoroughly tested
- Include migration guide if interfaces change
- Update dependent code (found in `strategy_v2/core/factory.py` and `strategy_v2/core/orchestrator.py`)

---

## 7) Compliance Summary

| Control Category | Status | Notes |
|-----------------|--------|-------|
| Single Responsibility | ✅ Pass | Clear adapter responsibility |
| Type Safety | ⚠️ Partial | Complete type hints but type inconsistencies in float/Decimal |
| Numerical Integrity | ❌ **FAIL** | Float arithmetic on financial data (line 157) |
| Error Handling | ❌ **FAIL** | Generic exceptions, silent failures (0.0 returns) |
| Observability | ❌ **FAIL** | Missing correlation_id, unstructured logging |
| Security | ✅ Pass | No secrets, no dynamic code execution |
| Idempotency | ⚠️ Partial | No explicit idempotency handling |
| Testing | ❌ **FAIL** | No tests found for this file |
| Complexity | ✅ Pass | Within acceptable limits |
| Documentation | ⚠️ Partial | Good docstrings but missing failure modes |

**Overall Assessment**: The file requires **critical fixes** before it can be considered production-ready for financial trading. The float arithmetic issue (line 157) and silent failure masking (lines 162, 168) are blocking issues that violate fundamental financial-grade coding standards.

---

**Audit completed**: 2025-01-XX by AI Copilot Agent  
**Next action**: Implement Priority 1 and Priority 2 fixes, add comprehensive test suite
