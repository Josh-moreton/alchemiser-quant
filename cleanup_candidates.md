# Shared Module Cleanup Candidates

Based on the usage analysis report, the following files and cleanup opportunities have been identified:

## High-Priority Removal Candidates (70 files with no importers)

### CLI Module (5 files) - Consider moving to application layer
- `cli/base_cli.py` - Base CLI functionality (1 symbol)
- `cli/cli.py` - Main CLI implementation (16 symbols) 
- `cli/dashboard_utils.py` - Dashboard utilities (6 symbols)
- `cli/strategy_tracking_utils.py` - Strategy tracking (3 symbols)

### Configuration Module (6 files) - Many appear unused
- `config/config_providers.py` - Config providers (1 symbol)
- `config/config_service.py` - Config service (1 symbol)  
- `config/env_loader.py` - Environment loader (0 symbols)
- `config/infrastructure_providers.py` - Infrastructure providers (1 symbol)
- `config/secrets_manager.py` - Secrets management (3 symbols)
- `config/service_providers.py` - Service providers (1 symbol)

### DTO Module (4 files) - Some DTOs unused
- `dto/broker_dto.py` - Broker DTOs (5 symbols)
- `dto/execution_report_dto.py` - Execution report (2 symbols)
- `dto/lambda_event_dto.py` - Lambda event (1 symbol)
- `dto/order_request_dto.py` - Order request (2 symbols)

### Notification System (9 files) - Entire subsystem unused
- `notifications/client.py` - Client (2 symbols)
- `notifications/config.py` - Config (3 symbols)
- `notifications/templates/base.py` - Base template (1 symbol)
- `notifications/templates/email_facade.py` - Email facade (4 symbols)
- `notifications/templates/multi_strategy.py` - Multi-strategy (1 symbol)
- `notifications/templates/performance.py` - Performance (1 symbol)
- `notifications/templates/portfolio.py` - Portfolio (3 symbols)
- `notifications/templates/signals.py` - Signals (1 symbol)

### Persistence Layer (3 files) - Storage handlers
- `persistence/factory.py` - Factory (3 symbols)
- `persistence/local_handler.py` - Local handler (1 symbol)
- `persistence/s3_handler.py` - S3 handler (1 symbol)

### Protocols (6 files) - Interface definitions
- `protocols/alpaca.py` - Alpaca protocols (2 symbols)
- `protocols/asset_metadata.py` - Asset metadata (1 symbol)
- `protocols/order_like.py` - Order-like (2 symbols)
- `protocols/persistence.py` - Persistence (1 symbol)
- `protocols/repository.py` - Repository (3 symbols)
- `protocols/strategy_tracking.py` - Strategy tracking (4 symbols)

### Schema Definitions (7 files) - Many schema definitions
- `schemas/accounts.py` - Account schemas (14 symbols)
- `schemas/base.py` - Base schemas (2 symbols)
- `schemas/cli.py` - CLI schemas (6 symbols)
- `schemas/enriched_data.py` - Enriched data (8 symbols)
- `schemas/errors.py` - Error schemas (5 symbols)
- `schemas/execution_summary.py` - Execution summary (12 symbols)
- `schemas/market_data.py` - Market data (10 symbols)
- `schemas/operations.py` - Operations (6 symbols)
- `schemas/reporting.py` - Reporting (7 symbols)

### Utilities (10 files) - Various utility functions  
- `utils/config.py` - Config utilities (3 symbols)
- `utils/context.py` - Context utilities (2 symbols)
- `utils/decorators.py` - Decorators (6 symbols)
- `utils/dto_conversion.py` - DTO conversion (8 symbols)
- `utils/price_discovery_utils.py` - Price discovery (7 symbols)
- `utils/serialization.py` - Serialization (2 symbols)
- `utils/timezone_utils.py` - Timezone utilities (3 symbols)
- `utils/validation_utils.py` - Validation (10 symbols)

## Re-export Cleanup Opportunities

The analysis found 24 re-exported symbols, indicating potential for simplifying import paths and reducing indirection in the `__init__.py` files.

## Recommendations

1. **Phase 1**: Remove obvious dead code (notifications, unused DTOs, empty files)
2. **Phase 2**: Evaluate CLI code for move to application layer
3. **Phase 3**: Consolidate configuration management 
4. **Phase 4**: Review and simplify re-exports
5. **Phase 5**: Update BUSINESS_UNITS_REPORT.md to reflect changes

## Impact Assessment

- **376 unused symbols** across 70 files represent significant cleanup opportunity
- **Total reduction potential**: ~67% of shared module files could be removed
- **Risk**: Low - these are unused files with no current importers
- **Benefit**: Cleaner module structure, reduced maintenance burden, clearer API surface