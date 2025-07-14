# Refactoring Guide for `nuclear_trading_bot.py`

The following list summarizes potential improvements worth refactoring in `nuclear_trading_bot.py`.

## General Code Structure
- **Move dynamic imports** (`numpy`, `re`, `time`, `argparse`) out of functions and place them at the top of the module for clarity and efficiency.
- **Use data classes and type hints**. The project already uses `dataclasses` in the backtester; applying them to the `Alert` class and to function arguments/returns will improve readability and reliability.
- **Replace bare `except:` blocks** with specific exceptions and logging. Silent failures hide useful debug information and complicate testing.
- **Factor out repeated alert creation logic** in `handle_nuclear_portfolio_signal` into a helper method to reduce duplication.
- **Break up very long methods** (e.g. `handle_nuclear_portfolio_signal`, `_evaluate_bear_subgroup_1/2`, `get_current_portfolio_allocation`) into smaller functions to isolate responsibilities.

## Strategy Engine
- **Simplify indicator calculation** in `calculate_indicators` and remove duplication by iterating over indicator functions in a loop.
- **Centralize constant values** (RSI thresholds, moving‑average windows, default portfolio size) into configuration or module‑level constants.
- **Consider vectorizing volatility calculations** in `_get_14_day_volatility` using Pandas operations rather than explicit loops.
- **Remove duplicated logic** between `_evaluate_bear_subgroup_1` and `_evaluate_bear_subgroup_2`. Many conditions are nearly identical and could be expressed through a common helper.
- **Introduce enumerations** for action types (`BUY`, `HOLD`, etc.) and for special symbols (`NUCLEAR_PORTFOLIO`, `UVXY_BTAL_PORTFOLIO`) to avoid typos.

## Logging and Error Handling
- **Use a dedicated logger** (`logging.getLogger(__name__)`) rather than the root logger to allow more flexible logging configuration.
- **Ensure all caught exceptions are logged**, especially inside data retrieval and indicator functions.

## Performance and Reuse
- **Cache market data more intelligently** or consider asynchronous fetching if requests become a bottleneck.
- **Avoid recomputing indicators** in `get_current_portfolio_allocation` by reusing previously computed data when possible.

## Testing and Maintenance
- **Add unit tests** for strategy evaluation branches and for helper functions. Existing tests only cover backtesting.
- **Document method behavior** thoroughly with docstrings so that strategy logic is easier to maintain.

