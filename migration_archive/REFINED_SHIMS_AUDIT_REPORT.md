# Refined Shims & Compatibility Layers Audit Report

## Executive Summary

This report provides a focused audit of **ACTUAL** shims, compatibility layers, and backward-compatibility code in the codebase. Unlike broader audits, this focuses on files that are genuinely shims or compatibility layers.

**Total Actual Shims Found**: 218

**Risk Distribution:**
- 🔴 **High Risk**: 178 items (active shims requiring careful migration)
- 🟡 **Medium Risk**: 38 items (import redirections and compatibility layers)
- 🟢 **Low Risk**: 2 items (backup files and cleanup items)

## Summary by Category

### Deprecated Code (72 items)

- 🔴 `scripts/rollback_legacy_deletions.py` - File explicitly marked with legacy/deprecated status
- 🔴 `the_alchemiser/main.py` (4 imports) - File explicitly marked with legacy/deprecated status
- 🔴 `examples/policy_layer_usage.py` - File explicitly marked with legacy/deprecated status
- 🔴 `the_alchemiser/execution/monitoring/websocket_order_monitor.py` (3 imports) - File explicitly marked with legacy/deprecated status
- 🔴 `the_alchemiser/execution/orders/order_validation_utils.py` - File explicitly marked with legacy/deprecated status
- 🔴 `the_alchemiser/execution/orders/service.py` (2 imports) - File explicitly marked with legacy/deprecated status
- 🔴 `the_alchemiser/execution/orders/validation.py` (2 imports) - File explicitly marked with legacy/deprecated status
- 🔴 `the_alchemiser/execution/orders/asset_order_handler.py` (1 imports) - File explicitly marked with legacy/deprecated status
- 🔴 `the_alchemiser/execution/core/execution_manager.py` (11 imports) - File explicitly marked with legacy/deprecated status
- 🔴 `the_alchemiser/execution/core/execution_manager_legacy.py` - File explicitly marked with legacy/deprecated status
- 🔴 `the_alchemiser/execution/core/execution_schemas.py` (12 imports) - File explicitly marked with legacy/deprecated status
- 🔴 `the_alchemiser/execution/core/canonical_executor.py` (6 imports) - File explicitly marked with legacy/deprecated status
- 🔴 `the_alchemiser/execution/mappers/account_mapping.py` (3 imports) - File explicitly marked with legacy/deprecated status
- 🔴 `the_alchemiser/execution/mappers/orders.py` (6 imports) - File explicitly marked with legacy/deprecated status
- 🔴 `the_alchemiser/execution/brokers/alpaca_client.py` (2 imports) - File explicitly marked with legacy/deprecated status
- 🔴 `the_alchemiser/execution/examples/canonical_integration.py` - File explicitly marked with legacy/deprecated status
- 🔴 `the_alchemiser/execution/strategies/smart_execution.py` (6 imports) - File explicitly marked with legacy/deprecated status
- 🔴 `the_alchemiser/execution/schemas/smart_trading.py` (1 imports) - File explicitly marked with legacy/deprecated status
- 🔴 `the_alchemiser/execution/brokers/alpaca/adapter.py` - File explicitly marked with legacy/deprecated status
- 🔴 `the_alchemiser/strategy/engines/nuclear_logic.py` - File explicitly marked with legacy/deprecated status
- 🔴 `the_alchemiser/strategy/engines/nuclear_typed_engine.py` (2 imports) - File explicitly marked with legacy/deprecated status
- 🔴 `the_alchemiser/strategy/data/domain_mapping.py` - File explicitly marked with legacy/deprecated status
- 🔴 `the_alchemiser/strategy/data/market_data_service.py` (8 imports) - File explicitly marked with legacy/deprecated status
- 🔴 `the_alchemiser/strategy/data/strategy_market_data_service.py` (1 imports) - File explicitly marked with legacy/deprecated status
- 🔴 `the_alchemiser/strategy/data/shared_market_data_service.py` - File explicitly marked with legacy/deprecated status
- 🔴 `the_alchemiser/strategy/mappers/market_data_adapter.py` (2 imports) - File explicitly marked with legacy/deprecated status
- 🔴 `the_alchemiser/strategy/mappers/strategy_signal_mapping.py` (3 imports) - File explicitly marked with legacy/deprecated status
- 🔴 `the_alchemiser/strategy/mappers/market_data_mapping.py` (4 imports) - File explicitly marked with legacy/deprecated status
- 🔴 `the_alchemiser/strategy/schemas/strategies.py` (2 imports) - File explicitly marked with legacy/deprecated status
- 🔴 `the_alchemiser/strategy/engines/protocols/__init__.py` - File explicitly marked with legacy/deprecated status
- 🔴 `the_alchemiser/strategy/engines/core/trading_engine.py` (3 imports) - File explicitly marked with legacy/deprecated status
- 🔴 `the_alchemiser/shared/utils/error_handling.py` - File explicitly marked with legacy/deprecated status
- 🔴 `the_alchemiser/shared/types/market_data_port.py` (10 imports) - File explicitly marked with legacy/deprecated status
- 🔴 `the_alchemiser/shared/config/bootstrap.py` (3 imports) - File explicitly marked with legacy/deprecated status
- 🔴 `the_alchemiser/shared/protocols/trading.py` - File explicitly marked with legacy/deprecated status
- 🔴 `the_alchemiser/shared/cli/signal_display_utils.py` - File explicitly marked with legacy/deprecated status
- 🔴 `the_alchemiser/shared/cli/signal_analyzer.py` (2 imports) - File explicitly marked with legacy/deprecated status
- 🔴 `the_alchemiser/shared/cli/cli_formatter.py` (4 imports) - File explicitly marked with legacy/deprecated status
- 🔴 `the_alchemiser/shared/cli/cli.py` - File explicitly marked with legacy/deprecated status
- 🔴 `the_alchemiser/shared/cli/trading_executor.py` (1 imports) - File explicitly marked with legacy/deprecated status
- 🔴 `the_alchemiser/shared/cli/dashboard_utils.py` (1 imports) - File explicitly marked with legacy/deprecated status
- 🔴 `the_alchemiser/shared/cli/portfolio_calculations.py` - File explicitly marked with legacy/deprecated status
- 🔴 `the_alchemiser/shared/value_objects/core_types.py` (40 imports) - File explicitly marked with legacy/deprecated status
- 🔴 `the_alchemiser/shared/mappers/execution_summary_mapping.py` - File explicitly marked with legacy/deprecated status
- 🔴 `the_alchemiser/shared/mappers/market_data_mappers.py` (1 imports) - File explicitly marked with legacy/deprecated status
- 🔴 `the_alchemiser/shared/schemas/execution_summary.py` - File explicitly marked with legacy/deprecated status
- 🔴 `the_alchemiser/shared/schemas/reporting.py` (3 imports) - File explicitly marked with legacy/deprecated status
- 🔴 `the_alchemiser/shared/schemas/enriched_data.py` (2 imports) - File explicitly marked with legacy/deprecated status
- 🔴 `the_alchemiser/portfolio/pnl/strategy_order_tracker.py` (6 imports) - File explicitly marked with legacy/deprecated status
- 🔴 `the_alchemiser/portfolio/holdings/position_manager.py` (1 imports) - File explicitly marked with legacy/deprecated status
- 🔴 `the_alchemiser/portfolio/calculations/portfolio_calculations.py` - File explicitly marked with legacy/deprecated status
- 🔴 `the_alchemiser/portfolio/mappers/tracking_normalization.py` - File explicitly marked with legacy/deprecated status
- 🔴 `the_alchemiser/portfolio/mappers/tracking.py` - File explicitly marked with legacy/deprecated status
- 🔴 `the_alchemiser/portfolio/policies/fractionability_policy_impl.py` (2 imports) - File explicitly marked with legacy/deprecated status
- 🔴 `the_alchemiser/portfolio/schemas/tracking.py` (4 imports) - File explicitly marked with legacy/deprecated status
- 🔴 `the_alchemiser/portfolio/state/symbol_classifier.py` - File explicitly marked with legacy/deprecated status
- 🔴 `the_alchemiser/execution/orders/asset_order_handler.py` (1 imports) - Contains actual deprecation warnings
- 🔴 `the_alchemiser/execution/brokers/alpaca_client.py` (2 imports) - Contains actual deprecation warnings
- 🔴 `the_alchemiser/shared/utils/error_handling.py` - Contains actual deprecation warnings
- 🔴 `the_alchemiser/portfolio/execution/execution_service.py` - Contains actual deprecation warnings
- 🔴 `the_alchemiser/portfolio/utils/portfolio_pnl_utils.py` (1 imports) - Contains actual deprecation warnings
- 🔴 `the_alchemiser/portfolio/holdings/position_manager.py` (1 imports) - Contains actual deprecation warnings
- 🔴 `the_alchemiser/portfolio/rebalancing/rebalance_plan.py` (2 imports) - Contains actual deprecation warnings
- 🔴 `the_alchemiser/portfolio/rebalancing/orchestrator.py` - Contains actual deprecation warnings
- 🔴 `the_alchemiser/portfolio/rebalancing/rebalancing_service.py` - Contains actual deprecation warnings
- 🔴 `the_alchemiser/portfolio/rebalancing/orchestrator_facade.py` (1 imports) - Contains actual deprecation warnings
- 🔴 `the_alchemiser/portfolio/analytics/analysis_service.py` - Contains actual deprecation warnings
- 🔴 `the_alchemiser/portfolio/analytics/position_analyzer.py` - Contains actual deprecation warnings
- 🔴 `the_alchemiser/portfolio/analytics/position_delta.py` - Contains actual deprecation warnings
- 🔴 `the_alchemiser/portfolio/analytics/attribution_engine.py` - Contains actual deprecation warnings
- 🔴 `the_alchemiser/portfolio/positions/position_service.py` (2 imports) - Contains actual deprecation warnings
- 🔴 `the_alchemiser/portfolio/positions/legacy_position_manager.py` (1 imports) - Contains actual deprecation warnings

### Import Redirections (81 items)

- 🟡 `scripts/migrate_phase2_imports.py` - Contains import redirections
- 🟡 `the_alchemiser/lambda_handler.py` - Contains import redirections
- 🟡 `the_alchemiser/execution/orders/order_validation_utils.py` - Contains import redirections
- 🟡 `the_alchemiser/execution/orders/__init__.py` - Contains import redirections
- 🟡 `the_alchemiser/execution/orders/lifecycle_adapter.py` - Contains import redirections
- 🟡 `the_alchemiser/execution/entities/__init__.py` - Contains import redirections
- 🟡 `the_alchemiser/execution/core/__init__.py` - Contains import redirections
- 🟡 `the_alchemiser/execution/core/execution_manager_legacy.py` - Contains import redirections
- 🟡 `the_alchemiser/execution/mappers/__init__.py` - Contains import redirections
- 🟡 `the_alchemiser/execution/examples/canonical_integration.py` - Contains import redirections
- 🟡 `the_alchemiser/execution/strategies/execution_context_adapter.py` - Contains import redirections
- 🟡 `the_alchemiser/execution/lifecycle/observers.py` - Contains import redirections
- 🟡 `the_alchemiser/execution/brokers/alpaca/adapter.py` - Contains import redirections
- 🟡 `the_alchemiser/strategy/data/__init__.py` - Contains import redirections
- 🟡 `the_alchemiser/strategy/data/domain_mapping.py` - Contains import redirections
- 🟡 `the_alchemiser/strategy/schemas/__init__.py` - Contains import redirections
- 🟡 `the_alchemiser/strategy/dsl/__init__.py` - Contains import redirections
- 🟡 `the_alchemiser/shared/utils/__init__.py` - Contains import redirections
- 🟡 `the_alchemiser/shared/utils/error_handling.py` - Contains import redirections
- 🟡 `the_alchemiser/shared/services/real_time_pricing.py` - Contains import redirections
- 🟡 `the_alchemiser/shared/types/__init__.py` - Contains import redirections
- 🟡 `the_alchemiser/shared/config/__init__.py` - Contains import redirections
- 🟡 `the_alchemiser/shared/protocols/trading.py` - Contains import redirections
- 🟡 `the_alchemiser/shared/value_objects/__init__.py` - Contains import redirections
- 🟡 `the_alchemiser/shared/mappers/execution_summary_mapping.py` - Contains import redirections
- 🟡 `the_alchemiser/shared/notifications/config.py` - Contains import redirections
- 🟡 `the_alchemiser/shared/schemas/execution_summary.py` - Contains import redirections
- 🟡 `the_alchemiser/shared/schemas/__init__.py` - Contains import redirections
- 🟡 `the_alchemiser/portfolio/execution/execution_service.py` - Contains import redirections
- 🟡 `the_alchemiser/portfolio/services/__init__.py` - Contains import redirections
- 🟡 `the_alchemiser/portfolio/rebalancing/orchestrator.py` - Contains import redirections
- 🟡 `the_alchemiser/portfolio/rebalancing/rebalancing_service.py` - Contains import redirections
- 🟡 `the_alchemiser/portfolio/mappers/__init__.py` - Contains import redirections
- 🟡 `the_alchemiser/portfolio/analytics/analysis_service.py` - Contains import redirections
- 🟡 `the_alchemiser/portfolio/analytics/position_analyzer.py` - Contains import redirections
- 🟡 `the_alchemiser/portfolio/analytics/position_delta.py` - Contains import redirections
- 🟡 `the_alchemiser/portfolio/analytics/attribution_engine.py` - Contains import redirections
- 🟡 `the_alchemiser/portfolio/schemas/__init__.py` - Contains import redirections
- 🔴 `the_alchemiser/main.py` (4 imports) - Contains import redirections
- 🔴 `the_alchemiser/execution/orders/order_schemas.py` (16 imports) - Contains import redirections
- 🔴 `the_alchemiser/execution/orders/validation.py` (2 imports) - Contains import redirections
- 🔴 `the_alchemiser/execution/orders/asset_order_handler.py` (1 imports) - Contains import redirections
- 🔴 `the_alchemiser/execution/core/execution_schemas.py` (12 imports) - Contains import redirections
- 🔴 `the_alchemiser/execution/core/account_facade.py` (1 imports) - Contains import redirections
- 🔴 `the_alchemiser/execution/core/canonical_executor.py` (6 imports) - Contains import redirections
- 🔴 `the_alchemiser/execution/mappers/orders.py` (6 imports) - Contains import redirections
- 🔴 `the_alchemiser/execution/brokers/alpaca_client.py` (2 imports) - Contains import redirections
- 🔴 `the_alchemiser/execution/strategies/smart_execution.py` (6 imports) - Contains import redirections
- 🔴 `the_alchemiser/strategy/engines/tecl_strategy_engine.py` (2 imports) - Contains import redirections
- 🔴 `the_alchemiser/strategy/engines/nuclear_typed_engine.py` (2 imports) - Contains import redirections
- 🔴 `the_alchemiser/strategy/engines/typed_klm_ensemble_engine.py` (3 imports) - Contains import redirections
- 🔴 `the_alchemiser/strategy/data/strategy_market_data_service.py` (1 imports) - Contains import redirections
- 🔴 `the_alchemiser/strategy/mappers/market_data_mapping.py` (4 imports) - Contains import redirections
- 🔴 `the_alchemiser/strategy/schemas/strategies.py` (2 imports) - Contains import redirections
- 🔴 `the_alchemiser/strategy/engines/core/trading_engine.py` (3 imports) - Contains import redirections
- 🔴 `the_alchemiser/strategy/engines/models/strategy_position_model.py` (1 imports) - Contains import redirections
- 🔴 `the_alchemiser/shared/utils/service_factory.py` (1 imports) - Contains import redirections
- 🔴 `the_alchemiser/shared/services/tick_size_service.py` (2 imports) - Contains import redirections
- 🔴 `the_alchemiser/shared/errors/error_handler.py` (11 imports) - Contains import redirections
- 🔴 `the_alchemiser/shared/config/service_providers.py` (1 imports) - Contains import redirections
- 🔴 `the_alchemiser/shared/config/infrastructure_providers.py` (1 imports) - Contains import redirections
- 🔴 `the_alchemiser/shared/config/bootstrap.py` (3 imports) - Contains import redirections
- 🔴 `the_alchemiser/shared/protocols/repository.py` (5 imports) - Contains import redirections
- 🔴 `the_alchemiser/shared/value_objects/core_types.py` (40 imports) - Contains import redirections
- 🔴 `the_alchemiser/shared/notifications/email_utils.py` (1 imports) - Contains import redirections
- 🔴 `the_alchemiser/shared/notifications/client.py` (1 imports) - Contains import redirections
- 🔴 `the_alchemiser/shared/schemas/base.py` (8 imports) - Contains import redirections
- 🔴 `the_alchemiser/shared/schemas/accounts.py` (4 imports) - Contains import redirections
- 🔴 `the_alchemiser/shared/schemas/enriched_data.py` (2 imports) - Contains import redirections
- 🔴 `the_alchemiser/shared/schemas/operations.py` (2 imports) - Contains import redirections
- 🔴 `the_alchemiser/shared/schemas/market_data.py` (2 imports) - Contains import redirections
- 🔴 `the_alchemiser/portfolio/utils/portfolio_pnl_utils.py` (1 imports) - Contains import redirections
- 🔴 `the_alchemiser/portfolio/pnl/strategy_order_tracker.py` (6 imports) - Contains import redirections
- 🔴 `the_alchemiser/portfolio/holdings/position_manager.py` (1 imports) - Contains import redirections
- 🔴 `the_alchemiser/portfolio/rebalancing/rebalance_plan.py` (2 imports) - Contains import redirections
- 🔴 `the_alchemiser/portfolio/rebalancing/orchestrator_facade.py` (1 imports) - Contains import redirections
- 🔴 `the_alchemiser/portfolio/core/rebalancing_orchestrator_facade.py` (1 imports) - Contains import redirections
- 🔴 `the_alchemiser/portfolio/mappers/portfolio_rebalancing_mapping.py` (2 imports) - Contains import redirections
- 🔴 `the_alchemiser/portfolio/positions/position_service.py` (2 imports) - Contains import redirections
- 🔴 `the_alchemiser/portfolio/positions/legacy_position_manager.py` (1 imports) - Contains import redirections
- 🔴 `the_alchemiser/portfolio/schemas/positions.py` (2 imports) - Contains import redirections

### Backup Files (2 items)

- 🟢 `the_alchemiser/execution/strategies/execution_context_adapter.py.backup` - Backup file
- 🟢 `the_alchemiser/portfolio/allocation/rebalance_execution_service.py.backup` - Backup file

### Legacy Named Files (5 items)

- 🔴 `scripts/rollback_legacy_deletions.py` - File explicitly named with *legacy*
- 🔴 `scripts/delete_legacy_safe.py` - File explicitly named with *legacy*
- 🔴 `the_alchemiser/execution/core/execution_manager_legacy.py` - File explicitly named with *legacy*
- 🔴 `the_alchemiser/shared/types/symbol_legacy.py` (7 imports) - File explicitly named with *legacy*
- 🔴 `the_alchemiser/portfolio/positions/legacy_position_manager.py` (1 imports) - File explicitly named with *legacy*

### Compatibility Shims (58 items)

- 🔴 `the_alchemiser/main.py` (4 imports) - File explicitly describes itself as a compatibility shim
- 🔴 `the_alchemiser/lambda_handler.py` - File explicitly describes itself as a compatibility shim
- 🔴 `the_alchemiser/execution/orders/order_schemas.py` (16 imports) - File explicitly describes itself as a compatibility shim
- 🔴 `the_alchemiser/execution/orders/asset_order_handler.py` (1 imports) - File explicitly describes itself as a compatibility shim
- 🔴 `the_alchemiser/execution/core/execution_manager_legacy.py` - File explicitly describes itself as a compatibility shim
- 🔴 `the_alchemiser/execution/core/execution_schemas.py` (12 imports) - File explicitly describes itself as a compatibility shim
- 🔴 `the_alchemiser/execution/core/account_facade.py` (1 imports) - File explicitly describes itself as a compatibility shim
- 🔴 `the_alchemiser/execution/core/canonical_executor.py` (6 imports) - File explicitly describes itself as a compatibility shim
- 🔴 `the_alchemiser/execution/mappers/orders.py` (6 imports) - File explicitly describes itself as a compatibility shim
- 🔴 `the_alchemiser/execution/brokers/alpaca_client.py` (2 imports) - File explicitly describes itself as a compatibility shim
- 🔴 `the_alchemiser/execution/strategies/smart_execution.py` (6 imports) - File explicitly describes itself as a compatibility shim
- 🔴 `the_alchemiser/execution/lifecycle/observers.py` - File explicitly describes itself as a compatibility shim
- 🔴 `the_alchemiser/execution/brokers/alpaca/adapter.py` - File explicitly describes itself as a compatibility shim
- 🔴 `the_alchemiser/strategy/engines/tecl_strategy_engine.py` (2 imports) - File explicitly describes itself as a compatibility shim
- 🔴 `the_alchemiser/strategy/engines/nuclear_typed_engine.py` (2 imports) - File explicitly describes itself as a compatibility shim
- 🔴 `the_alchemiser/strategy/engines/typed_klm_ensemble_engine.py` (3 imports) - File explicitly describes itself as a compatibility shim
- 🔴 `the_alchemiser/strategy/data/domain_mapping.py` - File explicitly describes itself as a compatibility shim
- 🔴 `the_alchemiser/strategy/data/strategy_market_data_service.py` (1 imports) - File explicitly describes itself as a compatibility shim
- 🔴 `the_alchemiser/strategy/mappers/market_data_mapping.py` (4 imports) - File explicitly describes itself as a compatibility shim
- 🔴 `the_alchemiser/strategy/schemas/strategies.py` (2 imports) - File explicitly describes itself as a compatibility shim
- 🔴 `the_alchemiser/strategy/engines/core/trading_engine.py` (3 imports) - File explicitly describes itself as a compatibility shim
- 🔴 `the_alchemiser/strategy/engines/models/strategy_position_model.py` (1 imports) - File explicitly describes itself as a compatibility shim
- 🔴 `the_alchemiser/shared/utils/service_factory.py` (1 imports) - File explicitly describes itself as a compatibility shim
- 🔴 `the_alchemiser/shared/utils/error_handling.py` - File explicitly describes itself as a compatibility shim
- 🔴 `the_alchemiser/shared/services/real_time_pricing.py` - File explicitly describes itself as a compatibility shim
- 🔴 `the_alchemiser/shared/errors/error_handler.py` (11 imports) - File explicitly describes itself as a compatibility shim
- 🔴 `the_alchemiser/shared/config/service_providers.py` (1 imports) - File explicitly describes itself as a compatibility shim
- 🔴 `the_alchemiser/shared/config/infrastructure_providers.py` (1 imports) - File explicitly describes itself as a compatibility shim
- 🔴 `the_alchemiser/shared/config/bootstrap.py` (3 imports) - File explicitly describes itself as a compatibility shim
- 🔴 `the_alchemiser/shared/protocols/repository.py` (5 imports) - File explicitly describes itself as a compatibility shim
- 🔴 `the_alchemiser/shared/value_objects/core_types.py` (40 imports) - File explicitly describes itself as a compatibility shim
- 🔴 `the_alchemiser/shared/mappers/execution_summary_mapping.py` - File explicitly describes itself as a compatibility shim
- 🔴 `the_alchemiser/shared/notifications/email_utils.py` (1 imports) - File explicitly describes itself as a compatibility shim
- 🔴 `the_alchemiser/shared/notifications/config.py` - File explicitly describes itself as a compatibility shim
- 🔴 `the_alchemiser/shared/notifications/client.py` (1 imports) - File explicitly describes itself as a compatibility shim
- 🔴 `the_alchemiser/shared/schemas/base.py` (8 imports) - File explicitly describes itself as a compatibility shim
- 🔴 `the_alchemiser/shared/schemas/execution_summary.py` - File explicitly describes itself as a compatibility shim
- 🔴 `the_alchemiser/shared/schemas/accounts.py` (4 imports) - File explicitly describes itself as a compatibility shim
- 🔴 `the_alchemiser/shared/schemas/enriched_data.py` (2 imports) - File explicitly describes itself as a compatibility shim
- 🔴 `the_alchemiser/shared/schemas/operations.py` (2 imports) - File explicitly describes itself as a compatibility shim
- 🔴 `the_alchemiser/shared/schemas/market_data.py` (2 imports) - File explicitly describes itself as a compatibility shim
- 🔴 `the_alchemiser/portfolio/execution/execution_service.py` - File explicitly describes itself as a compatibility shim
- 🔴 `the_alchemiser/portfolio/utils/portfolio_pnl_utils.py` (1 imports) - File explicitly describes itself as a compatibility shim
- 🔴 `the_alchemiser/portfolio/pnl/strategy_order_tracker.py` (6 imports) - File explicitly describes itself as a compatibility shim
- 🔴 `the_alchemiser/portfolio/holdings/position_manager.py` (1 imports) - File explicitly describes itself as a compatibility shim
- 🔴 `the_alchemiser/portfolio/rebalancing/rebalance_plan.py` (2 imports) - File explicitly describes itself as a compatibility shim
- 🔴 `the_alchemiser/portfolio/rebalancing/orchestrator.py` - File explicitly describes itself as a compatibility shim
- 🔴 `the_alchemiser/portfolio/rebalancing/rebalancing_service.py` - File explicitly describes itself as a compatibility shim
- 🔴 `the_alchemiser/portfolio/rebalancing/orchestrator_facade.py` (1 imports) - File explicitly describes itself as a compatibility shim
- 🔴 `the_alchemiser/portfolio/core/rebalancing_orchestrator_facade.py` (1 imports) - File explicitly describes itself as a compatibility shim
- 🔴 `the_alchemiser/portfolio/mappers/portfolio_rebalancing_mapping.py` (2 imports) - File explicitly describes itself as a compatibility shim
- 🔴 `the_alchemiser/portfolio/analytics/analysis_service.py` - File explicitly describes itself as a compatibility shim
- 🔴 `the_alchemiser/portfolio/analytics/position_analyzer.py` - File explicitly describes itself as a compatibility shim
- 🔴 `the_alchemiser/portfolio/analytics/position_delta.py` - File explicitly describes itself as a compatibility shim
- 🔴 `the_alchemiser/portfolio/analytics/attribution_engine.py` - File explicitly describes itself as a compatibility shim
- 🔴 `the_alchemiser/portfolio/positions/position_service.py` (2 imports) - File explicitly describes itself as a compatibility shim
- 🔴 `the_alchemiser/portfolio/positions/legacy_position_manager.py` (1 imports) - File explicitly describes itself as a compatibility shim
- 🔴 `the_alchemiser/portfolio/schemas/positions.py` (2 imports) - File explicitly describes itself as a compatibility shim

## Detailed Analysis

### 🔴 HIGH RISK SHIMS (178 items)

**1. rollback_legacy_deletions.py**
- **File**: `scripts/rollback_legacy_deletions.py`
- **Description**: File explicitly marked with legacy/deprecated status
- **Purpose**: File with explicit legacy/deprecated status marker
- **Suggested Action**: review_for_migration
- **Evidence**: Status markers: """
Legacy Deletion Rollback Script

This script can rollback the safe deletions if needed by restor...

**2. main.py**
- **File**: `the_alchemiser/main.py`
- **Description**: File explicitly marked with legacy/deprecated status
- **Purpose**: File with explicit legacy/deprecated status marker
- **Suggested Action**: review_for_migration
- **Active Imports**: 4 files importing this shim
- **Evidence**: Status markers: """Business Unit: utilities; Status: current.

Main Entry Point for The Alchemiser Trading System.

...; Actively imported by 4 files

**3. policy_layer_usage.py**
- **File**: `examples/policy_layer_usage.py`
- **Description**: File explicitly marked with legacy/deprecated status
- **Purpose**: File with explicit legacy/deprecated status marker
- **Suggested Action**: review_for_migration
- **Evidence**: Status markers: """Business Unit: utilities; Status: legacy.

Unified Policy Layer Usage Example

This example demon...

**4. websocket_order_monitor.py**
- **File**: `the_alchemiser/execution/monitoring/websocket_order_monitor.py`
- **Description**: File explicitly marked with legacy/deprecated status
- **Purpose**: File with explicit legacy/deprecated status marker
- **Suggested Action**: review_for_migration
- **Active Imports**: 3 files importing this shim
- **Evidence**: Status markers: """Business Unit: execution | Status: current

WebSocket Order Monitoring Utilities.

This module pr...; Actively imported by 3 files

**5. order_validation_utils.py**
- **File**: `the_alchemiser/execution/orders/order_validation_utils.py`
- **Description**: File explicitly marked with legacy/deprecated status
- **Purpose**: File with explicit legacy/deprecated status marker
- **Suggested Action**: review_for_migration
- **Evidence**: Status markers: """Business Unit: execution | Status: current.

Order Validation Utilities.

This module provides he...

**6. service.py**
- **File**: `the_alchemiser/execution/orders/service.py`
- **Description**: File explicitly marked with legacy/deprecated status
- **Purpose**: File with explicit legacy/deprecated status marker
- **Suggested Action**: review_for_migration
- **Active Imports**: 2 files importing this shim
- **Evidence**: Status markers: """Business Unit: execution; Status: current.

Enhanced Order Service.

This service provides type-s...; Actively imported by 2 files

**7. validation.py**
- **File**: `the_alchemiser/execution/orders/validation.py`
- **Description**: File explicitly marked with legacy/deprecated status
- **Purpose**: File with explicit legacy/deprecated status marker
- **Suggested Action**: review_for_migration
- **Active Imports**: 2 files importing this shim
- **Evidence**: Status markers: """Business Unit: execution | Status: current.

Order Validation and Type Safety Module.

This modul...; Actively imported by 2 files

**8. asset_order_handler.py**
- **File**: `the_alchemiser/execution/orders/asset_order_handler.py`
- **Description**: File explicitly marked with legacy/deprecated status
- **Purpose**: File with explicit legacy/deprecated status marker
- **Suggested Action**: review_for_migration
- **Active Imports**: 1 files importing this shim
- **Evidence**: Status markers: """Business Unit: execution; Status: current.

Asset-Specific Order Logic.

This module handles asse...; Actively imported by 1 files

**9. execution_manager.py**
- **File**: `the_alchemiser/execution/core/execution_manager.py`
- **Description**: File explicitly marked with legacy/deprecated status
- **Purpose**: File with explicit legacy/deprecated status marker
- **Suggested Action**: review_for_migration
- **Active Imports**: 11 files importing this shim
- **Evidence**: Status markers: """Business Unit: execution | Status: current

Trading service facade aggregating order, position, m...; Actively imported by 11 files

**10. execution_manager_legacy.py**
- **File**: `the_alchemiser/execution/core/execution_manager_legacy.py`
- **Description**: File explicitly marked with legacy/deprecated status
- **Purpose**: File with explicit legacy/deprecated status marker
- **Suggested Action**: review_for_migration
- **Evidence**: Status markers: """Business Unit: execution; Status: legacy.

CRITICAL: This module has moved to the_alchemiser.exec...

**11. execution_schemas.py**
- **File**: `the_alchemiser/execution/core/execution_schemas.py`
- **Description**: File explicitly marked with legacy/deprecated status
- **Purpose**: File with explicit legacy/deprecated status marker
- **Suggested Action**: review_for_migration
- **Active Imports**: 12 files importing this shim
- **Evidence**: Status markers: """Business Unit: order execution/placement; Status: current.

Trading execution and result DTOs for...; Actively imported by 12 files

**12. canonical_executor.py**
- **File**: `the_alchemiser/execution/core/canonical_executor.py`
- **Description**: File explicitly marked with legacy/deprecated status
- **Purpose**: File with explicit legacy/deprecated status marker
- **Suggested Action**: review_for_migration
- **Active Imports**: 6 files importing this shim
- **Evidence**: Status markers: """Business Unit: execution; Status: legacy.

CRITICAL: This module has moved to the_alchemiser.exec...; Actively imported by 6 files

**13. account_mapping.py**
- **File**: `the_alchemiser/execution/mappers/account_mapping.py`
- **Description**: File explicitly marked with legacy/deprecated status
- **Purpose**: File with explicit legacy/deprecated status marker
- **Suggested Action**: review_for_migration
- **Active Imports**: 3 files importing this shim
- **Evidence**: Status markers: """Business Unit: utilities; Status: current."""

from __future__ import annotations

from dataclass...; Actively imported by 3 files

**14. orders.py**
- **File**: `the_alchemiser/execution/mappers/orders.py`
- **Description**: File explicitly marked with legacy/deprecated status
- **Purpose**: File with explicit legacy/deprecated status marker
- **Suggested Action**: review_for_migration
- **Active Imports**: 6 files importing this shim
- **Evidence**: Status markers: """Business Unit: order execution/placement; Status: current.

Order mapping utilities and status no...; Actively imported by 6 files

**15. alpaca_client.py**
- **File**: `the_alchemiser/execution/brokers/alpaca_client.py`
- **Description**: File explicitly marked with legacy/deprecated status
- **Purpose**: File with explicit legacy/deprecated status marker
- **Suggested Action**: review_for_migration
- **Active Imports**: 2 files importing this shim
- **Evidence**: Status markers: """Business Unit: execution | Status: current

Alpaca Client for Direct API Access.

A streamlined, ...; Actively imported by 2 files

**16. canonical_integration.py**
- **File**: `the_alchemiser/execution/examples/canonical_integration.py`
- **Description**: File explicitly marked with legacy/deprecated status
- **Purpose**: File with explicit legacy/deprecated status marker
- **Suggested Action**: review_for_migration
- **Evidence**: Status markers: """Business Unit: execution | Status: current.

Integration example for canonical order executor.

T...

**17. smart_execution.py**
- **File**: `the_alchemiser/execution/strategies/smart_execution.py`
- **Description**: File explicitly marked with legacy/deprecated status
- **Purpose**: File with explicit legacy/deprecated status marker
- **Suggested Action**: review_for_migration
- **Active Imports**: 6 files importing this shim
- **Evidence**: Status markers: """Business Unit: order execution/placement; Status: current.

Smart Execution Engine with Professio...; Actively imported by 6 files

**18. smart_trading.py**
- **File**: `the_alchemiser/execution/schemas/smart_trading.py`
- **Description**: File explicitly marked with legacy/deprecated status
- **Purpose**: File with explicit legacy/deprecated status marker
- **Suggested Action**: review_for_migration
- **Active Imports**: 1 files importing this shim
- **Evidence**: Status markers: """Business Unit: shared | Status: current

Smart Trading - migrated from legacy location.
"""

#!/u...; Actively imported by 1 files

**19. adapter.py**
- **File**: `the_alchemiser/execution/brokers/alpaca/adapter.py`
- **Description**: File explicitly marked with legacy/deprecated status
- **Purpose**: File with explicit legacy/deprecated status marker
- **Suggested Action**: review_for_migration
- **Evidence**: Status markers: """Business Unit: execution; Status: current.

Alpaca broker adapter for execution module.

This mod...

**20. nuclear_logic.py**
- **File**: `the_alchemiser/strategy/engines/nuclear_logic.py`
- **Description**: File explicitly marked with legacy/deprecated status
- **Purpose**: File with explicit legacy/deprecated status marker
- **Suggested Action**: review_for_migration
- **Evidence**: Status markers: """Business Unit: utilities; Status: current.

Pure evaluation logic for the Nuclear strategy (typed...

**21. nuclear_typed_engine.py**
- **File**: `the_alchemiser/strategy/engines/nuclear_typed_engine.py`
- **Description**: File explicitly marked with legacy/deprecated status
- **Purpose**: File with explicit legacy/deprecated status marker
- **Suggested Action**: review_for_migration
- **Active Imports**: 2 files importing this shim
- **Evidence**: Status markers: """Business Unit: utilities; Status: current.

Typed Nuclear Strategy Engine.

Typed implementation ...; Actively imported by 2 files

**22. domain_mapping.py**
- **File**: `the_alchemiser/strategy/data/domain_mapping.py`
- **Description**: File explicitly marked with legacy/deprecated status
- **Purpose**: File with explicit legacy/deprecated status marker
- **Suggested Action**: review_for_migration
- **Evidence**: Status markers: """Business Unit: strategy & signal generation; Status: current.

Mapping utilities between strategy...

**23. market_data_service.py**
- **File**: `the_alchemiser/strategy/data/market_data_service.py`
- **Description**: File explicitly marked with legacy/deprecated status
- **Purpose**: File with explicit legacy/deprecated status marker
- **Suggested Action**: review_for_migration
- **Active Imports**: 8 files importing this shim
- **Evidence**: Status markers: """Business Unit: utilities; Status: current.

Market Data Service - Enhanced market data operations...; Actively imported by 8 files

**24. strategy_market_data_service.py**
- **File**: `the_alchemiser/strategy/data/strategy_market_data_service.py`
- **Description**: File explicitly marked with legacy/deprecated status
- **Purpose**: File with explicit legacy/deprecated status marker
- **Suggested Action**: review_for_migration
- **Active Imports**: 1 files importing this shim
- **Evidence**: Status markers: """Business Unit: strategy & signal generation; Status: current.

Strategy Market Data Service - Can...; Actively imported by 1 files

**25. shared_market_data_service.py**
- **File**: `the_alchemiser/strategy/data/shared_market_data_service.py`
- **Description**: File explicitly marked with legacy/deprecated status
- **Purpose**: File with explicit legacy/deprecated status marker
- **Suggested Action**: review_for_migration
- **Evidence**: Status markers: """Business Unit: utilities; Status: current.

Market data services package exports.

Prefer MarketD...

**26. market_data_adapter.py**
- **File**: `the_alchemiser/strategy/mappers/market_data_adapter.py`
- **Description**: File explicitly marked with legacy/deprecated status
- **Purpose**: File with explicit legacy/deprecated status marker
- **Suggested Action**: review_for_migration
- **Active Imports**: 2 files importing this shim
- **Evidence**: Status markers: """Business Unit: strategy & signal generation; Status: current.

Strategy market data adapter for D...; Actively imported by 2 files

**27. strategy_signal_mapping.py**
- **File**: `the_alchemiser/strategy/mappers/strategy_signal_mapping.py`
- **Description**: File explicitly marked with legacy/deprecated status
- **Purpose**: File with explicit legacy/deprecated status marker
- **Suggested Action**: review_for_migration
- **Active Imports**: 3 files importing this shim
- **Evidence**: Status markers: """Business Unit: strategy & signal generation; Status: current.

Mapping utilities for strategy sig...; Actively imported by 3 files

**28. market_data_mapping.py**
- **File**: `the_alchemiser/strategy/mappers/market_data_mapping.py`
- **Description**: File explicitly marked with legacy/deprecated status
- **Purpose**: File with explicit legacy/deprecated status marker
- **Suggested Action**: review_for_migration
- **Active Imports**: 4 files importing this shim
- **Evidence**: Status markers: """Business Unit: utilities; Status: current.

Market data mapping utilities for strategy adaptation...; Actively imported by 4 files

**29. strategies.py**
- **File**: `the_alchemiser/strategy/schemas/strategies.py`
- **Description**: File explicitly marked with legacy/deprecated status
- **Purpose**: File with explicit legacy/deprecated status marker
- **Suggested Action**: review_for_migration
- **Active Imports**: 2 files importing this shim
- **Evidence**: Status markers: """Business Unit: utilities; Status: current.

Pure mapping functions for strategy signals to displa...; Actively imported by 2 files

**30. __init__.py**
- **File**: `the_alchemiser/strategy/engines/protocols/__init__.py`
- **Description**: File explicitly marked with legacy/deprecated status
- **Purpose**: File with explicit legacy/deprecated status marker
- **Suggested Action**: review_for_migration
- **Evidence**: Status markers: """Business Unit: utilities; Status: current."""

from __future__ import annotations

from .strategy...

**31. trading_engine.py**
- **File**: `the_alchemiser/strategy/engines/core/trading_engine.py`
- **Description**: File explicitly marked with legacy/deprecated status
- **Purpose**: File with explicit legacy/deprecated status marker
- **Suggested Action**: review_for_migration
- **Active Imports**: 3 files importing this shim
- **Evidence**: Status markers: """Business Unit: order execution/placement; Status: current.

Trading Engine for The Alchemiser.

U...; Actively imported by 3 files

**32. error_handling.py**
- **File**: `the_alchemiser/shared/utils/error_handling.py`
- **Description**: File explicitly marked with legacy/deprecated status
- **Purpose**: File with explicit legacy/deprecated status marker
- **Suggested Action**: review_for_migration
- **Evidence**: Status markers: """Business Unit: utilities; Status: current.

[DEPRECATED] Legacy error handling utilities.

This m...

**33. market_data_port.py**
- **File**: `the_alchemiser/shared/types/market_data_port.py`
- **Description**: File explicitly marked with legacy/deprecated status
- **Purpose**: File with explicit legacy/deprecated status marker
- **Suggested Action**: review_for_migration
- **Active Imports**: 10 files importing this shim
- **Evidence**: Status markers: """Business Unit: utilities; Status: current.

Domain port for market data access.

This port define...; Actively imported by 10 files

**34. bootstrap.py**
- **File**: `the_alchemiser/shared/config/bootstrap.py`
- **Description**: File explicitly marked with legacy/deprecated status
- **Purpose**: File with explicit legacy/deprecated status marker
- **Suggested Action**: review_for_migration
- **Active Imports**: 3 files importing this shim
- **Evidence**: Status markers: """Business Unit: order execution/placement; Status: current.

Trading Engine Bootstrap Module.

Enc...; Actively imported by 3 files

**35. trading.py**
- **File**: `the_alchemiser/shared/protocols/trading.py`
- **Description**: File explicitly marked with legacy/deprecated status
- **Purpose**: File with explicit legacy/deprecated status marker
- **Suggested Action**: review_for_migration
- **Evidence**: Status markers: """Business Unit: order execution/placement; Status: current.

Application-layer ports module for tr...

**36. signal_display_utils.py**
- **File**: `the_alchemiser/shared/cli/signal_display_utils.py`
- **Description**: File explicitly marked with legacy/deprecated status
- **Purpose**: File with explicit legacy/deprecated status marker
- **Suggested Action**: review_for_migration
- **Evidence**: Status markers: """Business Unit: shared; Status: current.

Signal Display Utilities.

This module provides helper f...

**37. signal_analyzer.py**
- **File**: `the_alchemiser/shared/cli/signal_analyzer.py`
- **Description**: File explicitly marked with legacy/deprecated status
- **Purpose**: File with explicit legacy/deprecated status marker
- **Suggested Action**: review_for_migration
- **Active Imports**: 2 files importing this shim
- **Evidence**: Status markers: """Business Unit: shared | Status: current

Signal analysis CLI module.

Handles signal generation a...; Actively imported by 2 files

**38. cli_formatter.py**
- **File**: `the_alchemiser/shared/cli/cli_formatter.py`
- **Description**: File explicitly marked with legacy/deprecated status
- **Purpose**: File with explicit legacy/deprecated status marker
- **Suggested Action**: review_for_migration
- **Active Imports**: 4 files importing this shim
- **Evidence**: Status markers: """Business Unit: shared | Status: current

CLI formatting utilities for the trading system.
"""

fr...; Actively imported by 4 files

**39. cli.py**
- **File**: `the_alchemiser/shared/cli/cli.py`
- **Description**: File explicitly marked with legacy/deprecated status
- **Purpose**: File with explicit legacy/deprecated status marker
- **Suggested Action**: review_for_migration
- **Evidence**: Status markers: """Business Unit: shared | Status: current

Command-Line Interface for The Alchemiser Quantitative T...

**40. trading_executor.py**
- **File**: `the_alchemiser/shared/cli/trading_executor.py`
- **Description**: File explicitly marked with legacy/deprecated status
- **Purpose**: File with explicit legacy/deprecated status marker
- **Suggested Action**: review_for_migration
- **Active Imports**: 1 files importing this shim
- **Evidence**: Status markers: """Business Unit: shared | Status: current

Trading execution CLI module.

Handles trading execution...; Actively imported by 1 files

**41. dashboard_utils.py**
- **File**: `the_alchemiser/shared/cli/dashboard_utils.py`
- **Description**: File explicitly marked with legacy/deprecated status
- **Purpose**: File with explicit legacy/deprecated status marker
- **Suggested Action**: review_for_migration
- **Active Imports**: 1 files importing this shim
- **Evidence**: Status markers: """Business Unit: shared | Status: current

Dashboard Utils - migrated from legacy location.
"""

#!...; Actively imported by 1 files

**42. portfolio_calculations.py**
- **File**: `the_alchemiser/shared/cli/portfolio_calculations.py`
- **Description**: File explicitly marked with legacy/deprecated status
- **Purpose**: File with explicit legacy/deprecated status marker
- **Suggested Action**: review_for_migration
- **Evidence**: Status markers: """Business Unit: shared | Status: current

Portfolio Calculations - migrated from legacy location.
...

**43. core_types.py**
- **File**: `the_alchemiser/shared/value_objects/core_types.py`
- **Description**: File explicitly marked with legacy/deprecated status
- **Purpose**: File with explicit legacy/deprecated status marker
- **Suggested Action**: review_for_migration
- **Active Imports**: 40 files importing this shim
- **Evidence**: Status markers: """Business Unit: utilities; Status: current.

Core type definitions for The Alchemiser trading syst...; Actively imported by 40 files

**44. execution_summary_mapping.py**
- **File**: `the_alchemiser/shared/mappers/execution_summary_mapping.py`
- **Description**: File explicitly marked with legacy/deprecated status
- **Purpose**: File with explicit legacy/deprecated status marker
- **Suggested Action**: review_for_migration
- **Evidence**: Status markers: """Business Unit: shared | Status: current

Execution Summary Mapping - migrated from legacy locatio...

**45. market_data_mappers.py**
- **File**: `the_alchemiser/shared/mappers/market_data_mappers.py`
- **Description**: File explicitly marked with legacy/deprecated status
- **Purpose**: File with explicit legacy/deprecated status marker
- **Suggested Action**: review_for_migration
- **Active Imports**: 1 files importing this shim
- **Evidence**: Status markers: """Business Unit: shared | Status: current

Market Data Mappers - migrated from legacy location.
"""...; Actively imported by 1 files

**46. execution_summary.py**
- **File**: `the_alchemiser/shared/schemas/execution_summary.py`
- **Description**: File explicitly marked with legacy/deprecated status
- **Purpose**: File with explicit legacy/deprecated status marker
- **Suggested Action**: review_for_migration
- **Evidence**: Status markers: """Business Unit: shared | Status: current

Execution Summary - migrated from legacy location.
"""

...

**47. reporting.py**
- **File**: `the_alchemiser/shared/schemas/reporting.py`
- **Description**: File explicitly marked with legacy/deprecated status
- **Purpose**: File with explicit legacy/deprecated status marker
- **Suggested Action**: review_for_migration
- **Active Imports**: 3 files importing this shim
- **Evidence**: Status markers: """Business Unit: shared | Status: current

Reporting - migrated from legacy location.
"""

#!/usr/b...; Actively imported by 3 files

**48. enriched_data.py**
- **File**: `the_alchemiser/shared/schemas/enriched_data.py`
- **Description**: File explicitly marked with legacy/deprecated status
- **Purpose**: File with explicit legacy/deprecated status marker
- **Suggested Action**: review_for_migration
- **Active Imports**: 2 files importing this shim
- **Evidence**: Status markers: """Business Unit: shared | Status: current

Enriched Data - migrated from legacy location.
"""

#!/u...; Actively imported by 2 files

**49. strategy_order_tracker.py**
- **File**: `the_alchemiser/portfolio/pnl/strategy_order_tracker.py`
- **Description**: File explicitly marked with legacy/deprecated status
- **Purpose**: File with explicit legacy/deprecated status marker
- **Suggested Action**: review_for_migration
- **Active Imports**: 6 files importing this shim
- **Evidence**: Status markers: """Business Unit: strategy & signal generation; Status: current.

Strategy Order Tracker for Per-Str...; Actively imported by 6 files

**50. position_manager.py**
- **File**: `the_alchemiser/portfolio/holdings/position_manager.py`
- **Description**: File explicitly marked with legacy/deprecated status
- **Purpose**: File with explicit legacy/deprecated status marker
- **Suggested Action**: review_for_migration
- **Active Imports**: 1 files importing this shim
- **Evidence**: Status markers: """Business Unit: order execution/placement; Status: current.

Position Management Utilities.

This ...; Actively imported by 1 files

**51. portfolio_calculations.py**
- **File**: `the_alchemiser/portfolio/calculations/portfolio_calculations.py`
- **Description**: File explicitly marked with legacy/deprecated status
- **Purpose**: File with explicit legacy/deprecated status marker
- **Suggested Action**: review_for_migration
- **Evidence**: Status markers: """Business Unit: portfolio assessment & management; Status: current.

Portfolio calculation utiliti...

**52. tracking_normalization.py**
- **File**: `the_alchemiser/portfolio/mappers/tracking_normalization.py`
- **Description**: File explicitly marked with legacy/deprecated status
- **Purpose**: File with explicit legacy/deprecated status marker
- **Suggested Action**: review_for_migration
- **Evidence**: Status markers: """Business Unit: portfolio | Status: current

Tracking Normalization - migrated from legacy locatio...

**53. tracking.py**
- **File**: `the_alchemiser/portfolio/mappers/tracking.py`
- **Description**: File explicitly marked with legacy/deprecated status
- **Purpose**: File with explicit legacy/deprecated status marker
- **Suggested Action**: review_for_migration
- **Evidence**: Status markers: """Business Unit: portfolio | Status: current

Tracking - migrated from legacy location.
"""

from _...

**54. fractionability_policy_impl.py**
- **File**: `the_alchemiser/portfolio/policies/fractionability_policy_impl.py`
- **Description**: File explicitly marked with legacy/deprecated status
- **Purpose**: File with explicit legacy/deprecated status marker
- **Suggested Action**: review_for_migration
- **Active Imports**: 2 files importing this shim
- **Evidence**: Status markers: """Business Unit: portfolio | Status: current

Fractionability policy implementation.

Concrete impl...; Actively imported by 2 files

**55. tracking.py**
- **File**: `the_alchemiser/portfolio/schemas/tracking.py`
- **Description**: File explicitly marked with legacy/deprecated status
- **Purpose**: File with explicit legacy/deprecated status marker
- **Suggested Action**: review_for_migration
- **Active Imports**: 4 files importing this shim
- **Evidence**: Status markers: """Business Unit: utilities; Status: current.

Strategy Tracking DTOs for The Alchemiser Trading Sys...; Actively imported by 4 files

**56. symbol_classifier.py**
- **File**: `the_alchemiser/portfolio/state/symbol_classifier.py`
- **Description**: File explicitly marked with legacy/deprecated status
- **Purpose**: File with explicit legacy/deprecated status marker
- **Suggested Action**: review_for_migration
- **Evidence**: Status markers: """Business Unit: strategy & signal generation; Status: current.

Symbol classification for strategy...

**57. asset_order_handler.py**
- **File**: `the_alchemiser/execution/orders/asset_order_handler.py`
- **Description**: Contains actual deprecation warnings
- **Purpose**: File issues deprecation warnings
- **Suggested Action**: review_for_removal
- **Active Imports**: 1 files importing this shim
- **Evidence**: warnings\.warn\s*\(; DeprecationWarning; DEPRECATED:; Warning: AssetOrderHandler.handle_fractionability_error is deprecated. ...; Actively imported by 1 files

**58. alpaca_client.py**
- **File**: `the_alchemiser/execution/brokers/alpaca_client.py`
- **Description**: Contains actual deprecation warnings
- **Purpose**: File issues deprecation warnings
- **Suggested Action**: review_for_removal
- **Active Imports**: 2 files importing this shim
- **Evidence**: DEPRECATED:; Actively imported by 2 files

**59. error_handling.py**
- **File**: `the_alchemiser/shared/utils/error_handling.py`
- **Description**: Contains actual deprecation warnings
- **Purpose**: File issues deprecation warnings
- **Suggested Action**: review_for_removal
- **Evidence**: warnings\.warn\s*\(; DeprecationWarning; \[DEPRECATED\]; Warning: the_alchemiser.shared.utils.error_handling is deprecated. ...

**60. execution_service.py**
- **File**: `the_alchemiser/portfolio/execution/execution_service.py`
- **Description**: Contains actual deprecation warnings
- **Purpose**: File issues deprecation warnings
- **Suggested Action**: review_for_removal
- **Evidence**: warnings\.warn\s*\(; DeprecationWarning; DEPRECATED:; Warning: Importing from ...

**61. portfolio_pnl_utils.py**
- **File**: `the_alchemiser/portfolio/utils/portfolio_pnl_utils.py`
- **Description**: Contains actual deprecation warnings
- **Purpose**: File issues deprecation warnings
- **Suggested Action**: review_for_removal
- **Active Imports**: 1 files importing this shim
- **Evidence**: warnings\.warn\s*\(; DeprecationWarning; DEPRECATED:; Warning: Importing from ...; Actively imported by 1 files

**62. position_manager.py**
- **File**: `the_alchemiser/portfolio/holdings/position_manager.py`
- **Description**: Contains actual deprecation warnings
- **Purpose**: File issues deprecation warnings
- **Suggested Action**: review_for_removal
- **Active Imports**: 1 files importing this shim
- **Evidence**: warnings\.warn\s*\(; DeprecationWarning; DEPRECATED:; Warning: PositionManager.validate_sell_position is deprecated. ...; Actively imported by 1 files

**63. rebalance_plan.py**
- **File**: `the_alchemiser/portfolio/rebalancing/rebalance_plan.py`
- **Description**: Contains actual deprecation warnings
- **Purpose**: File issues deprecation warnings
- **Suggested Action**: review_for_removal
- **Active Imports**: 2 files importing this shim
- **Evidence**: warnings\.warn\s*\(; DeprecationWarning; DEPRECATED:; Warning: Importing from ...; Actively imported by 2 files

**64. orchestrator.py**
- **File**: `the_alchemiser/portfolio/rebalancing/orchestrator.py`
- **Description**: Contains actual deprecation warnings
- **Purpose**: File issues deprecation warnings
- **Suggested Action**: review_for_removal
- **Evidence**: warnings\.warn\s*\(; DeprecationWarning; DEPRECATED:; Warning: Importing from ...

**65. rebalancing_service.py**
- **File**: `the_alchemiser/portfolio/rebalancing/rebalancing_service.py`
- **Description**: Contains actual deprecation warnings
- **Purpose**: File issues deprecation warnings
- **Suggested Action**: review_for_removal
- **Evidence**: warnings\.warn\s*\(; DeprecationWarning; DEPRECATED:; Warning: Importing from ...

**66. orchestrator_facade.py**
- **File**: `the_alchemiser/portfolio/rebalancing/orchestrator_facade.py`
- **Description**: Contains actual deprecation warnings
- **Purpose**: File issues deprecation warnings
- **Suggested Action**: review_for_removal
- **Active Imports**: 1 files importing this shim
- **Evidence**: warnings\.warn\s*\(; DeprecationWarning; DEPRECATED:; Warning: Importing from ...; Actively imported by 1 files

**67. analysis_service.py**
- **File**: `the_alchemiser/portfolio/analytics/analysis_service.py`
- **Description**: Contains actual deprecation warnings
- **Purpose**: File issues deprecation warnings
- **Suggested Action**: review_for_removal
- **Evidence**: warnings\.warn\s*\(; DeprecationWarning; DEPRECATED:; Warning: Importing from ...

**68. position_analyzer.py**
- **File**: `the_alchemiser/portfolio/analytics/position_analyzer.py`
- **Description**: Contains actual deprecation warnings
- **Purpose**: File issues deprecation warnings
- **Suggested Action**: review_for_removal
- **Evidence**: warnings\.warn\s*\(; DeprecationWarning; DEPRECATED:; Warning: Importing from ...

**69. position_delta.py**
- **File**: `the_alchemiser/portfolio/analytics/position_delta.py`
- **Description**: Contains actual deprecation warnings
- **Purpose**: File issues deprecation warnings
- **Suggested Action**: review_for_removal
- **Evidence**: warnings\.warn\s*\(; DeprecationWarning; DEPRECATED:; Warning: Importing from ...

**70. attribution_engine.py**
- **File**: `the_alchemiser/portfolio/analytics/attribution_engine.py`
- **Description**: Contains actual deprecation warnings
- **Purpose**: File issues deprecation warnings
- **Suggested Action**: review_for_removal
- **Evidence**: warnings\.warn\s*\(; DeprecationWarning; DEPRECATED:; Warning: Importing from ...

**71. position_service.py**
- **File**: `the_alchemiser/portfolio/positions/position_service.py`
- **Description**: Contains actual deprecation warnings
- **Purpose**: File issues deprecation warnings
- **Suggested Action**: review_for_removal
- **Active Imports**: 2 files importing this shim
- **Evidence**: warnings\.warn\s*\(; DeprecationWarning; DEPRECATED:; Warning: Importing from ...; Actively imported by 2 files

**72. legacy_position_manager.py**
- **File**: `the_alchemiser/portfolio/positions/legacy_position_manager.py`
- **Description**: Contains actual deprecation warnings
- **Purpose**: File issues deprecation warnings
- **Suggested Action**: review_for_removal
- **Active Imports**: 1 files importing this shim
- **Evidence**: warnings\.warn\s*\(; DeprecationWarning; DEPRECATED:; Warning: Importing from ...; Actively imported by 1 files

**73. main.py**
- **File**: `the_alchemiser/main.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 4 files importing this shim
- **Evidence**: Redirection: )  # Keep global for backward compatibility during transition; Actively imported by 4 files

**74. order_schemas.py**
- **File**: `the_alchemiser/execution/orders/order_schemas.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 16 files importing this shim
- **Evidence**: Redirection: # Backward compatibility aliases - will be removed in future version; Actively imported by 16 files

**75. validation.py**
- **File**: `the_alchemiser/execution/orders/validation.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 2 files importing this shim
- **Evidence**: Redirection: Duplicate file orders/order_validation.py was removed to eliminate redundancy.; Actively imported by 2 files

**76. asset_order_handler.py**
- **File**: `the_alchemiser/execution/orders/asset_order_handler.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 1 files importing this shim
- **Evidence**: Redirection: DEPRECATED: This fractionability error handling has been moved to FractionabilityPolicy.; Redirection: This method remains for backward compatibility only.; Redirection: DEPRECATED: This fractionability error handling has been moved to FractionabilityPolicy.; Actively imported by 1 files

**77. execution_schemas.py**
- **File**: `the_alchemiser/execution/core/execution_schemas.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 12 files importing this shim
- **Evidence**: Redirection: # NOTE: LimitOrderResultDTO moved to interfaces/schemas/orders.py to avoid duplicate; Redirection: # Backward compatibility aliases; Redirection: # Backward compatibility aliases - will be removed in future version; Actively imported by 12 files

**78. account_facade.py**
- **File**: `the_alchemiser/execution/core/account_facade.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 1 files importing this shim
- **Evidence**: Redirection: pass  # Fallback for backward compatibility; Actively imported by 1 files

**79. canonical_executor.py**
- **File**: `the_alchemiser/execution/core/canonical_executor.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 6 files importing this shim
- **Evidence**: Star import: from the_alchemiser.execution.core.executor import *  # noqa: F403; Redirection: CRITICAL: This module has moved to the_alchemiser.execution.core; Redirection: This shim maintains backward compatibility for execution systems.; Redirection: # Log the redirection for audit purposes; Actively imported by 6 files

**80. orders.py**
- **File**: `the_alchemiser/execution/mappers/orders.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 6 files importing this shim
- **Evidence**: Redirection: """Convert ValidatedOrderDTO back to dictionary for backward compatibility.; Actively imported by 6 files

**81. alpaca_client.py**
- **File**: `the_alchemiser/execution/brokers/alpaca_client.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 2 files importing this shim
- **Evidence**: Redirection: trading_client: Alpaca trading client for API calls (backward compatibility).; Redirection: self.trading_client = alpaca_manager.trading_client  # Backward compatibility; Actively imported by 2 files

**82. smart_execution.py**
- **File**: `the_alchemiser/execution/strategies/smart_execution.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 6 files importing this shim
- **Evidence**: Redirection: def trading_client(self) -> Any: ...  # Backward compatibility; Actively imported by 6 files

**83. tecl_strategy_engine.py**
- **File**: `the_alchemiser/strategy/engines/tecl_strategy_engine.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 2 files importing this shim
- **Evidence**: Redirection: self.data_provider = data_provider  # Keep for backward compatibility with existing methods; Actively imported by 2 files

**84. nuclear_typed_engine.py**
- **File**: `the_alchemiser/strategy/engines/nuclear_typed_engine.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 2 files importing this shim
- **Evidence**: Redirection: Supports two calling conventions for backward compatibility:; Actively imported by 2 files

**85. typed_klm_ensemble_engine.py**
- **File**: `the_alchemiser/strategy/engines/typed_klm_ensemble_engine.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 3 files importing this shim
- **Evidence**: Redirection: Supports two calling conventions for backward compatibility:; Actively imported by 3 files

**86. strategy_market_data_service.py**
- **File**: `the_alchemiser/strategy/data/strategy_market_data_service.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 1 files importing this shim
- **Evidence**: Redirection: # --- Legacy Adapter Methods (for backward compatibility) ---; Actively imported by 1 files

**87. market_data_mapping.py**
- **File**: `the_alchemiser/strategy/mappers/market_data_mapping.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 4 files importing this shim
- **Evidence**: Redirection: """Convert QuoteModel to tuple format for backward compatibility.; Actively imported by 4 files

**88. strategies.py**
- **File**: `the_alchemiser/strategy/schemas/strategies.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 2 files importing this shim
- **Evidence**: Redirection: Backward Compatibility:; Actively imported by 2 files

**89. trading_engine.py**
- **File**: `the_alchemiser/strategy/engines/core/trading_engine.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 3 files importing this shim
- **Evidence**: Redirection: This is an alias for get_positions() to maintain backward compatibility.; Actively imported by 3 files

**90. strategy_position_model.py**
- **File**: `the_alchemiser/strategy/engines/models/strategy_position_model.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 1 files importing this shim
- **Evidence**: Redirection: # Convenience methods for backward compatibility; Redirection: """Get unrealized P&L as float for backward compatibility."""; Redirection: """Get unrealized P&L percentage as float for backward compatibility."""; Actively imported by 1 files

**91. service_factory.py**
- **File**: `the_alchemiser/shared/utils/service_factory.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 1 files importing this shim
- **Evidence**: Redirection: # Backward compatibility: direct instantiation; Actively imported by 1 files

**92. tick_size_service.py**
- **File**: `the_alchemiser/shared/services/tick_size_service.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 2 files importing this shim
- **Evidence**: Redirection: # NOTE: Global singleton access was removed to align with DDD and DI rules.; Actively imported by 2 files

**93. error_handler.py**
- **File**: `the_alchemiser/shared/errors/error_handler.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 11 files importing this shim
- **Evidence**: Redirection: # For any other object that might have a to_dict method (backward compatibility); Redirection: # Global enhanced error reporter instance (for backward compatibility); Actively imported by 11 files

**94. service_providers.py**
- **File**: `the_alchemiser/shared/config/service_providers.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 1 files importing this shim
- **Evidence**: Redirection: # Backward compatibility: provide TradingServiceManager; Actively imported by 1 files

**95. infrastructure_providers.py**
- **File**: `the_alchemiser/shared/config/infrastructure_providers.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 1 files importing this shim
- **Evidence**: Redirection: # Backward compatibility: provide same interface; Actively imported by 1 files

**96. bootstrap.py**
- **File**: `the_alchemiser/shared/config/bootstrap.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 3 files importing this shim
- **Evidence**: Redirection: and AlpacaManager for backward compatibility.; Actively imported by 3 files

**97. repository.py**
- **File**: `the_alchemiser/shared/protocols/repository.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 5 files importing this shim
- **Evidence**: Redirection: """Access to underlying trading client for backward compatibility.; Redirection: Note: This property is for backward compatibility during migration.; Actively imported by 5 files

**98. core_types.py**
- **File**: `the_alchemiser/shared/value_objects/core_types.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 40 files importing this shim
- **Evidence**: Redirection: core business entities and concepts. Interface/UI types have been moved to; Redirection: # Legacy field aliases for backward compatibility; Redirection: # Trading Execution Types (moved to interfaces/schemas/execution.py); Actively imported by 40 files

**99. email_utils.py**
- **File**: `the_alchemiser/shared/notifications/email_utils.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 1 files importing this shim
- **Evidence**: Redirection: This module now imports from the new modular email system for backward compatibility.; Redirection: This file maintains backward compatibility for existing imports.; Redirection: # Backward compatibility aliases for internal functions that might still be referenced; Actively imported by 1 files

**100. client.py**
- **File**: `the_alchemiser/shared/notifications/client.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 1 files importing this shim
- **Evidence**: Redirection: # Global instance for backward compatibility; Redirection: """Send an email notification (backward compatibility function)."""; Actively imported by 1 files

**101. base.py**
- **File**: `the_alchemiser/shared/schemas/base.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 8 files importing this shim
- **Evidence**: Redirection: # Backward compatibility alias - will be removed in future version; Actively imported by 8 files

**102. accounts.py**
- **File**: `the_alchemiser/shared/schemas/accounts.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 4 files importing this shim
- **Evidence**: Redirection: # Backward compatibility aliases - will be removed in future version; Actively imported by 4 files

**103. enriched_data.py**
- **File**: `the_alchemiser/shared/schemas/enriched_data.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 2 files importing this shim
- **Evidence**: Redirection: # Backward compatibility aliases - will be removed in future version; Actively imported by 2 files

**104. operations.py**
- **File**: `the_alchemiser/shared/schemas/operations.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 2 files importing this shim
- **Evidence**: Redirection: # Backward compatibility aliases - will be removed in future version; Actively imported by 2 files

**105. market_data.py**
- **File**: `the_alchemiser/shared/schemas/market_data.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 2 files importing this shim
- **Evidence**: Redirection: # Backward compatibility aliases - will be removed in future version; Actively imported by 2 files

**106. portfolio_pnl_utils.py**
- **File**: `the_alchemiser/portfolio/utils/portfolio_pnl_utils.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 1 files importing this shim
- **Evidence**: Star import: from the_alchemiser.portfolio.pnl.portfolio_pnl_utils import *; Redirection: """DEPRECATED: This module has moved to the_alchemiser.portfolio.pnl; Redirection: This shim maintains backward compatibility.; Actively imported by 1 files

**107. strategy_order_tracker.py**
- **File**: `the_alchemiser/portfolio/pnl/strategy_order_tracker.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 6 files importing this shim
- **Evidence**: Redirection: # Process orders with backward compatibility; Actively imported by 6 files

**108. position_manager.py**
- **File**: `the_alchemiser/portfolio/holdings/position_manager.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 1 files importing this shim
- **Evidence**: Redirection: DEPRECATED: This position validation logic has been moved to PositionPolicy.; Redirection: This method remains for backward compatibility only.; Redirection: DEPRECATED: This buying power validation logic has been moved to BuyingPowerPolicy.; Actively imported by 1 files

**109. rebalance_plan.py**
- **File**: `the_alchemiser/portfolio/rebalancing/rebalance_plan.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 2 files importing this shim
- **Evidence**: Star import: from the_alchemiser.portfolio.allocation.rebalance_plan import *; Redirection: """DEPRECATED: This module has moved to the_alchemiser.portfolio.allocation; Redirection: This shim maintains backward compatibility.; Actively imported by 2 files

**110. orchestrator_facade.py**
- **File**: `the_alchemiser/portfolio/rebalancing/orchestrator_facade.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 1 files importing this shim
- **Evidence**: Star import: from the_alchemiser.portfolio.core.rebalancing_orchestrator_facade import *; Redirection: """DEPRECATED: This module has moved to the_alchemiser.portfolio.core; Redirection: This shim maintains backward compatibility.; Actively imported by 1 files

**111. rebalancing_orchestrator_facade.py**
- **File**: `the_alchemiser/portfolio/core/rebalancing_orchestrator_facade.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 1 files importing this shim
- **Evidence**: Redirection: async rebalancing cycle in a new event loop to maintain backward compatibility.; Redirection: # Run the async orchestrator method using asyncio.run for backward compatibility; Actively imported by 1 files

**112. portfolio_rebalancing_mapping.py**
- **File**: `the_alchemiser/portfolio/mappers/portfolio_rebalancing_mapping.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 2 files importing this shim
- **Evidence**: Redirection: Provides backward compatibility for incomplete dict structures.; Redirection: Provides backward compatibility for incomplete dict structures.; Actively imported by 2 files

**113. position_service.py**
- **File**: `the_alchemiser/portfolio/positions/position_service.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 2 files importing this shim
- **Evidence**: Star import: from the_alchemiser.portfolio.holdings.position_service import *; Redirection: """DEPRECATED: This module has moved to the_alchemiser.portfolio.holdings; Redirection: This shim maintains backward compatibility.; Actively imported by 2 files

**114. legacy_position_manager.py**
- **File**: `the_alchemiser/portfolio/positions/legacy_position_manager.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 1 files importing this shim
- **Evidence**: Star import: from the_alchemiser.portfolio.holdings.position_manager import *; Redirection: """DEPRECATED: This module has moved to the_alchemiser.portfolio.holdings; Redirection: This shim maintains backward compatibility.; Actively imported by 1 files

**115. positions.py**
- **File**: `the_alchemiser/portfolio/schemas/positions.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 2 files importing this shim
- **Evidence**: Redirection: # Backward compatibility aliases - will be removed in future version; Actively imported by 2 files

**116. rollback_legacy_deletions.py**
- **File**: `scripts/rollback_legacy_deletions.py`
- **Description**: File explicitly named with *legacy*
- **Purpose**: File explicitly named with legacy/deprecated pattern
- **Suggested Action**: review_for_migration
- **Evidence**: Filename pattern: *legacy*

**117. delete_legacy_safe.py**
- **File**: `scripts/delete_legacy_safe.py`
- **Description**: File explicitly named with *legacy*
- **Purpose**: File explicitly named with legacy/deprecated pattern
- **Suggested Action**: review_for_migration
- **Evidence**: Filename pattern: *legacy*

**118. execution_manager_legacy.py**
- **File**: `the_alchemiser/execution/core/execution_manager_legacy.py`
- **Description**: File explicitly named with *legacy*
- **Purpose**: File explicitly named with legacy/deprecated pattern
- **Suggested Action**: review_for_migration
- **Evidence**: Filename pattern: *legacy*

**119. symbol_legacy.py**
- **File**: `the_alchemiser/shared/types/symbol_legacy.py`
- **Description**: File explicitly named with *legacy*
- **Purpose**: File explicitly named with legacy/deprecated pattern
- **Suggested Action**: review_for_migration
- **Active Imports**: 7 files importing this shim
- **Evidence**: Filename pattern: *legacy*; Actively imported by 7 files

**120. legacy_position_manager.py**
- **File**: `the_alchemiser/portfolio/positions/legacy_position_manager.py`
- **Description**: File explicitly named with *legacy*
- **Purpose**: File explicitly named with legacy/deprecated pattern
- **Suggested Action**: review_for_migration
- **Active Imports**: 1 files importing this shim
- **Evidence**: Filename pattern: *legacy*; Actively imported by 1 files

**121. main.py**
- **File**: `the_alchemiser/main.py`
- **Description**: File explicitly describes itself as a compatibility shim
- **Purpose**: Explicit compatibility/backward-compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 4 files importing this shim
- **Evidence**: Shim indicators: backward compatibility; Actively imported by 4 files

**122. lambda_handler.py**
- **File**: `the_alchemiser/lambda_handler.py`
- **Description**: File explicitly describes itself as a compatibility shim
- **Purpose**: Explicit compatibility/backward-compatibility shim
- **Suggested Action**: migrate_imports
- **Evidence**: Shim indicators: backward compatibility

**123. order_schemas.py**
- **File**: `the_alchemiser/execution/orders/order_schemas.py`
- **Description**: File explicitly describes itself as a compatibility shim
- **Purpose**: Explicit compatibility/backward-compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 16 files importing this shim
- **Evidence**: Shim indicators: backward compatibility; Actively imported by 16 files

**124. asset_order_handler.py**
- **File**: `the_alchemiser/execution/orders/asset_order_handler.py`
- **Description**: File explicitly describes itself as a compatibility shim
- **Purpose**: Explicit compatibility/backward-compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 1 files importing this shim
- **Evidence**: Shim indicators: backward compatibility; Actively imported by 1 files

**125. execution_manager_legacy.py**
- **File**: `the_alchemiser/execution/core/execution_manager_legacy.py`
- **Description**: File explicitly describes itself as a compatibility shim
- **Purpose**: Explicit compatibility/backward-compatibility shim
- **Suggested Action**: migrate_imports
- **Evidence**: Shim indicators: this shim, shim maintains, backward compatibility

**126. execution_schemas.py**
- **File**: `the_alchemiser/execution/core/execution_schemas.py`
- **Description**: File explicitly describes itself as a compatibility shim
- **Purpose**: Explicit compatibility/backward-compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 12 files importing this shim
- **Evidence**: Shim indicators: backward compatibility; Actively imported by 12 files

**127. account_facade.py**
- **File**: `the_alchemiser/execution/core/account_facade.py`
- **Description**: File explicitly describes itself as a compatibility shim
- **Purpose**: Explicit compatibility/backward-compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 1 files importing this shim
- **Evidence**: Shim indicators: backward compatibility; Actively imported by 1 files

**128. canonical_executor.py**
- **File**: `the_alchemiser/execution/core/canonical_executor.py`
- **Description**: File explicitly describes itself as a compatibility shim
- **Purpose**: Explicit compatibility/backward-compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 6 files importing this shim
- **Evidence**: Shim indicators: this shim, shim maintains, backward compatibility; Actively imported by 6 files

**129. orders.py**
- **File**: `the_alchemiser/execution/mappers/orders.py`
- **Description**: File explicitly describes itself as a compatibility shim
- **Purpose**: Explicit compatibility/backward-compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 6 files importing this shim
- **Evidence**: Shim indicators: backward compatibility; Actively imported by 6 files

**130. alpaca_client.py**
- **File**: `the_alchemiser/execution/brokers/alpaca_client.py`
- **Description**: File explicitly describes itself as a compatibility shim
- **Purpose**: Explicit compatibility/backward-compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 2 files importing this shim
- **Evidence**: Shim indicators: backward compatibility; Actively imported by 2 files

**131. smart_execution.py**
- **File**: `the_alchemiser/execution/strategies/smart_execution.py`
- **Description**: File explicitly describes itself as a compatibility shim
- **Purpose**: Explicit compatibility/backward-compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 6 files importing this shim
- **Evidence**: Shim indicators: backward compatibility; Actively imported by 6 files

**132. observers.py**
- **File**: `the_alchemiser/execution/lifecycle/observers.py`
- **Description**: File explicitly describes itself as a compatibility shim
- **Purpose**: Explicit compatibility/backward-compatibility shim
- **Suggested Action**: migrate_imports
- **Evidence**: Shim indicators: backward compatibility

**133. adapter.py**
- **File**: `the_alchemiser/execution/brokers/alpaca/adapter.py`
- **Description**: File explicitly describes itself as a compatibility shim
- **Purpose**: Explicit compatibility/backward-compatibility shim
- **Suggested Action**: migrate_imports
- **Evidence**: Shim indicators: backward compatibility, maintains backward

**134. tecl_strategy_engine.py**
- **File**: `the_alchemiser/strategy/engines/tecl_strategy_engine.py`
- **Description**: File explicitly describes itself as a compatibility shim
- **Purpose**: Explicit compatibility/backward-compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 2 files importing this shim
- **Evidence**: Shim indicators: backward compatibility; Actively imported by 2 files

**135. nuclear_typed_engine.py**
- **File**: `the_alchemiser/strategy/engines/nuclear_typed_engine.py`
- **Description**: File explicitly describes itself as a compatibility shim
- **Purpose**: Explicit compatibility/backward-compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 2 files importing this shim
- **Evidence**: Shim indicators: backward compatibility; Actively imported by 2 files

**136. typed_klm_ensemble_engine.py**
- **File**: `the_alchemiser/strategy/engines/typed_klm_ensemble_engine.py`
- **Description**: File explicitly describes itself as a compatibility shim
- **Purpose**: Explicit compatibility/backward-compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 3 files importing this shim
- **Evidence**: Shim indicators: backward compatibility; Actively imported by 3 files

**137. domain_mapping.py**
- **File**: `the_alchemiser/strategy/data/domain_mapping.py`
- **Description**: File explicitly describes itself as a compatibility shim
- **Purpose**: Explicit compatibility/backward-compatibility shim
- **Suggested Action**: migrate_imports
- **Evidence**: Shim indicators: backward compatibility

**138. strategy_market_data_service.py**
- **File**: `the_alchemiser/strategy/data/strategy_market_data_service.py`
- **Description**: File explicitly describes itself as a compatibility shim
- **Purpose**: Explicit compatibility/backward-compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 1 files importing this shim
- **Evidence**: Shim indicators: backward compatibility; Actively imported by 1 files

**139. market_data_mapping.py**
- **File**: `the_alchemiser/strategy/mappers/market_data_mapping.py`
- **Description**: File explicitly describes itself as a compatibility shim
- **Purpose**: Explicit compatibility/backward-compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 4 files importing this shim
- **Evidence**: Shim indicators: backward compatibility; Actively imported by 4 files

**140. strategies.py**
- **File**: `the_alchemiser/strategy/schemas/strategies.py`
- **Description**: File explicitly describes itself as a compatibility shim
- **Purpose**: Explicit compatibility/backward-compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 2 files importing this shim
- **Evidence**: Shim indicators: backward compatibility; Actively imported by 2 files

**141. trading_engine.py**
- **File**: `the_alchemiser/strategy/engines/core/trading_engine.py`
- **Description**: File explicitly describes itself as a compatibility shim
- **Purpose**: Explicit compatibility/backward-compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 3 files importing this shim
- **Evidence**: Shim indicators: backward compatibility; Actively imported by 3 files

**142. strategy_position_model.py**
- **File**: `the_alchemiser/strategy/engines/models/strategy_position_model.py`
- **Description**: File explicitly describes itself as a compatibility shim
- **Purpose**: Explicit compatibility/backward-compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 1 files importing this shim
- **Evidence**: Shim indicators: backward compatibility; Actively imported by 1 files

**143. service_factory.py**
- **File**: `the_alchemiser/shared/utils/service_factory.py`
- **Description**: File explicitly describes itself as a compatibility shim
- **Purpose**: Explicit compatibility/backward-compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 1 files importing this shim
- **Evidence**: Shim indicators: backward compatibility; Actively imported by 1 files

**144. error_handling.py**
- **File**: `the_alchemiser/shared/utils/error_handling.py`
- **Description**: File explicitly describes itself as a compatibility shim
- **Purpose**: Explicit compatibility/backward-compatibility shim
- **Suggested Action**: migrate_imports
- **Evidence**: Shim indicators: backward compatibility

**145. real_time_pricing.py**
- **File**: `the_alchemiser/shared/services/real_time_pricing.py`
- **Description**: File explicitly describes itself as a compatibility shim
- **Purpose**: Explicit compatibility/backward-compatibility shim
- **Suggested Action**: migrate_imports
- **Evidence**: Shim indicators: backward compatibility

**146. error_handler.py**
- **File**: `the_alchemiser/shared/errors/error_handler.py`
- **Description**: File explicitly describes itself as a compatibility shim
- **Purpose**: Explicit compatibility/backward-compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 11 files importing this shim
- **Evidence**: Shim indicators: backward compatibility; Actively imported by 11 files

**147. service_providers.py**
- **File**: `the_alchemiser/shared/config/service_providers.py`
- **Description**: File explicitly describes itself as a compatibility shim
- **Purpose**: Explicit compatibility/backward-compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 1 files importing this shim
- **Evidence**: Shim indicators: backward compatibility; Actively imported by 1 files

**148. infrastructure_providers.py**
- **File**: `the_alchemiser/shared/config/infrastructure_providers.py`
- **Description**: File explicitly describes itself as a compatibility shim
- **Purpose**: Explicit compatibility/backward-compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 1 files importing this shim
- **Evidence**: Shim indicators: backward compatibility; Actively imported by 1 files

**149. bootstrap.py**
- **File**: `the_alchemiser/shared/config/bootstrap.py`
- **Description**: File explicitly describes itself as a compatibility shim
- **Purpose**: Explicit compatibility/backward-compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 3 files importing this shim
- **Evidence**: Shim indicators: backward compatibility; Actively imported by 3 files

**150. repository.py**
- **File**: `the_alchemiser/shared/protocols/repository.py`
- **Description**: File explicitly describes itself as a compatibility shim
- **Purpose**: Explicit compatibility/backward-compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 5 files importing this shim
- **Evidence**: Shim indicators: backward compatibility; Actively imported by 5 files

**151. core_types.py**
- **File**: `the_alchemiser/shared/value_objects/core_types.py`
- **Description**: File explicitly describes itself as a compatibility shim
- **Purpose**: Explicit compatibility/backward-compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 40 files importing this shim
- **Evidence**: Shim indicators: backward compatibility; Actively imported by 40 files

**152. execution_summary_mapping.py**
- **File**: `the_alchemiser/shared/mappers/execution_summary_mapping.py`
- **Description**: File explicitly describes itself as a compatibility shim
- **Purpose**: Explicit compatibility/backward-compatibility shim
- **Suggested Action**: migrate_imports
- **Evidence**: Shim indicators: backward compatibility

**153. email_utils.py**
- **File**: `the_alchemiser/shared/notifications/email_utils.py`
- **Description**: File explicitly describes itself as a compatibility shim
- **Purpose**: Explicit compatibility/backward-compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 1 files importing this shim
- **Evidence**: Shim indicators: backward compatibility, maintains backward; Actively imported by 1 files

**154. config.py**
- **File**: `the_alchemiser/shared/notifications/config.py`
- **Description**: File explicitly describes itself as a compatibility shim
- **Purpose**: Explicit compatibility/backward-compatibility shim
- **Suggested Action**: migrate_imports
- **Evidence**: Shim indicators: backward compatibility

**155. client.py**
- **File**: `the_alchemiser/shared/notifications/client.py`
- **Description**: File explicitly describes itself as a compatibility shim
- **Purpose**: Explicit compatibility/backward-compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 1 files importing this shim
- **Evidence**: Shim indicators: backward compatibility; Actively imported by 1 files

**156. base.py**
- **File**: `the_alchemiser/shared/schemas/base.py`
- **Description**: File explicitly describes itself as a compatibility shim
- **Purpose**: Explicit compatibility/backward-compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 8 files importing this shim
- **Evidence**: Shim indicators: backward compatibility; Actively imported by 8 files

**157. execution_summary.py**
- **File**: `the_alchemiser/shared/schemas/execution_summary.py`
- **Description**: File explicitly describes itself as a compatibility shim
- **Purpose**: Explicit compatibility/backward-compatibility shim
- **Suggested Action**: migrate_imports
- **Evidence**: Shim indicators: backward compatibility

**158. accounts.py**
- **File**: `the_alchemiser/shared/schemas/accounts.py`
- **Description**: File explicitly describes itself as a compatibility shim
- **Purpose**: Explicit compatibility/backward-compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 4 files importing this shim
- **Evidence**: Shim indicators: backward compatibility; Actively imported by 4 files

**159. enriched_data.py**
- **File**: `the_alchemiser/shared/schemas/enriched_data.py`
- **Description**: File explicitly describes itself as a compatibility shim
- **Purpose**: Explicit compatibility/backward-compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 2 files importing this shim
- **Evidence**: Shim indicators: backward compatibility; Actively imported by 2 files

**160. operations.py**
- **File**: `the_alchemiser/shared/schemas/operations.py`
- **Description**: File explicitly describes itself as a compatibility shim
- **Purpose**: Explicit compatibility/backward-compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 2 files importing this shim
- **Evidence**: Shim indicators: backward compatibility; Actively imported by 2 files

**161. market_data.py**
- **File**: `the_alchemiser/shared/schemas/market_data.py`
- **Description**: File explicitly describes itself as a compatibility shim
- **Purpose**: Explicit compatibility/backward-compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 2 files importing this shim
- **Evidence**: Shim indicators: backward compatibility; Actively imported by 2 files

**162. execution_service.py**
- **File**: `the_alchemiser/portfolio/execution/execution_service.py`
- **Description**: File explicitly describes itself as a compatibility shim
- **Purpose**: Explicit compatibility/backward-compatibility shim
- **Suggested Action**: migrate_imports
- **Evidence**: Shim indicators: this shim, shim maintains, backward compatibility

**163. portfolio_pnl_utils.py**
- **File**: `the_alchemiser/portfolio/utils/portfolio_pnl_utils.py`
- **Description**: File explicitly describes itself as a compatibility shim
- **Purpose**: Explicit compatibility/backward-compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 1 files importing this shim
- **Evidence**: Shim indicators: this shim, shim maintains, backward compatibility; Actively imported by 1 files

**164. strategy_order_tracker.py**
- **File**: `the_alchemiser/portfolio/pnl/strategy_order_tracker.py`
- **Description**: File explicitly describes itself as a compatibility shim
- **Purpose**: Explicit compatibility/backward-compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 6 files importing this shim
- **Evidence**: Shim indicators: backward compatibility; Actively imported by 6 files

**165. position_manager.py**
- **File**: `the_alchemiser/portfolio/holdings/position_manager.py`
- **Description**: File explicitly describes itself as a compatibility shim
- **Purpose**: Explicit compatibility/backward-compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 1 files importing this shim
- **Evidence**: Shim indicators: backward compatibility; Actively imported by 1 files

**166. rebalance_plan.py**
- **File**: `the_alchemiser/portfolio/rebalancing/rebalance_plan.py`
- **Description**: File explicitly describes itself as a compatibility shim
- **Purpose**: Explicit compatibility/backward-compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 2 files importing this shim
- **Evidence**: Shim indicators: this shim, shim maintains, backward compatibility; Actively imported by 2 files

**167. orchestrator.py**
- **File**: `the_alchemiser/portfolio/rebalancing/orchestrator.py`
- **Description**: File explicitly describes itself as a compatibility shim
- **Purpose**: Explicit compatibility/backward-compatibility shim
- **Suggested Action**: migrate_imports
- **Evidence**: Shim indicators: this shim, shim maintains, backward compatibility

**168. rebalancing_service.py**
- **File**: `the_alchemiser/portfolio/rebalancing/rebalancing_service.py`
- **Description**: File explicitly describes itself as a compatibility shim
- **Purpose**: Explicit compatibility/backward-compatibility shim
- **Suggested Action**: migrate_imports
- **Evidence**: Shim indicators: this shim, shim maintains, backward compatibility

**169. orchestrator_facade.py**
- **File**: `the_alchemiser/portfolio/rebalancing/orchestrator_facade.py`
- **Description**: File explicitly describes itself as a compatibility shim
- **Purpose**: Explicit compatibility/backward-compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 1 files importing this shim
- **Evidence**: Shim indicators: this shim, shim maintains, backward compatibility; Actively imported by 1 files

**170. rebalancing_orchestrator_facade.py**
- **File**: `the_alchemiser/portfolio/core/rebalancing_orchestrator_facade.py`
- **Description**: File explicitly describes itself as a compatibility shim
- **Purpose**: Explicit compatibility/backward-compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 1 files importing this shim
- **Evidence**: Shim indicators: backward compatibility; Actively imported by 1 files

**171. portfolio_rebalancing_mapping.py**
- **File**: `the_alchemiser/portfolio/mappers/portfolio_rebalancing_mapping.py`
- **Description**: File explicitly describes itself as a compatibility shim
- **Purpose**: Explicit compatibility/backward-compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 2 files importing this shim
- **Evidence**: Shim indicators: backward compatibility; Actively imported by 2 files

**172. analysis_service.py**
- **File**: `the_alchemiser/portfolio/analytics/analysis_service.py`
- **Description**: File explicitly describes itself as a compatibility shim
- **Purpose**: Explicit compatibility/backward-compatibility shim
- **Suggested Action**: migrate_imports
- **Evidence**: Shim indicators: this shim, shim maintains, backward compatibility

**173. position_analyzer.py**
- **File**: `the_alchemiser/portfolio/analytics/position_analyzer.py`
- **Description**: File explicitly describes itself as a compatibility shim
- **Purpose**: Explicit compatibility/backward-compatibility shim
- **Suggested Action**: migrate_imports
- **Evidence**: Shim indicators: this shim, shim maintains, backward compatibility

**174. position_delta.py**
- **File**: `the_alchemiser/portfolio/analytics/position_delta.py`
- **Description**: File explicitly describes itself as a compatibility shim
- **Purpose**: Explicit compatibility/backward-compatibility shim
- **Suggested Action**: migrate_imports
- **Evidence**: Shim indicators: this shim, shim maintains, backward compatibility

**175. attribution_engine.py**
- **File**: `the_alchemiser/portfolio/analytics/attribution_engine.py`
- **Description**: File explicitly describes itself as a compatibility shim
- **Purpose**: Explicit compatibility/backward-compatibility shim
- **Suggested Action**: migrate_imports
- **Evidence**: Shim indicators: this shim, shim maintains, backward compatibility

**176. position_service.py**
- **File**: `the_alchemiser/portfolio/positions/position_service.py`
- **Description**: File explicitly describes itself as a compatibility shim
- **Purpose**: Explicit compatibility/backward-compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 2 files importing this shim
- **Evidence**: Shim indicators: this shim, shim maintains, backward compatibility; Actively imported by 2 files

**177. legacy_position_manager.py**
- **File**: `the_alchemiser/portfolio/positions/legacy_position_manager.py`
- **Description**: File explicitly describes itself as a compatibility shim
- **Purpose**: Explicit compatibility/backward-compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 1 files importing this shim
- **Evidence**: Shim indicators: this shim, shim maintains, backward compatibility; Actively imported by 1 files

**178. positions.py**
- **File**: `the_alchemiser/portfolio/schemas/positions.py`
- **Description**: File explicitly describes itself as a compatibility shim
- **Purpose**: Explicit compatibility/backward-compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 2 files importing this shim
- **Evidence**: Shim indicators: backward compatibility; Actively imported by 2 files

### 🟡 MEDIUM RISK SHIMS (38 items)

**1. migrate_phase2_imports.py**
- **File**: `scripts/migrate_phase2_imports.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Evidence**: Redirection: print("🎯 Legacy files moved to proper modular locations")

**2. lambda_handler.py**
- **File**: `the_alchemiser/lambda_handler.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Evidence**: Redirection: Backward Compatibility:

**3. order_validation_utils.py**
- **File**: `the_alchemiser/execution/orders/order_validation_utils.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Evidence**: Redirection: Legacy file order_validation_utils_legacy.py was removed to eliminate redundancy.

**4. __init__.py**
- **File**: `the_alchemiser/execution/orders/__init__.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Evidence**: Star import: from .order_id import *; Star import: from .order_schemas import *; Star import: from .order_status import *

**5. lifecycle_adapter.py**
- **File**: `the_alchemiser/execution/orders/lifecycle_adapter.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Evidence**: Redirection: Duplicate file adapters/order_lifecycle_adapter.py was removed to eliminate redundancy.

**6. __init__.py**
- **File**: `the_alchemiser/execution/entities/__init__.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Evidence**: Star import: from .order import *

**7. __init__.py**
- **File**: `the_alchemiser/execution/core/__init__.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Evidence**: Star import: from .execution_schemas import *

**8. execution_manager_legacy.py**
- **File**: `the_alchemiser/execution/core/execution_manager_legacy.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Evidence**: Star import: from the_alchemiser.execution.core.manager import *  # noqa: F403; Redirection: CRITICAL: This module has moved to the_alchemiser.execution.core; Redirection: This shim maintains backward compatibility for execution systems.; Redirection: # Log the redirection for audit purposes

**9. __init__.py**
- **File**: `the_alchemiser/execution/mappers/__init__.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Evidence**: Star import: from .account_mapping import *; Star import: from .execution import *; Star import: from .order_mapping import *

**10. canonical_integration.py**
- **File**: `the_alchemiser/execution/examples/canonical_integration.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Evidence**: Redirection: Duplicate file core/canonical_integration_example.py was removed to eliminate redundancy.

**11. execution_context_adapter.py**
- **File**: `the_alchemiser/execution/strategies/execution_context_adapter.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Evidence**: Redirection: Duplicate file adapters/execution_context_adapter.py was removed to eliminate redundancy.

**12. observers.py**
- **File**: `the_alchemiser/execution/lifecycle/observers.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Evidence**: Redirection: ) -> None:  # Transitional: bool retained for backward compatibility

**13. adapter.py**
- **File**: `the_alchemiser/execution/brokers/alpaca/adapter.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Evidence**: Redirection: 3. Maintains backward compatibility; Redirection: """Get the trading client for backward compatibility."""; Redirection: """Get the data client for backward compatibility."""

**14. __init__.py**
- **File**: `the_alchemiser/strategy/data/__init__.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Evidence**: Star import: from .price_fetching_utils import *; Star import: from .price_service import *; Star import: from .price_utils import *

**15. domain_mapping.py**
- **File**: `the_alchemiser/strategy/data/domain_mapping.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Evidence**: Redirection: # Legacy signal normalization (for backward compatibility); Redirection: strategy_signal_mapping module for backward compatibility.

**16. __init__.py**
- **File**: `the_alchemiser/strategy/schemas/__init__.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Evidence**: Star import: from .strategies import *

**17. __init__.py**
- **File**: `the_alchemiser/strategy/dsl/__init__.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Evidence**: Star import: from .errors import *; Star import: from .evaluator import *; Star import: from .evaluator_cache import *

**18. __init__.py**
- **File**: `the_alchemiser/shared/utils/__init__.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Evidence**: Star import: from ..types.exceptions import *; Star import: from .error_handling import *  # Legacy deprecated; Star import: from .error_reporter import *

**19. error_handling.py**
- **File**: `the_alchemiser/shared/utils/error_handling.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Evidence**: Redirection: This module has been deprecated and its functionality has been moved to:; Redirection: This module is kept temporarily for backward compatibility but will be removed

**20. real_time_pricing.py**
- **File**: `the_alchemiser/shared/services/real_time_pricing.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Evidence**: Redirection: existing trading systems while maintaining backward compatibility.

**21. __init__.py**
- **File**: `the_alchemiser/shared/types/__init__.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Evidence**: Star import: from .time_in_force import *

**22. __init__.py**
- **File**: `the_alchemiser/shared/config/__init__.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Evidence**: Star import: from .config import *

**23. trading.py**
- **File**: `the_alchemiser/shared/protocols/trading.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Evidence**: Redirection: This protocol is optional and may be moved to interface layer if rendering

**24. __init__.py**
- **File**: `the_alchemiser/shared/value_objects/__init__.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Evidence**: Star import: from .core_types import *; Star import: from .symbol import *

**25. execution_summary_mapping.py**
- **File**: `the_alchemiser/shared/mappers/execution_summary_mapping.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Evidence**: Redirection: Provides backward compatibility for incomplete dict structures.

**26. config.py**
- **File**: `the_alchemiser/shared/notifications/config.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Evidence**: Redirection: # Global instance for backward compatibility; Redirection: """Get email configuration (backward compatibility function)."""

**27. execution_summary.py**
- **File**: `the_alchemiser/shared/schemas/execution_summary.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Evidence**: Redirection: # Backward compatibility aliases - will be removed in future version

**28. __init__.py**
- **File**: `the_alchemiser/shared/schemas/__init__.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Evidence**: Star import: from .accounts import *; Star import: from .base import *; Star import: from .common import *

**29. execution_service.py**
- **File**: `the_alchemiser/portfolio/execution/execution_service.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Evidence**: Star import: from the_alchemiser.portfolio.allocation.rebalance_execution_service import *; Redirection: """DEPRECATED: This module has moved to the_alchemiser.portfolio.allocation; Redirection: This shim maintains backward compatibility.

**30. __init__.py**
- **File**: `the_alchemiser/portfolio/services/__init__.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Evidence**: Star import: from .rebalancing_policy import *

**31. orchestrator.py**
- **File**: `the_alchemiser/portfolio/rebalancing/orchestrator.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Evidence**: Star import: from the_alchemiser.portfolio.core.rebalancing_orchestrator import *; Redirection: """DEPRECATED: This module has moved to the_alchemiser.portfolio.core; Redirection: This shim maintains backward compatibility.

**32. rebalancing_service.py**
- **File**: `the_alchemiser/portfolio/rebalancing/rebalancing_service.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Evidence**: Star import: from the_alchemiser.portfolio.allocation.portfolio_rebalancing_service import *; Redirection: """DEPRECATED: This module has moved to the_alchemiser.portfolio.allocation; Redirection: This shim maintains backward compatibility.

**33. __init__.py**
- **File**: `the_alchemiser/portfolio/mappers/__init__.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Evidence**: Star import: from .portfolio_rebalancing_mapping import *; Star import: from .position_mapping import *

**34. analysis_service.py**
- **File**: `the_alchemiser/portfolio/analytics/analysis_service.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Evidence**: Star import: from the_alchemiser.portfolio.core.portfolio_analysis_service import *; Redirection: """DEPRECATED: This module has moved to the_alchemiser.portfolio.core; Redirection: This shim maintains backward compatibility.

**35. position_analyzer.py**
- **File**: `the_alchemiser/portfolio/analytics/position_analyzer.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Evidence**: Star import: from the_alchemiser.portfolio.holdings.position_analyzer import *; Redirection: """DEPRECATED: This module has moved to the_alchemiser.portfolio.holdings; Redirection: This shim maintains backward compatibility.

**36. position_delta.py**
- **File**: `the_alchemiser/portfolio/analytics/position_delta.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Evidence**: Star import: from the_alchemiser.portfolio.holdings.position_delta import *; Redirection: """DEPRECATED: This module has moved to the_alchemiser.portfolio.holdings; Redirection: This shim maintains backward compatibility.

**37. attribution_engine.py**
- **File**: `the_alchemiser/portfolio/analytics/attribution_engine.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Evidence**: Star import: from the_alchemiser.portfolio.state.attribution_engine import *; Redirection: """DEPRECATED: This module has moved to the_alchemiser.portfolio.state; Redirection: This shim maintains backward compatibility.

**38. __init__.py**
- **File**: `the_alchemiser/portfolio/schemas/__init__.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Evidence**: Star import: from .rebalancing import *; Star import: from .tracking import *

### 🟢 LOW RISK SHIMS (2 items)

**1. execution_context_adapter.py.backup**
- **File**: `the_alchemiser/execution/strategies/execution_context_adapter.py.backup`
- **Description**: Backup file
- **Purpose**: Backup or temporary file that should be cleaned up
- **Suggested Action**: remove
- **Evidence**: Backup file pattern: *.backup

**2. rebalance_execution_service.py.backup**
- **File**: `the_alchemiser/portfolio/allocation/rebalance_execution_service.py.backup`
- **Description**: Backup file
- **Purpose**: Backup or temporary file that should be cleaned up
- **Suggested Action**: remove
- **Evidence**: Backup file pattern: *.backup

## Specific Recommendations

### High Priority Actions

1. **Review 178 high-risk shims** - These require immediate attention
2. **Migrate 129 actively imported shims** - Update import statements first
3. **Remove backup files** - These can likely be safely deleted

### Migration Strategy

1. **Phase 1**: Update import statements for actively used shims
2. **Phase 2**: Remove or replace deprecated shims with warnings
3. **Phase 3**: Clean up backup files and unused legacy code
4. **Phase 4**: Validate no broken imports remain

### Safety Guidelines

- **Never remove a shim with active imports without migration**
- **Test after each shim removal**
- **Keep migration atomic - one shim at a time**
- **Document replacement paths for team awareness**

---

**Generated**: January 2025
**Scope**: Actual shims and compatibility layers only
**Issue**: #492
**Tool**: scripts/refined_shim_auditor.py