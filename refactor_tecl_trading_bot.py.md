# Refactor Plan for `tecl_trading_bot.py`

## Current Issues
- ~330 lines handling TECL strategy orchestration, including indicator calculation, strategy evaluation and run loops.
- Much of the logic mirrors `nuclear_trading_bot.py` with slight variations.
- Continuous execution and alerting code mixed with strategy logic.

## Goals
- Share common runner and executor infrastructure with the nuclear strategy.
- Keep TECL-specific logic in a dedicated engine module.
- Reduce duplicate code for logging and data fetching.

## Proposed Modules & Files
- `strategies/tecl/engine.py` – pure strategy evaluation logic (already partly in `tecl_strategy_engine.py`).
- `strategies/tecl/executor.py` – fetches data, computes indicators and determines portfolio allocations.
- Reuse `strategies/nuclear/runner.py` from previous refactor for scheduling and alert handling.

## Step-by-Step Refactor
1. **Extract Execution Functions**
   - Move `get_market_data`, `calculate_indicators`, `evaluate_tecl_strategy` into `strategies/tecl/executor.py`.
   - Executor returns portfolio signals and alerts similar to nuclear counterpart.

2. **Use Shared Runner**
   - Replace `run_once` and `run_continuous` with calls to a generic `StrategyRunner` class.

3. **Simplify `tecl_trading_bot.py`**
   - Create small wrapper functions that instantiate the executor and runner.
   - Keep CLI or script entry point only.

4. **Unit Tests**
   - Add tests for TECL executor verifying correct asset allocation under various market regimes.

## Rationale
- Aligning TECL implementation with the nuclear strategy reduces maintenance effort.
- Clear separation of data retrieval, strategy evaluation and runtime looping will improve readability and testing.

