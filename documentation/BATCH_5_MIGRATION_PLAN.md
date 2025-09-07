# Phase 2 Migration - Batch 5 Plan

**Batch Size**: 15 files (continuing proven 15-file systematic approach)  
**Priority**: HIGH - Top import dependency files (14-4 imports each)
**Target**: Continue systematic legacy cleanup with proper business unit alignment

## Batch 5 File Selection (15 files)

Selected based on highest import dependencies from remaining legacy files:

| Priority | File | Current Location | Target Module | Imports | Business Unit Rationale |
|----------|------|------------------|---------------|---------|-------------------------|
| 1 | `alpaca_manager.py` | `services/repository/` | `execution/brokers/` | 14 | Broker API integration belongs in execution |
| 2 | `money.py` | `domain/shared_kernel/value_objects/` | `shared/types/` | 13 | Core financial type used across modules |
| 3 | `policy_result.py` | `domain/policies/` | `shared/types/` | 13 | Cross-cutting policy result type |
| 4 | `strategy_signal.py` | `domain/strategies/value_objects/` | `strategy/signals/` | 13 | Strategy signal generation |
| 5 | `percentage.py` | `domain/shared_kernel/value_objects/` | `shared/types/` | 11 | Core numeric type used across modules |
| 6 | `trading_service_manager.py` | `services/trading/` | `execution/services/` | 10 | Trading service coordination |
| 7 | `canonical_executor.py` | `application/execution/` | `execution/core/` | 10 | Core execution logic |
| 8 | `evaluator.py` | `domain/dsl/` | `strategy/dsl/` | 10 | DSL evaluation for strategies |
| 9 | `symbol.py` | `domain/shared_kernel/value_objects/` | `shared/types/` | 9 | Core trading symbol type |
| 10 | `market_data_mapping.py` | `application/mapping/` | `strategy/mappers/` | 8 | Market data for strategy signals |
| 11 | `bar.py` | `domain/market_data/models/` | `shared/types/` | 8 | Core market data structure |
| 12 | `evaluator_cache.py` | `domain/dsl/` | `strategy/dsl/` | 8 | DSL evaluation caching |
| 13 | `common.py` | `interfaces/schemas/` | `shared/schemas/` | 7 | Common schema definitions |
| 14 | `quote.py` | `domain/market_data/models/` | `shared/types/` | 7 | Core market data structure |
| 15 | `secrets_manager.py` | `infrastructure/secrets/` | `shared/config/` | 7 | Configuration and secrets |

## Migration Strategy

### Business Unit Alignment
- **execution/**: 3 files (broker integration, services, core execution)
- **strategy/**: 4 files (signals, DSL, data mapping)  
- **shared/**: 8 files (types, schemas, configuration)

### Migration Order
Execute in priority order (highest import count first) to unblock dependencies quickly.

### Success Criteria
- [ ] All 15 files moved to appropriate modular locations
- [ ] All import references updated (estimated ~135 total imports)
- [ ] Zero functional impact - all health checks pass
- [ ] Proper business unit boundaries maintained
- [ ] Documentation updated with results