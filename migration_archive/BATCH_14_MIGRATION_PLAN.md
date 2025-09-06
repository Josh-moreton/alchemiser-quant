# Batch 14 Migration Plan

**Generated**: January 2025
**Batch Size**: 15 files
**Target**: Consolidate legacy naming patterns and backup strategy files

## Files for Migration

### 1. execution/services/account_service.py
- **Target**: `execution/brokers/account_service.py`
- **Reason**: Account services belong with broker operations
- **Estimated Imports**: 14

### 2. shared/services/market_data_service.py  
- **Target**: `strategy/data/market_data_service.py`
- **Reason**: Market data is strategy input, not shared utility
- **Estimated Imports**: 11

### 3. strategy/mappers/strategy_domain_mapping.py
- **Target**: `strategy/core/domain_mapping.py`
- **Reason**: Core strategy functionality, not separate mapper
- **Estimated Imports**: 3

### 4. shared/interfaces/trading_ports.py
- **Target**: `shared/interfaces/trading.py`
- **Reason**: Simplified naming convention
- **Estimated Imports**: 2

### 5. shared/interfaces/trading_repository.py
- **Target**: `shared/interfaces/repository.py`
- **Reason**: Generic repository interface
- **Estimated Imports**: 1

### 6. shared/config/application_container.py
- **Target**: `shared/config/container.py`
- **Reason**: Simplified container naming
- **Estimated Imports**: 2

### 7. domain/strategies_backup/protocols/strategy_engine.py
- **Target**: `strategy/interfaces/engine_protocol.py`
- **Reason**: Strategy engine interface belongs in strategy module
- **Estimated Imports**: 1

### 8. domain/strategies_backup/klm_workers/variant_530_18.py
- **Target**: `strategy/archived/klm/variant_530_18.py`
- **Reason**: Archive backup strategy variants
- **Estimated Imports**: 0

### 9. domain/strategies_backup/klm_workers/variant_506_38.py
- **Target**: `strategy/archived/klm/variant_506_38.py`
- **Reason**: Archive backup strategy variants
- **Estimated Imports**: 0

### 10. domain/strategies_backup/klm_workers/variant_410_38.py
- **Target**: `strategy/archived/klm/variant_410_38.py`
- **Reason**: Archive backup strategy variants
- **Estimated Imports**: 0

### 11. domain/strategies_backup/klm_workers/variant_830_21.py
- **Target**: `strategy/archived/klm/variant_830_21.py`
- **Reason**: Archive backup strategy variants
- **Estimated Imports**: 0

### 12. domain/strategies_backup/klm_workers/variant_nova.py
- **Target**: `strategy/archived/klm/variant_nova.py`
- **Reason**: Archive backup strategy variants
- **Estimated Imports**: 0

### 13. domain/strategies_backup/klm_workers/variant_1280_26.py
- **Target**: `strategy/archived/klm/variant_1280_26.py`
- **Reason**: Archive backup strategy variants
- **Estimated Imports**: 0

### 14. domain/strategies_backup/klm_workers/variant_520_22.py
- **Target**: `strategy/archived/klm/variant_520_22.py`
- **Reason**: Archive backup strategy variants
- **Estimated Imports**: 0

### 15. domain/strategies_backup/klm_workers/base_klm_variant.py
- **Target**: `strategy/archived/klm/base_variant.py`
- **Reason**: Archive backup strategy base class
- **Estimated Imports**: 0

## Execution Plan

1. Create target directories
2. Move files to proper modular locations
3. Update import statements
4. Remove empty legacy directories
5. Update documentation

**Total Estimated Import Updates**: ~34

## Success Criteria

- All files moved to proper business unit locations
- All import references updated
- Zero functional impact
- Documentation updated
- Lint checks pass