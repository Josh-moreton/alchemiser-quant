# Refactor Plan for `cli.py`

## Current Issues
- Over 560 lines containing Typer command definitions, progress display logic and direct interactions with trading modules.
- Long command functions such as `backtest` and `trade` perform heavy lifting themselves.
- Duplicated code for progress bars and status output.

## Goals
- Keep CLI layer thin – commands should delegate to service modules.
- Reuse common progress and console rendering utilities.
- Facilitate unit testing of command behaviour without running full strategies.

## Proposed Modules & Files
- `cli/commands/` – subpackage housing separate modules for trading, backtesting and deployment commands.
- `cli/progress.py` – wrappers for Rich progress/spinner utilities.
- Each command module imports from core services rather than implementing logic inline.

## Step-by-Step Refactor
1. **Create `cli/commands/trade.py`**
   - Implement `trade` command which instantiates the trading bot and triggers strategy execution.
   - Extract logic currently inside `@app.command('trade')`.

2. **Create `cli/commands/backtest.py`**
   - Move backtesting related commands (`backtest`, `backtest-dual`, `backtest-compare`, etc.) here.
   - Use functions from `backtest.engine` (see refactor plan for `test_backtest.py`).

3. **Create `cli/commands/deploy.py` and `cli/commands/status.py`**
   - House `deploy` and `status` implementations separately.

4. **Introduce `cli/progress.py`**
   - Provide helpers `run_with_spinner(message, func, *args)` and `progress_bar(iterable, description)` to reduce duplication.

5. **Simplify `cli.py`**
   - Configure Typer app and register commands from submodules:
     ```python
     app.add_typer(trade_app, name="trade")
     app.add_typer(backtest_app, name="backtest")
     ```
   - Keep `show_welcome` and `main()` only.

6. **Tests**
   - Add unit tests in `tests/cli/test_cli.py` using Typer's `CliRunner` to validate command wiring.

## Rationale
- Splitting commands into modules shortens each file and clarifies boundaries between CLI and business logic.
- Shared progress utilities eliminate repeated spinner setup.
- Smaller command functions make automated tests and future extensions easier.

