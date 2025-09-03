# Legacy Cleanup Plan

Based on comprehensive audit findings, this plan addresses 271 total findings.

## Phase 1: Safe Deletions (Low Risk)

### Backup Files to Remove
Found 0 backup files safe for removal:


### Deprecated Comments to Clean
Found 34 deprecated comments to review:

- `the_alchemiser/execution/orders/service.py:79` - Deprecated code or comment: # Legacy place_market_order / place_limit_order removed. Use CanonicalOrderExecutor externally.
- `the_alchemiser/execution/orders/validation.py:297` - Deprecated code or comment: # Legacy compatibility functions for existing code
- `the_alchemiser/execution/orders/asset_order_handler.py:167` - Deprecated code or comment: DEPRECATED: This fractionability error handling has been moved to FractionabilityPolicy.
- `the_alchemiser/execution/orders/asset_order_handler.py:291` - Deprecated code or comment: DEPRECATED: This fractionability error handling has been moved to FractionabilityPolicy.
- `the_alchemiser/execution/brokers/alpaca_client.py:82` - Deprecated code or comment: # DEPRECATED: LimitOrderHandler import removed - use CanonicalOrderExecutor instead
- `the_alchemiser/execution/brokers/alpaca_client.py:143` - Deprecated code or comment: # DEPRECATED: LimitOrderHandler removed - use CanonicalOrderExecutor instead
- `the_alchemiser/execution/brokers/alpaca_client.py:223` - Deprecated code or comment: # Legacy direct order placement methods removed - use CanonicalOrderExecutor externally.
- `the_alchemiser/strategy/data/domain_mapping.py:85` - Deprecated code or comment: # Legacy signal normalization (for backward compatibility)
- `the_alchemiser/strategy/signals/strategy_signal.py:1` - Deprecated code or comment: """DEPRECATED: Strategy value objects moved to the_alchemiser.strategy.engines.value_objects.
- `the_alchemiser/shared/utils/__init__.py:21` - Deprecated code or comment: from .error_handling import *  # Legacy deprecated
- ... and 24 more

## Phase 2: Shim Analysis and Removal

### Compatibility Shims Requiring Import Migration
Found 46 shim files requiring import updates:

- `the_alchemiser/execution/orders/asset_order_handler.py` - 1 importing files
  - `the_alchemiser/execution/brokers/alpaca_client.py`
- `the_alchemiser/execution/orders/asset_order_handler.py` - 1 importing files
  - `the_alchemiser/execution/brokers/alpaca_client.py`
- `the_alchemiser/execution/core/execution_manager_legacy.py` - 0 importing files
- `the_alchemiser/execution/core/canonical_executor.py` - 6 importing files
  - `examples/policy_layer_usage.py`
  - `the_alchemiser/execution/core/execution_manager.py`
  - `the_alchemiser/execution/brokers/alpaca_client.py`
  - ... and 3 more
- `the_alchemiser/execution/mappers/orders.py` - 6 importing files
  - `the_alchemiser/execution/orders/validation.py`
  - `the_alchemiser/execution/core/execution_manager.py`
  - `the_alchemiser/execution/mappers/alpaca_dto_mapping.py`
  - ... and 3 more
- `the_alchemiser/execution/brokers/alpaca_client.py` - 2 importing files
  - `the_alchemiser/strategy/engines/core/trading_engine.py`
  - `the_alchemiser/portfolio/allocation/rebalance_execution_service.py`
- `the_alchemiser/strategy/signals/strategy_signal.py` - 7 importing files
  - `the_alchemiser/strategy/protocols/engine_protocol.py`
  - `the_alchemiser/strategy/managers/typed_strategy_manager.py`
  - `the_alchemiser/strategy/engines/klm_ensemble_engine.py`
  - ... and 4 more
- `the_alchemiser/main.py` - 4 importing files
  - `the_alchemiser/__init__.py`
  - `the_alchemiser/lambda_handler.py`
  - `the_alchemiser/strategy/engines/core/trading_engine.py`
  - ... and 1 more
- `the_alchemiser/shared/utils/error_handling.py` - 0 importing files
- `the_alchemiser/shared/value_objects/core_types.py` - 41 importing files
  - `the_alchemiser/execution/core/manager.py`
  - `the_alchemiser/execution/core/execution_schemas.py`
  - `the_alchemiser/execution/core/account_facade.py`
  - ... and 38 more
- ... and 36 more shims

## Phase 3: Legacy Structure Migration

### High Priority: utils/ and services/ directories
These directories should be migrated to the new modular structure:

#### services/ (7 files)

- `the_alchemiser/execution/services/__init__.py`
- `the_alchemiser/shared/services/tick_size_service.py`
- `the_alchemiser/shared/services/websocket_connection_manager.py`
- `the_alchemiser/shared/services/real_time_pricing.py`
- `the_alchemiser/shared/services/alert_service.py`
- ... and 2 more files

#### utils/ (20 files)

- `the_alchemiser/utils/__init__.py`
- `the_alchemiser/utils/serialization.py`
- `the_alchemiser/shared/utils/error_reporter.py`
- `the_alchemiser/shared/utils/account_utils.py`
- `the_alchemiser/shared/utils/error_recovery.py`
- ... and 15 more files

## Recommended Implementation Order

1. **Start with backup file removal** (zero risk)
2. **Clean deprecated comments** (documentation cleanup)
3. **Analyze shim dependencies** (prepare for import migration)
4. **Migrate legacy structure files** (requires careful planning)
5. **Remove shims after import migration** (final cleanup)

## Safety Recommendations

- Always test after each phase
- Use version control for easy rollback
- Consider creating a staging branch for cleanup work
- Run import-linter to validate module boundaries
- Update documentation as you go

---
*Generated by legacy_cleanup_helper.py*