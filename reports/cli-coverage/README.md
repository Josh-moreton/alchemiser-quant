# CLI Coverage Report

## Entry Points
- `alchemiser` → `the_alchemiser.interface.cli.cli:app`

## Execution Matrix
- **signal_default**: `cli signal` – Baseline run with default options
- **trade_default**: `cli trade` – Baseline run with default options
- **trade_live**: `cli trade --live --force` – Exercise boolean flag --live
- **trade_ignore_market_hours**: `cli trade --ignore-market-hours` – Exercise boolean flag --ignore-market-hours
- **status_default**: `cli status` – Baseline run with default options
- **status_live**: `cli status --live` – Exercise boolean flag --live
- **deploy_default**: `cli deploy` – Baseline run with default options
- **version_default**: `cli version` – Baseline run with default options
- **validate-indicators_default**: `cli validate-indicators` – Baseline run with default options
- **validate-indicators_mode_quick**: `cli validate-indicators --mode quick` – Test mode quick
- **validate-indicators_mode_full**: `cli validate-indicators --mode full` – Test mode full

## Coverage Summary
Overall coverage: 14.1%
See `coverage_summary.txt` for full details.

## Module Usage
- [Used modules](used_modules.csv)
- [Unused modules](unused_modules.csv)

## Risky gaps
- the_alchemiser/main_original_backup.py
- the_alchemiser/lambda_handler.py
- the_alchemiser/__init__.py
- the_alchemiser/application/order_validation_utils.py
- the_alchemiser/application/smart_pricing_handler.py
- the_alchemiser/application/smart_execution.py
- the_alchemiser/application/portfolio_pnl_utils.py
- the_alchemiser/application/progressive_order_utils.py
- the_alchemiser/application/limit_order_handler.py
- the_alchemiser/application/asset_order_handler.py
- the_alchemiser/application/spread_assessment.py
- the_alchemiser/application/order_validation.py
- the_alchemiser/application/__init__.py
- the_alchemiser/application/alpaca_client.py
- the_alchemiser/container/__init__.py
- the_alchemiser/domain/__init__.py
- the_alchemiser/services/error_recovery.py
- the_alchemiser/services/position_manager.py
- the_alchemiser/services/price_fetching_utils.py
- the_alchemiser/services/error_monitoring.py
- the_alchemiser/services/price_service.py
- the_alchemiser/services/error_reporter.py
- the_alchemiser/services/__init__.py
- the_alchemiser/services/retry_decorator.py
- the_alchemiser/services/error_handling.py
- the_alchemiser/utils/__init__.py
- the_alchemiser/application/portfolio_rebalancer/__init__.py
- the_alchemiser/application/tracking/integration.py
- the_alchemiser/application/tracking/__init__.py
- the_alchemiser/infrastructure/websocket/websocket_order_monitor.py
- the_alchemiser/infrastructure/websocket/__init__.py
- the_alchemiser/infrastructure/websocket/websocket_connection_manager.py
- the_alchemiser/infrastructure/data_providers/unified_data_provider_facade.py
- the_alchemiser/infrastructure/data_providers/real_time_pricing.py
- the_alchemiser/infrastructure/data_providers/__init__.py
- the_alchemiser/infrastructure/logging/__init__.py
- the_alchemiser/infrastructure/validation/__init__.py
- the_alchemiser/infrastructure/alerts/__init__.py
- the_alchemiser/infrastructure/alerts/alert_service.py
- the_alchemiser/infrastructure/secrets/__init__.py
- the_alchemiser/infrastructure/s3/__init__.py
- the_alchemiser/infrastructure/config/__init__.py
- the_alchemiser/domain/registry/__init__.py
- the_alchemiser/domain/math/market_timing_utils.py
- the_alchemiser/domain/math/__init__.py
- the_alchemiser/domain/math/asset_info.py
- the_alchemiser/domain/models/__init__.py
- the_alchemiser/domain/strategies/__init__.py
- the_alchemiser/domain/strategies/klm_trading_bot.py
- the_alchemiser/domain/interfaces/__init__.py
- the_alchemiser/domain/strategies/klm_workers/__init__.py
- the_alchemiser/interface/email/client.py
- the_alchemiser/interface/email/__init__.py
- the_alchemiser/interface/email/config.py
- the_alchemiser/interface/email/email_utils.py
- the_alchemiser/interface/cli/signal_display_utils.py
- the_alchemiser/interface/cli/dashboard_utils.py
- the_alchemiser/interface/cli/trading_executor.py
- the_alchemiser/interface/cli/__init__.py
- the_alchemiser/interface/cli/signal_analyzer.py
- the_alchemiser/interface/email/templates/multi_strategy.py
- the_alchemiser/interface/email/templates/error_report.py
- the_alchemiser/interface/email/templates/base.py
- the_alchemiser/interface/email/templates/portfolio.py
- the_alchemiser/interface/email/templates/trading_report.py
- the_alchemiser/interface/email/templates/signals.py
- the_alchemiser/interface/email/templates/__init__.py
- the_alchemiser/interface/email/templates/performance.py
- the_alchemiser/services/enhanced/__init__.py

## Next actions
- Review unused production modules for relevance or removal.
- Expand tests to cover critical paths.
