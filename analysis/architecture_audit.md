# Architecture Audit Report

Date: 2025-08-12

## Executive Summary

- Automated static scan of repository produced per-file assessment.

- High number of domain files importing infrastructure or IO modules.

- Multiple modules use AlpacaManager outside services, breaching facade pattern.

- Float arithmetic appears in many domain/services modules; use Decimal.

- Error handling gaps detected via bare except blocks in several modules.

## Heatmap

|Layer|High|Medium|Low|
|---|---|---|---|
|domain|25|6|8|
|services|0|21|6|
|infrastructure|0|6|15|
|application|11|1|8|
|interface|0|5|12|
|tests|0|23|14|
|utils|0|0|3|
|unknown|5|5|11|

## Binding Policies

- Domain has no IO and uses Decimal for money
- Application orchestrates use-cases without concrete IO
- Services expose TradingServiceManager facade; AlpacaManager hidden
- Infrastructure implements concrete adapters and AWS/Lambda glue
- Interface is Typer+Rich only; user formatting

## Layer Violations

- the_alchemiser/application/smart_execution.py — import the_alchemiser.infrastructure.data_providers.data_provider at L24
- the_alchemiser/application/smart_pricing_handler.py — import the_alchemiser.infrastructure.logging.logging_utils at L15
- the_alchemiser/application/execution_manager.py — import the_alchemiser.infrastructure.logging.logging_utils at L81
- the_alchemiser/application/execution_manager.py — import the_alchemiser.infrastructure.logging.logging_utils at L96
- the_alchemiser/application/execution_manager.py — import the_alchemiser.infrastructure.logging.logging_utils at L135
- the_alchemiser/application/asset_order_handler.py — import the_alchemiser.infrastructure.logging.logging_utils at L19
- the_alchemiser/application/reporting.py — import the_alchemiser.infrastructure.s3.s3_utils at L67
- the_alchemiser/application/alpaca_client.py — import the_alchemiser.infrastructure.data_providers.data_provider at L62
- the_alchemiser/application/alpaca_client.py — import the_alchemiser.infrastructure.websocket.websocket_connection_manager at L63
- the_alchemiser/application/alpaca_client.py — import the_alchemiser.infrastructure.websocket.websocket_order_monitor at L66
- the_alchemiser/application/trading_engine.py — import the_alchemiser.infrastructure.config at L38
- the_alchemiser/application/trading_engine.py — import the_alchemiser.infrastructure.config at L163
- the_alchemiser/application/trading_engine.py — import the_alchemiser.infrastructure.data_providers.data_provider at L172
- the_alchemiser/application/trading_engine.py — import the_alchemiser.infrastructure.logging.logging_utils at L254
- the_alchemiser/application/trading_engine.py — import the_alchemiser.infrastructure.logging.logging_utils at L284
- the_alchemiser/domain/models/market_data.py — import datetime at L6
- the_alchemiser/domain/models/market_data.py — import pandas at L8
- the_alchemiser/domain/models/order.py — import datetime at L6
- the_alchemiser/domain/math/market_timing_utils.py — import datetime at L10
- the_alchemiser/domain/math/indicator_utils.py — import logging at L6
- ... 57 more

## Facade Breaches

- PHASE3_ARCHITECTURE_DOCUMENTATION.md — uses AlpacaManager
- INCREMENTAL_IMPROVEMENT_PLAN.md — uses AlpacaManager
- PHASE2_INTERFACE_EXTRACTION_COMPLETE.md — uses AlpacaManager
- PHASE1_MIGRATION_COMPLETE.md — uses AlpacaManager
- .github/copilot-instructions.md — uses AlpacaManager
- the_alchemiser/application/smart_execution.py — uses AlpacaManager
- the_alchemiser/application/alpaca_client.py — uses AlpacaManager
- the_alchemiser/domain/math/asset_info.py — uses AlpacaManager
- the_alchemiser/domain/interfaces/trading_repository.py — uses AlpacaManager
- the_alchemiser/domain/interfaces/account_repository.py — uses AlpacaManager
- the_alchemiser/domain/interfaces/market_data_repository.py — uses AlpacaManager

## Decimal & Error Handling Gaps

- the_alchemiser/services/price_fetching_utils.py — float arithmetic
- the_alchemiser/services/error_recovery.py — float arithmetic
- the_alchemiser/services/streaming_service.py — float arithmetic
- the_alchemiser/services/position_manager.py — float arithmetic
- the_alchemiser/services/account_service.py — float arithmetic
- the_alchemiser/services/error_monitoring.py — float arithmetic
- the_alchemiser/services/price_service.py — float arithmetic
- the_alchemiser/services/account_utils.py — float arithmetic
- the_alchemiser/services/market_data_client.py — float arithmetic
- the_alchemiser/services/error_handler.py — float arithmetic
- the_alchemiser/services/retry_decorator.py — float arithmetic
- the_alchemiser/services/enhanced/position_service.py — float arithmetic
- the_alchemiser/services/enhanced/account_service.py — float arithmetic
- the_alchemiser/services/enhanced/trading_service_manager.py — float arithmetic
- the_alchemiser/services/enhanced/market_data_service.py — float arithmetic
- the_alchemiser/services/enhanced/order_service.py — float arithmetic
- the_alchemiser/domain/models/position.py — float arithmetic
- the_alchemiser/domain/models/strategy.py — float arithmetic
- the_alchemiser/domain/models/order.py — float arithmetic
- the_alchemiser/domain/math/market_timing_utils.py — float arithmetic
- ... 15 more decimal issues
- README.md — bare except
- tests/performance/test_performance_benchmarks.py — bare except
- tests/performance/test_load_testing.py — bare except
- tests/performance/test_stress_testing.py — bare except
- the_alchemiser/services/position_manager.py — bare except
- the_alchemiser/application/smart_execution.py — bare except
- the_alchemiser/application/alpaca_client.py — bare except
- the_alchemiser/interface/email/templates/portfolio.py — bare except
- the_alchemiser/interface/email/templates/signals.py — bare except
- the_alchemiser/infrastructure/websocket/websocket_connection_manager.py — bare except
- the_alchemiser/infrastructure/websocket/websocket_order_monitor.py — bare except
- the_alchemiser/infrastructure/data_providers/unified_data_provider_facade.py — bare except
- the_alchemiser/domain/math/math_utils.py — bare except
- the_alchemiser/domain/math/indicators.py — bare except
- the_alchemiser/domain/strategies/klm_workers/variant_830_21.py — bare except
- the_alchemiser/domain/strategies/klm_workers/variant_1200_28.py — bare except
- the_alchemiser/domain/strategies/klm_workers/variant_520_22.py — bare except
- the_alchemiser/domain/strategies/klm_workers/variant_410_38.py — bare except

## File Findings

poetry.lock • poetry module • Placement: ✅ • Single concern: ❌ • Risk: M • Action: Refactor to comply with architecture
package-lock.json • package-lock module • Placement: ✅ • Single concern: ✅ • Risk: L • Action: None
PHASE3_ARCHITECTURE_DOCUMENTATION.md • PHASE3_ARCHITECTURE_DOCUMENTATION module • Placement: ✅ • Single concern: ❌ • Risk: H • Action: Refactor to comply with architecture
template.yaml • template module • Placement: ✅ • Single concern: ✅ • Risk: L • Action: None
INCREMENTAL_IMPROVEMENT_PLAN.md • INCREMENTAL_IMPROVEMENT_PLAN module • Placement: ✅ • Single concern: ❌ • Risk: H • Action: Refactor to comply with architecture
pyproject.toml • pyproject module • Placement: ✅ • Single concern: ✅ • Risk: L • Action: None
ALPACA_ARCHITECTURE_REDESIGN_PLAN.md • ALPACA_ARCHITECTURE_REDESIGN_PLAN module • Placement: ✅ • Single concern: ❌ • Risk: M • Action: Refactor to comply with architecture
PHASE2_INTERFACE_EXTRACTION_COMPLETE.md • PHASE2_INTERFACE_EXTRACTION_COMPLETE module • Placement: ✅ • Single concern: ❌ • Risk: H • Action: Refactor to comply with architecture
.pre-commit-config.yaml • .pre-commit-config module • Placement: ✅ • Single concern: ✅ • Risk: L • Action: None
reacrchitecting.md • reacrchitecting module • Placement: ✅ • Single concern: ✅ • Risk: L • Action: None
package.json • package module • Placement: ✅ • Single concern: ✅ • Risk: L • Action: None
samconfig.toml • samconfig module • Placement: ✅ • Single concern: ✅ • Risk: L • Action: None
PHASE1_MIGRATION_COMPLETE.md • PHASE1_MIGRATION_COMPLETE module • Placement: ✅ • Single concern: ❌ • Risk: H • Action: Refactor to comply with architecture
README.md • README module • Placement: ✅ • Single concern: ❌ • Risk: M • Action: Refactor to comply with architecture
SOC_DUPLICATION_REPORT.md • SOC_DUPLICATION_REPORT module • Placement: ✅ • Single concern: ✅ • Risk: L • Action: None
.github/dependabot.yml • dependabot module • Placement: ✅ • Single concern: ✅ • Risk: L • Action: None
.github/copilot-instructions.md • copilot-instructions module • Placement: ✅ • Single concern: ❌ • Risk: H • Action: Refactor to comply with architecture
tests/__init__.py • The Alchemiser Testing Framework • Placement: ✅ • Single concern: ✅ • Risk: L • Action: None
tests/test_unified_data_provider_baseline.py • test_unified_data_provider_baseline module • Placement: ✅ • Single concern: ❌ • Risk: M • Action: Refactor to comply with architecture
tests/conftest.py • Global test configuration and fixtures for The Alchemiser testing framework. • Placement: ✅ • Single concern: ❌ • Risk: M • Action: Refactor to comply with architecture
tests/README.md • README module • Placement: ✅ • Single concern: ✅ • Risk: L • Action: None
the_alchemiser/__init__.py • The Alchemiser Quantitative Trading System Package. • Placement: ✅ • Single concern: ✅ • Risk: L • Action: None
the_alchemiser/main.py • main module • Placement: ✅ • Single concern: ❌ • Risk: M • Action: Refactor to comply with architecture
the_alchemiser/lambda_handler.py • AWS Lambda Handler for The Alchemiser Quantitative Trading System. • Placement: ✅ • Single concern: ❌ • Risk: M • Action: Refactor to comply with architecture
tests/utils/__init__.py • Testing utilities and mock framework for The Alchemiser. • Placement: ✅ • Single concern: ✅ • Risk: L • Action: None
tests/utils/mocks.py • Mock framework for external dependencies in The Alchemiser. • Placement: ✅ • Single concern: ❌ • Risk: M • Action: Refactor to comply with architecture
tests/utils/test_num.py • test_num module • Placement: ✅ • Single concern: ✅ • Risk: L • Action: None
tests/fixtures/__init__.py • Market data fixtures for testing. • Placement: ✅ • Single concern: ✅ • Risk: L • Action: None
tests/fixtures/market_data.py • Market data fixtures for comprehensive testing scenarios. • Placement: ✅ • Single concern: ❌ • Risk: M • Action: Refactor to comply with architecture
tests/public_api/test_services_public_api.py • test_services_public_api module • Placement: ✅ • Single concern: ✅ • Risk: L • Action: None
tests/unit/test_refactored_services.py • Unit tests for the refactored service-based architecture. • Placement: ✅ • Single concern: ❌ • Risk: M • Action: Refactor to comply with architecture
tests/unit/test_portfolio.py • Unit tests for portfolio management and rebalancing logic. • Placement: ✅ • Single concern: ❌ • Risk: M • Action: Refactor to comply with architecture
tests/unit/test_pytest_mock_integration.py • Example test demonstrating pytest-mock usage. • Placement: ✅ • Single concern: ✅ • Risk: L • Action: None
tests/unit/test_trading_math.py • Unit tests for trading math calculations. • Placement: ✅ • Single concern: ❌ • Risk: M • Action: Refactor to comply with architecture
tests/unit/test_types.py • Unit tests for core type definitions and validation. • Placement: ✅ • Single concern: ❌ • Risk: M • Action: Refactor to comply with architecture
tests/unit/test_indicators.py • Unit tests for technical indicators calculations. • Placement: ✅ • Single concern: ❌ • Risk: M • Action: Refactor to comply with architecture
tests/infrastructure/test_aws_infrastructure.py • Infrastructure Testing • Placement: ✅ • Single concern: ❌ • Risk: M • Action: Refactor to comply with architecture
tests/deployment/test_deployment_validation.py • Production Deployment Testing • Placement: ✅ • Single concern: ❌ • Risk: M • Action: Refactor to comply with architecture
tests/simulation/test_chaos_engineering.py • Chaos Engineering Tests • Placement: ✅ • Single concern: ❌ • Risk: M • Action: Refactor to comply with architecture
tests/simulation/test_market_scenarios.py • Market Scenario Testing • Placement: ✅ • Single concern: ❌ • Risk: M • Action: Refactor to comply with architecture
tests/monitoring/test_production_monitoring.py • Production Monitoring & Metrics Testing • Placement: ✅ • Single concern: ❌ • Risk: M • Action: Refactor to comply with architecture
tests/regression/test_regression_suite.py • Regression Testing Framework • Placement: ✅ • Single concern: ❌ • Risk: M • Action: Refactor to comply with architecture
tests/performance/test_performance_benchmarks.py • Performance & Load Testing • Placement: ✅ • Single concern: ❌ • Risk: M • Action: Refactor to comply with architecture
tests/performance/test_load_testing.py • Load Testing for Trading System • Placement: ✅ • Single concern: ❌ • Risk: M • Action: Refactor to comply with architecture
tests/performance/test_stress_testing.py • Stress Testing & Edge Case Performance • Placement: ✅ • Single concern: ❌ • Risk: M • Action: Refactor to comply with architecture
tests/performance/run_phase5_summary.py • run_phase5_summary module • Placement: ✅ • Single concern: ✅ • Risk: L • Action: None
tests/property/__init__.py • Property-based tests for The Alchemiser trading system. • Placement: ✅ • Single concern: ✅ • Risk: L • Action: None
tests/property/test_trading_properties.py • Property-based tests for trading mathematics and calculations. • Placement: ✅ • Single concern: ❌ • Risk: M • Action: Refactor to comply with architecture
tests/application/test_alpaca_client.py • test_alpaca_client module • Placement: ✅ • Single concern: ✅ • Risk: L • Action: None
tests/application/test_trading_engine.py • test_trading_engine module • Placement: ✅ • Single concern: ❌ • Risk: M • Action: Refactor to comply with architecture
tests/integration/__init__.py • Integration tests package for The Alchemiser. • Placement: ✅ • Single concern: ✅ • Risk: L • Action: None
tests/integration/test_service_integration.py • Integration tests for the refactored service-based architecture. • Placement: ✅ • Single concern: ❌ • Risk: M • Action: Refactor to comply with architecture
tests/integration/test_contract_validation.py • Contract tests for external API integrations. • Placement: ✅ • Single concern: ❌ • Risk: M • Action: Refactor to comply with architecture
tests/integration/test_comprehensive_flows.py • Comprehensive integration tests for The Alchemiser component interactions. • Placement: ✅ • Single concern: ❌ • Risk: M • Action: Refactor to comply with architecture
tests/integration/test_basic_integration.py • Basic integration tests for The Alchemiser trading system. • Placement: ✅ • Single concern: ✅ • Risk: L • Action: None
tests/interface/cli/test_dashboard_utils.py • test_dashboard_utils module • Placement: ✅ • Single concern: ✅ • Risk: L • Action: None
tests/services/enhanced/test_trading_service_manager.py • test_trading_service_manager module • Placement: ✅ • Single concern: ✅ • Risk: L • Action: None
the_alchemiser/utils/__init__.py • Utility functions and helpers for The Alchemiser Quantitative Trading System. • Placement: ✅ • Single concern: ✅ • Risk: L • Action: None
the_alchemiser/utils/common.py • Common constants and enums shared across the trading system. • Placement: ✅ • Single concern: ✅ • Risk: L • Action: None
the_alchemiser/utils/num.py • num module • Placement: ✅ • Single concern: ✅ • Risk: L • Action: None
the_alchemiser/execution/account_service.py • Account and position management helpers. • Placement: ✅ • Single concern: ✅ • Risk: L • Action: None
the_alchemiser/services/price_fetching_utils.py • price_fetching_utils module • Placement: ✅ • Single concern: ❌ • Risk: M • Action: Refactor to comply with architecture
the_alchemiser/services/error_recovery.py • error_recovery module • Placement: ✅ • Single concern: ❌ • Risk: M • Action: Refactor to comply with architecture
the_alchemiser/services/__init__.py • Core services for the trading system. • Placement: ✅ • Single concern: ✅ • Risk: L • Action: None
the_alchemiser/services/streaming_service.py • streaming_service module • Placement: ✅ • Single concern: ❌ • Risk: M • Action: Refactor to comply with architecture
the_alchemiser/services/error_handling.py • Centralized error handling and logging utilities. • Placement: ✅ • Single concern: ❌ • Risk: M • Action: Refactor to comply with architecture
the_alchemiser/services/position_manager.py • position_manager module • Placement: ✅ • Single concern: ❌ • Risk: M • Action: Refactor to comply with architecture
the_alchemiser/services/cache_manager.py • Cache management service with TTL support. • Placement: ✅ • Single concern: ❌ • Risk: M • Action: Refactor to comply with architecture
the_alchemiser/services/error_reporter.py • error_reporter module • Placement: ✅ • Single concern: ❌ • Risk: M • Action: Refactor to comply with architecture
the_alchemiser/services/account_service.py • Account Service • Placement: ✅ • Single concern: ❌ • Risk: M • Action: Refactor to comply with architecture
the_alchemiser/services/exceptions.py • exceptions module • Placement: ✅ • Single concern: ❌ • Risk: M • Action: Refactor to comply with architecture
the_alchemiser/services/error_monitoring.py • error_monitoring module • Placement: ✅ • Single concern: ❌ • Risk: M • Action: Refactor to comply with architecture
the_alchemiser/services/price_service.py • Modern price fetching service. • Placement: ✅ • Single concern: ❌ • Risk: M • Action: Refactor to comply with architecture
the_alchemiser/services/price_utils.py • Price Utilities • Placement: ✅ • Single concern: ✅ • Risk: L • Action: None
the_alchemiser/services/account_utils.py • account_utils module • Placement: ✅ • Single concern: ❌ • Risk: M • Action: Refactor to comply with architecture
the_alchemiser/services/config_service.py • config_service module • Placement: ✅ • Single concern: ✅ • Risk: L • Action: None
the_alchemiser/services/market_data_client.py • market_data_client module • Placement: ✅ • Single concern: ❌ • Risk: M • Action: Refactor to comply with architecture
the_alchemiser/services/secrets_service.py • secrets_service module • Placement: ✅ • Single concern: ✅ • Risk: L • Action: None
the_alchemiser/services/error_handler.py • error_handler module • Placement: ✅ • Single concern: ❌ • Risk: M • Action: Refactor to comply with architecture
the_alchemiser/services/alpaca_manager.py • Centralized Alpaca client management - Phase 1 of incremental improvements. • Placement: ✅ • Single concern: ❌ • Risk: M • Action: Refactor to comply with architecture
the_alchemiser/services/retry_decorator.py • retry_decorator module • Placement: ✅ • Single concern: ❌ • Risk: M • Action: Refactor to comply with architecture
the_alchemiser/services/trading_client_service.py • trading_client_service module • Placement: ✅ • Single concern: ✅ • Risk: L • Action: None
the_alchemiser/domain/__init__.py • Domain Layer • Placement: ✅ • Single concern: ✅ • Risk: L • Action: None
the_alchemiser/domain/types.py • Core type definitions for The Alchemiser trading system. • Placement: ✅ • Single concern: ❌ • Risk: M • Action: Refactor to comply with architecture
the_alchemiser/application/portfolio_pnl_utils.py • portfolio_pnl_utils module • Placement: ✅ • Single concern: ✅ • Risk: L • Action: None
the_alchemiser/application/__init__.py • Execution package for The Alchemiser Quantitative Trading System. • Placement: ✅ • Single concern: ✅ • Risk: L • Action: None
the_alchemiser/application/smart_execution.py • smart_execution module • Placement: ❌ (→ the_alchemiser/services/smart_execution.py) • Single concern: ❌ • Risk: H • Action: Refactor to comply with architecture
the_alchemiser/application/spread_assessment.py • spread_assessment module • Placement: ✅ • Single concern: ✅ • Risk: L • Action: None
the_alchemiser/application/types.py • Type definitions for the execution package. • Placement: ✅ • Single concern: ✅ • Risk: L • Action: None
the_alchemiser/application/smart_pricing_handler.py • smart_pricing_handler module • Placement: ❌ (→ the_alchemiser/services/smart_pricing_handler.py) • Single concern: ❌ • Risk: H • Action: Refactor to comply with architecture
the_alchemiser/application/execution_manager.py • Coordinate execution of multiple trading strategies. • Placement: ❌ (→ the_alchemiser/services/execution_manager.py) • Single concern: ❌ • Risk: H • Action: Refactor to comply with architecture
the_alchemiser/application/asset_order_handler.py • asset_order_handler module • Placement: ❌ (→ the_alchemiser/services/asset_order_handler.py) • Single concern: ❌ • Risk: H • Action: Refactor to comply with architecture
the_alchemiser/application/order_validation_utils.py • order_validation_utils module • Placement: ✅ • Single concern: ✅ • Risk: L • Action: None
the_alchemiser/application/reporting.py • Helpers for building execution summaries and dashboard data. • Placement: ❌ (→ the_alchemiser/services/reporting.py) • Single concern: ❌ • Risk: H • Action: Refactor to comply with architecture
the_alchemiser/application/alpaca_client.py • alpaca_client module • Placement: ❌ (→ the_alchemiser/services/alpaca_client.py) • Single concern: ❌ • Risk: H • Action: Refactor to comply with architecture
the_alchemiser/application/order_validation.py • order_validation module • Placement: ✅ • Single concern: ❌ • Risk: M • Action: Refactor to comply with architecture
the_alchemiser/application/trading_engine.py • trading_engine module • Placement: ❌ (→ the_alchemiser/services/trading_engine.py) • Single concern: ❌ • Risk: H • Action: Refactor to comply with architecture
the_alchemiser/application/limit_order_handler.py • limit_order_handler module • Placement: ❌ (→ the_alchemiser/services/limit_order_handler.py) • Single concern: ❌ • Risk: H • Action: Refactor to comply with architecture
the_alchemiser/application/progressive_order_utils.py • progressive_order_utils module • Placement: ❌ (→ the_alchemiser/services/progressive_order_utils.py) • Single concern: ❌ • Risk: H • Action: Refactor to comply with architecture
the_alchemiser/interface/email/config.py • Email configuration management module. • Placement: ✅ • Single concern: ✅ • Risk: L • Action: None
the_alchemiser/interface/email/__init__.py • Email module for The Alchemiser quantitative trading system. • Placement: ✅ • Single concern: ✅ • Risk: L • Action: None
the_alchemiser/interface/email/email_utils.py • Email utilities module - REFACTORED • Placement: ✅ • Single concern: ✅ • Risk: L • Action: None
the_alchemiser/interface/email/client.py • Email client module for sending notifications. • Placement: ✅ • Single concern: ✅ • Risk: L • Action: None
the_alchemiser/interface/cli/__init__.py • __init__ module • Placement: ✅ • Single concern: ✅ • Risk: L • Action: None
the_alchemiser/interface/cli/cli.py • cli module • Placement: ✅ • Single concern: ❌ • Risk: M • Action: Refactor to comply with architecture
the_alchemiser/interface/cli/signal_display_utils.py • signal_display_utils module • Placement: ✅ • Single concern: ✅ • Risk: L • Action: None
the_alchemiser/interface/cli/cli_formatter.py • cli_formatter module • Placement: ✅ • Single concern: ❌ • Risk: M • Action: Refactor to comply with architecture
the_alchemiser/interface/cli/dashboard_utils.py • dashboard_utils module • Placement: ✅ • Single concern: ✅ • Risk: L • Action: None
the_alchemiser/interface/email/templates/multi_strategy.py • Multi-strategy report template builder. • Placement: ✅ • Single concern: ✅ • Risk: L • Action: None
the_alchemiser/interface/email/templates/__init__.py • Email templates module for The Alchemiser. • Placement: ✅ • Single concern: ✅ • Risk: L • Action: None
the_alchemiser/interface/email/templates/trading_report.py • Main trading report template builder. • Placement: ✅ • Single concern: ✅ • Risk: L • Action: None
the_alchemiser/interface/email/templates/portfolio.py • Portfolio content builder for email templates. • Placement: ✅ • Single concern: ❌ • Risk: M • Action: Refactor to comply with architecture
the_alchemiser/interface/email/templates/base.py • Base HTML email template module. • Placement: ✅ • Single concern: ✅ • Risk: L • Action: None
the_alchemiser/interface/email/templates/performance.py • Performance content builder for email templates. • Placement: ✅ • Single concern: ❌ • Risk: M • Action: Refactor to comply with architecture
the_alchemiser/interface/email/templates/error_report.py • Error report template builder. • Placement: ✅ • Single concern: ✅ • Risk: L • Action: None
the_alchemiser/interface/email/templates/signals.py • Signals content builder for email templates. • Placement: ✅ • Single concern: ❌ • Risk: M • Action: Refactor to comply with architecture
the_alchemiser/infrastructure/validation/__init__.py • Validation utilities for The Alchemiser Quantitative Trading System. • Placement: ✅ • Single concern: ✅ • Risk: L • Action: None
the_alchemiser/infrastructure/validation/indicator_validator.py • indicator_validator module • Placement: ✅ • Single concern: ❌ • Risk: M • Action: Refactor to comply with architecture
the_alchemiser/infrastructure/logging/__init__.py • Logging helpers and structured formatter. • Placement: ✅ • Single concern: ✅ • Risk: L • Action: None
the_alchemiser/infrastructure/logging/logging_utils.py • Logging helpers for consistent structured output. • Placement: ✅ • Single concern: ✅ • Risk: L • Action: None
the_alchemiser/infrastructure/secrets/secrets_manager.py • secrets_manager module • Placement: ✅ • Single concern: ✅ • Risk: L • Action: None
the_alchemiser/infrastructure/secrets/__init__.py • Secret management utilities. • Placement: ✅ • Single concern: ✅ • Risk: L • Action: None
the_alchemiser/infrastructure/websocket/__init__.py • __init__ module • Placement: ✅ • Single concern: ✅ • Risk: L • Action: None
the_alchemiser/infrastructure/websocket/websocket_connection_manager.py • websocket_connection_manager module • Placement: ✅ • Single concern: ❌ • Risk: M • Action: Refactor to comply with architecture
the_alchemiser/infrastructure/websocket/websocket_order_monitor.py • websocket_order_monitor module • Placement: ✅ • Single concern: ❌ • Risk: M • Action: Refactor to comply with architecture
the_alchemiser/infrastructure/s3/__init__.py • __init__ module • Placement: ✅ • Single concern: ✅ • Risk: L • Action: None
the_alchemiser/infrastructure/s3/s3_utils.py • s3_utils module • Placement: ✅ • Single concern: ✅ • Risk: L • Action: None
the_alchemiser/infrastructure/data_providers/real_time_pricing.py • real_time_pricing module • Placement: ✅ • Single concern: ❌ • Risk: M • Action: Refactor to comply with architecture
the_alchemiser/infrastructure/data_providers/__init__.py • Data provider utilities and abstractions. • Placement: ✅ • Single concern: ✅ • Risk: L • Action: None
the_alchemiser/infrastructure/data_providers/data_provider.py • Unified historical and real-time market data access layer. • Placement: ✅ • Single concern: ❌ • Risk: M • Action: Refactor to comply with architecture
the_alchemiser/infrastructure/data_providers/unified_data_provider_facade.py • Backward-compatible facade for UnifiedDataProvider using refactored services. • Placement: ✅ • Single concern: ❌ • Risk: M • Action: Refactor to comply with architecture
the_alchemiser/infrastructure/alerts/__init__.py • Alerting utilities for translating strategy signals into notifications. • Placement: ✅ • Single concern: ✅ • Risk: L • Action: None
the_alchemiser/infrastructure/alerts/alert_service.py • Utility functions and classes for generating trading alerts. • Placement: ✅ • Single concern: ✅ • Risk: L • Action: None
the_alchemiser/infrastructure/config/config.py • config module • Placement: ✅ • Single concern: ✅ • Risk: L • Action: None
the_alchemiser/infrastructure/config/__init__.py • Configuration package for The Alchemiser Quantitative Trading System. • Placement: ✅ • Single concern: ✅ • Risk: L • Action: None
the_alchemiser/infrastructure/config/execution_config.py • execution_config module • Placement: ✅ • Single concern: ✅ • Risk: L • Action: None
the_alchemiser/infrastructure/config/config_utils.py • Configuration Utilities • Placement: ✅ • Single concern: ✅ • Risk: L • Action: None
the_alchemiser/services/enhanced/__init__.py • Enhanced Services Layer • Placement: ✅ • Single concern: ✅ • Risk: L • Action: None
the_alchemiser/services/enhanced/position_service.py • Enhanced Position Service • Placement: ✅ • Single concern: ❌ • Risk: M • Action: Refactor to comply with architecture
the_alchemiser/services/enhanced/account_service.py • account_service module • Placement: ✅ • Single concern: ❌ • Risk: M • Action: Refactor to comply with architecture
the_alchemiser/services/enhanced/trading_service_manager.py • trading_service_manager module • Placement: ✅ • Single concern: ❌ • Risk: M • Action: Refactor to comply with architecture
the_alchemiser/services/enhanced/market_data_service.py • Market Data Service - Enhanced market data operations with caching and validation. • Placement: ✅ • Single concern: ❌ • Risk: M • Action: Refactor to comply with architecture
the_alchemiser/services/enhanced/order_service.py • Enhanced Order Service • Placement: ✅ • Single concern: ❌ • Risk: M • Action: Refactor to comply with architecture
the_alchemiser/domain/models/__init__.py • Domain models for the trading system. • Placement: ✅ • Single concern: ✅ • Risk: L • Action: None
the_alchemiser/domain/models/account.py • Account domain models. • Placement: ✅ • Single concern: ✅ • Risk: L • Action: None
the_alchemiser/domain/models/market_data.py • Market data domain models. • Placement: ❌ (→ the_alchemiser/infrastructure/market_data.py) • Single concern: ❌ • Risk: H • Action: Refactor to comply with architecture
the_alchemiser/domain/models/position.py • Position domain models. • Placement: ✅ • Single concern: ❌ • Risk: M • Action: Refactor to comply with architecture
the_alchemiser/domain/models/strategy.py • Strategy domain models. • Placement: ✅ • Single concern: ❌ • Risk: M • Action: Refactor to comply with architecture
the_alchemiser/domain/models/order.py • Order domain models. • Placement: ❌ (→ the_alchemiser/infrastructure/order.py) • Single concern: ❌ • Risk: H • Action: Refactor to comply with architecture
the_alchemiser/domain/math/market_timing_utils.py • market_timing_utils module • Placement: ❌ (→ the_alchemiser/infrastructure/market_timing_utils.py) • Single concern: ❌ • Risk: H • Action: Refactor to comply with architecture
the_alchemiser/domain/math/__init__.py • Indicator calculation utilities. • Placement: ✅ • Single concern: ✅ • Risk: L • Action: None
the_alchemiser/domain/math/indicator_utils.py • Indicator utility functions for safe calculation and error handling. • Placement: ❌ (→ the_alchemiser/infrastructure/indicator_utils.py) • Single concern: ❌ • Risk: H • Action: Refactor to comply with architecture
the_alchemiser/domain/math/math_utils.py • Mathematical Utilities for Trading Strategies • Placement: ❌ (→ the_alchemiser/infrastructure/math_utils.py) • Single concern: ❌ • Risk: H • Action: Refactor to comply with architecture
the_alchemiser/domain/math/asset_info.py • asset_info module • Placement: ❌ (→ the_alchemiser/infrastructure/asset_info.py) • Single concern: ❌ • Risk: H • Action: Refactor to comply with architecture
the_alchemiser/domain/math/indicators.py • Technical indicators for trading strategies. • Placement: ❌ (→ the_alchemiser/infrastructure/indicators.py) • Single concern: ❌ • Risk: H • Action: Refactor to comply with architecture
the_alchemiser/domain/math/trading_math.py • trading_math module • Placement: ✅ • Single concern: ❌ • Risk: M • Action: Refactor to comply with architecture
the_alchemiser/domain/interfaces/__init__.py • Domain Layer Interfaces • Placement: ✅ • Single concern: ✅ • Risk: L • Action: None
the_alchemiser/domain/interfaces/trading_repository.py • Trading Repository Interface • Placement: ✅ • Single concern: ❌ • Risk: H • Action: Refactor to comply with architecture
the_alchemiser/domain/interfaces/account_repository.py • Account Repository Interface • Placement: ✅ • Single concern: ❌ • Risk: H • Action: Refactor to comply with architecture
the_alchemiser/domain/interfaces/market_data_repository.py • Market Data Repository Interface • Placement: ✅ • Single concern: ❌ • Risk: H • Action: Refactor to comply with architecture
the_alchemiser/domain/strategies/klm_trading_bot.py • klm_trading_bot module • Placement: ❌ (→ the_alchemiser/infrastructure/klm_trading_bot.py) • Single concern: ❌ • Risk: H • Action: Refactor to comply with architecture
the_alchemiser/domain/strategies/__init__.py • Trading strategy engines and orchestration. • Placement: ✅ • Single concern: ✅ • Risk: L • Action: None
the_alchemiser/domain/strategies/nuclear_signals.py • nuclear_signals module • Placement: ❌ (→ the_alchemiser/infrastructure/nuclear_signals.py) • Single concern: ❌ • Risk: H • Action: Refactor to comply with architecture
the_alchemiser/domain/strategies/tecl_strategy_engine.py • tecl_strategy_engine module • Placement: ❌ (→ the_alchemiser/infrastructure/tecl_strategy_engine.py) • Single concern: ❌ • Risk: H • Action: Refactor to comply with architecture
the_alchemiser/domain/strategies/strategy_manager.py • strategy_manager module • Placement: ❌ (→ the_alchemiser/infrastructure/strategy_manager.py) • Single concern: ❌ • Risk: H • Action: Refactor to comply with architecture
the_alchemiser/domain/strategies/strategy_engine.py • Nuclear Trading Strategy Scenario Classes • Placement: ❌ (→ the_alchemiser/infrastructure/strategy_engine.py) • Single concern: ❌ • Risk: H • Action: Refactor to comply with architecture
the_alchemiser/domain/strategies/tecl_signals.py • tecl_signals module • Placement: ❌ (→ the_alchemiser/infrastructure/tecl_signals.py) • Single concern: ❌ • Risk: H • Action: Refactor to comply with architecture
the_alchemiser/domain/strategies/klm_ensemble_engine.py • KLM Strategy Ensemble Engine • Placement: ❌ (→ the_alchemiser/infrastructure/klm_ensemble_engine.py) • Single concern: ❌ • Risk: H • Action: Refactor to comply with architecture
the_alchemiser/domain/registry/__init__.py • Registry package for The Alchemiser Quantitative Trading System. • Placement: ✅ • Single concern: ✅ • Risk: L • Action: None
the_alchemiser/domain/registry/strategy_registry.py • strategy_registry module • Placement: ✅ • Single concern: ❌ • Risk: M • Action: Refactor to comply with architecture
the_alchemiser/domain/strategies/klm_workers/variant_830_21.py • KLM Strategy Variant 830/21 - "MonkeyBusiness Simons variant V2" • Placement: ❌ (→ the_alchemiser/infrastructure/variant_830_21.py) • Single concern: ❌ • Risk: H • Action: Refactor to comply with architecture
the_alchemiser/domain/strategies/klm_workers/__init__.py • KLM Strategy Workers Package • Placement: ✅ • Single concern: ✅ • Risk: L • Action: None
the_alchemiser/domain/strategies/klm_workers/variant_1200_28.py • KLM Strategy Variant 1200/28 - "KMLM (43)" • Placement: ❌ (→ the_alchemiser/infrastructure/variant_1200_28.py) • Single concern: ❌ • Risk: H • Action: Refactor to comply with architecture
the_alchemiser/domain/strategies/klm_workers/variant_1280_26.py • KLM Strategy Variant 1280/26 - "KMLM (50)" • Placement: ❌ (→ the_alchemiser/infrastructure/variant_1280_26.py) • Single concern: ❌ • Risk: H • Action: Refactor to comply with architecture
the_alchemiser/domain/strategies/klm_workers/variant_530_18.py • KLM Strategy Variant 530/18 - "KMLM Switcher | Anansi Mods" • Placement: ❌ (→ the_alchemiser/infrastructure/variant_530_18.py) • Single concern: ❌ • Risk: H • Action: Refactor to comply with architecture
the_alchemiser/domain/strategies/klm_workers/variant_520_22.py • KLM Strategy Variant 520/22 - "KMLM (23) - Original" • Placement: ❌ (→ the_alchemiser/infrastructure/variant_520_22.py) • Single concern: ❌ • Risk: H • Action: Refactor to comply with architecture
the_alchemiser/domain/strategies/klm_workers/variant_nova.py • KLM Strategy Variant Nova - "Nerfed 2900/8 (373) - Nova - Short BT" • Placement: ❌ (→ the_alchemiser/infrastructure/variant_nova.py) • Single concern: ❌ • Risk: H • Action: Refactor to comply with architecture
the_alchemiser/domain/strategies/klm_workers/base_klm_variant.py • Base KLM Strategy Variant • Placement: ❌ (→ the_alchemiser/infrastructure/base_klm_variant.py) • Single concern: ❌ • Risk: H • Action: Refactor to comply with architecture
the_alchemiser/domain/strategies/klm_workers/variant_410_38.py • KLM Strategy Variant 410/38 - "MonkeyBusiness Simons variant" • Placement: ✅ • Single concern: ❌ • Risk: M • Action: Refactor to comply with architecture
the_alchemiser/domain/strategies/klm_workers/variant_506_38.py • KLM Strategy Variant 506/38 - "KMLM (13) - Longer BT" • Placement: ❌ (→ the_alchemiser/infrastructure/variant_506_38.py) • Single concern: ❌ • Risk: H • Action: Refactor to comply with architecture
the_alchemiser/application/tracking/integration.py • integration module • Placement: ✅ • Single concern: ✅ • Risk: L • Action: None
the_alchemiser/application/tracking/__init__.py • Strategy tracking package for The Alchemiser. • Placement: ✅ • Single concern: ✅ • Risk: L • Action: None
the_alchemiser/application/tracking/strategy_order_tracker.py • strategy_order_tracker module • Placement: ❌ (→ the_alchemiser/services/strategy_order_tracker.py) • Single concern: ❌ • Risk: H • Action: Refactor to comply with architecture
the_alchemiser/application/portfolio_rebalancer/__init__.py • __init__ module • Placement: ✅ • Single concern: ✅ • Risk: L • Action: None
the_alchemiser/application/portfolio_rebalancer/portfolio_rebalancer.py • portfolio_rebalancer module • Placement: ❌ (→ the_alchemiser/services/portfolio_rebalancer.py) • Single concern: ❌ • Risk: H • Action: Refactor to comply with architecture

## Move/Rename Plan

- No automated plan generated

## Refactor Plan

- P1: Remove IO imports from domain modules, ensure Decimal usage
- P2: Replace AlpacaManager usage outside services with TradingServiceManager
- P3: Add TradingSystemErrorHandler where bare except present

## Test Gaps

- Review modules with unknown test coverage for boundary tests


## Appendix

- Automated analysis; manual review recommended for false positives
