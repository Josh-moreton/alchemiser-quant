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
- `the_alchemiser/shared_kernel/infrastructure/base_alpaca_adapter.py` - Base Alpaca adapter for shared connection management
- `the_alchemiser/shared_kernel/interfaces/__init__.py` - Shared kernel interfaces layer
- `the_alchemiser/shared_kernel/exceptions/__init__.py` - Exceptions package
- `the_alchemiser/shared_kernel/exceptions/base_exceptions.py` - Base exception classes and cross-cutting exceptions
- `the_alchemiser/shared_kernel/tooling/__init__.py` - Tooling package
- `the_alchemiser/shared_kernel/tooling/retry.py` - Retry utility functions
- `the_alchemiser/domain/shared_kernel/types.py` - Backwards compatibility shim (ActionType enum & value object re-exports)
- `the_alchemiser/domain/shared_kernel/tooling/__init__.py` - Tooling package (numeric helpers export)
- `the_alchemiser/domain/shared_kernel/tooling/num.py` - Float tolerance comparison utility (`floats_equal`)

### Strategy Context
**Business Unit**: strategy & signal generation | **Status**: current

- `the_alchemiser/strategy/__init__.py` - Strategy context entry point
- `the_alchemiser/strategy/domain/__init__.py` - Strategy domain layer
- `the_alchemiser/strategy/domain/exceptions.py` - Strategy-specific exception classes
- `the_alchemiser/strategy/application/__init__.py` - Strategy application layer
- `the_alchemiser/strategy/application/contracts/__init__.py` - Strategy application contracts package
- `the_alchemiser/strategy/application/contracts/_envelope.py` - Envelope mixin for consistent message metadata
- `the_alchemiser/strategy/application/contracts/signal_contract_v1.py` - Signal contract V1 for cross-context communication
- `the_alchemiser/strategy/application/use_cases/market_data_operations.py` - Market data operations use case
- `the_alchemiser/strategy/application/use_cases/strategy_data_service.py` - Strategy data service use case
- `the_alchemiser/strategy/infrastructure/__init__.py` - Strategy infrastructure layer
- `the_alchemiser/strategy/infrastructure/adapters/market_data_client.py` - Market data client adapter
- `the_alchemiser/strategy/infrastructure/adapters/streaming_adapter.py` - Streaming data adapter
- `the_alchemiser/strategy/infrastructure/adapters/alpaca_market_data_adapter.py` - Alpaca market data adapter
- `the_alchemiser/strategy/infrastructure/utils/price_utils.py` - Price utility functions
- `the_alchemiser/strategy/interfaces/__init__.py` - Strategy interfaces layer

### Portfolio Context
**Business Unit**: portfolio assessment & management | **Status**: current

- `the_alchemiser/portfolio/__init__.py` - Portfolio context entry point
- `the_alchemiser/portfolio/domain/__init__.py` - Portfolio domain layer
- `the_alchemiser/portfolio/domain/utils/__init__.py` - Portfolio domain utilities package
- `the_alchemiser/portfolio/domain/utils/account_data_utils.py` - Account data utility functions
- `the_alchemiser/portfolio/application/__init__.py` - Portfolio application layer
- `the_alchemiser/portfolio/application/contracts/__init__.py` - Portfolio application contracts package
- `the_alchemiser/portfolio/application/contracts/_envelope.py` - Envelope mixin for consistent message metadata
- `the_alchemiser/portfolio/application/contracts/rebalance_plan_contract_v1.py` - Rebalance plan contract V1 for cross-context communication
- `the_alchemiser/portfolio/application/use_cases/account_operations.py` - Account operations use case
- `the_alchemiser/portfolio/infrastructure/__init__.py` - Portfolio infrastructure layer
- `the_alchemiser/portfolio/infrastructure/adapters/alpaca_account_adapter.py` - Alpaca account adapter
- `the_alchemiser/portfolio/interfaces/__init__.py` - Portfolio interfaces layer

### Execution Context
**Business Unit**: order execution/placement | **Status**: current

- `the_alchemiser/execution/__init__.py` - Execution context entry point
- `the_alchemiser/execution/domain/__init__.py` - Execution domain layer
- `the_alchemiser/execution/domain/exceptions.py` - Execution-specific exception classes  
- `the_alchemiser/execution/application/__init__.py` - Execution application layer
- `the_alchemiser/execution/application/contracts/__init__.py` - Execution application contracts package
- `the_alchemiser/execution/application/contracts/_envelope.py` - Envelope mixin for consistent message metadata
- `the_alchemiser/execution/application/contracts/execution_report_contract_v1.py` - Execution report contract V1 for cross-context communication
- `the_alchemiser/execution/application/use_cases/order_operations.py` - Order operations use case
- `the_alchemiser/execution/application/use_cases/position_analysis.py` - Position analysis use case
- `the_alchemiser/execution/infrastructure/__init__.py` - Execution infrastructure layer
- `the_alchemiser/execution/infrastructure/adapters/alpaca_order_adapter.py` - Alpaca order adapter
- `the_alchemiser/execution/interfaces/__init__.py` - Execution interfaces layer
- `the_alchemiser/portfolio/domain/__init__.py` - Portfolio domain layer
- `the_alchemiser/portfolio/application/__init__.py` - Portfolio application layer
- `the_alchemiser/portfolio/infrastructure/__init__.py` - Portfolio infrastructure layer
- `the_alchemiser/portfolio/interfaces/__init__.py` - Portfolio interfaces layer

### Execution Context
**Business Unit**: order execution/placement | **Status**: current

- `the_alchemiser/execution/__init__.py` - Execution context entry point
- `the_alchemiser/execution/domain/__init__.py` - Execution domain layer
- `the_alchemiser/execution/application/__init__.py` - Execution application layer
- `the_alchemiser/execution/infrastructure/__init__.py` - Execution infrastructure layer
- `the_alchemiser/execution/interfaces/__init__.py` - Execution interfaces layer

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

- **Total new modules**: 47 new DDD bounded context modules (Task 1) + 4 migration utility modules (Task 2) + 18 services migration modules (Task 3)
- **Modules by business unit**:
  - utilities: 24 modules (shared_kernel + anti_corruption + interface utilities + tooling shim)
  - strategy & signal generation: 12 modules (strategy context with market data operations)
  - portfolio assessment & management: 9 modules (portfolio context with account operations)
  - order execution/placement: 10 modules (execution context with trading operations)
- **All modules status**: current

**Note**: Task 3 (DDD Epic #375) completed migration of services/ directory into bounded context domain & application layers. The legacy services structure has been eliminated and replaced with context-specific adapters and use cases following strict layered architecture.
