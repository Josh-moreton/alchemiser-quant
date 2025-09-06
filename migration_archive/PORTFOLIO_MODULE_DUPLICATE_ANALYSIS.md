# Portfolio Module Duplicate Analysis

## CLI Entry Point
- **File**: `the_alchemiser/shared/cli/cli.py`
- **Function**: `trade()` command (line ~400)
- **Entry Point Configuration**: `pyproject.toml` defines `alchemiser = "the_alchemiser.shared.cli.cli:app"`

## Execution Path Trace

The execution flow for `poetry run alchemiser trade` follows this path:

1. **CLI Layer** (`shared/cli/cli.py`)
   - `trade()` function calls `main()` from `the_alchemiser.main`
   - Builds argument list and passes to main entry point

2. **Main Orchestrator** (`main.py`)
   - `TradingSystem.execute_trading()` creates `TradingExecutor`
   - Initializes dependency injection container
   - Handles top-level error boundaries

3. **Trading Executor** (`shared/cli/trading_executor.py`)
   - `TradingExecutor.run()` creates `TradingEngine` via modern bootstrap
   - Checks market hours using `is_market_open()`
   - Calls `trader.execute_multi_strategy()`

4. **Trading Engine** (`strategy/engines/core/trading_engine.py`)
   - Creates `AlpacaClient` and `SmartExecution` for order management
   - Initializes `PortfolioManagementFacade` and `RebalancingOrchestratorFacade`
   - Executes multi-strategy workflow via `execute_multi_strategy()`

5. **Portfolio Module Integration Points**:
   - **PortfolioManagementFacade** → **RebalancingOrchestrator** for rebalancing logic
   - **RebalancingOrchestratorFacade** → **RebalanceExecutionService** for execution
   - **PositionManager** → Position tracking and management
   - **PortfolioCalculations** → Mathematical calculations and analytics

## AST-Based Duplicate Detection Results

### Summary Statistics
- **Total Files Analyzed**: 69
- **Total Functions**: 339
- **Total Classes**: 67
- **Exact Duplicates**: 40
- **Near Duplicates**: 56
- **Duplication Percentage**: 23.6%

### File Category Analysis

#### Position Analysis Files
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/holdings/position_model.py` - `from_dict()` (line 29)
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/holdings/position_model.py` - `to_dict()` (line 42)
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/holdings/position_model.py` - `is_profitable()` (line 56)
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/holdings/position_model.py` - `percentage_return()` (line 61)
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/holdings/position_model.py` - `shares_count()` (line 66)
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/holdings/position_model.py` - `is_long()` (line 71)
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/holdings/position_model.py` - `is_short()` (line 76)
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/holdings/position_model.py` - `average_cost()` (line 81)
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/holdings/position_service.py` - `__init__()` (line 71)
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/holdings/position_service.py` - `get_positions_with_analysis()` (line 93)


#### Rebalancing Files
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/allocation/rebalance_plan.py` - `trade_direction()` (line 32)
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/allocation/rebalance_plan.py` - `trade_amount_abs()` (line 39)
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/allocation/rebalance_plan.py` - `weight_change_bps()` (line 44)
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/allocation/rebalance_plan.py` - `__str__()` (line 48)
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/allocation/portfolio_rebalancing_service.py` - `__init__()` (line 49)
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/allocation/portfolio_rebalancing_service.py` - `_calculate_rebalancing_plan_domain()` (line 72)
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/allocation/portfolio_rebalancing_service.py` - `calculate_rebalancing_plan()` (line 94)
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/allocation/portfolio_rebalancing_service.py` - `analyze_position_deltas()` (line 129)
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/allocation/portfolio_rebalancing_service.py` - `get_rebalancing_summary()` (line 161)
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/allocation/portfolio_rebalancing_service.py` - `get_symbols_requiring_sells()` (line 237)


#### P&L Analysis Files  
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/pnl/strategy_order_tracker.py` - `get_strategy_tracker()` (line 1237)
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/pnl/strategy_order_tracker.py` - `from_order_data()` (line 70)
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/pnl/strategy_order_tracker.py` - `update_with_order()` (line 102)
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/pnl/strategy_order_tracker.py` - `total_return_pct()` (line 146)
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/pnl/strategy_order_tracker.py` - `__init__()` (line 156)
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/pnl/strategy_order_tracker.py` - `_setup_s3_paths()` (line 187)
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/pnl/strategy_order_tracker.py` - `record_order()` (line 212)
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/pnl/strategy_order_tracker.py` - `_process_order()` (line 266)
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/pnl/strategy_order_tracker.py` - `get_execution_summary_dto()` (line 297)
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/pnl/strategy_order_tracker.py` - `get_strategy_pnl()` (line 369)


### Duplicate Function Names Across Files

#### `total_return_pct()` appears in 2 files:
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/schemas/tracking.py`
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/pnl/strategy_order_tracker.py`

#### `__init__()` appears in 17 files:
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/holdings/position_manager.py`
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/tracking/integration.py`
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/core/portfolio_management_facade.py`
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/core/portfolio_analysis_service.py`
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/allocation/portfolio_rebalancing_service.py`
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/fractionability_policy_impl.py`
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/allocation/rebalance_execution_service.py`
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/position_policy_impl.py`
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/holdings/position_service.py`
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/pnl/strategy_order_tracker.py`
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/core/rebalancing_orchestrator.py`
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/buying_power_policy_impl.py`
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/risk_policy_impl.py`
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/policy_orchestrator.py`
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/state/attribution_engine.py`
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/allocation/rebalance_calculator.py`
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/core/rebalancing_orchestrator_facade.py`

#### `from_dict()` appears in 2 files:
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/holdings/position_model.py`
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/mappers/position.py`

#### `to_dict()` appears in 2 files:
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/holdings/position_model.py`
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/mappers/position.py`

#### `is_profitable()` appears in 2 files:
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/holdings/position_model.py`
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/mappers/position.py`

#### `percentage_return()` appears in 2 files:
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/holdings/position_model.py`
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/mappers/position.py`

#### `shares_count()` appears in 2 files:
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/holdings/position_model.py`
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/mappers/position.py`

#### `is_long()` appears in 2 files:
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/holdings/position_model.py`
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/mappers/position.py`

#### `is_short()` appears in 2 files:
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/holdings/position_model.py`
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/mappers/position.py`

#### `average_cost()` appears in 2 files:
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/holdings/position_model.py`
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/mappers/position.py`

#### `get_current_positions()` appears in 2 files:
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/holdings/position_manager.py`
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/core/portfolio_management_facade.py`

#### `should_use_liquidation_api()` appears in 3 files:
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/holdings/position_manager.py`
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/position_policy_impl.py`
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/position_policy.py`

#### `validate_buying_power()` appears in 3 files:
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/holdings/position_manager.py`
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/buying_power_policy.py`
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/buying_power_policy_impl.py`

#### `__str__()` appears in 2 files:
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/allocation/rebalance_plan.py`
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/holdings/position_delta.py`

#### `_to_decimal()` appears in 3 files:
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/mappers/position_mapping.py`
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/holdings/position_mapping.py`
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/calculations/portfolio_calculations.py`

#### `alpaca_position_to_summary()` appears in 2 files:
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/mappers/position_mapping.py`
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/holdings/position_mapping.py`

#### `calculate_rebalancing_plan()` appears in 2 files:
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/allocation/portfolio_rebalancing_service.py`
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/core/portfolio_management_facade.py`

#### `get_rebalancing_summary()` appears in 2 files:
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/allocation/portfolio_rebalancing_service.py`
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/core/portfolio_management_facade.py`

#### `estimate_rebalancing_impact()` appears in 2 files:
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/allocation/portfolio_rebalancing_service.py`
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/core/portfolio_management_facade.py`

#### `_get_current_position_values()` appears in 2 files:
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/allocation/portfolio_rebalancing_service.py`
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/core/portfolio_analysis_service.py`

#### `_get_portfolio_value()` appears in 2 files:
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/allocation/portfolio_rebalancing_service.py`
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/core/portfolio_analysis_service.py`

#### `dto_to_domain_rebalance_plan()` appears in 2 files:
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/allocation/portfolio_rebalancing_mapping.py`
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/mappers/portfolio_rebalancing_mapping.py`

#### `dto_plans_to_domain()` appears in 2 files:
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/allocation/portfolio_rebalancing_mapping.py`
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/mappers/portfolio_rebalancing_mapping.py`

#### `rebalance_plans_dict_to_collection_dto()` appears in 2 files:
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/allocation/portfolio_rebalancing_mapping.py`
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/mappers/portfolio_rebalancing_mapping.py`

#### `rebalancing_summary_dict_to_dto()` appears in 2 files:
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/allocation/portfolio_rebalancing_mapping.py`
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/mappers/portfolio_rebalancing_mapping.py`

#### `rebalancing_impact_dict_to_dto()` appears in 2 files:
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/allocation/portfolio_rebalancing_mapping.py`
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/mappers/portfolio_rebalancing_mapping.py`

#### `rebalance_instruction_dict_to_dto()` appears in 2 files:
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/allocation/portfolio_rebalancing_mapping.py`
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/mappers/portfolio_rebalancing_mapping.py`

#### `rebalance_execution_result_dict_to_dto()` appears in 2 files:
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/allocation/portfolio_rebalancing_mapping.py`
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/mappers/portfolio_rebalancing_mapping.py`

#### `safe_rebalancing_summary_dict_to_dto()` appears in 2 files:
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/allocation/portfolio_rebalancing_mapping.py`
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/mappers/portfolio_rebalancing_mapping.py`

#### `safe_rebalancing_impact_dict_to_dto()` appears in 2 files:
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/allocation/portfolio_rebalancing_mapping.py`
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/mappers/portfolio_rebalancing_mapping.py`

#### `validate_rebalancing_plan()` appears in 2 files:
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/allocation/rebalance_execution_service.py`
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/core/portfolio_management_facade.py`

#### `analyze_portfolio_drift()` appears in 2 files:
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/core/portfolio_management_facade.py`
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/core/portfolio_analysis_service.py`

#### `validate_and_adjust()` appears in 10 files:
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/buying_power_policy.py`
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/risk_policy.py`
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/fractionability_policy.py`
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/fractionability_policy_impl.py`
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/position_policy_impl.py`
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/position_policy.py`
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/buying_power_policy_impl.py`
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/policy_factory.py`
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/risk_policy_impl.py`
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/base_policy.py`

#### `is_fractionable()` appears in 2 files:
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/fractionability_policy.py`
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/fractionability_policy_impl.py`

#### `convert_to_whole_shares()` appears in 2 files:
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/fractionability_policy.py`
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/fractionability_policy_impl.py`

#### `policy_name()` appears in 10 files:
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/buying_power_policy.py`
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/risk_policy.py`
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/fractionability_policy.py`
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/fractionability_policy_impl.py`
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/position_policy_impl.py`
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/position_policy.py`
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/buying_power_policy_impl.py`
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/policy_factory.py`
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/risk_policy_impl.py`
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/base_policy.py`

#### `get_available_buying_power()` appears in 2 files:
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/buying_power_policy.py`
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/buying_power_policy_impl.py`

#### `estimate_order_value()` appears in 2 files:
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/buying_power_policy.py`
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/buying_power_policy_impl.py`

#### `calculate_risk_score()` appears in 2 files:
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/risk_policy_impl.py`
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/risk_policy.py`

#### `assess_position_concentration()` appears in 2 files:
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/risk_policy_impl.py`
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/risk_policy.py`

#### `validate_order_size()` appears in 2 files:
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/risk_policy_impl.py`
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/risk_policy.py`

#### `max_risk_score()` appears in 2 files:
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/risk_policy_impl.py`
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/risk_policy.py`

#### `get_available_position()` appears in 2 files:
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/position_policy_impl.py`
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/position_policy.py`

#### `validate_sell_quantity()` appears in 2 files:
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/position_policy_impl.py`
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/position_policy.py`

#### `classify_symbol()` appears in 2 files:
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/state/symbol_classifier.py`
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/state/attribution_engine.py`

#### `get_symbols_for_strategy()` appears in 2 files:
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/state/symbol_classifier.py`
- `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/state/attribution_engine.py`


### Exact Duplicates (100% AST Match)


#### `from_dict()` Duplication
- **File 1**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/holdings/position_model.py` (line 29)
- **File 2**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/mappers/position.py` (line 29)
- **Similarity**: 100% (identical AST)
- **Impact**: Complete code duplication


#### `to_dict()` Duplication
- **File 1**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/holdings/position_model.py` (line 42)
- **File 2**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/mappers/position.py` (line 42)
- **Similarity**: 100% (identical AST)
- **Impact**: Complete code duplication


#### `is_profitable()` Duplication
- **File 1**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/holdings/position_model.py` (line 56)
- **File 2**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/mappers/position.py` (line 56)
- **Similarity**: 100% (identical AST)
- **Impact**: Complete code duplication


#### `percentage_return()` Duplication
- **File 1**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/holdings/position_model.py` (line 61)
- **File 2**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/mappers/position.py` (line 61)
- **Similarity**: 100% (identical AST)
- **Impact**: Complete code duplication


#### `shares_count()` Duplication
- **File 1**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/holdings/position_model.py` (line 66)
- **File 2**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/mappers/position.py` (line 66)
- **Similarity**: 100% (identical AST)
- **Impact**: Complete code duplication


#### `is_long()` Duplication
- **File 1**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/holdings/position_model.py` (line 71)
- **File 2**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/mappers/position.py` (line 71)
- **Similarity**: 100% (identical AST)
- **Impact**: Complete code duplication


#### `is_short()` Duplication
- **File 1**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/holdings/position_model.py` (line 76)
- **File 2**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/mappers/position.py` (line 76)
- **Similarity**: 100% (identical AST)
- **Impact**: Complete code duplication


#### `average_cost()` Duplication
- **File 1**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/holdings/position_model.py` (line 81)
- **File 2**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/mappers/position.py` (line 81)
- **Similarity**: 100% (identical AST)
- **Impact**: Complete code duplication


#### `_to_decimal()` Duplication
- **File 1**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/holdings/position_mapping.py` (line 21)
- **File 2**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/mappers/position_mapping.py` (line 21)
- **Similarity**: 100% (identical AST)
- **Impact**: Complete code duplication


#### `alpaca_position_to_summary()` Duplication
- **File 1**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/holdings/position_mapping.py` (line 30)
- **File 2**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/mappers/position_mapping.py` (line 30)
- **Similarity**: 100% (identical AST)
- **Impact**: Complete code duplication


#### `_get_current_position_values()` Duplication
- **File 1**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/allocation/portfolio_rebalancing_service.py` (line 362)
- **File 2**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/core/portfolio_analysis_service.py` (line 287)
- **Similarity**: 100% (identical AST)
- **Impact**: Complete code duplication


#### `dto_to_domain_rebalance_plan()` Duplication
- **File 1**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/allocation/portfolio_rebalancing_mapping.py` (line 43)
- **File 2**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/mappers/portfolio_rebalancing_mapping.py` (line 42)
- **Similarity**: 100% (identical AST)
- **Impact**: Complete code duplication


#### `dto_plans_to_domain()` Duplication
- **File 1**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/allocation/portfolio_rebalancing_mapping.py` (line 62)
- **File 2**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/mappers/portfolio_rebalancing_mapping.py` (line 61)
- **Similarity**: 100% (identical AST)
- **Impact**: Complete code duplication


#### `rebalance_plans_dict_to_collection_dto()` Duplication
- **File 1**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/allocation/portfolio_rebalancing_mapping.py` (line 67)
- **File 2**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/mappers/portfolio_rebalancing_mapping.py` (line 66)
- **Similarity**: 100% (identical AST)
- **Impact**: Complete code duplication


#### `rebalancing_summary_dict_to_dto()` Duplication
- **File 1**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/allocation/portfolio_rebalancing_mapping.py` (line 92)
- **File 2**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/mappers/portfolio_rebalancing_mapping.py` (line 91)
- **Similarity**: 100% (identical AST)
- **Impact**: Complete code duplication


#### `rebalancing_impact_dict_to_dto()` Duplication
- **File 1**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/allocation/portfolio_rebalancing_mapping.py` (line 109)
- **File 2**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/mappers/portfolio_rebalancing_mapping.py` (line 108)
- **Similarity**: 100% (identical AST)
- **Impact**: Complete code duplication


#### `rebalance_instruction_dict_to_dto()` Duplication
- **File 1**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/allocation/portfolio_rebalancing_mapping.py` (line 127)
- **File 2**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/mappers/portfolio_rebalancing_mapping.py` (line 126)
- **Similarity**: 100% (identical AST)
- **Impact**: Complete code duplication


#### `rebalance_execution_result_dict_to_dto()` Duplication
- **File 1**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/allocation/portfolio_rebalancing_mapping.py` (line 140)
- **File 2**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/mappers/portfolio_rebalancing_mapping.py` (line 139)
- **Similarity**: 100% (identical AST)
- **Impact**: Complete code duplication


#### `safe_rebalancing_summary_dict_to_dto()` Duplication
- **File 1**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/allocation/portfolio_rebalancing_mapping.py` (line 170)
- **File 2**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/mappers/portfolio_rebalancing_mapping.py` (line 169)
- **Similarity**: 100% (identical AST)
- **Impact**: Complete code duplication


#### `safe_rebalancing_impact_dict_to_dto()` Duplication
- **File 1**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/allocation/portfolio_rebalancing_mapping.py` (line 194)
- **File 2**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/mappers/portfolio_rebalancing_mapping.py` (line 193)
- **Similarity**: 100% (identical AST)
- **Impact**: Complete code duplication


#### `policy_name()` Duplication
- **File 1**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/fractionability_policy.py` (line 63)
- **File 2**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/base_policy.py` (line 38)
- **Similarity**: 100% (identical AST)
- **Impact**: Complete code duplication


#### `policy_name()` Duplication
- **File 1**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/fractionability_policy.py` (line 63)
- **File 2**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/buying_power_policy.py` (line 85)
- **Similarity**: 100% (identical AST)
- **Impact**: Complete code duplication


#### `policy_name()` Duplication
- **File 1**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/fractionability_policy.py` (line 63)
- **File 2**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/position_policy.py` (line 78)
- **Similarity**: 100% (identical AST)
- **Impact**: Complete code duplication


#### `policy_name()` Duplication
- **File 1**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/fractionability_policy.py` (line 63)
- **File 2**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/risk_policy.py` (line 88)
- **Similarity**: 100% (identical AST)
- **Impact**: Complete code duplication


#### `policy_name()` Duplication
- **File 1**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/base_policy.py` (line 38)
- **File 2**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/buying_power_policy.py` (line 85)
- **Similarity**: 100% (identical AST)
- **Impact**: Complete code duplication


#### `policy_name()` Duplication
- **File 1**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/base_policy.py` (line 38)
- **File 2**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/position_policy.py` (line 78)
- **Similarity**: 100% (identical AST)
- **Impact**: Complete code duplication


#### `policy_name()` Duplication
- **File 1**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/base_policy.py` (line 38)
- **File 2**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/risk_policy.py` (line 88)
- **Similarity**: 100% (identical AST)
- **Impact**: Complete code duplication


#### `policy_name()` Duplication
- **File 1**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/buying_power_policy.py` (line 85)
- **File 2**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/position_policy.py` (line 78)
- **Similarity**: 100% (identical AST)
- **Impact**: Complete code duplication


#### `policy_name()` Duplication
- **File 1**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/buying_power_policy.py` (line 85)
- **File 2**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/risk_policy.py` (line 88)
- **Similarity**: 100% (identical AST)
- **Impact**: Complete code duplication


#### `policy_name()` Duplication
- **File 1**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/position_policy.py` (line 78)
- **File 2**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/risk_policy.py` (line 88)
- **Similarity**: 100% (identical AST)
- **Impact**: Complete code duplication


#### `policy_name()` Duplication
- **File 1**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/fractionability_policy_impl.py` (line 219)
- **File 2**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/buying_power_policy_impl.py` (line 293)
- **Similarity**: 100% (identical AST)
- **Impact**: Complete code duplication


#### `policy_name()` Duplication
- **File 1**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/fractionability_policy_impl.py` (line 219)
- **File 2**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/risk_policy_impl.py` (line 356)
- **Similarity**: 100% (identical AST)
- **Impact**: Complete code duplication


#### `policy_name()` Duplication
- **File 1**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/fractionability_policy_impl.py` (line 219)
- **File 2**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/position_policy_impl.py` (line 315)
- **Similarity**: 100% (identical AST)
- **Impact**: Complete code duplication


#### `policy_name()` Duplication
- **File 1**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/buying_power_policy_impl.py` (line 293)
- **File 2**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/risk_policy_impl.py` (line 356)
- **Similarity**: 100% (identical AST)
- **Impact**: Complete code duplication


#### `policy_name()` Duplication
- **File 1**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/buying_power_policy_impl.py` (line 293)
- **File 2**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/position_policy_impl.py` (line 315)
- **Similarity**: 100% (identical AST)
- **Impact**: Complete code duplication


#### `policy_name()` Duplication
- **File 1**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/risk_policy_impl.py` (line 356)
- **File 2**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/position_policy_impl.py` (line 315)
- **Similarity**: 100% (identical AST)
- **Impact**: Complete code duplication


#### `validate_and_adjust()` Duplication
- **File 1**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/policy_factory.py` (line 107)
- **File 2**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/policy_factory.py` (line 115)
- **Similarity**: 100% (identical AST)
- **Impact**: Complete code duplication


#### `validate_and_adjust()` Duplication
- **File 1**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/policy_factory.py` (line 107)
- **File 2**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/policy_factory.py` (line 123)
- **Similarity**: 100% (identical AST)
- **Impact**: Complete code duplication


#### `validate_and_adjust()` Duplication
- **File 1**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/policy_factory.py` (line 115)
- **File 2**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/policy_factory.py` (line 123)
- **Similarity**: 100% (identical AST)
- **Impact**: Complete code duplication


#### `validate_strategy()` Duplication
- **File 1**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/schemas/tracking.py` (line 98)
- **File 2**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/schemas/tracking.py` (line 386)
- **Similarity**: 100% (identical AST)
- **Impact**: Complete code duplication

### Near Duplicates (80-99% Similarity)


#### `total_return_pct()` vs `total_return_pct()` - 90.4% Similar
- **File 1**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/pnl/strategy_order_tracker.py` (line 146)
- **File 2**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/schemas/tracking.py` (line 434)
- **Similarity Score**: 0.904
- **Analysis**: Similar structure with minor variations


#### `is_long()` vs `is_short()` - 90.0% Similar
- **File 1**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/holdings/position_model.py` (line 71)
- **File 2**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/holdings/position_model.py` (line 76)
- **Similarity Score**: 0.900
- **Analysis**: Similar structure with minor variations


#### `is_long()` vs `is_short()` - 90.0% Similar
- **File 1**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/holdings/position_model.py` (line 71)
- **File 2**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/mappers/position.py` (line 76)
- **Similarity Score**: 0.900
- **Analysis**: Similar structure with minor variations


#### `is_short()` vs `is_long()` - 90.0% Similar
- **File 1**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/holdings/position_model.py` (line 76)
- **File 2**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/mappers/position.py` (line 71)
- **Similarity Score**: 0.900
- **Analysis**: Similar structure with minor variations


#### `filter_actionable_deltas()` vs `get_sell_deltas()` - 84.6% Similar
- **File 1**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/holdings/position_analyzer.py` (line 92)
- **File 2**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/holdings/position_analyzer.py` (line 98)
- **Similarity Score**: 0.846
- **Analysis**: Similar structure with minor variations


#### `filter_actionable_deltas()` vs `get_buy_deltas()` - 84.6% Similar
- **File 1**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/holdings/position_analyzer.py` (line 92)
- **File 2**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/holdings/position_analyzer.py` (line 104)
- **Similarity Score**: 0.846
- **Analysis**: Similar structure with minor variations


#### `get_sell_deltas()` vs `get_buy_deltas()` - 90.3% Similar
- **File 1**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/holdings/position_analyzer.py` (line 98)
- **File 2**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/holdings/position_analyzer.py` (line 104)
- **Similarity Score**: 0.903
- **Analysis**: Similar structure with minor variations


#### `get_positions_to_sell()` vs `get_positions_to_buy()` - 89.5% Similar
- **File 1**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/holdings/position_analyzer.py` (line 164)
- **File 2**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/holdings/position_analyzer.py` (line 176)
- **Similarity Score**: 0.895
- **Analysis**: Similar structure with minor variations


#### `is_buy()` vs `is_sell()` - 86.0% Similar
- **File 1**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/holdings/position_delta.py` (line 36)
- **File 2**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/holdings/position_delta.py` (line 41)
- **Similarity Score**: 0.860
- **Analysis**: Similar structure with minor variations


#### `quantity_abs()` vs `trade_amount_abs()` - 82.9% Similar
- **File 1**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/holdings/position_delta.py` (line 46)
- **File 2**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/allocation/rebalance_plan.py` (line 39)
- **Similarity Score**: 0.829
- **Analysis**: Similar structure with minor variations


#### `_to_decimal()` vs `_to_decimal()` - 84.6% Similar
- **File 1**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/holdings/position_mapping.py` (line 21)
- **File 2**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/calculations/portfolio_calculations.py` (line 24)
- **Similarity Score**: 0.846
- **Analysis**: Similar structure with minor variations


#### `_to_decimal()` vs `_to_decimal()` - 84.6% Similar
- **File 1**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/calculations/portfolio_calculations.py` (line 24)
- **File 2**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/mappers/position_mapping.py` (line 21)
- **Similarity Score**: 0.846
- **Analysis**: Similar structure with minor variations


#### `create_strategy_aware_order_callback()` vs `wrapper()` - 88.3% Similar
- **File 1**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/tracking/integration.py` (line 113)
- **File 2**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/tracking/integration.py` (line 116)
- **Similarity Score**: 0.883
- **Analysis**: Similar structure with minor variations


#### `__init__()` vs `__init__()` - 80.0% Similar
- **File 1**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/allocation/portfolio_rebalancing_service.py` (line 49)
- **File 2**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/core/portfolio_analysis_service.py` (line 28)
- **Similarity Score**: 0.800
- **Analysis**: Similar structure with minor variations


#### `get_symbols_requiring_sells()` vs `get_symbols_requiring_buys()` - 89.2% Similar
- **File 1**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/allocation/portfolio_rebalancing_service.py` (line 237)
- **File 2**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/allocation/portfolio_rebalancing_service.py` (line 251)
- **Similarity Score**: 0.892
- **Analysis**: Similar structure with minor variations


#### `_get_current_position_values()` vs `get_current_positions()` - 93.9% Similar
- **File 1**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/allocation/portfolio_rebalancing_service.py` (line 362)
- **File 2**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/core/portfolio_management_facade.py` (line 462)
- **Similarity Score**: 0.939
- **Analysis**: Similar structure with minor variations


#### `get_sell_plans()` vs `get_buy_plans()` - 89.5% Similar
- **File 1**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/allocation/rebalance_calculator.py` (line 76)
- **File 2**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/allocation/rebalance_calculator.py` (line 84)
- **Similarity Score**: 0.895
- **Analysis**: Similar structure with minor variations


#### `_place_sell_order()` vs `_place_buy_order()` - 93.3% Similar
- **File 1**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/allocation/rebalance_execution_service.py` (line 354)
- **File 2**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/allocation/rebalance_execution_service.py` (line 404)
- **Similarity Score**: 0.933
- **Analysis**: Similar structure with minor variations


#### `get_portfolio_analysis()` vs `get_strategy_performance()` - 82.2% Similar
- **File 1**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/core/portfolio_management_facade.py` (line 83)
- **File 2**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/core/portfolio_management_facade.py` (line 91)
- **Similarity Score**: 0.822
- **Analysis**: Similar structure with minor variations


#### `get_rebalancing_summary()` vs `estimate_rebalancing_impact()` - 81.7% Similar
- **File 1**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/core/portfolio_management_facade.py` (line 117)
- **File 2**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/core/portfolio_management_facade.py` (line 127)
- **Similarity Score**: 0.817
- **Analysis**: Similar structure with minor variations


#### `get_symbols_to_sell()` vs `get_symbols_to_buy()` - 87.5% Similar
- **File 1**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/core/portfolio_management_facade.py` (line 137)
- **File 2**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/core/portfolio_management_facade.py` (line 141)
- **Similarity Score**: 0.875
- **Analysis**: Similar structure with minor variations


#### `get_current_portfolio_value()` vs `_get_portfolio_value()` - 86.0% Similar
- **File 1**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/core/portfolio_management_facade.py` (line 457)
- **File 2**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/core/portfolio_analysis_service.py` (line 300)
- **Similarity Score**: 0.860
- **Analysis**: Similar structure with minor variations


#### `get_current_positions()` vs `_get_current_position_values()` - 93.9% Similar
- **File 1**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/core/portfolio_management_facade.py` (line 462)
- **File 2**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/core/portfolio_analysis_service.py` (line 287)
- **Similarity Score**: 0.939
- **Analysis**: Similar structure with minor variations


#### `execute_sell_phase()` vs `execute_buy_phase()` - 82.4% Similar
- **File 1**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/core/rebalancing_orchestrator.py` (line 66)
- **File 2**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/core/rebalancing_orchestrator.py` (line 158)
- **Similarity Score**: 0.824
- **Analysis**: Similar structure with minor variations


#### `is_long()` vs `is_short()` - 90.0% Similar
- **File 1**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/mappers/position.py` (line 71)
- **File 2**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/mappers/position.py` (line 76)
- **Similarity Score**: 0.900
- **Analysis**: Similar structure with minor variations


#### `strategy_pnl_to_dict()` vs `dict_to_strategy_pnl_dict()` - 82.7% Similar
- **File 1**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/mappers/tracking_mapping.py` (line 130)
- **File 2**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/mappers/tracking_mapping.py` (line 143)
- **Similarity Score**: 0.827
- **Analysis**: Similar structure with minor variations


#### `strategy_pnl_to_dict()` vs `strategy_pnl_dto_to_dataclass_dict()` - 82.2% Similar
- **File 1**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/mappers/tracking_mapping.py` (line 130)
- **File 2**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/mappers/tracking_mapping.py` (line 265)
- **Similarity Score**: 0.822
- **Analysis**: Similar structure with minor variations


#### `dict_to_strategy_pnl_dict()` vs `strategy_pnl_dto_to_dataclass_dict()` - 81.3% Similar
- **File 1**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/mappers/tracking_mapping.py` (line 143)
- **File 2**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/mappers/tracking_mapping.py` (line 265)
- **Similarity Score**: 0.813
- **Analysis**: Similar structure with minor variations


#### `dto_to_domain_order_request()` vs `domain_order_request_to_dto()` - 84.4% Similar
- **File 1**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/mappers/policy_mapping.py` (line 29)
- **File 2**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/mappers/policy_mapping.py` (line 48)
- **Similarity Score**: 0.844
- **Analysis**: Similar structure with minor variations


#### `orchestrator_name()` vs `policy_name()` - 80.0% Similar
- **File 1**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/policy_orchestrator.py` (line 350)
- **File 2**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/fractionability_policy_impl.py` (line 219)
- **Similarity Score**: 0.800
- **Analysis**: Similar structure with minor variations


#### `orchestrator_name()` vs `policy_name()` - 80.0% Similar
- **File 1**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/policy_orchestrator.py` (line 350)
- **File 2**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/buying_power_policy_impl.py` (line 293)
- **Similarity Score**: 0.800
- **Analysis**: Similar structure with minor variations


#### `orchestrator_name()` vs `policy_name()` - 80.0% Similar
- **File 1**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/policy_orchestrator.py` (line 350)
- **File 2**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/risk_policy_impl.py` (line 356)
- **Similarity Score**: 0.800
- **Analysis**: Similar structure with minor variations


#### `orchestrator_name()` vs `policy_name()` - 80.0% Similar
- **File 1**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/policy_orchestrator.py` (line 350)
- **File 2**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/position_policy_impl.py` (line 315)
- **Similarity Score**: 0.800
- **Analysis**: Similar structure with minor variations


#### `policy_name()` vs `policy_name()` - 86.8% Similar
- **File 1**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/fractionability_policy.py` (line 63)
- **File 2**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/fractionability_policy_impl.py` (line 219)
- **Similarity Score**: 0.868
- **Analysis**: Similar structure with minor variations


#### `policy_name()` vs `policy_name()` - 86.8% Similar
- **File 1**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/fractionability_policy.py` (line 63)
- **File 2**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/buying_power_policy_impl.py` (line 293)
- **Similarity Score**: 0.868
- **Analysis**: Similar structure with minor variations


#### `policy_name()` vs `policy_name()` - 86.8% Similar
- **File 1**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/fractionability_policy.py` (line 63)
- **File 2**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/risk_policy_impl.py` (line 356)
- **Similarity Score**: 0.868
- **Analysis**: Similar structure with minor variations


#### `policy_name()` vs `policy_name()` - 86.8% Similar
- **File 1**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/fractionability_policy.py` (line 63)
- **File 2**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/position_policy_impl.py` (line 315)
- **Similarity Score**: 0.868
- **Analysis**: Similar structure with minor variations


#### `policy_name()` vs `policy_name()` - 86.8% Similar
- **File 1**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/fractionability_policy_impl.py` (line 219)
- **File 2**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/base_policy.py` (line 38)
- **Similarity Score**: 0.868
- **Analysis**: Similar structure with minor variations


#### `policy_name()` vs `policy_name()` - 86.8% Similar
- **File 1**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/fractionability_policy_impl.py` (line 219)
- **File 2**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/buying_power_policy.py` (line 85)
- **Similarity Score**: 0.868
- **Analysis**: Similar structure with minor variations


#### `policy_name()` vs `policy_name()` - 86.8% Similar
- **File 1**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/fractionability_policy_impl.py` (line 219)
- **File 2**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/position_policy.py` (line 78)
- **Similarity Score**: 0.868
- **Analysis**: Similar structure with minor variations


#### `policy_name()` vs `policy_name()` - 86.8% Similar
- **File 1**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/fractionability_policy_impl.py` (line 219)
- **File 2**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/risk_policy.py` (line 88)
- **Similarity Score**: 0.868
- **Analysis**: Similar structure with minor variations


#### `policy_name()` vs `policy_name()` - 86.8% Similar
- **File 1**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/buying_power_policy_impl.py` (line 293)
- **File 2**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/base_policy.py` (line 38)
- **Similarity Score**: 0.868
- **Analysis**: Similar structure with minor variations


#### `policy_name()` vs `policy_name()` - 86.8% Similar
- **File 1**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/buying_power_policy_impl.py` (line 293)
- **File 2**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/buying_power_policy.py` (line 85)
- **Similarity Score**: 0.868
- **Analysis**: Similar structure with minor variations


#### `policy_name()` vs `policy_name()` - 86.8% Similar
- **File 1**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/buying_power_policy_impl.py` (line 293)
- **File 2**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/position_policy.py` (line 78)
- **Similarity Score**: 0.868
- **Analysis**: Similar structure with minor variations


#### `policy_name()` vs `policy_name()` - 86.8% Similar
- **File 1**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/buying_power_policy_impl.py` (line 293)
- **File 2**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/risk_policy.py` (line 88)
- **Similarity Score**: 0.868
- **Analysis**: Similar structure with minor variations


#### `max_risk_score()` vs `max_risk_score()` - 85.7% Similar
- **File 1**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/risk_policy_impl.py` (line 351)
- **File 2**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/risk_policy.py` (line 83)
- **Similarity Score**: 0.857
- **Analysis**: Similar structure with minor variations


#### `policy_name()` vs `policy_name()` - 86.8% Similar
- **File 1**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/risk_policy_impl.py` (line 356)
- **File 2**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/base_policy.py` (line 38)
- **Similarity Score**: 0.868
- **Analysis**: Similar structure with minor variations


#### `policy_name()` vs `policy_name()` - 86.8% Similar
- **File 1**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/risk_policy_impl.py` (line 356)
- **File 2**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/buying_power_policy.py` (line 85)
- **Similarity Score**: 0.868
- **Analysis**: Similar structure with minor variations


#### `policy_name()` vs `policy_name()` - 86.8% Similar
- **File 1**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/risk_policy_impl.py` (line 356)
- **File 2**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/position_policy.py` (line 78)
- **Similarity Score**: 0.868
- **Analysis**: Similar structure with minor variations


#### `policy_name()` vs `policy_name()` - 86.8% Similar
- **File 1**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/risk_policy_impl.py` (line 356)
- **File 2**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/risk_policy.py` (line 88)
- **Similarity Score**: 0.868
- **Analysis**: Similar structure with minor variations


#### `policy_name()` vs `policy_name()` - 86.8% Similar
- **File 1**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/position_policy_impl.py` (line 315)
- **File 2**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/base_policy.py` (line 38)
- **Similarity Score**: 0.868
- **Analysis**: Similar structure with minor variations


#### `policy_name()` vs `policy_name()` - 86.8% Similar
- **File 1**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/position_policy_impl.py` (line 315)
- **File 2**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/buying_power_policy.py` (line 85)
- **Similarity Score**: 0.868
- **Analysis**: Similar structure with minor variations


#### `policy_name()` vs `policy_name()` - 86.8% Similar
- **File 1**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/position_policy_impl.py` (line 315)
- **File 2**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/position_policy.py` (line 78)
- **Similarity Score**: 0.868
- **Analysis**: Similar structure with minor variations


#### `policy_name()` vs `policy_name()` - 86.8% Similar
- **File 1**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/position_policy_impl.py` (line 315)
- **File 2**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/risk_policy.py` (line 88)
- **Similarity Score**: 0.868
- **Analysis**: Similar structure with minor variations


#### `is_nuclear_symbol()` vs `is_tecl_symbol()` - 88.7% Similar
- **File 1**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/state/symbol_classifier.py` (line 104)
- **File 2**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/state/symbol_classifier.py` (line 108)
- **Similarity Score**: 0.887
- **Analysis**: Similar structure with minor variations


#### `get_strategy_exposures()` vs `calculate_strategy_allocations()` - 84.5% Similar
- **File 1**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/state/attribution_engine.py` (line 163)
- **File 2**: `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/state/attribution_engine.py` (line 196)
- **Similarity Score**: 0.845
- **Analysis**: Similar structure with minor variations


### Duplicates Within Active Execution Path

The following duplicates appear within the traced `alchemiser trade` execution path:

1. **_get_current_position_values()** - Used in active execution path
2. **_place_sell_order()** - Used in active execution path
3. **get_portfolio_analysis()** - Used in active execution path
4. **get_rebalancing_summary()** - Used in active execution path
5. **get_symbols_to_sell()** - Used in active execution path
6. **get_current_portfolio_value()** - Used in active execution path
7. **get_current_positions()** - Used in active execution path


## Key Findings

### Portfolio Module Structure Analysis

- **Position Analysis Capability**: 67 functions across multiple files
- **Rebalancing Logic**: 60 functions handling portfolio rebalancing
- **P&L Tracking**: 48 functions for profit/loss analysis

- **Function Name Overlaps**: 46 function names appear in multiple files


### Architectural Observations

1. **Multiple Position Analysis Implementations**: The portfolio module contains multiple files handling position analysis, suggesting potential capability overlap.

2. **Rebalancing Logic Distribution**: Rebalancing functionality is spread across multiple files with similar naming patterns.

3. **P&L Calculation Redundancy**: Multiple files contain P&L calculation logic that may be duplicated.

## Recommendations

### Priority 1: Remove Exact Duplicates

The following exact duplicates should be consolidated immediately:

- Consolidate `from_dict()` from `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/holdings/position_model.py` and `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/mappers/position.py`
- Consolidate `to_dict()` from `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/holdings/position_model.py` and `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/mappers/position.py`
- Consolidate `is_profitable()` from `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/holdings/position_model.py` and `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/mappers/position.py`
- Consolidate `percentage_return()` from `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/holdings/position_model.py` and `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/mappers/position.py`
- Consolidate `shares_count()` from `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/holdings/position_model.py` and `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/mappers/position.py`
- Consolidate `is_long()` from `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/holdings/position_model.py` and `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/mappers/position.py`
- Consolidate `is_short()` from `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/holdings/position_model.py` and `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/mappers/position.py`
- Consolidate `average_cost()` from `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/holdings/position_model.py` and `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/mappers/position.py`
- Consolidate `_to_decimal()` from `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/holdings/position_mapping.py` and `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/mappers/position_mapping.py`
- Consolidate `alpaca_position_to_summary()` from `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/holdings/position_mapping.py` and `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/mappers/position_mapping.py`
- Consolidate `_get_current_position_values()` from `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/allocation/portfolio_rebalancing_service.py` and `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/core/portfolio_analysis_service.py`
- Consolidate `dto_to_domain_rebalance_plan()` from `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/allocation/portfolio_rebalancing_mapping.py` and `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/mappers/portfolio_rebalancing_mapping.py`
- Consolidate `dto_plans_to_domain()` from `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/allocation/portfolio_rebalancing_mapping.py` and `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/mappers/portfolio_rebalancing_mapping.py`
- Consolidate `rebalance_plans_dict_to_collection_dto()` from `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/allocation/portfolio_rebalancing_mapping.py` and `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/mappers/portfolio_rebalancing_mapping.py`
- Consolidate `rebalancing_summary_dict_to_dto()` from `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/allocation/portfolio_rebalancing_mapping.py` and `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/mappers/portfolio_rebalancing_mapping.py`
- Consolidate `rebalancing_impact_dict_to_dto()` from `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/allocation/portfolio_rebalancing_mapping.py` and `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/mappers/portfolio_rebalancing_mapping.py`
- Consolidate `rebalance_instruction_dict_to_dto()` from `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/allocation/portfolio_rebalancing_mapping.py` and `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/mappers/portfolio_rebalancing_mapping.py`
- Consolidate `rebalance_execution_result_dict_to_dto()` from `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/allocation/portfolio_rebalancing_mapping.py` and `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/mappers/portfolio_rebalancing_mapping.py`
- Consolidate `safe_rebalancing_summary_dict_to_dto()` from `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/allocation/portfolio_rebalancing_mapping.py` and `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/mappers/portfolio_rebalancing_mapping.py`
- Consolidate `safe_rebalancing_impact_dict_to_dto()` from `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/allocation/portfolio_rebalancing_mapping.py` and `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/mappers/portfolio_rebalancing_mapping.py`
- Consolidate `policy_name()` from `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/fractionability_policy.py` and `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/base_policy.py`
- Consolidate `policy_name()` from `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/fractionability_policy.py` and `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/buying_power_policy.py`
- Consolidate `policy_name()` from `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/fractionability_policy.py` and `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/position_policy.py`
- Consolidate `policy_name()` from `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/fractionability_policy.py` and `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/risk_policy.py`
- Consolidate `policy_name()` from `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/base_policy.py` and `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/buying_power_policy.py`
- Consolidate `policy_name()` from `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/base_policy.py` and `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/position_policy.py`
- Consolidate `policy_name()` from `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/base_policy.py` and `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/risk_policy.py`
- Consolidate `policy_name()` from `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/buying_power_policy.py` and `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/position_policy.py`
- Consolidate `policy_name()` from `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/buying_power_policy.py` and `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/risk_policy.py`
- Consolidate `policy_name()` from `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/position_policy.py` and `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/risk_policy.py`
- Consolidate `policy_name()` from `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/fractionability_policy_impl.py` and `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/buying_power_policy_impl.py`
- Consolidate `policy_name()` from `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/fractionability_policy_impl.py` and `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/risk_policy_impl.py`
- Consolidate `policy_name()` from `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/fractionability_policy_impl.py` and `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/position_policy_impl.py`
- Consolidate `policy_name()` from `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/buying_power_policy_impl.py` and `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/risk_policy_impl.py`
- Consolidate `policy_name()` from `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/buying_power_policy_impl.py` and `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/position_policy_impl.py`
- Consolidate `policy_name()` from `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/risk_policy_impl.py` and `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/position_policy_impl.py`
- Consolidate `validate_and_adjust()` from `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/policy_factory.py` and `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/policy_factory.py`
- Consolidate `validate_and_adjust()` from `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/policy_factory.py` and `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/policy_factory.py`
- Consolidate `validate_and_adjust()` from `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/policy_factory.py` and `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/policies/policy_factory.py`
- Consolidate `validate_strategy()` from `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/schemas/tracking.py` and `/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/portfolio/schemas/tracking.py`


### Priority 2: Review Function Name Overlaps

Consider refactoring or consolidating functions with identical names:

- `total_return_pct()` appears in 2 different files
- `__init__()` appears in 17 different files
- `from_dict()` appears in 2 different files
- `to_dict()` appears in 2 different files
- `is_profitable()` appears in 2 different files


### Priority 3: Architecture Improvements

1. **Consolidate Position Analysis**: Create a single, unified position analysis service
2. **Streamline Rebalancing Logic**: Establish clear separation between planning and execution  
3. **Centralize P&L Calculations**: Create shared P&L utility functions
4. **Improve Module Boundaries**: Ensure clear responsibilities for each portfolio submodule

## Impact Summary


- **Impact Level**: HIGH
- **Description**: Significant code duplication requiring immediate attention
- **Files Affected**: 34 out of 69 files show potential overlaps
- **Maintenance Risk**: High
- **Architectural Complexity**: High

### Specific Module Overlaps

- **Position Analysis**: 67 functions suggest potential consolidation opportunities
- **Rebalancing Logic**: 60 functions may indicate scattered responsibilities
- **P&L Calculations**: 48 functions could benefit from centralization


---

*Analysis completed on /home/runner/work/alchemiser-quant/alchemiser-quant using AST-based duplicate detection.*
*Portfolio module contains 69 files with 339 functions and 67 classes.*
