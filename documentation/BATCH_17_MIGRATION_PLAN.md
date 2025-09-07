# Batch 17 Migration Plan - Final Cleanup
**Date**: January 2025  
**Status**: Ready for execution  
**Target**: Complete remaining legacy file migrations  

## Files to Migrate (18+ files)

Based on analysis of remaining legacy files in services/, application/, domain/, infrastructure/, and interfaces/ directories:

| File | Current Location | Target Location | Business Unit | Imports | Priority |
|------|------------------|-----------------|---------------|---------|----------|
| `symbol_classifier.py` | `domain/portfolio/strategy_attribution/` | **REMOVE** - Deprecated shim | N/A | 0 | LOW |
| `account_like.py` | `domain/protocols/` | `shared/protocols/` | shared | ? | MEDIUM |
| `order_like.py` | `domain/protocols/` | `shared/protocols/` | shared | ? | MEDIUM |
| `position_like.py` | `domain/protocols/` | `shared/protocols/` | shared | ? | MEDIUM |
| `strategy_registry.py` | `domain/registry/` | `strategy/registry/` | strategy | ? | MEDIUM |
| `nuclear_logic.py` | `domain/strategies/` | `strategy/engines/archived/` | strategy | ? | LOW |
| `variant_1200_28.py` | `domain/strategies_backup/klm_workers/` | `strategy/engines/archived/backup/` | strategy | ? | LOW |
| `strategy_position_model.py` | `domain/strategies_backup/models/` | `strategy/engines/archived/backup/` | strategy | ? | LOW |
| `strategy_signal_model.py` | `domain/strategies_backup/models/` | `strategy/engines/archived/backup/` | strategy | ? | LOW |
| `alert.py` | `domain/strategies_backup/value_objects/` | `strategy/engines/archived/backup/` | strategy | ? | LOW |
| `confidence.py` | `domain/strategies_backup/value_objects/` | `strategy/engines/archived/backup/` | strategy | ? | LOW |
| `strategy_signal.py` | `domain/strategies_backup/value_objects/` | `strategy/engines/archived/backup/` | strategy | ? | LOW |
| Trading error files | `domain/trading/errors/` | `execution/errors/` | execution | ? | MEDIUM |
| Trading lifecycle files | `domain/trading/lifecycle/` | `execution/lifecycle/` | execution | ? | MEDIUM |
| Trading protocol files | `domain/trading/protocols/` | `execution/protocols/` | execution | ? | MEDIUM |
| `alert_service.py` | `infrastructure/alerts/` | `shared/services/` | shared | ? | LOW |
| `real_time_pricing.py` | `infrastructure/data_providers/` | `shared/services/` | shared | ? | MEDIUM |
| `infrastructure_providers.py` | `infrastructure/dependency_injection/` | `shared/config/` | shared | ? | LOW |
| Notification files | `infrastructure/notifications/` | `shared/notifications/` | shared | ? | LOW |
| `slippage_analyzer.py` | `infrastructure/services/` | `execution/analytics/` | execution | 2 | MEDIUM |
| `tick_size_service.py` | `infrastructure/services/` | `shared/services/` | shared | ? | LOW |
| `websocket_connection_manager.py` | `infrastructure/websocket/` | `shared/services/` | shared | ? | LOW |
| Portfolio service files | `portfolio/services/` | `portfolio/` (various subdirs) | portfolio | ? | MEDIUM |
| Repository interfaces | `shared/interfaces/` | `shared/protocols/` | shared | ? | LOW |
| Core domain mapping | `strategy/core/domain_mapping.py` | `strategy/data/` | strategy | ? | LOW |
| Engine protocol | `strategy/interfaces/engine_protocol.py` | `strategy/protocols/` | strategy | ? | LOW |

## Migration Strategy

1. **Remove deprecated shims**: Delete symbol_classifier.py (already deprecated)
2. **Systematic file movement**: Move files to appropriate business unit locations
3. **Import updates**: Update all import references to point to new locations
4. **Documentation**: Update migration reports and statistics

## Expected Impact

- **Files migrated**: ~18+ files
- **Import statements to update**: 20-50 (estimated)
- **Completion target**: 100% legacy file migration
- **Business unit alignment**: Complete modular architecture