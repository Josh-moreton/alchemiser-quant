# Shared Module Consolidation Opportunities

## Executive Summary

This analysis identifies functionality currently duplicated across the strategy, portfolio, and execution modules that could be consolidated into the shared module to improve code reuse and reduce duplication.

## Duplicate Pattern Analysis

The following patterns appear frequently across multiple modules and may indicate opportunities for shared utilities:


### Error Handling Pattern

**Modules affected**: execution, portfolio, strategy
**Total files with pattern**: 87

**Top files by usage**:
- `the_alchemiser/execution/errors/classifier.py` (execution) - 337 occurrences
- `the_alchemiser/portfolio/pnl/strategy_order_tracker.py` (portfolio) - 286 occurrences
- `the_alchemiser/execution/brokers/alpaca/adapter.py` (execution) - 177 occurrences
- `the_alchemiser/execution/strategies/smart_execution.py` (execution) - 155 occurrences
- `the_alchemiser/portfolio/holdings/position_manager.py` (portfolio) - 152 occurrences

**Recommendation**: Consider creating shared utilities for common error handling functionality.


### Logging Pattern

**Modules affected**: execution, portfolio, strategy
**Total files with pattern**: 84

**Top files by usage**:
- `the_alchemiser/portfolio/pnl/strategy_order_tracker.py` (portfolio) - 269 occurrences
- `the_alchemiser/execution/errors/classifier.py` (execution) - 212 occurrences
- `the_alchemiser/strategy/engines/core/trading_engine.py` (strategy) - 209 occurrences
- `the_alchemiser/execution/strategies/smart_execution.py` (execution) - 205 occurrences
- `the_alchemiser/portfolio/holdings/position_manager.py` (portfolio) - 152 occurrences

**Recommendation**: Consider creating shared utilities for common logging functionality.


### Validation Pattern

**Modules affected**: execution, portfolio, strategy
**Total files with pattern**: 13

**Top files by usage**:
- `the_alchemiser/portfolio/schemas/tracking.py` (portfolio) - 15 occurrences
- `the_alchemiser/execution/orders/schemas.py` (execution) - 15 occurrences
- `the_alchemiser/strategy/validation/indicator_validator.py` (strategy) - 13 occurrences
- `the_alchemiser/execution/core/execution_schemas.py` (execution) - 11 occurrences
- `the_alchemiser/execution/orders/service.py` (execution) - 10 occurrences

**Recommendation**: Consider creating shared utilities for common validation functionality.


### Formatting Pattern

**Modules affected**: execution, portfolio, strategy
**Total files with pattern**: 66

**Top files by usage**:
- `the_alchemiser/execution/errors/classifier.py` (execution) - 78 occurrences
- `the_alchemiser/execution/brokers/alpaca/adapter.py` (execution) - 66 occurrences
- `the_alchemiser/portfolio/pnl/strategy_order_tracker.py` (portfolio) - 60 occurrences
- `the_alchemiser/strategy/dsl/evaluator.py` (strategy) - 48 occurrences
- `the_alchemiser/execution/strategies/smart_execution.py` (execution) - 46 occurrences

**Recommendation**: Consider creating shared utilities for common formatting functionality.


### Calculation Pattern

**Modules affected**: execution, portfolio, strategy
**Total files with pattern**: 10

**Top files by usage**:
- `the_alchemiser/strategy/engines/klm/engine.py` (strategy) - 13 occurrences
- `the_alchemiser/portfolio/allocation/portfolio_rebalancing_service.py` (portfolio) - 10 occurrences
- `the_alchemiser/portfolio/allocation/rebalance_calculator.py` (portfolio) - 7 occurrences
- `the_alchemiser/portfolio/core/portfolio_management_facade.py` (portfolio) - 7 occurrences
- `the_alchemiser/strategy/engines/nuclear/engine.py` (strategy) - 6 occurrences

**Recommendation**: Consider creating shared utilities for common calculation functionality.


### Conversion Pattern

**Modules affected**: execution, portfolio, strategy
**Total files with pattern**: 37

**Top files by usage**:
- `the_alchemiser/execution/lifecycle/observers.py` (execution) - 37 occurrences
- `the_alchemiser/portfolio/mappers/portfolio_rebalancing_mapping.py` (portfolio) - 30 occurrences
- `the_alchemiser/portfolio/pnl/strategy_order_tracker.py` (portfolio) - 27 occurrences
- `the_alchemiser/strategy/data/domain_mapping.py` (strategy) - 24 occurrences
- `the_alchemiser/portfolio/allocation/rebalance_execution_service.py` (portfolio) - 24 occurrences

**Recommendation**: Consider creating shared utilities for common conversion functionality.


### Config Pattern

**Modules affected**: execution, portfolio, strategy
**Total files with pattern**: 26

**Top files by usage**:
- `the_alchemiser/execution/config/execution_config.py` (execution) - 60 occurrences
- `the_alchemiser/strategy/registry/strategy_registry.py` (strategy) - 43 occurrences
- `the_alchemiser/strategy/dsl/optimization_config.py` (strategy) - 34 occurrences
- `the_alchemiser/strategy/engines/core/trading_engine.py` (strategy) - 25 occurrences
- `the_alchemiser/execution/strategies/smart_execution.py` (execution) - 23 occurrences

**Recommendation**: Consider creating shared utilities for common config functionality.


### Utils Pattern

**Modules affected**: execution, portfolio, strategy
**Total files with pattern**: 12

**Top files by usage**:
- `the_alchemiser/strategy/engines/klm/base_variant.py` (strategy) - 10 occurrences
- `the_alchemiser/strategy/engines/core/trading_engine.py` (strategy) - 9 occurrences
- `the_alchemiser/portfolio/utils/portfolio_utilities.py` (portfolio) - 9 occurrences
- `the_alchemiser/portfolio/core/portfolio_analysis_service.py` (portfolio) - 9 occurrences
- `the_alchemiser/portfolio/calculations/portfolio_calculations.py` (portfolio) - 8 occurrences

**Recommendation**: Consider creating shared utilities for common utils functionality.


### Cache Pattern

**Modules affected**: portfolio, strategy
**Total files with pattern**: 6

**Top files by usage**:
- `the_alchemiser/strategy/dsl/evaluator.py` (strategy) - 78 occurrences
- `the_alchemiser/strategy/data/market_data_service.py` (strategy) - 49 occurrences
- `the_alchemiser/portfolio/pnl/strategy_order_tracker.py` (portfolio) - 32 occurrences
- `the_alchemiser/strategy/dsl/evaluator_cache.py` (strategy) - 15 occurrences
- `the_alchemiser/strategy/dsl/interning.py` (strategy) - 9 occurrences

**Recommendation**: Consider creating shared utilities for common cache functionality.


## Duplicate Function Analysis

The following functions appear in multiple modules with the same name, indicating potential duplication:


### Function: `validate_symbol()`

**Found in modules**: execution, strategy
**Occurrences**:
- `the_alchemiser/strategy/validation/indicator_validator.py` (strategy)
- `the_alchemiser/execution/orders/schemas.py` (execution)
- `the_alchemiser/execution/core/execution_schemas.py` (execution)
- `the_alchemiser/execution/schemas/alpaca.py` (execution)

**Recommendation**: Review these implementations to determine if they can be consolidated into a shared utility.


### Function: `is_long()`

**Found in modules**: portfolio, strategy
**Occurrences**:
- `the_alchemiser/strategy/types/strategy.py` (strategy)
- `the_alchemiser/portfolio/holdings/position_model.py` (portfolio)

**Recommendation**: Review these implementations to determine if they can be consolidated into a shared utility.


### Function: `is_short()`

**Found in modules**: portfolio, strategy
**Occurrences**:
- `the_alchemiser/strategy/types/strategy.py` (strategy)
- `the_alchemiser/portfolio/holdings/position_model.py` (portfolio)

**Recommendation**: Review these implementations to determine if they can be consolidated into a shared utility.


### Function: `is_profitable()`

**Found in modules**: portfolio, strategy
**Occurrences**:
- `the_alchemiser/strategy/types/strategy.py` (strategy)
- `the_alchemiser/portfolio/holdings/position_model.py` (portfolio)

**Recommendation**: Review these implementations to determine if they can be consolidated into a shared utility.


### Function: `get_account_info()`

**Found in modules**: execution, strategy
**Occurrences**:
- `the_alchemiser/strategy/engines/core/trading_engine.py` (strategy)
- `the_alchemiser/strategy/engines/core/trading_engine.py` (strategy)
- `the_alchemiser/execution/core/account_facade.py` (execution)
- `the_alchemiser/execution/brokers/account_service.py` (execution)

**Recommendation**: Review these implementations to determine if they can be consolidated into a shared utility.


### Function: `get_positions_dict()`

**Found in modules**: execution, strategy
**Occurrences**:
- `the_alchemiser/strategy/engines/core/trading_engine.py` (strategy)
- `the_alchemiser/strategy/engines/core/trading_engine.py` (strategy)
- `the_alchemiser/execution/core/account_facade.py` (execution)
- `the_alchemiser/execution/brokers/account_service.py` (execution)
- `the_alchemiser/execution/brokers/alpaca/adapter.py` (execution)

**Recommendation**: Review these implementations to determine if they can be consolidated into a shared utility.


### Function: `get_current_price()`

**Found in modules**: execution, portfolio, strategy
**Occurrences**:
- `the_alchemiser/strategy/engines/core/trading_engine.py` (strategy)
- `the_alchemiser/strategy/engines/core/trading_engine.py` (strategy)
- `the_alchemiser/strategy/data/streaming_service.py` (strategy)
- `the_alchemiser/strategy/data/streaming_service.py` (strategy)
- `the_alchemiser/strategy/mappers/market_data_adapter.py` (strategy)
- `the_alchemiser/portfolio/policies/protocols.py` (portfolio)
- `the_alchemiser/execution/core/account_facade.py` (execution)
- `the_alchemiser/execution/brokers/account_service.py` (execution)
- `the_alchemiser/execution/brokers/alpaca/adapter.py` (execution)
- `the_alchemiser/execution/strategies/smart_execution.py` (execution)

**Recommendation**: Review these implementations to determine if they can be consolidated into a shared utility.


### Function: `get_current_prices()`

**Found in modules**: execution, strategy
**Occurrences**:
- `the_alchemiser/strategy/engines/core/trading_engine.py` (strategy)
- `the_alchemiser/strategy/engines/core/trading_engine.py` (strategy)
- `the_alchemiser/execution/core/account_facade.py` (execution)
- `the_alchemiser/execution/brokers/account_service.py` (execution)
- `the_alchemiser/execution/brokers/alpaca/adapter.py` (execution)

**Recommendation**: Review these implementations to determine if they can be consolidated into a shared utility.


### Function: `rebalance_portfolio()`

**Found in modules**: portfolio, strategy
**Occurrences**:
- `the_alchemiser/strategy/engines/core/trading_engine.py` (strategy)
- `the_alchemiser/strategy/engines/core/trading_engine.py` (strategy)
- `the_alchemiser/portfolio/core/portfolio_management_facade.py` (portfolio)

**Recommendation**: Review these implementations to determine if they can be consolidated into a shared utility.


### Function: `execute_multi_strategy()`

**Found in modules**: execution, strategy
**Occurrences**:
- `the_alchemiser/strategy/engines/core/trading_engine.py` (strategy)
- `the_alchemiser/strategy/engines/core/trading_engine.py` (strategy)
- `the_alchemiser/execution/core/manager.py` (execution)

**Recommendation**: Review these implementations to determine if they can be consolidated into a shared utility.


### Function: `get_enriched_account_info()`

**Found in modules**: execution, strategy
**Occurrences**:
- `the_alchemiser/strategy/engines/core/trading_engine.py` (strategy)
- `the_alchemiser/execution/core/account_facade.py` (execution)

**Recommendation**: Review these implementations to determine if they can be consolidated into a shared utility.


### Function: `get_positions()`

**Found in modules**: execution, strategy
**Occurrences**:
- `the_alchemiser/strategy/engines/core/trading_engine.py` (strategy)
- `the_alchemiser/execution/core/account_facade.py` (execution)
- `the_alchemiser/execution/brokers/alpaca/adapter.py` (execution)

**Recommendation**: Review these implementations to determine if they can be consolidated into a shared utility.


### Function: `wait_for_settlement()`

**Found in modules**: execution, strategy
**Occurrences**:
- `the_alchemiser/strategy/engines/core/trading_engine.py` (strategy)
- `the_alchemiser/execution/strategies/smart_execution.py` (execution)

**Recommendation**: Review these implementations to determine if they can be consolidated into a shared utility.


### Function: `place_order()`

**Found in modules**: execution, strategy
**Occurrences**:
- `the_alchemiser/strategy/engines/core/trading_engine.py` (strategy)
- `the_alchemiser/execution/brokers/alpaca/adapter.py` (execution)
- `the_alchemiser/execution/strategies/smart_execution.py` (execution)

**Recommendation**: Review these implementations to determine if they can be consolidated into a shared utility.


### Function: `execute_rebalancing()`

**Found in modules**: portfolio, strategy
**Occurrences**:
- `the_alchemiser/strategy/engines/core/trading_engine.py` (strategy)
- `the_alchemiser/portfolio/core/portfolio_management_facade.py` (portfolio)

**Recommendation**: Review these implementations to determine if they can be consolidated into a shared utility.


### Function: `get_latest_quote()`

**Found in modules**: execution, strategy
**Occurrences**:
- `the_alchemiser/strategy/data/market_data_service.py` (strategy)
- `the_alchemiser/strategy/data/market_data_client.py` (strategy)
- `the_alchemiser/strategy/mappers/market_data_adapter.py` (strategy)
- `the_alchemiser/execution/brokers/alpaca/adapter.py` (execution)
- `the_alchemiser/execution/strategies/execution_context_adapter.py` (execution)
- `the_alchemiser/execution/strategies/aggressive_limit_strategy.py` (execution)
- `the_alchemiser/execution/strategies/smart_execution.py` (execution)

**Recommendation**: Review these implementations to determine if they can be consolidated into a shared utility.


### Function: `get_historical_bars()`

**Found in modules**: execution, strategy
**Occurrences**:
- `the_alchemiser/strategy/data/market_data_client.py` (strategy)
- `the_alchemiser/execution/brokers/alpaca/adapter.py` (execution)

**Recommendation**: Review these implementations to determine if they can be consolidated into a shared utility.


### Function: `get_strategy_config()`

**Found in modules**: execution, strategy
**Occurrences**:
- `the_alchemiser/strategy/registry/strategy_registry.py` (strategy)
- `the_alchemiser/execution/strategies/config.py` (execution)

**Recommendation**: Review these implementations to determine if they can be consolidated into a shared utility.


### Function: `to_dict()`

**Found in modules**: execution, portfolio, strategy
**Occurrences**:
- `the_alchemiser/strategy/dsl/strategy_loader.py` (strategy)
- `the_alchemiser/strategy/dsl/optimization_config.py` (strategy)
- `the_alchemiser/portfolio/holdings/position_model.py` (portfolio)
- `the_alchemiser/execution/errors/order_error.py` (execution)
- `the_alchemiser/execution/lifecycle/exceptions.py` (execution)

**Recommendation**: Review these implementations to determine if they can be consolidated into a shared utility.


### Function: `get_portfolio_value()`

**Found in modules**: execution, portfolio
**Occurrences**:
- `the_alchemiser/portfolio/utils/portfolio_utilities.py` (portfolio)
- `the_alchemiser/execution/core/refactored_execution_manager.py` (execution)
- `the_alchemiser/execution/core/data_transformation_service.py` (execution)
- `the_alchemiser/execution/brokers/alpaca/adapter.py` (execution)

**Recommendation**: Review these implementations to determine if they can be consolidated into a shared utility.


### Function: `from_dict()`

**Found in modules**: execution, portfolio
**Occurrences**:
- `the_alchemiser/portfolio/holdings/position_model.py` (portfolio)
- `the_alchemiser/execution/mappers/order_domain_mappers.py` (execution)

**Recommendation**: Review these implementations to determine if they can be consolidated into a shared utility.


### Function: `get_current_positions()`

**Found in modules**: execution, portfolio
**Occurrences**:
- `the_alchemiser/portfolio/holdings/position_manager.py` (portfolio)
- `the_alchemiser/portfolio/core/portfolio_management_facade.py` (portfolio)
- `the_alchemiser/execution/brokers/alpaca/adapter.py` (execution)
- `the_alchemiser/execution/strategies/smart_execution.py` (execution)

**Recommendation**: Review these implementations to determine if they can be consolidated into a shared utility.


### Function: `execute_liquidation()`

**Found in modules**: execution, portfolio
**Occurrences**:
- `the_alchemiser/portfolio/holdings/position_manager.py` (portfolio)
- `the_alchemiser/execution/strategies/smart_execution.py` (execution)

**Recommendation**: Review these implementations to determine if they can be consolidated into a shared utility.


### Function: `cancel_all_orders()`

**Found in modules**: execution, portfolio
**Occurrences**:
- `the_alchemiser/portfolio/holdings/position_manager.py` (portfolio)
- `the_alchemiser/execution/brokers/alpaca/adapter.py` (execution)

**Recommendation**: Review these implementations to determine if they can be consolidated into a shared utility.


### Function: `is_buy()`

**Found in modules**: execution, portfolio
**Occurrences**:
- `the_alchemiser/portfolio/holdings/position_delta.py` (portfolio)
- `the_alchemiser/execution/orders/schemas.py` (execution)

**Recommendation**: Review these implementations to determine if they can be consolidated into a shared utility.


### Function: `is_sell()`

**Found in modules**: execution, portfolio
**Occurrences**:
- `the_alchemiser/portfolio/holdings/position_delta.py` (portfolio)
- `the_alchemiser/execution/orders/schemas.py` (execution)

**Recommendation**: Review these implementations to determine if they can be consolidated into a shared utility.


### Function: `dto_to_domain_order_request()`

**Found in modules**: execution, portfolio
**Occurrences**:
- `the_alchemiser/portfolio/mappers/policy_mapping.py` (portfolio)
- `the_alchemiser/execution/examples/canonical_integration.py` (execution)

**Recommendation**: Review these implementations to determine if they can be consolidated into a shared utility.


### Function: `get_account()`

**Found in modules**: execution, portfolio
**Occurrences**:
- `the_alchemiser/portfolio/policies/protocols.py` (portfolio)
- `the_alchemiser/execution/brokers/alpaca/adapter.py` (execution)

**Recommendation**: Review these implementations to determine if they can be consolidated into a shared utility.


### Function: `get_all_positions()`

**Found in modules**: execution, portfolio
**Occurrences**:
- `the_alchemiser/portfolio/policies/protocols.py` (portfolio)
- `the_alchemiser/execution/core/refactored_execution_manager.py` (execution)
- `the_alchemiser/execution/core/data_transformation_service.py` (execution)
- `the_alchemiser/execution/brokers/alpaca/adapter.py` (execution)

**Recommendation**: Review these implementations to determine if they can be consolidated into a shared utility.


### Function: `normalize_symbol()`

**Found in modules**: execution, portfolio
**Occurrences**:
- `the_alchemiser/portfolio/schemas/tracking.py` (portfolio)
- `the_alchemiser/execution/orders/consolidated_validation.py` (execution)

**Recommendation**: Review these implementations to determine if they can be consolidated into a shared utility.


## Consolidation Recommendations

### High Priority Consolidation Candidates

Based on the analysis, the following areas show the highest potential for consolidation:


**1. Logging Utilities**
- Appears in 3 modules
- 3676 total occurrences across 84 files
- **Action**: Create `shared/utils/logging_utils.py`


**2. Error Handling Utilities**
- Appears in 3 modules
- 3570 total occurrences across 87 files
- **Action**: Create `shared/utils/error_handling_utils.py`


**3. Formatting Utilities**
- Appears in 3 modules
- 1306 total occurrences across 66 files
- **Action**: Create `shared/utils/formatting_utils.py`


**4. Conversion Utilities**
- Appears in 3 modules
- 493 total occurrences across 37 files
- **Action**: Create `shared/utils/conversion_utils.py`


**5. Config Utilities**
- Appears in 3 modules
- 432 total occurrences across 26 files
- **Action**: Create `shared/utils/config_utils.py`


### Missing Shared Utilities

The analysis suggests these shared utilities are needed but don't currently exist:

1. **Error Handling Utilities** - Standardize error handling patterns
2. **Validation Utilities** - Common validation logic
3. **Calculation Utilities** - Mathematical operations
4. **Formatting Utilities** - Data formatting and display
5. **Retry Utilities** - Standardized retry mechanisms

### Implementation Plan

1. **Phase 1**: Create high-priority shared utilities
2. **Phase 2**: Migrate duplicate implementations to use shared utilities
3. **Phase 3**: Remove now-redundant module-specific implementations
4. **Phase 4**: Add comprehensive tests for shared utilities

---

*Generated by Shared Module Consolidation Analysis*
