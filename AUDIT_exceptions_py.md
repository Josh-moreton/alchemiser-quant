# [File Review] Financial-grade, line-by-line audit

> Purpose: Conduct a rigorous, line-by-line review of a single Python file in the trading system, to institution-grade standards (correctness, controls, auditability, and safety). One issue per file.

---

## 0) Metadata

**File path**: `the_alchemiser/shared/types/exceptions.py`

**Commit SHA / Tag**: `0d9f659` (current HEAD)

**Reviewer(s)**: GitHub Copilot

**Date**: 2025-10-06

**Business function / Module**: shared/types (exception hierarchy)

**Runtime context**: Used across all modules (strategy, portfolio, execution, orchestration, adapters)

**Criticality**: P1 (High) - Foundation exception classes used throughout the system

**Direct dependencies (imports)**:
```
Internal: None (base module)
External: datetime (stdlib), typing (stdlib)
```

**Dependents (files importing from this module)**:
```
- the_alchemiser/main.py
- the_alchemiser/execution_v2/core/smart_execution_strategy/repeg.py
- the_alchemiser/strategy_v2/engines/dsl/types.py
- the_alchemiser/strategy_v2/engines/dsl/events.py
- the_alchemiser/strategy_v2/handlers/signal_generation_handler.py
- the_alchemiser/strategy_v2/core/factory.py
- the_alchemiser/strategy_v2/adapters/market_data_adapter.py
- the_alchemiser/shared/brokers/alpaca_manager.py
- the_alchemiser/shared/types/trading_errors.py
- the_alchemiser/shared/utils/decorators.py
- the_alchemiser/shared/utils/__init__.py
- the_alchemiser/shared/utils/portfolio_calculations.py
- the_alchemiser/shared/utils/error_reporter.py
- the_alchemiser/shared/services/market_data_service.py
- the_alchemiser/shared/errors/error_handler.py
- the_alchemiser/shared/errors/error_utils.py
- the_alchemiser/shared/errors/catalog.py
- the_alchemiser/shared/errors/__init__.py
- the_alchemiser/shared/errors/error_details.py
- the_alchemiser/shared/errors/enhanced_exceptions.py
- the_alchemiser/orchestration/system.py
- the_alchemiser/portfolio_v2/core/planner.py
- the_alchemiser/portfolio_v2/core/state_reader.py
```

**External services touched**: N/A (pure Python exception definitions)

**Interfaces (DTOs/events) produced/consumed**: N/A (exception classes only)

**Related docs/specs**:
- `.github/copilot-instructions.md` - Error handling guidelines
- `the_alchemiser/shared/errors/` - Enhanced exception framework
- `tests/shared/types/test_trading_errors.py` - Test patterns

---

## 1) Scope & Objectives

- Verify the file's **single responsibility** (exception hierarchy definition) and alignment with intended business capability.
- Ensure **correctness**, **type safety**, **consistent initialization patterns**.
- Validate **error handling best practices**, **observability support**, **security**, and **compliance** controls.
- Confirm exception hierarchy is logical and properly inherits from base classes.
- Identify **inconsistencies**, **missing context tracking**, **security risks** (PII/secrets leakage).
- Check for **complete docstrings**, **type hints**, and **parameter validation**.

---

## 2) Summary of Findings (use severity labels)

### Critical
None identified.

### High
1. **Missing context propagation in multiple exception classes** - Several exception subclasses (lines 56-62, 145-162, 186-201, 242-252, 254-264, 281-283, 304-323, 349-351) don't call `super().__init__` with context dict, breaking observability chain.
2. **Float usage for money amounts** - Lines 74-75, 86-90, 99-101, 113-114, 122-123, 152-154, 159-161, 172-174, 177-179, 193-194 use `float` for financial quantities (quantity, price, amounts), violating "never use float for money" rule.
3. **Inconsistent context initialization** - Some classes build context dict and pass to super (ConfigurationError, OrderExecutionError, PortfolioError, StrategyExecutionError), others don't (DataProviderError, TradingClientError, most others).

### Medium
4. **Missing module header compliance** - Line 2: Business Unit is "utilities" but should be "shared" based on module location.
5. **Missing correlation_id/causation_id support** - Only PortfolioError (line 211) accepts correlation_id; other exceptions lack idempotency/traceability support.
6. **Incomplete docstrings** - Most exception classes have one-line docstrings without details on: when raised, what context is captured, recovery strategies.
7. **No retry metadata** - Exceptions don't track retry_count, max_retries, or retry_after (except RateLimitError has retry_after).
8. **Type hints allow None for floats** - Lines 73-76, 113-115, 136-137, 152-155, 172-174, 193-195: `float | None` parameters should use Decimal for money.

### Low
9. **Context attribute redundancy** - Many classes store context values both as instance attributes AND in context dict (e.g., lines 52-53, 96-102).
10. **Missing type narrowing** - Line 273: `value: str | int | float | None` is too broad; should use proper types or Any.
11. **Empty exception classes** - Lines 56-62, 281-283, 304-315, 349-351: Several exceptions are empty shells with no added value.
12. **Inconsistent parameter naming** - `config_value` (line 43), `data_type` (line 258), `field_name` (line 272), `logger_name` (line 319) - inconsistent naming patterns.

### Info/Nits
13. **Missing __all__ export** - No explicit export list for public API.
14. **No error severity enum** - Unlike enhanced_exceptions.py which has ErrorSeverity, base exceptions lack severity classification.
15. **Timestamp uses datetime.now(UTC)** - Line 24: Should use frozen/immutable approach or property to prevent mutation.
16. **to_dict() doesn't include subclass attributes** - Line 26-33: Base class to_dict() doesn't call subclass attributes.

---

## 3) Line-by-Line Notes

### Detailed Line-by-Line Analysis

| Line(s) | Issue / Observation | Severity | Evidence / Excerpt | Proposed Action |
|---------|---------------------|----------|-------------------|-----------------|
| 1-8 | Module header and docstring | Info | Business Unit: utilities; should be "shared" | Update to "Business Unit: shared" |
| 10-13 | Imports complete and correct | ✓ | Standard library only, properly ordered | No action |
| 16-33 | AlchemiserError base class | Medium | Missing correlation_id, causation_id support; timestamp mutable | Add traceability fields; make timestamp immutable |
| 24 | Mutable timestamp | Low | `self.timestamp = datetime.now(UTC)` called at init | Consider making this a @property or freeze it |
| 26-33 | to_dict() incomplete | Low | Doesn't serialize subclass-specific attributes | Document limitation or make extensible |
| 36-53 | ConfigurationError class | Medium | Uses str() conversion for safety (good) but missing correlation_id | Add correlation_id parameter |
| 43 | Float in type hint | Medium | `config_value: str \| int \| float \| bool \| None` allows float | Consider Decimal or document non-monetary use |
| 50 | String conversion | ✓ | Good: `str(config_value)` prevents serialization issues | No action |
| 56-62 | DataProviderError, TradingClientError | High | Empty classes, no context propagation | Add proper __init__ with context support |
| 64-103 | OrderExecutionError | High | Uses float for quantity, price (lines 74-75, 86-90, 99-101) | Change to Decimal type |
| 73-76 | Financial float parameters | High | `quantity: float \| None`, `price: float \| None` | Must use Decimal per guidelines |
| 77 | retry_count parameter | ✓ | Good: includes retry tracking | No action |
| 86-90 | Float in context | High | Financial amounts stored as float in context | Must use Decimal |
| 92-93 | Missing retry_count in context | Medium | retry_count not added to context when > 0 | Add to context for observability |
| 105-126 | OrderPlacementError | High | Inherits float issues from parent | Change to Decimal |
| 113-115 | Float parameters | High | `quantity: float \| None`, `price: float \| None` | Change to Decimal |
| 125 | New reason attribute | Low | Not passed to parent or added to context | Add to context dict |
| 128-143 | OrderTimeoutError | Medium | Missing context propagation for timeout_seconds, attempt_number | Add to context dict |
| 136-137 | timeout_seconds as float | Low | Could be int, but float acceptable for duration | Document or use timedelta |
| 141-142 | Attributes not in context | Medium | timeout_seconds, attempt_number not added to context | Add to context for observability |
| 145-162 | SpreadAnalysisError | High | Float for bid/ask/spread_cents (lines 152-154, 159-161) | Change to Decimal |
| 152-154 | Financial float parameters | High | `bid: float \| None`, `ask: float \| None`, `spread_cents: float \| None` | Must use Decimal |
| 157 | Missing context initialization | High | No context dict built; parent called with message only | Build context dict with spread data |
| 164-180 | BuyingPowerError | High | Float for financial amounts (lines 172-174, 177-179) | Change to Decimal |
| 172-174 | Financial float parameters | High | `required_amount`, `available_amount`, `shortfall` all float | Must use Decimal |
| 176 | Missing context initialization | High | No context dict built with financial amounts | Build context dict |
| 182-185 | InsufficientFundsError | Low | Empty class, no added value | Consider removing or adding context |
| 186-201 | PositionValidationError | High | Float for qty (lines 193-194); no context dict | Change to Decimal, add context |
| 193-194 | Float for quantities | High | `requested_qty: float \| None`, `available_qty: float \| None` | Change to Decimal |
| 197-200 | Attributes not in context | High | Symbol and quantities not added to context | Build context dict |
| 203-226 | PortfolioError | ✓ | Good: proper context dict, correlation_id support | Model for other exceptions |
| 228-240 | NegativeCashBalanceError | Medium | cash_balance as string (line 234) is odd; no propagation to context | Use Decimal, add to context |
| 234 | String for cash_balance | Medium | `cash_balance: str \| None` should be Decimal | Change to Decimal |
| 238-239 | Missing cash_balance in parent | Medium | cash_balance not passed to parent context | Add to context via parent call |
| 242-252 | IndicatorCalculationError | High | No context dict built; attributes not propagated | Build context dict |
| 249-251 | Attributes not in context | High | indicator_name, symbol only stored as attributes | Add to context dict |
| 254-264 | MarketDataError | High | No context dict built; attributes not propagated | Build context dict |
| 261-263 | Attributes not in context | High | symbol, data_type only stored as attributes | Add to context dict |
| 266-279 | ValidationError | High | No context dict built; float in type hint (line 273) | Build context dict, fix types |
| 273 | Broad type hint | Medium | `value: str \| int \| float \| None` too broad | Use Any or proper type |
| 276-278 | Attributes not in context | High | field_name, value only stored as attributes | Add to context dict |
| 281-283 | NotificationError | Low | Empty class, no added value | Add context support or document |
| 285-293 | S3OperationError | High | No context dict built | Build context dict |
| 290-292 | Attributes not in context | High | bucket, key only stored as attributes | Add to context dict |
| 295-302 | RateLimitError | High | No context dict built | Build context dict |
| 298 | retry_after parameter | ✓ | Good: includes retry timing info | No action |
| 300-301 | retry_after not in context | Medium | Should be in context for observability | Add to context dict |
| 304-310 | MarketClosedError, WebSocketError, StreamingError | Low | Empty classes | Add context or document |
| 316-323 | LoggingError | High | No context dict built | Build context dict |
| 321-322 | logger_name not in context | High | Should be in context for observability | Add to context dict |
| 325-335 | FileOperationError | High | No context dict built | Build context dict |
| 332-334 | Attributes not in context | High | file_path, operation only stored as attributes | Add to context dict |
| 337-347 | DatabaseError | High | No context dict built | Build context dict |
| 344-346 | Attributes not in context | High | table_name, operation only stored as attributes | Add to context dict |
| 349-351 | SecurityError | Low | Empty class | Add context or document |
| 353-360 | EnvironmentError | High | Inherits from ConfigurationError but doesn't use parent properly | Build context dict, use parent's config_key |
| 356-359 | Missing parent context | High | Doesn't leverage parent's config_key/config_value | Pass env_var as config_key to parent |
| 362-385 | StrategyExecutionError | ✓ | Good: proper context dict building | Model for other exceptions |
| 387-389 | StrategyValidationError | Low | Empty class | Add context or document |

---

## 4) Correctness & Contracts

### Correctness Checklist

- [x] The file has a **clear purpose** (exception hierarchy) and does not mix unrelated concerns (SRP) ✓
- [x] Public functions/classes have **docstrings** - ⚠️ Most have basic docstrings but lack detail (when raised, context captured, recovery)
- [x] **Type hints** are complete - ⚠️ Present but incorrect (float for money)
- [ ] **DTOs** N/A - these are exceptions, not DTOs
- [ ] **Numerical correctness**: ❌ FAILS - Uses float for currency/quantities instead of Decimal
- [x] **Error handling**: ✓ These ARE the error classes
- [ ] **Idempotency**: ⚠️ Only PortfolioError supports correlation_id for idempotency tracking
- [ ] **Determinism**: ✓ Exceptions are deterministic (timestamp is only non-deterministic element)
- [x] **Security**: ✓ No eval/exec; ⚠️ Some exceptions store account_id (line 75, 91) - should be redacted in logs
- [x] **Observability**: ⚠️ Inconsistent - some build context dicts, many don't
- [ ] **Testing**: ⚠️ Only test_trading_errors.py exists; no comprehensive test coverage for all exception classes
- [ ] **Performance**: ✓ Exception creation is not performance-critical
- [x] **Complexity**: ✓ All methods are simple (< 10 lines, no branches)
- [x] **Module size**: ✓ 388 lines is under 500 line soft limit
- [x] **Imports**: ✓ Minimal, stdlib only, properly ordered

### Key Issues Summary:

1. **CRITICAL: Float usage for money** - Violates core guardrail "Never use float for money"
2. **HIGH: Inconsistent context propagation** - Many exceptions don't build context dicts
3. **MEDIUM: Missing traceability** - Most exceptions lack correlation_id/causation_id support
4. **MEDIUM: Incomplete docstrings** - Need more detail for institutional use

---

## 5) Recommendations & Action Items

### Must Fix (High Priority)

1. **Replace all float types for financial amounts with Decimal**
   - Lines 74-75, 86-90, 99-101, 113-114, 122-123, 152-154, 159-161, 172-174, 177-179, 193-194
   - Change parameter types: `quantity: Decimal | None`, `price: Decimal | None`, etc.
   - Update context dict values to use Decimal

2. **Add context dict initialization to all exception classes**
   - DataProviderError (lines 56-58)
   - TradingClientError (lines 60-62)
   - SpreadAnalysisError (lines 145-162)
   - BuyingPowerError (lines 164-180)
   - PositionValidationError (lines 186-201)
   - IndicatorCalculationError (lines 242-252)
   - MarketDataError (lines 254-264)
   - ValidationError (lines 266-279)
   - S3OperationError (lines 285-293)
   - RateLimitError (lines 295-302)
   - LoggingError (lines 316-323)
   - FileOperationError (lines 325-335)
   - DatabaseError (lines 337-347)

3. **Add correlation_id parameter to base AlchemiserError**
   - Line 19: Add `correlation_id: str | None = None` parameter
   - Line 23: Store in context dict
   - Propagate to all subclasses

### Should Fix (Medium Priority)

4. **Update module header** - Line 2: Change "utilities" to "shared"

5. **Enhance docstrings** - Add details about when each exception is raised, what context is captured, and recovery strategies

6. **Add security considerations** - Document that account_id and other PII should be redacted in logs

7. **Fix NegativeCashBalanceError** - Line 234: Change cash_balance from str to Decimal

8. **Fix EnvironmentError** - Lines 356-359: Properly use parent ConfigurationError's parameters

### Could Fix (Low Priority)

9. **Add __all__ export list** - Explicit public API

10. **Add severity classification** - Consider adding severity field like enhanced_exceptions.py

11. **Document empty exception classes** - Clarify why some exceptions have no custom initialization

12. **Consider consolidating duplicate attributes** - Storing values both as attributes AND in context is redundant

---

## 6) Test Coverage Requirements

Need to create comprehensive test file: `tests/shared/types/test_exceptions.py`

### Test Cases Required:

1. **AlchemiserError base class**
   - Basic initialization
   - Context dict handling
   - Timestamp creation
   - to_dict() serialization
   - With/without correlation_id

2. **Each exception subclass**
   - Basic initialization
   - Parameter validation
   - Context dict properly populated
   - Inheritance chain correct
   - Can be raised and caught

3. **Financial exceptions with Decimal**
   - OrderExecutionError with Decimal quantities/prices
   - SpreadAnalysisError with Decimal spread values
   - BuyingPowerError with Decimal amounts
   - PositionValidationError with Decimal quantities

4. **Edge cases**
   - None values for optional parameters
   - Empty strings
   - Zero values for financial amounts
   - Unicode in messages

5. **Security tests**
   - Sensitive data (account_id) present in context but documented for redaction
   - No secrets inadvertently leaked

---

## 7) Additional Notes

### Architecture Observations

- This module serves as the **foundation exception hierarchy** for the entire system
- **24+ modules depend on this file** - any breaking changes require careful coordination
- There's parallel development: `shared/errors/enhanced_exceptions.py` provides richer functionality (retry metadata, severity) - consider deprecating or merging these
- **Design inconsistency**: Some exceptions (PortfolioError, StrategyExecutionError, OrderExecutionError, ConfigurationError) follow good patterns with context dict building; others don't

### Migration Path

To fix the float→Decimal issues without breaking existing code:

1. Add Decimal support alongside float (use Union[float, Decimal])
2. Add deprecation warnings for float usage
3. Update all callers to use Decimal
4. Remove float support in major version bump

### Integration with Enhanced Exceptions

The codebase has two exception frameworks:
- `shared/types/exceptions.py` (this file) - legacy, widely used
- `shared/errors/enhanced_exceptions.py` - newer, richer features (retry, severity, correlation_id)

Consider:
- Extending AlchemiserError to support features from EnhancedAlchemiserError
- Or, deprecating this file in favor of enhanced_exceptions.py
- Document the relationship and migration path

---

**Audit completed**: 2025-10-06  
**Auditor**: GitHub Copilot  
**Total lines reviewed**: 388  
**Critical issues**: 0  
**High severity issues**: 3  
**Medium severity issues**: 5  
**Low severity issues**: 4  
**Info/nits**: 4  
**Status**: File requires updates for compliance with institutional standards
