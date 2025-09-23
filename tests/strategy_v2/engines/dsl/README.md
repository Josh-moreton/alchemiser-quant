# DSL Engine Test Suite

Comprehensive test suite for the Strategy v2 DSL engine using event-driven mocks and golden/snapshot testing.

## Overview

This test suite validates the DSL engine that processes Clojure strategy files (`.clj`) and produces portfolio allocations through an event-driven architecture.

### Test Coverage

- **Unit Tests**: Core DSL engine components (parser, evaluator, engine)
- **Integration Tests**: End-to-end evaluation through event-driven pipeline  
- **Property Tests**: Engine invariants (idempotency, correlation, state isolation)
- **Scenario Tests**: Different market conditions (normal, stress, edge cases)
- **Golden Tests**: Regression detection through snapshot comparison
- **Strategy Discovery**: Automatic testing of all CLJ files in the repository

## Running Tests

### Basic Test Execution

```bash
# Run all DSL engine tests
pytest tests/strategy_v2/engines/dsl/ -v

# Run specific test categories
pytest tests/strategy_v2/engines/dsl/ -m unit -v           # Unit tests only
pytest tests/strategy_v2/engines/dsl/ -m integration -v   # Integration tests only
pytest tests/strategy_v2/engines/dsl/ -m property -v      # Property-based tests only
pytest tests/strategy_v2/engines/dsl/ -m golden -v        # Golden/snapshot tests only
pytest tests/strategy_v2/engines/dsl/ -m strategy -v      # Strategy-specific tests only

# Run with output capture to see detailed results
pytest tests/strategy_v2/engines/dsl/ -v -s
```

### Test Components

#### 1. Unit Tests (`test_dsl_engine_unit.py`)
- S-expression parser functionality
- DSL engine initialization and event handling
- Error handling and edge cases

#### 2. Strategy Discovery (`test_strategy_discovery.py`)
- Automatic discovery of CLJ strategy files
- Content analysis and validation
- Parametrized testing across all strategies

#### 3. Scenario-Based Tests (`test_scenario_based.py`)
- Normal market conditions
- Stress scenarios (volatility spikes, gaps)
- Edge cases (out-of-order data, duplicates)
- Multi-symbol scenarios
- Property-based invariant testing

#### 4. Golden/Snapshot Tests (`test_golden_snapshots.py`)
- Regression detection through result comparison
- Deterministic evaluation validation
- Pipeline integration testing

## Strategy Files Tested

The test suite automatically discovers and tests all CLJ strategy files:

- `Grail.clj`
- `KLM.clj` 
- `Nuclear.clj`
- `Phoenix.clj`
- `Starburst.clj`
- `TECL.clj`
- `TQQQ-FLT.clj`

## Golden/Snapshot Testing

### Understanding Snapshots

Golden tests capture the exact behavior of strategy evaluations and compare against known-good results to detect regressions.

### Managing Snapshots

#### Initial Snapshot Creation
When running golden tests for the first time, snapshots will be automatically created:

```bash
pytest tests/strategy_v2/engines/dsl/test_golden_snapshots.py -v
```

Snapshots are stored in `tests/snapshots/` directory:
- `{strategy_name}_evaluation.json` - Individual strategy results
- `pipeline_results.json` - Pipeline integration results

#### Updating Snapshots

When strategy behavior intentionally changes, update snapshots:

```bash
# Regenerate all snapshots
REGENERATE_SNAPSHOTS=1 pytest tests/strategy_v2/engines/dsl/test_golden_snapshots.py::TestGoldenSnapshots::test_regenerate_snapshots_if_requested -v
```

#### Reviewing Snapshot Changes

Before committing snapshot changes:

1. Review the diff to understand what changed
2. Verify changes are intentional and correct
3. Update any related documentation

```bash
git diff tests/snapshots/
```

## Test Infrastructure

### Event-Driven Test Harness

The `DslTestHarness` provides:
- Mock event bus with event recording
- Deterministic market data with seeded randomness
- Virtual time control for time-based testing
- State isolation between test runs

```python
from tests.utils.test_harness import DslTestHarness

# Create harness with deterministic seed
harness = DslTestHarness("/path/to/repository", seed=42)

# Evaluate strategy
result = harness.evaluate_strategy("strategy.clj")

# Analyze results
print(f"Events generated: {len(result.all_events)}")
print(f"Success: {result.success}")
```

### Mock Market Data

The `MockMarketDataService` provides:
- Deterministic price and indicator data
- Realistic value ranges for different indicator types
- Cached results for consistent testing

### Scenario Generation

The `ScenarioGenerator` creates:
- Normal market scenarios with moderate volatility
- Stress scenarios with high volatility and events
- Edge cases with data quality issues
- Multi-symbol correlation scenarios

## Configuration

### pytest Configuration

Settings in `pytest.ini`:
- Test discovery patterns
- Marker definitions
- Output formatting

### Test Markers

- `unit`: Unit tests for individual components
- `integration`: End-to-end integration tests
- `property`: Property-based invariant tests
- `golden`: Golden/snapshot tests
- `slow`: Long-running tests
- `strategy`: Strategy-specific tests
- `dsl`: DSL engine tests
- `event_driven`: Event-driven architecture tests

### Running Specific Test Categories

```bash
# Fast tests only (exclude slow)
pytest tests/strategy_v2/engines/dsl/ -v -m "not slow"

# Integration and golden tests
pytest tests/strategy_v2/engines/dsl/ -v -m "integration or golden"

# Property-based tests only
pytest tests/strategy_v2/engines/dsl/ -v -m property
```

## Coverage and Quality Gates

### Code Coverage

Run tests with coverage reporting:

```bash
# Generate coverage report
pytest tests/strategy_v2/engines/dsl/ --cov=the_alchemiser.strategy_v2.engines.dsl --cov-report=term-missing --cov-report=html

# View HTML coverage report
open htmlcov/index.html
```

### Quality Thresholds

Tests enforce quality gates:
- Minimum code coverage (85% target)
- All CLJ files must be parseable
- Deterministic test results (no flakiness)
- Event correlation integrity

## Debugging Failed Tests

### Common Issues

1. **Parser Errors**: CLJ file syntax issues
   ```bash
   pytest tests/strategy_v2/engines/dsl/test_dsl_engine_unit.py::TestSexprParser -v -s
   ```

2. **Event Flow Issues**: Event-driven architecture problems
   ```bash
   pytest tests/strategy_v2/engines/dsl/test_scenario_based.py::TestEventDrivenWorkflow -v -s
   ```

3. **Snapshot Mismatches**: Behavioral changes detected
   ```bash
   pytest tests/strategy_v2/engines/dsl/test_golden_snapshots.py -v -s
   ```

### Verbose Output

For detailed debugging information:

```bash
# Maximum verbosity with output capture
pytest tests/strategy_v2/engines/dsl/ -vvv -s --tb=long

# Show local variables in tracebacks
pytest tests/strategy_v2/engines/dsl/ -v -s --tb=long --showlocals
```

## Adding New Tests

### Adding a New Strategy Test

1. Add the strategy CLJ file to the repository root
2. Tests will automatically discover and include it
3. Run the test suite to validate

### Adding New Scenarios

1. Extend `ScenarioGenerator` in `tests/utils/dsl_test_utils.py`
2. Add scenario test methods in `test_scenario_based.py`
3. Update documentation

### Adding New Property Tests

1. Add test methods to `TestDslEngineInvariants` in `test_scenario_based.py`
2. Use the `@pytest.mark.property` decorator
3. Focus on testing invariant properties of the engine

## Continuous Integration

### CI Configuration

The test suite is designed for CI environments:
- Deterministic results with seeded randomness
- No external dependencies (mocked market data)
- Configurable test timeouts
- Artifact generation (coverage reports, snapshots)

### Performance Considerations

- Unit tests: ~1-2 seconds per strategy
- Integration tests: ~5-10 seconds per scenario
- Golden tests: ~2-3 seconds per strategy
- Full suite: ~30-60 seconds total

## Troubleshooting

### Test Environment Issues

```bash
# Verify test environment
python -c "import pytest; print('pytest:', pytest.__version__)"
python -c "from the_alchemiser.strategy_v2.engines.dsl import DslEngine; print('DSL engine importable')"

# Check strategy file discovery
python -c "
from tests.utils.dsl_test_utils import StrategyDiscovery
from pathlib import Path
discovery = StrategyDiscovery(Path('.'))
files = discovery.discover_clj_files()
print(f'Found {len(files)} CLJ files:', [f.name for f in files])
"
```

### Common Error Solutions

1. **ImportError**: Ensure package is installed in development mode
   ```bash
   pip install -e .
   ```

2. **No CLJ files found**: Verify files exist in repository root
   ```bash
   ls -la *.clj
   ```

3. **Snapshot validation failures**: Check if behavior intentionally changed
   ```bash
   git diff tests/snapshots/
   ```

## Contributing

When contributing new tests:

1. Follow existing naming conventions
2. Add appropriate test markers
3. Include docstrings explaining test purpose
4. Update this documentation for new features
5. Ensure tests are deterministic and fast