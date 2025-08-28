# Business Units Report

| File | Business Unit | Status | Description |
| --- | --- | --- | --- |
| examples/policy_layer_usage.py | utilities | legacy | Functions: example_policy_usage, execute_order, get_trading_client, get_data_provider, fractionability_only_example, canonical_executor_integration, get_alpaca_repository |
| scripts/update_docstrings.py | utilities | current | Functions: classify, status |
| the_alchemiser/main.py | utilities | current | Classes: TradingSystem; Functions: _resolve_log_level, configure_application_logging, create_argument_parser, main |
| the_alchemiser/__init__.py | utilities | current |  |
| the_alchemiser/lambda_handler.py | utilities | current | Functions: parse_event_mode, lambda_handler |
| the_alchemiser/infrastructure/__init__.py | utilities | current |  |
| the_alchemiser/container/__init__.py | utilities | current |  |
| the_alchemiser/container/config_providers.py | utilities | current | Classes: ConfigProviders |
| the_alchemiser/container/infrastructure_providers.py | utilities | current | Classes: InfrastructureProviders |
| the_alchemiser/container/service_providers.py | utilities | current | Classes: ServiceProviders |
| the_alchemiser/container/application_container.py | utilities | current | Classes: ApplicationContainer |
| the_alchemiser/execution/account_service.py | order execution/placement | current | Classes: DataProvider, AccountService |
| the_alchemiser/application/__init__.py | utilities | current |  |
| the_alchemiser/domain/__init__.py | utilities | current |  |
| the_alchemiser/domain/types.py | utilities | current | Classes: AccountInfo, PortfolioHistoryData, ClosedPositionData, EnrichedAccountInfo, PositionInfo, OrderDetails, StrategySignalBase, StrategySignal, StrategyPnLSummary, StrategyPositionData, KLMVariantResult, KLMDecision, MarketDataPoint, IndicatorData, PriceData, QuoteData, DataProviderResult, TradeAnalysis, PortfolioSnapshot, ErrorContext, AlpacaOrderProtocol, AlpacaOrderObject |
| the_alchemiser/interfaces/__init__.py | utilities | current |  |
| the_alchemiser/ports/__init__.py | utilities | current | Classes: MarketData, OrderExecution, RiskChecks, PositionStore, Clock, Notifier |
| the_alchemiser/services/__init__.py | utilities | current |  |
| the_alchemiser/utils/serialization.py | utilities | current | Classes: _ModelDumpProtocol; Functions: _is_model_dump_obj, to_serializable, ensure_serialized_dict |
| the_alchemiser/utils/__init__.py | utilities | current |  |
| the_alchemiser/utils/num.py | utilities | current | Functions: floats_equal |
| the_alchemiser/utils/common.py | utilities | current | Classes: ActionType |
| the_alchemiser/infrastructure/config/execution_config.py | order execution/placement | current | Classes: ExecutionConfig; Functions: get_execution_config, reload_execution_config, create_strategy_config |
| the_alchemiser/infrastructure/config/__init__.py | utilities | current |  |
| the_alchemiser/infrastructure/config/config_utils.py | utilities | current | Functions: load_alert_config |
| the_alchemiser/infrastructure/config/config.py | utilities | current | Classes: LoggingSettings, AlpacaSettings, AwsSettings, AlertsSettings, SecretsManagerSettings, StrategySettings, EmailSettings, DataSettings, TrackingSettings, ExecutionSettings, Settings; Functions: load_settings |
| the_alchemiser/infrastructure/secrets/__init__.py | utilities | current |  |
| the_alchemiser/infrastructure/secrets/secrets_manager.py | utilities | current | Classes: SecretsManager |
| the_alchemiser/infrastructure/adapters/__init__.py | utilities | current |  |
| the_alchemiser/infrastructure/logging/__init__.py | utilities | current |  |
| the_alchemiser/infrastructure/logging/logging_utils.py | utilities | current | Classes: AlchemiserLoggerAdapter, StructuredFormatter; Functions: get_logger, set_request_id, set_error_id, get_request_id, get_error_id, generate_request_id, log_with_context, setup_logging, configure_test_logging, configure_production_logging, get_service_logger, get_trading_logger, log_trade_event, log_error_with_context |
| the_alchemiser/infrastructure/alerts/__init__.py | utilities | current |  |
| the_alchemiser/infrastructure/alerts/alert_service.py | utilities | current | Classes: Alert; Functions: create_alert, create_alerts_from_signal, log_alert_to_file, log_alerts_to_file |
| the_alchemiser/infrastructure/validation/indicator_validator.py | utilities | current | Classes: IndicatorValidationSuite |
| the_alchemiser/infrastructure/validation/__init__.py | utilities | current |  |
| the_alchemiser/infrastructure/s3/__init__.py | utilities | current |  |
| the_alchemiser/infrastructure/s3/s3_utils.py | utilities | current | Classes: S3Handler, S3FileHandler; Functions: get_s3_handler, replace_file_handlers_with_s3 |
| the_alchemiser/infrastructure/websocket/__init__.py | utilities | current |  |
| the_alchemiser/infrastructure/websocket/websocket_order_monitor.py | order execution/placement | current | Classes: OrderCompletionMonitor |
| the_alchemiser/infrastructure/websocket/websocket_connection_manager.py | utilities | current | Classes: WebSocketConnectionManager |
| the_alchemiser/infrastructure/services/__init__.py | utilities | current |  |
| the_alchemiser/infrastructure/services/tick_size_service.py | utilities | current | Classes: TickSizeProvider, DynamicTickSizeService; Functions: create_tick_size_service, resolve_tick_size |
| the_alchemiser/infrastructure/services/slippage_analyzer.py | utilities | current | Classes: SlippageAnalysis, SlippageAnalyzer; Functions: create_slippage_analyzer |
| the_alchemiser/infrastructure/data_providers/__init__.py | utilities | current |  |
| the_alchemiser/infrastructure/data_providers/real_time_pricing.py | utilities | current | Classes: RealTimeQuote, RealTimePricingService, RealTimePricingManager |
| the_alchemiser/application/reporting/reporting.py | utilities | current | Functions: create_execution_summary, save_dashboard_data, build_portfolio_state_data |
| the_alchemiser/application/reporting/__init__.py | utilities | current |  |
| the_alchemiser/application/execution/order_lifecycle_adapter.py | order execution/placement | current | Classes: TradingClientProtocol, WebSocketOrderLifecycleAdapter |
| the_alchemiser/application/execution/execution_manager.py | order execution/placement | current | Classes: ExecutionManager |
| the_alchemiser/application/execution/spread_assessment.py | order execution/placement | current | Classes: SpreadQuality, PreMarketConditions, SpreadAnalysis, SpreadAssessment |
| the_alchemiser/application/execution/canonical_integration_example.py | order execution/placement | legacy | Functions: dto_to_domain_order_request, execute_order_with_canonical_path, example_integration |
| the_alchemiser/application/execution/smart_execution.py | order execution/placement | current | Classes: OrderExecutor, DataProvider, SmartExecution; Functions: is_market_open |
| the_alchemiser/application/execution/smart_pricing_handler.py | order execution/placement | current | Classes: SmartPricingHandler |
| the_alchemiser/application/execution/__init__.py | order execution/placement | current |  |
| the_alchemiser/application/execution/canonical_executor.py | order execution/placement | current | Classes: CanonicalOrderExecutor |
| the_alchemiser/application/execution/order_request_builder.py | order execution/placement | current | Classes: OrderRequestBuilder |
| the_alchemiser/application/trading/bootstrap.py | order execution/placement | current | Classes: TradingBootstrapContext; Functions: bootstrap_from_container, bootstrap_from_service_manager, bootstrap_traditional |
| the_alchemiser/application/trading/alpaca_client.py | order execution/placement | current | Classes: AlpacaClient |
| the_alchemiser/application/trading/__init__.py | order execution/placement | current |  |
| the_alchemiser/application/trading/ports.py | order execution/placement | current | Classes: AccountReadPort, OrderExecutionPort, StrategyAdapterPort, RebalancingOrchestratorPort, ReportingPort |
| the_alchemiser/application/trading/engine_service.py | order execution/placement | current | Classes: AccountInfoProvider, PositionProvider, PriceProvider, RebalancingService, MultiStrategyExecutor, TradingEngine; Functions: _create_default_account_info, main |
| the_alchemiser/application/trading/portfolio_calculations.py | portfolio assessment & management | current | Classes: AllocationComparison; Functions: _to_decimal, calculate_target_vs_current_allocations, build_allocation_comparison |
| the_alchemiser/application/trading/account_facade.py | order execution/placement | current | Classes: AccountFacade; Functions: _create_default_account_info |
| the_alchemiser/application/policies/policy_factory.py | utilities | current | Classes: PolicyFactory |
| the_alchemiser/application/policies/buying_power_policy_impl.py | utilities | current | Classes: BuyingPowerPolicyImpl |
| the_alchemiser/application/policies/fractionability_policy_impl.py | utilities | current | Classes: FractionabilityPolicyImpl |
| the_alchemiser/application/policies/__init__.py | utilities | current |  |
| the_alchemiser/application/policies/policy_orchestrator.py | utilities | current | Classes: PolicyOrchestrator |
| the_alchemiser/application/policies/position_policy_impl.py | utilities | current | Classes: PositionPolicyImpl |
| the_alchemiser/application/policies/risk_policy_impl.py | utilities | current | Classes: RiskPolicyImpl |
| the_alchemiser/application/mapping/account_mapping.py | utilities | current | Classes: AccountMetrics, AccountSummaryTyped; Functions: to_money_usd, account_summary_to_typed, account_typed_to_serializable |
| the_alchemiser/application/mapping/alpaca_dto_mapping.py | utilities | current | Functions: alpaca_order_to_dto, alpaca_dto_to_execution_result, alpaca_order_to_execution_result, create_error_execution_result, alpaca_exception_to_error_dto |
| the_alchemiser/application/mapping/tracking_mapping.py | utilities | current | Functions: strategy_order_to_event_dto, event_dto_to_strategy_order_dict, orders_to_execution_summary_dto, strategy_pnl_to_dict, dict_to_strategy_pnl_dict, normalize_timestamp, ensure_decimal_precision, strategy_order_dataclass_to_dto, strategy_order_dto_to_dataclass_dict, strategy_position_dataclass_to_dto, strategy_position_dto_to_dataclass_dict, strategy_pnl_dataclass_to_dto, strategy_pnl_dto_to_dataclass_dict, strategy_pnl_dto_to_dict |
| the_alchemiser/application/mapping/tracking.py | utilities | current | Functions: strategy_order_event_dto_to_dict, strategy_execution_summary_dto_to_dict, dict_to_strategy_order_event_dto, dict_to_strategy_execution_summary_dto |
| the_alchemiser/application/mapping/strategy_domain_mapping.py | strategy & signal generation | current | Functions: dto_to_strategy_signal_model, strategy_signal_model_to_dto, dto_to_strategy_position_model, strategy_position_model_to_dto, map_strategy_signals_to_models, map_strategy_models_to_dtos, map_strategy_positions_to_models, map_strategy_position_models_to_dtos, normalize_legacy_signal_dict |
| the_alchemiser/application/mapping/execution.py | order execution/placement | current | Functions: _to_decimal, ensure_money, ensure_quantity, _normalize_timestamp_str, _get_attr, _normalize_order_details, _normalize_orders, execution_result_dto_to_dict, dict_to_execution_result_dto, trading_plan_dto_to_dict, dict_to_trading_plan_dto, websocket_result_dto_to_dict, dict_to_websocket_result_dto, quote_dto_to_dict, dict_to_quote_dto, lambda_event_dto_to_dict, dict_to_lambda_event_dto, order_history_dto_to_dict, dict_to_order_history_dto, account_info_to_execution_result_dto, create_trading_plan_dto, create_quote_dto |
| the_alchemiser/application/mapping/order_mapping.py | order execution/placement | current | Classes: OrderSummary; Functions: _coerce_decimal, _map_status, alpaca_order_to_domain, summarize_order, order_to_dict, raw_order_envelope_to_domain_order, raw_order_envelope_to_execution_result_dto |
| the_alchemiser/application/mapping/__init__.py | utilities | current |  |
| the_alchemiser/application/mapping/position_mapping.py | utilities | current | Classes: PositionSummary; Functions: _to_decimal, alpaca_position_to_summary |
| the_alchemiser/application/mapping/tracking_normalization.py | utilities | current | Functions: ensure_price, normalize_tracking_order, normalize_pnl_summary |
| the_alchemiser/application/mapping/market_data_mappers.py | utilities | current | Functions: _parse_ts, bars_to_domain, quote_to_domain |
| the_alchemiser/application/mapping/orders.py | order execution/placement | current | Functions: normalize_order_status, dict_to_order_request_dto, order_request_to_validated_dto, validated_dto_to_dict, validated_dto_to_order_handler_params, order_request_dto_to_domain_order_params, domain_order_to_execution_result_dto |
| the_alchemiser/application/mapping/strategy_signal_mapping.py | strategy & signal generation | current | Functions: _normalize_action, legacy_signal_to_typed, map_signals_dict, typed_dict_to_domain_signal, convert_signals_dict_to_domain, typed_strategy_signal_to_validated_order |
| the_alchemiser/application/mapping/policy_mapping.py | utilities | current | Functions: dto_to_domain_order_request, domain_order_request_to_dto, domain_warning_to_dto, dto_warning_to_domain, domain_result_to_dto, dto_to_domain_result |
| the_alchemiser/application/mapping/pandas_time_series.py | utilities | current | Functions: bars_to_dataframe |
| the_alchemiser/application/mapping/strategy_market_data_adapter.py | strategy & signal generation | current | Classes: StrategyMarketDataAdapter |
| the_alchemiser/application/mapping/strategies.py | utilities | current | Classes: StrategySignalDisplayDTO; Functions: handle_portfolio_symbol_alias, format_strategy_signal_for_display, create_empty_signal_dict, typed_signals_to_display_signals_dict, compute_consolidated_portfolio, run_all_strategies_mapping |
| the_alchemiser/application/mapping/market_data_mapping.py | utilities | current | Functions: bars_to_dataframe, quote_to_tuple, symbol_str_to_symbol, quote_to_current_price, dataframe_to_bars |
| the_alchemiser/application/mapping/trading_service_dto_mapping.py | order execution/placement | current | Functions: position_summary_to_dto, dict_to_position_summary_dto, dict_to_portfolio_summary_dto, dict_to_close_position_dto, dict_to_position_analytics_dto, dict_to_position_metrics_dto, account_summary_typed_to_dto, dict_to_enriched_account_summary_dto, dict_to_buying_power_dto, dict_to_risk_metrics_dto, dict_to_trade_eligibility_dto, dict_to_portfolio_allocation_dto, dict_to_price_dto, dict_to_price_history_dto, dict_to_spread_analysis_dto, dict_to_market_status_dto, dict_to_multi_symbol_quotes_dto, dict_to_order_cancellation_dto, dict_to_order_status_dto, dict_to_operation_result_dto, list_to_open_orders_dto, list_to_enriched_positions_dto |
| the_alchemiser/application/mapping/portfolio_rebalancing_mapping.py | portfolio assessment & management | current | Functions: dto_to_domain_rebalance_plan, dto_plans_to_domain, rebalance_plans_dict_to_collection_dto, rebalancing_summary_dict_to_dto, rebalancing_impact_dict_to_dto, rebalance_instruction_dict_to_dto, rebalance_execution_result_dict_to_dto, safe_rebalancing_summary_dict_to_dto, safe_rebalancing_impact_dict_to_dto |
| the_alchemiser/application/mapping/execution_summary_mapping.py | order execution/placement | current | Functions: dict_to_allocation_summary_dto, dict_to_strategy_pnl_summary_dto, dict_to_strategy_summary_dto, dict_to_trading_summary_dto, dict_to_execution_summary_dto, dict_to_portfolio_state_dto, safe_dict_to_execution_summary_dto, safe_dict_to_portfolio_state_dto |
| the_alchemiser/application/portfolio/rebalancing_orchestrator_facade.py | portfolio assessment & management | current | Classes: RebalancingOrchestratorFacade |
| the_alchemiser/application/portfolio/rebalancing_orchestrator.py | portfolio assessment & management | current | Classes: RebalancingOrchestrator |
| the_alchemiser/application/portfolio/__init__.py | portfolio assessment & management | current |  |
| the_alchemiser/application/portfolio/portfolio_pnl_utils.py | portfolio assessment & management | current | Functions: calculate_strategy_pnl_summary, extract_trading_summary, build_strategy_summary, build_allocation_summary |
| the_alchemiser/application/tracking/strategy_order_tracker.py | strategy & signal generation | current | Classes: StrategyOrder, StrategyPosition, StrategyPnL, StrategyOrderTracker; Functions: get_strategy_tracker |
| the_alchemiser/application/tracking/integration.py | utilities | current | Classes: StrategyExecutionContext, StrategyTrackingMixin; Functions: strategy_execution_context, track_order_execution, get_current_strategy_context, create_strategy_aware_order_callback, extract_order_details_from_alpaca_order, track_alpaca_order_if_filled, configure_strategy_tracking_integration |
| the_alchemiser/application/tracking/__init__.py | utilities | current |  |
| the_alchemiser/application/orders/order_validation.py | order execution/placement | current | Classes: OrderValidationError, RiskLimits, ValidationResult, OrderValidator; Functions: validate_order_list |
| the_alchemiser/application/orders/__init__.py | order execution/placement | current |  |
| the_alchemiser/application/orders/progressive_order_utils.py | order execution/placement | current | Classes: OrderExecutionParams, ProgressiveOrderCalculator; Functions: get_market_urgency_level |
| the_alchemiser/application/orders/order_validation_utils.py | order execution/placement | current | Functions: validate_quantity, validate_notional, validate_order_parameters, round_quantity_for_asset |
| the_alchemiser/application/orders/asset_order_handler.py | order execution/placement | current | Classes: AssetOrderHandler |
| the_alchemiser/application/execution/strategies/aggressive_limit_strategy.py | strategy & signal generation | current | Classes: ExecutionContext, AggressiveLimitStrategy |
| the_alchemiser/application/execution/strategies/execution_context_adapter.py | order execution/placement | current | Classes: ExecutionContextAdapter |
| the_alchemiser/application/execution/strategies/__init__.py | order execution/placement | current |  |
| the_alchemiser/application/execution/strategies/repeg_strategy.py | strategy & signal generation | current | Classes: AttemptPlan, AttemptResult, AttemptState, RepegStrategy |
| the_alchemiser/application/execution/strategies/config.py | order execution/placement | current | Classes: StrategyConfig, StrategyConfigProvider |
| the_alchemiser/application/trading/lifecycle/observers.py | order execution/placement | current | Classes: LoggingObserver, MetricsObserver |
| the_alchemiser/application/trading/lifecycle/cli_observer_interface.py | order execution/placement | current | Classes: CLILifecycleObserver, CLIObserverAdapter |
| the_alchemiser/application/trading/lifecycle/__init__.py | order execution/placement | current |  |
| the_alchemiser/application/trading/lifecycle/manager.py | order execution/placement | current | Classes: OrderLifecycleManager |
| the_alchemiser/application/trading/lifecycle/dispatcher.py | order execution/placement | current | Classes: LifecycleEventDispatcher |
| the_alchemiser/application/portfolio/services/__init__.py | portfolio assessment & management | current |  |
| the_alchemiser/application/portfolio/services/portfolio_rebalancing_service.py | portfolio assessment & management | current | Classes: PortfolioRebalancingService |
| the_alchemiser/application/portfolio/services/portfolio_management_facade.py | portfolio assessment & management | current | Classes: PortfolioManagementFacade |
| the_alchemiser/application/portfolio/services/portfolio_analysis_service.py | portfolio assessment & management | current | Classes: PortfolioAnalysisService |
| the_alchemiser/application/portfolio/services/rebalance_execution_service.py | portfolio assessment & management | current | Classes: RebalanceExecutionService |
| the_alchemiser/domain/trading/__init__.py | order execution/placement | current |  |
| the_alchemiser/domain/market_data/__init__.py | utilities | current |  |
| the_alchemiser/domain/dsl/parser.py | utilities | current | Classes: Vector, DSLParser |
| the_alchemiser/domain/dsl/evaluator.py | utilities | current | Classes: DSLEvaluator |
| the_alchemiser/domain/dsl/__init__.py | utilities | current |  |
| the_alchemiser/domain/dsl/evaluator_cache.py | utilities | current | Classes: EvalContext, NodeEvaluationCache; Functions: create_eval_context, get_memo_stats, clear_memo_stats, is_pure_node, _structural_key, _stable_value, ensure_node_id |
| the_alchemiser/domain/dsl/strategy_loader.py | strategy & signal generation | current | Classes: StrategyLoader, StrategyResult |
| the_alchemiser/domain/dsl/ast.py | utilities | current | Classes: ASTNode, NumberLiteral, Symbol, GreaterThan, LessThan, If, RSI, MovingAveragePrice, MovingAverageReturn, CumulativeReturn, CurrentPrice, StdevReturn, Asset, Group, WeightEqual, WeightSpecified, WeightInverseVolatility, Filter, SelectTop, SelectBottom, FunctionCall, Strategy |
| the_alchemiser/domain/dsl/optimization_config.py | utilities | current | Classes: DSLOptimizationConfig; Functions: _env_bool, _env_int, _env_parallel_enabled, _env_parallel_mode, get_default_config, set_default_config, configure_from_environment, get_optimization_stats |
| the_alchemiser/domain/dsl/errors.py | utilities | current | Classes: DSLError, ParseError, SchemaError, EvaluationError, SecurityError, IndicatorError, PortfolioError |
| the_alchemiser/domain/dsl/interning.py | utilities | current | Functions: node_key, _stable_value, intern_node, _compute_node_id, canonicalise_ast, _canonicalise_recursive, _canonicalise_value, get_intern_stats, clear_intern_stats, clear_intern_pool |
| the_alchemiser/domain/registry/strategy_registry.py | strategy & signal generation | current | Classes: StrategyType, StrategyConfig, StrategyRegistry |
| the_alchemiser/domain/registry/__init__.py | utilities | current |  |
| the_alchemiser/domain/shared_kernel/__init__.py | utilities | current |  |
| the_alchemiser/domain/shared_kernel/types.py | utilities | current |  |
| the_alchemiser/domain/interfaces/__init__.py | utilities | current |  |
| the_alchemiser/domain/interfaces/market_data_repository.py | utilities | current | Classes: MarketDataRepository |
| the_alchemiser/domain/interfaces/trading_repository.py | order execution/placement | current | Classes: TradingRepository |
| the_alchemiser/domain/interfaces/account_repository.py | utilities | current | Classes: AccountRepository |
| the_alchemiser/domain/policies/policy_result.py | utilities | current | Classes: PolicyWarning, PolicyResult; Functions: create_approved_result, create_rejected_result |
| the_alchemiser/domain/policies/base_policy.py | utilities | current | Classes: OrderPolicy |
| the_alchemiser/domain/policies/risk_policy.py | utilities | current | Classes: RiskPolicy |
| the_alchemiser/domain/policies/protocols.py | utilities | current | Classes: TradingClientProtocol, DataProviderProtocol |
| the_alchemiser/domain/policies/buying_power_policy.py | utilities | current | Classes: BuyingPowerPolicy |
| the_alchemiser/domain/policies/__init__.py | utilities | current |  |
| the_alchemiser/domain/policies/fractionability_policy.py | utilities | current | Classes: FractionabilityPolicy |
| the_alchemiser/domain/policies/position_policy.py | utilities | current | Classes: PositionPolicy |
| the_alchemiser/domain/portfolio/__init__.py | portfolio assessment & management | current |  |
| the_alchemiser/domain/strategies/typed_strategy_manager.py | strategy & signal generation | current | Classes: AggregatedSignals, TypedStrategyManager |
| the_alchemiser/domain/strategies/nuclear_logic.py | utilities | current | Functions: evaluate_nuclear_strategy |
| the_alchemiser/domain/strategies/__init__.py | utilities | current |  |
| the_alchemiser/domain/strategies/typed_klm_ensemble_engine.py | utilities | current | Classes: TypedKLMStrategyEngine |
| the_alchemiser/domain/strategies/tecl_strategy_engine.py | strategy & signal generation | current | Classes: TECLStrategyEngine; Functions: main |
| the_alchemiser/domain/strategies/strategy_manager.py | strategy & signal generation | current |  |
| the_alchemiser/domain/strategies/nuclear_typed_engine.py | utilities | current | Classes: NuclearTypedEngine |
| the_alchemiser/domain/strategies/engine.py | utilities | current | Classes: StrategyEngine |
| the_alchemiser/domain/services/__init__.py | utilities | current |  |
| the_alchemiser/domain/services/rebalancing_policy.py | utilities | current | Functions: calculate_rebalance_orders |
| the_alchemiser/domain/math/trading_math.py | order execution/placement | current | Functions: calculate_position_size, calculate_dynamic_limit_price, calculate_dynamic_limit_price_with_symbol, calculate_slippage_buffer, calculate_allocation_discrepancy, calculate_rebalance_amounts |
| the_alchemiser/domain/math/__init__.py | utilities | current |  |
| the_alchemiser/domain/math/indicator_utils.py | utilities | current | Functions: safe_get_indicator |
| the_alchemiser/domain/math/asset_info.py | utilities | current | Classes: AssetType, FractionabilityDetector |
| the_alchemiser/domain/math/math_utils.py | utilities | current | Functions: calculate_stdev_returns, calculate_moving_average, calculate_moving_average_return, calculate_percentage_change, calculate_rolling_metric, safe_division, normalize_to_range, calculate_ensemble_score |
| the_alchemiser/domain/math/market_timing_utils.py | utilities | current | Classes: ExecutionStrategy, MarketOpenTimingEngine |
| the_alchemiser/domain/math/indicators.py | utilities | current | Classes: TechnicalIndicators |
| the_alchemiser/domain/models/strategy.py | strategy & signal generation | current | Classes: StrategySignalModel, StrategyPositionModel |
| the_alchemiser/domain/models/__init__.py | utilities | current |  |
| the_alchemiser/domain/models/market_data.py | utilities | current | Classes: BarModel, QuoteModel, PriceDataModel; Functions: bars_to_dataframe, dataframe_to_bars |
| the_alchemiser/domain/models/position.py | utilities | current | Classes: PositionModel |
| the_alchemiser/domain/models/account.py | utilities | current | Classes: AccountModel, PortfolioHistoryModel |
| the_alchemiser/domain/models/order.py | order execution/placement | current | Classes: OrderModel |
| the_alchemiser/domain/trading/lifecycle/exceptions.py | order execution/placement | current | Classes: InvalidOrderStateTransitionError |
| the_alchemiser/domain/trading/lifecycle/protocols.py | order execution/placement | current | Classes: LifecycleObserver |
| the_alchemiser/domain/trading/lifecycle/states.py | order execution/placement | current | Classes: OrderLifecycleState |
| the_alchemiser/domain/trading/lifecycle/__init__.py | order execution/placement | current |  |
| the_alchemiser/domain/trading/lifecycle/events.py | order execution/placement | current | Classes: LifecycleEventType, OrderLifecycleEvent |
| the_alchemiser/domain/trading/lifecycle/transitions.py | order execution/placement | current |  |
| the_alchemiser/domain/trading/protocols/order_lifecycle.py | order execution/placement | current | Classes: OrderLifecycleMonitor |
| the_alchemiser/domain/trading/protocols/__init__.py | order execution/placement | current |  |
| the_alchemiser/domain/trading/protocols/trading_repository.py | order execution/placement | current | Classes: TradingRepository |
| the_alchemiser/domain/trading/value_objects/symbol.py | order execution/placement | current | Classes: Symbol |
| the_alchemiser/domain/trading/value_objects/order_type.py | order execution/placement | current | Classes: OrderType |
| the_alchemiser/domain/trading/value_objects/order_request.py | order execution/placement | current | Classes: OrderRequest |
| the_alchemiser/domain/trading/value_objects/quantity.py | order execution/placement | current | Classes: Quantity |
| the_alchemiser/domain/trading/value_objects/order_id.py | order execution/placement | current | Classes: OrderId |
| the_alchemiser/domain/trading/value_objects/order_status.py | order execution/placement | current | Classes: OrderStatus |
| the_alchemiser/domain/trading/value_objects/side.py | order execution/placement | current | Classes: Side |
| the_alchemiser/domain/trading/value_objects/time_in_force.py | order execution/placement | current | Classes: TimeInForce |
| the_alchemiser/domain/trading/value_objects/order_status_literal.py | order execution/placement | current |  |
| the_alchemiser/domain/trading/errors/error_codes.py | order execution/placement | current | Classes: OrderErrorCode |
| the_alchemiser/domain/trading/errors/classifier.py | order execution/placement | current | Classes: ClassificationRule, OrderErrorClassifier; Functions: classify_exception, classify_alpaca_error, classify_validation_failure |
| the_alchemiser/domain/trading/errors/order_error.py | order execution/placement | current | Classes: OrderError; Functions: get_remediation_hint |
| the_alchemiser/domain/trading/errors/__init__.py | order execution/placement | current |  |
| the_alchemiser/domain/trading/errors/error_categories.py | order execution/placement | current | Classes: OrderErrorCategory |
| the_alchemiser/domain/trading/entities/order.py | order execution/placement | current | Classes: Order |
| the_alchemiser/domain/market_data/protocols/market_data_port.py | utilities | current | Classes: MarketDataPort |
| the_alchemiser/domain/market_data/models/quote.py | utilities | current | Classes: QuoteModel |
| the_alchemiser/domain/market_data/models/bar.py | utilities | current | Classes: BarModel |
| the_alchemiser/domain/shared_kernel/value_objects/identifier.py | utilities | current | Classes: Identifier |
| the_alchemiser/domain/shared_kernel/value_objects/symbol.py | utilities | current | Classes: Symbol |
| the_alchemiser/domain/shared_kernel/value_objects/money.py | utilities | current | Classes: Money |
| the_alchemiser/domain/shared_kernel/value_objects/percentage.py | utilities | current | Classes: Percentage |
| the_alchemiser/domain/portfolio/strategy_attribution/symbol_classifier.py | strategy & signal generation | current | Classes: SymbolClassifier |
| the_alchemiser/domain/portfolio/strategy_attribution/__init__.py | strategy & signal generation | current |  |
| the_alchemiser/domain/portfolio/strategy_attribution/attribution_engine.py | strategy & signal generation | current | Classes: StrategyAttributionEngine |
| the_alchemiser/domain/portfolio/position/position_analyzer.py | portfolio assessment & management | current | Classes: PositionAnalyzer |
| the_alchemiser/domain/portfolio/position/position_delta.py | portfolio assessment & management | current | Classes: PositionDelta |
| the_alchemiser/domain/portfolio/position/__init__.py | portfolio assessment & management | current |  |
| the_alchemiser/domain/portfolio/rebalancing/rebalance_plan.py | portfolio assessment & management | current | Classes: RebalancePlan |
| the_alchemiser/domain/portfolio/rebalancing/__init__.py | portfolio assessment & management | current |  |
| the_alchemiser/domain/portfolio/rebalancing/rebalance_calculator.py | portfolio assessment & management | current | Classes: RebalanceCalculator |
| the_alchemiser/domain/strategies/protocols/__init__.py | utilities | current |  |
| the_alchemiser/domain/strategies/protocols/strategy_engine.py | strategy & signal generation | current | Classes: StrategyEngine |
| the_alchemiser/domain/strategies/value_objects/alert.py | utilities | current | Classes: Alert |
| the_alchemiser/domain/strategies/value_objects/strategy_signal.py | strategy & signal generation | current | Classes: StrategySignal |
| the_alchemiser/domain/strategies/value_objects/confidence.py | utilities | current | Classes: Confidence |
| the_alchemiser/domain/strategies/klm_workers/variant_506_38.py | utilities | current | Classes: KlmVariant50638 |
| the_alchemiser/domain/strategies/klm_workers/variant_1200_28.py | utilities | current | Classes: KlmVariant120028 |
| the_alchemiser/domain/strategies/klm_workers/variant_nova.py | utilities | current | Classes: KLMVariantNova |
| the_alchemiser/domain/strategies/klm_workers/base_klm_variant.py | utilities | current | Classes: BaseKLMVariant |
| the_alchemiser/domain/strategies/klm_workers/variant_520_22.py | utilities | current | Classes: KlmVariant52022 |
| the_alchemiser/domain/strategies/klm_workers/__init__.py | utilities | current |  |
| the_alchemiser/domain/strategies/klm_workers/variant_410_38.py | utilities | current | Classes: KlmVariant41038 |
| the_alchemiser/domain/strategies/klm_workers/variant_530_18.py | utilities | current | Classes: KlmVariant53018 |
| the_alchemiser/domain/strategies/klm_workers/variant_830_21.py | utilities | current | Classes: KlmVariant83021 |
| the_alchemiser/domain/strategies/klm_workers/variant_1280_26.py | utilities | current | Classes: KlmVariant128026 |
| the_alchemiser/domain/strategies/entities/__init__.py | utilities | current |  |
| the_alchemiser/domain/strategies/models/strategy_position_model.py | strategy & signal generation | current | Classes: StrategyPositionModel |
| the_alchemiser/domain/strategies/models/__init__.py | utilities | current |  |
| the_alchemiser/domain/strategies/models/strategy_signal_model.py | strategy & signal generation | current | Classes: StrategySignalModel |
| the_alchemiser/interfaces/schemas/cli.py | utilities | current | Classes: CLIOptions, CLICommandResult, CLISignalData, CLIAccountDisplay, CLIPortfolioData, CLIOrderDisplay |
| the_alchemiser/interfaces/schemas/smart_trading.py | order execution/placement | current | Classes: OrderValidationMetadataDTO, SmartOrderExecutionDTO, TradingDashboardDTO |
| the_alchemiser/interfaces/schemas/tracking.py | utilities | current | Classes: OrderEventStatus, ExecutionStatus, StrategyValidationMixin, StrategyOrderEventDTO, StrategyOrderDTO, StrategyPositionDTO, StrategyPnLDTO, StrategyExecutionSummaryDTO |
| the_alchemiser/interfaces/schemas/execution.py | order execution/placement | current | Classes: TradingAction, WebSocketStatus, ExecutionResultDTO, TradingPlanDTO, WebSocketResultDTO, QuoteDTO, LambdaEventDTO, OrderHistoryDTO |
| the_alchemiser/interfaces/schemas/reporting.py | utilities | current | Classes: DashboardMetrics, ReportingData, EmailReportData, EmailCredentials, EmailSummary, BacktestResult, PerformanceMetrics |
| the_alchemiser/interfaces/schemas/__init__.py | utilities | current |  |
| the_alchemiser/interfaces/schemas/execution_summary.py | order execution/placement | current | Classes: AllocationSummaryDTO, StrategyPnLSummaryDTO, StrategySummaryDTO, TradingSummaryDTO, ExecutionSummaryDTO, PortfolioStateDTO |
| the_alchemiser/interfaces/schemas/enriched_data.py | utilities | current | Classes: EnrichedOrderDTO, OpenOrdersDTO, EnrichedPositionDTO, EnrichedPositionsDTO |
| the_alchemiser/interfaces/schemas/orders.py | order execution/placement | current | Classes: OrderValidationMixin, OrderRequestDTO, ValidatedOrderDTO, OrderExecutionResultDTO, LimitOrderResultDTO, RawOrderEnvelope, AdjustedOrderRequestDTO, PolicyWarningDTO |
| the_alchemiser/interfaces/schemas/market_data.py | utilities | current | Classes: PriceDTO, PriceHistoryDTO, SpreadAnalysisDTO, MarketStatusDTO, MultiSymbolQuotesDTO |
| the_alchemiser/interfaces/schemas/base.py | utilities | current | Classes: ResultDTO |
| the_alchemiser/interfaces/schemas/common.py | utilities | current | Classes: MultiStrategyExecutionResultDTO |
| the_alchemiser/interfaces/schemas/portfolio_rebalancing.py | portfolio assessment & management | current | Classes: RebalancePlanDTO, RebalancePlanCollectionDTO, RebalancingSummaryDTO, RebalancingImpactDTO, RebalanceInstructionDTO, RebalanceExecutionResultDTO |
| the_alchemiser/interfaces/schemas/alpaca.py | utilities | current | Classes: AlpacaOrderDTO, AlpacaErrorDTO |
| the_alchemiser/interfaces/schemas/accounts.py | utilities | current | Classes: AccountSummaryDTO, AccountMetricsDTO, BuyingPowerDTO, RiskMetricsDTO, TradeEligibilityDTO, PortfolioAllocationDTO, EnrichedAccountSummaryDTO |
| the_alchemiser/interfaces/schemas/operations.py | utilities | current | Classes: OperationResultDTO, OrderCancellationDTO, OrderStatusDTO |
| the_alchemiser/interfaces/schemas/errors.py | utilities | current | Classes: ErrorDetailInfo, ErrorSummaryData, ErrorReportSummary, ErrorNotificationData, ErrorContextData |
| the_alchemiser/interfaces/schemas/positions.py | utilities | current | Classes: PositionDTO, PositionSummaryDTO, PortfolioSummaryDTO, PortfolioMetricsDTO, PositionAnalyticsDTO, PositionMetricsDTO, LargestPositionDTO, ClosePositionResultDTO, PortfolioValueDTO |
| the_alchemiser/services/repository/alpaca_manager.py | utilities | current | Classes: AlpacaManager; Functions: create_alpaca_manager |
| the_alchemiser/services/repository/__init__.py | utilities | current |  |
| the_alchemiser/services/trading/position_manager.py | order execution/placement | current | Classes: PositionManager |
| the_alchemiser/services/trading/trading_client_service.py | order execution/placement | current | Classes: TradingClientService |
| the_alchemiser/services/trading/__init__.py | order execution/placement | current |  |
| the_alchemiser/services/trading/order_service.py | order execution/placement | current | Classes: OrderType, OrderValidationError, OrderOperationError, OrderService |
| the_alchemiser/services/trading/position_service.py | order execution/placement | current | Classes: PositionInfo, PortfolioSummary, PositionValidationError, PositionService |
| the_alchemiser/services/trading/trading_service_manager.py | order execution/placement | current | Classes: TradingServiceManager |
| the_alchemiser/services/market_data/streaming_service.py | utilities | current | Classes: _RealTimePricingProtocol, StreamingService |
| the_alchemiser/services/market_data/price_utils.py | utilities | current | Functions: ensure_scalar_price |
| the_alchemiser/services/market_data/__init__.py | utilities | current |  |
| the_alchemiser/services/market_data/market_data_client.py | utilities | current | Classes: MarketDataClient |
| the_alchemiser/services/market_data/strategy_market_data_service.py | strategy & signal generation | current | Classes: StrategyMarketDataService |
| the_alchemiser/services/market_data/price_fetching_utils.py | utilities | current | Functions: subscribe_for_real_time, extract_bid_ask, calculate_price_from_bid_ask, get_price_from_quote_api, get_price_from_historical_fallback, create_cleanup_function |
| the_alchemiser/services/market_data/market_data_service.py | utilities | current | Classes: MarketDataService |
| the_alchemiser/services/market_data/price_service.py | utilities | current | Classes: ModernPriceFetchingService |
| the_alchemiser/services/errors/handler.py | utilities | current | Classes: ErrorSeverity, ErrorCategory, ErrorDetails, EnhancedAlchemiserError, TradingSystemErrorHandler, EnhancedTradingError, EnhancedDataError, CircuitBreakerOpenError, CircuitBreaker, EnhancedErrorReporter; Functions: get_error_handler, handle_trading_error, send_error_notification_if_needed, retry_with_backoff, categorize_error_severity, create_enhanced_error, get_enhanced_error_reporter, get_global_error_reporter, handle_errors_with_retry |
| the_alchemiser/services/errors/error_recovery.py | utilities | current | Classes: RecoveryResult, ErrorRecoveryStrategy, TradingErrorRecovery, DataErrorRecovery, CircuitState, CircuitBreakerOpenError, CircuitBreaker, RetryStrategy, ExponentialBackoffStrategy, LinearBackoffStrategy, FixedIntervalStrategy, FibonacciBackoffStrategy, SmartRetryManager, ErrorRecoveryManager; Functions: get_recovery_manager, with_circuit_breaker, with_retry, with_resilience |
| the_alchemiser/services/errors/exceptions.py | utilities | current | Classes: AlchemiserError, ConfigurationError, DataProviderError, TradingClientError, OrderExecutionError, OrderPlacementError, OrderTimeoutError, SpreadAnalysisError, BuyingPowerError, InsufficientFundsError, PositionValidationError, StrategyExecutionError, IndicatorCalculationError, MarketDataError, ValidationError, NotificationError, S3OperationError, RateLimitError, MarketClosedError, WebSocketError, StreamingError, LoggingError, FileOperationError, DatabaseError, SecurityError, EnvironmentError |
| the_alchemiser/services/errors/error_reporter.py | utilities | current | Classes: ErrorReporter; Functions: get_error_reporter, report_error_globally |
| the_alchemiser/services/errors/error_handling.py | utilities | current | Classes: ErrorHandler, ServiceMetrics, ErrorContext; Functions: create_service_logger, _deprecated_decorator_stub, _deprecated_instance_stub, with_metrics |
| the_alchemiser/services/errors/__init__.py | utilities | current |  |
| the_alchemiser/services/errors/decorators.py | utilities | current | Functions: translate_service_errors, translate_market_data_errors, translate_trading_errors, translate_streaming_errors, translate_config_errors |
| the_alchemiser/services/errors/scope.py | utilities | current | Classes: _ScopeErrorHandler, ErrorScope; Functions: create_error_scope |
| the_alchemiser/services/errors/context.py | utilities | current | Classes: ErrorContextData; Functions: create_error_context |
| the_alchemiser/services/errors/error_monitoring.py | utilities | current | Classes: HealthStatus, ErrorEvent, RecoveryStats, ErrorMetricsCollector, AlertThresholdManager, HealthReport, ErrorHealthDashboard, ProductionMonitor; Functions: get_production_monitor, record_error_for_monitoring, record_recovery_for_monitoring, get_system_health, get_health_dashboard |
| the_alchemiser/services/account/account_utils.py | utilities | current | Functions: extract_comprehensive_account_data, extract_basic_account_metrics, calculate_position_target_deltas, extract_current_position_values |
| the_alchemiser/services/account/__init__.py | utilities | current |  |
| the_alchemiser/services/account/account_service.py | utilities | current | Classes: AccountService |
| the_alchemiser/services/shared/config_service.py | utilities | current | Classes: ConfigService |
| the_alchemiser/services/shared/service_factory.py | utilities | current | Classes: ServiceFactory |
| the_alchemiser/services/shared/__init__.py | utilities | current |  |
| the_alchemiser/services/shared/retry_decorator.py | utilities | current | Functions: retry_with_backoff, retry_api_call, retry_data_fetch, retry_order_execution |
| the_alchemiser/services/shared/cache_manager.py | utilities | current | Classes: CacheManager |
| the_alchemiser/services/shared/secrets_service.py | utilities | current | Classes: SecretsService |
| the_alchemiser/interface/cli/signal_analyzer.py | utilities | current | Classes: SignalAnalyzer |
| the_alchemiser/interface/cli/cli.py | utilities | current | Functions: show_welcome, signal, trade, status, dsl_count, deploy, version, validate_indicators, main |
| the_alchemiser/interface/cli/signal_display_utils.py | utilities | current | Functions: display_signal_results, display_typed_signal_results, display_signal_results_unified, display_technical_indicators, display_portfolio_details |
| the_alchemiser/interface/cli/__init__.py | utilities | current |  |
| the_alchemiser/interface/cli/cli_formatter.py | utilities | current | Functions: render_technical_indicators, render_strategy_signals, render_portfolio_allocation, render_orders_executed, _format_money, render_account_info, render_header, render_footer, render_target_vs_current_allocations, render_execution_plan, render_enriched_order_summaries, render_multi_strategy_summary |
| the_alchemiser/interface/cli/trading_executor.py | order execution/placement | current | Classes: TradingExecutor |
| the_alchemiser/interface/cli/portfolio_calculations.py | portfolio assessment & management | current | Functions: calculate_target_vs_current_allocations |
| the_alchemiser/interface/cli/error_display_utils.py | utilities | current | Functions: render_order_error, render_order_errors_table, render_error_summary, format_error_for_notification, _get_error_severity |
| the_alchemiser/interface/cli/dashboard_utils.py | utilities | current | Functions: build_basic_dashboard_structure, extract_portfolio_metrics, extract_positions_data, extract_strategies_data, extract_recent_trades_data, build_s3_paths |
| the_alchemiser/interface/email/client.py | utilities | current | Classes: EmailClient; Functions: send_email_notification |
| the_alchemiser/interface/email/email_utils.py | utilities | current | Functions: _build_portfolio_display, _build_closed_positions_pnl_email_html, _build_technical_indicators_email_html, _build_detailed_strategy_signals_email_html, _build_enhanced_trading_summary_email_html, _build_enhanced_portfolio_email_html |
| the_alchemiser/interface/email/__init__.py | utilities | current |  |
| the_alchemiser/interface/email/config.py | utilities | current | Classes: EmailConfig; Functions: get_email_config, is_neutral_mode_enabled |
| the_alchemiser/interface/email/templates/performance.py | utilities | current | Classes: PerformanceBuilder |
| the_alchemiser/interface/email/templates/multi_strategy.py | strategy & signal generation | current | Classes: MultiStrategyReportBuilder |
| the_alchemiser/interface/email/templates/__init__.py | utilities | current | Classes: EmailTemplates; Functions: build_trading_report_html, build_multi_strategy_email_html, build_multi_strategy_email_html_neutral, build_error_email_html |
| the_alchemiser/interface/email/templates/base.py | utilities | current | Classes: BaseEmailTemplate |
| the_alchemiser/interface/email/templates/trading_report.py | order execution/placement | current | Classes: TradingReportBuilder |
| the_alchemiser/interface/email/templates/error_report.py | utilities | current | Classes: ErrorReportBuilder |
| the_alchemiser/interface/email/templates/portfolio.py | portfolio assessment & management | current | Classes: ExecutionSummaryLike, PortfolioBuilder; Functions: _normalise_result |
| the_alchemiser/interface/email/templates/signals.py | utilities | current | Classes: SignalsBuilder |
