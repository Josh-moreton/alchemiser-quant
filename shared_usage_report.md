# Shared Module Usage Report

Static analysis of `the_alchemiser.shared` module usage across the repository.

## Summary

- **Total shared files analyzed**: 104
- **Files with no importers**: 70
- **Total public symbols**: 438
- **Unused symbols**: 376

## Potentially Unused Files

- `the_alchemiser/shared/brokers/alpaca_utils.py` (9 public symbols)
- `the_alchemiser/shared/cli/base_cli.py` (1 public symbols)
- `the_alchemiser/shared/cli/cli.py` (16 public symbols)
- `the_alchemiser/shared/cli/dashboard_utils.py` (6 public symbols)
- `the_alchemiser/shared/cli/strategy_tracking_utils.py` (3 public symbols)
- `the_alchemiser/shared/config/config_providers.py` (1 public symbols)
- `the_alchemiser/shared/config/config_service.py` (1 public symbols)
- `the_alchemiser/shared/config/env_loader.py` (0 public symbols)
- `the_alchemiser/shared/config/infrastructure_providers.py` (1 public symbols)
- `the_alchemiser/shared/config/secrets_manager.py` (3 public symbols)
- `the_alchemiser/shared/config/service_providers.py` (1 public symbols)
- `the_alchemiser/shared/dto/broker_dto.py` (5 public symbols)
- `the_alchemiser/shared/dto/execution_report_dto.py` (2 public symbols)
- `the_alchemiser/shared/dto/lambda_event_dto.py` (1 public symbols)
- `the_alchemiser/shared/dto/order_request_dto.py` (2 public symbols)
- `the_alchemiser/shared/errors/context.py` (1 public symbols)
- `the_alchemiser/shared/events/handlers.py` (1 public symbols)
- `the_alchemiser/shared/logging/logging.py` (3 public symbols)
- `the_alchemiser/shared/mappers/execution_summary_mapping.py` (7 public symbols)
- `the_alchemiser/shared/mappers/market_data_mappers.py` (2 public symbols)
- `the_alchemiser/shared/math/asset_info.py` (3 public symbols)
- `the_alchemiser/shared/math/num.py` (3 public symbols)
- `the_alchemiser/shared/math/trading_math.py` (6 public symbols)
- `the_alchemiser/shared/notifications/client.py` (2 public symbols)
- `the_alchemiser/shared/notifications/config.py` (3 public symbols)
- `the_alchemiser/shared/notifications/templates/base.py` (1 public symbols)
- `the_alchemiser/shared/notifications/templates/email_facade.py` (4 public symbols)
- `the_alchemiser/shared/notifications/templates/multi_strategy.py` (1 public symbols)
- `the_alchemiser/shared/notifications/templates/performance.py` (1 public symbols)
- `the_alchemiser/shared/notifications/templates/portfolio.py` (3 public symbols)
- `the_alchemiser/shared/notifications/templates/signals.py` (1 public symbols)
- `the_alchemiser/shared/persistence/factory.py` (3 public symbols)
- `the_alchemiser/shared/persistence/local_handler.py` (1 public symbols)
- `the_alchemiser/shared/persistence/s3_handler.py` (1 public symbols)
- `the_alchemiser/shared/protocols/alpaca.py` (2 public symbols)
- `the_alchemiser/shared/protocols/asset_metadata.py` (1 public symbols)
- `the_alchemiser/shared/protocols/order_like.py` (2 public symbols)
- `the_alchemiser/shared/protocols/persistence.py` (1 public symbols)
- `the_alchemiser/shared/protocols/repository.py` (3 public symbols)
- `the_alchemiser/shared/protocols/strategy_tracking.py` (4 public symbols)
- `the_alchemiser/shared/reporting/reporting.py` (3 public symbols)
- `the_alchemiser/shared/schemas/accounts.py` (14 public symbols)
- `the_alchemiser/shared/schemas/base.py` (2 public symbols)
- `the_alchemiser/shared/schemas/cli.py` (6 public symbols)
- `the_alchemiser/shared/schemas/enriched_data.py` (8 public symbols)
- `the_alchemiser/shared/schemas/errors.py` (5 public symbols)
- `the_alchemiser/shared/schemas/execution_summary.py` (12 public symbols)
- `the_alchemiser/shared/schemas/market_data.py` (10 public symbols)
- `the_alchemiser/shared/schemas/operations.py` (6 public symbols)
- `the_alchemiser/shared/schemas/reporting.py` (7 public symbols)
- `the_alchemiser/shared/services/market_data_service.py` (1 public symbols)
- `the_alchemiser/shared/services/real_time_pricing.py` (3 public symbols)
- `the_alchemiser/shared/services/tick_size_service.py` (2 public symbols)
- `the_alchemiser/shared/types/account.py` (2 public symbols)
- `the_alchemiser/shared/types/broker_enums.py` (4 public symbols)
- `the_alchemiser/shared/types/money.py` (1 public symbols)
- `the_alchemiser/shared/types/quantity.py` (1 public symbols)
- `the_alchemiser/shared/types/quote.py` (1 public symbols)
- `the_alchemiser/shared/types/time_in_force.py` (1 public symbols)
- `the_alchemiser/shared/types/trading_errors.py` (2 public symbols)
- `the_alchemiser/shared/utils/config.py` (3 public symbols)
- `the_alchemiser/shared/utils/context.py` (2 public symbols)
- `the_alchemiser/shared/utils/decorators.py` (6 public symbols)
- `the_alchemiser/shared/utils/dto_conversion.py` (8 public symbols)
- `the_alchemiser/shared/utils/error_reporter.py` (4 public symbols)
- `the_alchemiser/shared/utils/price_discovery_utils.py` (7 public symbols)
- `the_alchemiser/shared/utils/serialization.py` (2 public symbols)
- `the_alchemiser/shared/utils/timezone_utils.py` (3 public symbols)
- `the_alchemiser/shared/utils/validation_utils.py` (10 public symbols)
- `the_alchemiser/shared/value_objects/identifier.py` (2 public symbols)

## Detailed Usage Analysis

### the_alchemiser.shared.brokers.alpaca_manager

- **File**: `the_alchemiser/shared/brokers/alpaca_manager.py`
- **Importer count**: 4
- **Confidence**: high
- **Public symbols**: 3
- **Imported symbols**: 1
- **Unused symbols**: 2
- **Importers** (4):
  - `the_alchemiser/execution_v2/core/execution_manager.py`
  - `the_alchemiser/execution_v2/core/executor.py`
  - `the_alchemiser/portfolio_v2/adapters/alpaca_data_adapter.py`
  - `the_alchemiser/portfolio_v2/core/portfolio_service.py`
- **Unused symbols**: ['create_alpaca_manager', 'logger']

### the_alchemiser.shared.brokers.alpaca_utils

- **File**: `the_alchemiser/shared/brokers/alpaca_utils.py`
- **Importer count**: 0
- **Confidence**: high
- **Public symbols**: 9
- **Imported symbols**: 0
- **Unused symbols**: 9
- **Unused symbols**: ['create_data_client', 'create_stock_bars_request', 'create_stock_data_stream', 'create_stock_latest_quote_request', 'create_timeframe', 'create_trading_client', 'create_trading_stream', 'get_alpaca_quote_type', 'get_alpaca_trade_type']

### the_alchemiser.shared.cli.base_cli

- **File**: `the_alchemiser/shared/cli/base_cli.py`
- **Importer count**: 0
- **Confidence**: high
- **Public symbols**: 1
- **Imported symbols**: 0
- **Unused symbols**: 1
- **Unused symbols**: ['BaseCLI']

### the_alchemiser.shared.cli.cli

- **File**: `the_alchemiser/shared/cli/cli.py`
- **Importer count**: 0
- **Confidence**: high
- **Public symbols**: 16
- **Imported symbols**: 0
- **Unused symbols**: 16
- **Unused symbols**: ['PROGRESS_DESCRIPTION_FORMAT', 'STYLE_BOLD_BLUE', 'STYLE_BOLD_CYAN', 'STYLE_BOLD_GREEN', 'STYLE_BOLD_MAGENTA', 'STYLE_BOLD_RED', 'STYLE_BOLD_YELLOW', 'STYLE_ITALIC', 'app', 'console', 'deploy', 'main', 'show_welcome', 'status', 'trade', 'version']

### the_alchemiser.shared.cli.cli_formatter

- **File**: `the_alchemiser/shared/cli/cli_formatter.py`
- **Importer count**: 1
- **Confidence**: high
- **Public symbols**: 12
- **Imported symbols**: 2
- **Unused symbols**: 10
- **Importers** (1):
  - `the_alchemiser/main.py`
- **Unused symbols**: ['render_account_info', 'render_enriched_order_summaries', 'render_execution_plan', 'render_multi_strategy_summary', 'render_multi_strategy_summary_dto', 'render_orders_executed', 'render_portfolio_allocation', 'render_strategy_signals', 'render_target_vs_current_allocations', 'render_technical_indicators']

### the_alchemiser.shared.cli.dashboard_utils

- **File**: `the_alchemiser/shared/cli/dashboard_utils.py`
- **Importer count**: 0
- **Confidence**: high
- **Public symbols**: 6
- **Imported symbols**: 0
- **Unused symbols**: 6
- **Unused symbols**: ['build_basic_dashboard_structure', 'build_s3_paths', 'extract_portfolio_metrics', 'extract_positions_data', 'extract_recent_trades_data', 'extract_strategies_data']

### the_alchemiser.shared.cli.strategy_tracking_utils

- **File**: `the_alchemiser/shared/cli/strategy_tracking_utils.py`
- **Importer count**: 0
- **Confidence**: high
- **Public symbols**: 3
- **Imported symbols**: 0
- **Unused symbols**: 3
- **Unused symbols**: ['BOLD_MAGENTA_STYLE', 'display_detailed_strategy_positions', 'display_strategy_tracking']

### the_alchemiser.shared.cli.trading_executor

- **File**: `the_alchemiser/shared/cli/trading_executor.py`
- **Importer count**: 1
- **Confidence**: high
- **Public symbols**: 2
- **Imported symbols**: 1
- **Unused symbols**: 1
- **Importers** (1):
  - `the_alchemiser/main.py`
- **Unused symbols**: ['ExecutionResult']

### the_alchemiser.shared.config.confidence_config

- **File**: `the_alchemiser/shared/config/confidence_config.py`
- **Importer count**: 4
- **Confidence**: high
- **Public symbols**: 5
- **Imported symbols**: 3
- **Unused symbols**: 2
- **Importers** (4):
  - `the_alchemiser/orchestration/strategy_orchestrator.py`
  - `the_alchemiser/strategy_v2/engines/klm/engine.py`
  - `the_alchemiser/strategy_v2/engines/nuclear/engine.py`
  - `the_alchemiser/strategy_v2/engines/tecl/engine.py`
- **Unused symbols**: ['AggregationConfig', 'KLMConfidenceConfig']

### the_alchemiser.shared.config.config

- **File**: `the_alchemiser/shared/config/config.py`
- **Importer count**: 5
- **Confidence**: high
- **Public symbols**: 12
- **Imported symbols**: 2
- **Unused symbols**: 10
- **Importers** (5):
  - `the_alchemiser/lambda_handler.py`
  - `the_alchemiser/main.py`
  - `the_alchemiser/orchestration/portfolio_orchestrator.py`
  - `the_alchemiser/orchestration/signal_orchestrator.py`
  - `the_alchemiser/orchestration/trading_orchestrator.py`
- **Unused symbols**: ['AlertsSettings', 'AlpacaSettings', 'AwsSettings', 'DataSettings', 'EmailSettings', 'ExecutionSettings', 'LoggingSettings', 'SecretsManagerSettings', 'StrategySettings', 'TrackingSettings']

### the_alchemiser.shared.config.config_providers

- **File**: `the_alchemiser/shared/config/config_providers.py`
- **Importer count**: 0
- **Confidence**: high
- **Public symbols**: 1
- **Imported symbols**: 0
- **Unused symbols**: 1
- **Unused symbols**: ['ConfigProviders']

### the_alchemiser.shared.config.config_service

- **File**: `the_alchemiser/shared/config/config_service.py`
- **Importer count**: 0
- **Confidence**: high
- **Public symbols**: 1
- **Imported symbols**: 0
- **Unused symbols**: 1
- **Unused symbols**: ['ConfigService']

### the_alchemiser.shared.config.container

- **File**: `the_alchemiser/shared/config/container.py`
- **Importer count**: 5
- **Confidence**: high
- **Public symbols**: 1
- **Imported symbols**: 1
- **Unused symbols**: 0
- **Importers** (5):
  - `the_alchemiser/main.py`
  - `the_alchemiser/orchestration/event_driven_orchestrator.py`
  - `the_alchemiser/orchestration/portfolio_orchestrator.py`
  - `the_alchemiser/orchestration/signal_orchestrator.py`
  - `the_alchemiser/orchestration/trading_orchestrator.py`

### the_alchemiser.shared.config.env_loader

- **File**: `the_alchemiser/shared/config/env_loader.py`
- **Importer count**: 0
- **Confidence**: high
- **Public symbols**: 0
- **Imported symbols**: 0
- **Unused symbols**: 0

### the_alchemiser.shared.config.infrastructure_providers

- **File**: `the_alchemiser/shared/config/infrastructure_providers.py`
- **Importer count**: 0
- **Confidence**: high
- **Public symbols**: 1
- **Imported symbols**: 0
- **Unused symbols**: 1
- **Unused symbols**: ['InfrastructureProviders']

### the_alchemiser.shared.config.secrets_adapter

- **File**: `the_alchemiser/shared/config/secrets_adapter.py`
- **Importer count**: 2
- **Confidence**: high
- **Public symbols**: 4
- **Imported symbols**: 1
- **Unused symbols**: 3
- **Importers** (2):
  - `the_alchemiser/lambda_handler.py`
  - `the_alchemiser/main.py`
- **Unused symbols**: ['get_email_password', 'get_twelvedata_api_key', 'logger']

### the_alchemiser.shared.config.secrets_manager

- **File**: `the_alchemiser/shared/config/secrets_manager.py`
- **Importer count**: 0
- **Confidence**: high
- **Public symbols**: 3
- **Imported symbols**: 0
- **Unused symbols**: 3
- **Unused symbols**: ['SecretsManager', 'logger', 'secrets_manager']

### the_alchemiser.shared.config.service_providers

- **File**: `the_alchemiser/shared/config/service_providers.py`
- **Importer count**: 0
- **Confidence**: high
- **Public symbols**: 1
- **Imported symbols**: 0
- **Unused symbols**: 1
- **Unused symbols**: ['ServiceProviders']

### the_alchemiser.shared.dto.broker_dto

- **File**: `the_alchemiser/shared/dto/broker_dto.py`
- **Importer count**: 0
- **Confidence**: high
- **Public symbols**: 5
- **Imported symbols**: 0
- **Unused symbols**: 5
- **Unused symbols**: ['OrderExecutionResult', 'OrderExecutionResultDTO', 'WebSocketResult', 'WebSocketResultDTO', 'WebSocketStatus']

### the_alchemiser.shared.dto.consolidated_portfolio_dto

- **File**: `the_alchemiser/shared/dto/consolidated_portfolio_dto.py`
- **Importer count**: 2
- **Confidence**: high
- **Public symbols**: 1
- **Imported symbols**: 1
- **Unused symbols**: 0
- **Importers** (2):
  - `the_alchemiser/orchestration/portfolio_orchestrator.py`
  - `the_alchemiser/orchestration/signal_orchestrator.py`

### the_alchemiser.shared.dto.execution_report_dto

- **File**: `the_alchemiser/shared/dto/execution_report_dto.py`
- **Importer count**: 0
- **Confidence**: high
- **Public symbols**: 2
- **Imported symbols**: 0
- **Unused symbols**: 2
- **Unused symbols**: ['ExecutedOrderDTO', 'ExecutionReportDTO']

### the_alchemiser.shared.dto.lambda_event_dto

- **File**: `the_alchemiser/shared/dto/lambda_event_dto.py`
- **Importer count**: 0
- **Confidence**: high
- **Public symbols**: 1
- **Imported symbols**: 0
- **Unused symbols**: 1
- **Unused symbols**: ['LambdaEventDTO']

### the_alchemiser.shared.dto.order_request_dto

- **File**: `the_alchemiser/shared/dto/order_request_dto.py`
- **Importer count**: 0
- **Confidence**: high
- **Public symbols**: 2
- **Imported symbols**: 0
- **Unused symbols**: 2
- **Unused symbols**: ['MarketDataDTO', 'OrderRequestDTO']

### the_alchemiser.shared.dto.portfolio_state_dto

- **File**: `the_alchemiser/shared/dto/portfolio_state_dto.py`
- **Importer count**: 2
- **Confidence**: high
- **Public symbols**: 3
- **Imported symbols**: 2
- **Unused symbols**: 1
- **Importers** (2):
  - `the_alchemiser/orchestration/portfolio_orchestrator.py`
  - `the_alchemiser/orchestration/trading_orchestrator.py`
- **Unused symbols**: ['PositionDTO']

### the_alchemiser.shared.dto.rebalance_plan_dto

- **File**: `the_alchemiser/shared/dto/rebalance_plan_dto.py`
- **Importer count**: 7
- **Confidence**: high
- **Public symbols**: 2
- **Imported symbols**: 2
- **Unused symbols**: 0
- **Importers** (7):
  - `the_alchemiser/execution_v2/core/execution_manager.py`
  - `the_alchemiser/execution_v2/core/execution_tracker.py`
  - `the_alchemiser/execution_v2/core/executor.py`
  - `the_alchemiser/orchestration/portfolio_orchestrator.py`
  - `the_alchemiser/orchestration/trading_orchestrator.py`
  - `the_alchemiser/portfolio_v2/core/planner.py`
  - `the_alchemiser/portfolio_v2/core/portfolio_service.py`

### the_alchemiser.shared.dto.signal_dto

- **File**: `the_alchemiser/shared/dto/signal_dto.py`
- **Importer count**: 1
- **Confidence**: high
- **Public symbols**: 1
- **Imported symbols**: 1
- **Unused symbols**: 0
- **Importers** (1):
  - `the_alchemiser/orchestration/signal_orchestrator.py`

### the_alchemiser.shared.dto.strategy_allocation_dto

- **File**: `the_alchemiser/shared/dto/strategy_allocation_dto.py`
- **Importer count**: 3
- **Confidence**: high
- **Public symbols**: 1
- **Imported symbols**: 1
- **Unused symbols**: 0
- **Importers** (3):
  - `the_alchemiser/orchestration/portfolio_orchestrator.py`
  - `the_alchemiser/portfolio_v2/core/planner.py`
  - `the_alchemiser/portfolio_v2/core/portfolio_service.py`

### the_alchemiser.shared.errors.context

- **File**: `the_alchemiser/shared/errors/context.py`
- **Importer count**: 0
- **Confidence**: high
- **Public symbols**: 1
- **Imported symbols**: 0
- **Unused symbols**: 1
- **Unused symbols**: ['ErrorContextData']

### the_alchemiser.shared.errors.error_handler

- **File**: `the_alchemiser/shared/errors/error_handler.py`
- **Importer count**: 3
- **Confidence**: high
- **Public symbols**: 23
- **Imported symbols**: 3
- **Unused symbols**: 20
- **Importers** (3):
  - `the_alchemiser/lambda_handler.py`
  - `the_alchemiser/main.py`
  - `the_alchemiser/orchestration/trading_orchestrator.py`
- **Unused symbols**: ['CircuitBreaker', 'CircuitBreakerOpenError', 'EnhancedAlchemiserError', 'EnhancedDataError', 'EnhancedErrorReporter', 'EnhancedTradingError', 'ErrorCategory', 'ErrorDetailInfo', 'ErrorDetails', 'ErrorNotificationData', 'ErrorReportSummary', 'ErrorSeverity', 'ErrorSummaryData', 'categorize_error_severity', 'create_enhanced_error', 'get_enhanced_error_reporter', 'get_error_handler', 'get_global_error_reporter', 'handle_errors_with_retry', 'retry_with_backoff']

### the_alchemiser.shared.events.base

- **File**: `the_alchemiser/shared/events/base.py`
- **Importer count**: 1
- **Confidence**: high
- **Public symbols**: 1
- **Imported symbols**: 1
- **Unused symbols**: 0
- **Importers** (1):
  - `the_alchemiser/orchestration/event_driven_orchestrator.py`

### the_alchemiser.shared.events.bus

- **File**: `the_alchemiser/shared/events/bus.py`
- **Importer count**: 5
- **Confidence**: high
- **Public symbols**: 1
- **Imported symbols**: 1
- **Unused symbols**: 0
- **Importers** (5):
  - `the_alchemiser/main.py`
  - `the_alchemiser/orchestration/event_driven_orchestrator.py`
  - `the_alchemiser/orchestration/portfolio_orchestrator.py`
  - `the_alchemiser/orchestration/signal_orchestrator.py`
  - `the_alchemiser/orchestration/trading_orchestrator.py`

### the_alchemiser.shared.events.handlers

- **File**: `the_alchemiser/shared/events/handlers.py`
- **Importer count**: 0
- **Confidence**: high
- **Public symbols**: 1
- **Imported symbols**: 0
- **Unused symbols**: 1
- **Unused symbols**: ['EventHandler']

### the_alchemiser.shared.events.schemas

- **File**: `the_alchemiser/shared/events/schemas.py`
- **Importer count**: 5
- **Confidence**: high
- **Public symbols**: 8
- **Imported symbols**: 6
- **Unused symbols**: 2
- **Importers** (5):
  - `the_alchemiser/main.py`
  - `the_alchemiser/orchestration/event_driven_orchestrator.py`
  - `the_alchemiser/orchestration/portfolio_orchestrator.py`
  - `the_alchemiser/orchestration/signal_orchestrator.py`
  - `the_alchemiser/orchestration/trading_orchestrator.py`
- **Unused symbols**: ['EVENT_TYPE_DESCRIPTION', 'PortfolioStateChanged']

### the_alchemiser.shared.logging.logging

- **File**: `the_alchemiser/shared/logging/logging.py`
- **Importer count**: 0
- **Confidence**: high
- **Public symbols**: 3
- **Imported symbols**: 0
- **Unused symbols**: 3
- **Unused symbols**: ['get_logger', 'log_with_context', 'setup_logging']

### the_alchemiser.shared.logging.logging_utils

- **File**: `the_alchemiser/shared/logging/logging_utils.py`
- **Importer count**: 12
- **Confidence**: high
- **Public symbols**: 18
- **Imported symbols**: 8
- **Unused symbols**: 10
- **Importers** (12):
  - `the_alchemiser/lambda_handler.py`
  - `the_alchemiser/main.py`
  - `the_alchemiser/orchestration/event_driven_orchestrator.py`
  - `the_alchemiser/orchestration/portfolio_orchestrator.py`
  - `the_alchemiser/orchestration/signal_orchestrator.py`
  - `the_alchemiser/orchestration/trading_orchestrator.py`
  - `the_alchemiser/portfolio_v2/adapters/alpaca_data_adapter.py`
  - `the_alchemiser/portfolio_v2/core/planner.py`
  - `the_alchemiser/portfolio_v2/core/portfolio_service.py`
  - `the_alchemiser/portfolio_v2/core/state_reader.py`
  - _(and 2 more)_
- **Unused symbols**: ['AlchemiserLoggerAdapter', 'StructuredFormatter', 'configure_test_logging', 'get_error_id', 'get_request_id', 'get_service_logger', 'log_data_transfer_checkpoint', 'log_trade_event', 'log_trade_expectation_vs_reality', 'set_error_id']

### the_alchemiser.shared.mappers.execution_summary_mapping

- **File**: `the_alchemiser/shared/mappers/execution_summary_mapping.py`
- **Importer count**: 0
- **Confidence**: high
- **Public symbols**: 7
- **Imported symbols**: 0
- **Unused symbols**: 7
- **Unused symbols**: ['allocation_comparison_to_dict', 'dict_to_allocation_summary_dto', 'dict_to_execution_summary_dto', 'dict_to_portfolio_state_dto', 'dict_to_strategy_pnl_summary_dto', 'dict_to_strategy_summary_dto', 'dict_to_trading_summary_dto']

### the_alchemiser.shared.mappers.market_data_mappers

- **File**: `the_alchemiser/shared/mappers/market_data_mappers.py`
- **Importer count**: 0
- **Confidence**: high
- **Public symbols**: 2
- **Imported symbols**: 0
- **Unused symbols**: 2
- **Unused symbols**: ['bars_to_domain', 'quote_to_domain']

### the_alchemiser.shared.math.asset_info

- **File**: `the_alchemiser/shared/math/asset_info.py`
- **Importer count**: 0
- **Confidence**: high
- **Public symbols**: 3
- **Imported symbols**: 0
- **Unused symbols**: 3
- **Unused symbols**: ['AssetType', 'FractionabilityDetector', 'fractionability_detector']

### the_alchemiser.shared.math.math_utils

- **File**: `the_alchemiser/shared/math/math_utils.py`
- **Importer count**: 1
- **Confidence**: high
- **Public symbols**: 8
- **Imported symbols**: 2
- **Unused symbols**: 6
- **Importers** (1):
  - `the_alchemiser/strategy_v2/engines/klm/engine.py`
- **Unused symbols**: ['calculate_ensemble_score', 'calculate_moving_average', 'calculate_percentage_change', 'calculate_rolling_metric', 'normalize_to_range', 'safe_division']

### the_alchemiser.shared.math.num

- **File**: `the_alchemiser/shared/math/num.py`
- **Importer count**: 0
- **Confidence**: high
- **Public symbols**: 3
- **Imported symbols**: 0
- **Unused symbols**: 3
- **Unused symbols**: ['Number', 'SequenceLike', 'floats_equal']

### the_alchemiser.shared.math.trading_math

- **File**: `the_alchemiser/shared/math/trading_math.py`
- **Importer count**: 0
- **Confidence**: high
- **Public symbols**: 6
- **Imported symbols**: 0
- **Unused symbols**: 6
- **Unused symbols**: ['calculate_allocation_discrepancy', 'calculate_dynamic_limit_price', 'calculate_dynamic_limit_price_with_symbol', 'calculate_position_size', 'calculate_rebalance_amounts', 'calculate_slippage_buffer']

### the_alchemiser.shared.notifications.client

- **File**: `the_alchemiser/shared/notifications/client.py`
- **Importer count**: 0
- **Confidence**: high
- **Public symbols**: 2
- **Imported symbols**: 0
- **Unused symbols**: 2
- **Unused symbols**: ['EmailClient', 'send_email_notification']

### the_alchemiser.shared.notifications.config

- **File**: `the_alchemiser/shared/notifications/config.py`
- **Importer count**: 0
- **Confidence**: high
- **Public symbols**: 3
- **Imported symbols**: 0
- **Unused symbols**: 3
- **Unused symbols**: ['EmailConfig', 'get_email_config', 'is_neutral_mode_enabled']

### the_alchemiser.shared.notifications.email_utils

- **File**: `the_alchemiser/shared/notifications/email_utils.py`
- **Importer count**: 1
- **Confidence**: high
- **Public symbols**: 12
- **Imported symbols**: 2
- **Unused symbols**: 10
- **Importers** (1):
  - `the_alchemiser/orchestration/trading_orchestrator.py`
- **Unused symbols**: ['BaseEmailTemplate', 'EmailClient', 'EmailTemplates', 'PerformanceBuilder', 'PortfolioBuilder', 'SignalsBuilder', 'build_multi_strategy_email_html', 'build_trading_report_html', 'get_email_config', 'is_neutral_mode_enabled']

### the_alchemiser.shared.notifications.templates.base

- **File**: `the_alchemiser/shared/notifications/templates/base.py`
- **Importer count**: 0
- **Confidence**: high
- **Public symbols**: 1
- **Imported symbols**: 0
- **Unused symbols**: 1
- **Unused symbols**: ['BaseEmailTemplate']

### the_alchemiser.shared.notifications.templates.email_facade

- **File**: `the_alchemiser/shared/notifications/templates/email_facade.py`
- **Importer count**: 0
- **Confidence**: high
- **Public symbols**: 4
- **Imported symbols**: 0
- **Unused symbols**: 4
- **Unused symbols**: ['EmailTemplates', 'build_error_email_html', 'build_multi_strategy_email_html', 'build_trading_report_html']

### the_alchemiser.shared.notifications.templates.multi_strategy

- **File**: `the_alchemiser/shared/notifications/templates/multi_strategy.py`
- **Importer count**: 0
- **Confidence**: high
- **Public symbols**: 1
- **Imported symbols**: 0
- **Unused symbols**: 1
- **Unused symbols**: ['MultiStrategyReportBuilder']

### the_alchemiser.shared.notifications.templates.performance

- **File**: `the_alchemiser/shared/notifications/templates/performance.py`
- **Importer count**: 0
- **Confidence**: high
- **Public symbols**: 1
- **Imported symbols**: 0
- **Unused symbols**: 1
- **Unused symbols**: ['PerformanceBuilder']

### the_alchemiser.shared.notifications.templates.portfolio

- **File**: `the_alchemiser/shared/notifications/templates/portfolio.py`
- **Importer count**: 0
- **Confidence**: high
- **Public symbols**: 3
- **Imported symbols**: 0
- **Unused symbols**: 3
- **Unused symbols**: ['ExecutionLike', 'ExecutionSummaryLike', 'PortfolioBuilder']

### the_alchemiser.shared.notifications.templates.signals

- **File**: `the_alchemiser/shared/notifications/templates/signals.py`
- **Importer count**: 0
- **Confidence**: high
- **Public symbols**: 1
- **Imported symbols**: 0
- **Unused symbols**: 1
- **Unused symbols**: ['SignalsBuilder']

### the_alchemiser.shared.persistence.factory

- **File**: `the_alchemiser/shared/persistence/factory.py`
- **Importer count**: 0
- **Confidence**: high
- **Public symbols**: 3
- **Imported symbols**: 0
- **Unused symbols**: 3
- **Unused symbols**: ['create_persistence_handler', 'detect_paper_trading_from_environment', 'get_default_persistence_handler']

### the_alchemiser.shared.persistence.local_handler

- **File**: `the_alchemiser/shared/persistence/local_handler.py`
- **Importer count**: 0
- **Confidence**: high
- **Public symbols**: 1
- **Imported symbols**: 0
- **Unused symbols**: 1
- **Unused symbols**: ['LocalFileHandler']

### the_alchemiser.shared.persistence.s3_handler

- **File**: `the_alchemiser/shared/persistence/s3_handler.py`
- **Importer count**: 0
- **Confidence**: high
- **Public symbols**: 1
- **Imported symbols**: 0
- **Unused symbols**: 1
- **Unused symbols**: ['S3Handler']

### the_alchemiser.shared.protocols.alpaca

- **File**: `the_alchemiser/shared/protocols/alpaca.py`
- **Importer count**: 0
- **Confidence**: high
- **Public symbols**: 2
- **Imported symbols**: 0
- **Unused symbols**: 2
- **Unused symbols**: ['AlpacaOrderObject', 'AlpacaOrderProtocol']

### the_alchemiser.shared.protocols.asset_metadata

- **File**: `the_alchemiser/shared/protocols/asset_metadata.py`
- **Importer count**: 0
- **Confidence**: high
- **Public symbols**: 1
- **Imported symbols**: 0
- **Unused symbols**: 1
- **Unused symbols**: ['AssetMetadataProvider']

### the_alchemiser.shared.protocols.order_like

- **File**: `the_alchemiser/shared/protocols/order_like.py`
- **Importer count**: 0
- **Confidence**: high
- **Public symbols**: 2
- **Imported symbols**: 0
- **Unused symbols**: 2
- **Unused symbols**: ['OrderLikeProtocol', 'PositionLikeProtocol']

### the_alchemiser.shared.protocols.persistence

- **File**: `the_alchemiser/shared/protocols/persistence.py`
- **Importer count**: 0
- **Confidence**: high
- **Public symbols**: 1
- **Imported symbols**: 0
- **Unused symbols**: 1
- **Unused symbols**: ['PersistenceHandler']

### the_alchemiser.shared.protocols.repository

- **File**: `the_alchemiser/shared/protocols/repository.py`
- **Importer count**: 0
- **Confidence**: high
- **Public symbols**: 3
- **Imported symbols**: 0
- **Unused symbols**: 3
- **Unused symbols**: ['AccountRepository', 'MarketDataRepository', 'TradingRepository']

### the_alchemiser.shared.protocols.strategy_tracking

- **File**: `the_alchemiser/shared/protocols/strategy_tracking.py`
- **Importer count**: 0
- **Confidence**: high
- **Public symbols**: 4
- **Imported symbols**: 0
- **Unused symbols**: 4
- **Unused symbols**: ['StrategyOrderProtocol', 'StrategyOrderTrackerProtocol', 'StrategyPnLSummaryProtocol', 'StrategyPositionProtocol']

### the_alchemiser.shared.reporting.reporting

- **File**: `the_alchemiser/shared/reporting/reporting.py`
- **Importer count**: 0
- **Confidence**: high
- **Public symbols**: 3
- **Imported symbols**: 0
- **Unused symbols**: 3
- **Unused symbols**: ['build_portfolio_state_data', 'create_execution_summary', 'save_dashboard_data']

### the_alchemiser.shared.schemas.accounts

- **File**: `the_alchemiser/shared/schemas/accounts.py`
- **Importer count**: 0
- **Confidence**: high
- **Public symbols**: 14
- **Imported symbols**: 0
- **Unused symbols**: 14
- **Unused symbols**: ['AccountMetrics', 'AccountMetricsDTO', 'AccountSummary', 'AccountSummaryDTO', 'BuyingPowerDTO', 'BuyingPowerResult', 'EnrichedAccountSummaryDTO', 'EnrichedAccountSummaryView', 'PortfolioAllocationDTO', 'PortfolioAllocationResult', 'RiskMetricsDTO', 'RiskMetricsResult', 'TradeEligibilityDTO', 'TradeEligibilityResult']

### the_alchemiser.shared.schemas.base

- **File**: `the_alchemiser/shared/schemas/base.py`
- **Importer count**: 0
- **Confidence**: high
- **Public symbols**: 2
- **Imported symbols**: 0
- **Unused symbols**: 2
- **Unused symbols**: ['Result', 'ResultDTO']

### the_alchemiser.shared.schemas.cli

- **File**: `the_alchemiser/shared/schemas/cli.py`
- **Importer count**: 0
- **Confidence**: high
- **Public symbols**: 6
- **Imported symbols**: 0
- **Unused symbols**: 6
- **Unused symbols**: ['CLIAccountDisplay', 'CLICommandResult', 'CLIOptions', 'CLIOrderDisplay', 'CLIPortfolioData', 'CLISignalData']

### the_alchemiser.shared.schemas.common

- **File**: `the_alchemiser/shared/schemas/common.py`
- **Importer count**: 2
- **Confidence**: high
- **Public symbols**: 3
- **Imported symbols**: 1
- **Unused symbols**: 2
- **Importers** (2):
  - `the_alchemiser/orchestration/portfolio_orchestrator.py`
  - `the_alchemiser/orchestration/trading_orchestrator.py`
- **Unused symbols**: ['MultiStrategyExecutionResultDTO', 'MultiStrategySummaryDTO']

### the_alchemiser.shared.schemas.enriched_data

- **File**: `the_alchemiser/shared/schemas/enriched_data.py`
- **Importer count**: 0
- **Confidence**: high
- **Public symbols**: 8
- **Imported symbols**: 0
- **Unused symbols**: 8
- **Unused symbols**: ['EnrichedOrderDTO', 'EnrichedOrderView', 'EnrichedPositionDTO', 'EnrichedPositionView', 'EnrichedPositionsDTO', 'EnrichedPositionsView', 'OpenOrdersDTO', 'OpenOrdersView']

### the_alchemiser.shared.schemas.errors

- **File**: `the_alchemiser/shared/schemas/errors.py`
- **Importer count**: 0
- **Confidence**: high
- **Public symbols**: 5
- **Imported symbols**: 0
- **Unused symbols**: 5
- **Unused symbols**: ['ErrorContextData', 'ErrorDetailInfo', 'ErrorNotificationData', 'ErrorReportSummary', 'ErrorSummaryData']

### the_alchemiser.shared.schemas.execution_summary

- **File**: `the_alchemiser/shared/schemas/execution_summary.py`
- **Importer count**: 0
- **Confidence**: high
- **Public symbols**: 12
- **Imported symbols**: 0
- **Unused symbols**: 12
- **Unused symbols**: ['AllocationSummary', 'AllocationSummaryDTO', 'ExecutionSummary', 'ExecutionSummaryDTO', 'PortfolioState', 'PortfolioStateDTO', 'StrategyPnLSummary', 'StrategyPnLSummaryDTO', 'StrategySummary', 'StrategySummaryDTO', 'TradingSummary', 'TradingSummaryDTO']

### the_alchemiser.shared.schemas.market_data

- **File**: `the_alchemiser/shared/schemas/market_data.py`
- **Importer count**: 0
- **Confidence**: high
- **Public symbols**: 10
- **Imported symbols**: 0
- **Unused symbols**: 10
- **Unused symbols**: ['MarketStatusDTO', 'MarketStatusResult', 'MultiSymbolQuotesDTO', 'MultiSymbolQuotesResult', 'PriceDTO', 'PriceHistoryDTO', 'PriceHistoryResult', 'PriceResult', 'SpreadAnalysisDTO', 'SpreadAnalysisResult']

### the_alchemiser.shared.schemas.operations

- **File**: `the_alchemiser/shared/schemas/operations.py`
- **Importer count**: 0
- **Confidence**: high
- **Public symbols**: 6
- **Imported symbols**: 0
- **Unused symbols**: 6
- **Unused symbols**: ['OperationResult', 'OperationResultDTO', 'OrderCancellationDTO', 'OrderCancellationResult', 'OrderStatusDTO', 'OrderStatusResult']

### the_alchemiser.shared.schemas.reporting

- **File**: `the_alchemiser/shared/schemas/reporting.py`
- **Importer count**: 0
- **Confidence**: high
- **Public symbols**: 7
- **Imported symbols**: 0
- **Unused symbols**: 7
- **Unused symbols**: ['BacktestResult', 'DashboardMetrics', 'EmailCredentials', 'EmailReportData', 'EmailSummary', 'PerformanceMetrics', 'ReportingData']

### the_alchemiser.shared.services.market_data_service

- **File**: `the_alchemiser/shared/services/market_data_service.py`
- **Importer count**: 0
- **Confidence**: high
- **Public symbols**: 1
- **Imported symbols**: 0
- **Unused symbols**: 1
- **Unused symbols**: ['MarketDataService']

### the_alchemiser.shared.services.real_time_pricing

- **File**: `the_alchemiser/shared/services/real_time_pricing.py`
- **Importer count**: 0
- **Confidence**: high
- **Public symbols**: 3
- **Imported symbols**: 0
- **Unused symbols**: 3
- **Unused symbols**: ['RealTimePricingManager', 'RealTimePricingService', 'RealTimeQuote']

### the_alchemiser.shared.services.tick_size_service

- **File**: `the_alchemiser/shared/services/tick_size_service.py`
- **Importer count**: 0
- **Confidence**: high
- **Public symbols**: 2
- **Imported symbols**: 0
- **Unused symbols**: 2
- **Unused symbols**: ['DynamicTickSizeService', 'TickSizeService']

### the_alchemiser.shared.types.account

- **File**: `the_alchemiser/shared/types/account.py`
- **Importer count**: 0
- **Confidence**: high
- **Public symbols**: 2
- **Imported symbols**: 0
- **Unused symbols**: 2
- **Unused symbols**: ['AccountModel', 'PortfolioHistoryModel']

### the_alchemiser.shared.types.broker_enums

- **File**: `the_alchemiser/shared/types/broker_enums.py`
- **Importer count**: 0
- **Confidence**: high
- **Public symbols**: 4
- **Imported symbols**: 0
- **Unused symbols**: 4
- **Unused symbols**: ['BrokerOrderSide', 'BrokerTimeInForce', 'OrderSideType', 'TimeInForceType']

### the_alchemiser.shared.types.exceptions

- **File**: `the_alchemiser/shared/types/exceptions.py`
- **Importer count**: 9
- **Confidence**: high
- **Public symbols**: 28
- **Imported symbols**: 6
- **Unused symbols**: 22
- **Importers** (9):
  - `the_alchemiser/lambda_handler.py`
  - `the_alchemiser/main.py`
  - `the_alchemiser/orchestration/signal_orchestrator.py`
  - `the_alchemiser/orchestration/strategy_orchestrator.py`
  - `the_alchemiser/orchestration/trading_orchestrator.py`
  - `the_alchemiser/portfolio_v2/core/planner.py`
  - `the_alchemiser/portfolio_v2/core/portfolio_service.py`
  - `the_alchemiser/strategy_v2/engines/klm/engine.py`
  - `the_alchemiser/strategy_v2/engines/nuclear/engine.py`
- **Unused symbols**: ['AlchemiserError', 'BuyingPowerError', 'DatabaseError', 'EnvironmentError', 'FileOperationError', 'IndicatorCalculationError', 'InsufficientFundsError', 'LoggingError', 'MarketClosedError', 'MarketDataError', 'OrderExecutionError', 'OrderPlacementError', 'OrderTimeoutError', 'PositionValidationError', 'RateLimitError', 'S3OperationError', 'SecurityError', 'SpreadAnalysisError', 'StrategyValidationError', 'StreamingError', 'ValidationError', 'WebSocketError']

### the_alchemiser.shared.types.market_data

- **File**: `the_alchemiser/shared/types/market_data.py`
- **Importer count**: 4
- **Confidence**: high
- **Public symbols**: 5
- **Imported symbols**: 1
- **Unused symbols**: 4
- **Importers** (4):
  - `the_alchemiser/portfolio_v2/adapters/alpaca_data_adapter.py`
  - `the_alchemiser/strategy_v2/engines/klm/engine.py`
  - `the_alchemiser/strategy_v2/engines/nuclear/engine.py`
  - `the_alchemiser/strategy_v2/engines/tecl/engine.py`
- **Unused symbols**: ['BarModel', 'PriceDataModel', 'QuoteModel', 'dataframe_to_bars']

### the_alchemiser.shared.types.market_data_port

- **File**: `the_alchemiser/shared/types/market_data_port.py`
- **Importer count**: 4
- **Confidence**: high
- **Public symbols**: 1
- **Imported symbols**: 1
- **Unused symbols**: 0
- **Importers** (4):
  - `the_alchemiser/orchestration/strategy_orchestrator.py`
  - `the_alchemiser/strategy_v2/engines/klm/engine.py`
  - `the_alchemiser/strategy_v2/engines/nuclear/engine.py`
  - `the_alchemiser/strategy_v2/engines/tecl/engine.py`

### the_alchemiser.shared.types.money

- **File**: `the_alchemiser/shared/types/money.py`
- **Importer count**: 0
- **Confidence**: high
- **Public symbols**: 1
- **Imported symbols**: 0
- **Unused symbols**: 1
- **Unused symbols**: ['Money']

### the_alchemiser.shared.types.percentage

- **File**: `the_alchemiser/shared/types/percentage.py`
- **Importer count**: 3
- **Confidence**: high
- **Public symbols**: 1
- **Imported symbols**: 1
- **Unused symbols**: 0
- **Importers** (3):
  - `the_alchemiser/strategy_v2/engines/klm/engine.py`
  - `the_alchemiser/strategy_v2/engines/nuclear/engine.py`
  - `the_alchemiser/strategy_v2/engines/tecl/engine.py`

### the_alchemiser.shared.types.quantity

- **File**: `the_alchemiser/shared/types/quantity.py`
- **Importer count**: 0
- **Confidence**: high
- **Public symbols**: 1
- **Imported symbols**: 0
- **Unused symbols**: 1
- **Unused symbols**: ['Quantity']

### the_alchemiser.shared.types.quote

- **File**: `the_alchemiser/shared/types/quote.py`
- **Importer count**: 0
- **Confidence**: high
- **Public symbols**: 1
- **Imported symbols**: 0
- **Unused symbols**: 1
- **Unused symbols**: ['QuoteModel']

### the_alchemiser.shared.types.strategy_protocol

- **File**: `the_alchemiser/shared/types/strategy_protocol.py`
- **Importer count**: 4
- **Confidence**: high
- **Public symbols**: 1
- **Imported symbols**: 1
- **Unused symbols**: 0
- **Importers** (4):
  - `the_alchemiser/orchestration/strategy_orchestrator.py`
  - `the_alchemiser/strategy_v2/engines/klm/engine.py`
  - `the_alchemiser/strategy_v2/engines/nuclear/engine.py`
  - `the_alchemiser/strategy_v2/engines/tecl/engine.py`

### the_alchemiser.shared.types.strategy_registry

- **File**: `the_alchemiser/shared/types/strategy_registry.py`
- **Importer count**: 1
- **Confidence**: high
- **Public symbols**: 1
- **Imported symbols**: 1
- **Unused symbols**: 0
- **Importers** (1):
  - `the_alchemiser/orchestration/strategy_orchestrator.py`

### the_alchemiser.shared.types.strategy_types

- **File**: `the_alchemiser/shared/types/strategy_types.py`
- **Importer count**: 1
- **Confidence**: high
- **Public symbols**: 1
- **Imported symbols**: 1
- **Unused symbols**: 0
- **Importers** (1):
  - `the_alchemiser/orchestration/strategy_orchestrator.py`

### the_alchemiser.shared.types.strategy_value_objects

- **File**: `the_alchemiser/shared/types/strategy_value_objects.py`
- **Importer count**: 4
- **Confidence**: high
- **Public symbols**: 2
- **Imported symbols**: 2
- **Unused symbols**: 0
- **Importers** (4):
  - `the_alchemiser/orchestration/strategy_orchestrator.py`
  - `the_alchemiser/strategy_v2/engines/klm/engine.py`
  - `the_alchemiser/strategy_v2/engines/nuclear/engine.py`
  - `the_alchemiser/strategy_v2/engines/tecl/engine.py`

### the_alchemiser.shared.types.time_in_force

- **File**: `the_alchemiser/shared/types/time_in_force.py`
- **Importer count**: 0
- **Confidence**: high
- **Public symbols**: 1
- **Imported symbols**: 0
- **Unused symbols**: 1
- **Unused symbols**: ['TimeInForce']

### the_alchemiser.shared.types.trading_errors

- **File**: `the_alchemiser/shared/types/trading_errors.py`
- **Importer count**: 0
- **Confidence**: high
- **Public symbols**: 2
- **Imported symbols**: 0
- **Unused symbols**: 2
- **Unused symbols**: ['OrderError', 'classify_exception']

### the_alchemiser.shared.utils.common

- **File**: `the_alchemiser/shared/utils/common.py`
- **Importer count**: 11
- **Confidence**: high
- **Public symbols**: 1
- **Imported symbols**: 1
- **Unused symbols**: 0
- **Importers** (11):
  - `the_alchemiser/strategy_v2/engines/klm/base_variant.py`
  - `the_alchemiser/strategy_v2/engines/klm/engine.py`
  - `the_alchemiser/strategy_v2/engines/klm/variants/variant_1280_26.py`
  - `the_alchemiser/strategy_v2/engines/klm/variants/variant_410_38.py`
  - `the_alchemiser/strategy_v2/engines/klm/variants/variant_506_38.py`
  - `the_alchemiser/strategy_v2/engines/klm/variants/variant_520_22.py`
  - `the_alchemiser/strategy_v2/engines/klm/variants/variant_530_18.py`
  - `the_alchemiser/strategy_v2/engines/klm/variants/variant_830_21.py`
  - `the_alchemiser/strategy_v2/engines/klm/variants/variant_nova.py`
  - `the_alchemiser/strategy_v2/engines/tecl/engine.py`
  - _(and 1 more)_

### the_alchemiser.shared.utils.config

- **File**: `the_alchemiser/shared/utils/config.py`
- **Importer count**: 0
- **Confidence**: high
- **Public symbols**: 3
- **Imported symbols**: 0
- **Unused symbols**: 3
- **Unused symbols**: ['ModularConfig', 'get_global_config', 'load_module_config']

### the_alchemiser.shared.utils.context

- **File**: `the_alchemiser/shared/utils/context.py`
- **Importer count**: 0
- **Confidence**: high
- **Public symbols**: 2
- **Imported symbols**: 0
- **Unused symbols**: 2
- **Unused symbols**: ['ErrorContextData', 'create_error_context']

### the_alchemiser.shared.utils.decorators

- **File**: `the_alchemiser/shared/utils/decorators.py`
- **Importer count**: 0
- **Confidence**: high
- **Public symbols**: 6
- **Imported symbols**: 0
- **Unused symbols**: 6
- **Unused symbols**: ['F', 'translate_config_errors', 'translate_market_data_errors', 'translate_service_errors', 'translate_streaming_errors', 'translate_trading_errors']

### the_alchemiser.shared.utils.dto_conversion

- **File**: `the_alchemiser/shared/utils/dto_conversion.py`
- **Importer count**: 0
- **Confidence**: high
- **Public symbols**: 8
- **Imported symbols**: 0
- **Unused symbols**: 8
- **Unused symbols**: ['convert_datetime_fields_from_dict', 'convert_datetime_fields_to_dict', 'convert_decimal_fields_from_dict', 'convert_decimal_fields_to_dict', 'convert_nested_order_data', 'convert_nested_rebalance_item_data', 'convert_string_to_datetime', 'convert_string_to_decimal']

### the_alchemiser.shared.utils.error_reporter

- **File**: `the_alchemiser/shared/utils/error_reporter.py`
- **Importer count**: 0
- **Confidence**: high
- **Public symbols**: 4
- **Imported symbols**: 0
- **Unused symbols**: 4
- **Unused symbols**: ['ErrorReporter', 'get_error_reporter', 'logger', 'report_error_globally']

### the_alchemiser.shared.utils.portfolio_calculations

- **File**: `the_alchemiser/shared/utils/portfolio_calculations.py`
- **Importer count**: 1
- **Confidence**: high
- **Public symbols**: 1
- **Imported symbols**: 1
- **Unused symbols**: 0
- **Importers** (1):
  - `the_alchemiser/orchestration/portfolio_orchestrator.py`

### the_alchemiser.shared.utils.price_discovery_utils

- **File**: `the_alchemiser/shared/utils/price_discovery_utils.py`
- **Importer count**: 0
- **Confidence**: high
- **Public symbols**: 7
- **Imported symbols**: 0
- **Unused symbols**: 7
- **Unused symbols**: ['PriceProvider', 'QuoteProvider', 'calculate_midpoint_price', 'get_current_price_as_decimal', 'get_current_price_from_quote', 'get_current_price_with_fallback', 'logger']

### the_alchemiser.shared.utils.serialization

- **File**: `the_alchemiser/shared/utils/serialization.py`
- **Importer count**: 0
- **Confidence**: high
- **Public symbols**: 2
- **Imported symbols**: 0
- **Unused symbols**: 2
- **Unused symbols**: ['ensure_serialized_dict', 'to_serializable']

### the_alchemiser.shared.utils.service_factory

- **File**: `the_alchemiser/shared/utils/service_factory.py`
- **Importer count**: 1
- **Confidence**: high
- **Public symbols**: 1
- **Imported symbols**: 1
- **Unused symbols**: 0
- **Importers** (1):
  - `the_alchemiser/main.py`

### the_alchemiser.shared.utils.strategy_utils

- **File**: `the_alchemiser/shared/utils/strategy_utils.py`
- **Importer count**: 1
- **Confidence**: high
- **Public symbols**: 1
- **Imported symbols**: 1
- **Unused symbols**: 0
- **Importers** (1):
  - `the_alchemiser/orchestration/signal_orchestrator.py`

### the_alchemiser.shared.utils.timezone_utils

- **File**: `the_alchemiser/shared/utils/timezone_utils.py`
- **Importer count**: 0
- **Confidence**: high
- **Public symbols**: 3
- **Imported symbols**: 0
- **Unused symbols**: 3
- **Unused symbols**: ['ensure_timezone_aware', 'normalize_timestamp_to_utc', 'to_iso_string']

### the_alchemiser.shared.utils.validation_utils

- **File**: `the_alchemiser/shared/utils/validation_utils.py`
- **Importer count**: 0
- **Confidence**: high
- **Public symbols**: 10
- **Imported symbols**: 0
- **Unused symbols**: 10
- **Unused symbols**: ['ALERT_SEVERITIES', 'CONFIDENCE_RANGE', 'ORDER_SIDES', 'ORDER_TYPES', 'PERCENTAGE_RANGE', 'SIGNAL_ACTIONS', 'validate_decimal_range', 'validate_enum_value', 'validate_non_negative_integer', 'validate_order_limit_price']

### the_alchemiser.shared.value_objects.core_types

- **File**: `the_alchemiser/shared/value_objects/core_types.py`
- **Importer count**: 11
- **Confidence**: high
- **Public symbols**: 22
- **Imported symbols**: 1
- **Unused symbols**: 21
- **Importers** (11):
  - `the_alchemiser/strategy_v2/engines/klm/base_variant.py`
  - `the_alchemiser/strategy_v2/engines/klm/engine.py`
  - `the_alchemiser/strategy_v2/engines/klm/variants/variant_1280_26.py`
  - `the_alchemiser/strategy_v2/engines/klm/variants/variant_410_38.py`
  - `the_alchemiser/strategy_v2/engines/klm/variants/variant_506_38.py`
  - `the_alchemiser/strategy_v2/engines/klm/variants/variant_520_22.py`
  - `the_alchemiser/strategy_v2/engines/klm/variants/variant_530_18.py`
  - `the_alchemiser/strategy_v2/engines/klm/variants/variant_830_21.py`
  - `the_alchemiser/strategy_v2/engines/klm/variants/variant_nova.py`
  - `the_alchemiser/strategy_v2/indicators/indicators.py`
  - _(and 1 more)_
- **Unused symbols**: ['AccountInfo', 'ClosedPositionData', 'DataProviderResult', 'EnrichedAccountInfo', 'ErrorContext', 'IndicatorData', 'KLMVariantResult', 'MarketDataPoint', 'OrderDetails', 'OrderStatusLiteral', 'PortfolioHistoryData', 'PortfolioSnapshot', 'PositionInfo', 'PositionsDict', 'PriceData', 'QuoteData', 'StrategyPnLSummary', 'StrategyPositionData', 'StrategySignal', 'StrategySignalBase', 'TradeAnalysis']

### the_alchemiser.shared.value_objects.identifier

- **File**: `the_alchemiser/shared/value_objects/identifier.py`
- **Importer count**: 0
- **Confidence**: high
- **Public symbols**: 2
- **Imported symbols**: 0
- **Unused symbols**: 2
- **Unused symbols**: ['Identifier', 'T_contra']

### the_alchemiser.shared.value_objects.symbol

- **File**: `the_alchemiser/shared/value_objects/symbol.py`
- **Importer count**: 4
- **Confidence**: high
- **Public symbols**: 1
- **Imported symbols**: 1
- **Unused symbols**: 0
- **Importers** (4):
  - `the_alchemiser/orchestration/strategy_orchestrator.py`
  - `the_alchemiser/strategy_v2/engines/klm/engine.py`
  - `the_alchemiser/strategy_v2/engines/nuclear/engine.py`
  - `the_alchemiser/strategy_v2/engines/tecl/engine.py`

## Re-export Analysis

Found 104 re-exported symbols.

- `the_alchemiser.shared.annotations` → `the_alchemiser.shared.__future__`
- `the_alchemiser.shared.brokers.AlpacaManager` → `the_alchemiser.shared.brokers.alpaca_manager`
- `the_alchemiser.shared.brokers.annotations` → `the_alchemiser.shared.brokers.__future__`
- `the_alchemiser.shared.brokers.create_alpaca_manager` → `the_alchemiser.shared.brokers.alpaca_manager`
- `the_alchemiser.shared.config.Settings` → `the_alchemiser.shared.config.config`
- `the_alchemiser.shared.config.load_settings` → `the_alchemiser.shared.config.config`
- `the_alchemiser.shared.dto.ExecutedOrderDTO` → `the_alchemiser.shared.dto.the_alchemiser.shared.dto.execution_report_dto`
- `the_alchemiser.shared.dto.ExecutionReportDTO` → `the_alchemiser.shared.dto.the_alchemiser.shared.dto.execution_report_dto`
- `the_alchemiser.shared.dto.LambdaEventDTO` → `the_alchemiser.shared.dto.the_alchemiser.shared.dto.lambda_event_dto`
- `the_alchemiser.shared.dto.MarketDataDTO` → `the_alchemiser.shared.dto.the_alchemiser.shared.dto.order_request_dto`
- `the_alchemiser.shared.dto.OrderRequestDTO` → `the_alchemiser.shared.dto.the_alchemiser.shared.dto.order_request_dto`
- `the_alchemiser.shared.dto.PortfolioMetricsDTO` → `the_alchemiser.shared.dto.the_alchemiser.shared.dto.portfolio_state_dto`
- `the_alchemiser.shared.dto.PortfolioStateDTO` → `the_alchemiser.shared.dto.the_alchemiser.shared.dto.portfolio_state_dto`
- `the_alchemiser.shared.dto.PositionDTO` → `the_alchemiser.shared.dto.the_alchemiser.shared.dto.portfolio_state_dto`
- `the_alchemiser.shared.dto.RebalancePlanDTO` → `the_alchemiser.shared.dto.the_alchemiser.shared.dto.rebalance_plan_dto`
- `the_alchemiser.shared.dto.RebalancePlanItemDTO` → `the_alchemiser.shared.dto.the_alchemiser.shared.dto.rebalance_plan_dto`
- `the_alchemiser.shared.dto.StrategyAllocationDTO` → `the_alchemiser.shared.dto.the_alchemiser.shared.dto.strategy_allocation_dto`
- `the_alchemiser.shared.dto.StrategySignalDTO` → `the_alchemiser.shared.dto.the_alchemiser.shared.dto.signal_dto`
- `the_alchemiser.shared.dto.annotations` → `the_alchemiser.shared.dto.__future__`
- `the_alchemiser.shared.events.AllocationComparisonCompleted` → `the_alchemiser.shared.events.schemas`
- _(and 84 more)_

