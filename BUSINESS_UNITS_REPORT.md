# Business Units Report

This document provides an inventory of all modules in the Alchemiser system, categorized by business unit and status.

## Business Unit Classifications

Every module is classified under one of these business units:
- **strategy & signal generation**: Strategy engines, signal computation, and technical analysis
- **portfolio assessment & management**: Portfolio rebalancing, position management, and risk assessment
- **order execution/placement**: Order routing, execution algorithms, and trade settlement
- **utilities**: Cross-cutting concerns, shared infrastructure, and support functions

## Status Classifications
- **current**: Actively maintained, follows current architecture patterns
- **legacy**: Older code that may need refactoring or migration

---

## DDD Bounded Contexts Structure

### Strategy Context
**Purpose**: Signal generation, indicator calculation, regime detection, strategy composition

#### Domain Layer
**Business Unit**: strategy & signal generation | **Status**: current


#### Domain Layer
**Business Unit**: strategy & signal generation | **Status**: current

- `strategy/domain/__init__.py`
- `strategy/domain/ast.py`
- `strategy/domain/engine.py`
- `strategy/domain/entities/__init__.py`
- `strategy/domain/errors.py`
- `strategy/domain/errors/__init__.py`
- `strategy/domain/errors/strategy_errors.py`
- `strategy/domain/evaluator.py`
- `strategy/domain/evaluator_cache.py`
- `strategy/domain/interning.py`
- `strategy/domain/klm_workers/__init__.py`
- `strategy/domain/klm_workers/base_klm_variant.py`
- `strategy/domain/klm_workers/variant_1200_28.py`
- `strategy/domain/klm_workers/variant_1280_26.py`
- `strategy/domain/klm_workers/variant_410_38.py`
- `strategy/domain/klm_workers/variant_506_38.py`
- `strategy/domain/klm_workers/variant_520_22.py`
- `strategy/domain/klm_workers/variant_530_18.py`
- `strategy/domain/klm_workers/variant_830_21.py`
- `strategy/domain/klm_workers/variant_nova.py`
- `strategy/domain/models/__init__.py`
- `strategy/domain/models/strategy_position_model.py`
- `strategy/domain/models/strategy_signal_model.py`
- `strategy/domain/nuclear_logic.py`
- `strategy/domain/nuclear_typed_engine.py`
- `strategy/domain/optimization_config.py`
- `strategy/domain/parser.py`
- `strategy/domain/protocols/__init__.py`
- `strategy/domain/protocols/strategy_engine.py`
- `strategy/domain/strategy.py`
- `strategy/domain/strategy_loader.py`
- `strategy/domain/strategy_manager.py`
- `strategy/domain/tecl_strategy_engine.py`
- `strategy/domain/typed_klm_ensemble_engine.py`
- `strategy/domain/typed_strategy_manager.py`
- `strategy/domain/value_objects/alert.py`
- `strategy/domain/value_objects/confidence.py`
- `strategy/domain/value_objects/strategy_signal.py`


#### Application Layer
**Business Unit**: strategy & signal generation | **Status**: current

- `strategy/application/__init__.py`
- `strategy/application/integration.py`
- `strategy/application/strategy_order_tracker.py`


#### Infrastructure Layer
**Business Unit**: strategy & signal generation | **Status**: current

- `strategy/infrastructure/__init__.py`
- `strategy/infrastructure/market_data.py`
- `strategy/infrastructure/market_data/__init__.py`
- `strategy/infrastructure/market_data/market_data_client.py`
- `strategy/infrastructure/market_data/market_data_service.py`
- `strategy/infrastructure/market_data/price_fetching_utils.py`
- `strategy/infrastructure/market_data/price_service.py`
- `strategy/infrastructure/market_data/price_utils.py`
- `strategy/infrastructure/market_data/strategy_market_data_service.py`
- `strategy/infrastructure/market_data/streaming_service.py`
- `strategy/infrastructure/models/bar.py`
- `strategy/infrastructure/models/quote.py`
- `strategy/infrastructure/protocols/market_data_port.py`
- `strategy/infrastructure/real_time_pricing.py`


#### Interfaces Layer
**Business Unit**: strategy & signal generation | **Status**: current

- `strategy/interfaces/__init__.py`


### Portfolio Context
**Purpose**: Portfolio state, valuation, allocations, risk constraints, rebalancing decisions

#### Domain Layer
**Business Unit**: portfolio assessment & management | **Status**: current

- `portfolio/domain/__init__.py`
- `portfolio/domain/account.py`
- `portfolio/domain/position/__init__.py`
- `portfolio/domain/position/position_analyzer.py`
- `portfolio/domain/position/position_delta.py`
- `portfolio/domain/rebalancing/__init__.py`
- `portfolio/domain/rebalancing/rebalance_calculator.py`
- `portfolio/domain/rebalancing/rebalance_plan.py`
- `portfolio/domain/strategy_attribution/__init__.py`
- `portfolio/domain/strategy_attribution/attribution_engine.py`
- `portfolio/domain/strategy_attribution/symbol_classifier.py`


#### Application Layer
**Business Unit**: portfolio assessment & management | **Status**: current

- `portfolio/application/__init__.py`
- `portfolio/application/portfolio_pnl_utils.py`
- `portfolio/application/rebalancing_orchestrator.py`
- `portfolio/application/rebalancing_orchestrator_facade.py`
- `portfolio/application/reporting.py`
- `portfolio/application/services/__init__.py`
- `portfolio/application/services/account_service.py`
- `portfolio/application/services/account_utils.py`
- `portfolio/application/services/portfolio_analysis_service.py`
- `portfolio/application/services/portfolio_management_facade.py`
- `portfolio/application/services/portfolio_rebalancing_service.py`
- `portfolio/application/services/position_manager.py`
- `portfolio/application/services/position_service.py`
- `portfolio/application/services/rebalance_execution_service.py`


#### Infrastructure Layer
**Business Unit**: portfolio assessment & management | **Status**: current

- `portfolio/infrastructure/__init__.py`


#### Interfaces Layer
**Business Unit**: portfolio assessment & management | **Status**: current

- `portfolio/interfaces/__init__.py`


### Execution Context
**Purpose**: Order validation, smart execution strategies, routing, monitoring fill lifecycle

#### Domain Layer
**Business Unit**: order execution/placement | **Status**: current

- `execution/domain/__init__.py`
- `execution/domain/base_policy.py`
- `execution/domain/buying_power_policy.py`
- `execution/domain/entities/order.py`
- `execution/domain/errors/__init__.py`
- `execution/domain/errors/classifier.py`
- `execution/domain/errors/error_categories.py`
- `execution/domain/errors/error_codes.py`
- `execution/domain/errors/order_error.py`
- `execution/domain/fractionability_policy.py`
- `execution/domain/lifecycle/__init__.py`
- `execution/domain/lifecycle/events.py`
- `execution/domain/lifecycle/exceptions.py`
- `execution/domain/lifecycle/protocols.py`
- `execution/domain/lifecycle/states.py`
- `execution/domain/lifecycle/transitions.py`
- `execution/domain/policy_result.py`
- `execution/domain/position_policy.py`
- `execution/domain/protocols.py`
- `execution/domain/protocols/__init__.py`
- `execution/domain/protocols/order_lifecycle.py`
- `execution/domain/protocols/trading_repository.py`
- `execution/domain/risk_policy.py`
- `execution/domain/value_objects/order_id.py`
- `execution/domain/value_objects/order_request.py`
- `execution/domain/value_objects/order_status.py`
- `execution/domain/value_objects/order_status_literal.py`
- `execution/domain/value_objects/order_type.py`
- `execution/domain/value_objects/quantity.py`
- `execution/domain/value_objects/side.py`
- `execution/domain/value_objects/symbol.py`
- `execution/domain/value_objects/time_in_force.py`


#### Application Layer
**Business Unit**: order execution/placement | **Status**: current

- `execution/application/__init__.py`
- `execution/application/account_facade.py`
- `execution/application/alpaca_client.py`
- `execution/application/asset_order_handler.py`
- `execution/application/bootstrap.py`
- `execution/application/buying_power_policy_impl.py`
- `execution/application/canonical_executor.py`
- `execution/application/canonical_integration_example.py`
- `execution/application/engine_service.py`
- `execution/application/execution_manager.py`
- `execution/application/fractionability_policy_impl.py`
- `execution/application/lifecycle/__init__.py`
- `execution/application/lifecycle/dispatcher.py`
- `execution/application/lifecycle/manager.py`
- `execution/application/lifecycle/observers.py`
- `execution/application/order_lifecycle_adapter.py`
- `execution/application/order_request_builder.py`
- `execution/application/order_validation.py`
- `execution/application/order_validation_utils.py`
- `execution/application/policy_factory.py`
- `execution/application/policy_orchestrator.py`
- `execution/application/portfolio_calculations.py`
- `execution/application/ports.py`
- `execution/application/position_policy_impl.py`
- `execution/application/progressive_order_utils.py`
- `execution/application/risk_policy_impl.py`
- `execution/application/services/__init__.py`
- `execution/application/services/order_service.py`
- `execution/application/smart_execution.py`
- `execution/application/smart_pricing_handler.py`
- `execution/application/spread_assessment.py`
- `execution/application/strategies/__init__.py`
- `execution/application/strategies/aggressive_limit_strategy.py`
- `execution/application/strategies/config.py`
- `execution/application/strategies/execution_context_adapter.py`
- `execution/application/strategies/repeg_strategy.py`


#### Infrastructure Layer
**Business Unit**: order execution/placement | **Status**: current

- `execution/infrastructure/__init__.py`
- `execution/infrastructure/brokers/__init__.py`
- `execution/infrastructure/brokers/trading_service_manager.py`
- `execution/infrastructure/repositories/__init__.py`
- `execution/infrastructure/repositories/alpaca_manager.py`


#### Interfaces Layer
**Business Unit**: order execution/placement | **Status**: current

- `execution/interfaces/__init__.py`


### Shared Kernel
**Purpose**: Cross-cutting concerns and shared value objects

#### Domain Layer
**Business Unit**: utilities | **Status**: current

- `shared_kernel/domain/__init__.py`
- `shared_kernel/domain/account_like.py`
- `shared_kernel/domain/account_repository.py`
- `shared_kernel/domain/asset_info.py`
- `shared_kernel/domain/indicator_utils.py`
- `shared_kernel/domain/indicators.py`
- `shared_kernel/domain/market_data_repository.py`
- `shared_kernel/domain/market_timing_utils.py`
- `shared_kernel/domain/math_utils.py`
- `shared_kernel/domain/order_like.py`
- `shared_kernel/domain/position_like.py`
- `shared_kernel/domain/protocols/__init__.py`
- `shared_kernel/domain/protocols/asset_metadata_provider.py`
- `shared_kernel/domain/rebalancing_policy.py`
- `shared_kernel/domain/strategy_registry.py`
- `shared_kernel/domain/trading_math.py`
- `shared_kernel/domain/trading_repository.py`
- `shared_kernel/domain/types.py`


#### Application Layer
**Business Unit**: utilities | **Status**: current

- `shared_kernel/application/__init__.py`


#### Infrastructure Layer
**Business Unit**: utilities | **Status**: current

- `shared_kernel/infrastructure/__init__.py`
- `shared_kernel/infrastructure/alert_service.py`
- `shared_kernel/infrastructure/application_container.py`
- `shared_kernel/infrastructure/client.py`
- `shared_kernel/infrastructure/config.py`
- `shared_kernel/infrastructure/config/__init__.py`
- `shared_kernel/infrastructure/config/config_service.py`
- `shared_kernel/infrastructure/config_providers.py`
- `shared_kernel/infrastructure/config_utils.py`
- `shared_kernel/infrastructure/email_utils.py`
- `shared_kernel/infrastructure/errors/__init__.py`
- `shared_kernel/infrastructure/errors/context.py`
- `shared_kernel/infrastructure/errors/decorators.py`
- `shared_kernel/infrastructure/errors/error_handling.py`
- `shared_kernel/infrastructure/errors/error_monitoring.py`
- `shared_kernel/infrastructure/errors/error_recovery.py`
- `shared_kernel/infrastructure/errors/error_reporter.py`
- `shared_kernel/infrastructure/errors/exceptions.py`
- `shared_kernel/infrastructure/errors/handler.py`
- `shared_kernel/infrastructure/errors/scope.py`
- `shared_kernel/infrastructure/execution_config.py`
- `shared_kernel/infrastructure/indicator_validator.py`
- `shared_kernel/infrastructure/infrastructure_providers.py`
- `shared_kernel/infrastructure/logging_utils.py`
- `shared_kernel/infrastructure/s3_utils.py`
- `shared_kernel/infrastructure/secrets/__init__.py`
- `shared_kernel/infrastructure/secrets/secrets_service.py`
- `shared_kernel/infrastructure/secrets_manager.py`
- `shared_kernel/infrastructure/service_providers.py`
- `shared_kernel/infrastructure/slippage_analyzer.py`
- `shared_kernel/infrastructure/templates/__init__.py`
- `shared_kernel/infrastructure/templates/base.py`
- `shared_kernel/infrastructure/templates/error_report.py`
- `shared_kernel/infrastructure/templates/multi_strategy.py`
- `shared_kernel/infrastructure/templates/performance.py`
- `shared_kernel/infrastructure/templates/portfolio.py`
- `shared_kernel/infrastructure/templates/signals.py`
- `shared_kernel/infrastructure/templates/trading_report.py`
- `shared_kernel/infrastructure/tick_size_service.py`
- `shared_kernel/infrastructure/utilities/__init__.py`
- `shared_kernel/infrastructure/websocket_connection_manager.py`
- `shared_kernel/infrastructure/websocket_order_monitor.py`


#### Interfaces Layer
**Business Unit**: utilities | **Status**: current

- `shared_kernel/interfaces/__init__.py`
- `shared_kernel/interfaces/accounts.py`
- `shared_kernel/interfaces/alpaca.py`
- `shared_kernel/interfaces/base.py`
- `shared_kernel/interfaces/cli.py`
- `shared_kernel/interfaces/cli_formatter.py`
- `shared_kernel/interfaces/common.py`
- `shared_kernel/interfaces/dashboard_utils.py`
- `shared_kernel/interfaces/enriched_data.py`
- `shared_kernel/interfaces/error_display_utils.py`
- `shared_kernel/interfaces/errors.py`
- `shared_kernel/interfaces/execution.py`
- `shared_kernel/interfaces/execution_summary.py`
- `shared_kernel/interfaces/market_data.py`
- `shared_kernel/interfaces/operations.py`
- `shared_kernel/interfaces/orders.py`
- `shared_kernel/interfaces/portfolio_calculations.py`
- `shared_kernel/interfaces/portfolio_rebalancing.py`
- `shared_kernel/interfaces/positions.py`
- `shared_kernel/interfaces/reporting.py`
- `shared_kernel/interfaces/serialization.py`
- `shared_kernel/interfaces/signal_analyzer.py`
- `shared_kernel/interfaces/signal_display_utils.py`
- `shared_kernel/interfaces/smart_trading.py`
- `shared_kernel/interfaces/tracking.py`
- `shared_kernel/interfaces/trading_executor.py`


### Anti-Corruption Layer
**Purpose**: External ↔ internal mappers and translation

**Business Unit**: utilities | **Status**: current

- `anti_corruption/__init__.py`
- `anti_corruption/account_mapping.py`
- `anti_corruption/alpaca_dto_mapping.py`
- `anti_corruption/application/__init__.py`
- `anti_corruption/domain/__init__.py`
- `anti_corruption/execution.py`
- `anti_corruption/execution_summary_mapping.py`
- `anti_corruption/infrastructure/__init__.py`
- `anti_corruption/interfaces/__init__.py`
- `anti_corruption/market_data_mappers.py`
- `anti_corruption/market_data_mapping.py`
- `anti_corruption/models/__init__.py`
- `anti_corruption/models/order.py`
- `anti_corruption/models/position.py`
- `anti_corruption/order_mapping.py`
- `anti_corruption/orders.py`
- `anti_corruption/pandas_time_series.py`
- `anti_corruption/policy_mapping.py`
- `anti_corruption/portfolio_rebalancing_mapping.py`
- `anti_corruption/position_mapping.py`
- `anti_corruption/strategies.py`
- `anti_corruption/strategy_domain_mapping.py`
- `anti_corruption/strategy_market_data_adapter.py`
- `anti_corruption/strategy_signal_mapping.py`
- `anti_corruption/tracking.py`
- `anti_corruption/tracking_mapping.py`
- `anti_corruption/tracking_normalization.py`
- `anti_corruption/trading_service_dto_mapping.py`


### Top-Level Modules
**Business Unit**: utilities | **Status**: current

- `the_alchemiser/__init__.py`
- `the_alchemiser/lambda_handler.py`
- `the_alchemiser/main.py`


---

## Summary

**Total modules**: 275
**Architecture**: Domain-Driven Design with bounded contexts
**Migration status**: Complete - all legacy services/ directory content migrated
