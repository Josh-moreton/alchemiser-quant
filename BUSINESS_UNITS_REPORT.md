# Business Units Report

This document tracks all modules in the Alchemiser trading system organized by business unit and status.

## Business Units

### Strategy & Signal Generation
- **Status**: current
- **Description**: Handles strategy execution, signal generation, and strategy-specific business logic

#### New Bounded Context Structure
- `strategy/domain/` - Strategy domain models and business rules
- `strategy/application/` - Strategy orchestration and use cases  
- `strategy/infrastructure/` - External strategy data providers and adapters
- `strategy/interfaces/` - Strategy CLI commands and DTOs

### Portfolio Assessment & Management  
- **Status**: current
- **Description**: Handles portfolio management, rebalancing, and portfolio-specific business logic

#### New Bounded Context Structure
- `portfolio/domain/` - Portfolio domain models and business rules
- `portfolio/application/` - Portfolio orchestration and use cases
- `portfolio/infrastructure/` - External portfolio data providers and adapters
- `portfolio/interfaces/` - Portfolio CLI commands and DTOs

### Order Execution/Placement
- **Status**: current  
- **Description**: Handles order execution, placement, and execution-specific business logic

#### New Bounded Context Structure
- `execution/domain/` - Execution domain models and business rules
- `execution/application/` - Execution orchestration and use cases
- `execution/infrastructure/` - External execution data providers and adapters
- `execution/interfaces/` - Execution CLI commands and DTOs

### Utilities
- **Status**: current
- **Description**: Cross-cutting concerns and shared infrastructure

#### Shared Kernel
- `shared_kernel/value_objects/` - Cross-context value objects
  - `identifier.py` - Universal identifier value object
  - `money.py` - Financial amount value object  
  - `percentage.py` - Percentage value object
  - `symbol.py` - Trading symbol value object

#### Anti-Corruption Layer
- `anti_corruption/domain/` - Anti-corruption domain contracts
- `anti_corruption/application/` - Translation orchestration
- `anti_corruption/infrastructure/` - External system adapters
- `anti_corruption/interfaces/` - Anti-corruption DTOs

## Migration Status

### Completed (Phase 1)
- [x] Created bounded context directory structures
- [x] Moved shared kernel value objects to top-level `shared_kernel/`
- [x] Updated all import statements (26 files updated)
- [x] Verified mypy compliance maintained
- [x] Verified CLI functionality maintained

### Future Phases
- [ ] Move strategy-specific code to `strategy/` bounded context
- [ ] Move portfolio-specific code to `portfolio/` bounded context  
- [ ] Move execution-specific code to `execution/` bounded context
- [ ] Implement anti-corruption mappers in `anti_corruption/`
- [ ] Refactor services layer to align with bounded contexts

## Notes

- All new bounded context packages are properly documented with business unit and status
- Shared kernel maintains framework-agnostic design
- Import paths updated from `the_alchemiser.domain.shared_kernel.value_objects.*` to `shared_kernel.value_objects.*`
- No functional changes introduced - purely structural reorganization