# Model Inventory

Total files: 19
Total Pydantic models: 11
Total dataclasses: 28

## scripts/perform_services_reorg.py

### Dataclasses

- **Move**: fields (2) src, dst

### IO Edges

sys, pathlib



## scripts/update_imports_after_services_reorg.py

### Dataclasses

- **Change**: fields (3) path, original, updated

### IO Edges

sys, pathlib



## the_alchemiser/application/execution/spread_assessment.py

### Dataclasses

- **PreMarketConditions**: fields (4) spread_cents, spread_quality, recommended_wait_minutes, max_slippage_bps

- **SpreadAnalysis**: fields (4) spread_cents, spread_quality, spread_bps, midpoint



## the_alchemiser/application/orders/order_validation.py

### Pydantic Models

- **ValidatedOrder**: fields (17) id, client_order_id, symbol, quantity, side, order_type, time_in_force, limit_price, stop_price, status, filled_qty, filled_avg_price, created_at, updated_at, estimated_value, risk_checks_passed, validation_errors

### Dataclasses

- **RiskLimits**: fields (5) max_position_pct, max_portfolio_concentration, max_order_value, min_order_value, max_daily_trades

- **ValidationResult**: fields (4) is_valid, errors, warnings, validated_order

- **SettlementResult**: fields (6) success, settled_orders, failed_orders, timeout_orders, errors, settlement_time_seconds

### IO Edges

pydantic



## the_alchemiser/application/orders/progressive_order_utils.py

### Dataclasses

- **OrderExecutionParams**: fields (4) max_wait_seconds, step_count, step_percentages, tick_aggressiveness



## the_alchemiser/application/tracking/strategy_order_tracker.py

### Dataclasses

- **StrategyOrder**: fields (7) order_id, strategy, symbol, side, quantity, price, timestamp

- **StrategyPosition**: fields (6) strategy, symbol, quantity, average_cost, total_cost, last_updated

- **StrategyPnL**: fields (6) strategy, realized_pnl, unrealized_pnl, total_pnl, positions, allocation_value



## the_alchemiser/application/types.py

### Dataclasses

- **MultiStrategyExecutionResult**: fields (8) success, strategy_signals, consolidated_portfolio, orders_executed, account_info_before, account_info_after, execution_summary, final_portfolio_state



## the_alchemiser/domain/models/account.py

### Dataclasses

- **AccountModel**: fields (10) account_id, equity, cash, buying_power, day_trades_remaining, portfolio_value, last_equity, daytrading_buying_power, regt_buying_power, status

- **PortfolioHistoryModel**: fields (4) profit_loss, profit_loss_pct, equity, timestamp



## the_alchemiser/domain/models/market_data.py

### Dataclasses

- **BarModel**: fields (7) symbol, timestamp, open, high, low, close, volume

- **QuoteModel**: fields (6) symbol, bid_price, ask_price, bid_size, ask_size, timestamp

- **PriceDataModel**: fields (6) symbol, price, timestamp, bid, ask, volume



## the_alchemiser/domain/models/order.py

### Dataclasses

- **OrderModel**: fields (11) id, symbol, qty, side, order_type, time_in_force, status, filled_qty, filled_avg_price, created_at, updated_at



## the_alchemiser/domain/models/position.py

### Dataclasses

- **PositionModel**: fields (8) symbol, qty, side, market_value, cost_basis, unrealized_pl, unrealized_plpc, current_price



## the_alchemiser/domain/models/strategy.py

### Dataclasses

- **StrategySignalModel**: fields (5) symbol, action, confidence, reasoning, allocation_percentage

- **StrategyPositionModel**: fields (5) symbol, quantity, entry_price, current_price, strategy_type



## the_alchemiser/domain/portfolio/position/position_delta.py

### Dataclasses

- **PositionDelta**: fields (7) symbol, current_qty, target_qty, delta, action, quantity, message



## the_alchemiser/domain/portfolio/rebalancing/rebalance_plan.py

### Dataclasses

- **RebalancePlan**: fields (8) symbol, current_weight, target_weight, weight_diff, target_value, current_value, trade_amount, needs_rebalance



## the_alchemiser/domain/registry/strategy_registry.py

### Dataclasses

- **StrategyConfig**: fields (5) strategy_type, engine_class, default_allocation, description, enabled



## the_alchemiser/infrastructure/config/config.py

### Pydantic Models

- **LoggingSettings**: fields (1) level

- **AlpacaSettings**: fields (5) endpoint, paper_endpoint, cash_reserve_pct, slippage_bps, enable_websocket_orders

- **AwsSettings**: fields (5) region, account_id, repo_name, lambda_arn, image_tag

- **AlertsSettings**: fields (2) alert_config_s3, cooldown_minutes

- **SecretsManagerSettings**: fields (2) region_name, secret_name

- **StrategySettings**: fields (3) default_strategy_allocations, poll_timeout, poll_interval

- **EmailSettings**: fields (5) smtp_server, smtp_port, from_email, to_email, neutral_mode

- **DataSettings**: fields (2) cache_duration, default_symbol

- **TrackingSettings**: fields (5) s3_bucket, strategy_orders_path, strategy_positions_path, strategy_pnl_history_path, order_history_limit

- **ExecutionSettings**: fields (9) max_slippage_bps, aggressive_timeout_seconds, max_repegs, enable_premarket_assessment, market_open_fast_execution, tight_spread_threshold, wide_spread_threshold, leveraged_etf_symbols, high_volume_etfs

### IO Edges

pydantic



## the_alchemiser/infrastructure/config/execution_config.py

### Dataclasses

- **ExecutionConfig**: fields (9) max_slippage_bps, aggressive_timeout_seconds, max_repegs, enable_premarket_assessment, market_open_fast_execution, tight_spread_threshold, wide_spread_threshold, leveraged_etf_symbols, high_volume_etfs



## the_alchemiser/infrastructure/data_providers/real_time_pricing.py

### Dataclasses

- **RealTimeQuote**: fields (4) bid, ask, last_price, timestamp



## the_alchemiser/services/trading/position_service.py

### Dataclasses

- **PositionInfo**: fields (8) symbol, quantity, market_value, unrealized_pnl, unrealized_pnl_percent, cost_basis, current_price, weight_percent

- **PortfolioSummary**: fields (6) total_market_value, total_positions, largest_position_value, largest_position_percent, cash_balance, total_equity


