# Performance Testing Documentation

This directory contains lightweight performance benchmarks for The Alchemiser trading strategies to ensure no major regressions in execution timing and memory usage.

## Overview

The performance tests are designed to:
- Catch performance regressions in strategy execution
- Ensure strategy loops remain within acceptable timing thresholds
- Monitor memory usage stability during repeated operations
- Validate scalability as the number of strategies increases

## Test Categories

### Individual Strategy Performance (`test_strategy_performance.py`)

Tests individual strategy engines:

- **Nuclear Strategy**: Signal generation and validation performance
- **TECL Strategy**: Signal generation with market data processing
- **KLM Strategy**: Ensemble evaluation and variant performance

### Multi-Strategy Performance (`test_multi_strategy_performance.py`)

Tests strategy aggregation and management:

- **Multi-Strategy Generation**: Combined execution of all strategies
- **Signal Aggregation**: Performance of conflict resolution logic
- **Scalability**: Performance with different numbers of strategies
- **Memory Usage**: Stability during repeated operations

## Performance Thresholds

Current baseline thresholds (defined in `conftest.py`):

| Operation | Threshold | Rationale |
|-----------|-----------|-----------|
| Nuclear Signal Generation | 100ms | Fast technical analysis |
| TECL Signal Generation | 150ms | Volatility calculations |
| KLM Signal Generation | 500ms | Multiple variant ensemble |
| Multi-Strategy Generation | 800ms | All strategies combined |
| Signal Validation | 50ms | Simple validation logic |

### Baseline Methodology

Thresholds were established based on:
1. Current performance measurements on CI infrastructure
2. Real-time trading requirements (sub-second execution)
3. Safety margins to account for system variability
4. Scalability considerations for production deployment

## Running Performance Tests

### Local Execution

```bash
# Run all performance tests
make perf

# Run specific performance test categories
poetry run pytest tests/performance/test_strategy_performance.py -v
poetry run pytest tests/performance/test_multi_strategy_performance.py -v

# Run with detailed timing output
poetry run pytest tests/performance/ -v -s

# Run performance tests with coverage
poetry run pytest tests/performance/ --cov=the_alchemiser/domain/strategies
```

### CI Integration

Performance tests can be run in CI with:

```bash
# Optional performance check (non-blocking)
make perf-check

# Include in full test suite
make test-all
```

## Understanding Results

### Timing Measurements

- **Average Time**: Mean execution time across multiple runs
- **Maximum Time**: Worst-case execution time observed
- **Standard Deviation**: Consistency of performance across runs

### Failure Scenarios

Tests will fail if:
- Average execution time exceeds threshold
- Memory growth indicates memory leaks
- Performance variability is too high (high standard deviation)
- Scalability degradation is excessive (>5x slower with multiple strategies)

### Interpreting Failures

When performance tests fail:

1. **Check System Load**: Ensure CI/test environment isn't overloaded
2. **Compare Trends**: Look for gradual degradation vs sudden spikes
3. **Profile Code**: Use profiling tools to identify bottlenecks
4. **Review Changes**: Check recent commits for performance-impacting changes

## Maintenance

### Updating Thresholds

Thresholds should be updated when:
- Legitimate performance improvements allow tightening thresholds
- Infrastructure changes require threshold adjustments
- New features add necessary overhead

To update thresholds, modify `PERFORMANCE_THRESHOLDS` in `conftest.py`.

### Adding New Tests

When adding new strategies or major features:
1. Add corresponding performance tests
2. Establish baseline measurements
3. Set appropriate thresholds
4. Document expected performance characteristics

## Debugging Performance Issues

### Common Causes

- **Network Overhead**: Mock external API calls in performance tests
- **Data Processing**: Large datasets or inefficient pandas operations
- **Strategy Complexity**: Multiple variants or complex calculations
- **Memory Allocation**: Object creation in tight loops

### Profiling Tools

```bash
# Profile specific test
poetry run python -m cProfile -o profile.stats -m pytest tests/performance/test_strategy_performance.py::TestNuclearStrategyPerformance::test_nuclear_signal_generation_performance

# Memory profiling
poetry run python -m memory_profiler tests/performance/test_multi_strategy_performance.py
```

### Optimization Guidelines

1. **Cache Expensive Calculations**: Avoid recalculating indicators
2. **Batch Operations**: Process multiple symbols together
3. **Minimize Object Creation**: Reuse objects in loops
4. **Profile Before Optimizing**: Measure to identify actual bottlenecks

## Integration with Production Monitoring

These performance tests complement production monitoring:
- **Development**: Catch regressions before deployment
- **Staging**: Validate performance in production-like environment  
- **Production**: Monitor actual execution times and compare to baselines

The performance characteristics validated here should align with production SLA requirements for real-time trading operations.