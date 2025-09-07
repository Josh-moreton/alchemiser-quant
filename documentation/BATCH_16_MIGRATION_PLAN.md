# Batch 16 Migration Plan

## Target Files (15 highest priority by import count)

| Priority | File | Current Location | Target Location | Imports | Business Unit |
|----------|------|------------------|-----------------|---------|---------------|
| 1 | exceptions.py | shared/utils/ | shared/types/ | 29 | shared |
| 2 | logging.py | shared/utils/ | shared/logging/ | 26 | shared |
| 3 | logging_utils.py | shared/utils/ | shared/logging/ | 26 | shared |
| 4 | common.py | utils/ | shared/utils/ | 22 | shared |
| 5 | num.py | utils/ | shared/math/ | 13 | shared |
| 6 | error_handler.py | shared/utils/ | shared/errors/ | 9 | shared |
| 7 | engine.py | domain/strategies/ | strategy/engines/ | 5 | strategy |
| 8 | strategy_registry.py | domain/registry/ | strategy/registry/ | 5 | strategy |
| 9 | account_utils.py | shared/utils/ | shared/utils/ | 4 | shared |
| 10 | context.py | shared/utils/ | shared/utils/ | 4 | shared |
| 11 | decorators.py | shared/utils/ | shared/utils/ | 4 | shared |
| 12 | typed_strategy_manager.py | domain/strategies/ | strategy/engines/ | 4 | strategy |
| 13 | s3_utils.py | infrastructure/s3/ | shared/utils/ | 4 | shared |
| 14 | order_status_literal.py | domain/trading/value_objects/ | execution/orders/ | 3 | execution |
| 15 | typed_klm_ensemble_engine.py | domain/strategies/ | strategy/engines/ | 3 | strategy |

## Migration Strategy

1. **High-impact utilities first** (exceptions, logging, common utils)
2. **Strategy domain objects** to strategy/ module
3. **Trading domain objects** to execution/ module
4. **Infrastructure adapters** to shared/utils/

## Expected Import Updates: ~140+ import statements