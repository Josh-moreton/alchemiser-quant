# Shims & Compatibility Layers Audit Report

## Executive Summary

This report provides a comprehensive audit of all shims, compatibility layers, and backward-compatibility code in the codebase. The audit identified **196 potential items** requiring review.

**Risk Distribution:**
- 🔴 **High Risk**: 124 items
- 🟡 **Medium Risk**: 65 items
- 🟢 **Low Risk**: 7 items

## Summary by Category

### Other Compatibility (116 items)

- `scripts/audit_shims_compatibility.py` - File with *shim* pattern in name
- `scripts/audit_shims_compatibility.py` - File with *compat* pattern in name
- `the_alchemiser/execution/orders/lifecycle_adapter.py` - File with *adapter* pattern in name
- `the_alchemiser/execution/strategies/execution_context_adapter.py` - File with *adapter* pattern in name
- `the_alchemiser/execution/brokers/alpaca/adapter.py` - File with *adapter* pattern in name
- `the_alchemiser/strategy/mappers/market_data_adapter.py` - File with *adapter* pattern in name
- `the_alchemiser/shared/adapters/portfolio_adapters.py` - File with *adapter* pattern in name
- `the_alchemiser/shared/adapters/execution_adapters.py` - File with *adapter* pattern in name
- `the_alchemiser/shared/adapters/strategy_adapters.py` - File with *adapter* pattern in name
- `scripts/migrate_phase2_imports.py` - Contains compatibility/shim keywords: adapter
- `scripts/delete_legacy_safe.py` - Contains compatibility/shim keywords: adapter
- `scripts/audit_shims_compatibility.py` - Contains compatibility/shim keywords: shim, compatibility, backward, compat, polyfill, adapter, wrapper, bridge
- `the_alchemiser/main.py` - Contains compatibility/shim keywords: compatibility, backward, compat
- `the_alchemiser/lambda_handler.py` - Contains compatibility/shim keywords: compatibility, backward, compat
- `the_alchemiser/execution/__init__.py` - Contains compatibility/shim keywords: adapter
- `the_alchemiser/shared/dto_communication_demo.py` - Contains compatibility/shim keywords: adapter
- `the_alchemiser/shared/simple_dto_test.py` - Contains compatibility/shim keywords: adapter
- `the_alchemiser/execution/orders/order_schemas.py` - Contains compatibility/shim keywords: compatibility, backward, compat
- `the_alchemiser/execution/orders/validation.py` - Contains compatibility/shim keywords: compatibility, compat
- `the_alchemiser/execution/orders/asset_order_handler.py` - Contains compatibility/shim keywords: compatibility, backward, compat
- `the_alchemiser/execution/orders/lifecycle_adapter.py` - Contains compatibility/shim keywords: adapter
- `the_alchemiser/execution/protocols/trading_repository.py` - Contains compatibility/shim keywords: adapter
- `the_alchemiser/execution/core/execution_manager.py` - Contains compatibility/shim keywords: compatibility, backward, compat
- `the_alchemiser/execution/core/execution_manager_legacy.py` - Contains compatibility/shim keywords: shim, compatibility, backward, compat
- `the_alchemiser/execution/core/execution_schemas.py` - Contains compatibility/shim keywords: compatibility, backward, compat
- `the_alchemiser/execution/core/account_facade.py` - Contains compatibility/shim keywords: compatibility, backward, compat
- `the_alchemiser/execution/core/canonical_executor.py` - Contains compatibility/shim keywords: shim, compatibility, backward, compat
- `the_alchemiser/execution/mappers/execution.py` - Contains compatibility/shim keywords: adapter
- `the_alchemiser/execution/mappers/orders.py` - Contains compatibility/shim keywords: compatibility, backward, compat
- `the_alchemiser/execution/brokers/__init__.py` - Contains compatibility/shim keywords: adapter
- `the_alchemiser/execution/brokers/account_service.py` - Contains compatibility/shim keywords: compatibility, compat
- `the_alchemiser/execution/brokers/alpaca_client.py` - Contains compatibility/shim keywords: compatibility, backward, compat, wrapper
- `the_alchemiser/execution/strategies/execution_context_adapter.py` - Contains compatibility/shim keywords: compatibility, compat, adapter, bridge
- `the_alchemiser/execution/strategies/__init__.py` - Contains compatibility/shim keywords: adapter
- `the_alchemiser/execution/strategies/smart_execution.py` - Contains compatibility/shim keywords: compatibility, backward, compat, adapter
- `the_alchemiser/execution/lifecycle/observers.py` - Contains compatibility/shim keywords: compatibility, backward, compat
- `the_alchemiser/execution/brokers/alpaca/adapter.py` - Contains compatibility/shim keywords: compatibility, backward, compat, adapter
- `the_alchemiser/execution/brokers/alpaca/__init__.py` - Contains compatibility/shim keywords: adapter
- `the_alchemiser/strategy/engines/tecl_strategy_engine.py` - Contains compatibility/shim keywords: compatibility, backward, compat
- `the_alchemiser/strategy/engines/nuclear_typed_engine.py` - Contains compatibility/shim keywords: compatibility, backward, compat
- `the_alchemiser/strategy/engines/typed_klm_ensemble_engine.py` - Contains compatibility/shim keywords: compatibility, backward, compat
- `the_alchemiser/strategy/data/domain_mapping.py` - Contains compatibility/shim keywords: compatibility, backward, compat
- `the_alchemiser/strategy/data/market_data_service.py` - Contains compatibility/shim keywords: compatibility, compat
- `the_alchemiser/strategy/data/strategy_market_data_service.py` - Contains compatibility/shim keywords: compatibility, backward, compat, adapter
- `the_alchemiser/strategy/mappers/market_data_adapter.py` - Contains compatibility/shim keywords: compatibility, compat, adapter, bridge
- `the_alchemiser/strategy/mappers/__init__.py` - Contains compatibility/shim keywords: adapter
- `the_alchemiser/strategy/mappers/market_data_mapping.py` - Contains compatibility/shim keywords: compatibility, backward, compat
- `the_alchemiser/strategy/schemas/strategies.py` - Contains compatibility/shim keywords: compatibility, backward, compat, adapter
- `the_alchemiser/strategy/indicators/indicators.py` - Contains compatibility/shim keywords: compatibility, compat
- `the_alchemiser/strategy/dsl/evaluator.py` - Contains compatibility/shim keywords: backward, compat, wrapper
- `the_alchemiser/strategy/dsl/parser.py` - Contains compatibility/shim keywords: compatibility, compat, wrapper
- `the_alchemiser/strategy/engines/protocols/__init__.py` - Contains compatibility/shim keywords: adapter
- `the_alchemiser/strategy/engines/core/trading_engine.py` - Contains compatibility/shim keywords: compatibility, backward, compat, adapter, bridge
- `the_alchemiser/strategy/engines/models/strategy_position_model.py` - Contains compatibility/shim keywords: compatibility, backward, compat
- `the_alchemiser/shared/adapters/portfolio_adapters.py` - Contains compatibility/shim keywords: adapter
- `the_alchemiser/shared/adapters/execution_adapters.py` - Contains compatibility/shim keywords: adapter
- `the_alchemiser/shared/adapters/__init__.py` - Contains compatibility/shim keywords: adapter
- `the_alchemiser/shared/adapters/integration_helpers.py` - Contains compatibility/shim keywords: adapter
- `the_alchemiser/shared/adapters/strategy_adapters.py` - Contains compatibility/shim keywords: adapter
- `the_alchemiser/shared/utils/account_utils.py` - Contains compatibility/shim keywords: compatibility, compat
- `the_alchemiser/shared/utils/error_recovery.py` - Contains compatibility/shim keywords: wrapper
- `the_alchemiser/shared/utils/retry_decorator.py` - Contains compatibility/shim keywords: wrapper
- `the_alchemiser/shared/utils/service_factory.py` - Contains compatibility/shim keywords: compatibility, backward, compat
- `the_alchemiser/shared/utils/error_handling.py` - Contains compatibility/shim keywords: compatibility, backward, compat
- `the_alchemiser/shared/utils/decorators.py` - Contains compatibility/shim keywords: wrapper
- `the_alchemiser/shared/services/real_time_pricing.py` - Contains compatibility/shim keywords: compatibility, backward, compat
- `the_alchemiser/shared/errors/error_handler.py` - Contains compatibility/shim keywords: compatibility, backward, compat, wrapper
- `the_alchemiser/shared/config/service_providers.py` - Contains compatibility/shim keywords: compatibility, backward, compat
- `the_alchemiser/shared/config/infrastructure_providers.py` - Contains compatibility/shim keywords: compatibility, backward, compat
- `the_alchemiser/shared/config/bootstrap.py` - Contains compatibility/shim keywords: compatibility, backward, compat, adapter
- `the_alchemiser/shared/protocols/trading.py` - Contains compatibility/shim keywords: adapter
- `the_alchemiser/shared/protocols/repository.py` - Contains compatibility/shim keywords: compatibility, backward, compat
- `the_alchemiser/shared/cli/signal_display_utils.py` - Contains compatibility/shim keywords: compatibility, compat
- `the_alchemiser/shared/cli/signal_analyzer.py` - Contains compatibility/shim keywords: compatibility, compat, adapter
- `the_alchemiser/shared/cli/cli.py` - Contains compatibility/shim keywords: compatibility, compat, adapter
- `the_alchemiser/shared/value_objects/core_types.py` - Contains compatibility/shim keywords: compatibility, backward, compat
- `the_alchemiser/shared/mappers/execution_summary_mapping.py` - Contains compatibility/shim keywords: compatibility, backward, compat
- `the_alchemiser/shared/notifications/email_utils.py` - Contains compatibility/shim keywords: compatibility, backward, compat
- `the_alchemiser/shared/notifications/config.py` - Contains compatibility/shim keywords: compatibility, backward, compat
- `the_alchemiser/shared/notifications/client.py` - Contains compatibility/shim keywords: compatibility, backward, compat
- `the_alchemiser/shared/logging/logging_utils.py` - Contains compatibility/shim keywords: adapter
- `the_alchemiser/shared/schemas/base.py` - Contains compatibility/shim keywords: compatibility, backward, compat
- `the_alchemiser/shared/schemas/execution_summary.py` - Contains compatibility/shim keywords: compatibility, backward, compat
- `the_alchemiser/shared/schemas/accounts.py` - Contains compatibility/shim keywords: compatibility, backward, compat
- `the_alchemiser/shared/schemas/enriched_data.py` - Contains compatibility/shim keywords: compatibility, backward, compat
- `the_alchemiser/shared/schemas/operations.py` - Contains compatibility/shim keywords: compatibility, backward, compat
- `the_alchemiser/shared/schemas/market_data.py` - Contains compatibility/shim keywords: compatibility, backward, compat
- `the_alchemiser/shared/notifications/templates/base.py` - Contains compatibility/shim keywords: compat
- `the_alchemiser/shared/notifications/templates/error_report.py` - Contains compatibility/shim keywords: compat
- `the_alchemiser/portfolio/execution/execution_service.py` - Contains compatibility/shim keywords: shim, compatibility, backward, compat
- `the_alchemiser/portfolio/utils/portfolio_pnl_utils.py` - Contains compatibility/shim keywords: shim, compatibility, backward, compat
- `the_alchemiser/portfolio/pnl/strategy_order_tracker.py` - Contains compatibility/shim keywords: compatibility, backward, compat
- `the_alchemiser/portfolio/holdings/position_manager.py` - Contains compatibility/shim keywords: compatibility, backward, compat
- `the_alchemiser/portfolio/rebalancing/rebalance_plan.py` - Contains compatibility/shim keywords: shim, compatibility, backward, compat
- `the_alchemiser/portfolio/rebalancing/orchestrator.py` - Contains compatibility/shim keywords: shim, compatibility, backward, compat
- `the_alchemiser/portfolio/rebalancing/rebalancing_service.py` - Contains compatibility/shim keywords: shim, compatibility, backward, compat
- `the_alchemiser/portfolio/rebalancing/orchestrator_facade.py` - Contains compatibility/shim keywords: shim, compatibility, backward, compat
- `the_alchemiser/portfolio/calculations/portfolio_calculations.py` - Contains compatibility/shim keywords: compat
- `the_alchemiser/portfolio/tracking/integration.py` - Contains compatibility/shim keywords: wrapper
- `the_alchemiser/portfolio/allocation/portfolio_rebalancing_service.py` - Contains compatibility/shim keywords: adapter
- `the_alchemiser/portfolio/core/portfolio_management_facade.py` - Contains compatibility/shim keywords: compat
- `the_alchemiser/portfolio/core/rebalancing_orchestrator_facade.py` - Contains compatibility/shim keywords: compatibility, backward, compat
- `the_alchemiser/portfolio/mappers/portfolio_rebalancing_mapping.py` - Contains compatibility/shim keywords: compatibility, backward, compat
- `the_alchemiser/portfolio/analytics/analysis_service.py` - Contains compatibility/shim keywords: shim, compatibility, backward, compat
- `the_alchemiser/portfolio/analytics/position_analyzer.py` - Contains compatibility/shim keywords: shim, compatibility, backward, compat
- `the_alchemiser/portfolio/analytics/position_delta.py` - Contains compatibility/shim keywords: shim, compatibility, backward, compat
- `the_alchemiser/portfolio/analytics/attribution_engine.py` - Contains compatibility/shim keywords: shim, compatibility, backward, compat
- `the_alchemiser/portfolio/positions/position_service.py` - Contains compatibility/shim keywords: shim, compatibility, backward, compat
- `the_alchemiser/portfolio/positions/legacy_position_manager.py` - Contains compatibility/shim keywords: shim, compatibility, backward, compat
- `the_alchemiser/portfolio/policies/fractionability_policy_impl.py` - Contains compatibility/shim keywords: compatibility, compat
- `the_alchemiser/portfolio/schemas/tracking.py` - Contains compatibility/shim keywords: compatibility, compat
- `the_alchemiser/portfolio/schemas/positions.py` - Contains compatibility/shim keywords: compatibility, backward, compat
- `the_alchemiser/portfolio/state/symbol_classifier.py` - Contains compatibility/shim keywords: compatibility, backward, compat
- `the_alchemiser/portfolio/state/attribution_engine.py` - Contains compatibility/shim keywords: compatibility, backward, compat
- `scripts/audit_shims_compatibility.py` - Contains polyfill or environment-specific compatibility code
- `the_alchemiser/__init__.py` - Contains polyfill or environment-specific compatibility code

### Legacy Code (5 items)

- `scripts/rollback_legacy_deletions.py` - File with *legacy* pattern in name
- `scripts/delete_legacy_safe.py` - File with *legacy* pattern in name
- `the_alchemiser/execution/core/execution_manager_legacy.py` - File with *legacy* pattern in name
- `the_alchemiser/shared/types/symbol_legacy.py` - File with *legacy* pattern in name
- `the_alchemiser/portfolio/positions/legacy_position_manager.py` - File with *legacy* pattern in name

### Deprecated Code (30 items)

- `scripts/audit_shims_compatibility.py` - Contains deprecation warnings or removal notices
- `the_alchemiser/main.py` - Contains deprecation warnings or removal notices
- `the_alchemiser/execution/orders/asset_order_handler.py` - Contains deprecation warnings or removal notices
- `the_alchemiser/execution/mappers/orders.py` - Contains deprecation warnings or removal notices
- `the_alchemiser/execution/brokers/alpaca_client.py` - Contains deprecation warnings or removal notices
- `the_alchemiser/strategy/data/shared_market_data_service.py` - Contains deprecation warnings or removal notices
- `the_alchemiser/strategy/engines/protocols/__init__.py` - Contains deprecation warnings or removal notices
- `the_alchemiser/strategy/engines/klm_workers/variant_530_18.py` - Contains deprecation warnings or removal notices
- `the_alchemiser/strategy/engines/klm_workers/variant_1280_26.py` - Contains deprecation warnings or removal notices
- `the_alchemiser/shared/utils/__init__.py` - Contains deprecation warnings or removal notices
- `the_alchemiser/shared/utils/error_handling.py` - Contains deprecation warnings or removal notices
- `the_alchemiser/shared/cli/cli.py` - Contains deprecation warnings or removal notices
- `the_alchemiser/shared/cli/trading_executor.py` - Contains deprecation warnings or removal notices
- `the_alchemiser/portfolio/execution/execution_service.py` - Contains deprecation warnings or removal notices
- `the_alchemiser/portfolio/utils/portfolio_pnl_utils.py` - Contains deprecation warnings or removal notices
- `the_alchemiser/portfolio/holdings/position_manager.py` - Contains deprecation warnings or removal notices
- `the_alchemiser/portfolio/rebalancing/rebalance_plan.py` - Contains deprecation warnings or removal notices
- `the_alchemiser/portfolio/rebalancing/orchestrator.py` - Contains deprecation warnings or removal notices
- `the_alchemiser/portfolio/rebalancing/rebalancing_service.py` - Contains deprecation warnings or removal notices
- `the_alchemiser/portfolio/rebalancing/orchestrator_facade.py` - Contains deprecation warnings or removal notices
- `the_alchemiser/portfolio/analytics/analysis_service.py` - Contains deprecation warnings or removal notices
- `the_alchemiser/portfolio/analytics/position_analyzer.py` - Contains deprecation warnings or removal notices
- `the_alchemiser/portfolio/analytics/position_delta.py` - Contains deprecation warnings or removal notices
- `the_alchemiser/portfolio/analytics/attribution_engine.py` - Contains deprecation warnings or removal notices
- `the_alchemiser/portfolio/positions/position_service.py` - Contains deprecation warnings or removal notices
- `the_alchemiser/portfolio/positions/legacy_position_manager.py` - Contains deprecation warnings or removal notices
- `scripts/audit_shims_compatibility.py` - File marked with legacy/deprecated status
- `examples/policy_layer_usage.py` - File marked with legacy/deprecated status
- `the_alchemiser/execution/core/execution_manager_legacy.py` - File marked with legacy/deprecated status
- `the_alchemiser/execution/core/canonical_executor.py` - File marked with legacy/deprecated status

### Import Redirections (43 items)

- `scripts/migrate_phase2_imports.py` - Contains import redirections or compatibility imports
- `scripts/audit_shims_compatibility.py` - Contains import redirections or compatibility imports
- `the_alchemiser/execution/orders/order_validation_utils.py` - Contains import redirections or compatibility imports
- `the_alchemiser/execution/orders/order_schemas.py` - Contains import redirections or compatibility imports
- `the_alchemiser/execution/orders/validation.py` - Contains import redirections or compatibility imports
- `the_alchemiser/execution/orders/asset_order_handler.py` - Contains import redirections or compatibility imports
- `the_alchemiser/execution/orders/lifecycle_adapter.py` - Contains import redirections or compatibility imports
- `the_alchemiser/execution/core/execution_manager_legacy.py` - Contains import redirections or compatibility imports
- `the_alchemiser/execution/core/execution_schemas.py` - Contains import redirections or compatibility imports
- `the_alchemiser/execution/core/canonical_executor.py` - Contains import redirections or compatibility imports
- `the_alchemiser/execution/brokers/alpaca_client.py` - Contains import redirections or compatibility imports
- `the_alchemiser/execution/examples/canonical_integration.py` - Contains import redirections or compatibility imports
- `the_alchemiser/execution/strategies/execution_context_adapter.py` - Contains import redirections or compatibility imports
- `the_alchemiser/execution/strategies/smart_execution.py` - Contains import redirections or compatibility imports
- `the_alchemiser/shared/utils/__init__.py` - Contains import redirections or compatibility imports
- `the_alchemiser/shared/utils/service_factory.py` - Contains import redirections or compatibility imports
- `the_alchemiser/shared/utils/error_handling.py` - Contains import redirections or compatibility imports
- `the_alchemiser/shared/services/tick_size_service.py` - Contains import redirections or compatibility imports
- `the_alchemiser/shared/config/service_providers.py` - Contains import redirections or compatibility imports
- `the_alchemiser/shared/config/infrastructure_providers.py` - Contains import redirections or compatibility imports
- `the_alchemiser/shared/protocols/trading.py` - Contains import redirections or compatibility imports
- `the_alchemiser/shared/value_objects/core_types.py` - Contains import redirections or compatibility imports
- `the_alchemiser/shared/notifications/email_utils.py` - Contains import redirections or compatibility imports
- `the_alchemiser/shared/schemas/base.py` - Contains import redirections or compatibility imports
- `the_alchemiser/shared/schemas/execution_summary.py` - Contains import redirections or compatibility imports
- `the_alchemiser/shared/schemas/accounts.py` - Contains import redirections or compatibility imports
- `the_alchemiser/shared/schemas/enriched_data.py` - Contains import redirections or compatibility imports
- `the_alchemiser/shared/schemas/operations.py` - Contains import redirections or compatibility imports
- `the_alchemiser/shared/schemas/market_data.py` - Contains import redirections or compatibility imports
- `the_alchemiser/portfolio/execution/execution_service.py` - Contains import redirections or compatibility imports
- `the_alchemiser/portfolio/utils/portfolio_pnl_utils.py` - Contains import redirections or compatibility imports
- `the_alchemiser/portfolio/holdings/position_manager.py` - Contains import redirections or compatibility imports
- `the_alchemiser/portfolio/rebalancing/rebalance_plan.py` - Contains import redirections or compatibility imports
- `the_alchemiser/portfolio/rebalancing/orchestrator.py` - Contains import redirections or compatibility imports
- `the_alchemiser/portfolio/rebalancing/rebalancing_service.py` - Contains import redirections or compatibility imports
- `the_alchemiser/portfolio/rebalancing/orchestrator_facade.py` - Contains import redirections or compatibility imports
- `the_alchemiser/portfolio/analytics/analysis_service.py` - Contains import redirections or compatibility imports
- `the_alchemiser/portfolio/analytics/position_analyzer.py` - Contains import redirections or compatibility imports
- `the_alchemiser/portfolio/analytics/position_delta.py` - Contains import redirections or compatibility imports
- `the_alchemiser/portfolio/analytics/attribution_engine.py` - Contains import redirections or compatibility imports
- `the_alchemiser/portfolio/positions/position_service.py` - Contains import redirections or compatibility imports
- `the_alchemiser/portfolio/positions/legacy_position_manager.py` - Contains import redirections or compatibility imports
- `the_alchemiser/portfolio/schemas/positions.py` - Contains import redirections or compatibility imports

### Backup Files (2 items)

- `the_alchemiser/execution/strategies/execution_context_adapter.py.backup` - Backup file with pattern: *.backup
- `the_alchemiser/portfolio/allocation/rebalance_execution_service.py.backup` - Backup file with pattern: *.backup

## Detailed Findings by Risk Level

### 🔴 HIGH RISK (124 items)

**1. symbol_legacy.py**
- **File**: `the_alchemiser/shared/types/symbol_legacy.py`
- **Description**: File with *legacy* pattern in name
- **Purpose**: File named with pattern: *legacy*
- **Suggested Action**: analyze
- **Risk Level**: high
- **Active Imports**: 7 files
- **Evidence**: Filename matches pattern: *legacy*; Actively imported by 7 files

**2. legacy_position_manager.py**
- **File**: `the_alchemiser/portfolio/positions/legacy_position_manager.py`
- **Description**: File with *legacy* pattern in name
- **Purpose**: File named with pattern: *legacy*
- **Suggested Action**: analyze
- **Risk Level**: high
- **Active Imports**: 1 files
- **Evidence**: Filename matches pattern: *legacy*; Actively imported by 1 files

**3. market_data_adapter.py**
- **File**: `the_alchemiser/strategy/mappers/market_data_adapter.py`
- **Description**: File with *adapter* pattern in name
- **Purpose**: File named with pattern: *adapter*
- **Suggested Action**: analyze
- **Risk Level**: high
- **Active Imports**: 2 files
- **Evidence**: Filename matches pattern: *adapter*; Actively imported by 2 files

**4. portfolio_adapters.py**
- **File**: `the_alchemiser/shared/adapters/portfolio_adapters.py`
- **Description**: File with *adapter* pattern in name
- **Purpose**: File named with pattern: *adapter*
- **Suggested Action**: analyze
- **Risk Level**: high
- **Active Imports**: 2 files
- **Evidence**: Filename matches pattern: *adapter*; Actively imported by 2 files

**5. execution_adapters.py**
- **File**: `the_alchemiser/shared/adapters/execution_adapters.py`
- **Description**: File with *adapter* pattern in name
- **Purpose**: File named with pattern: *adapter*
- **Suggested Action**: analyze
- **Risk Level**: high
- **Active Imports**: 2 files
- **Evidence**: Filename matches pattern: *adapter*; Actively imported by 2 files

**6. strategy_adapters.py**
- **File**: `the_alchemiser/shared/adapters/strategy_adapters.py`
- **Description**: File with *adapter* pattern in name
- **Purpose**: File named with pattern: *adapter*
- **Suggested Action**: analyze
- **Risk Level**: high
- **Active Imports**: 2 files
- **Evidence**: Filename matches pattern: *adapter*; Actively imported by 2 files

**7. main.py**
- **File**: `the_alchemiser/main.py`
- **Description**: Contains compatibility/shim keywords: compatibility, backward, compat
- **Purpose**: File contains compatibility-related content
- **Suggested Action**: analyze
- **Risk Level**: high
- **Active Imports**: 4 files
- **Evidence**: Keywords found: compatibility, backward, compat; Actively imported by 4 files

**8. order_schemas.py**
- **File**: `the_alchemiser/execution/orders/order_schemas.py`
- **Description**: Contains compatibility/shim keywords: compatibility, backward, compat
- **Purpose**: File contains compatibility-related content
- **Suggested Action**: analyze
- **Risk Level**: high
- **Active Imports**: 16 files
- **Evidence**: Keywords found: compatibility, backward, compat; Actively imported by 16 files

**9. validation.py**
- **File**: `the_alchemiser/execution/orders/validation.py`
- **Description**: Contains compatibility/shim keywords: compatibility, compat
- **Purpose**: File contains compatibility-related content
- **Suggested Action**: analyze
- **Risk Level**: high
- **Active Imports**: 2 files
- **Evidence**: Keywords found: compatibility, compat; Actively imported by 2 files

**10. asset_order_handler.py**
- **File**: `the_alchemiser/execution/orders/asset_order_handler.py`
- **Description**: Contains compatibility/shim keywords: compatibility, backward, compat
- **Purpose**: File contains compatibility-related content
- **Suggested Action**: analyze
- **Risk Level**: high
- **Active Imports**: 1 files
- **Evidence**: Keywords found: compatibility, backward, compat; Actively imported by 1 files

**11. execution_manager.py**
- **File**: `the_alchemiser/execution/core/execution_manager.py`
- **Description**: Contains compatibility/shim keywords: compatibility, backward, compat
- **Purpose**: File contains compatibility-related content
- **Suggested Action**: analyze
- **Risk Level**: high
- **Active Imports**: 11 files
- **Evidence**: Keywords found: compatibility, backward, compat; Actively imported by 11 files

**12. execution_schemas.py**
- **File**: `the_alchemiser/execution/core/execution_schemas.py`
- **Description**: Contains compatibility/shim keywords: compatibility, backward, compat
- **Purpose**: File contains compatibility-related content
- **Suggested Action**: analyze
- **Risk Level**: high
- **Active Imports**: 12 files
- **Evidence**: Keywords found: compatibility, backward, compat; Actively imported by 12 files

**13. account_facade.py**
- **File**: `the_alchemiser/execution/core/account_facade.py`
- **Description**: Contains compatibility/shim keywords: compatibility, backward, compat
- **Purpose**: File contains compatibility-related content
- **Suggested Action**: analyze
- **Risk Level**: high
- **Active Imports**: 1 files
- **Evidence**: Keywords found: compatibility, backward, compat; Actively imported by 1 files

**14. canonical_executor.py**
- **File**: `the_alchemiser/execution/core/canonical_executor.py`
- **Description**: Contains compatibility/shim keywords: shim, compatibility, backward, compat
- **Purpose**: File contains compatibility-related content
- **Suggested Action**: analyze
- **Risk Level**: high
- **Active Imports**: 6 files
- **Evidence**: Keywords found: shim, compatibility, backward, compat; Actively imported by 6 files

**15. execution.py**
- **File**: `the_alchemiser/execution/mappers/execution.py`
- **Description**: Contains compatibility/shim keywords: adapter
- **Purpose**: File contains compatibility-related content
- **Suggested Action**: analyze
- **Risk Level**: high
- **Active Imports**: 2 files
- **Evidence**: Keywords found: adapter; Actively imported by 2 files

**16. orders.py**
- **File**: `the_alchemiser/execution/mappers/orders.py`
- **Description**: Contains compatibility/shim keywords: compatibility, backward, compat
- **Purpose**: File contains compatibility-related content
- **Suggested Action**: analyze
- **Risk Level**: high
- **Active Imports**: 6 files
- **Evidence**: Keywords found: compatibility, backward, compat; Actively imported by 6 files

**17. account_service.py**
- **File**: `the_alchemiser/execution/brokers/account_service.py`
- **Description**: Contains compatibility/shim keywords: compatibility, compat
- **Purpose**: File contains compatibility-related content
- **Suggested Action**: analyze
- **Risk Level**: high
- **Active Imports**: 6 files
- **Evidence**: Keywords found: compatibility, compat; Actively imported by 6 files

**18. alpaca_client.py**
- **File**: `the_alchemiser/execution/brokers/alpaca_client.py`
- **Description**: Contains compatibility/shim keywords: compatibility, backward, compat, wrapper
- **Purpose**: File contains compatibility-related content
- **Suggested Action**: analyze
- **Risk Level**: high
- **Active Imports**: 2 files
- **Evidence**: Keywords found: compatibility, backward, compat, wrapper; Actively imported by 2 files

**19. smart_execution.py**
- **File**: `the_alchemiser/execution/strategies/smart_execution.py`
- **Description**: Contains compatibility/shim keywords: compatibility, backward, compat, adapter
- **Purpose**: File contains compatibility-related content
- **Suggested Action**: analyze
- **Risk Level**: high
- **Active Imports**: 6 files
- **Evidence**: Keywords found: compatibility, backward, compat, adapter; Actively imported by 6 files

**20. tecl_strategy_engine.py**
- **File**: `the_alchemiser/strategy/engines/tecl_strategy_engine.py`
- **Description**: Contains compatibility/shim keywords: compatibility, backward, compat
- **Purpose**: File contains compatibility-related content
- **Suggested Action**: analyze
- **Risk Level**: high
- **Active Imports**: 2 files
- **Evidence**: Keywords found: compatibility, backward, compat; Actively imported by 2 files

**21. nuclear_typed_engine.py**
- **File**: `the_alchemiser/strategy/engines/nuclear_typed_engine.py`
- **Description**: Contains compatibility/shim keywords: compatibility, backward, compat
- **Purpose**: File contains compatibility-related content
- **Suggested Action**: analyze
- **Risk Level**: high
- **Active Imports**: 2 files
- **Evidence**: Keywords found: compatibility, backward, compat; Actively imported by 2 files

**22. typed_klm_ensemble_engine.py**
- **File**: `the_alchemiser/strategy/engines/typed_klm_ensemble_engine.py`
- **Description**: Contains compatibility/shim keywords: compatibility, backward, compat
- **Purpose**: File contains compatibility-related content
- **Suggested Action**: analyze
- **Risk Level**: high
- **Active Imports**: 3 files
- **Evidence**: Keywords found: compatibility, backward, compat; Actively imported by 3 files

**23. market_data_service.py**
- **File**: `the_alchemiser/strategy/data/market_data_service.py`
- **Description**: Contains compatibility/shim keywords: compatibility, compat
- **Purpose**: File contains compatibility-related content
- **Suggested Action**: analyze
- **Risk Level**: high
- **Active Imports**: 8 files
- **Evidence**: Keywords found: compatibility, compat; Actively imported by 8 files

**24. strategy_market_data_service.py**
- **File**: `the_alchemiser/strategy/data/strategy_market_data_service.py`
- **Description**: Contains compatibility/shim keywords: compatibility, backward, compat, adapter
- **Purpose**: File contains compatibility-related content
- **Suggested Action**: analyze
- **Risk Level**: high
- **Active Imports**: 1 files
- **Evidence**: Keywords found: compatibility, backward, compat, adapter; Actively imported by 1 files

**25. market_data_adapter.py**
- **File**: `the_alchemiser/strategy/mappers/market_data_adapter.py`
- **Description**: Contains compatibility/shim keywords: compatibility, compat, adapter, bridge
- **Purpose**: File contains compatibility-related content
- **Suggested Action**: analyze
- **Risk Level**: high
- **Active Imports**: 2 files
- **Evidence**: Keywords found: compatibility, compat, adapter, bridge; Actively imported by 2 files

**26. market_data_mapping.py**
- **File**: `the_alchemiser/strategy/mappers/market_data_mapping.py`
- **Description**: Contains compatibility/shim keywords: compatibility, backward, compat
- **Purpose**: File contains compatibility-related content
- **Suggested Action**: analyze
- **Risk Level**: high
- **Active Imports**: 4 files
- **Evidence**: Keywords found: compatibility, backward, compat; Actively imported by 4 files

**27. strategies.py**
- **File**: `the_alchemiser/strategy/schemas/strategies.py`
- **Description**: Contains compatibility/shim keywords: compatibility, backward, compat, adapter
- **Purpose**: File contains compatibility-related content
- **Suggested Action**: analyze
- **Risk Level**: high
- **Active Imports**: 2 files
- **Evidence**: Keywords found: compatibility, backward, compat, adapter; Actively imported by 2 files

**28. indicators.py**
- **File**: `the_alchemiser/strategy/indicators/indicators.py`
- **Description**: Contains compatibility/shim keywords: compatibility, compat
- **Purpose**: File contains compatibility-related content
- **Suggested Action**: analyze
- **Risk Level**: high
- **Active Imports**: 5 files
- **Evidence**: Keywords found: compatibility, compat; Actively imported by 5 files

**29. evaluator.py**
- **File**: `the_alchemiser/strategy/dsl/evaluator.py`
- **Description**: Contains compatibility/shim keywords: backward, compat, wrapper
- **Purpose**: File contains compatibility-related content
- **Suggested Action**: analyze
- **Risk Level**: high
- **Active Imports**: 1 files
- **Evidence**: Keywords found: backward, compat, wrapper; Actively imported by 1 files

**30. parser.py**
- **File**: `the_alchemiser/strategy/dsl/parser.py`
- **Description**: Contains compatibility/shim keywords: compatibility, compat, wrapper
- **Purpose**: File contains compatibility-related content
- **Suggested Action**: analyze
- **Risk Level**: high
- **Active Imports**: 2 files
- **Evidence**: Keywords found: compatibility, compat, wrapper; Actively imported by 2 files

**31. trading_engine.py**
- **File**: `the_alchemiser/strategy/engines/core/trading_engine.py`
- **Description**: Contains compatibility/shim keywords: compatibility, backward, compat, adapter, bridge
- **Purpose**: File contains compatibility-related content
- **Suggested Action**: analyze
- **Risk Level**: high
- **Active Imports**: 3 files
- **Evidence**: Keywords found: compatibility, backward, compat, adapter, bridge; Actively imported by 3 files

**32. strategy_position_model.py**
- **File**: `the_alchemiser/strategy/engines/models/strategy_position_model.py`
- **Description**: Contains compatibility/shim keywords: compatibility, backward, compat
- **Purpose**: File contains compatibility-related content
- **Suggested Action**: analyze
- **Risk Level**: high
- **Active Imports**: 1 files
- **Evidence**: Keywords found: compatibility, backward, compat; Actively imported by 1 files

**33. portfolio_adapters.py**
- **File**: `the_alchemiser/shared/adapters/portfolio_adapters.py`
- **Description**: Contains compatibility/shim keywords: adapter
- **Purpose**: File contains compatibility-related content
- **Suggested Action**: analyze
- **Risk Level**: high
- **Active Imports**: 2 files
- **Evidence**: Keywords found: adapter; Actively imported by 2 files

**34. execution_adapters.py**
- **File**: `the_alchemiser/shared/adapters/execution_adapters.py`
- **Description**: Contains compatibility/shim keywords: adapter
- **Purpose**: File contains compatibility-related content
- **Suggested Action**: analyze
- **Risk Level**: high
- **Active Imports**: 2 files
- **Evidence**: Keywords found: adapter; Actively imported by 2 files

**35. integration_helpers.py**
- **File**: `the_alchemiser/shared/adapters/integration_helpers.py`
- **Description**: Contains compatibility/shim keywords: adapter
- **Purpose**: File contains compatibility-related content
- **Suggested Action**: analyze
- **Risk Level**: high
- **Active Imports**: 1 files
- **Evidence**: Keywords found: adapter; Actively imported by 1 files

**36. strategy_adapters.py**
- **File**: `the_alchemiser/shared/adapters/strategy_adapters.py`
- **Description**: Contains compatibility/shim keywords: adapter
- **Purpose**: File contains compatibility-related content
- **Suggested Action**: analyze
- **Risk Level**: high
- **Active Imports**: 2 files
- **Evidence**: Keywords found: adapter; Actively imported by 2 files

**37. account_utils.py**
- **File**: `the_alchemiser/shared/utils/account_utils.py`
- **Description**: Contains compatibility/shim keywords: compatibility, compat
- **Purpose**: File contains compatibility-related content
- **Suggested Action**: analyze
- **Risk Level**: high
- **Active Imports**: 4 files
- **Evidence**: Keywords found: compatibility, compat; Actively imported by 4 files

**38. service_factory.py**
- **File**: `the_alchemiser/shared/utils/service_factory.py`
- **Description**: Contains compatibility/shim keywords: compatibility, backward, compat
- **Purpose**: File contains compatibility-related content
- **Suggested Action**: analyze
- **Risk Level**: high
- **Active Imports**: 1 files
- **Evidence**: Keywords found: compatibility, backward, compat; Actively imported by 1 files

**39. decorators.py**
- **File**: `the_alchemiser/shared/utils/decorators.py`
- **Description**: Contains compatibility/shim keywords: wrapper
- **Purpose**: File contains compatibility-related content
- **Suggested Action**: analyze
- **Risk Level**: high
- **Active Imports**: 4 files
- **Evidence**: Keywords found: wrapper; Actively imported by 4 files

**40. error_handler.py**
- **File**: `the_alchemiser/shared/errors/error_handler.py`
- **Description**: Contains compatibility/shim keywords: compatibility, backward, compat, wrapper
- **Purpose**: File contains compatibility-related content
- **Suggested Action**: analyze
- **Risk Level**: high
- **Active Imports**: 11 files
- **Evidence**: Keywords found: compatibility, backward, compat, wrapper; Actively imported by 11 files

**41. service_providers.py**
- **File**: `the_alchemiser/shared/config/service_providers.py`
- **Description**: Contains compatibility/shim keywords: compatibility, backward, compat
- **Purpose**: File contains compatibility-related content
- **Suggested Action**: analyze
- **Risk Level**: high
- **Active Imports**: 1 files
- **Evidence**: Keywords found: compatibility, backward, compat; Actively imported by 1 files

**42. infrastructure_providers.py**
- **File**: `the_alchemiser/shared/config/infrastructure_providers.py`
- **Description**: Contains compatibility/shim keywords: compatibility, backward, compat
- **Purpose**: File contains compatibility-related content
- **Suggested Action**: analyze
- **Risk Level**: high
- **Active Imports**: 1 files
- **Evidence**: Keywords found: compatibility, backward, compat; Actively imported by 1 files

**43. bootstrap.py**
- **File**: `the_alchemiser/shared/config/bootstrap.py`
- **Description**: Contains compatibility/shim keywords: compatibility, backward, compat, adapter
- **Purpose**: File contains compatibility-related content
- **Suggested Action**: analyze
- **Risk Level**: high
- **Active Imports**: 3 files
- **Evidence**: Keywords found: compatibility, backward, compat, adapter; Actively imported by 3 files

**44. repository.py**
- **File**: `the_alchemiser/shared/protocols/repository.py`
- **Description**: Contains compatibility/shim keywords: compatibility, backward, compat
- **Purpose**: File contains compatibility-related content
- **Suggested Action**: analyze
- **Risk Level**: high
- **Active Imports**: 5 files
- **Evidence**: Keywords found: compatibility, backward, compat; Actively imported by 5 files

**45. signal_analyzer.py**
- **File**: `the_alchemiser/shared/cli/signal_analyzer.py`
- **Description**: Contains compatibility/shim keywords: compatibility, compat, adapter
- **Purpose**: File contains compatibility-related content
- **Suggested Action**: analyze
- **Risk Level**: high
- **Active Imports**: 2 files
- **Evidence**: Keywords found: compatibility, compat, adapter; Actively imported by 2 files

**46. core_types.py**
- **File**: `the_alchemiser/shared/value_objects/core_types.py`
- **Description**: Contains compatibility/shim keywords: compatibility, backward, compat
- **Purpose**: File contains compatibility-related content
- **Suggested Action**: analyze
- **Risk Level**: high
- **Active Imports**: 40 files
- **Evidence**: Keywords found: compatibility, backward, compat; Actively imported by 40 files

**47. email_utils.py**
- **File**: `the_alchemiser/shared/notifications/email_utils.py`
- **Description**: Contains compatibility/shim keywords: compatibility, backward, compat
- **Purpose**: File contains compatibility-related content
- **Suggested Action**: analyze
- **Risk Level**: high
- **Active Imports**: 1 files
- **Evidence**: Keywords found: compatibility, backward, compat; Actively imported by 1 files

**48. client.py**
- **File**: `the_alchemiser/shared/notifications/client.py`
- **Description**: Contains compatibility/shim keywords: compatibility, backward, compat
- **Purpose**: File contains compatibility-related content
- **Suggested Action**: analyze
- **Risk Level**: high
- **Active Imports**: 1 files
- **Evidence**: Keywords found: compatibility, backward, compat; Actively imported by 1 files

**49. logging_utils.py**
- **File**: `the_alchemiser/shared/logging/logging_utils.py`
- **Description**: Contains compatibility/shim keywords: adapter
- **Purpose**: File contains compatibility-related content
- **Suggested Action**: analyze
- **Risk Level**: high
- **Active Imports**: 20 files
- **Evidence**: Keywords found: adapter; Actively imported by 20 files

**50. base.py**
- **File**: `the_alchemiser/shared/schemas/base.py`
- **Description**: Contains compatibility/shim keywords: compatibility, backward, compat
- **Purpose**: File contains compatibility-related content
- **Suggested Action**: analyze
- **Risk Level**: high
- **Active Imports**: 8 files
- **Evidence**: Keywords found: compatibility, backward, compat; Actively imported by 8 files

**51. accounts.py**
- **File**: `the_alchemiser/shared/schemas/accounts.py`
- **Description**: Contains compatibility/shim keywords: compatibility, backward, compat
- **Purpose**: File contains compatibility-related content
- **Suggested Action**: analyze
- **Risk Level**: high
- **Active Imports**: 4 files
- **Evidence**: Keywords found: compatibility, backward, compat; Actively imported by 4 files

**52. enriched_data.py**
- **File**: `the_alchemiser/shared/schemas/enriched_data.py`
- **Description**: Contains compatibility/shim keywords: compatibility, backward, compat
- **Purpose**: File contains compatibility-related content
- **Suggested Action**: analyze
- **Risk Level**: high
- **Active Imports**: 2 files
- **Evidence**: Keywords found: compatibility, backward, compat; Actively imported by 2 files

**53. operations.py**
- **File**: `the_alchemiser/shared/schemas/operations.py`
- **Description**: Contains compatibility/shim keywords: compatibility, backward, compat
- **Purpose**: File contains compatibility-related content
- **Suggested Action**: analyze
- **Risk Level**: high
- **Active Imports**: 2 files
- **Evidence**: Keywords found: compatibility, backward, compat; Actively imported by 2 files

**54. market_data.py**
- **File**: `the_alchemiser/shared/schemas/market_data.py`
- **Description**: Contains compatibility/shim keywords: compatibility, backward, compat
- **Purpose**: File contains compatibility-related content
- **Suggested Action**: analyze
- **Risk Level**: high
- **Active Imports**: 2 files
- **Evidence**: Keywords found: compatibility, backward, compat; Actively imported by 2 files

**55. portfolio_pnl_utils.py**
- **File**: `the_alchemiser/portfolio/utils/portfolio_pnl_utils.py`
- **Description**: Contains compatibility/shim keywords: shim, compatibility, backward, compat
- **Purpose**: File contains compatibility-related content
- **Suggested Action**: analyze
- **Risk Level**: high
- **Active Imports**: 1 files
- **Evidence**: Keywords found: shim, compatibility, backward, compat; Actively imported by 1 files

**56. strategy_order_tracker.py**
- **File**: `the_alchemiser/portfolio/pnl/strategy_order_tracker.py`
- **Description**: Contains compatibility/shim keywords: compatibility, backward, compat
- **Purpose**: File contains compatibility-related content
- **Suggested Action**: analyze
- **Risk Level**: high
- **Active Imports**: 6 files
- **Evidence**: Keywords found: compatibility, backward, compat; Actively imported by 6 files

**57. position_manager.py**
- **File**: `the_alchemiser/portfolio/holdings/position_manager.py`
- **Description**: Contains compatibility/shim keywords: compatibility, backward, compat
- **Purpose**: File contains compatibility-related content
- **Suggested Action**: analyze
- **Risk Level**: high
- **Active Imports**: 1 files
- **Evidence**: Keywords found: compatibility, backward, compat; Actively imported by 1 files

**58. rebalance_plan.py**
- **File**: `the_alchemiser/portfolio/rebalancing/rebalance_plan.py`
- **Description**: Contains compatibility/shim keywords: shim, compatibility, backward, compat
- **Purpose**: File contains compatibility-related content
- **Suggested Action**: analyze
- **Risk Level**: high
- **Active Imports**: 2 files
- **Evidence**: Keywords found: shim, compatibility, backward, compat; Actively imported by 2 files

**59. orchestrator_facade.py**
- **File**: `the_alchemiser/portfolio/rebalancing/orchestrator_facade.py`
- **Description**: Contains compatibility/shim keywords: shim, compatibility, backward, compat
- **Purpose**: File contains compatibility-related content
- **Suggested Action**: analyze
- **Risk Level**: high
- **Active Imports**: 1 files
- **Evidence**: Keywords found: shim, compatibility, backward, compat; Actively imported by 1 files

**60. portfolio_rebalancing_service.py**
- **File**: `the_alchemiser/portfolio/allocation/portfolio_rebalancing_service.py`
- **Description**: Contains compatibility/shim keywords: adapter
- **Purpose**: File contains compatibility-related content
- **Suggested Action**: analyze
- **Risk Level**: high
- **Active Imports**: 1 files
- **Evidence**: Keywords found: adapter; Actively imported by 1 files

**61. portfolio_management_facade.py**
- **File**: `the_alchemiser/portfolio/core/portfolio_management_facade.py`
- **Description**: Contains compatibility/shim keywords: compat
- **Purpose**: File contains compatibility-related content
- **Suggested Action**: analyze
- **Risk Level**: high
- **Active Imports**: 1 files
- **Evidence**: Keywords found: compat; Actively imported by 1 files

**62. rebalancing_orchestrator_facade.py**
- **File**: `the_alchemiser/portfolio/core/rebalancing_orchestrator_facade.py`
- **Description**: Contains compatibility/shim keywords: compatibility, backward, compat
- **Purpose**: File contains compatibility-related content
- **Suggested Action**: analyze
- **Risk Level**: high
- **Active Imports**: 1 files
- **Evidence**: Keywords found: compatibility, backward, compat; Actively imported by 1 files

**63. portfolio_rebalancing_mapping.py**
- **File**: `the_alchemiser/portfolio/mappers/portfolio_rebalancing_mapping.py`
- **Description**: Contains compatibility/shim keywords: compatibility, backward, compat
- **Purpose**: File contains compatibility-related content
- **Suggested Action**: analyze
- **Risk Level**: high
- **Active Imports**: 2 files
- **Evidence**: Keywords found: compatibility, backward, compat; Actively imported by 2 files

**64. position_service.py**
- **File**: `the_alchemiser/portfolio/positions/position_service.py`
- **Description**: Contains compatibility/shim keywords: shim, compatibility, backward, compat
- **Purpose**: File contains compatibility-related content
- **Suggested Action**: analyze
- **Risk Level**: high
- **Active Imports**: 2 files
- **Evidence**: Keywords found: shim, compatibility, backward, compat; Actively imported by 2 files

**65. legacy_position_manager.py**
- **File**: `the_alchemiser/portfolio/positions/legacy_position_manager.py`
- **Description**: Contains compatibility/shim keywords: shim, compatibility, backward, compat
- **Purpose**: File contains compatibility-related content
- **Suggested Action**: analyze
- **Risk Level**: high
- **Active Imports**: 1 files
- **Evidence**: Keywords found: shim, compatibility, backward, compat; Actively imported by 1 files

**66. fractionability_policy_impl.py**
- **File**: `the_alchemiser/portfolio/policies/fractionability_policy_impl.py`
- **Description**: Contains compatibility/shim keywords: compatibility, compat
- **Purpose**: File contains compatibility-related content
- **Suggested Action**: analyze
- **Risk Level**: high
- **Active Imports**: 2 files
- **Evidence**: Keywords found: compatibility, compat; Actively imported by 2 files

**67. tracking.py**
- **File**: `the_alchemiser/portfolio/schemas/tracking.py`
- **Description**: Contains compatibility/shim keywords: compatibility, compat
- **Purpose**: File contains compatibility-related content
- **Suggested Action**: analyze
- **Risk Level**: high
- **Active Imports**: 4 files
- **Evidence**: Keywords found: compatibility, compat; Actively imported by 4 files

**68. positions.py**
- **File**: `the_alchemiser/portfolio/schemas/positions.py`
- **Description**: Contains compatibility/shim keywords: compatibility, backward, compat
- **Purpose**: File contains compatibility-related content
- **Suggested Action**: analyze
- **Risk Level**: high
- **Active Imports**: 2 files
- **Evidence**: Keywords found: compatibility, backward, compat; Actively imported by 2 files

**69. attribution_engine.py**
- **File**: `the_alchemiser/portfolio/state/attribution_engine.py`
- **Description**: Contains compatibility/shim keywords: compatibility, backward, compat
- **Purpose**: File contains compatibility-related content
- **Suggested Action**: analyze
- **Risk Level**: high
- **Active Imports**: 2 files
- **Evidence**: Keywords found: compatibility, backward, compat; Actively imported by 2 files

**70. audit_shims_compatibility.py**
- **File**: `scripts/audit_shims_compatibility.py`
- **Description**: Contains deprecation warnings or removal notices
- **Purpose**: File marked for deprecation or removal
- **Suggested Action**: review_for_removal
- **Risk Level**: high
- **Evidence**: Deprecation patterns: deprecated, DEPRECATED, deprecated

**71. main.py**
- **File**: `the_alchemiser/main.py`
- **Description**: Contains deprecation warnings or removal notices
- **Purpose**: File marked for deprecation or removal
- **Suggested Action**: review_for_removal
- **Risk Level**: high
- **Active Imports**: 4 files
- **Evidence**: Deprecation patterns: deprecated; Actively imported by 4 files

**72. asset_order_handler.py**
- **File**: `the_alchemiser/execution/orders/asset_order_handler.py`
- **Description**: Contains deprecation warnings or removal notices
- **Purpose**: File marked for deprecation or removal
- **Suggested Action**: review_for_removal
- **Risk Level**: high
- **Active Imports**: 1 files
- **Evidence**: Deprecation patterns: DEPRECATED, deprecated, DEPRECATED; Actively imported by 1 files

**73. orders.py**
- **File**: `the_alchemiser/execution/mappers/orders.py`
- **Description**: Contains deprecation warnings or removal notices
- **Purpose**: File marked for deprecation or removal
- **Suggested Action**: review_for_removal
- **Risk Level**: high
- **Active Imports**: 6 files
- **Evidence**: Deprecation patterns: deprecated; Actively imported by 6 files

**74. alpaca_client.py**
- **File**: `the_alchemiser/execution/brokers/alpaca_client.py`
- **Description**: Contains deprecation warnings or removal notices
- **Purpose**: File marked for deprecation or removal
- **Suggested Action**: review_for_removal
- **Risk Level**: high
- **Active Imports**: 2 files
- **Evidence**: Deprecation patterns: DEPRECATED, DEPRECATED, # DEPRECATED; Actively imported by 2 files

**75. shared_market_data_service.py**
- **File**: `the_alchemiser/strategy/data/shared_market_data_service.py`
- **Description**: Contains deprecation warnings or removal notices
- **Purpose**: File marked for deprecation or removal
- **Suggested Action**: review_for_removal
- **Risk Level**: high
- **Evidence**: Deprecation patterns: deprecated

**76. __init__.py**
- **File**: `the_alchemiser/strategy/engines/protocols/__init__.py`
- **Description**: Contains deprecation warnings or removal notices
- **Purpose**: File marked for deprecation or removal
- **Suggested Action**: review_for_removal
- **Risk Level**: high
- **Evidence**: Deprecation patterns: deprecated, # DEPRECATION NOTICE: MarketDataPort from this module is deprecated

**77. variant_530_18.py**
- **File**: `the_alchemiser/strategy/engines/klm_workers/variant_530_18.py`
- **Description**: Contains deprecation warnings or removal notices
- **Purpose**: File marked for deprecation or removal
- **Suggested Action**: review_for_removal
- **Risk Level**: high
- **Evidence**: Deprecation patterns: TODO: Phase 9 - Remove, TODO: Phase 9 - Remove, TODO: Phase 9 - Remove

**78. variant_1280_26.py**
- **File**: `the_alchemiser/strategy/engines/klm_workers/variant_1280_26.py`
- **Description**: Contains deprecation warnings or removal notices
- **Purpose**: File marked for deprecation or removal
- **Suggested Action**: review_for_removal
- **Risk Level**: high
- **Evidence**: Deprecation patterns: TODO: Phase 9 - Remove, TODO: Phase 9 - Remove

**79. __init__.py**
- **File**: `the_alchemiser/shared/utils/__init__.py`
- **Description**: Contains deprecation warnings or removal notices
- **Purpose**: File marked for deprecation or removal
- **Suggested Action**: review_for_removal
- **Risk Level**: high
- **Evidence**: Deprecation patterns: deprecated, # Legacy deprecated

**80. error_handling.py**
- **File**: `the_alchemiser/shared/utils/error_handling.py`
- **Description**: Contains deprecation warnings or removal notices
- **Purpose**: File marked for deprecation or removal
- **Suggested Action**: review_for_removal
- **Risk Level**: high
- **Evidence**: Deprecation patterns: DEPRECATED, deprecated, deprecated

**81. cli.py**
- **File**: `the_alchemiser/shared/cli/cli.py`
- **Description**: Contains deprecation warnings or removal notices
- **Purpose**: File marked for deprecation or removal
- **Suggested Action**: review_for_removal
- **Risk Level**: high
- **Evidence**: Deprecation patterns: deprecated

**82. trading_executor.py**
- **File**: `the_alchemiser/shared/cli/trading_executor.py`
- **Description**: Contains deprecation warnings or removal notices
- **Purpose**: File marked for deprecation or removal
- **Suggested Action**: review_for_removal
- **Risk Level**: high
- **Active Imports**: 1 files
- **Evidence**: Deprecation patterns: deprecated, # Use modern bootstrap approach instead of deprecated; Actively imported by 1 files

**83. execution_service.py**
- **File**: `the_alchemiser/portfolio/execution/execution_service.py`
- **Description**: Contains deprecation warnings or removal notices
- **Purpose**: File marked for deprecation or removal
- **Suggested Action**: review_for_removal
- **Risk Level**: high
- **Evidence**: Deprecation patterns: DEPRECATED, deprecated

**84. portfolio_pnl_utils.py**
- **File**: `the_alchemiser/portfolio/utils/portfolio_pnl_utils.py`
- **Description**: Contains deprecation warnings or removal notices
- **Purpose**: File marked for deprecation or removal
- **Suggested Action**: review_for_removal
- **Risk Level**: high
- **Active Imports**: 1 files
- **Evidence**: Deprecation patterns: DEPRECATED, deprecated; Actively imported by 1 files

**85. position_manager.py**
- **File**: `the_alchemiser/portfolio/holdings/position_manager.py`
- **Description**: Contains deprecation warnings or removal notices
- **Purpose**: File marked for deprecation or removal
- **Suggested Action**: review_for_removal
- **Risk Level**: high
- **Active Imports**: 1 files
- **Evidence**: Deprecation patterns: DEPRECATED, deprecated, DEPRECATED; Actively imported by 1 files

**86. rebalance_plan.py**
- **File**: `the_alchemiser/portfolio/rebalancing/rebalance_plan.py`
- **Description**: Contains deprecation warnings or removal notices
- **Purpose**: File marked for deprecation or removal
- **Suggested Action**: review_for_removal
- **Risk Level**: high
- **Active Imports**: 2 files
- **Evidence**: Deprecation patterns: DEPRECATED, deprecated; Actively imported by 2 files

**87. orchestrator.py**
- **File**: `the_alchemiser/portfolio/rebalancing/orchestrator.py`
- **Description**: Contains deprecation warnings or removal notices
- **Purpose**: File marked for deprecation or removal
- **Suggested Action**: review_for_removal
- **Risk Level**: high
- **Evidence**: Deprecation patterns: DEPRECATED, deprecated

**88. rebalancing_service.py**
- **File**: `the_alchemiser/portfolio/rebalancing/rebalancing_service.py`
- **Description**: Contains deprecation warnings or removal notices
- **Purpose**: File marked for deprecation or removal
- **Suggested Action**: review_for_removal
- **Risk Level**: high
- **Evidence**: Deprecation patterns: DEPRECATED, deprecated

**89. orchestrator_facade.py**
- **File**: `the_alchemiser/portfolio/rebalancing/orchestrator_facade.py`
- **Description**: Contains deprecation warnings or removal notices
- **Purpose**: File marked for deprecation or removal
- **Suggested Action**: review_for_removal
- **Risk Level**: high
- **Active Imports**: 1 files
- **Evidence**: Deprecation patterns: DEPRECATED, deprecated; Actively imported by 1 files

**90. analysis_service.py**
- **File**: `the_alchemiser/portfolio/analytics/analysis_service.py`
- **Description**: Contains deprecation warnings or removal notices
- **Purpose**: File marked for deprecation or removal
- **Suggested Action**: review_for_removal
- **Risk Level**: high
- **Evidence**: Deprecation patterns: DEPRECATED, deprecated

**91. position_analyzer.py**
- **File**: `the_alchemiser/portfolio/analytics/position_analyzer.py`
- **Description**: Contains deprecation warnings or removal notices
- **Purpose**: File marked for deprecation or removal
- **Suggested Action**: review_for_removal
- **Risk Level**: high
- **Evidence**: Deprecation patterns: DEPRECATED, deprecated

**92. position_delta.py**
- **File**: `the_alchemiser/portfolio/analytics/position_delta.py`
- **Description**: Contains deprecation warnings or removal notices
- **Purpose**: File marked for deprecation or removal
- **Suggested Action**: review_for_removal
- **Risk Level**: high
- **Evidence**: Deprecation patterns: DEPRECATED, deprecated

**93. attribution_engine.py**
- **File**: `the_alchemiser/portfolio/analytics/attribution_engine.py`
- **Description**: Contains deprecation warnings or removal notices
- **Purpose**: File marked for deprecation or removal
- **Suggested Action**: review_for_removal
- **Risk Level**: high
- **Evidence**: Deprecation patterns: DEPRECATED, deprecated

**94. position_service.py**
- **File**: `the_alchemiser/portfolio/positions/position_service.py`
- **Description**: Contains deprecation warnings or removal notices
- **Purpose**: File marked for deprecation or removal
- **Suggested Action**: review_for_removal
- **Risk Level**: high
- **Active Imports**: 2 files
- **Evidence**: Deprecation patterns: DEPRECATED, deprecated; Actively imported by 2 files

**95. legacy_position_manager.py**
- **File**: `the_alchemiser/portfolio/positions/legacy_position_manager.py`
- **Description**: Contains deprecation warnings or removal notices
- **Purpose**: File marked for deprecation or removal
- **Suggested Action**: review_for_removal
- **Risk Level**: high
- **Active Imports**: 1 files
- **Evidence**: Deprecation patterns: DEPRECATED, deprecated; Actively imported by 1 files

**96. order_schemas.py**
- **File**: `the_alchemiser/execution/orders/order_schemas.py`
- **Description**: Contains import redirections or compatibility imports
- **Purpose**: File provides import compatibility layer
- **Suggested Action**: migrate_imports
- **Risk Level**: high
- **Active Imports**: 16 files
- **Evidence**: Import patterns: # Backward compatibility; Actively imported by 16 files

**97. validation.py**
- **File**: `the_alchemiser/execution/orders/validation.py`
- **Description**: Contains import redirections or compatibility imports
- **Purpose**: File provides import compatibility layer
- **Suggested Action**: migrate_imports
- **Risk Level**: high
- **Active Imports**: 2 files
- **Evidence**: Import patterns: moved to; Actively imported by 2 files

**98. asset_order_handler.py**
- **File**: `the_alchemiser/execution/orders/asset_order_handler.py`
- **Description**: Contains import redirections or compatibility imports
- **Purpose**: File provides import compatibility layer
- **Suggested Action**: migrate_imports
- **Risk Level**: high
- **Active Imports**: 1 files
- **Evidence**: Import patterns: moved to, moved to; Actively imported by 1 files

**99. execution_schemas.py**
- **File**: `the_alchemiser/execution/core/execution_schemas.py`
- **Description**: Contains import redirections or compatibility imports
- **Purpose**: File provides import compatibility layer
- **Suggested Action**: migrate_imports
- **Risk Level**: high
- **Active Imports**: 12 files
- **Evidence**: Import patterns: # Backward compatibility, # Backward compatibility, moved to; Actively imported by 12 files

**100. canonical_executor.py**
- **File**: `the_alchemiser/execution/core/canonical_executor.py`
- **Description**: Contains import redirections or compatibility imports
- **Purpose**: File provides import compatibility layer
- **Suggested Action**: migrate_imports
- **Risk Level**: high
- **Active Imports**: 6 files
- **Evidence**: Import patterns: moved to, Import redirect; Actively imported by 6 files

**101. alpaca_client.py**
- **File**: `the_alchemiser/execution/brokers/alpaca_client.py`
- **Description**: Contains import redirections or compatibility imports
- **Purpose**: File provides import compatibility layer
- **Suggested Action**: migrate_imports
- **Risk Level**: high
- **Active Imports**: 2 files
- **Evidence**: Import patterns: # Backward compatibility; Actively imported by 2 files

**102. smart_execution.py**
- **File**: `the_alchemiser/execution/strategies/smart_execution.py`
- **Description**: Contains import redirections or compatibility imports
- **Purpose**: File provides import compatibility layer
- **Suggested Action**: migrate_imports
- **Risk Level**: high
- **Active Imports**: 6 files
- **Evidence**: Import patterns: # Backward compatibility; Actively imported by 6 files

**103. service_factory.py**
- **File**: `the_alchemiser/shared/utils/service_factory.py`
- **Description**: Contains import redirections or compatibility imports
- **Purpose**: File provides import compatibility layer
- **Suggested Action**: migrate_imports
- **Risk Level**: high
- **Active Imports**: 1 files
- **Evidence**: Import patterns: # Backward compatibility; Actively imported by 1 files

**104. tick_size_service.py**
- **File**: `the_alchemiser/shared/services/tick_size_service.py`
- **Description**: Contains import redirections or compatibility imports
- **Purpose**: File provides import compatibility layer
- **Suggested Action**: migrate_imports
- **Risk Level**: high
- **Active Imports**: 2 files
- **Evidence**: Import patterns: moved to; Actively imported by 2 files

**105. service_providers.py**
- **File**: `the_alchemiser/shared/config/service_providers.py`
- **Description**: Contains import redirections or compatibility imports
- **Purpose**: File provides import compatibility layer
- **Suggested Action**: migrate_imports
- **Risk Level**: high
- **Active Imports**: 1 files
- **Evidence**: Import patterns: # Backward compatibility; Actively imported by 1 files

**106. infrastructure_providers.py**
- **File**: `the_alchemiser/shared/config/infrastructure_providers.py`
- **Description**: Contains import redirections or compatibility imports
- **Purpose**: File provides import compatibility layer
- **Suggested Action**: migrate_imports
- **Risk Level**: high
- **Active Imports**: 1 files
- **Evidence**: Import patterns: # Backward compatibility; Actively imported by 1 files

**107. core_types.py**
- **File**: `the_alchemiser/shared/value_objects/core_types.py`
- **Description**: Contains import redirections or compatibility imports
- **Purpose**: File provides import compatibility layer
- **Suggested Action**: migrate_imports
- **Risk Level**: high
- **Active Imports**: 40 files
- **Evidence**: Import patterns: moved to, moved to, moved to; Actively imported by 40 files

**108. email_utils.py**
- **File**: `the_alchemiser/shared/notifications/email_utils.py`
- **Description**: Contains import redirections or compatibility imports
- **Purpose**: File provides import compatibility layer
- **Suggested Action**: migrate_imports
- **Risk Level**: high
- **Active Imports**: 1 files
- **Evidence**: Import patterns: # Backward compatibility; Actively imported by 1 files

**109. base.py**
- **File**: `the_alchemiser/shared/schemas/base.py`
- **Description**: Contains import redirections or compatibility imports
- **Purpose**: File provides import compatibility layer
- **Suggested Action**: migrate_imports
- **Risk Level**: high
- **Active Imports**: 8 files
- **Evidence**: Import patterns: # Backward compatibility; Actively imported by 8 files

**110. accounts.py**
- **File**: `the_alchemiser/shared/schemas/accounts.py`
- **Description**: Contains import redirections or compatibility imports
- **Purpose**: File provides import compatibility layer
- **Suggested Action**: migrate_imports
- **Risk Level**: high
- **Active Imports**: 4 files
- **Evidence**: Import patterns: # Backward compatibility; Actively imported by 4 files

**111. enriched_data.py**
- **File**: `the_alchemiser/shared/schemas/enriched_data.py`
- **Description**: Contains import redirections or compatibility imports
- **Purpose**: File provides import compatibility layer
- **Suggested Action**: migrate_imports
- **Risk Level**: high
- **Active Imports**: 2 files
- **Evidence**: Import patterns: # Backward compatibility; Actively imported by 2 files

**112. operations.py**
- **File**: `the_alchemiser/shared/schemas/operations.py`
- **Description**: Contains import redirections or compatibility imports
- **Purpose**: File provides import compatibility layer
- **Suggested Action**: migrate_imports
- **Risk Level**: high
- **Active Imports**: 2 files
- **Evidence**: Import patterns: # Backward compatibility; Actively imported by 2 files

**113. market_data.py**
- **File**: `the_alchemiser/shared/schemas/market_data.py`
- **Description**: Contains import redirections or compatibility imports
- **Purpose**: File provides import compatibility layer
- **Suggested Action**: migrate_imports
- **Risk Level**: high
- **Active Imports**: 2 files
- **Evidence**: Import patterns: # Backward compatibility; Actively imported by 2 files

**114. portfolio_pnl_utils.py**
- **File**: `the_alchemiser/portfolio/utils/portfolio_pnl_utils.py`
- **Description**: Contains import redirections or compatibility imports
- **Purpose**: File provides import compatibility layer
- **Suggested Action**: migrate_imports
- **Risk Level**: high
- **Active Imports**: 1 files
- **Evidence**: Import patterns: moved to; Actively imported by 1 files

**115. position_manager.py**
- **File**: `the_alchemiser/portfolio/holdings/position_manager.py`
- **Description**: Contains import redirections or compatibility imports
- **Purpose**: File provides import compatibility layer
- **Suggested Action**: migrate_imports
- **Risk Level**: high
- **Active Imports**: 1 files
- **Evidence**: Import patterns: moved to, moved to; Actively imported by 1 files

**116. rebalance_plan.py**
- **File**: `the_alchemiser/portfolio/rebalancing/rebalance_plan.py`
- **Description**: Contains import redirections or compatibility imports
- **Purpose**: File provides import compatibility layer
- **Suggested Action**: migrate_imports
- **Risk Level**: high
- **Active Imports**: 2 files
- **Evidence**: Import patterns: moved to; Actively imported by 2 files

**117. orchestrator_facade.py**
- **File**: `the_alchemiser/portfolio/rebalancing/orchestrator_facade.py`
- **Description**: Contains import redirections or compatibility imports
- **Purpose**: File provides import compatibility layer
- **Suggested Action**: migrate_imports
- **Risk Level**: high
- **Active Imports**: 1 files
- **Evidence**: Import patterns: moved to; Actively imported by 1 files

**118. position_service.py**
- **File**: `the_alchemiser/portfolio/positions/position_service.py`
- **Description**: Contains import redirections or compatibility imports
- **Purpose**: File provides import compatibility layer
- **Suggested Action**: migrate_imports
- **Risk Level**: high
- **Active Imports**: 2 files
- **Evidence**: Import patterns: moved to; Actively imported by 2 files

**119. legacy_position_manager.py**
- **File**: `the_alchemiser/portfolio/positions/legacy_position_manager.py`
- **Description**: Contains import redirections or compatibility imports
- **Purpose**: File provides import compatibility layer
- **Suggested Action**: migrate_imports
- **Risk Level**: high
- **Active Imports**: 1 files
- **Evidence**: Import patterns: moved to; Actively imported by 1 files

**120. positions.py**
- **File**: `the_alchemiser/portfolio/schemas/positions.py`
- **Description**: Contains import redirections or compatibility imports
- **Purpose**: File provides import compatibility layer
- **Suggested Action**: migrate_imports
- **Risk Level**: high
- **Active Imports**: 2 files
- **Evidence**: Import patterns: # Backward compatibility; Actively imported by 2 files

**121. audit_shims_compatibility.py**
- **File**: `scripts/audit_shims_compatibility.py`
- **Description**: File marked with legacy/deprecated status
- **Purpose**: File explicitly marked as legacy or deprecated
- **Suggested Action**: review_for_migration
- **Risk Level**: high
- **Evidence**: Status markers: Status markers indicating legacy, Status: legacy, Status.*legacy, Status.*deprecated, Business Unit.*legacy

**122. policy_layer_usage.py**
- **File**: `examples/policy_layer_usage.py`
- **Description**: File marked with legacy/deprecated status
- **Purpose**: File explicitly marked as legacy or deprecated
- **Suggested Action**: review_for_migration
- **Risk Level**: high
- **Evidence**: Status markers: Status: legacy, Business Unit: utilities; Status: legacy

**123. execution_manager_legacy.py**
- **File**: `the_alchemiser/execution/core/execution_manager_legacy.py`
- **Description**: File marked with legacy/deprecated status
- **Purpose**: File explicitly marked as legacy or deprecated
- **Suggested Action**: review_for_migration
- **Risk Level**: high
- **Evidence**: Status markers: Status: legacy, Business Unit: execution; Status: legacy

**124. canonical_executor.py**
- **File**: `the_alchemiser/execution/core/canonical_executor.py`
- **Description**: File marked with legacy/deprecated status
- **Purpose**: File explicitly marked as legacy or deprecated
- **Suggested Action**: review_for_migration
- **Risk Level**: high
- **Active Imports**: 6 files
- **Evidence**: Status markers: Status: legacy, Business Unit: execution; Status: legacy; Actively imported by 6 files

### 🟡 MEDIUM RISK (65 items)

**1. rollback_legacy_deletions.py**
- **File**: `scripts/rollback_legacy_deletions.py`
- **Description**: File with *legacy* pattern in name
- **Purpose**: File named with pattern: *legacy*
- **Suggested Action**: analyze
- **Risk Level**: medium
- **Evidence**: Filename matches pattern: *legacy*

**2. delete_legacy_safe.py**
- **File**: `scripts/delete_legacy_safe.py`
- **Description**: File with *legacy* pattern in name
- **Purpose**: File named with pattern: *legacy*
- **Suggested Action**: analyze
- **Risk Level**: medium
- **Evidence**: Filename matches pattern: *legacy*

**3. execution_manager_legacy.py**
- **File**: `the_alchemiser/execution/core/execution_manager_legacy.py`
- **Description**: File with *legacy* pattern in name
- **Purpose**: File named with pattern: *legacy*
- **Suggested Action**: analyze
- **Risk Level**: medium
- **Evidence**: Filename matches pattern: *legacy*

**4. migrate_phase2_imports.py**
- **File**: `scripts/migrate_phase2_imports.py`
- **Description**: Contains compatibility/shim keywords: adapter
- **Purpose**: File contains compatibility-related content
- **Suggested Action**: analyze
- **Risk Level**: medium
- **Evidence**: Keywords found: adapter

**5. delete_legacy_safe.py**
- **File**: `scripts/delete_legacy_safe.py`
- **Description**: Contains compatibility/shim keywords: adapter
- **Purpose**: File contains compatibility-related content
- **Suggested Action**: analyze
- **Risk Level**: medium
- **Evidence**: Keywords found: adapter

**6. audit_shims_compatibility.py**
- **File**: `scripts/audit_shims_compatibility.py`
- **Description**: Contains compatibility/shim keywords: shim, compatibility, backward, compat, polyfill, adapter, wrapper, bridge
- **Purpose**: File contains compatibility-related content
- **Suggested Action**: analyze
- **Risk Level**: medium
- **Evidence**: Keywords found: shim, compatibility, backward, compat, polyfill, adapter, wrapper, bridge

**7. lambda_handler.py**
- **File**: `the_alchemiser/lambda_handler.py`
- **Description**: Contains compatibility/shim keywords: compatibility, backward, compat
- **Purpose**: File contains compatibility-related content
- **Suggested Action**: analyze
- **Risk Level**: medium
- **Evidence**: Keywords found: compatibility, backward, compat

**8. __init__.py**
- **File**: `the_alchemiser/execution/__init__.py`
- **Description**: Contains compatibility/shim keywords: adapter
- **Purpose**: File contains compatibility-related content
- **Suggested Action**: analyze
- **Risk Level**: medium
- **Evidence**: Keywords found: adapter

**9. dto_communication_demo.py**
- **File**: `the_alchemiser/shared/dto_communication_demo.py`
- **Description**: Contains compatibility/shim keywords: adapter
- **Purpose**: File contains compatibility-related content
- **Suggested Action**: analyze
- **Risk Level**: medium
- **Evidence**: Keywords found: adapter

**10. simple_dto_test.py**
- **File**: `the_alchemiser/shared/simple_dto_test.py`
- **Description**: Contains compatibility/shim keywords: adapter
- **Purpose**: File contains compatibility-related content
- **Suggested Action**: analyze
- **Risk Level**: medium
- **Evidence**: Keywords found: adapter

**11. lifecycle_adapter.py**
- **File**: `the_alchemiser/execution/orders/lifecycle_adapter.py`
- **Description**: Contains compatibility/shim keywords: adapter
- **Purpose**: File contains compatibility-related content
- **Suggested Action**: analyze
- **Risk Level**: medium
- **Evidence**: Keywords found: adapter

**12. trading_repository.py**
- **File**: `the_alchemiser/execution/protocols/trading_repository.py`
- **Description**: Contains compatibility/shim keywords: adapter
- **Purpose**: File contains compatibility-related content
- **Suggested Action**: analyze
- **Risk Level**: medium
- **Evidence**: Keywords found: adapter

**13. execution_manager_legacy.py**
- **File**: `the_alchemiser/execution/core/execution_manager_legacy.py`
- **Description**: Contains compatibility/shim keywords: shim, compatibility, backward, compat
- **Purpose**: File contains compatibility-related content
- **Suggested Action**: analyze
- **Risk Level**: medium
- **Evidence**: Keywords found: shim, compatibility, backward, compat

**14. __init__.py**
- **File**: `the_alchemiser/execution/brokers/__init__.py`
- **Description**: Contains compatibility/shim keywords: adapter
- **Purpose**: File contains compatibility-related content
- **Suggested Action**: analyze
- **Risk Level**: medium
- **Evidence**: Keywords found: adapter

**15. execution_context_adapter.py**
- **File**: `the_alchemiser/execution/strategies/execution_context_adapter.py`
- **Description**: Contains compatibility/shim keywords: compatibility, compat, adapter, bridge
- **Purpose**: File contains compatibility-related content
- **Suggested Action**: analyze
- **Risk Level**: medium
- **Evidence**: Keywords found: compatibility, compat, adapter, bridge

**16. __init__.py**
- **File**: `the_alchemiser/execution/strategies/__init__.py`
- **Description**: Contains compatibility/shim keywords: adapter
- **Purpose**: File contains compatibility-related content
- **Suggested Action**: analyze
- **Risk Level**: medium
- **Evidence**: Keywords found: adapter

**17. observers.py**
- **File**: `the_alchemiser/execution/lifecycle/observers.py`
- **Description**: Contains compatibility/shim keywords: compatibility, backward, compat
- **Purpose**: File contains compatibility-related content
- **Suggested Action**: analyze
- **Risk Level**: medium
- **Evidence**: Keywords found: compatibility, backward, compat

**18. adapter.py**
- **File**: `the_alchemiser/execution/brokers/alpaca/adapter.py`
- **Description**: Contains compatibility/shim keywords: compatibility, backward, compat, adapter
- **Purpose**: File contains compatibility-related content
- **Suggested Action**: analyze
- **Risk Level**: medium
- **Evidence**: Keywords found: compatibility, backward, compat, adapter

**19. __init__.py**
- **File**: `the_alchemiser/execution/brokers/alpaca/__init__.py`
- **Description**: Contains compatibility/shim keywords: adapter
- **Purpose**: File contains compatibility-related content
- **Suggested Action**: analyze
- **Risk Level**: medium
- **Evidence**: Keywords found: adapter

**20. domain_mapping.py**
- **File**: `the_alchemiser/strategy/data/domain_mapping.py`
- **Description**: Contains compatibility/shim keywords: compatibility, backward, compat
- **Purpose**: File contains compatibility-related content
- **Suggested Action**: analyze
- **Risk Level**: medium
- **Evidence**: Keywords found: compatibility, backward, compat

**21. __init__.py**
- **File**: `the_alchemiser/strategy/mappers/__init__.py`
- **Description**: Contains compatibility/shim keywords: adapter
- **Purpose**: File contains compatibility-related content
- **Suggested Action**: analyze
- **Risk Level**: medium
- **Evidence**: Keywords found: adapter

**22. __init__.py**
- **File**: `the_alchemiser/strategy/engines/protocols/__init__.py`
- **Description**: Contains compatibility/shim keywords: adapter
- **Purpose**: File contains compatibility-related content
- **Suggested Action**: analyze
- **Risk Level**: medium
- **Evidence**: Keywords found: adapter

**23. __init__.py**
- **File**: `the_alchemiser/shared/adapters/__init__.py`
- **Description**: Contains compatibility/shim keywords: adapter
- **Purpose**: File contains compatibility-related content
- **Suggested Action**: analyze
- **Risk Level**: medium
- **Evidence**: Keywords found: adapter

**24. error_recovery.py**
- **File**: `the_alchemiser/shared/utils/error_recovery.py`
- **Description**: Contains compatibility/shim keywords: wrapper
- **Purpose**: File contains compatibility-related content
- **Suggested Action**: analyze
- **Risk Level**: medium
- **Evidence**: Keywords found: wrapper

**25. retry_decorator.py**
- **File**: `the_alchemiser/shared/utils/retry_decorator.py`
- **Description**: Contains compatibility/shim keywords: wrapper
- **Purpose**: File contains compatibility-related content
- **Suggested Action**: analyze
- **Risk Level**: medium
- **Evidence**: Keywords found: wrapper

**26. error_handling.py**
- **File**: `the_alchemiser/shared/utils/error_handling.py`
- **Description**: Contains compatibility/shim keywords: compatibility, backward, compat
- **Purpose**: File contains compatibility-related content
- **Suggested Action**: analyze
- **Risk Level**: medium
- **Evidence**: Keywords found: compatibility, backward, compat

**27. real_time_pricing.py**
- **File**: `the_alchemiser/shared/services/real_time_pricing.py`
- **Description**: Contains compatibility/shim keywords: compatibility, backward, compat
- **Purpose**: File contains compatibility-related content
- **Suggested Action**: analyze
- **Risk Level**: medium
- **Evidence**: Keywords found: compatibility, backward, compat

**28. trading.py**
- **File**: `the_alchemiser/shared/protocols/trading.py`
- **Description**: Contains compatibility/shim keywords: adapter
- **Purpose**: File contains compatibility-related content
- **Suggested Action**: analyze
- **Risk Level**: medium
- **Evidence**: Keywords found: adapter

**29. signal_display_utils.py**
- **File**: `the_alchemiser/shared/cli/signal_display_utils.py`
- **Description**: Contains compatibility/shim keywords: compatibility, compat
- **Purpose**: File contains compatibility-related content
- **Suggested Action**: analyze
- **Risk Level**: medium
- **Evidence**: Keywords found: compatibility, compat

**30. cli.py**
- **File**: `the_alchemiser/shared/cli/cli.py`
- **Description**: Contains compatibility/shim keywords: compatibility, compat, adapter
- **Purpose**: File contains compatibility-related content
- **Suggested Action**: analyze
- **Risk Level**: medium
- **Evidence**: Keywords found: compatibility, compat, adapter

**31. execution_summary_mapping.py**
- **File**: `the_alchemiser/shared/mappers/execution_summary_mapping.py`
- **Description**: Contains compatibility/shim keywords: compatibility, backward, compat
- **Purpose**: File contains compatibility-related content
- **Suggested Action**: analyze
- **Risk Level**: medium
- **Evidence**: Keywords found: compatibility, backward, compat

**32. config.py**
- **File**: `the_alchemiser/shared/notifications/config.py`
- **Description**: Contains compatibility/shim keywords: compatibility, backward, compat
- **Purpose**: File contains compatibility-related content
- **Suggested Action**: analyze
- **Risk Level**: medium
- **Evidence**: Keywords found: compatibility, backward, compat

**33. execution_summary.py**
- **File**: `the_alchemiser/shared/schemas/execution_summary.py`
- **Description**: Contains compatibility/shim keywords: compatibility, backward, compat
- **Purpose**: File contains compatibility-related content
- **Suggested Action**: analyze
- **Risk Level**: medium
- **Evidence**: Keywords found: compatibility, backward, compat

**34. base.py**
- **File**: `the_alchemiser/shared/notifications/templates/base.py`
- **Description**: Contains compatibility/shim keywords: compat
- **Purpose**: File contains compatibility-related content
- **Suggested Action**: analyze
- **Risk Level**: medium
- **Evidence**: Keywords found: compat

**35. error_report.py**
- **File**: `the_alchemiser/shared/notifications/templates/error_report.py`
- **Description**: Contains compatibility/shim keywords: compat
- **Purpose**: File contains compatibility-related content
- **Suggested Action**: analyze
- **Risk Level**: medium
- **Evidence**: Keywords found: compat

**36. execution_service.py**
- **File**: `the_alchemiser/portfolio/execution/execution_service.py`
- **Description**: Contains compatibility/shim keywords: shim, compatibility, backward, compat
- **Purpose**: File contains compatibility-related content
- **Suggested Action**: analyze
- **Risk Level**: medium
- **Evidence**: Keywords found: shim, compatibility, backward, compat

**37. orchestrator.py**
- **File**: `the_alchemiser/portfolio/rebalancing/orchestrator.py`
- **Description**: Contains compatibility/shim keywords: shim, compatibility, backward, compat
- **Purpose**: File contains compatibility-related content
- **Suggested Action**: analyze
- **Risk Level**: medium
- **Evidence**: Keywords found: shim, compatibility, backward, compat

**38. rebalancing_service.py**
- **File**: `the_alchemiser/portfolio/rebalancing/rebalancing_service.py`
- **Description**: Contains compatibility/shim keywords: shim, compatibility, backward, compat
- **Purpose**: File contains compatibility-related content
- **Suggested Action**: analyze
- **Risk Level**: medium
- **Evidence**: Keywords found: shim, compatibility, backward, compat

**39. portfolio_calculations.py**
- **File**: `the_alchemiser/portfolio/calculations/portfolio_calculations.py`
- **Description**: Contains compatibility/shim keywords: compat
- **Purpose**: File contains compatibility-related content
- **Suggested Action**: analyze
- **Risk Level**: medium
- **Evidence**: Keywords found: compat

**40. integration.py**
- **File**: `the_alchemiser/portfolio/tracking/integration.py`
- **Description**: Contains compatibility/shim keywords: wrapper
- **Purpose**: File contains compatibility-related content
- **Suggested Action**: analyze
- **Risk Level**: medium
- **Evidence**: Keywords found: wrapper

**41. analysis_service.py**
- **File**: `the_alchemiser/portfolio/analytics/analysis_service.py`
- **Description**: Contains compatibility/shim keywords: shim, compatibility, backward, compat
- **Purpose**: File contains compatibility-related content
- **Suggested Action**: analyze
- **Risk Level**: medium
- **Evidence**: Keywords found: shim, compatibility, backward, compat

**42. position_analyzer.py**
- **File**: `the_alchemiser/portfolio/analytics/position_analyzer.py`
- **Description**: Contains compatibility/shim keywords: shim, compatibility, backward, compat
- **Purpose**: File contains compatibility-related content
- **Suggested Action**: analyze
- **Risk Level**: medium
- **Evidence**: Keywords found: shim, compatibility, backward, compat

**43. position_delta.py**
- **File**: `the_alchemiser/portfolio/analytics/position_delta.py`
- **Description**: Contains compatibility/shim keywords: shim, compatibility, backward, compat
- **Purpose**: File contains compatibility-related content
- **Suggested Action**: analyze
- **Risk Level**: medium
- **Evidence**: Keywords found: shim, compatibility, backward, compat

**44. attribution_engine.py**
- **File**: `the_alchemiser/portfolio/analytics/attribution_engine.py`
- **Description**: Contains compatibility/shim keywords: shim, compatibility, backward, compat
- **Purpose**: File contains compatibility-related content
- **Suggested Action**: analyze
- **Risk Level**: medium
- **Evidence**: Keywords found: shim, compatibility, backward, compat

**45. symbol_classifier.py**
- **File**: `the_alchemiser/portfolio/state/symbol_classifier.py`
- **Description**: Contains compatibility/shim keywords: compatibility, backward, compat
- **Purpose**: File contains compatibility-related content
- **Suggested Action**: analyze
- **Risk Level**: medium
- **Evidence**: Keywords found: compatibility, backward, compat

**46. migrate_phase2_imports.py**
- **File**: `scripts/migrate_phase2_imports.py`
- **Description**: Contains import redirections or compatibility imports
- **Purpose**: File provides import compatibility layer
- **Suggested Action**: migrate_imports
- **Risk Level**: medium
- **Evidence**: Import patterns: moved to

**47. audit_shims_compatibility.py**
- **File**: `scripts/audit_shims_compatibility.py`
- **Description**: Contains import redirections or compatibility imports
- **Purpose**: File provides import compatibility layer
- **Suggested Action**: migrate_imports
- **Risk Level**: medium
- **Evidence**: Import patterns: from.*import.*\*.*#.*redirect, from.*import.*\*.*#.*compat, # Import.*redirect

**48. order_validation_utils.py**
- **File**: `the_alchemiser/execution/orders/order_validation_utils.py`
- **Description**: Contains import redirections or compatibility imports
- **Purpose**: File provides import compatibility layer
- **Suggested Action**: migrate_imports
- **Risk Level**: medium
- **Evidence**: Import patterns: moved to

**49. lifecycle_adapter.py**
- **File**: `the_alchemiser/execution/orders/lifecycle_adapter.py`
- **Description**: Contains import redirections or compatibility imports
- **Purpose**: File provides import compatibility layer
- **Suggested Action**: migrate_imports
- **Risk Level**: medium
- **Evidence**: Import patterns: moved to

**50. execution_manager_legacy.py**
- **File**: `the_alchemiser/execution/core/execution_manager_legacy.py`
- **Description**: Contains import redirections or compatibility imports
- **Purpose**: File provides import compatibility layer
- **Suggested Action**: migrate_imports
- **Risk Level**: medium
- **Evidence**: Import patterns: moved to, Import redirect

**51. canonical_integration.py**
- **File**: `the_alchemiser/execution/examples/canonical_integration.py`
- **Description**: Contains import redirections or compatibility imports
- **Purpose**: File provides import compatibility layer
- **Suggested Action**: migrate_imports
- **Risk Level**: medium
- **Evidence**: Import patterns: moved to

**52. execution_context_adapter.py**
- **File**: `the_alchemiser/execution/strategies/execution_context_adapter.py`
- **Description**: Contains import redirections or compatibility imports
- **Purpose**: File provides import compatibility layer
- **Suggested Action**: migrate_imports
- **Risk Level**: medium
- **Evidence**: Import patterns: moved to

**53. __init__.py**
- **File**: `the_alchemiser/shared/utils/__init__.py`
- **Description**: Contains import redirections or compatibility imports
- **Purpose**: File provides import compatibility layer
- **Suggested Action**: migrate_imports
- **Risk Level**: medium
- **Evidence**: Import patterns: from .error_handling import *  # Legacy deprecated

**54. error_handling.py**
- **File**: `the_alchemiser/shared/utils/error_handling.py`
- **Description**: Contains import redirections or compatibility imports
- **Purpose**: File provides import compatibility layer
- **Suggested Action**: migrate_imports
- **Risk Level**: medium
- **Evidence**: Import patterns: moved to

**55. trading.py**
- **File**: `the_alchemiser/shared/protocols/trading.py`
- **Description**: Contains import redirections or compatibility imports
- **Purpose**: File provides import compatibility layer
- **Suggested Action**: migrate_imports
- **Risk Level**: medium
- **Evidence**: Import patterns: moved to

**56. execution_summary.py**
- **File**: `the_alchemiser/shared/schemas/execution_summary.py`
- **Description**: Contains import redirections or compatibility imports
- **Purpose**: File provides import compatibility layer
- **Suggested Action**: migrate_imports
- **Risk Level**: medium
- **Evidence**: Import patterns: # Backward compatibility

**57. execution_service.py**
- **File**: `the_alchemiser/portfolio/execution/execution_service.py`
- **Description**: Contains import redirections or compatibility imports
- **Purpose**: File provides import compatibility layer
- **Suggested Action**: migrate_imports
- **Risk Level**: medium
- **Evidence**: Import patterns: moved to

**58. orchestrator.py**
- **File**: `the_alchemiser/portfolio/rebalancing/orchestrator.py`
- **Description**: Contains import redirections or compatibility imports
- **Purpose**: File provides import compatibility layer
- **Suggested Action**: migrate_imports
- **Risk Level**: medium
- **Evidence**: Import patterns: moved to

**59. rebalancing_service.py**
- **File**: `the_alchemiser/portfolio/rebalancing/rebalancing_service.py`
- **Description**: Contains import redirections or compatibility imports
- **Purpose**: File provides import compatibility layer
- **Suggested Action**: migrate_imports
- **Risk Level**: medium
- **Evidence**: Import patterns: moved to

**60. analysis_service.py**
- **File**: `the_alchemiser/portfolio/analytics/analysis_service.py`
- **Description**: Contains import redirections or compatibility imports
- **Purpose**: File provides import compatibility layer
- **Suggested Action**: migrate_imports
- **Risk Level**: medium
- **Evidence**: Import patterns: moved to

**61. position_analyzer.py**
- **File**: `the_alchemiser/portfolio/analytics/position_analyzer.py`
- **Description**: Contains import redirections or compatibility imports
- **Purpose**: File provides import compatibility layer
- **Suggested Action**: migrate_imports
- **Risk Level**: medium
- **Evidence**: Import patterns: moved to

**62. position_delta.py**
- **File**: `the_alchemiser/portfolio/analytics/position_delta.py`
- **Description**: Contains import redirections or compatibility imports
- **Purpose**: File provides import compatibility layer
- **Suggested Action**: migrate_imports
- **Risk Level**: medium
- **Evidence**: Import patterns: moved to

**63. attribution_engine.py**
- **File**: `the_alchemiser/portfolio/analytics/attribution_engine.py`
- **Description**: Contains import redirections or compatibility imports
- **Purpose**: File provides import compatibility layer
- **Suggested Action**: migrate_imports
- **Risk Level**: medium
- **Evidence**: Import patterns: moved to

**64. audit_shims_compatibility.py**
- **File**: `scripts/audit_shims_compatibility.py`
- **Description**: Contains polyfill or environment-specific compatibility code
- **Purpose**: File provides cross-version or cross-platform compatibility
- **Suggested Action**: review_for_modernization
- **Risk Level**: medium
- **Evidence**: Polyfill patterns: polyfill, # Patch for, # Fix for.*version

**65. __init__.py**
- **File**: `the_alchemiser/__init__.py`
- **Description**: Contains polyfill or environment-specific compatibility code
- **Purpose**: File provides cross-version or cross-platform compatibility
- **Suggested Action**: review_for_modernization
- **Risk Level**: medium
- **Evidence**: Polyfill patterns: platform\.

### 🟢 LOW RISK (7 items)

**1. audit_shims_compatibility.py**
- **File**: `scripts/audit_shims_compatibility.py`
- **Description**: File with *shim* pattern in name
- **Purpose**: File named with pattern: *shim*
- **Suggested Action**: analyze
- **Risk Level**: low
- **Evidence**: Filename matches pattern: *shim*

**2. audit_shims_compatibility.py**
- **File**: `scripts/audit_shims_compatibility.py`
- **Description**: File with *compat* pattern in name
- **Purpose**: File named with pattern: *compat*
- **Suggested Action**: analyze
- **Risk Level**: low
- **Evidence**: Filename matches pattern: *compat*

**3. lifecycle_adapter.py**
- **File**: `the_alchemiser/execution/orders/lifecycle_adapter.py`
- **Description**: File with *adapter* pattern in name
- **Purpose**: File named with pattern: *adapter*
- **Suggested Action**: analyze
- **Risk Level**: low
- **Evidence**: Filename matches pattern: *adapter*

**4. execution_context_adapter.py**
- **File**: `the_alchemiser/execution/strategies/execution_context_adapter.py`
- **Description**: File with *adapter* pattern in name
- **Purpose**: File named with pattern: *adapter*
- **Suggested Action**: analyze
- **Risk Level**: low
- **Evidence**: Filename matches pattern: *adapter*

**5. adapter.py**
- **File**: `the_alchemiser/execution/brokers/alpaca/adapter.py`
- **Description**: File with *adapter* pattern in name
- **Purpose**: File named with pattern: *adapter*
- **Suggested Action**: analyze
- **Risk Level**: low
- **Evidence**: Filename matches pattern: *adapter*

**6. execution_context_adapter.py.backup**
- **File**: `the_alchemiser/execution/strategies/execution_context_adapter.py.backup`
- **Description**: Backup file with pattern: *.backup
- **Purpose**: Backup or temporary file
- **Suggested Action**: remove
- **Risk Level**: low
- **Evidence**: Backup file pattern: *.backup

**7. rebalance_execution_service.py.backup**
- **File**: `the_alchemiser/portfolio/allocation/rebalance_execution_service.py.backup`
- **Description**: Backup file with pattern: *.backup
- **Purpose**: Backup or temporary file
- **Suggested Action**: remove
- **Risk Level**: low
- **Evidence**: Backup file pattern: *.backup

## Recommendations

### Immediate Actions
1. **High Risk Items**: Require immediate attention and careful migration planning
2. **Active Imports**: Items with active imports need coordinated migration
3. **Backup Files**: Can likely be safely removed if no longer needed

### Risk Mitigation
1. **Never remove more than 5 shims without testing**
2. **Update import statements before removing shim files**
3. **Maintain compatibility during migration periods**
4. **Test thoroughly after each removal**

---

**Generated**: null
**Scope**: Complete codebase shims and compatibility audit
**Issue**: #492
**Tool**: scripts/audit_shims_compatibility.py