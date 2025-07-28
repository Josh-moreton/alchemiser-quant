# Refactor Plan for `alpaca_trader.py`

## Current Issues
- **Size**: ~1067 lines with many responsibilities.
- **Responsibilities Mixed**: data access, order execution, portfolio rebalancing, CLI output and logging all in one class.
- **Large Methods**: e.g. `rebalance_portfolio` and `execute_nuclear_strategy` exceed several hundred lines and contain deeply nested logic.
- **Duplicated Logic**: Order placement and settlement handling repeated with similar patterns.

## Goals
- Separate concerns for easier maintenance and testing.
- Reduce method size and cyclomatic complexity.
- Make trading utilities reusable by other components.

## Proposed Modules & Files
- `execution/order_manager.py` – handle order placement, dynamic limit logic and settlement waiting.
- `execution/portfolio_rebalancer.py` – encapsulate portfolio rebalance flow.
- `ui/trading_cli.py` – move all rich/console rendering functions.
- `utils/trading_math.py` – utility functions like `calculate_position_size` and `calculate_dynamic_limit_price`.
- Keep `alpaca_trader.py` focused on high level orchestration using the above components.

## Step-by-Step Refactor
1. **Create `execution/order_manager.py`**
   - Implement a class `OrderManager` with methods:
     ```python
     class OrderManager:
         def __init__(self, trading_client, data_provider, ignore_market_hours=False):
             ...
         def place_limit_or_market(...):
             ...  # moved logic from `place_order`
         def wait_for_settlement(...):
             ...
     ```
   - Move logic from `place_order` and `wait_for_settlement` here.
   - Provide hooks for slippage calculation from `utils/trading_math`.

2. **Create `utils/trading_math.py`**
   - Functions: `calculate_dynamic_limit_price`, `calculate_position_size`.
   - Unit-testable pure functions with no side effects.

3. **Create `execution/portfolio_rebalancer.py`**
   - Implement `PortfolioRebalancer` class which receives `OrderManager` and handles the workflow previously in `rebalance_portfolio`.
   - Break down into helper methods: `_build_order_plan`, `_execute_orders`, `_verify_allocations`.

4. **Create `ui/trading_cli.py`**
   - Move display related methods: `display_target_vs_current_allocations`, `check_allocation_discrepancies` and any print/render code.
   - These functions take simple data structures and return text/console objects.

5. **Slim down `AlpacaTradingBot`**
   - Keep only initialization, `get_account_info`, `get_positions`, `get_current_price`, and orchestration methods (`execute_nuclear_strategy` etc.).
   - Inject `OrderManager`, `PortfolioRebalancer`, and UI helpers via constructor.
   - Replace long inline logic with calls to these collaborators.

6. **Logging and Trade Recording**
   - Move JSON logging code in `log_trade_execution` to a helper module `utils/trade_logger.py` so it can be reused.

7. **Unit Tests**
   - Create tests for new utilities in `tests/test_trading_math.py` and `tests/test_order_manager.py` focusing on limit price calculations and order flow.

## Rationale
- Splitting responsibilities improves readability and testability.
- Pure utility functions make it easier to write unit tests without Alpaca dependencies.
- Smaller classes (`OrderManager`, `PortfolioRebalancer`) encapsulate complex workflows and allow reuse for multi-strategy trading.
- UI code separated from logic enables headless operation and potential web interfaces in the future.

