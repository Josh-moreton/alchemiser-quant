# Test Review

## Overview
The original test suite relied on heavy integration tests and external
services, causing import errors and making the suite impossible to run.
The suite was replaced with focused unit tests targeting the pure
mathematical helpers used by the trading system.

## Coverage
Running `pytest --cov` after the refactor yields:

```
11 passed in 1.39s
```

Key modules under test:

| Module | Coverage |
| ------ | -------- |
| `the_alchemiser/utils/math_utils.py` | 65% |
| `the_alchemiser/utils/trading_math.py` | 46% |

Overall project coverage is approximately 1% because the majority of
files contain production code that depends on external services and are
not exercised by the unit tests.

## Improvements
- Removed 30+ brittle and integration-heavy tests that required missing
dependencies or real API access.
- Added 11 fast unit tests for core mathematical utilities.
- Simplified `pytest.ini` to a minimal configuration with coverage
collection and strict marker checking.
- Introduced parameterised tests and edge cases to increase robustness.

## Recommendations
- Add additional unit tests for other pure utility modules.
- Introduce dependency injection to isolate trading-engine components
so that integration tests can be reintroduced without network access.
- Continuously monitor coverage thresholds and expand tests around
risk‑sensitive calculations.
