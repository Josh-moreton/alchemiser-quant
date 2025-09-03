# Import Dependency Migration Report

**Generated**: 2025-09-03 16:35:55
**Total Modules Analyzed**: 241

## Executive Summary

- **HIGH PRIORITY**: 7 heavily-used legacy modules
- **MEDIUM PRIORITY**: 15 lightly-used legacy modules
- **LOW PRIORITY**: 16 shim modules for cleanup

## Migration Priority Analysis

### 🔴 HIGH PRIORITY: Heavily-Used Legacy Modules

These modules are imported by 3+ files and should be migrated first:

| Module | Importers | Files Importing |
|--------|-----------|-----------------|
| `the_alchemiser.shared.utils.common` | 12 | `the_alchemiser.strategy.engines.klm_ensemble_engine`, `the_alchemiser.strategy.engines.tecl_strategy_engine`, `the_alchemiser.strategy.engines.typed_klm_ensemble_engine` + 9 more |
| `the_alchemiser.shared.utils.context` | 6 | `the_alchemiser.strategy.engines.core.trading_engine`, `the_alchemiser.strategy.engines.core.trading_engine`, `the_alchemiser.shared.utils.error_monitoring` + 3 more |
| `the_alchemiser.shared.services.errors` | 5 | `the_alchemiser.lambda_handler`, `the_alchemiser.lambda_handler`, `the_alchemiser.execution.core.manager` + 2 more |
| `the_alchemiser.shared.utils.account_utils` | 5 | `the_alchemiser.shared.utils.__init__`, `the_alchemiser.shared.cli.portfolio_calculations`, `the_alchemiser.shared.reporting.reporting` + 2 more |
| `the_alchemiser.shared.utils.decorators` | 4 | `the_alchemiser.execution.orders.service`, `the_alchemiser.execution.core.execution_manager`, `the_alchemiser.strategy.data.market_data_service` + 1 more |
| `the_alchemiser.shared.utils.s3_utils` | 4 | `the_alchemiser.shared.services.alert_service`, `the_alchemiser.shared.reporting.reporting`, `the_alchemiser.shared.logging.logging_utils` + 1 more |
| `the_alchemiser.portfolio.utils.portfolio_utilities` | 3 | `the_alchemiser.portfolio.utils.__init__`, `the_alchemiser.portfolio.allocation.portfolio_rebalancing_service`, `the_alchemiser.portfolio.core.portfolio_analysis_service` |

### 🟡 MEDIUM PRIORITY: Lightly-Used Legacy Modules

These modules have 1-2 importers and can be migrated after high priority:

| Module | Importers | Files Importing |
|--------|-----------|-----------------|
| `the_alchemiser.utils.serialization` | 2 | `the_alchemiser.execution.core.account_facade`, `the_alchemiser.portfolio.core.portfolio_management_facade` |
| `the_alchemiser.shared.services.tick_size_service` | 2 | `the_alchemiser.execution.strategies.repeg_strategy`, `the_alchemiser.shared.math.trading_math` |
| `the_alchemiser.shared.utils.handler` | 2 | `the_alchemiser.shared.utils.error_recovery`, `the_alchemiser.shared.utils.error_monitoring` |
| `the_alchemiser.portfolio.services.position_service` | 2 | `the_alchemiser.shared.config.service_providers`, `the_alchemiser.portfolio.services.__init__` |
| `the_alchemiser.shared.utils.service_factory` | 1 | `the_alchemiser.main` |
| `the_alchemiser.application.policies` | 1 | `examples.policy_layer_usage` |
| `the_alchemiser.domain.trading.value_objects.side` | 1 | `examples.policy_layer_usage` |
| `the_alchemiser.domain.trading.value_objects.time_in_force` | 1 | `examples.policy_layer_usage` |
| `the_alchemiser.shared.services.websocket_connection_manager` | 1 | `the_alchemiser.execution.brokers.alpaca_client` |
| `the_alchemiser.shared.utils.exceptions` | 1 | `the_alchemiser.shared.utils.error_recovery` |
| `the_alchemiser.shared.utils.error_handling` | 1 | `the_alchemiser.shared.utils.__init__` |
| `the_alchemiser.shared.utils.error_reporter` | 1 | `the_alchemiser.shared.utils.__init__` |
| `the_alchemiser.shared.services.shared.config_service` | 1 | `the_alchemiser.shared.utils.cache_manager` |
| `the_alchemiser.portfolio.utils.portfolio_pnl_utils` | 1 | `the_alchemiser.shared.reporting.reporting` |
| `the_alchemiser.portfolio.services.rebalancing_policy` | 1 | `the_alchemiser.portfolio.services.__init__` |

### 🟢 LOW PRIORITY: Shim Cleanup

These shim modules can be removed after updating import statements:

| Module | Importers | Files Importing |
|--------|-----------|-----------------|
| `the_alchemiser.shared.value_objects.core_types` | 38 | `the_alchemiser.execution.core.manager`, `the_alchemiser.execution.core.execution_schemas`, `the_alchemiser.execution.core.account_facade` + 35 more |
| `the_alchemiser.execution.core.execution_schemas` | 12 | `the_alchemiser.lambda_handler`, `the_alchemiser.execution.monitoring.websocket_order_monitor`, `the_alchemiser.execution.orders.lifecycle_adapter` + 9 more |
| `the_alchemiser.shared.schemas.base` | 9 | `the_alchemiser.execution.orders.order_schemas`, `the_alchemiser.execution.schemas.smart_trading`, `the_alchemiser.shared.schemas.__init__` + 6 more |
| `the_alchemiser.strategy.signals.strategy_signal` | 8 | `the_alchemiser.strategy.protocols.engine_protocol`, `the_alchemiser.strategy.managers.typed_strategy_manager`, `the_alchemiser.strategy.engines.klm_ensemble_engine` + 5 more |
| `the_alchemiser.execution.core.canonical_executor` | 7 | `examples.policy_layer_usage`, `the_alchemiser.execution.core.execution_manager`, `the_alchemiser.execution.core.execution_manager` + 4 more |
| `the_alchemiser.execution.mappers.orders` | 7 | `the_alchemiser.execution.orders.validation`, `the_alchemiser.execution.core.execution_manager`, `the_alchemiser.execution.mappers.alpaca_dto_mapping` + 4 more |
| `the_alchemiser.main` | 5 | `the_alchemiser.lambda_handler`, `the_alchemiser.strategy.engines.core.trading_engine`, `the_alchemiser.shared.cli.cli` + 2 more |
| `the_alchemiser.execution.brokers.alpaca_client` | 2 | `the_alchemiser.strategy.engines.core.trading_engine`, `the_alchemiser.portfolio.allocation.rebalance_execution_service` |
| `the_alchemiser.portfolio.rebalancing.rebalance_plan` | 2 | `the_alchemiser.portfolio.mappers.portfolio_rebalancing_mapping`, `the_alchemiser.portfolio.schemas.rebalancing` |
| `the_alchemiser.portfolio.positions.position_service` | 2 | `the_alchemiser.execution.core.execution_manager`, `the_alchemiser.execution.core.account_facade` |
| `the_alchemiser.execution.orders.asset_order_handler` | 1 | `the_alchemiser.execution.brokers.alpaca_client` |
| `the_alchemiser.shared.utils.error_handling` | 1 | `the_alchemiser.shared.utils.__init__` |
| `the_alchemiser.portfolio.utils.portfolio_pnl_utils` | 1 | `the_alchemiser.shared.reporting.reporting` |
| `the_alchemiser.portfolio.holdings.position_manager` | 1 | `the_alchemiser.portfolio.positions.legacy_position_manager` |
| `the_alchemiser.portfolio.rebalancing.orchestrator_facade` | 1 | `the_alchemiser.strategy.engines.core.trading_engine` |
| `the_alchemiser.portfolio.positions.legacy_position_manager` | 1 | `the_alchemiser.execution.brokers.alpaca_client` |

## Recommended Migration Strategy

### Phase 1: High Priority Migration
1. Create new modular implementations for heavily-used legacy modules
2. Update import statements in all importing files
3. Test thoroughly after each module migration
4. Remove legacy module after successful migration

### Phase 2: Medium Priority Migration
1. Handle lightly-used legacy modules
2. Combine similar modules where possible
3. Update documentation and examples

### Phase 3: Shim Cleanup
1. Update import statements to use new module locations
2. Remove shim files after import migration
3. Run import-linter to verify clean module boundaries

## Safety Recommendations

- Always migrate modules with fewer dependencies first when possible
- Create tests for new modular implementations before migration
- Use deprecation warnings during transition period
- Keep legacy modules temporarily for rollback safety
- Monitor CI/CD pipeline for import-related failures

---
*Generated by import_dependency_analyzer.py*