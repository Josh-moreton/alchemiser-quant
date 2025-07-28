# Refactor Plan for `tecl_strategy_engine.py`

## Current Issues
- ~322 lines containing TECL strategy logic mixed with data helper methods.
- Complex conditional branches for bull/bear regimes and sector rotation.
- Many magic numbers and indicator keys repeated inline.

## Goals
- Increase readability by extracting smaller functions and clear enumerations.
- Allow unit testing of each strategy component individually.
- Share common indicator utilities with other strategies.

## Proposed Modules & Files
- `strategies/tecl/constants.py` – define enums or constants for asset symbols and threshold values.
- `strategies/tecl/logic.py` – break down evaluation functions (`_evaluate_bull_market_path`, etc.) into separate classes or functions.
- `indicators/utils.py` – helper functions for RSI/MA calculations so they can be mocked or reused.

## Step-by-Step Refactor
1. **Introduce Constants Module**
   - Move hard-coded symbol lists and RSI thresholds to `constants.py`.
   - Reference these in the engine for clarity.

2. **Split Evaluation Logic**
   - Each of the private methods (`_evaluate_bull_market_path`, `_evaluate_bear_market_path`, etc.) becomes its own strategy component in `logic.py`.
   - Components return `(symbol_or_allocation, action, reason)` making them easy to unit test.

3. **Refactor `evaluate_tecl_strategy`**
   - Compose the above components and consolidate results.
   - Flatten deeply nested if-statements using early returns.

4. **Use Indicator Utilities**
   - Replace inline RSI/MA calculations with calls to `indicators.utils` so tests can focus on decision logic.

5. **Add Unit Tests**
   - One test per strategy component verifying behaviour under controlled indicator inputs.

## Rationale
- Constants and utilities reduce duplication and magic numbers.
- Smaller functions with clear inputs and outputs improve testability and maintainability.

