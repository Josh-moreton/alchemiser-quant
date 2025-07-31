# Refactoring Plan for `the_alchemiser/backtest/backtest_engine.py`

`backtest_engine.py` acts as a catch-all for data loading, strategy execution, CLI handling, and metric calculations. Breaking it apart will make the code easier to test and extend.

## Key Problems

- Configuration, strategy execution, metrics, and CLI parsing all live in a single 1100+ line script.
- Duplicated imports and large blocks of code hinder readability and maintenance.

## Proposed Package Layout

1. **`backtest/engine.py`** – Core `BacktestEngine` class orchestrating runs.
2. **`backtest/data_loader.py`** – Load and cache historical price data.
3. **`backtest/metrics.py`** – Performance metric calculations (CAGR, Sharpe ratio, etc.).
4. **`backtest/cli.py`** – Command-line interface and argument parsing.
5. **`backtest/strategies/`** – Strategy wrappers or adapters for individual strategies.
6. **Concurrency utilities** – Separate module for thread or process pool management.

## Additional Improvements

- Convert free functions into methods on `BacktestEngine` (e.g., `run_individual_strategy`).
- Introduce configuration dataclasses for engine settings and results.
- Make modules individually testable, including metrics and data loading.
- Add integration tests to verify CLI outputs.
