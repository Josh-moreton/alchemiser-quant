# Architecture Review

## Per-file Report

**Root and Container**  
- `the_alchemiser/__init__.py` – package metadata; follows architecture.  
- `the_alchemiser/main.py` – bootstraps TradingSystem and CLI; mixes orchestration, logging and config access; keep as application entry point but move CLI logic to `interface/cli/main.py` and centralise config loading in `infrastructure/config`.  
- `the_alchemiser/lambda_handler.py` – Lambda entry; pulls application logic and error handling together; acceptable but trim business logic to application layer only.  
- `the_alchemiser/container/application_container.py`, `config_providers.py`, `infrastructure_providers.py`, `service_providers.py` – DI configuration; correct placement; split provider definitions into separate modules to reduce coupling.

**Execution**  
- `execution/account_service.py` – account/position helpers; belongs in `services/account` or merged into `application/portfolio`; currently mixes position logic and market-data calls—split into interface (`AccountService`) and data adapter.

**Application Layer**  
- `application/execution/execution_manager.py` – coordinates order execution; OK.  
- `application/execution/smart_execution.py` (587 lines) – god file combining order splitting, slippage logic, logging and Alpaca calls; move pure calculations to `domain/math` or `application/orders`; keep Alpaca interactions in a dedicated infrastructure adapter.  
- `application/execution/smart_pricing_handler.py`, `spread_assessment.py` – pricing and spread utilities; largely compliant; ensure API calls go through service layer.  
- `application/orders/asset_order_handler.py` (288), `limit_order_handler.py` (238), `progressive_order_utils.py` (330), `order_validation.py` (640), `order_validation_utils.py` – extensive order rules; break into smaller modules: validation schemas in domain, execution helpers in application.  
- `application/portfolio/services/portfolio_analysis_service.py` (432), `portfolio_management_facade.py` (244), `portfolio_rebalancing_service.py` (273), `rebalance_execution_service.py` (351) – mix analysis, orchestration and trading; move analytics to domain/portfolio, retain orchestration here, and delegate trade placement to services layer.  
- `application/portfolio/portfolio_pnl_utils.py` – P&L utilities; consider move to `domain/portfolio`.  
- `application/reporting/reporting.py` – summary builders; OK but avoid direct file/console I/O.  
- `application/tracking/integration.py` (262) and `strategy_order_tracker.py` (809) – tracking and persistence; 809-line tracker is a god file combining analytics, DB/cache, and reporting; split into data persistence adapter (infrastructure), tracking service (application) and analytics (domain).  
- `application/trading/alpaca_client.py` (456) – direct Alpaca API wrapper in application; should reside under `infrastructure` or `services/repository` and expose higher-level methods via service layer.  
- `application/trading/trading_engine.py` (1404) – massive orchestrator mixing strategy evaluation, execution, portfolio tasks, legacy adapters and config; split into modules: strategy orchestration, account/portfolio management, order execution. Move legacy adapter handling and Alpaca calls to services/infrastructure.  
- `application/types.py` – DTOs for application layer; fine.

**Domain Layer**  
- Models, math utilities and portfolio helpers (`domain/models/*`, `domain/math/*`, `domain/portfolio/*`, `domain/types.py`) – implement pure business logic; good.  
- `domain/registry/strategy_registry.py` – domain registry; fine.  
- Strategy engines: `strategy_engine.py` (487), `strategy_manager.py` (744), `nuclear_signals.py` (409), `tecl_signals.py` (260), `tecl_strategy_engine.py` (406), `klm_trading_bot.py` (291), `klm_ensemble_engine.py` (477), and all `klm_workers/variant_*.py` files – strategy logic. Many import `infrastructure.config`, `data_providers`, `logging`, and alert services, mixing domain with infrastructure. Introduce repository interfaces (`domain/interfaces`) and inject services from `services` layer; remove direct infrastructure imports. Large files (`strategy_manager.py` and some variants) should be decomposed (e.g., signal generation vs. validation).  
- `domain/strategies/strategy_manager.py` also loads settings and runtime data; move config loading to infrastructure/services.

**Services Layer**  
- Account services (`services/account/account_service.py` 485, `account_utils.py`, `legacy_account_service.py`) – handle account orchestration and util functions; `account_service.py` is large and mixes Alpaca API calls and business calculations; extract API calls to repository (`services/repository/alpaca_manager.py`) and move pure computations to domain.  
- Shared services (`shared/config_service.py`, `service_factory.py`, `cache_manager.py`, `retry_decorator.py`, `secrets_service.py`) – configuration and infrastructure helpers; ensure config and secrets move to `infrastructure/config` and `infrastructure/secrets` respectively.  
- Trading services (`trading/trading_service_manager.py` (339), `position_manager.py` (505), `position_service.py` (481), `order_service.py` (431), `trading_client_service.py`) – coordinate operations but contain heavy logic and Alpaca calls; move low-level API interactions to `services/repository/alpaca_manager.py` and keep orchestration thin.  
- Market data services (`market_data_client.py`, `market_data_service.py` (289), `price_service.py` (279), `streaming_service.py`, `price_fetching_utils.py`, `price_utils.py`) – combine caching, validation, and external API calls; split into domain validators, infrastructure adapters, and lightweight services.  
- Repository layer `alpaca_manager.py` (721) – enormous file providing all Alpaca API access; split by concern (orders, positions, market data) and move to `infrastructure` or keep as repository but reduce scope.  
- Error handling (`services/errors/*`) – `error_handler.py` (983), `error_monitoring.py` (542), `error_recovery.py` (612), `error_handling.py`, `error_reporter.py`, `exceptions.py`. These files mix logging, notifications, classification, recovery strategies, and configuration; split into: core error types (domain), handling utilities (services), notification adapters (infrastructure/email), and monitoring (infrastructure/logging).  
- `services/enhanced/__init__.py` – deprecated shim; can be removed once references cleaned.

**Infrastructure Layer**  
- Config (`infrastructure/config/config.py`, `config_utils.py`, `execution_config.py`) – config models/utilities; ensure no business logic resides here.  
- Data providers: `data_provider.py` (1127) and `real_time_pricing.py` (701) are god files combining historical retrieval, streaming, caching, and retry logic; split into REST client, WebSocket client, cache layer, and adapters implementing domain repository interfaces.  
- `unified_data_provider_facade.py` (306) – backward-compatible façade; acceptable as temporary adapter.  
- Logging (`logging/logging_utils.py`), S3 utilities (`s3_utils.py`), secrets (`secrets_manager.py`), adapters (`legacy_portfolio_adapter.py`), alerts (`alert_service.py`), validation (`indicator_validator.py`), websocket modules – mostly correctly placed, but avoid embedding business rules (e.g., alert logic) in infrastructure; expose interfaces consumed by services/domain.  
- `indicator_validator.py` has complex validation logic with API calls; split pure validation (domain) from data fetching (infrastructure).

**Interface Layer**  
- CLI files (`cli.py` 618, `cli_formatter.py` 526, `dashboard_utils.py`, `signal_analyzer.py`, `signal_display_utils.py`, `trading_executor.py`) – implement command handling and presentation. `cli.py` and `cli_formatter.py` are god files mixing command definitions, validation, formatting, and execution orchestration; break into per-command modules, keep execution via application layer, and move formatting helpers to separate files.  
- Email package (`email/client.py`, `config.py`, `email_utils.py`, templates) – generating and sending emails. Large template files (e.g., `templates/portfolio.py` 697 lines) mostly contain HTML; consider switching to templating engine (Jinja) and splitting into smaller templates. Move configuration management to infrastructure, keep client thin, and ensure no business logic leaks here.

**Utils**  
- `utils/common.py`, `utils/num.py`, `utils/__init__.py` – generic helpers; ensure they remain free of business rules.

**Miscellaneous `__init__.py` files**  
- Numerous package initializers (e.g., `services/__init__.py`, `infrastructure/*/__init__.py`, `interface/cli/__init__.py`, etc.) – all simple declarations; no action.

## Final Restructuring Plan

1. **Eliminate God Files**
   - Split `application/trading/trading_engine.py` into modules: `strategy_orchestrator`, `portfolio_manager`, `execution_facade`, and move Alpaca calls to services.
   - Break down `services/errors/error_handler.py`, `error_monitoring.py`, `error_recovery.py`, and `infrastructure/data_providers/data_provider.py` into focused modules per responsibility.
   - Reduce `strategy_order_tracker.py`, `cli.py`, `cli_formatter.py`, `portfolio.py` email template and `real_time_pricing.py` by extracting shared logic into utilities or separate services.

2. **Correct Layer Boundaries**
   - Move `execution/account_service.py` to `services/account` and inject a market-data repository instead of direct provider.
   - Refactor domain strategies (`strategy_manager.py`, `klm_trading_bot.py`, `nuclear_signals.py`, `tecl_signals.py`, etc.) to depend on interfaces from `domain/interfaces` and obtain data via injected repositories; remove direct imports from `infrastructure.config`, `data_providers`, and alert services.
   - Relocate `application/trading/alpaca_client.py` and any raw Alpaca calls to `services/repository` or an `infrastructure/alpaca` adapter.

3. **Improve Separation of Concerns**
   - Move configuration loading and secrets access from services/domain files to `infrastructure/config` and `infrastructure/secrets` with dependency injection.
   - Isolate email formatting and sending: templates in `interface/email/templates`, client in `infrastructure/notifications`, and service wrapper in `services/notifications`.
   - Ensure error notification and monitoring leverage infrastructure adapters rather than being embedded in core handlers.

4. **Introduce Interfaces and DI**
   - Define repository interfaces for market data, orders, accounts (`domain/interfaces`) and ensure services/application depend only on these abstractions.
   - Use the DI container to supply concrete infrastructure implementations.

5. **Clean Up Legacy & Deprecated Code**
   - Remove `services/enhanced/__init__.py` shim once migrations complete.
   - Replace enormous procedural blocks with smaller classes or functions, each with single responsibility.

6. **Adopt Templating & Utilities**
   - Replace raw HTML string builders with Jinja templates for email.
   - Extract repeated CLI formatting and validation logic into dedicated utility modules.

7. **Testing & Documentation**
   - After restructuring, update unit tests to follow new module boundaries and ensure each layer is tested in isolation.

