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
