## [Unreleased]

### Fixed
- **Double run bug**: Removed production fallback schedule that was causing duplicate strategy executions
  - **Root Cause**: Production had both a dynamic schedule (3:45 PM ET via Schedule Manager) and a fallback schedule (3:50 PM ET). When the dynamic schedule succeeded, the fallback would still trigger 5 minutes later, creating a second workflow run
  - **Solution**: Removed the `StrategySchedule` fallback resource from `template.yaml`. All environments (dev/staging/prod) now rely solely on the Schedule Manager for dynamic scheduling
  - **Justification**: 
    - Dev/staging already relied on Schedule Manager only and worked correctly
    - The fallback was meant as a "safety net" but added unnecessary complexity
    - If Schedule Manager fails, we get notified through normal WorkflowFailed event channels
    - Simpler architecture is more maintainable
  - **Impact**: Eliminates duplicate production runs that were wasting Lambda invocations and potentially interfering with proper trade execution
  - **File Modified**: `template.yaml` (removed lines 1741-1756)
  - **Note**: `StrategySchedulerRole` IAM role remains as it's still needed by the dynamic schedules created by Schedule Manager

- **Portfolio planner buying power validation**: Fixed critical bug where rebalance plans could exceed available capital
  - Root cause: Target allocations were calculated using total portfolio value rather than deployable capital
  - Changed `_calculate_dollar_values()` to use deployable capital = (cash + expected full exit proceeds) * (1 - cash_reserve_pct)
  - Previously used `portfolio_value * 0.99` which didn't account for capital already committed to existing positions
  - Added validation safety check that ensures BUY orders never exceed (cash + sell proceeds)
  - Added regression test `test_prevents_over_allocation_with_partial_positions` to catch partial position rebalancing bugs
  - Prevents execution failures from mathematically impossible trade plans
  - File: `the_alchemiser/portfolio_v2/core/planner.py`
## [3.3.11] - 2025-11-20

### Fixed
- **Critical: Full position liquidation failures due to fractional share precision mismatch**
  - **Root Cause**: When liquidating entire positions (target_weight=0%), the executor calculated exact share quantities that differed from Alpaca's reported available quantity by tiny fractions (e.g., requested 7.227358 vs available 7.2273576), causing limit orders to fail with "insufficient qty available" errors
  - **Primary Fix**: Implemented fallback chain for full position liquidations:
    1. **First**: Use Alpaca's `liquidate_position(symbol)` API (most reliable, handles exact quantity internally)
    2. **Second**: Fall back to smart execution with `is_complete_exit=True` flag
    3. **Third**: Use standard market order with `is_complete_exit=True` to fetch actual available quantity from position
  - **Changes**:
    - Modified `Executor._execute_single_item()` to detect full liquidations (target_weight=0 AND action=SELL) and call `liquidate_position()` API first
    - Added `is_complete_exit` parameter propagation through `execute_order()`, `_try_smart_execution()`, and `_execute_market_order()`
    - Enhanced `_execute_market_order()` to use `place_market_order(is_complete_exit=True)` which fetches actual available quantity from Alpaca position data
    - Used existing `is_complete_exit` flag in `SmartOrderRequest` for proper quantity adjustment in market order fallback
  - **Secondary Fix**: Enhanced buying power validation after sell settlement to detect and log when sell orders fail
    - Added detailed logging of buying power shortfall with percentage calculations
    - Added critical alerts when total BUY order cost exceeds available buying power
    - Improved error visibility for sell phase failures affecting buy phase execution
  - **Impact**: Eliminates fractional share precision errors causing ~$300+ sell order failures in production (SQQQ example: 7.227358 shares requested vs 7.2273576 available)
  - **Files Modified**:
    - `the_alchemiser/execution_v2/core/executor.py` (60+ line changes)
    - `the_alchemiser/execution_v2/utils/position_utils.py` (precision rounding fix)
    - `the_alchemiser/execution_v2/core/phase_executor.py` (order placement detection)
    - `tests/execution_v2/test_position_utils.py` (test updates for precision rounding)
    - `pyproject.toml` (version bump)
    - `CHANGELOG.md` (this file)

## [2.30.0] - 2025-10-27

### Changed
- **Documentation Reorganization**: Comprehensive restructuring of `docs/` folder (392 files)
  - Created hierarchical structure with 47 directories and 14 README indexes
  - Organized former file_reviews/ (324 files) into code-reviews/2025-10/ by module (strategy_v2, portfolio_v2, execution_v2, shared, orchestration)
  - Applied consistent naming: YYYY-MM-DD_ prefix for dated documents
  - Moved root-level docs to appropriate categories: architecture/, guides/, bug-fixes/, analysis/, etc.
  - Created comprehensive main docs/README.md with navigation
  - Generated code-reviews/index-by-file.md for easy file lookup across all reviews
  - Preserved git history with `git mv` commands
  - Improved discoverability: find any document within 2 clicks
  - Living documents (guides, architecture) have no dates; historical docs (bug fixes, reviews) are dated
  - Updated internal documentation links in current files to new paths (historical CHANGELOG references to old paths remain as-is for accuracy)

## [2.23.1] - 2025-10-13

### Changed
- **Refactored PhaseExecutor to reduce cognitive complexity**: Addressed SonarQube CRITICAL issue
  - Extracted common phase execution logic into `_execute_phase()` helper method
  - Extracted order execution logic into `_execute_order()` helper method
  - Reduced `execute_buy_phase` cognitive complexity from 16 to 0 (below limit of 15)
  - Reduced `execute_sell_phase` cognitive complexity from 10 to 0
  - Applied DRY principle - eliminated code duplication between sell and buy phases
  - Maintained backward compatibility - no API changes
  - Preserved all existing behavior including idempotency, micro-order checks, and logging
  - File: `the_alchemiser/execution_v2/core/phase_executor.py`

## [2.21.0] - 2025-10-13

### Added
- **Comprehensive test suite for AlpacaManager**: Created `tests/shared/brokers/test_alpaca_manager.py` with 25 tests
  - Singleton behavior tests (6 tests): same/different credentials, cleanup, hash collision handling
  - Credential security tests (5 tests): hashing, deprecation warnings, no credential exposure in logs/repr
  - Thread safety tests (3 tests): concurrent instance creation, cleanup coordination with Events, multiple threads
  - Delegation tests (6 tests): market data operations, Decimal handling (float/Decimal defensive conversion), properties
  - Cleanup tests (3 tests): cleanup_all_instances, error isolation per instance, post-cleanup instance creation
  - Factory function tests (2 tests): create_alpaca_manager creation and singleton respect
  - All tests use proper mocking to avoid external dependencies
  - Target: 80%+ test coverage for critical integration point

### Changed
- **AlpacaManager architectural documentation**: Enhanced documentation for circular import pattern
  - Created `docs/adr/ADR-001-circular-imports.md` documenting intentional circular import trade-offs
  - Added comprehensive module docstring explaining singleton facade pattern and import requirements
  - Added inline comments at import locations (lines ~248, ~264) explaining circular dependency rationale
  - Documents that WebSocketConnectionManager and MarketDataService imports are intentionally deferred to __init__
  - References ADR in all relevant locations for architectural clarity
  - Created `docs/adr/README.md` with ADR usage guidelines and template

- **Optimized Decimal conversion in get_current_price**: Defensive programming for type safety
  - Added conditional conversion: checks if price is already Decimal before converting
  - Handles both Decimal and float returns from MarketDataService
  - Prevents unnecessary string conversion overhead when service returns Decimal
  - Maintains backward compatibility while preparing for future service enhancements
  - Converts via string (Decimal(str(price))) to avoid float precision issues

- **Enhanced factory function documentation**: Added usage context and rationale
  - Documented `create_alpaca_manager` is used by `pnl_service.py`
  - Added note about backward compatibility and stable public API
  - Included usage example in docstring
  - Clarifies factory provides minimal overhead and supports dependency injection

### Security
- **No changes to security posture**: All high-priority security fixes already completed in PR #2202
  - Credentials remain hashed (SHA-256) for dictionary keys
  - Credential properties still emit deprecation warnings
  - No credential exposure in logs, debug output, or __repr__

## [2.20.7] - 2025-10-10

### Added
- **File review documentation**: Completed institutional-grade review of `enhanced_exceptions.py`
  - Created `docs/file_reviews/FILE_REVIEW_enhanced_exceptions.md` documenting file removal
  - Confirmed file was correctly removed in v2.10.1 (never used in production)
  - Documented current exception system architecture (`shared/errors/exceptions.py`)
  - Provided recommendations for review process improvements (file existence validation)
  - References existing exception documentation (`EXCEPTIONS_ANALYSIS.md`, `EXCEPTIONS_QUICK_REFERENCE.md`)
## 2.21.0 - 2025-10-10

### Enhanced
- **RepegMonitoringService audit and improvements**: Institution-grade improvements to repeg monitoring
  - **Added typed error handling** - Created `RepegMonitoringError` extending `AlchemiserError` with context
  - **Added input validation** - phase_type now uses `Literal["SELL", "BUY"]`, config structure validated
  - **Added correlation tracking** - All methods now accept and propagate `correlation_id` for traceability
  - **Extracted magic numbers** - Created module constants (GRACE_WINDOW_SECONDS, EXTENDED_WAIT_MULTIPLIER, DEFAULT_MAX_REPEGS)
  - **Enhanced observability** - All log statements now include structured context with correlation_id
  - **Improved error handling** - Replaced generic Exception catches with specific typed exceptions
  - **Added safe attribute access** - Added guards for order_tracker and repeg_manager access
  - **Enhanced docstrings** - Added detailed documentation including Raises sections and usage examples
  - **Updated tests** - Added test coverage for new validation logic and error cases
  - **Created comprehensive audit report** - Full line-by-line review in `docs/file_reviews/FILE_REVIEW_repeg_monitoring_service.md`

## 2.16.5 - 2025-10-08

### Changed
- **SAM Build Architecture Improvement**: Optimized Lambda packaging following AWS best practices
  - **Changed CodeUri from `./` to `the_alchemiser/`** - SAM now only scans application directory
  - **Updated Handler path** - Now `lambda_handler.lambda_handler` (relative to CodeUri)
  - **Simplified exclusion patterns** - Moved from extensive root-level exclusions to minimal, focused patterns
  - **Added explicit includes** - Strategy files (*.clj) and config files (*.json) now explicitly included
  - **All exclusions in template.yaml** - BuildProperties now handles all exclusions including security (.env*, .aws/)
  - **Benefits**: Cleaner build process, easier maintenance, more aligned with AWS SAM documentation
  - **Documentation**: Created `docs/SAM_BUILD_ARCHITECTURE.md` with comprehensive build architecture guide

## 2.16.6 - 2025-10-09

### Fixed
- **Development workflow**: Aligned Makefile `format` target with pre-commit hooks to prevent double commits
  - Added trailing whitespace removal (matches pre-commit's `trailing-whitespace` hook)
  - Added end-of-file newline fixer (matches pre-commit's `end-of-file-fixer` hook)
  - Running `make format` now produces the same result as pre-commit hooks
  - Eliminates the need for two commits when using `make format && make type-check` before committing
  - Updated help text to reflect all formatting steps performed

## 2.16.1 - 2025-10-07

### Fixed
- **AWS Lambda deployment**: Fixed layer size exceeding 250MB unzipped limit and build failures
  - **Moved `pyarrow` from main to dev dependencies** - only needed for local backtest scripts, saves ~100MB
  - **Added `--use-container` flag to SAM build** - ensures Lambda-compatible wheel resolution for pandas/numpy
  - Enhanced `template.yaml` exclusions to prevent dev-only files from being packaged:
    - Excluded `scripts/` directory (backtest, stress_test - dev only)
    - Excluded data files (*.csv, *.parquet, data/ directory)
    - Excluded all Python cache artifacts (*.pyc, *.pyo, __pycache__)
    - Excluded documentation and configuration files not needed at runtime
  - Added Docker availability check in deployment script (required for container builds)
  - **Layer size reduced from ~287MB to ~149MB unzipped** (well under 250MB limit)
  - Changed pandas version constraint from `2.3.3` to `^2.2.0` for better wheel compatibility

## 2.20.2 - 2025-01-10

### Fixed
- **Mapper validation and observability**: Enhanced `execution_summary_mapping.py` with production-ready controls
  - **Added input validation** - All dict_to_* functions now validate dict inputs with TypeError on failure
  - **Added structured logging** - All conversions now log with correlation_id for traceability
  - **Fixed mode validation** - dict_to_execution_summary now validates mode is "paper" or "live" before DTO construction
  - **Fixed Decimal precision** - Replaced float defaults (0.0) with ZERO_DECIMAL constant to prevent precision loss
  - **Fixed idempotency issue** - dict_to_portfolio_state now accepts correlation_id/causation_id/timestamp as parameters
  - **Removed dead code** - Deleted unused allocation_comparison_to_dict function with silent error handling
  - **Added comprehensive docstrings** - All functions now document Args/Returns/Raises with field descriptions
  - **Added __all__ export** - Explicit API surface definition for public functions
  - **Added constants** - UNKNOWN_STRATEGY, DEFAULT_PORTFOLIO_ID, ZERO_DECIMAL for consistent defaults

### Added
- **Comprehensive test suite** - Created tests/shared/mappers/test_execution_summary_mapping.py
  - Tests for all dict_to_* functions with happy path, edge cases, and error conditions
  - Tests for Decimal precision preservation
  - Tests for default value handling
  - Tests for type validation
- **FILE_REVIEW documentation** - Created comprehensive line-by-line audit document
  - Identified 15 issues across Critical/High/Medium/Low severities
  - Documented all findings with severity labels and proposed fixes
  - Follows institution-grade review standards

## 2.16.1 - 2025-10-07

### Fixed
- **AWS Lambda deployment**: Fixed layer size exceeding 250MB unzipped limit and build failures
  - **Moved `pyarrow` from main to dev dependencies** - only needed for local backtest scripts, saves ~100MB
  - **Added `--use-container` flag to SAM build** - ensures Lambda-compatible wheel resolution for pandas/numpy
  - Enhanced `template.yaml` exclusions to prevent dev-only files from being packaged:
    - Excluded `scripts/` directory (backtest, stress_test - dev only)
    - Excluded data files (*.csv, *.parquet, data/ directory)
    - Excluded all Python cache artifacts (*.pyc, *.pyo, __pycache__)
    - Excluded documentation and configuration files not needed at runtime
  - Added Docker availability check in deployment script (required for container builds)
  - **Layer size reduced from ~287MB to ~149MB unzipped** (well under 250MB limit)
  - Changed pandas version constraint from `2.3.3` to `^2.2.0` for better wheel compatibility

## 2.5.16 - 2025-10-03

### Changed
- Stress test now supports dedicated `STRESS_TEST_KEY`/`STRESS_TEST_SECRET` environment variables. When present, these override standard Alpaca credentials for the session.
- The stress test unconditionally forces `ALPACA_ENDPOINT` to `https://paper-api.alpaca.markets/v2` to prevent accidental live trading during stress runs.

### Notes
- Docs updated in `scripts/STRESS_TEST_README.md` to explain the new env vars and paper-mode safety.

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [2.21.0] - 2025-01-10

### Fixed
- **shared/notifications/config.py** - Comprehensive remediation of all findings from file review
  - **HIGH**: Replaced bare `except Exception` handlers with typed `ConfigurationError` from `shared.errors`
  - **HIGH**: Removed PII leakage - no longer logs email addresses in debug mode
  - **HIGH**: Converted all logging to structured format with explicit parameters (no f-strings)
  - **HIGH**: Changed return type from `Optional[EmailCredentials]` to `EmailCredentials` with proper error raising
  - **MEDIUM**: Added thread-safe singleton pattern with double-check locking for global instance
  - **MEDIUM**: Implemented caching for `neutral_mode` flag to avoid redundant config loads
  - **MEDIUM**: Updated business unit classification from "utilities" to "notifications"
  - **LOW**: Added comprehensive docstrings with examples, pre/post-conditions, and use cases
  - **LOW**: Added deprecation warnings to backward compatibility functions (`get_email_config`, `is_neutral_mode_enabled`)
  - **INFO**: Enhanced class docstring with thread safety notes and caching strategy documentation

### Added
- **tests/shared/notifications/test_config.py** - Comprehensive test suite (400+ lines)
  - Test successful configuration loading with all fields
  - Test caching behavior and cache invalidation
  - Test missing required fields raise `ConfigurationError`
  - Test default fallback behavior (to_email defaults to from_email)
  - Test neutral mode caching and error handling
  - Test thread safety of singleton pattern with concurrent access
  - Test backward compatibility functions with deprecation warnings
  - Test error wrapping as `ConfigurationError` with proper chaining
  - 100% coverage of public API methods

### Changed
- **shared/notifications/config.py** - API changes for better type safety
  - `EmailConfig.get_config()` now raises `ConfigurationError` instead of returning `None`
  - `EmailConfig.is_neutral_mode_enabled()` now raises `ConfigurationError` on errors instead of returning `False`
  - Backward compatibility functions maintain original behavior (return `None`/`False` on errors) but emit deprecation warnings
  - Added `MODULE_NAME` constant for consistent structured logging

### Added
- **docs/file_reviews/FILE_REVIEW_shared_notifications_config.md** - Comprehensive financial-grade line-by-line audit of email configuration module
  - Identified 4 High severity issues (bare exception handlers, PII logging, tuple-returning legacy function)
  - Identified 5 Medium severity issues (f-string logging, cache validation, global mutable state)
  - Identified 4 Low severity issues (import inconsistencies, missing test coverage, performance)
  - Provided detailed remediation plan with priority-ordered fixes
  - Included comprehensive testing recommendations and implementation checklist

### Fixed
- **performance.py notification templates** - Complete refactor to address institutional-grade standards
  - **HIGH**: Replaced `Any` type hints with typed DTOs (`OrderNotificationDTO`, `TradingSummaryDTO`, `StrategyDataDTO`)
  - **HIGH**: Converted all float formatting to use `Decimal` for monetary values
  - **MEDIUM**: Added comprehensive docstrings with pre/post-conditions, failure modes, and examples
  - **MEDIUM**: Added structured logging with context for debugging and observability
  - **MEDIUM**: Added order truncation warnings when >10 orders displayed
  - **MEDIUM**: Improved order categorization with enum-based logic
  - **MEDIUM**: Added input validation with proper error handling
  - **LOW**: Extracted color and styling logic to constants (DRY principle)
  - **LOW**: Fixed magic number (MAX_REASON_LENGTH = 100) with named constant
  - **LOW**: Improved reason text truncation safety

### Added
- **shared/schemas/notifications.py** - New DTOs for type-safe email templates
  - `OrderSide` enum for BUY/SELL operations
  - `OrderNotificationDTO` with Decimal quantity and optional estimated_value
  - `TradingSummaryDTO` with validated counts and Decimal monetary values
  - `StrategyDataDTO` with allocation bounds (0.0-1.0) validation
- **tests/shared/notifications/templates/test_performance.py** - Comprehensive test suite (100+ tests)
  - Tests for all public methods with valid and edge case inputs
  - Tests for DTO validation and type safety
  - Tests for HTML structure and content correctness
  - Tests for order truncation behavior
  - Tests for Decimal handling
- **tests/shared/schemas/test_notifications.py** - Extended with DTO tests
  - Tests for OrderSide enum
  - Tests for OrderNotificationDTO validation and immutability
  - Tests for TradingSummaryDTO bounds checking
  - Tests for StrategyDataDTO allocation validation (0.0-1.0)
## [2.20.0] - 2025-01-06

### Added
- **File review document** - Comprehensive institution-grade review of `shared/schemas/__init__.py`
  - 680+ lines of detailed analysis covering correctness, security, performance, and compliance
  - Line-by-line audit table with severity classifications
  - Identified 1 critical issue, 2 medium issues, 2 low issues
  - Documentation in `docs/file_reviews/FILE_REVIEW_shared_schemas_init.md`
- **Backward compatibility for ErrorContextData** - Deprecated import path now supported
  - `ErrorContextData` moved from `shared.schemas.errors` to `shared.errors.context` in v2.18.0
  - Added `__getattr__` hook to provide backward compatibility with deprecation warning
  - Warns users to update imports, scheduled for removal in v3.0.0
  - Prevents breaking existing code that imports from old location
- **Comprehensive test suite** - `tests/shared/schemas/test_init.py` with 15 tests
  - Verifies all 58 exports are importable
  - Tests backward compatibility and deprecation warnings
  - Validates alphabetical sorting of `__all__`
  - Checks module documentation and Pydantic model conformance
  - Verifies invalid attribute access raises proper errors

### Fixed
- **Critical: Broken ErrorContextData export** - Fixed `AttributeError` on import
  - `ErrorContextData` was listed in `__all__` but not imported (moved to different module)
  - Would cause runtime errors for any code importing it
  - Fixed with backward compatibility shim + deprecation warning
- **Medium: Unsorted __all__ exports** - Alphabetically sorted 58 exports for maintainability
  - Previously unordered, making it difficult to spot missing/duplicate entries
  - Now sorted A-Z for easy maintenance and code review
  - Consistent with best practices seen in other reviewed modules

### Changed
- **Schemas module version** - Bumped from 2.19.0 to 2.20.0 (MINOR version)
  - New backward compatibility feature (non-breaking change)
  - Follows semantic versioning guidelines from copilot-instructions.md

### Removed
- **reporting.py schema module** - Removed unused dashboard and reporting DTOs
  - `DashboardMetrics`, `ReportingData`, `EmailReportData`, `EmailSummary` (0 usages)
  - `BacktestResult`, `PerformanceMetrics` (only commented-out references)
  - `MonthlySummaryDTO` and monthly summary email infrastructure removed
  - Eliminates ~1000 lines of unused code (DTOs, tests, templates)
- **monthly.py email template** - Monthly summary email functionality removed for simplicity
- **test_reporting.py** - 31 tests for removed reporting DTOs
- **test_monthly_summary_email.py** - Tests for removed monthly email template

### Added
- **notifications.py schema module** - New focused schema for email infrastructure
  - Extracted `EmailCredentials` from reporting.py to appropriate location
  - Maintains SMTP configuration for email notification system
  - Includes comprehensive test suite (6 tests)

### Changed
- **email_facade.py** - Deprecated `monthly_financial_summary()` method
  - Returns deprecation notice instead of generating email
  - Monthly P&L analysis in `pnl_service.py` remains functional (separate from emails)
- **client.py, config.py** - Updated imports to use `shared.schemas.notifications`

## [2.13.1] - 2025-10-07

### Fixed
- **Schema consolidation**: Removed duplicate schema definitions in `shared/errors/error_types.py`
  - `ErrorDetailInfo`, `ErrorSummaryData`, `ErrorReportSummary`, `ErrorNotificationData` now re-exported from canonical location (`shared/schemas/errors`)
  - Eliminated field mismatch: `ErrorNotificationData` now consistently has 9 fields (added `success`, `email_sent`, `correlation_id`, `event_id` to canonical version)
  - Added explicit `__all__` exports for backward compatibility
  - All 147 tests pass, no type errors

## [2.13.0] - 2025-10-07

### Changed
- **BREAKING**: Completed TypedDict → Pydantic migration for runtime validation
  - Migrated `shared/schemas/errors.py`: ErrorDetailInfo, ErrorSummaryData, ErrorReportSummary, ErrorNotificationData, ErrorContextData
  - Migrated `shared/schemas/reporting.py`: DashboardMetrics, ReportingData, EmailReportData, EmailCredentials, EmailSummary, BacktestResult, PerformanceMetrics
  - Migrated `shared/schemas/cli.py`: CLIOptions, CLICommandResult, CLISignalData, CLIAccountDisplay, CLIPortfolioData, CLIOrderDisplay
  - **All schemas now use Pydantic BaseModel with `ConfigDict(strict=True, frozen=True)` for immutability and runtime validation**
  - **Breaking changes**:
    - Dict-style access (e.g., `credentials["host"]`) replaced with attribute access (e.g., `credentials.host`)
    - ErrorContextData construction now requires Pydantic kwargs (e.g., `ErrorNotificationData(error_type=..., message=...)`)
    - Empty dicts are now returned instead of None for optional dict fields (Pydantic default_factory behavior)
    - `.to_dict()` methods use `model_dump(exclude_none=True)` (None values omitted from dict)

### Added
- Unified `shared/errors/context.py` with canonical ErrorContextData implementation
  - Full event-driven architecture support: `correlation_id`, `causation_id` fields
  - Optional `operation`, `component`, `function_name` for error location tracking
  - Auto-generated ISO 8601 timestamps
  - Backward-compatible with legacy `module` and `function` fields
  - Immutable frozen model with strict validation

### Deprecated
- `shared/errors/error_types.py` classes (ErrorDetailInfo, ErrorSummaryData, etc.)
  - Use canonical versions from `shared.schemas.errors` instead
  - Deprecation warnings added with migration guidance

### Fixed
- Error handler Pydantic compatibility: Updated ErrorNotificationData construction from dict to Pydantic model instantiation
- Notification module Pydantic compatibility: EmailCredentials dict access → attribute access
- Test expectations updated to match Pydantic behavior (empty dict defaults, exclude_none serialization)

## [2.12.0] - 2025-10-07

### Changed
- **BREAKING**: Moved exception classes from `shared/types/` to `shared/errors/` directory
  - `shared/types/exceptions.py` → `shared/errors/exceptions.py` (375 lines, 25+ exception classes)
  - `shared/types/trading_errors.py` → `shared/errors/trading_errors.py` (111 lines, OrderError + helpers)
  - Updated ~68 import statements across production code, tests, scripts, and documentation
  - **Rationale**: Exceptions are error-handling constructs, not type definitions; semantically belong in errors/ module
  - **Migration**: Replace `from the_alchemiser.shared.types.exceptions import ...` with `from the_alchemiser.shared.errors.exceptions import ...`

### Fixed
- Resolved 5 mypy errors from missing EnhancedDataError/EnhancedAlchemiserError (deleted in PR #1976)
- Updated all internal module imports in errors/ directory for consistency

## [2.10.1] - 2025-01-XX

### Added
- Exception system documentation
  - Added `docs/EXCEPTIONS_ANALYSIS.md` with comprehensive documentation
  - Added `docs/EXCEPTIONS_QUICK_REFERENCE.md` for quick developer reference
  - Documents `shared/types/exceptions.py` as the single active exception system
  - Provides usage guidelines, best practices, and complete exception reference

### Removed
- Removed unused enhanced exception system
  - Removed `shared/errors/enhanced_exceptions.py` (never used in production)
  - Removed `tests/shared/errors/test_enhanced_exceptions.py`
  - Removed `create_enhanced_error()` helper function from error_handler.py
  - Cleaned up exports from `shared/errors/__init__.py`
  - This simplifies the codebase by removing unused experimental code

### Removed
- **BREAKING**: Removed deprecated `the_alchemiser.shared.dto` shim module; use `the_alchemiser.shared.schemas` instead
  - The compatibility layer that provided backward compatibility has been removed
  - All imports from `the_alchemiser.shared.dto` will now raise `ImportError`
  - **Migration**: Replace `from the_alchemiser.shared.dto import ...` with `from the_alchemiser.shared.schemas import ...`

### Changed
- Updated documentation to use `shared.schemas` terminology instead of `shared.dto`
- Added import-linter rule to forbid future imports from deprecated DTO paths
- Updated module docstrings to reference schemas instead of DTOs

### Added
- Defensive test to ensure `the_alchemiser.shared.dto` imports raise `ImportError`
