# Batch 11 Migration Plan

**Generated**: January 2025  
**Target**: 15 files migration with systematic business unit alignment  
**Focus**: Medium/high priority application services and domain logic  

## Batch 11 Target Files

### Application Layer Services (8 files)
1. `application/policies/buying_power_policy_impl.py` → `portfolio/policies/buying_power_policy_impl.py`
2. `application/policies/fractionability_policy_impl.py` → `portfolio/policies/fractionability_policy_impl.py`
3. `application/policies/position_policy_impl.py` → `portfolio/policies/position_policy_impl.py`
4. `application/policies/risk_policy_impl.py` → `portfolio/policies/risk_policy_impl.py`
5. `application/policies/policy_factory.py` → `portfolio/policies/policy_factory.py`
6. `application/portfolio/services/portfolio_management_facade.py` → `portfolio/core/portfolio_management_facade.py`
7. `application/portfolio/rebalancing_orchestrator_facade.py` → `portfolio/rebalancing/orchestrator_facade.py`
8. `application/mapping/models/position.py` → `portfolio/mappers/position.py`

### Domain Layer Components (4 files)
9. `domain/shared_kernel/types.py` → `shared/types/shared_kernel_types.py`
10. `domain/shared_kernel/value_objects/identifier.py` → `shared/value_objects/identifier.py`
11. `domain/interfaces/account_repository.py` → `shared/interfaces/account_repository.py`
12. `domain/interfaces/market_data_repository.py` → `shared/interfaces/market_data_repository.py`

### Infrastructure Services (3 files)
13. `infrastructure/dependency_injection/application_container.py` → `shared/config/application_container.py`
14. `infrastructure/dependency_injection/config_providers.py` → `shared/config/config_providers.py`
15. `infrastructure/dependency_injection/service_providers.py` → `shared/config/service_providers.py`

## Import Impact Analysis

### High Priority Import Updates Required:
- **policy implementations**: 8 imports in policy_orchestrator.py + policy_factory.py
- **portfolio facades**: 2 imports in trading_engine.py  
- **position mapping**: 0 imports (safe migration)
- **shared kernel**: Potentially high impact due to core types

### Migration Strategy
1. Start with policy implementations (highest active import impact)
2. Move portfolio facade files (critical for trading engine)
3. Migrate domain interfaces and shared types
4. Finish with dependency injection infrastructure

## Business Unit Alignment
- **portfolio/**: Policy implementations, facades, position mapping ✅
- **shared/**: Domain interfaces, shared kernel types, DI containers ✅
- Conservative placement following modular architecture guidelines

## Estimated Effort
- **Import statements to update**: ~12-15
- **Files to validate**: 15 core files + dependent files
- **Business unit validation**: All modules properly aligned