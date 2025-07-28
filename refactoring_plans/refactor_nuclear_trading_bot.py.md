# Refactor Plan for `nuclear_trading_bot.py`

## Current Issues
- ~409 lines mixing data fetching, indicator calculation, strategy evaluation, alerts and continuous execution loops.
- Reuses code from `strategy_engine.py` but also implements additional logic inline.
- Some methods like `run_continuous` contain long loops with logging and sleep logic.

## Goals
- Separate pure strategy logic from orchestration completely.
- Provide clear interfaces for data access and alerting.
- Allow easier unit testing of market analysis without running infinite loops.

## Proposed Modules & Files
- `strategies/nuclear/engine.py` – keep pure signal logic (already partly in `strategy_engine.py`).
- `strategies/nuclear/executor.py` – new module that orchestrates fetching data via `UnifiedDataProvider`, invoking the engine and producing orders.
- `strategies/nuclear/runner.py` – handles continuous scheduling (sleep loops) and alert dispatch.
- `alerts/alert_logger.py` – central module for logging and storing alert history.

## Step-by-Step Refactor
1. **Extract Execution Logic**
   - Move `get_market_data`, `calculate_indicators` and `evaluate_nuclear_strategy` into `strategies/nuclear/executor.py`.
   - Executor returns a portfolio recommendation plus any alerts.

2. **Refactor Continuous Mode**
   - Implement a generic `StrategyRunner` class (maybe in `strategies/runner.py`) which accepts an executor and interval.
   - `runner.run_once()` calls executor and logs results; `runner.run_continuous()` manages the loop.

3. **Use Alert Service**
   - Replace direct S3 or logging code with calls to `alerts/alert_logger.log_alert(alert)`.

4. **Slim Down `nuclear_trading_bot.py`**
   - Keep only code to wire together `UnifiedDataProvider`, `NuclearStrategyEngine`, `StrategyRunner` and CLI entry point.
   - Provide simple functions `run_once()` and `run_continuous()`.

5. **Tests**
   - Unit tests for `NuclearExecutor` verifying that indicator calculation uses `TechnicalIndicators` correctly and signals match expected scenarios.

## Rationale
- Decoupling orchestration from strategy logic simplifies reasoning about each part.
- A common runner pattern can be reused for TECL and other strategies.
- Alert logging centralization avoids duplicate code across strategies.

