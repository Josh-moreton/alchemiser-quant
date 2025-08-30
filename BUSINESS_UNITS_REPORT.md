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

### Cross-Context Event Communication (DDD Epic #375 Phase 8)
**Business Unit**: utilities | **Status**: current

- `the_alchemiser/cross_context/__init__.py` - Cross-context coordination package
- `the_alchemiser/cross_context/eventing/__init__.py` - Eventing infrastructure package  
- `the_alchemiser/cross_context/eventing/event_bus.py` - EventBus protocol for publish/subscribe
- `the_alchemiser/cross_context/eventing/in_memory_event_bus.py` - In-memory EventBus implementation with idempotency
- `the_alchemiser/cross_context/eventing/composition_root.py` - Event system composition root and wiring

### Strategy Context
**Business Unit**: strategy & signal generation | **Status**: current

- `the_alchemiser/strategy/__init__.py` - Strategy context entry point
- `the_alchemiser/strategy/domain/__init__.py` - Strategy domain layer
- `the_alchemiser/strategy/domain/exceptions.py` - Strategy-specific exception classes
- `the_alchemiser/strategy/domain/value_objects/__init__.py` - Strategy domain value objects package
- `the_alchemiser/strategy/domain/value_objects/market_bar_vo.py` - Market data value object for OHLCV bars
- `the_alchemiser/strategy/application/__init__.py` - Strategy application layer
- `the_alchemiser/strategy/application/ports.py` - External dependency protocols (MarketDataPort, SignalPublisherPort)
- `the_alchemiser/strategy/application/contracts/__init__.py` - Strategy application contracts package
- `the_alchemiser/strategy/application/contracts/_envelope.py` - Envelope mixin for consistent message metadata
- `the_alchemiser/strategy/application/contracts/signal_contract_v1.py` - Signal contract V1 for cross-context communication
- `the_alchemiser/strategy/application/use_cases/market_data_operations.py` - Market data operations use case
- `the_alchemiser/strategy/application/use_cases/strategy_data_service.py` - Strategy data service use case
- `the_alchemiser/strategy/application/use_cases/generate_signals.py` - Signal generation use case
- `the_alchemiser/strategy/infrastructure/__init__.py` - Strategy infrastructure layer
- `the_alchemiser/strategy/infrastructure/adapters/market_data_client.py` - Market data client adapter
- `the_alchemiser/strategy/infrastructure/adapters/streaming_adapter.py` - Streaming data adapter
- `the_alchemiser/strategy/infrastructure/adapters/alpaca_market_data_adapter.py` - Alpaca market data adapter
- `the_alchemiser/strategy/infrastructure/adapters/in_memory_market_data_adapter.py` - In-memory market data adapter for testing
- `the_alchemiser/strategy/infrastructure/adapters/in_memory_signal_publisher_adapter.py` - In-memory signal publisher adapter for testing
- `the_alchemiser/strategy/infrastructure/adapters/event_bus_signal_publisher_adapter.py` - EventBus-based signal publisher adapter
- `the_alchemiser/strategy/infrastructure/adapters/alpaca_market_data_port_adapter.py` - Alpaca market data adapter implementing MarketDataPort protocol
- `the_alchemiser/strategy/infrastructure/adapters/sqs_signal_publisher_adapter.py` - SQS signal publisher adapter implementing SignalPublisherPort protocol
- `the_alchemiser/strategy/infrastructure/utils/price_utils.py` - Price utility functions
- `the_alchemiser/strategy/interfaces/__init__.py` - Strategy interfaces layer
- `the_alchemiser/strategy/interfaces/event_wiring.py` - Event subscription wiring for Strategy context
- `the_alchemiser/strategy/interfaces/aws_lambda/__init__.py` - Lambda interface layer package
- `the_alchemiser/strategy/interfaces/aws_lambda/bootstrap.py` - Bootstrap helper for Strategy Lambda handlers
- `the_alchemiser/strategy/interfaces/aws_lambda/strategy_signal_handler.py` - AWS Lambda handler for scheduled signal generation

### Portfolio Context
**Business Unit**: portfolio assessment & management | **Status**: current

- `the_alchemiser/portfolio/__init__.py` - Portfolio context entry point
- `the_alchemiser/portfolio/domain/__init__.py` - Portfolio domain layer
- `the_alchemiser/portfolio/domain/exceptions.py` - Portfolio-specific exception classes
- `the_alchemiser/portfolio/domain/entities/__init__.py` - Portfolio domain entities package
- `the_alchemiser/portfolio/domain/entities/position.py` - Position entity for portfolio holdings
- `the_alchemiser/portfolio/domain/value_objects/__init__.py` - Portfolio domain value objects package
- `the_alchemiser/portfolio/domain/value_objects/portfolio_snapshot_vo.py` - Portfolio snapshot value object
- `the_alchemiser/portfolio/domain/utils/__init__.py` - Portfolio domain utilities package
- `the_alchemiser/portfolio/domain/utils/account_data_utils.py` - Account data utility functions
- `the_alchemiser/portfolio/application/__init__.py` - Portfolio application layer
- `the_alchemiser/portfolio/application/ports.py` - External dependency protocols (PositionRepositoryPort, PlanPublisherPort, ExecutionReportHandlerPort, PortfolioStateRepositoryPort)
- `the_alchemiser/portfolio/application/contracts/__init__.py` - Portfolio application contracts package
- `the_alchemiser/portfolio/application/contracts/_envelope.py` - Envelope mixin for consistent message metadata
- `the_alchemiser/portfolio/application/contracts/rebalance_plan_contract_v1.py` - Rebalance plan contract V1 for cross-context communication
- `the_alchemiser/portfolio/application/use_cases/account_operations.py` - Account operations use case
- `the_alchemiser/portfolio/application/use_cases/generate_plan.py` - Plan generation use case (handles signals)
- `the_alchemiser/portfolio/application/use_cases/update_portfolio.py` - Portfolio update use case (handles execution reports)
- `the_alchemiser/portfolio/infrastructure/__init__.py` - Portfolio infrastructure layer
- `the_alchemiser/portfolio/infrastructure/adapters/alpaca_account_adapter.py` - Alpaca account adapter
- `the_alchemiser/portfolio/infrastructure/adapters/event_bus_plan_publisher_adapter.py` - EventBus-based plan publisher adapter
- `the_alchemiser/portfolio/infrastructure/adapters/dynamodb_position_repository_adapter.py` - DynamoDB position repository adapter implementing PositionRepositoryPort protocol
- `the_alchemiser/portfolio/interfaces/__init__.py` - Portfolio interfaces layer
- `the_alchemiser/portfolio/interfaces/event_wiring.py` - Event subscription wiring for Portfolio context
- `the_alchemiser/portfolio/interfaces/aws_lambda/__init__.py` - Lambda interface layer package
- `the_alchemiser/portfolio/interfaces/aws_lambda/bootstrap.py` - Bootstrap helper for Portfolio Lambda handlers
- `the_alchemiser/portfolio/interfaces/aws_lambda/signal_consumer_handler.py` - AWS Lambda handler for consuming strategy signals
- `the_alchemiser/portfolio/interfaces/aws_lambda/execution_report_consumer_handler.py` - AWS Lambda handler for consuming execution reports

### Execution Context
**Business Unit**: order execution/placement | **Status**: current

- `the_alchemiser/execution/__init__.py` - Execution context entry point
- `the_alchemiser/execution/domain/__init__.py` - Execution domain layer
- `the_alchemiser/execution/domain/exceptions.py` - Execution-specific exception classes  
- `the_alchemiser/execution/application/__init__.py` - Execution application layer
- `the_alchemiser/execution/application/ports.py` - External dependency protocols (OrderRouterPort, PlanSubscriberPort, ExecutionReportPublisherPort, ExecutionMarketDataPort)
- `the_alchemiser/execution/application/contracts/__init__.py` - Execution application contracts package
- `the_alchemiser/execution/application/contracts/_envelope.py` - Envelope mixin for consistent message metadata
- `the_alchemiser/execution/application/contracts/execution_report_contract_v1.py` - Execution report contract V1 for cross-context communication
- `the_alchemiser/execution/application/use_cases/order_operations.py` - Order operations use case
- `the_alchemiser/execution/application/use_cases/execute_plan.py` - Plan execution use case (handles plans)
- `the_alchemiser/execution/application/use_cases/position_analysis.py` - Position analysis use case
- `the_alchemiser/execution/infrastructure/__init__.py` - Execution infrastructure layer
- `the_alchemiser/execution/infrastructure/adapters/alpaca_order_adapter.py` - Alpaca order adapter
- `the_alchemiser/execution/infrastructure/adapters/event_bus_execution_report_publisher_adapter.py` - EventBus-based execution report publisher adapter
- `the_alchemiser/execution/infrastructure/adapters/alpaca_order_router_adapter.py` - Alpaca order router adapter implementing OrderRouterPort protocol
- `the_alchemiser/execution/interfaces/__init__.py` - Execution interfaces layer
- `the_alchemiser/execution/interfaces/event_wiring.py` - Event subscription wiring for Execution context
- `the_alchemiser/execution/interfaces/aws_lambda/__init__.py` - Lambda interface layer package
- `the_alchemiser/execution/interfaces/aws_lambda/bootstrap.py` - Bootstrap helper for Execution Lambda handlers
- `the_alchemiser/execution/interfaces/aws_lambda/plan_consumer_handler.py` - AWS Lambda handler for consuming rebalance plans
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
- `the_alchemiser/anti_corruption/market_data/__init__.py` - Market data anti-corruption layer
- `the_alchemiser/anti_corruption/market_data/alpaca_to_domain.py` - Alpaca market data to domain object mapping
- `the_alchemiser/anti_corruption/serialization/__init__.py` - Serialization anti-corruption layer
- `the_alchemiser/anti_corruption/serialization/signal_serializer.py` - Signal contract serialization for messaging
- `the_alchemiser/anti_corruption/persistence/__init__.py` - Persistence anti-corruption layer
- `the_alchemiser/anti_corruption/persistence/position_mapper.py` - Position entity to DynamoDB item mapping
- `the_alchemiser/anti_corruption/brokers/__init__.py` - Broker anti-corruption layer
- `the_alchemiser/anti_corruption/brokers/alpaca_order_mapper.py` - Domain order to Alpaca API request mapping

### Interface Utilities (Added in Task 2 / PR #398)
**Business Unit**: utilities | **Status**: current

- `the_alchemiser/interfaces/utils/__init__.py` - Interface utilities package
- `the_alchemiser/interfaces/utils/serialization.py` - Boundary-safe serialization helpers

### Infrastructure Services Migration (Added in Task 3 / PR #XXX)
**Business Unit**: utilities | **Status**: current

- `the_alchemiser/infrastructure/error_handling/__init__.py` - Error handling infrastructure package
- `the_alchemiser/infrastructure/error_handling/exceptions.py` - Domain-specific exception classes
- `the_alchemiser/infrastructure/error_handling/decorators.py` - Exception translation decorators
- `the_alchemiser/infrastructure/error_handling/context.py` - Error context utilities
- `the_alchemiser/infrastructure/error_handling/handler.py` - Trading system error handler (migrated)
- `the_alchemiser/infrastructure/market_data/__init__.py` - Market data infrastructure package
- `the_alchemiser/infrastructure/market_data/market_data_service.py` - Enhanced market data service (migrated)
- `the_alchemiser/infrastructure/brokers/__init__.py` - Broker infrastructure package
- `the_alchemiser/infrastructure/brokers/alpaca_manager.py` - Alpaca broker manager (migrated)
- `the_alchemiser/infrastructure/dependency_injection/factory.py` - Service factory (migrated)

### Application Services Migration (Added in Task 3 / PR #XXX)
**Business Unit**: portfolio assessment & management, order execution/placement | **Status**: current

- `the_alchemiser/application/account/__init__.py` - Account services package
- `the_alchemiser/application/account/account_service.py` - Account management service (migrated)
- `the_alchemiser/application/account/account_utils.py` - Account utility functions (migrated)
- `the_alchemiser/application/trading/service_manager.py` - Trading service manager (migrated)
- `the_alchemiser/application/trading/order_service.py` - Order management service (migrated)
- `the_alchemiser/application/trading/position_service.py` - Position management service (migrated)

---

## Task 2 Migration (PR #398) – Retirement of `utils/` Module

Task 2 of Epic #375 removed the legacy monolithic `the_alchemiser/utils/` module. Responsibilities were redistributed to bounded contexts:

- `ActionType` enum → shared kernel types shim (`the_alchemiser/domain/shared_kernel/types.py`)
- Numeric helper `floats_equal` → shared kernel tooling (`the_alchemiser/domain/shared_kernel/tooling/num.py`)
- Serialization utilities → interface utilities (`the_alchemiser/interfaces/utils/serialization.py`)

All imports across impacted files were updated; no remaining references to the removed `utils` namespace exist.

## Task 3 Migration (PR #XXX) – Retirement of `services/` Module

Task 3 of Epic #375 migrated the legacy monolithic `the_alchemiser/services/` module. Responsibilities were redistributed to bounded contexts and infrastructure layers:

### Services Module Migration
- **Error Handling Services** (`services.errors.*`) → **Infrastructure Error Handling** (`infrastructure.error_handling.*`)
  - Exception classes moved to `infrastructure/error_handling/exceptions.py`
  - Translation decorators moved to `infrastructure/error_handling/decorators.py`
  - Error context utilities moved to `infrastructure/error_handling/context.py`
  
- **Trading Services** (`services.trading.*`) → **Application Trading Layer** (`application.trading.*`)
  - `TradingServiceManager` moved to `application/trading/service_manager.py`
  - `OrderService` and `PositionService` moved to `application/trading/`
  
- **Market Data Services** (`services.market_data.*`) → **Infrastructure Market Data** (`infrastructure.market_data.*`)
  - `MarketDataService` moved to `infrastructure/market_data/market_data_service.py`
  
- **Repository Services** (`services.repository.*`) → **Infrastructure Brokers** (`infrastructure.brokers.*`)
  - `AlpacaManager` moved to `infrastructure/brokers/alpaca_manager.py`
  
- **Account Services** (`services.account.*`) → **Application Account Layer** (`application.account.*`)
  - `AccountService` moved to `application/account/account_service.py`
  - `AccountUtils` moved to `application/account/account_utils.py`
  
- **Shared Services** (`services.shared.*`) → **Infrastructure Utilities**
  - `ServiceFactory` moved to `infrastructure/dependency_injection/factory.py`

### Consumer Updates Completed
- **Lambda Handler**: Updated error handling imports to use `infrastructure.error_handling`
- **Main Application**: Updated service factory and error handling imports  
- **CLI Interfaces**: Updated error handling and trading service manager imports
- **Application Layer**: Updated 70+ imports across execution, trading, and strategy contexts
- **Infrastructure Layer**: Updated dependency injection service providers

All critical imports updated; 21 remaining references to legacy services are marked as TODOs for future handler migration completion.

## Summary

- **Total new modules**: 47 new DDD bounded context modules (Task 1) + 4 migration utility modules (Task 2) + 18 services migration modules (Task 3) + 8 new port/protocol modules (Task 5) + 11 new infrastructure adapters and anti-corruption mappers (Task 6) + 15 new event-driven communication modules (Task 8)
- **Modules by business unit**:
  - utilities: 37 modules (shared_kernel + anti_corruption + interface utilities + tooling shim + cross-context eventing)
  - strategy & signal generation: 20 modules (strategy context with market data operations + ports + value objects + adapters + event wiring)
  - portfolio assessment & management: 17 modules (portfolio context with account operations + ports + entities + value objects + adapters + event wiring)
  - order execution/placement: 15 modules (execution context with trading operations + ports + adapters + event wiring)
- **All modules status**: current

**Note**: Task 5 (DDD Epic #375) completed implementation of explicit typed Protocol interfaces (ports) per bounded context's application layer to fully invert dependencies on external systems and cross-context abstractions. Task 6 (DDD Epic #375 Phase 6) completed implementation of concrete infrastructure adapters satisfying these port protocols, with anti-corruption layers for clean external system integration. Task 8 (DDD Epic #375 Phase 8) completed implementation of in-process event publishing & consumption using synchronous EventBus abstraction, enabling decoupled communication between bounded contexts with idempotency guarantees and correlation/causation tracking. This enables deterministic testing, side-effect isolation, clean adapter swapping, proper separation between domain logic and external system concerns, and complete elimination of direct cross-context coupling.
