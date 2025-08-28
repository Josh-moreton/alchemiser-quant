# Business Units Report

This document provides an inventory of all modules in the Alchemiser system, categorized by business unit and status.

## Business Unit Classifications

Every module is classified under one of these business units:
- **strategy & signal generation**: Strategy engines, signal computation, and technical analysis
- **portfolio assessment & management**: Portfolio rebalancing, position management, and risk assessment
- **order execution/placement**: Order routing, execution algorithms, and trade settlement
- **utilities**: Cross-cutting concerns, shared infrastructure, and support functions

## Status Classifications
- **current**: Actively maintained, follows current architecture patterns
- **legacy**: Older code that may need refactoring or migration

---

## DDD Bounded Contexts (New Structure)

### Shared Kernel Context
**Business Unit**: utilities | **Status**: current

- `the_alchemiser/shared_kernel/__init__.py` - Shared kernel entry point
- `the_alchemiser/shared_kernel/value_objects/__init__.py` - Value objects package
- `the_alchemiser/shared_kernel/value_objects/money.py` - Money value object
- `the_alchemiser/shared_kernel/value_objects/percentage.py` - Percentage value object
- `the_alchemiser/shared_kernel/value_objects/identifier.py` - Identifier value object
- `the_alchemiser/shared_kernel/value_objects/symbol.py` - Symbol value object
- `the_alchemiser/shared_kernel/domain/__init__.py` - Shared kernel domain layer
- `the_alchemiser/shared_kernel/application/__init__.py` - Shared kernel application layer
- `the_alchemiser/shared_kernel/infrastructure/__init__.py` - Shared kernel infrastructure layer
- `the_alchemiser/shared_kernel/interfaces/__init__.py` - Shared kernel interfaces layer
- `the_alchemiser/shared_kernel/infrastructure/config/__init__.py` - Configuration infrastructure
- `the_alchemiser/shared_kernel/infrastructure/config/config_service.py` - Configuration service
- `the_alchemiser/shared_kernel/infrastructure/secrets/__init__.py` - Secrets management infrastructure
- `the_alchemiser/shared_kernel/infrastructure/secrets/secrets_service.py` - Secrets management service
- `the_alchemiser/shared_kernel/infrastructure/errors/__init__.py` - Error handling infrastructure
- `the_alchemiser/shared_kernel/infrastructure/errors/exceptions.py` - Custom exception classes
- `the_alchemiser/shared_kernel/infrastructure/errors/handler.py` - Error handler
- `the_alchemiser/shared_kernel/infrastructure/errors/decorators.py` - Error decorators
- `the_alchemiser/shared_kernel/infrastructure/errors/error_handling.py` - Error handling utilities
- `the_alchemiser/shared_kernel/infrastructure/errors/error_monitoring.py` - Error monitoring
- `the_alchemiser/shared_kernel/infrastructure/errors/error_recovery.py` - Error recovery
- `the_alchemiser/shared_kernel/infrastructure/errors/error_reporter.py` - Error reporting
- `the_alchemiser/shared_kernel/infrastructure/errors/context.py` - Error context
- `the_alchemiser/shared_kernel/infrastructure/errors/scope.py` - Error scope
- `the_alchemiser/shared_kernel/infrastructure/utilities/__init__.py` - Utilities infrastructure
- `the_alchemiser/shared_kernel/infrastructure/utilities/cache_manager.py` - Cache manager
- `the_alchemiser/shared_kernel/infrastructure/utilities/retry_decorator.py` - Retry decorator
- `the_alchemiser/shared_kernel/infrastructure/utilities/service_factory.py` - Service factory
- `the_alchemiser/domain/shared_kernel/types.py` - Backwards compatibility shim (ActionType enum & value object re-exports)
- `the_alchemiser/domain/shared_kernel/tooling/__init__.py` - Tooling package (numeric helpers export)
- `the_alchemiser/domain/shared_kernel/tooling/num.py` - Float tolerance comparison utility (`floats_equal`)

### Strategy Context
**Business Unit**: strategy & signal generation | **Status**: current

- `the_alchemiser/strategy/__init__.py` - Strategy context entry point
- `the_alchemiser/strategy/domain/__init__.py` - Strategy domain layer
- `the_alchemiser/strategy/application/__init__.py` - Strategy application layer
- `the_alchemiser/strategy/infrastructure/__init__.py` - Strategy infrastructure layer
- `the_alchemiser/strategy/interfaces/__init__.py` - Strategy interfaces layer
- `the_alchemiser/strategy/infrastructure/market_data/__init__.py` - Strategy infrastructure market data
- `the_alchemiser/strategy/infrastructure/market_data/market_data_service.py` - Market data service
- `the_alchemiser/strategy/infrastructure/market_data/market_data_client.py` - Market data client
- `the_alchemiser/strategy/infrastructure/market_data/price_fetching_utils.py` - Price fetching utilities
- `the_alchemiser/strategy/infrastructure/market_data/price_service.py` - Price service
- `the_alchemiser/strategy/infrastructure/market_data/price_utils.py` - Price utilities
- `the_alchemiser/strategy/infrastructure/market_data/streaming_service.py` - Streaming service
- `the_alchemiser/strategy/infrastructure/market_data/strategy_market_data_service.py` - Strategy market data service

### Portfolio Context
**Business Unit**: portfolio assessment & management | **Status**: current

- `the_alchemiser/portfolio/__init__.py` - Portfolio context entry point
- `the_alchemiser/portfolio/domain/__init__.py` - Portfolio domain layer
- `the_alchemiser/portfolio/application/__init__.py` - Portfolio application layer
- `the_alchemiser/portfolio/infrastructure/__init__.py` - Portfolio infrastructure layer
- `the_alchemiser/portfolio/interfaces/__init__.py` - Portfolio interfaces layer
- `the_alchemiser/portfolio/application/services/__init__.py` - Portfolio application services
- `the_alchemiser/portfolio/application/services/account_service.py` - Account management service
- `the_alchemiser/portfolio/application/services/account_utils.py` - Account data utilities
- `the_alchemiser/portfolio/application/services/position_service.py` - Position management service
- `the_alchemiser/portfolio/application/services/position_manager.py` - Position management utilities

### Execution Context
**Business Unit**: order execution/placement | **Status**: current

- `the_alchemiser/execution/__init__.py` - Execution context entry point
- `the_alchemiser/execution/domain/__init__.py` - Execution domain layer
- `the_alchemiser/execution/application/__init__.py` - Execution application layer
- `the_alchemiser/execution/infrastructure/__init__.py` - Execution infrastructure layer
- `the_alchemiser/execution/interfaces/__init__.py` - Execution interfaces layer
- `the_alchemiser/execution/application/services/__init__.py` - Execution application services
- `the_alchemiser/execution/application/services/order_service.py` - Order management service
- `the_alchemiser/execution/infrastructure/brokers/__init__.py` - Execution infrastructure brokers
- `the_alchemiser/execution/infrastructure/brokers/trading_service_manager.py` - Trading service manager
- `the_alchemiser/execution/infrastructure/repositories/__init__.py` - Execution infrastructure repositories
- `the_alchemiser/execution/infrastructure/repositories/alpaca_manager.py` - Alpaca repository manager

### Anti-Corruption Context
**Business Unit**: utilities | **Status**: current

- `the_alchemiser/anti_corruption/__init__.py` - Anti-corruption context entry point
- `the_alchemiser/anti_corruption/domain/__init__.py` - Anti-corruption domain layer
- `the_alchemiser/anti_corruption/application/__init__.py` - Anti-corruption application layer
- `the_alchemiser/anti_corruption/infrastructure/__init__.py` - Anti-corruption infrastructure layer
- `the_alchemiser/anti_corruption/interfaces/__init__.py` - Anti-corruption interfaces layer

### Interface Utilities (Added in Task 2 / PR #398)
**Business Unit**: utilities | **Status**: current

- `the_alchemiser/interfaces/utils/__init__.py` - Interface utilities package
- `the_alchemiser/interfaces/utils/serialization.py` - Boundary-safe serialization helpers

---

## Task 2 Migration (PR #398) – Retirement of `utils/` Module

Task 2 of Epic #375 removed the legacy monolithic `the_alchemiser/utils/` module. Responsibilities were redistributed to bounded contexts:

- `ActionType` enum → shared kernel types shim (`the_alchemiser/domain/shared_kernel/types.py`)
- Numeric helper `floats_equal` → shared kernel tooling (`the_alchemiser/domain/shared_kernel/tooling/num.py`)
- Serialization utilities → interface utilities (`the_alchemiser/interfaces/utils/serialization.py`)

All imports across impacted files were updated; no remaining references to the removed `utils` namespace exist.

## Summary

- **Total new modules**: 25 new DDD bounded context modules (Task 1) + 4 migration utility modules (Task 2)
- **Modules by business unit**:
  - utilities: 19 modules (shared_kernel + anti_corruption + interface utilities + tooling shim)
  - strategy & signal generation: 5 modules (strategy context)
  - portfolio assessment & management: 5 modules (portfolio context)
  - order execution/placement: 5 modules (execution context)
- **All modules status**: current

**Note**: Task 2 (PR #398) completed removal of the legacy `utils/` module. Task 3 (PR #399) completed migration of the `services/` directory into bounded context layers.

---

## Services Migration Summary (Task 3)

**Epic #375 Task 3**: Successfully migrated all services from `the_alchemiser/services/` into appropriate bounded context layers:

### Migrated Services by Context:

**Shared Kernel Infrastructure** (Cross-cutting concerns):
- Configuration management (config_service.py)
- Secrets management (secrets_service.py)
- Error handling utilities (exceptions, handlers, decorators, etc.)
- Caching and retry mechanisms
- Service factory utilities

**Portfolio Context Application** (Portfolio management):
- Account management service and utilities
- Position management service and utilities

**Strategy Context Infrastructure** (Market data for strategies):
- Market data service and client
- Price fetching and utilities
- Streaming services

**Execution Context** (Order execution):
- Order service (application layer)
- Trading service manager and Alpaca repository (infrastructure layer)

All services maintain their original functionality while now being properly classified within the DDD bounded context architecture. Import statements throughout the codebase have been updated accordingly.
