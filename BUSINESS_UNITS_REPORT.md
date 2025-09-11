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
- Strategy module files (to be documented)

## Business Unit: shared

### Status: current
- Shared module files (to be documented)

---

**Note**: This report should be updated when adding/removing files to maintain consistency with the modular architecture. New execution_v2 module follows strict DTO consumption principles and clean module boundaries.