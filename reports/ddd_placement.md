# DDD Placement

| Model | File | Layer | Notes |
|---|---|---|---|
| Move | scripts/perform_services_reorg.py | Presentation | Check if domain concept leaking missing slots missing kw_only |
| Change | scripts/update_imports_after_services_reorg.py | Presentation | Check if domain concept leaking missing frozen missing slots missing kw_only |
| PreMarketConditions | the_alchemiser/application/execution/spread_assessment.py | Application | Check if domain concept leaking missing frozen missing slots missing kw_only |
| SpreadAnalysis | the_alchemiser/application/execution/spread_assessment.py | Application | Check if domain concept leaking missing frozen missing slots missing kw_only |
| ValidatedOrder | the_alchemiser/application/orders/order_validation.py | Application |  |
| RiskLimits | the_alchemiser/application/orders/order_validation.py | Application | Check if domain concept leaking missing slots missing kw_only |
| ValidationResult | the_alchemiser/application/orders/order_validation.py | Application | Check if domain concept leaking missing frozen missing slots missing kw_only |
| SettlementResult | the_alchemiser/application/orders/order_validation.py | Application | Check if domain concept leaking missing frozen missing slots missing kw_only |
| OrderExecutionParams | the_alchemiser/application/orders/progressive_order_utils.py | Application | Check if domain concept leaking missing frozen missing slots missing kw_only |
| StrategyOrder | the_alchemiser/application/tracking/strategy_order_tracker.py | Application | Check if domain concept leaking missing frozen missing slots missing kw_only |
| StrategyPosition | the_alchemiser/application/tracking/strategy_order_tracker.py | Application | Check if domain concept leaking missing frozen missing slots missing kw_only |
| StrategyPnL | the_alchemiser/application/tracking/strategy_order_tracker.py | Application | Check if domain concept leaking missing frozen missing slots missing kw_only |
| MultiStrategyExecutionResult | the_alchemiser/application/types.py | Application | Check if domain concept leaking missing frozen missing slots missing kw_only |
| AccountModel | the_alchemiser/domain/models/account.py | Domain | missing slots missing kw_only |
| PortfolioHistoryModel | the_alchemiser/domain/models/account.py | Domain | missing slots missing kw_only |
| BarModel | the_alchemiser/domain/models/market_data.py | Domain | missing slots missing kw_only |
| QuoteModel | the_alchemiser/domain/models/market_data.py | Domain | missing slots missing kw_only |
| PriceDataModel | the_alchemiser/domain/models/market_data.py | Domain | missing slots missing kw_only |
| OrderModel | the_alchemiser/domain/models/order.py | Domain | missing slots missing kw_only |
| PositionModel | the_alchemiser/domain/models/position.py | Domain | missing slots missing kw_only |
| StrategySignalModel | the_alchemiser/domain/models/strategy.py | Domain | missing slots missing kw_only |
| StrategyPositionModel | the_alchemiser/domain/models/strategy.py | Domain | missing slots missing kw_only |
| PositionDelta | the_alchemiser/domain/portfolio/position/position_delta.py | Domain | missing slots missing kw_only |
| RebalancePlan | the_alchemiser/domain/portfolio/rebalancing/rebalance_plan.py | Domain | missing slots missing kw_only |
| StrategyConfig | the_alchemiser/domain/registry/strategy_registry.py | Domain | missing frozen missing slots missing kw_only |
| LoggingSettings | the_alchemiser/infrastructure/config/config.py | Infrastructure |  |
| AlpacaSettings | the_alchemiser/infrastructure/config/config.py | Infrastructure |  |
| AwsSettings | the_alchemiser/infrastructure/config/config.py | Infrastructure |  |
| AlertsSettings | the_alchemiser/infrastructure/config/config.py | Infrastructure |  |
| SecretsManagerSettings | the_alchemiser/infrastructure/config/config.py | Infrastructure |  |
| StrategySettings | the_alchemiser/infrastructure/config/config.py | Infrastructure |  |
| EmailSettings | the_alchemiser/infrastructure/config/config.py | Infrastructure |  |
| DataSettings | the_alchemiser/infrastructure/config/config.py | Infrastructure |  |
| TrackingSettings | the_alchemiser/infrastructure/config/config.py | Infrastructure |  |
| ExecutionSettings | the_alchemiser/infrastructure/config/config.py | Infrastructure |  |
| ExecutionConfig | the_alchemiser/infrastructure/config/execution_config.py | Infrastructure | Check if domain concept leaking missing frozen missing slots missing kw_only |
| RealTimeQuote | the_alchemiser/infrastructure/data_providers/real_time_pricing.py | Infrastructure | Check if domain concept leaking missing frozen missing slots missing kw_only |
| PositionInfo | the_alchemiser/services/trading/position_service.py | Application | Check if domain concept leaking missing frozen missing slots missing kw_only |
| PortfolioSummary | the_alchemiser/services/trading/position_service.py | Application | Check if domain concept leaking missing frozen missing slots missing kw_only |