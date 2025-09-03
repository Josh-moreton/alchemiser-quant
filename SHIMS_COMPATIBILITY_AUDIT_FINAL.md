# Shims & Compatibility Layers Audit Report

## Executive Summary

This report identifies **38 confirmed shims and compatibility layers** in the codebase that require attention. This focused audit only includes files that are definitively shims, import redirections, or legacy compatibility code.

**Risk Distribution:**
- 🔴 **High Risk**: 21 items (explicit legacy code, deprecation warnings)
- 🟡 **Medium Risk**: 15 items (import redirections)
- 🟢 **Low Risk**: 2 items (backup files)

**Active Usage**: 16 shims are actively imported by other files

## Detailed Findings

### 🔴 HIGH RISK (21 items)

**1. symbol_legacy.py** **[7 imports]**
- **File**: `the_alchemiser/shared/types/symbol_legacy.py`
- **Description**: File explicitly named with 'legacy' keyword
- **Purpose**: File explicitly indicating legacy status
- **Suggested Action**: review_for_migration
- **Evidence**: Filename contains 'legacy'; Actively imported by 7 files

**2. canonical_executor.py** **[6 imports]**
- **File**: `the_alchemiser/execution/core/canonical_executor.py`
- **Description**: Explicitly marked with 'Status: legacy'
- **Purpose**: Module explicitly marked as legacy
- **Suggested Action**: review_for_migration
- **Evidence**: """Business Unit: execution; Status: legacy.; Actively imported by 6 files

**3. rebalance_plan.py** **[2 imports]**
- **File**: `the_alchemiser/portfolio/rebalancing/rebalance_plan.py`
- **Description**: Contains actual deprecation warnings
- **Purpose**: Issues runtime deprecation warnings
- **Suggested Action**: review_for_removal
- **Evidence**: Warning: Importing from ...; Actively imported by 2 files

**4. position_service.py** **[2 imports]**
- **File**: `the_alchemiser/portfolio/positions/position_service.py`
- **Description**: Contains actual deprecation warnings
- **Purpose**: Issues runtime deprecation warnings
- **Suggested Action**: review_for_removal
- **Evidence**: Warning: Importing from ...; Actively imported by 2 files

**5. legacy_position_manager.py** **[1 imports]**
- **File**: `the_alchemiser/portfolio/positions/legacy_position_manager.py`
- **Description**: File explicitly named with 'legacy' keyword
- **Purpose**: File explicitly indicating legacy status
- **Suggested Action**: review_for_migration
- **Evidence**: Filename contains 'legacy'; Actively imported by 1 files

**6. asset_order_handler.py** **[1 imports]**
- **File**: `the_alchemiser/execution/orders/asset_order_handler.py`
- **Description**: Contains actual deprecation warnings
- **Purpose**: Issues runtime deprecation warnings
- **Suggested Action**: review_for_removal
- **Evidence**: Warning: AssetOrderHandler.handle_fractionability_error is deprecated. ...; Warning: AssetOrderHandler.handle_limit_order_fractionability_error is deprecated. ...; Actively imported by 1 files

**7. portfolio_pnl_utils.py** **[1 imports]**
- **File**: `the_alchemiser/portfolio/utils/portfolio_pnl_utils.py`
- **Description**: Contains actual deprecation warnings
- **Purpose**: Issues runtime deprecation warnings
- **Suggested Action**: review_for_removal
- **Evidence**: Warning: Importing from ...; Actively imported by 1 files

**8. position_manager.py** **[1 imports]**
- **File**: `the_alchemiser/portfolio/holdings/position_manager.py`
- **Description**: Contains actual deprecation warnings
- **Purpose**: Issues runtime deprecation warnings
- **Suggested Action**: review_for_removal
- **Evidence**: Warning: PositionManager.validate_sell_position is deprecated. ...; Warning: PositionManager.validate_buying_power is deprecated. ...; Actively imported by 1 files

**9. orchestrator_facade.py** **[1 imports]**
- **File**: `the_alchemiser/portfolio/rebalancing/orchestrator_facade.py`
- **Description**: Contains actual deprecation warnings
- **Purpose**: Issues runtime deprecation warnings
- **Suggested Action**: review_for_removal
- **Evidence**: Warning: Importing from ...; Actively imported by 1 files

**10. legacy_position_manager.py** **[1 imports]**
- **File**: `the_alchemiser/portfolio/positions/legacy_position_manager.py`
- **Description**: Contains actual deprecation warnings
- **Purpose**: Issues runtime deprecation warnings
- **Suggested Action**: review_for_removal
- **Evidence**: Warning: Importing from ...; Actively imported by 1 files

**11. execution_manager_legacy.py**
- **File**: `the_alchemiser/execution/core/execution_manager_legacy.py`
- **Description**: File explicitly named with 'legacy' keyword
- **Purpose**: File explicitly indicating legacy status
- **Suggested Action**: review_for_migration
- **Evidence**: Filename contains 'legacy'

**12. error_handling.py**
- **File**: `the_alchemiser/shared/utils/error_handling.py`
- **Description**: Contains actual deprecation warnings
- **Purpose**: Issues runtime deprecation warnings
- **Suggested Action**: review_for_removal
- **Evidence**: Warning: the_alchemiser.shared.utils.error_handling is deprecated. ...; Warning: create_service_logger is deprecated. ...

**13. execution_service.py**
- **File**: `the_alchemiser/portfolio/execution/execution_service.py`
- **Description**: Contains actual deprecation warnings
- **Purpose**: Issues runtime deprecation warnings
- **Suggested Action**: review_for_removal
- **Evidence**: Warning: Importing from ...

**14. orchestrator.py**
- **File**: `the_alchemiser/portfolio/rebalancing/orchestrator.py`
- **Description**: Contains actual deprecation warnings
- **Purpose**: Issues runtime deprecation warnings
- **Suggested Action**: review_for_removal
- **Evidence**: Warning: Importing from ...

**15. rebalancing_service.py**
- **File**: `the_alchemiser/portfolio/rebalancing/rebalancing_service.py`
- **Description**: Contains actual deprecation warnings
- **Purpose**: Issues runtime deprecation warnings
- **Suggested Action**: review_for_removal
- **Evidence**: Warning: Importing from ...

**16. analysis_service.py**
- **File**: `the_alchemiser/portfolio/analytics/analysis_service.py`
- **Description**: Contains actual deprecation warnings
- **Purpose**: Issues runtime deprecation warnings
- **Suggested Action**: review_for_removal
- **Evidence**: Warning: Importing from ...

**17. position_analyzer.py**
- **File**: `the_alchemiser/portfolio/analytics/position_analyzer.py`
- **Description**: Contains actual deprecation warnings
- **Purpose**: Issues runtime deprecation warnings
- **Suggested Action**: review_for_removal
- **Evidence**: Warning: Importing from ...

**18. position_delta.py**
- **File**: `the_alchemiser/portfolio/analytics/position_delta.py`
- **Description**: Contains actual deprecation warnings
- **Purpose**: Issues runtime deprecation warnings
- **Suggested Action**: review_for_removal
- **Evidence**: Warning: Importing from ...

**19. attribution_engine.py**
- **File**: `the_alchemiser/portfolio/analytics/attribution_engine.py`
- **Description**: Contains actual deprecation warnings
- **Purpose**: Issues runtime deprecation warnings
- **Suggested Action**: review_for_removal
- **Evidence**: Warning: Importing from ...

**20. policy_layer_usage.py**
- **File**: `examples/policy_layer_usage.py`
- **Description**: Explicitly marked with 'Status: legacy'
- **Purpose**: Module explicitly marked as legacy
- **Suggested Action**: review_for_migration
- **Evidence**: """Business Unit: utilities; Status: legacy.

**21. execution_manager_legacy.py**
- **File**: `the_alchemiser/execution/core/execution_manager_legacy.py`
- **Description**: Explicitly marked with 'Status: legacy'
- **Purpose**: Module explicitly marked as legacy
- **Suggested Action**: review_for_migration
- **Evidence**: """Business Unit: execution; Status: legacy.

### 🟡 MEDIUM RISK (15 items)

**1. canonical_executor.py** **[6 imports]**
- **File**: `the_alchemiser/execution/core/canonical_executor.py`
- **Description**: Import redirection shim
- **Purpose**: Redirects imports to new location
- **Suggested Action**: migrate_imports
- **Evidence**: Star imports: 1; Redirection language found; Short file: 9 lines; Actively imported by 6 files

**2. rebalance_plan.py** **[2 imports]**
- **File**: `the_alchemiser/portfolio/rebalancing/rebalance_plan.py`
- **Description**: Import redirection shim
- **Purpose**: Redirects imports to new location
- **Suggested Action**: migrate_imports
- **Evidence**: Star imports: 1; Redirection language found; Short file: 12 lines; Actively imported by 2 files

**3. position_service.py** **[2 imports]**
- **File**: `the_alchemiser/portfolio/positions/position_service.py`
- **Description**: Import redirection shim
- **Purpose**: Redirects imports to new location
- **Suggested Action**: migrate_imports
- **Evidence**: Star imports: 1; Redirection language found; Short file: 12 lines; Actively imported by 2 files

**4. portfolio_pnl_utils.py** **[1 imports]**
- **File**: `the_alchemiser/portfolio/utils/portfolio_pnl_utils.py`
- **Description**: Import redirection shim
- **Purpose**: Redirects imports to new location
- **Suggested Action**: migrate_imports
- **Evidence**: Star imports: 1; Redirection language found; Short file: 13 lines; Actively imported by 1 files

**5. orchestrator_facade.py** **[1 imports]**
- **File**: `the_alchemiser/portfolio/rebalancing/orchestrator_facade.py`
- **Description**: Import redirection shim
- **Purpose**: Redirects imports to new location
- **Suggested Action**: migrate_imports
- **Evidence**: Star imports: 1; Redirection language found; Short file: 12 lines; Actively imported by 1 files

**6. legacy_position_manager.py** **[1 imports]**
- **File**: `the_alchemiser/portfolio/positions/legacy_position_manager.py`
- **Description**: Import redirection shim
- **Purpose**: Redirects imports to new location
- **Suggested Action**: migrate_imports
- **Evidence**: Star imports: 1; Redirection language found; Short file: 12 lines; Actively imported by 1 files

**7. execution_manager_legacy.py**
- **File**: `the_alchemiser/execution/core/execution_manager_legacy.py`
- **Description**: Import redirection shim
- **Purpose**: Redirects imports to new location
- **Suggested Action**: migrate_imports
- **Evidence**: Star imports: 1; Redirection language found; Short file: 9 lines

**8. __init__.py**
- **File**: `the_alchemiser/shared/utils/__init__.py`
- **Description**: Import redirection shim
- **Purpose**: Redirects imports to new location
- **Suggested Action**: migrate_imports
- **Evidence**: Star imports: 3; Redirection language found; Short file: 18 lines

**9. execution_service.py**
- **File**: `the_alchemiser/portfolio/execution/execution_service.py`
- **Description**: Import redirection shim
- **Purpose**: Redirects imports to new location
- **Suggested Action**: migrate_imports
- **Evidence**: Star imports: 1; Redirection language found; Short file: 12 lines

**10. orchestrator.py**
- **File**: `the_alchemiser/portfolio/rebalancing/orchestrator.py`
- **Description**: Import redirection shim
- **Purpose**: Redirects imports to new location
- **Suggested Action**: migrate_imports
- **Evidence**: Star imports: 1; Redirection language found; Short file: 12 lines

**11. rebalancing_service.py**
- **File**: `the_alchemiser/portfolio/rebalancing/rebalancing_service.py`
- **Description**: Import redirection shim
- **Purpose**: Redirects imports to new location
- **Suggested Action**: migrate_imports
- **Evidence**: Star imports: 1; Redirection language found; Short file: 12 lines

**12. analysis_service.py**
- **File**: `the_alchemiser/portfolio/analytics/analysis_service.py`
- **Description**: Import redirection shim
- **Purpose**: Redirects imports to new location
- **Suggested Action**: migrate_imports
- **Evidence**: Star imports: 1; Redirection language found; Short file: 12 lines

**13. position_analyzer.py**
- **File**: `the_alchemiser/portfolio/analytics/position_analyzer.py`
- **Description**: Import redirection shim
- **Purpose**: Redirects imports to new location
- **Suggested Action**: migrate_imports
- **Evidence**: Star imports: 1; Redirection language found; Short file: 12 lines

**14. position_delta.py**
- **File**: `the_alchemiser/portfolio/analytics/position_delta.py`
- **Description**: Import redirection shim
- **Purpose**: Redirects imports to new location
- **Suggested Action**: migrate_imports
- **Evidence**: Star imports: 1; Redirection language found; Short file: 12 lines

**15. attribution_engine.py**
- **File**: `the_alchemiser/portfolio/analytics/attribution_engine.py`
- **Description**: Import redirection shim
- **Purpose**: Redirects imports to new location
- **Suggested Action**: migrate_imports
- **Evidence**: Star imports: 1; Redirection language found; Short file: 12 lines

### 🟢 LOW RISK (2 items)

**1. execution_context_adapter.py.backup**
- **File**: `the_alchemiser/execution/strategies/execution_context_adapter.py.backup`
- **Description**: Backup file (*.backup)
- **Purpose**: Backup file that should be cleaned up
- **Suggested Action**: remove
- **Evidence**: Backup pattern: *.backup

**2. rebalance_execution_service.py.backup**
- **File**: `the_alchemiser/portfolio/allocation/rebalance_execution_service.py.backup`
- **Description**: Backup file (*.backup)
- **Purpose**: Backup file that should be cleaned up
- **Suggested Action**: remove
- **Evidence**: Backup pattern: *.backup

## Recommendations

### Immediate Actions Required

1. **Review 21 high-risk shims** - These are explicitly marked as legacy or deprecated
2. **Handle 16 actively imported shims** - Must update import statements before removal
3. **Remove backup files** - These can be safely deleted

### Suggested Action Priority

1. **Backup Files** → Safe to remove immediately
2. **Import Redirections** → Update import statements, then remove shim
3. **Legacy Code** → Review, migrate functionality, then remove
4. **Deprecated Code** → Already marked for removal, coordinate timing

### Risk Mitigation

- **Test after each shim removal** to ensure no functionality is broken
- **Update import statements before removing shims**
- **Coordinate with team** for files with many active imports
- **Document replacement paths** for future reference

## Cross-Reference with Existing Work

This audit complements existing migration reports:
- `LEGACY_AUDIT_REPORT.md` - Broader legacy DDD architecture cleanup
- `STRATEGY_LEGACY_AUDIT_REPORT.md` - Strategy module specific cleanup
- `DELETION_SAFETY_MATRIX.md` - Safe deletion guidelines

The shims identified here are in addition to the legacy architecture cleanup already in progress.

---

**Generated**: January 2025  
**Scope**: Confirmed shims and compatibility layers only  
**Issue**: #492  
**Tool**: scripts/focused_shim_auditor.py  