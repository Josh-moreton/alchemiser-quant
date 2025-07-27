# Refactor Plan for `strategy_engine.py`

## Current Issues
- ~306 lines with numerous scenario classes for the nuclear strategy.
- Some classes share similar helper logic (checking RSI thresholds, combining portfolios) leading to duplication.
- Lack of clear separation between portfolio weighting methods and signal generation.

## Goals
- Create reusable strategy scenario components.
- Centralize volatility and RSI calculation helpers.
- Provide clean interface for the orchestration layer to request portfolio recommendations.

## Proposed Modules & Files
- `strategies/nuclear/scenarios/` – package containing individual scenario classes.
- `strategies/nuclear/utils.py` – common indicator utilities and portfolio weighting helpers.
- `strategies/nuclear/engine.py` – orchestrates scenarios and exposes `get_nuclear_portfolio`.

## Step-by-Step Refactor
1. **Move Scenario Classes**
   - Each scenario (`BearMarketStrategy`, `PrimaryOverboughtStrategy`, etc.) becomes its own module under `scenarios/`.
   - Export a base class `Scenario` defining `recommend(indicators)`.

2. **Extract Utilities**
   - Functions `_get_14_day_volatility`, `_bonds_stronger_than_psq`, etc. moved to `utils.py`.
   - Provide weighting helper `combine_with_inverse_volatility()`.

3. **Refactor `NuclearStrategyEngine`**
   - Keep only initialization and methods orchestrating scenarios.
   - Use a list of scenario instances executed in order of precedence.

4. **Simplify Data Structures**
   - Return structured objects representing portfolio recommendations rather than nested dicts.

5. **Tests**
   - Add unit tests per scenario verifying decisions given sample indicators.

## Rationale
- Breaking out scenarios clarifies the purpose of each and reduces duplication.
- Utility functions shared across scenarios avoid repeating indicator math.
- A modular engine makes it easier to adjust strategy logic without editing a monolithic file.

