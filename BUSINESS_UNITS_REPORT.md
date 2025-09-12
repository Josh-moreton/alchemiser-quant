# Business Units Report

This document tracks files by business unit as defined in the modular architecture.

## Business Unit: execution

### Status: current

**New execution_v2 module (recommended):**
- `the_alchemiser/execution_v2/__init__.py` - Main module exports
- `the_alchemiser/execution_v2/core/__init__.py` - Core components exports  
- `the_alchemiser/execution_v2/core/execution_manager.py` - Simple execution manager with factory
- `the_alchemiser/execution_v2/core/simple_executor.py` - Core DTO-driven executor
- `the_alchemiser/execution_v2/core/execution_tracker.py` - Execution logging and monitoring
- `the_alchemiser/execution_v2/models/__init__.py` - Models exports
- `the_alchemiser/execution_v2/models/execution_result.py` - Execution result DTOs

**Legacy execution module:** ✅ **REMOVED** - Deprecated module completely deleted

## Business Unit: portfolio

### Status: current

**New portfolio_v2 module (recommended):**
- `the_alchemiser/portfolio_v2/__init__.py` - Main module exports (PortfolioServiceV2, RebalancePlanCalculator)
- `the_alchemiser/portfolio_v2/core/__init__.py` - Core components exports
- `the_alchemiser/portfolio_v2/core/portfolio_service.py` - Main orchestration facade for rebalance plans
- `the_alchemiser/portfolio_v2/core/planner.py` - Core rebalance plan calculator
- `the_alchemiser/portfolio_v2/core/state_reader.py` - Portfolio state snapshot builder
- `the_alchemiser/portfolio_v2/adapters/__init__.py` - Adapters exports
- `the_alchemiser/portfolio_v2/adapters/alpaca_data_adapter.py` - Data access via shared AlpacaManager
- `the_alchemiser/portfolio_v2/models/__init__.py` - Models exports
- `the_alchemiser/portfolio_v2/models/portfolio_snapshot.py` - Immutable portfolio state snapshot
- `the_alchemiser/portfolio_v2/models/sizing_policy.py` - Trade sizing and rounding policies

**Shared DTOs (added for portfolio_v2):**
- `the_alchemiser/shared/dto/strategy_allocation_dto.py` - Strategy allocation DTO for portfolio input

**Shared exceptions (updated for portfolio_v2):**
- `the_alchemiser/shared/types/exceptions.py` - Added PortfolioError for portfolio_v2 error handling

**Legacy portfolio module:** ✅ **REMOVED** - Deprecated module completely deleted

## Business Unit: strategy  

### Status: current

**New strategy_v2 module (recommended):**
- `the_alchemiser/strategy_v2/__init__.py` - Main module exports
- `the_alchemiser/strategy_v2/core/__init__.py` - Core components exports
- `the_alchemiser/strategy_v2/core/orchestrator.py` - Strategy orchestrator for running engines
- `the_alchemiser/strategy_v2/core/registry.py` - Strategy registry for mapping strategy names
- `the_alchemiser/strategy_v2/engines/__init__.py` - Engines exports
- `the_alchemiser/strategy_v2/engines/engine.py` - Strategy engine protocol and base types
- `the_alchemiser/strategy_v2/engines/value_objects.py` - Strategy value objects (Confidence, StrategySignal)
- `the_alchemiser/strategy_v2/engines/errors.py` - Strategy error types
- `the_alchemiser/strategy_v2/engines/nuclear/engine.py` - Nuclear strategy engine implementation
- `the_alchemiser/strategy_v2/engines/klm/engine.py` - KLM strategy engine implementation  
- `the_alchemiser/strategy_v2/engines/tecl/engine.py` - TECL strategy engine implementation
- `the_alchemiser/strategy_v2/indicators/__init__.py` - Indicators exports
- `the_alchemiser/strategy_v2/indicators/indicators.py` - Technical indicators implementation
- `the_alchemiser/strategy_v2/indicators/indicator_utils.py` - Indicator utility functions
- `the_alchemiser/strategy_v2/adapters/__init__.py` - Adapters exports
- `the_alchemiser/strategy_v2/adapters/market_data_adapter.py` - Market data adapter for strategy execution
- `the_alchemiser/strategy_v2/models/__init__.py` - Models exports
- `the_alchemiser/strategy_v2/models/context.py` - Strategy execution context

**Legacy strategy module:** ✅ **REMOVED** - Deprecated module completely deleted

## Business Unit: shared

### Status: current

**Orchestration (NEW):**
- `the_alchemiser/shared/orchestration/__init__.py` - Main orchestration exports
- `the_alchemiser/shared/orchestration/signal_orchestrator.py` - Signal analysis workflow orchestration
- `the_alchemiser/shared/orchestration/trading_orchestrator.py` - Trading execution workflow orchestration
- `the_alchemiser/shared/orchestration/strategy_orchestrator.py` - Multi-strategy coordination and conflict resolution
- `the_alchemiser/shared/orchestration/portfolio_orchestrator.py` - Portfolio rebalancing workflow orchestration

**CLI (UPDATED):**
- `the_alchemiser/shared/cli/cli.py` - Main CLI entry point (thin wrapper using orchestration)
- `the_alchemiser/shared/cli/signal_analyzer.py` - Signal analysis CLI (thin wrapper)
- `the_alchemiser/shared/cli/trading_executor.py` - Trading execution CLI (thin wrapper)
- `the_alchemiser/shared/cli/cli_formatter.py` - CLI display formatting utilities
- `the_alchemiser/shared/cli/dashboard_utils.py` - Dashboard utilities

**Types (UPDATED):**
- `the_alchemiser/shared/types/strategy_types.py` - Strategy type enumeration for orchestration
- `the_alchemiser/shared/types/strategy_registry.py` - Strategy registry bridge for migration
- `the_alchemiser/shared/types/exceptions.py` - Shared exception types
- `the_alchemiser/shared/types/market_data_port.py` - Market data port protocol
- `the_alchemiser/shared/types/percentage.py` - Percentage value object
- `the_alchemiser/shared/types/quote.py` - Quote data models

**Configuration:**
- `the_alchemiser/shared/config/config.py` - Application configuration management
- `the_alchemiser/shared/config/container.py` - Dependency injection container
- `the_alchemiser/shared/config/bootstrap.py` - Application bootstrap logic
- `the_alchemiser/shared/config/confidence_config.py` - Strategy confidence configuration
- `the_alchemiser/shared/config/service_providers.py` - Service provider configuration
- `the_alchemiser/shared/config/infrastructure_providers.py` - Infrastructure provider configuration

**Utilities:**
- `the_alchemiser/shared/utils/strategy_utils.py` - Strategy utility functions
- `the_alchemiser/shared/utils/common.py` - Common utility functions
- `the_alchemiser/shared/value_objects/symbol.py` - Symbol value object
- `the_alchemiser/shared/logging/logging_utils.py` - Logging utilities (S3 handler removed)
- `the_alchemiser/shared/errors/error_handler.py` - Error handling utilities
- `the_alchemiser/shared/notifications/email_utils.py` - Email notification utilities
- `the_alchemiser/shared/notifications/templates/` - Email templates
- `the_alchemiser/shared/math/math_utils.py` - Mathematical utility functions
- `the_alchemiser/shared/brokers/alpaca_manager.py` - Alpaca broker integration manager

## Architecture Summary

The new architecture follows a clean modular design:

### Business Units (Core Domain Logic)
- **strategy_v2/**: Signal generation, indicators, ML models, regime detection
- **portfolio_v2/**: Portfolio state management, sizing, rebalancing logic, risk management  
- **execution_v2/**: Broker API integrations, order placement, smart execution, error handling

### Cross-Module Coordination
- **shared/orchestration/**: Workflow orchestration that coordinates between business units
  - SignalOrchestrator: Signal analysis workflow
  - TradingOrchestrator: Trading execution workflow
  - StrategyOrchestrator: Multi-strategy coordination
  - PortfolioOrchestrator: Portfolio rebalancing workflow

### Shared Infrastructure
- **shared/**: DTOs, utilities, logging, cross-cutting concerns, common value objects

### User Interface
- **shared/cli/**: Thin CLI wrappers that delegate to orchestration layer

## Migration Status: ✅ COMPLETE

- ✅ Deprecated modules `/strategy`, `/portfolio`, `/execution` completely removed
- ✅ New orchestration layer created in `/shared/orchestration/`
- ✅ CLI updated to thin wrappers using orchestration
- ✅ All business logic migrated to `_v2` modules or orchestration layer
- ✅ No legacy fallback patterns - migration path is explicit

The system now follows clean separation of concerns with proper module boundaries and no circular dependencies.

**New strategy_v2 module (recommended):**
- `the_alchemiser/strategy_v2/__init__.py` - Main module exports (StrategyOrchestrator, StrategyContext)
- `the_alchemiser/strategy_v2/core/__init__.py` - Core components exports
- `the_alchemiser/strategy_v2/core/orchestrator.py` - Strategy orchestration and DTO mapping
- `the_alchemiser/strategy_v2/core/registry.py` - Strategy engine registry
- `the_alchemiser/strategy_v2/core/factory.py` - Factory functions for orchestrator setup
- `the_alchemiser/strategy_v2/adapters/__init__.py` - Adapters exports
- `the_alchemiser/strategy_v2/adapters/market_data_adapter.py` - Market data adapter wrapping AlpacaManager
- `the_alchemiser/strategy_v2/adapters/feature_pipeline.py` - Feature computation with float tolerance handling
- `the_alchemiser/strategy_v2/models/__init__.py` - Models exports
- `the_alchemiser/strategy_v2/models/context.py` - Immutable strategy execution context
- `the_alchemiser/strategy_v2/engines/` - Strategy engines moved from legacy (Nuclear, KLM, TECL)
- `the_alchemiser/strategy_v2/indicators/` - Technical indicators moved from legacy
- `the_alchemiser/strategy_v2/errors.py` - Typed error classes with module context
- `the_alchemiser/strategy_v2/README.md` - Module documentation and usage

**Legacy strategy module (deprecated):**
- `the_alchemiser/strategy/README_DEPRECATED.md` - Deprecation notice and migration guide
- `the_alchemiser/strategy/engines/nuclear/__init__.py` - Compatibility shim for Nuclear engine
- `the_alchemiser/strategy/engines/klm/__init__.py` - Compatibility shim for KLM engine
- `the_alchemiser/strategy/engines/tecl/__init__.py` - Compatibility shim for TECL engine
- `the_alchemiser/strategy/indicators/__init__.py` - Compatibility shim for indicators
- `the_alchemiser/strategy/...` - Other legacy strategy files (see README_DEPRECATED.md)

## Business Unit: shared

### Status: current
- Shared module files (to be documented)

---

**Note**: This report should be updated when adding/removing files to maintain consistency with the modular architecture. New execution_v2 module follows strict DTO consumption principles and clean module boundaries.