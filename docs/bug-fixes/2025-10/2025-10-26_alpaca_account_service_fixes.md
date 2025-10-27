# Fixes Applied to alpaca_account_service.py

## Summary

Conducted a comprehensive financial-grade review of `the_alchemiser/shared/services/alpaca_account_service.py` and implemented critical fixes to bring the file into compliance with institutional trading standards.

## Critical Issues Fixed

### 1. Money Handling (HIGH PRIORITY - CRITICAL)
**Problem**: Financial values (buying_power, cash, equity, portfolio_value) were returned as `float` instead of `Decimal`, violating money handling guardrails and risking precision loss.

**Fix**:
- Changed return types from `float | None` to `Decimal | None` for:
  - `get_buying_power()` 
  - `get_portfolio_value()`
- Changed `get_positions_dict()` return type from `dict[str, float]` to `dict[str, Decimal]`
- Updated `get_account_dict()` to return financial values as strings (preserving precision)
- Updated helper method `_extract_position_entry()` to return `Decimal` quantities
- Added `from decimal import Decimal` import

**Impact**: 
- Ensures no precision loss in financial calculations
- Complies with copilot instructions mandate: "Money: `Decimal` with explicit contexts; never mix with float"

### 2. Error Handling (HIGH PRIORITY - CRITICAL)
**Problem**: Multiple issues with error handling:
- Broad `Exception` catches that silently swallow errors
- Inconsistent patterns (some methods raise, others return None)
- No retry logic for transient Alpaca API failures
- String matching on error messages (fragile)

**Fix**:
- Added proper exception hierarchy using `TradingClientError` from `shared.errors.exceptions`
- Wrapped all API calls with `alpaca_retry_context` for automatic retry on transient failures
- Standardized error handling: methods now consistently raise `TradingClientError` on failure
- Improved error detection in `get_position()` to check multiple error message patterns
- Added proper exception chaining with `from e`

**Impact**:
- Better resilience to transient network/API failures
- Clear error propagation to callers
- Consistent error handling patterns throughout the service

### 3. Structured Logging (MEDIUM PRIORITY)
**Problem**: Logger calls used f-strings instead of structured logging parameters.

**Fix**:
- Replaced all f-string logger calls with structured parameters
- Added module context: `module="alpaca_account_service"`
- Used keyword arguments for error details: `error=str(e)`, `symbol=symbol`, etc.

**Impact**:
- Better observability and log aggregation
- Easier debugging with structured fields

### 4. Documentation (MEDIUM PRIORITY)
**Problem**: Missing detailed docstrings explaining error conditions and return types.

**Fix**:
- Added comprehensive docstrings to all modified methods
- Documented `Raises` sections for exception types
- Clarified return type semantics (e.g., "None if unavailable")
- Added notes about precision handling for financial values

**Impact**:
- Clearer API contracts
- Better IDE/editor support

## Ripple Effect Changes

To maintain type consistency, updated dependent files:

### 1. `shared/protocols/repository.py`
- Updated `AccountRepository` protocol methods to return `Decimal`
- Updated `TradingRepository` protocol methods to return `Decimal`
- Added `from decimal import Decimal` import

### 2. `shared/brokers/alpaca_manager.py`
- Updated method signatures to match new return types
- Added `from decimal import Decimal` import
- Updated `get_current_positions()` alias method

### 3. Version Bump
- Bumped version from 2.18.0 to 2.18.1 (patch version for bug fixes)

## Validation

All changes validated with:
- ✅ Type checking: `poetry run mypy` - Success
- ✅ Linting: `poetry run ruff check` - All checks passed
- ✅ Tests: 99 alpaca-related tests passed

## What Was NOT Changed

Intentionally kept minimal changes:
- Did not remove redundant `get_account_info()` method (breaking change)
- Did not extract timeframe normalization logic (separate refactoring task)
- Did not introduce new DTOs (architectural decision for separate PR)
- Did not remove `get_all_positions()` alias (breaking change)

## Remaining Recommendations

Low priority improvements for future PRs:
1. Create proper DTOs in `shared/schemas/account.py` for account data
2. Extract timeframe normalization to shared utility
3. Add comprehensive test coverage specifically for this service
4. Consider deprecating redundant methods with migration path

## Files Changed

1. `the_alchemiser/shared/services/alpaca_account_service.py` - Core fixes
2. `the_alchemiser/shared/protocols/repository.py` - Protocol updates
3. `the_alchemiser/shared/brokers/alpaca_manager.py` - Type signature updates
4. `pyproject.toml` - Version bump
5. `REVIEW_alpaca_account_service.md` - Detailed review document (new)

## Compliance Status

✅ **Numerical Correctness**: All money values use Decimal  
✅ **Error Handling**: Proper exception hierarchy, retry logic, narrow catches  
✅ **Observability**: Structured logging with context  
✅ **Type Safety**: Complete type hints, mypy clean  
✅ **Idempotency**: Read-only operations inherently idempotent  
✅ **Security**: No secrets, proper input handling  
✅ **Module Size**: 367 lines (within 500 line limit)  
✅ **Imports**: Clean structure, no wildcards  

## References

- Review Document: `REVIEW_alpaca_account_service.md`
- Copilot Instructions: `.github/copilot-instructions.md`
- Alpaca Architecture: `docs/ALPACA_ARCHITECTURE.md`
