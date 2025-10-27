# [File Review] Financial-grade, line-by-line audit

> Purpose: Conduct a rigorous, line-by-line review of a single Python file in the trading system, to institution-grade standards (correctness, controls, auditability, and safety). One issue per file.

---

## 0) Metadata

**File path**: `the_alchemiser/shared/services/market_data_service.py`

**Commit SHA / Tag**: `802cf268358e3299fb6b80a4b7cf3d4bda2994f4`

**Reviewer(s)**: Copilot Agent

**Date**: 2025-10-07

**Business function / Module**: shared - Services

**Runtime context**: AWS Lambda, Paper/Live Trading, Python 3.12+, Backtesting

**Criticality**: P2 (Medium) - Critical market data service for all trading strategies

**Direct dependencies (imports)**:
```
Internal:
  - the_alchemiser.shared.logging (get_logger)
  - the_alchemiser.shared.types.market_data (BarModel, QuoteModel)
  - the_alchemiser.shared.types.market_data_port (MarketDataPort)
  - the_alchemiser.shared.utils.alpaca_error_handler (AlpacaErrorHandler, HTTPError, RequestException, RetryException)
  - the_alchemiser.shared.value_objects.symbol (Symbol)
  - the_alchemiser.shared.brokers.alpaca_manager (AlpacaManager) [TYPE_CHECKING only]
  - the_alchemiser.shared.errors.exceptions (DataProviderError) [lazy import]
  - the_alchemiser.shared.utils.price_discovery_utils (get_current_price_from_quote) [lazy import]
  - the_alchemiser.shared.protocols.market_data (BarsIterable) [lazy import]

External:
  - alpaca.data.requests (StockLatestQuoteRequest, StockBarsRequest)
  - alpaca.data.timeframe (TimeFrame, TimeFrameUnit)
  - stdlib: time, datetime, decimal, secrets, typing
```

**External services touched**:
```
- Alpaca Market Data API (via AlpacaManager)
  * get_stock_latest_quote
  * get_stock_bars
  * get_current_price
```

**Interfaces (DTOs/events) produced/consumed**:
```
Produced:
  - BarModel (shared.types.market_data)
  - QuoteModel (shared.types.market_data)
  - dict[str, Any] (historical bars)
  - dict[str, float] (current prices)

Consumed:
  - Symbol (shared.value_objects.symbol)
  - AlpacaManager interface for market data access
```

**Related docs/specs**:
- [Copilot Instructions](.github/copilot-instructions.md)
- [Alpaca Architecture](docs/ALPACA_ARCHITECTURE.md)
- [Market Data Port Review](docs/file_reviews/FILE_REVIEW_market_data_port.md)
- [Alpaca Error Handler Review](docs/file_reviews/FILE_REVIEW_alpaca_error_handler.md)

**Usage locations**:
- `strategy_v2/adapters/market_data_adapter.py` (uses MarketDataService)
- `orchestration/event_driven_orchestrator.py` (injects MarketDataService)
- `execution_v2/services/execution_manager.py` (uses market data)
- Backtesting implementations

**File metrics**:
- **Lines of code**: 548
- **Functions/Methods**: 15 (1 constructor + 7 public + 7 private)
- **Cyclomatic Complexity**: Not explicitly measured, but appears within bounds
- **Test Coverage**: No dedicated test file found (tests exist for protocol and adapters)

---

## 1) Scope & Objectives

- ✅ Verify the file's **single responsibility** and alignment with intended business capability
- ⚠️ Ensure **correctness**, **numerical integrity**, **deterministic behaviour** where required
- ⚠️ Validate **error handling**, **idempotency**, **observability**, **security**, and **compliance** controls
- ✅ Confirm **interfaces/contracts** (DTOs/events) are accurate, versioned, and tested
- ⚠️ Identify **dead code**, **complexity hotspots**, and **performance risks**

---

## 2) Summary of Findings (use severity labels)

### Critical
**None identified** ✅

### High
1. **Missing correlation_id/causation_id in logging** - All logger calls lack distributed tracing fields required by copilot instructions (Lines 87, 162, 183, 206, 226, 259-262, 266-267, 270, 333-336, 340-342, 477, 485, 512)
2. **Non-deterministic RNG in production code** - Uses `secrets.randbelow()` for jitter in retry logic, violating determinism requirement (Line 331)
3. **No idempotency protection** - `get_historical_bars` performs retries without idempotency keys, could result in duplicate data fetches (Lines 273-346)

### Medium
1. **Float comparison without isclose()** - Lines 131, 140, 149 use `> 0` on float without tolerance check (violates float guardrail)
2. **Inconsistent return type documentation** - `get_mid_price` returns `float | None` but should consider `Decimal` for financial data (Line 165)
3. **Redundant datetime imports** - `datetime` imported at module level (line 12) and again locally in 3 functions (lines 108, 386, 526)
4. **Generic Exception catch** - Lines 86, 161, 182, 205-207, 269, 326, 460, 484 catch broad `Exception` types
5. **No timeout specification** - External API calls lack explicit timeout parameters (Lines 114, 247, 311)
6. **Period parsing lacks validation** - `_period_to_dates` silently defaults to 365 days on invalid input (Line 398)
7. **Incomplete type hint** - `_extract_bars_from_response_core` returns `Any | None` instead of specific type (Line 433)

### Low
1. **F-string logging** - Lines 87, 162, 183, 206, 226, 259-262, 266-267, 270 use f-strings which are evaluated even if log level is filtered
2. **Magic numbers** - Hardcoded values: 3 retries (line 292), 0.6 sleep (line 293), 1.0 + 0.2 jitter (line 331), 1000 divisor (line 331), 5 days threshold (line 509)
3. **Inconsistent error raising** - Some methods return None on error, others raise exceptions (compare lines 159 vs 343)
4. **Missing pre-conditions in docstrings** - Date format requirements not explicitly documented (line 274)
5. **Duplicate timeframe mapping** - Mappings exist in both `_normalize_timeframe` (line 361) and `_resolve_timeframe_core` (line 419)
6. **No rate limit handling** - Service doesn't implement rate limiting despite copilot instruction to "respect rate limits" (all public methods)

### Info/Nits
1. **Import organization** - Local imports scattered through file instead of at module level (lines 89, 108-109, 111, 199-200, 243-244, 288-289, 386, 417, 444, 446, 526)
2. **Missing newline before private methods** - Line 348 starts private methods without clear section separator
3. **Inconsistent quote construction** - Lines 132-157 have complex conditional logic that could be simplified
4. **Docstring inconsistency** - Some methods document exceptions (line 62), others don't (lines 186-207)
5. **No module-level constants** - Magic numbers should be extracted to constants at module level
6. **Timeframe normalization redundant** - Both normalizes and resolves timeframes separately

---

## 3) Line-by-Line Notes

### Detailed Line-by-Line Analysis

| Line(s) | Issue / Observation | Severity | Evidence / Excerpt | Proposed Action |
|---------|---------------------|----------|-------------------|-----------------|
| 1-7 | Module header and docstring | ✅ PASS | Correct format: `"""Business Unit: shared \| Status: current."""` | None |
| 9 | Future annotations import | ✅ PASS | Best practice for Python 3.12+ | None |
| 11-15 | Module-level imports | ⚠️ MEDIUM | Multiple imports including `secrets.randbelow` for non-deterministic jitter | Document jitter behavior, consider making deterministic for tests |
| 14 | secrets import | 🔴 HIGH | `from secrets import randbelow` - used in production retry logic (line 331), not deterministic | Add test mode with seeded RNG or document exemption |
| 17-26 | Internal imports | ✅ PASS | Clean import structure, no `import *` | None |
| 28-29 | TYPE_CHECKING block | ✅ PASS | Proper use for avoiding circular imports | None |
| 32-38 | Class definition and docstring | ✅ PASS | Clear purpose, implements MarketDataPort protocol | None |
| 40-48 | `__init__` method | ✅ PASS | Clean constructor, stores repo and logger | None |
| 47 | Logger initialization | 🔴 HIGH | No correlation_id support in logger | Add support for distributed tracing context |
| 50-91 | `get_bars` method | ⚠️ MEDIUM | 42 lines (within 50 line limit), good docstring | Consider extracting conversion logic |
| 62 | Docstring - Raises | ✅ PASS | Documents exception type | None |
| 65-78 | Bar fetching logic | ✅ PASS | Clean normalization and conversion flow | None |
| 82 | BarModel conversion | ⚠️ MEDIUM | List comprehension could fail partially | Consider error handling per bar |
| 86-91 | Exception handling | ⚠️ MEDIUM | Catches broad `Exception`, logs with f-string | Use structured logging, narrow exception types |
| 87 | F-string in logging | ⚠️ LOW | `f"Failed to get bars..."` - always evaluated | Use lazy logging: `"Failed...", symbol, period, timeframe` |
| 89 | Lazy import | ℹ️ INFO | Local import of DataProviderError | Consider module-level import if frequently used |
| 93-163 | `get_latest_quote` method | 🔴 CRITICAL | 71 lines (exceeds 50 line soft limit), complex logic | Refactor into smaller helper methods |
| 108-109 | Redundant imports | ⚠️ MEDIUM | `datetime` and `Decimal` already imported at module level | Remove or document reason for local import |
| 111 | Lazy import | ℹ️ INFO | `StockLatestQuoteRequest` imported locally | Acceptable to avoid circular deps |
| 114 | API call without timeout | ⚠️ MEDIUM | `get_stock_latest_quote(request)` - no explicit timeout | Add timeout parameter per copilot instructions |
| 118-122 | Float extraction | ⚠️ MEDIUM | Extracts prices as `float` without Decimal conversion initially | Consider using Decimal from start for precision |
| 124-128 | Timestamp normalization | ✅ PASS | Properly handles timezone-aware datetime | None |
| 131, 140, 149 | Float comparison | 🔴 HIGH | `if bid_price > 0` - direct float comparison violates guardrail | Use `math.isclose(bid_price, 0, abs_tol=1e-9)` or `Decimal` |
| 132-157 | Conditional quote construction | ⚠️ LOW | Complex nested conditionals for bid/ask handling | Could extract to helper method or use match/case |
| 134-138 | QuoteModel creation | ✅ PASS | Properly converts to Decimal | None |
| 141-147 | Bid-only fallback | ⚠️ LOW | Uses bid_price for both bid and ask when ask missing | Document this business logic decision |
| 150-156 | Ask-only fallback | ⚠️ LOW | Uses ask_price for both bid and ask when bid missing | Document this business logic decision |
| 159 | Return None on missing data | ✅ PASS | Aligns with protocol contract | None |
| 161-163 | Exception handling | ⚠️ MEDIUM | Catches broad `Exception`, logs warning, returns None | Consider distinguishing transient vs permanent failures |
| 162 | F-string in logging | ⚠️ LOW | `f"Failed to get quote..."` - always evaluated | Use lazy logging parameters |
| 165-184 | `get_mid_price` method | ✅ PASS | Clean delegation to repo, 20 lines | None |
| 165 | Return type | ⚠️ MEDIUM | Returns `float \| None` for financial data | Consider `Decimal` for consistency |
| 180 | Delegation | ✅ PASS | Delegates to AlpacaManager | None |
| 182-184 | Exception handling | ⚠️ MEDIUM | Broad Exception catch, returns None | Match behavior with protocol contract |
| 186-207 | `get_current_price` method | ✅ PASS | 22 lines, delegates to utility function | None |
| 199-201 | Lazy import | ℹ️ INFO | Imports price discovery utility locally | Consider module-level import |
| 204 | Delegation to utility | ✅ PASS | Uses centralized price discovery | Good separation of concerns |
| 205-207 | Exception handling | ⚠️ MEDIUM | Catches Exception and re-raises | Why catch and re-raise without transformation? |
| 206 | Logging and raising | ⚠️ LOW | Logs error then raises - could be redundant | Let caller handle logging or transform exception |
| 209-230 | `get_current_prices` method | ✅ PASS | 22 lines, batch operation | None |
| 220-226 | Loop over symbols | ⚠️ MEDIUM | Sequential calls, could be slow for many symbols | Consider batch API if available |
| 226 | Warning logging | ⚠️ LOW | Logs warning for each missing price | Could accumulate and log once |
| 228-230 | Exception handling | ⚠️ MEDIUM | Catches Exception and re-raises | Same issue as line 205-207 |
| 232-271 | `get_quote` method | ✅ PASS | 40 lines (within limit) | None |
| 244 | Lazy import | ℹ️ INFO | Local StockLatestQuoteRequest import | Acceptable pattern |
| 247 | API call without timeout | ⚠️ MEDIUM | No explicit timeout parameter | Add timeout per copilot instructions |
| 252 | model_dump() usage | ✅ PASS | Proper Pydantic v2 method | None |
| 257-268 | Specific exception handling | ✅ PASS | Catches narrow exception types (RetryException, HTTPError, RequestException) | Good pattern |
| 259-267 | Error message construction | ✅ PASS | Clear error messages with context | None |
| 260 | Rate limit detection | ⚠️ LOW | String-based detection of rate limits | Consider using exception attributes if available |
| 269-271 | Fallback Exception handler | ⚠️ MEDIUM | Returns None on generic Exception | Inconsistent with specific exception handling above |
| 270 | Logging | ⚠️ LOW | F-string logging | Use lazy logging |
| 273-346 | `get_historical_bars` method | 🔴 CRITICAL | 74 lines (exceeds 50 line soft limit), retry logic | Refactor into smaller methods |
| 288-289 | Lazy import | ℹ️ INFO | Local StockBarsRequest import | Acceptable |
| 292-293 | Retry configuration | ⚠️ LOW | Magic numbers: 3 retries, 0.6 base sleep | Extract to class constants or config |
| 295-337 | Retry loop | 🔴 HIGH | Complex retry logic without idempotency keys | Add correlation_id, implement idempotency |
| 298 | Timeframe resolution | ✅ PASS | Delegates to helper method | None |
| 300-301 | Date parsing | ⚠️ MEDIUM | fromisoformat assumes valid format | Validate input or document precondition |
| 303-308 | Request construction | ✅ PASS | Clean Alpaca SDK usage | None |
| 311 | API call without timeout | ⚠️ MEDIUM | No explicit timeout | Add timeout parameter |
| 314-321 | Empty data handling | ⚠️ MEDIUM | Treats missing data as transient error | Could lead to unnecessary retries |
| 326-343 | Exception handling in retry | ⚠️ MEDIUM | Catches all exception types broadly | Good use of AlpacaErrorHandler for classification |
| 327 | Transient error detection | ✅ PASS | Uses AlpacaErrorHandler.is_transient_error | Good integration |
| 331 | Jitter calculation | 🔴 HIGH | `randbelow(1000) / 1000.0` - non-deterministic | Make deterministic for tests |
| 331 | Magic numbers in jitter | ⚠️ LOW | Hardcoded 1.0, 0.2, 1000 | Extract to constants with names |
| 333-336 | Retry logging | 🔴 HIGH | No correlation_id in log message | Add tracing context |
| 336 | Sleep in retry | ✅ PASS | Exponential backoff with jitter | Good pattern |
| 340-343 | Error sanitization | ✅ PASS | Uses AlpacaErrorHandler for safe error messages | Security-conscious |
| 346 | Defensive fallback | ✅ PASS | Returns empty list if loop exhausted | Static analysis helper |
| 348-374 | `_normalize_timeframe` method | ⚠️ LOW | 27 lines for mapping | Could use constant dict at module level |
| 361-367 | Timeframe mapping | ⚠️ LOW | Duplicates mapping in _resolve_timeframe_core | Consolidate mappings |
| 369-374 | Fallback behavior | ⚠️ MEDIUM | Returns input as-is if not found | Could raise ValueError for invalid input |
| 376-402 | `_period_to_dates` method | ⚠️ MEDIUM | 27 lines, simple period parsing | Document supported formats |
| 386 | Redundant import | ⚠️ MEDIUM | `from datetime import datetime` already imported | Remove duplicate |
| 388 | UTC datetime | ✅ PASS | Uses datetime.now(UTC) | Correct pattern |
| 391-397 | Period parsing | ⚠️ MEDIUM | Simple string replacement | Fragile, consider regex or dedicated parser |
| 398 | Silent default | ⚠️ MEDIUM | Defaults to 365 days on invalid input | Should raise ValueError instead |
| 404-431 | `_resolve_timeframe_core` method | ⚠️ LOW | 28 lines for timeframe resolution | Duplicates _normalize_timeframe mapping |
| 404 | Return type annotation | ⚠️ MEDIUM | Returns `Any` with noqa comment | Should be `TimeFrame` type |
| 417 | Lazy import | ℹ️ INFO | Imports TimeFrame locally | Acceptable |
| 419-425 | Timeframe mapping | ⚠️ LOW | Duplicates mapping from _normalize_timeframe | Consolidate into single source of truth |
| 428-430 | ValueError on invalid | ✅ PASS | Raises exception for unsupported timeframe | Good validation |
| 433-463 | `_extract_bars_from_response_core` method | ⚠️ MEDIUM | 31 lines, tries multiple access patterns | Document expected response shape |
| 433 | Return type | ⚠️ MEDIUM | Returns `Any \| None` instead of BarsIterable | Use proper type hint |
| 444-446 | Lazy imports | ℹ️ INFO | Local imports for typing | Acceptable pattern |
| 448-461 | Multiple access attempts | ✅ PASS | Defensive response parsing | Handles SDK version differences |
| 460-461 | Broad Exception catch | ⚠️ MEDIUM | Catches Exception and returns None | May hide real errors |
| 465-487 | `_convert_bars_to_dicts_core` method | ✅ PASS | 23 lines, clean conversion | None |
| 476 | List conversion | ✅ PASS | Converts iterable to list | None |
| 477 | Debug logging | ✅ PASS | Logs success count | Good observability |
| 482 | model_dump() usage | ✅ PASS | Proper Pydantic v2 serialization | None |
| 484-486 | Exception handling | ⚠️ LOW | Catches Exception, logs warning, continues | Acceptable for resilience |
| 485 | Pragma comment | ✅ PASS | `# pragma: no cover` for exceptional case | Appropriate |
| 489-513 | `_should_raise_missing_data_error_core` method | ✅ PASS | 25 lines, clear heuristic | None |
| 504-505 | Date parsing | ✅ PASS | Uses fromisoformat | None |
| 506 | Day calculation | ✅ PASS | Clear timedelta usage | None |
| 509 | Magic number | ⚠️ LOW | Hardcoded 5 days threshold | Extract to constant |
| 509 | Timeframe comparison | ⚠️ MEDIUM | Uses lowercase comparison | Inconsistent with normalization |
| 512 | Warning logging | ⚠️ LOW | F-string logging | Use lazy logging |
| 515-548 | `_convert_to_bar_model` method | ✅ PASS | 34 lines (within limit) | None |
| 526 | Redundant import | ⚠️ MEDIUM | `from datetime import datetime` already imported | Remove duplicate |
| 528-545 | Dictionary access | ✅ PASS | Uses .get() with defaults | Defensive coding |
| 530-535 | Fallback values | ⚠️ MEDIUM | Uses datetime.now(UTC) and 0 as defaults | May hide data quality issues |
| 537-545 | BarModel construction | ✅ PASS | Proper Decimal conversion for prices | Follows financial guardrails |
| 547-548 | ValueError on unexpected type | ✅ PASS | Raises exception for non-dict | Good validation |

---

## 4) Correctness & Contracts

### Correctness Checklist

- [x] The file has a **clear purpose** and does not mix unrelated concerns (SRP)
  - ✅ Single responsibility: Market data service providing domain interface
  - ✅ Clean separation: orchestrators → service → AlpacaManager → API

- [ ] Public functions/classes have **docstrings** with inputs/outputs, pre/post-conditions, and failure modes
  - ✅ Most methods have docstrings with Args and Returns
  - ⚠️ Missing pre-conditions: date format requirements not documented (line 274)
  - ⚠️ Inconsistent Raises documentation: some methods document, others don't

- [x] **Type hints** are complete and precise (no `Any` in domain logic; use `Literal/NewType` where helpful)
  - ⚠️ Two occurrences of `Any` with noqa (lines 404, 433, 465, 515)
  - ✅ Most type hints are precise and complete
  - ⚠️ Could use Literal for timeframe/period format strings

- [x] **DTOs** are **frozen/immutable** and validated (e.g., Pydantic v2 models with constrained types)
  - ✅ BarModel and QuoteModel are Pydantic models (defined elsewhere)
  - ✅ Uses model_dump() for Pydantic v2 serialization

- [ ] **Numerical correctness**: currency uses `Decimal`; floats use `math.isclose` or explicit tolerances; no `==`/`!=` on floats
  - ✅ Decimal used for bar prices (lines 540-543)
  - ✅ Decimal used for quote prices (lines 134-137)
  - 🔴 **VIOLATION**: Float comparisons at lines 131, 140, 149 use `> 0` without tolerance
  - ⚠️ get_mid_price returns float instead of Decimal (line 165)

- [ ] **Error handling**: exceptions are narrow, typed (from `shared.errors`), logged with context, and never silently caught
  - ⚠️ Multiple broad `Exception` catches (lines 86, 161, 182, 269, 326, 460, 484)
  - ✅ Some narrow exception handling (lines 257-268)
  - ✅ Uses AlpacaErrorHandler for error classification
  - ⚠️ Inconsistent error behavior: some return None, others raise

- [ ] **Idempotency**: handlers tolerate replays; side-effects are guarded by idempotency keys or checks
  - 🔴 **VIOLATION**: No idempotency keys in retry logic (lines 295-337)
  - ⚠️ Multiple retries could result in duplicate API calls without protection
  - ℹ️ Read-only operations are naturally idempotent at data level

- [ ] **Determinism**: tests freeze time (`freezegun`), seed RNG; no hidden randomness in business logic
  - 🔴 **VIOLATION**: Uses `secrets.randbelow()` for jitter without test mode (line 331)
  - ✅ No other sources of randomness identified
  - ⚠️ Needs deterministic test mode with seeded RNG

- [x] **Security**: no secrets in code/logs; input validation at boundaries; no `eval`/`exec`/dynamic imports
  - ✅ No hardcoded secrets
  - ✅ Uses AlpacaErrorHandler.sanitize_error_message to remove sensitive data
  - ✅ No eval/exec usage
  - ⚠️ Input validation could be stronger (period format, date format)

- [ ] **Observability**: structured logging with `correlation_id`/`causation_id`; one log per state change; no spam in hot loops
  - 🔴 **VIOLATION**: No correlation_id/causation_id in any log statements
  - ⚠️ Uses f-strings in logging (always evaluated)
  - ✅ Appropriate log levels (error, warning, debug)
  - ⚠️ Multiple logs in retry loop could be noisy

- [ ] **Testing**: public APIs have tests; property-based tests for maths; coverage ≥ 80% (≥ 90% for strategy/portfolio)
  - ⚠️ No dedicated test file for MarketDataService found
  - ✅ Protocol tests exist (test_market_data_port.py)
  - ⚠️ Adapter tests exist but may not cover service fully
  - ❌ No property-based tests for period parsing or timeframe normalization

- [ ] **Performance**: no hidden I/O in hot paths; vectorised Pandas ops; HTTP clients pooled with rate limits
  - ⚠️ Sequential symbol fetching in get_current_prices (line 220-226)
  - 🔴 No rate limiting implementation
  - ⚠️ No explicit timeouts on API calls (lines 114, 247, 311)
  - ✅ Retry logic with exponential backoff prevents overwhelming API

- [x] **Complexity**: cyclomatic ≤ 10, cognitive ≤ 15, functions ≤ 50 lines, params ≤ 5
  - ⚠️ get_latest_quote: 71 lines (exceeds 50 line soft limit)
  - ⚠️ get_historical_bars: 74 lines (exceeds 50 line soft limit)
  - ✅ All methods have ≤ 4 parameters
  - ℹ️ Cyclomatic complexity not measured but appears reasonable

- [x] **Module size**: ≤ 500 lines (soft), split if > 800
  - ✅ 548 lines (within soft limit, below split threshold)

- [x] **Imports**: no `import *`; stdlib → third-party → local; no deep relative imports
  - ✅ No `import *` usage
  - ✅ Import order follows convention
  - ⚠️ Many local imports scattered through file (lazy imports)

---

## 5) Additional Notes

### Strengths
1. **Clean Protocol Implementation**: Properly implements MarketDataPort protocol with all required methods
2. **Good Error Integration**: Excellent use of AlpacaErrorHandler for error classification and sanitization
3. **Security Conscious**: Properly sanitizes error messages to prevent leaking sensitive data
4. **Retry Logic**: Implements exponential backoff with jitter for transient failures
5. **Type Safety**: Uses Pydantic models for data validation and serialization
6. **Defensive Coding**: Handles multiple response shapes from Alpaca SDK gracefully

### Critical Improvements Needed
1. **Add Distributed Tracing**: All log statements must include `correlation_id` and `causation_id` per copilot instructions
2. **Fix Float Comparisons**: Replace `> 0` comparisons with `math.isclose()` or use Decimal consistently (lines 131, 140, 149)
3. **Make Jitter Deterministic**: Add test mode with seeded RNG for reproducible tests (line 331)
4. **Add Idempotency Keys**: Implement idempotency protection for retry logic (lines 295-337)
5. **Refactor Long Methods**: Split get_latest_quote (71 lines) and get_historical_bars (74 lines) into smaller functions

### Recommended Improvements
1. **Add Explicit Timeouts**: All external API calls should have bounded timeouts
2. **Implement Rate Limiting**: Add rate limit handling per copilot instructions
3. **Create Test File**: Add `tests/shared/services/test_market_data_service.py` with comprehensive coverage
4. **Extract Constants**: Move magic numbers to module-level constants (retry counts, sleep durations, thresholds)
5. **Consolidate Timeframe Logic**: Merge `_normalize_timeframe` and `_resolve_timeframe_core` into single function
6. **Remove Duplicate Imports**: Clean up redundant datetime imports (lines 108, 386, 526)
7. **Add Input Validation**: Validate period format and date strings more strictly
8. **Use Lazy Logging**: Replace f-strings with lazy parameter logging
9. **Document Business Logic**: Add docstrings explaining bid/ask fallback behavior (lines 141-156)
10. **Consider Decimal Return Types**: Use Decimal for get_mid_price for consistency

### Architecture Notes
- Service properly acts as anti-corruption layer between domain and Alpaca SDK
- Good separation of concerns: normalization, error handling, conversion
- Lazy imports prevent circular dependencies effectively
- Protocol-based design enables testing with mocks and backtesting implementations

### Performance Considerations
- Sequential price fetching could be slow for large symbol lists (consider batch API)
- No caching mechanism (acceptable for real-time data, but consider for static metadata)
- Retry logic could add significant latency on failures (acceptable trade-off for reliability)

### Security Considerations
- Properly sanitizes error messages via AlpacaErrorHandler
- No secrets in code or logs
- Input validation could be strengthened

### Testing Gaps
- No dedicated unit tests for MarketDataService class
- No property-based tests for period parsing edge cases
- No tests for retry logic behavior
- No tests for deterministic jitter in controlled environment

---

## Action Items by Priority

### Priority 1 (Critical - Must Fix)
1. Add correlation_id and causation_id to all log statements (Lines 87, 162, 183, 206, 226, 259-262, 266-267, 270, 333-336, 340-342, 477, 485, 512)
2. Fix float comparisons to use math.isclose() or Decimal consistently (Lines 131, 140, 149)
3. Make jitter calculation deterministic for tests (Line 331)
4. Refactor get_latest_quote to be ≤ 50 lines (Lines 93-163)
5. Refactor get_historical_bars to be ≤ 50 lines (Lines 273-346)

### Priority 2 (High - Should Fix)
6. Add idempotency keys or request tracking for retry logic (Lines 295-337)
7. Add explicit timeouts to all API calls (Lines 114, 247, 311)
8. Create comprehensive test file: tests/shared/services/test_market_data_service.py
9. Remove duplicate datetime imports (Lines 108, 386, 526)
10. Extract magic numbers to module-level constants

### Priority 3 (Medium - Nice to Have)
11. Consolidate timeframe mapping into single source of truth
12. Add stricter input validation for period and date formats
13. Implement rate limiting per copilot instructions
14. Use lazy logging parameters instead of f-strings
15. Consider Decimal return type for get_mid_price
16. Add property-based tests for period parsing and timeframe normalization

### Priority 4 (Low - Polish)
17. Add clear section separator before private methods (Line 348)
18. Improve docstring consistency (document Raises clause in all public methods)
19. Document business logic decisions (bid/ask fallback behavior)
20. Consider batch API for get_current_prices if available

---

**Review completed**: 2025-10-07  
**Reviewer**: Copilot Agent  
**Status**: COMPLETE - Ready for remediation
