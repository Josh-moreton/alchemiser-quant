# Business Units Report

This document provides an inventory of all modules in the Alchemiser system, categorized by business unit and status.

## Business Unit Classifications

Every module is classified under one of these business units:
- **strategy & signal generation**: Strategy engines, signal computation, technical analysis, and market data acquisition
- **portfolio assessment & management**: Portfolio rebalancing, position management, account management, and risk assessment  
- **order execution/placement**: Order routing, execution algorithms, trade settlement, and order lifecycle management
- **utilities**: Cross-cutting concerns, shared infrastructure, and support functions

## Status Classifications
- **current**: Actively maintained, follows current architecture patterns
- **legacy**: Older code that may need refactoring or migration

---

## DDD Bounded Contexts (Current Structure)

### Shared Kernel Context
**Business Unit**: utilities | **Status**: current

- `the_alchemiser/shared_kernel/__init__.py` - Shared kernel entry point
- `the_alchemiser/shared_kernel/errors.py` - Base exceptions and ubiquitous error types
- `the_alchemiser/shared_kernel/value_objects/__init__.py` - Value objects package
- `the_alchemiser/shared_kernel/value_objects/money.py` - Money value object
- `the_alchemiser/shared_kernel/value_objects/percentage.py` - Percentage value object
- `the_alchemiser/shared_kernel/value_objects/identifier.py` - Identifier value object
- `the_alchemiser/shared_kernel/value_objects/symbol.py` - Symbol value object
- `the_alchemiser/domain/shared_kernel/types.py` - Backwards compatibility shim (ActionType enum & value object re-exports)
- `the_alchemiser/domain/shared_kernel/tooling/num.py` - Float tolerance comparison utility (`floats_equal`)

### Strategy Context
**Business Unit**: strategy & signal generation | **Status**: current

#### Domain Layer
- `the_alchemiser/strategy/__init__.py` - Strategy context entry point
- `the_alchemiser/strategy/domain/__init__.py` - Strategy domain layer
- `the_alchemiser/strategy/domain/errors.py` - Strategy-specific domain errors

#### Application Layer
- `the_alchemiser/strategy/application/__init__.py` - Strategy application layer
- `the_alchemiser/strategy/application/strategy_application.py` - Strategy application service
- `the_alchemiser/strategy/application/engine_service.py` - Multi-strategy trading engine orchestration
- `the_alchemiser/strategy/application/bootstrap.py` - Trading engine dependency injection bootstrap
- `the_alchemiser/strategy/application/ports.py` - Application-layer protocol interfaces
- `the_alchemiser/strategy/application/mapping/strategies.py` - Strategy DTO mapping
- `the_alchemiser/strategy/application/mapping/strategy_domain_mapping.py` - Strategy domain mapping
- `the_alchemiser/strategy/application/mapping/strategy_market_data_adapter.py` - Market data adapter
- `the_alchemiser/strategy/application/mapping/strategy_signal_mapping.py` - Signal mapping
- `the_alchemiser/strategy/application/mapping/market_data_mappers.py` - Market data mappers
- `the_alchemiser/strategy/application/mapping/market_data_mapping.py` - Market data mapping

#### Infrastructure Layer
- `the_alchemiser/strategy/infrastructure/__init__.py` - Strategy infrastructure layer
- `the_alchemiser/strategy/infrastructure/market_data_service.py` - Market data service for strategies
- `the_alchemiser/strategy/infrastructure/price_service.py` - Price data service
- `the_alchemiser/strategy/infrastructure/strategy_market_data_service.py` - Strategy-specific market data

#### Interfaces Layer
- `the_alchemiser/strategy/interfaces/__init__.py` - Strategy interfaces layer

### Portfolio Context
**Business Unit**: portfolio assessment & management | **Status**: current

#### Domain Layer
- `the_alchemiser/portfolio/__init__.py` - Portfolio context entry point
- `the_alchemiser/portfolio/domain/__init__.py` - Portfolio domain layer
- `the_alchemiser/portfolio/domain/errors.py` - Portfolio-specific domain errors

#### Application Layer
- `the_alchemiser/portfolio/application/__init__.py` - Portfolio application layer
- `the_alchemiser/portfolio/application/portfolio_application.py` - Portfolio application service
- `the_alchemiser/portfolio/application/account_facade.py` - Account operations facade
- `the_alchemiser/portfolio/application/account_service.py` - Account management service
- `the_alchemiser/portfolio/application/account_utils.py` - Account utility functions
- `the_alchemiser/portfolio/application/portfolio_calculations.py` - Portfolio calculation logic
- `the_alchemiser/portfolio/application/portfolio_pnl_utils.py` - P&L calculation utilities
- `the_alchemiser/portfolio/application/buying_power_policy_impl.py` - Buying power policy implementation
- `the_alchemiser/portfolio/application/position_policy_impl.py` - Position validation policy
- `the_alchemiser/portfolio/application/risk_policy_impl.py` - Risk management policy
- `the_alchemiser/portfolio/application/fractionability_policy_impl.py` - Fractional shares policy
- `the_alchemiser/portfolio/application/policy_factory.py` - Policy factory
- `the_alchemiser/portfolio/application/policy_orchestrator.py` - Policy orchestration
- `the_alchemiser/portfolio/application/rebalancing_orchestrator.py` - Portfolio rebalancing orchestrator
- `the_alchemiser/portfolio/application/rebalancing_orchestrator_facade.py` - Rebalancing facade
- `the_alchemiser/portfolio/application/mapping/account_mapping.py` - Account DTO mapping
- `the_alchemiser/portfolio/application/mapping/position_mapping.py` - Position DTO mapping
- `the_alchemiser/portfolio/application/mapping/portfolio_rebalancing_mapping.py` - Rebalancing mapping
- `the_alchemiser/portfolio/application/mapping/policy_mapping.py` - Policy mapping
- `the_alchemiser/portfolio/application/services/portfolio_analysis_service.py` - Portfolio analysis
- `the_alchemiser/portfolio/application/services/portfolio_management_facade.py` - Portfolio management facade
- `the_alchemiser/portfolio/application/services/portfolio_rebalancing_service.py` - Rebalancing service
- `the_alchemiser/portfolio/application/services/rebalance_execution_service.py` - Rebalance execution

#### Infrastructure Layer
- `the_alchemiser/portfolio/infrastructure/__init__.py` - Portfolio infrastructure layer

#### Interfaces Layer
- `the_alchemiser/portfolio/interfaces/__init__.py` - Portfolio interfaces layer

### Execution Context
**Business Unit**: order execution/placement | **Status**: current

#### Domain Layer
- `the_alchemiser/execution/__init__.py` - Execution context entry point
- `the_alchemiser/execution/domain/__init__.py` - Execution domain layer
- `the_alchemiser/execution/domain/errors.py` - Execution-specific domain errors

#### Application Layer
- `the_alchemiser/execution/application/__init__.py` - Execution application layer
- `the_alchemiser/execution/application/execution_application.py` - Execution application service
- `the_alchemiser/execution/application/order_service.py` - Enhanced order placement service
- `the_alchemiser/execution/application/position_service.py` - Position monitoring service
- `the_alchemiser/execution/application/position_manager.py` - Position management
- `the_alchemiser/execution/application/order_validation.py` - Order validation service
- `the_alchemiser/execution/application/order_validation_utils.py` - Order validation utilities
- `the_alchemiser/execution/application/asset_order_handler.py` - Asset-specific order handling
- `the_alchemiser/execution/application/progressive_order_utils.py` - Progressive order utilities
- `the_alchemiser/execution/application/smart_execution.py` - Smart execution engine
- `the_alchemiser/execution/application/smart_pricing_handler.py` - Smart pricing logic
- `the_alchemiser/execution/application/spread_assessment.py` - Spread analysis
- `the_alchemiser/execution/application/execution_manager.py` - Execution management
- `the_alchemiser/execution/application/canonical_executor.py` - Canonical order executor
- `the_alchemiser/execution/application/canonical_integration_example.py` - Integration example
- `the_alchemiser/execution/application/order_request_builder.py` - Order request builder
- `the_alchemiser/execution/application/order_lifecycle_adapter.py` - Order lifecycle adapter
- `the_alchemiser/execution/application/dispatcher.py` - Lifecycle event dispatcher
- `the_alchemiser/execution/application/manager.py` - Order lifecycle manager
- `the_alchemiser/execution/application/observers.py` - Lifecycle observers
- `the_alchemiser/execution/application/trading_service_manager.py` - Legacy trading service manager (to be removed)
- `the_alchemiser/execution/application/mapping/order_mapping.py` - Order DTO mapping
- `the_alchemiser/execution/application/mapping/orders.py` - Order mapping utilities
- `the_alchemiser/execution/application/mapping/execution.py` - Execution mapping
- `the_alchemiser/execution/application/mapping/execution_summary_mapping.py` - Execution summary mapping
- `the_alchemiser/execution/application/mapping/alpaca_dto_mapping.py` - Alpaca DTO mapping
- `the_alchemiser/execution/application/strategies/aggressive_limit_strategy.py` - Aggressive limit strategy
- `the_alchemiser/execution/application/strategies/repeg_strategy.py` - Re-pegging strategy
- `the_alchemiser/execution/application/strategies/execution_context_adapter.py` - Execution context adapter
- `the_alchemiser/execution/application/strategies/config.py` - Strategy configuration

#### Infrastructure Layer
- `the_alchemiser/execution/infrastructure/__init__.py` - Execution infrastructure layer
- `the_alchemiser/execution/infrastructure/alpaca_client.py` - Alpaca trading client

#### Interfaces Layer
- `the_alchemiser/execution/interfaces/__init__.py` - Execution interfaces layer

---

## Cross-Cutting Concerns (Interfaces Layer)
**Business Unit**: utilities | **Status**: current

### CLI and User Interfaces
- `the_alchemiser/interfaces/cli/cli.py` - Main CLI application
- `the_alchemiser/interfaces/cli/signal_analyzer.py` - Signal analysis CLI
- `the_alchemiser/interfaces/cli/trading_executor.py` - Trading execution CLI
- `the_alchemiser/interfaces/cli/cli_formatter.py` - CLI output formatting
- `the_alchemiser/interfaces/cli/portfolio_calculations.py` - Portfolio CLI calculations

### System Coordination
- `the_alchemiser/interfaces/trading_system_coordinator.py` - DDD-compliant trading system coordinator

### Tracking and Reporting
- `the_alchemiser/interfaces/reporting.py` - Reporting functionality
- `the_alchemiser/interfaces/strategy_order_tracker.py` - Strategy order tracking
- `the_alchemiser/interfaces/tracking.py` - General tracking utilities
- `the_alchemiser/interfaces/tracking_mapping.py` - Tracking DTO mapping
- `the_alchemiser/interfaces/tracking_normalization.py` - Tracking data normalization
- `the_alchemiser/interfaces/integration.py` - System integration utilities

### Cross-Context Mappings
- `the_alchemiser/interfaces/trading_service_dto_mapping.py` - Cross-context DTO mapping
- `the_alchemiser/interfaces/pandas_time_series.py` - Time series mapping
- `the_alchemiser/interfaces/models/order.py` - Order interface models
- `the_alchemiser/interfaces/models/position.py` - Position interface models

### Schemas and DTOs
- `the_alchemiser/interfaces/schemas/` - All DTO definitions and interface contracts

---

## Legacy Application Structure (To Be Removed)
**Business Unit**: utilities | **Status**: legacy

The following directories contain legacy code that has been migrated to bounded contexts but not yet removed:

- `the_alchemiser/application/` - Legacy application layer (migrated to bounded contexts)
- `the_alchemiser/domain/` - Legacy domain layer (partially migrated)
- `the_alchemiser/infrastructure/` - Infrastructure layer (still contains shared infrastructure)

---

## Summary

- **Total bounded context modules**: 150+ modules across 3 bounded contexts
- **Modules by business unit**:
  - strategy & signal generation: 25+ modules (strategy context + market data infrastructure)
  - portfolio assessment & management: 35+ modules (portfolio context + account management)
  - order execution/placement: 45+ modules (execution context + order management)
  - utilities: 40+ modules (shared kernel + interfaces + cross-cutting concerns)
- **All new modules status**: current
- **Architecture**: Proper DDD bounded contexts with clean separation of concerns

**Migration Status**: Epic #375 successfully completed. The monolithic services/ directory has been fully migrated into proper DDD bounded contexts (strategy, portfolio, execution) with clean separation of domain, application, infrastructure, and interface layers. The legacy TradingServiceManager god-object has been decomposed into three focused application services that respect bounded context boundaries.