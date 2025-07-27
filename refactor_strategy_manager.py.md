# Refactor Plan for `strategy_manager.py`

## Current Issues
- Approximately 389 lines coordinating multiple strategies and tracking positions.
- Contains enumeration types, data classes, position tracking logic and CLI demo code in one file.
- Helper methods like `_get_strategy_portfolio_allocation` and `_update_position_tracking` are lengthy and intertwined.

## Goals
- Isolate data models, position tracking and management logic.
- Provide clear API for adding new strategies.
- Remove demo/`main()` code from the module.

## Proposed Modules & Files
- `strategies/manager.py` – high level class managing strategy execution order and allocations.
- `strategies/positions.py` – data classes for `StrategyPosition` and helpers for serialization.
- `strategies/performance.py` – summary and reporting utilities.
- Move CLI demo into `scripts/demo_strategy_manager.py`.

## Step-by-Step Refactor
1. **Create `positions.py`**
   - Define `StrategyPosition` dataclass with `to_dict` and `from_dict` functions.
   - Handle JSON serialization separately from manager code.

2. **Create `manager.py`**
   - Contains `StrategyManager` class with methods `run_all_strategies`, `update_positions` and `get_allocations`.
   - Takes `strategy_allocations` and a shared data provider on construction.
   - Uses helper functions from `positions.py` for tracking.

3. **Create `performance.py`**
   - Move `get_strategy_performance_summary` here and add functions to compute returns per strategy.

4. **Refactor Existing Module**
   - Update imports across the project to use `strategies.manager.StrategyManager`.
   - Remove the `main()` function from production code; keep example usage under `scripts/`.

5. **Add Tests**
   - `tests/strategies/test_manager.py` covering position tracking updates and allocation merging.

## Rationale
- Splitting data models and management logic simplifies reasoning about each responsibility.
- Externalizing the CLI demo prevents accidental execution in production environments.
- Modular design makes it easier to plug in additional strategies later on.

