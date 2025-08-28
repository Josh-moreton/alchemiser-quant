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

### Strategy Context
**Business Unit**: strategy & signal generation | **Status**: current

- `the_alchemiser/strategy/__init__.py` - Strategy context entry point
- `the_alchemiser/strategy/domain/__init__.py` - Strategy domain layer
- `the_alchemiser/strategy/application/__init__.py` - Strategy application layer
- `the_alchemiser/strategy/infrastructure/__init__.py` - Strategy infrastructure layer
- `the_alchemiser/strategy/interfaces/__init__.py` - Strategy interfaces layer

### Portfolio Context  
**Business Unit**: portfolio assessment & management | **Status**: current

- `the_alchemiser/portfolio/__init__.py` - Portfolio context entry point
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

---

## Summary

- **Total new modules**: 25 new DDD bounded context modules
- **Modules by business unit**:
  - utilities: 15 modules (shared_kernel + anti_corruption contexts)
  - strategy & signal generation: 5 modules (strategy context)
  - portfolio assessment & management: 5 modules (portfolio context)  
  - order execution/placement: 5 modules (execution context)
- **All modules status**: current

**Note**: This report shows only the new DDD bounded context structure created in Task 1 of Epic #375. Additional existing modules will be documented as they are migrated to the new structure in subsequent tasks.