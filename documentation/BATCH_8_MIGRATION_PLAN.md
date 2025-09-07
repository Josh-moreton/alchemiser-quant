# Phase 2 Migration - Batch 8 Plan

**Target Date**: January 2025  
**Batch Size**: 15 files (maintaining proven systematic approach)
**Priority**: MEDIUM to LOW - Mixed cleanup (shims + orphaned files)

## Files Selected for Migration

### execution/ business unit (4 files)
1. **trading_service_manager.py** (474 bytes) - Legacy shim → `execution/core/`
   - Source: `execution/services/trading_service_manager.py`
   - Target: DELETE (confirmed shim to execution_manager.py)
   - Action: REMOVE SHIM

2. **order_service.py** (~5KB) → `execution/services/` 
   - Source: `execution/services/order_service.py`
   - Target: `execution/services/order_service.py` (consolidate location)
   - Action: VERIFY + ALIGN

3. **position_manager_original.py** → `execution/services/`
   - Source: `execution/services/position_manager_original.py`
   - Target: DELETE or migrate to portfolio/ if needed

4. **account_service.py** (21KB) → `execution/services/`
   - Source: `execution/services/account_service.py`
   - Target: `execution/services/account_service.py` (verify placement)

### shared/ business unit (6 files) - Utilities & Error Handling
5. **error_recovery.py** (21KB) → `shared/utils/`
   - Source: `services/errors/error_recovery.py`
   - Target: `shared/utils/error_recovery.py`
   - Action: MIGRATE

6. **error_monitoring.py** (20KB) → `shared/utils/`
   - Source: `services/errors/error_monitoring.py`
   - Target: `shared/utils/error_monitoring.py`
   - Action: MIGRATE

7. **scope.py** → `shared/utils/`
   - Source: `services/errors/scope.py`
   - Target: `shared/utils/error_scope.py`
   - Action: MIGRATE

8. **retry_decorator.py** (3.6KB) → `shared/utils/`
   - Source: `services/shared/retry_decorator.py`
   - Target: `shared/utils/retry_decorator.py`
   - Action: MIGRATE

9. **secrets_service.py** → `shared/config/`
   - Source: `services/shared/secrets_service.py`
   - Target: `shared/config/secrets_service.py`
   - Action: MIGRATE

10. **cache_manager.py** → `shared/utils/`
    - Source: `services/shared/cache_manager.py`
    - Target: `shared/utils/cache_manager.py`
    - Action: MIGRATE

### portfolio/ business unit (2 files)
11. **position_manager.py** → `portfolio/positions/`
    - Source: `services/trading/position_manager.py`
    - Target: `portfolio/positions/legacy_position_manager.py`
    - Action: MIGRATE

12. **service_factory.py** → `shared/utils/`
    - Source: `services/shared/service_factory.py`
    - Target: `shared/utils/service_factory.py`
    - Action: MIGRATE

### shared/ business unit (3 files) - Configuration & CLI
13. **config_service.py** → `shared/config/`
    - Source: `services/shared/config_service.py`
    - Target: `shared/config/config_service.py`
    - Action: MIGRATE

14. **error_display_utils.py** → `shared/cli/`
    - Source: `interfaces/cli/error_display_utils.py`
    - Target: `shared/cli/error_display_utils.py`
    - Action: MIGRATE

15. **signal_display_utils.py** → `shared/cli/`
    - Source: `interfaces/cli/signal_display_utils.py`
    - Target: `shared/cli/signal_display_utils.py`
    - Action: MIGRATE

## Business Unit Alignment Strategy

**execution/**: Order services, account management, trading service management
**portfolio/**: Position tracking and management
**shared/**: Cross-cutting concerns (errors, utilities, CLI, configuration)

## Risk Assessment

**LOW RISK**: Most files appear to be utilities or have minimal imports
**SHIM CLEANUP**: Some files like trading_service_manager.py are just redirects
**SIZE RANGE**: 474 bytes - 21KB per file

## Migration Process

1. **Analyze Dependencies**: Check imports for each file
2. **Move Files**: Use git mv for each file to target location
3. **Update Imports**: Update any references to moved files
4. **Update Business Unit Docstrings**: Add proper module declarations
5. **Delete Shims**: Remove confirmed legacy shims
6. **Verify**: Test that migrations don't break functionality

## Expected Impact

- **Files migrated**: 15
- **Estimated imports to update**: 5-15 statements
- **Business units organized**: execution/, portfolio/, shared/
- **Legacy cleanup**: services/ and interfaces/ directories reduced

Ready for execution following proven 15-file batch methodology.