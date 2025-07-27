# Refactor Plan for `test_backtest.py`

## Current Issues
- **Size**: ~946 lines containing both backtest implementation and test cases.
- **Mixed Concerns**: The file defines helper functions (`run_backtest`, `_preload_symbol_data`, etc.) and test suites together.
- **Deep Nesting and Inner Functions**: Backtest functions contain nested mock implementations making tests hard to follow.
- **Hardcoded Credentials and configuration manipulation**.

## Goals
- Separate reusable backtest logic from tests.
- Simplify tests using fixtures and parameterization.
- Remove hardcoded secrets.

## Proposed Modules & Files
- `backtest/engine.py` – move core backtest routines (`run_backtest`, `run_backtest_dual_rebalance`, etc.).
- `tests/backtest/test_backtest.py` – keep only pytest test functions, using fixtures to setup data.
- `tests/backtest/conftest.py` – define fixtures for data provider, temporary config and sample data.

## Step-by-Step Refactor
1. **Extract Backtest Logic**
   - Create `backtest/engine.py` with public functions:
     ```python
     def run_backtest(...):
         ...
     def run_backtest_dual_rebalance(...):
         ...
     def run_backtest_comparison(...):
         ...
     ```
   - These functions should not depend on pytest and should accept configuration parameters.

2. **Move Helper Functions**
   - `_preload_symbol_data`, `_calculate_slippage_cost`, `_add_market_noise`, `_get_realistic_execution_price` become private utilities in `backtest/utils.py`.
   - Replace nested mock functions with dependency injection or monkeypatch via fixtures.

3. **Redesign Tests**
   - Under `tests/backtest/test_backtest.py`, import functions from `backtest.engine`.
   - Use pytest fixtures for temporary config modifications instead of directly manipulating global config variables.
   - Parameterize tests for different price types and deposit scenarios.
   - Remove embedded printing and rely on assertions only.

4. **Credentials Handling**
   - Use environment variable fixtures or mocking to supply Alpaca keys instead of hardcoded values.

5. **Documentation**
   - Document usage of the new backtest engine in `README.md` under a Backtesting section.

## Rationale
- Separating backtest logic allows reuse by CLI commands and other tests.
- Pytest fixtures and parameterization reduce duplication and make tests clearer.
- Removing hardcoded credentials improves security and configurability.

