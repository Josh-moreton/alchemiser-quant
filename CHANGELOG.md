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

## [2.10.1] - 2025-01-XX

### Added
- Comprehensive exception systems analysis documentation
  - Added `docs/EXCEPTIONS_ANALYSIS.md` with detailed investigation of legacy vs enhanced exception systems
  - Added `docs/EXCEPTIONS_QUICK_REFERENCE.md` for quick developer reference
  - Documents the relationship between `shared/types/exceptions.py` (legacy) and `shared/errors/enhanced_exceptions.py` (enhanced)
  - Provides clear recommendations: use legacy system for production code until enhanced system is fully migrated
  - Analysis confirms enhanced system extends legacy (not parallel) - EnhancedAlchemiserError inherits from AlchemiserError

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
