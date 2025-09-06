# Batch 12 Migration Plan

**Date**: January 2025  
**Batch Size**: 15 files  
**Priority**: MEDIUM/LOW priority files (continuing systematic cleanup)

## Files for Migration

| Priority | File | Target Location | Rationale | Imports | Size |
|----------|------|-----------------|-----------|---------|------|
| HIGH | `application/trading/bootstrap.py` | `shared/config/bootstrap.py` | Trading system bootstrap logic (3 active imports) | 13 | 253 |
| HIGH | `application/trading/account_facade.py` | `execution/core/account_facade.py` | Account operations for execution (1 active import) | 13 | 528 |
| HIGH | `application/trading/lifecycle/dispatcher.py` | `execution/lifecycle/dispatcher.py` | Order lifecycle dispatch (1 active import) | 6 | 137 |
| MEDIUM | `application/trading/portfolio_calculations.py` | `portfolio/calculations/portfolio_calculations.py` | Portfolio computation logic | 5 | 119 |
| MEDIUM | `application/trading/lifecycle/manager.py` | `execution/lifecycle/manager.py` | Lifecycle management for orders | 10 | 206 |
| MEDIUM | `application/trading/lifecycle/observers.py` | `execution/lifecycle/observers.py` | Order lifecycle observation | 10 | 517 |
| MEDIUM | `application/trading/ports.py` | `shared/interfaces/trading_ports.py` | Trading interface definitions | 9 | 125 |
| MEDIUM | `application/tracking/integration.py` | `portfolio/tracking/integration.py` | Portfolio tracking integration | 9 | 301 |
| MEDIUM | `application/reporting/reporting.py` | `shared/reporting/reporting.py` | Cross-cutting reporting utilities | 11 | 161 |
| MEDIUM | `domain/strategies_backup/engine.py` | `strategy/engines/legacy/backup_engine.py` | Legacy strategy engine backup | 9 | 218 |
| LOW | `services/market_data/__init__.py` | `shared/services/market_data_service.py` | Market data service interface | 3 | 16 |
| LOW | `services/__init__.py` | `shared/services/__init__.py` | Service module initialization | 1 | 32 |
| LOW | `domain/strategies_backup/strategy_manager.py` | `strategy/managers/legacy_strategy_manager.py` | Legacy strategy management | 1 | 3 |
| LOW | `domain/strategies_backup/errors/strategy_errors.py` | `strategy/errors/strategy_errors.py` | Strategy-specific error handling | 1 | 41 |
| LOW | `domain/strategies_backup/nuclear_logic.py` | `strategy/engines/legacy/nuclear_logic.py` | Legacy nuclear strategy logic | 2 | 190 |

## Migration Strategy

### Phase 1: High Priority (3 files)
1. **bootstrap.py** → `shared/config/` (system configuration)
2. **account_facade.py** → `execution/core/` (account operations)  
3. **dispatcher.py** → `execution/lifecycle/` (order dispatch)

### Phase 2: Medium Priority (7 files)
4. **portfolio_calculations.py** → `portfolio/calculations/`
5. **manager.py** → `execution/lifecycle/`
6. **observers.py** → `execution/lifecycle/`  
7. **ports.py** → `shared/interfaces/`
8. **integration.py** → `portfolio/tracking/`
9. **reporting.py** → `shared/reporting/`
10. **engine.py** → `strategy/engines/legacy/`

### Phase 3: Low Priority (5 files)
11. **market_data/__init__.py** → `shared/services/`
12. **services/__init__.py** → `shared/services/`
13. **strategy_manager.py** → `strategy/managers/`
14. **strategy_errors.py** → `strategy/errors/`
15. **nuclear_logic.py** → `strategy/engines/legacy/`

## Business Unit Alignment

- **execution/**: 4 files (account, lifecycle components)
- **portfolio/**: 2 files (calculations, tracking)
- **strategy/**: 4 files (legacy engines, management, errors)
- **shared/**: 5 files (config, interfaces, services, reporting)

## Expected Import Updates

Based on analysis, approximately 8-12 import statements will need updates across:
- CLI components referencing bootstrap
- Trading components using account facade
- Order management using dispatcher
- Portfolio calculation consumers

## Success Criteria

1. All 15 files successfully moved to target locations
2. Import statements updated with zero syntax errors
3. Proper business unit boundaries maintained
4. Documentation updated to reflect progress
5. Health checks pass throughout migration