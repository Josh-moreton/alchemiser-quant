# Refactor Plan for `test_dynamic_pegging.py`

## Current Issues
- ~381 lines of complex test cases with custom helper classes and manual simulation of market scenarios.
- Test class mixes data structures, utility methods and high level scenarios.
- Many magic numbers and repeated setup code.

## Goals
- Organize tests by scenario with clear fixtures.
- Reuse helper functions between tests and actual trading code.
- Improve readability and maintainability of the test suite.

## Proposed Modules & Files
- `tests/pegging/helpers.py` – shared dataclasses and price simulation utilities.
- `tests/pegging/test_dynamic_pegging.py` – rewritten pytest file using fixtures and parameterization.
- `tests/pegging/data/` – optional sample data files for long scenarios.

## Step-by-Step Refactor
1. **Move Helper Classes**
   - `TestScenario` dataclass and fake quote/price utilities go to `helpers.py`.
   - Provide functions like `simulate_limit_order_steps()` reused by tests and trading code.

2. **Use Pytest Fixtures**
   - Create fixtures for `AlpacaTradingBot` mock, time mocking and scenario data.
   - Parameterize market conditions rather than hard-coding multiple methods.

3. **Simplify Assertions**
   - Focus each test on one behaviour (price progression, rebalancing, edge cases).
   - Use helper assertions from `helpers.py` to check expected results.

4. **Document Scenarios**
   - Include comments or README section inside `tests/pegging/` explaining how scenarios map to trading logic.

## Rationale
- Splitting helpers and using fixtures reduces duplicated setup and makes tests clearer.
- Parameterization allows extending the suite with new scenarios without bloating single functions.

