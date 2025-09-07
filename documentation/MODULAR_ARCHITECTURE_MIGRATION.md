# Migration to Modular Architecture

## Overview

This migration transforms The Alchemiser from its current Domain-Driven Design (DDD) layered architecture to a clean four-module structure optimized for AI development and maintainability.

## Baseline Information

**Baseline Commit:** `13842739f83524852173460f7790ba90c178ea5e`  
**Baseline Branch:** `copilot/fix-443` (treating as main)  
**Baseline Date:** December 2024  
**Baseline Linting Status:** 679 errors (acceptable baseline state)

## Migration Strategy

The migration follows a phased approach to minimize risk and ensure system stability:

### Phase 0 - Preparation (Current)
- ✅ Create baseline branch and documentation
- ✅ Establish smoke tests for core functionality
- ✅ Document rollback procedures
- ✅ Create PR templates for migration work

### Phase 1 - Foundation Setup
- Create new modular directory structure (strategy/, portfolio/, execution/, shared/)
- Establish module boundaries and dependency rules
- Set up import linting to enforce architectural constraints

### Phase 2 - Content Migration
- Move existing code to appropriate modules
- Update imports and dependencies
- Maintain backward compatibility during transition

### Phase 3 - Cleanup & Optimization
- Remove legacy structures
- Optimize module interfaces
- Complete documentation updates

## Target Architecture

```
the_alchemiser/
├── strategy/           # Signal generation and indicators
│   ├── indicators/     # Technical indicators
│   ├── engines/        # Strategy implementations  
│   ├── signals/        # Signal processing
│   └── models/         # ML models
├── portfolio/          # Portfolio state and rebalancing
│   ├── positions/      # Position tracking
│   ├── rebalancing/    # Rebalancing algorithms
│   ├── valuation/      # Portfolio metrics
│   └── risk/           # Risk management
├── execution/          # Broker integrations and orders
│   ├── brokers/        # Broker API integrations
│   ├── orders/         # Order management
│   ├── strategies/     # Smart execution
│   └── routing/        # Order routing
└── shared/             # DTOs, utilities, cross-cutting
    ├── dtos/           # Data transfer objects
    ├── types/          # Common value objects
    ├── utils/          # Utility functions
    ├── config/         # Configuration
    └── logging/        # Logging setup
```

## Module Dependency Rules

✅ **Allowed Dependencies:**
- strategy/ → shared/
- portfolio/ → shared/  
- execution/ → shared/

❌ **Forbidden Dependencies:**
- strategy/ → portfolio/
- strategy/ → execution/
- portfolio/ → execution/
- shared/ → any other module

## Branch Policy

### Branch Naming Convention
- `migration/modular-split` - Main migration branch
- `migration/modular-split/phase-X-description` - Phase-specific work
- `migration/modular-split/module-name-migration` - Module-specific migrations

### PR Naming Convention
- `[Migration] Phase X: Description` - Phase-level PRs
- `[Migration] Module: strategy - Description` - Module-specific PRs
- `[Migration] Cleanup: Description` - Cleanup and optimization PRs

### Review Requirements
All migration PRs must include:
1. Smoke test results (scripts/smoke_tests.sh output)
2. MyPy type checking report
3. Architectural compliance verification
4. Impact assessment on existing functionality

## Rollback Strategy

See `migration/ROLLBACK.md` for detailed rollback procedures. At any point during the migration, the system can be reverted to the baseline state using documented commands.

## Success Criteria

- ✅ 100% MyPy compliance maintained
- ✅ All existing CLI functionality preserved
- ✅ Module dependency rules enforced
- ✅ No breaking changes to external interfaces
- ✅ Performance characteristics maintained or improved

## Testing Strategy

- **Smoke Tests:** Basic functionality verification (CLI + core flows)
- **Integration Tests:** Module boundary validation
- **Regression Tests:** Ensure no functionality loss
- **Performance Tests:** Verify no performance degradation

The migration prioritizes safety and incremental progress over speed, ensuring the system remains stable and functional throughout the transition.