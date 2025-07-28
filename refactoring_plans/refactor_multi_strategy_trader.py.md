# Refactor Plan for `multi_strategy_trader.py`

## Current Issues
- ~508 lines extending `AlpacaTradingBot` with multi-strategy features.
- Handles execution, portfolio tracking, dashboard data saving and summary display all in one class.
- Several private helper methods performing file I/O and summary formatting.
- Some logic duplicates behaviour from `alpaca_trader.py` (e.g., rebalancing).

## Goals
- Separate execution coordination from reporting and persistence.
- Reuse portfolio rebalancing code extracted in `portfolio_rebalancer.py`.
- Simplify access to performance data through a service class.

## Proposed Modules & Files
- `execution/multi_strategy_executor.py` – orchestrates running multiple strategies and uses `PortfolioRebalancer`.
- `reports/performance_tracker.py` – responsible for saving dashboard data and producing summary dictionaries.
- `ui/multi_strategy_summary.py` – formatting and display utilities currently in `_create_execution_summary` and `display_multi_strategy_summary`.

## Step-by-Step Refactor
1. **Create `multi_strategy_executor.py`**
   - Class `MultiStrategyExecutor` receives `StrategyManager`, `OrderManager` and `PortfolioRebalancer`.
   - Method `execute()` returns an `ExecutionResult` similar to the current dataclass but without printing or saving.
   - Move `execute_multi_strategy` logic here.

2. **Create `performance_tracker.py`**
   - Functions to persist dashboard JSON to S3/local storage.
   - Track strategy signals and portfolio states after each run.

3. **Create `multi_strategy_summary.py`**
   - Pure formatting helpers converting an `ExecutionResult` to rich tables or plain strings.
   - Used by CLI or other UIs.

4. **Refactor `MultiStrategyAlpacaTrader`**
   - Become a thin wrapper that composes the above classes.
   - Replace `_save_dashboard_data`, `_create_execution_summary`, and `display_multi_strategy_summary` with calls to `performance_tracker` and `multi_strategy_summary`.

5. **Unit Tests**
   - Add tests for `MultiStrategyExecutor` using mocked strategies and order manager to ensure correct portfolio rebalance calls.

## Rationale
- Decoupling execution, persistence and presentation makes the codebase more modular and easier to extend with new strategies.
- Shared rebalancing logic avoids duplication between single-strategy and multi-strategy trading.

