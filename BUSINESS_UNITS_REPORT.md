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

**Legacy execution module (deprecated):**
- `the_alchemiser/execution/README_DEPRECATED.md` - Deprecation notice and migration guide
- `the_alchemiser/execution/...` - Legacy execution files (see README_DEPRECATED.md)

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

**Legacy portfolio module (existing):**
- `the_alchemiser/portfolio/...` - Legacy portfolio files (to be deprecated after portfolio_v2 migration)

## Business Unit: strategy  

### Status: current

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