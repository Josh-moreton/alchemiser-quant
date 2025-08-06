# Trading System Testing Framework - Usage Guide

## Overview

This comprehensive testing framework provides 146 tests across 6 phases of validation for the trading system. The framework is designed to ensure reliability, performance, and production readiness.

## Quick Start

### Running All Tests

```bash
# Run all 146 tests
pytest

# Run with coverage
pytest --cov=the_alchemiser --cov-report=html

# Run with detailed output
pytest -v
```

### Running Specific Test Categories

#### Phase 1-3: Core Testing

```bash
# Unit tests (36 tests)
pytest tests/unit/

# Integration tests (28 tests)
pytest tests/integration/

# Property-based tests (9 tests)
pytest tests/property/
```

#### Phase 4: Advanced Scenarios

```bash
# Market scenario tests (7 tests)
pytest tests/scenarios/

# Chaos engineering tests (8 tests)
pytest tests/chaos/
```

#### Phase 5: Performance Testing

```bash
# Performance benchmarks (4 tests)
pytest tests/performance/test_performance_benchmarks.py

# Load testing (3 tests)
pytest tests/performance/test_load_testing.py

# Stress testing (5 tests)
pytest tests/performance/test_stress_testing.py

# Scalability testing (2 tests)
pytest tests/performance/test_scalability_testing.py
```

#### Phase 6: Production Readiness

```bash
# Production monitoring (8 tests)
pytest tests/monitoring/

# Regression testing (4 tests)
pytest tests/regression/

# Deployment validation (7 tests)
pytest tests/deployment/
```

## Test Categories Explained

### 1. Unit Tests (36 tests)

**Purpose**: Validate individual components and functions
**When to Run**:

- After every code change
- Before committing code
- During development

**Key Areas**:

- Trading mathematics (price calculations, position sizing)
- Portfolio management (rebalancing, allocation)
- Mock integration (AWS, Alpaca API mocking)

### 2. Integration Tests (28 tests)

**Purpose**: Validate component interactions and workflows
**When to Run**:

- Before feature releases
- After API changes
- Weekly integration testing

**Key Areas**:

- Signal generation pipelines
- Cash flow management
- API contract validation

### 3. Property-Based Tests (9 tests)

**Purpose**: Mathematical property validation using random inputs
**When to Run**:

- Before releases
- After mathematical formula changes
- Monthly comprehensive testing

**Key Areas**:

- Technical indicator properties
- Portfolio calculation invariants
- Financial mathematics validation

### 4. Market Scenario Tests (7 tests)

**Purpose**: Validate system behavior under market conditions
**When to Run**:

- Before production deployment
- After strategy changes
- Quarterly stress testing

**Key Areas**:

- Market crash scenarios
- Flash crash handling
- Bear market performance

### 5. Chaos Engineering Tests (8 tests)

**Purpose**: Test system resilience and failure handling
**When to Run**:

- Before production deployment
- After infrastructure changes
- Monthly resilience testing

**Key Areas**:

- API failure handling
- Network latency simulation
- Memory pressure testing

### 6. Performance Tests (15+ tests)

**Purpose**: Validate system performance and scalability
**When to Run**:

- Before production deployment
- After performance optimizations
- Weekly performance monitoring

**Key Areas**:

- Benchmark performance
- Load handling capacity
- Stress testing limits

### 7. Production Monitoring Tests (8 tests)

**Purpose**: Validate monitoring and alerting systems
**When to Run**:

- Before production deployment
- After monitoring changes
- Weekly monitoring validation

**Key Areas**:

- Metrics collection accuracy
- Alert rule processing
- System health monitoring

### 8. Regression Tests (4 tests)

**Purpose**: Prevent performance and functionality regressions
**When to Run**:

- Before each release
- After major changes
- Daily automated testing

**Key Areas**:

- Baseline comparison
- Performance regression detection
- Historical comparison validation

### 9. Deployment Validation Tests (7 tests)

**Purpose**: Ensure production deployment readiness
**When to Run**:

- Before production deployment
- After configuration changes
- Pre-deployment validation

**Key Areas**:

- AWS infrastructure validation
- Environment configuration
- System health checks

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Trading System Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v3
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install poetry
        poetry install
    
    - name: Run Core Tests (Phases 1-3)
      run: |
        poetry run pytest tests/unit/ tests/integration/ tests/property/ -v
    
    - name: Run Scenario Tests (Phase 4)
      run: |
        poetry run pytest tests/scenarios/ tests/chaos/ -v
    
    - name: Run Performance Tests (Phase 5)
      run: |
        poetry run pytest tests/performance/ -v
    
    - name: Run Production Tests (Phase 6)
      run: |
        poetry run pytest tests/monitoring/ tests/regression/ tests/deployment/ -v
```

### Pre-deployment Validation

```bash
#!/bin/bash
# pre-deploy-validation.sh

echo "Running pre-deployment validation..."

# Core functionality
pytest tests/unit/ tests/integration/ -x
if [ $? -ne 0 ]; then
    echo "❌ Core tests failed"
    exit 1
fi

# Performance validation
pytest tests/performance/test_performance_benchmarks.py -x
if [ $? -ne 0 ]; then
    echo "❌ Performance tests failed"
    exit 1
fi

# Production readiness
pytest tests/deployment/test_deployment_validation.py -x
if [ $? -ne 0 ]; then
    echo "❌ Deployment validation failed"
    exit 1
fi

echo "✅ All pre-deployment validations passed"
```

## Performance Baselines

### Expected Performance Metrics

```python
# Performance baselines for regression testing
PERFORMANCE_BASELINES = {
    "indicator_calculation_time": {
        "moving_average": 0.001,  # seconds per 1000 data points
        "rsi": 0.002,
        "bollinger_bands": 0.003
    },
    "portfolio_operations": {
        "rebalance_time": 0.01,  # seconds per rebalance
        "position_update": 0.001,  # seconds per position
        "value_calculation": 0.001
    },
    "api_performance": {
        "market_data_fetch": 1.0,  # seconds per request
        "order_execution": 0.5,
        "portfolio_sync": 2.0
    },
    "memory_usage": {
        "base_memory": 50.0,  # MB
        "per_strategy": 10.0,  # MB per strategy
        "per_position": 0.1   # MB per position
    }
}
```

## Troubleshooting

### Common Issues

1. **Mock Import Errors**

   ```bash
   # Install missing test dependencies
   pip install pytest-mock moto hypothesis
   ```

2. **AWS Credential Issues**

   ```bash
   # Set up test credentials
   export AWS_ACCESS_KEY_ID=test
   export AWS_SECRET_ACCESS_KEY=test
   export AWS_DEFAULT_REGION=us-east-1
   ```

3. **Memory Issues in Performance Tests**

   ```bash
   # Run with increased memory
   pytest tests/performance/ --maxfail=1 -x
   ```

4. **Timeout Issues**

   ```bash
   # Run with increased timeout
   pytest tests/performance/ --timeout=300
   ```

### Test Environment Setup

```bash
# Complete test environment setup
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
export TRADING_ENV=test
export LOG_LEVEL=DEBUG

# Install all test dependencies
poetry install --with dev,test

# Validate test environment
python -c "import pytest, hypothesis, moto; print('✅ Test environment ready')"
```

## Maintenance

### Monthly Tasks

- [ ] Update performance baselines
- [ ] Review and update chaos engineering scenarios
- [ ] Validate monitoring alert thresholds
- [ ] Check regression test coverage

### Quarterly Tasks

- [ ] Comprehensive performance analysis
- [ ] Market scenario validation
- [ ] Infrastructure resilience testing
- [ ] Documentation updates

### Annual Tasks

- [ ] Complete framework review
- [ ] Performance benchmark updates
- [ ] Test strategy optimization
- [ ] Framework modernization

## Framework Statistics

- **Total Tests**: 146
- **Code Coverage**: 90%+ (target)
- **Execution Time**: ~2-3 minutes (all tests)
- **Categories**: 9 distinct test categories
- **Phases**: 6 comprehensive validation phases
- **Dependencies**: pytest, hypothesis, moto, boto3, numpy

This framework provides comprehensive validation for production trading systems with automated testing, performance monitoring, and deployment validation.
