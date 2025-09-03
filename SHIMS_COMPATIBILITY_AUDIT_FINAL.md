# Shims & Compatibility Layers Audit Report

## Executive Summary

This report identifies **28 confirmed shims and compatibility layers** in the codebase that require attention. This focused audit only includes files that are definitively shims, import redirections, or legacy compatibility code.

**Risk Distribution:**
- 🔴 **High Risk**: 15 items (explicit legacy code, deprecation warnings)
- 🟡 **Medium Risk**: 13 items (import redirections)
- 🟢 **Low Risk**: 0 items (backup files)

**Active Usage**: 1 shims are actively imported by other files

## Detailed Findings

### 🔴 HIGH RISK (15 items)

**1. position_manager.py** **[1 imports]**
- **File**: `the_alchemiser/portfolio/holdings/position_manager.py`
- **Description**: Contains actual deprecation warnings
- **Purpose**: Issues runtime deprecation warnings
- **Suggested Action**: review_for_removal
- **Evidence**: Warning: PositionManager.validate_sell_position is deprecated. ...; Warning: PositionManager.validate_buying_power is deprecated. ...; Actively imported by 1 files

**2. asset_order_handler.py**
- **File**: `the_alchemiser/execution/orders/asset_order_handler.py`
- **Description**: Contains actual deprecation warnings
- **Purpose**: Issues runtime deprecation warnings
- **Suggested Action**: review_for_removal
- **Evidence**: Warning: AssetOrderHandler.handle_fractionability_error is deprecated. ...; Warning: AssetOrderHandler.handle_limit_order_fractionability_error is deprecated. ...

**3. error_handling.py**
- **File**: `the_alchemiser/shared/utils/error_handling.py`
- **Description**: Contains actual deprecation warnings
- **Purpose**: Issues runtime deprecation warnings
- **Suggested Action**: review_for_removal
- **Evidence**: Warning: the_alchemiser.shared.utils.error_handling is deprecated. ...; Warning: create_service_logger is deprecated. ...

**4. execution_service.py**
- **File**: `the_alchemiser/portfolio/execution/execution_service.py`
- **Description**: Contains actual deprecation warnings
- **Purpose**: Issues runtime deprecation warnings
- **Suggested Action**: review_for_removal
- **Evidence**: Warning: Importing from ...

**5. portfolio_pnl_utils.py**
- **File**: `the_alchemiser/portfolio/utils/portfolio_pnl_utils.py`
- **Description**: Contains actual deprecation warnings
- **Purpose**: Issues runtime deprecation warnings
- **Suggested Action**: review_for_removal
- **Evidence**: Warning: Importing from ...

**6. rebalance_plan.py**
- **File**: `the_alchemiser/portfolio/rebalancing/rebalance_plan.py`
- **Description**: Contains actual deprecation warnings
- **Purpose**: Issues runtime deprecation warnings
- **Suggested Action**: review_for_removal
- **Evidence**: Warning: Importing from ...

**7. orchestrator.py**
- **File**: `the_alchemiser/portfolio/rebalancing/orchestrator.py`
- **Description**: Contains actual deprecation warnings
- **Purpose**: Issues runtime deprecation warnings
- **Suggested Action**: review_for_removal
- **Evidence**: Warning: Importing from ...

**8. rebalancing_service.py**
- **File**: `the_alchemiser/portfolio/rebalancing/rebalancing_service.py`
- **Description**: Contains actual deprecation warnings
- **Purpose**: Issues runtime deprecation warnings
- **Suggested Action**: review_for_removal
- **Evidence**: Warning: Importing from ...

**9. orchestrator_facade.py**
- **File**: `the_alchemiser/portfolio/rebalancing/orchestrator_facade.py`
- **Description**: Contains actual deprecation warnings
- **Purpose**: Issues runtime deprecation warnings
- **Suggested Action**: review_for_removal
- **Evidence**: Warning: Importing from ...

**10. analysis_service.py**
- **File**: `the_alchemiser/portfolio/analytics/analysis_service.py`
- **Description**: Contains actual deprecation warnings
- **Purpose**: Issues runtime deprecation warnings
- **Suggested Action**: review_for_removal
- **Evidence**: Warning: Importing from ...

**11. position_analyzer.py**
- **File**: `the_alchemiser/portfolio/analytics/position_analyzer.py`
- **Description**: Contains actual deprecation warnings
- **Purpose**: Issues runtime deprecation warnings
- **Suggested Action**: review_for_removal
- **Evidence**: Warning: Importing from ...

**12. position_delta.py**
- **File**: `the_alchemiser/portfolio/analytics/position_delta.py`
- **Description**: Contains actual deprecation warnings
- **Purpose**: Issues runtime deprecation warnings
- **Suggested Action**: review_for_removal
- **Evidence**: Warning: Importing from ...

**13. attribution_engine.py**
- **File**: `the_alchemiser/portfolio/analytics/attribution_engine.py`
- **Description**: Contains actual deprecation warnings
- **Purpose**: Issues runtime deprecation warnings
- **Suggested Action**: review_for_removal
- **Evidence**: Warning: Importing from ...

**14. position_service.py**
- **File**: `the_alchemiser/portfolio/positions/position_service.py`
- **Description**: Contains actual deprecation warnings
- **Purpose**: Issues runtime deprecation warnings
- **Suggested Action**: review_for_removal
- **Evidence**: Warning: Importing from ...

**15. canonical_executor.py**
- **File**: `the_alchemiser/execution/core/canonical_executor.py`
- **Description**: Explicitly marked with 'Status: legacy'
- **Purpose**: Module explicitly marked as legacy
- **Suggested Action**: review_for_migration
- **Evidence**: """Business Unit: execution; Status: legacy.

### 🟡 MEDIUM RISK (13 items)

**1. canonical_executor.py**
- **File**: `the_alchemiser/execution/core/canonical_executor.py`
- **Description**: Import redirection shim
- **Purpose**: Redirects imports to new location
- **Suggested Action**: migrate_imports
- **Evidence**: Star imports: 1; Redirection language found; Short file: 9 lines

**2. __init__.py**
- **File**: `the_alchemiser/shared/utils/__init__.py`
- **Description**: Import redirection shim
- **Purpose**: Redirects imports to new location
- **Suggested Action**: migrate_imports
- **Evidence**: Star imports: 3; Redirection language found; Short file: 18 lines

**3. execution_service.py**
- **File**: `the_alchemiser/portfolio/execution/execution_service.py`
- **Description**: Import redirection shim
- **Purpose**: Redirects imports to new location
- **Suggested Action**: migrate_imports
- **Evidence**: Star imports: 1; Redirection language found; Short file: 12 lines

**4. portfolio_pnl_utils.py**
- **File**: `the_alchemiser/portfolio/utils/portfolio_pnl_utils.py`
- **Description**: Import redirection shim
- **Purpose**: Redirects imports to new location
- **Suggested Action**: migrate_imports
- **Evidence**: Star imports: 1; Redirection language found; Short file: 13 lines

**5. rebalance_plan.py**
- **File**: `the_alchemiser/portfolio/rebalancing/rebalance_plan.py`
- **Description**: Import redirection shim
- **Purpose**: Redirects imports to new location
- **Suggested Action**: migrate_imports
- **Evidence**: Star imports: 1; Redirection language found; Short file: 12 lines

**6. orchestrator.py**
- **File**: `the_alchemiser/portfolio/rebalancing/orchestrator.py`
- **Description**: Import redirection shim
- **Purpose**: Redirects imports to new location
- **Suggested Action**: migrate_imports
- **Evidence**: Star imports: 1; Redirection language found; Short file: 12 lines

**7. rebalancing_service.py**
- **File**: `the_alchemiser/portfolio/rebalancing/rebalancing_service.py`
- **Description**: Import redirection shim
- **Purpose**: Redirects imports to new location
- **Suggested Action**: migrate_imports
- **Evidence**: Star imports: 1; Redirection language found; Short file: 12 lines

**8. orchestrator_facade.py**
- **File**: `the_alchemiser/portfolio/rebalancing/orchestrator_facade.py`
- **Description**: Import redirection shim
- **Purpose**: Redirects imports to new location
- **Suggested Action**: migrate_imports
- **Evidence**: Star imports: 1; Redirection language found; Short file: 12 lines

**9. analysis_service.py**
- **File**: `the_alchemiser/portfolio/analytics/analysis_service.py`
- **Description**: Import redirection shim
- **Purpose**: Redirects imports to new location
- **Suggested Action**: migrate_imports
- **Evidence**: Star imports: 1; Redirection language found; Short file: 12 lines

**10. position_analyzer.py**
- **File**: `the_alchemiser/portfolio/analytics/position_analyzer.py`
- **Description**: Import redirection shim
- **Purpose**: Redirects imports to new location
- **Suggested Action**: migrate_imports
- **Evidence**: Star imports: 1; Redirection language found; Short file: 12 lines

**11. position_delta.py**
- **File**: `the_alchemiser/portfolio/analytics/position_delta.py`
- **Description**: Import redirection shim
- **Purpose**: Redirects imports to new location
- **Suggested Action**: migrate_imports
- **Evidence**: Star imports: 1; Redirection language found; Short file: 12 lines

**12. attribution_engine.py**
- **File**: `the_alchemiser/portfolio/analytics/attribution_engine.py`
- **Description**: Import redirection shim
- **Purpose**: Redirects imports to new location
- **Suggested Action**: migrate_imports
- **Evidence**: Star imports: 1; Redirection language found; Short file: 12 lines

**13. position_service.py**
- **File**: `the_alchemiser/portfolio/positions/position_service.py`
- **Description**: Import redirection shim
- **Purpose**: Redirects imports to new location
- **Suggested Action**: migrate_imports
- **Evidence**: Star imports: 1; Redirection language found; Short file: 12 lines

## Recommendations

### Immediate Actions Required

1. **Review 15 high-risk shims** - These are explicitly marked as legacy or deprecated
2. **Handle 1 actively imported shims** - Must update import statements before removal
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