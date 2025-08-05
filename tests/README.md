# The Alchemiser Testing Framework

## Overview

This comprehensive testing framework ensures reliability and accuracy of The Alchemiser trading system through multi-layered testing strategies.

## Architecture

```
tests/
├── unit/                     # Fast, isolated tests (✅ IMPLEMENTED)
├── integration/              # Component interaction tests
├── contract/                 # External API compatibility
├── property/                 # Property-based testing with hypothesis
├── simulation/               # Market scenario testing
├── infrastructure/           # AWS/deployment tests
├── utils/                    # Testing utilities
├── fixtures/                 # Test data fixtures
└── conftest.py              # Global pytest configuration
```

## Key Features

### ✅ Implemented

- **pytest** primary testing framework
- **pytest-mock** enhanced mocking capabilities (replaces unittest.mock)
- **hypothesis** property-based testing for edge cases
- **Comprehensive fixtures** for market data, portfolio states, and mock services
- **36 unit tests** covering trading math, portfolio logic, and core calculations
- **Mock integration** for Alpaca API, AWS services, and environment variables

### 🔄 In Progress

- Integration tests for component interactions
- Contract tests for external API validation
- Property-based testing for edge cases

### 📋 Planned

- Market scenario simulation framework
- Infrastructure and deployment testing
- Chaos engineering for resilience testing

## Quick Start

### Running Tests

```bash
# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=the_alchemiser

# Run specific test category
python -m pytest tests/unit/
python -m pytest tests/integration/

# Run with verbose output
python -m pytest -v

# Run tests in parallel
python -m pytest -n auto
```

### Writing Tests

#### Unit Tests with pytest-mock

```python
def test_alpaca_order_submission(mocker):
    """Test order submission with mocked Alpaca API."""
    # Use pytest-mock for clean mocking
    mock_client = mocker.patch('alpaca.trading.TradingClient')
    mock_client.return_value.submit_order.return_value = Mock(id="test_123")
    
    # Test your code
    result = trading_engine.place_order("AAPL", 100, "BUY")
    assert result.order_id == "test_123"
```

#### Using Global Fixtures

```python
def test_portfolio_rebalancing(mock_alpaca_client, sample_portfolio_value):
    """Test using global fixtures from conftest.py."""
    # mock_alpaca_client and sample_portfolio_value are automatically available
    portfolio = create_portfolio(sample_portfolio_value)
    assert portfolio.total_value == sample_portfolio_value
```

#### Property-Based Testing

```python
from hypothesis import given, strategies as st

@given(prices=st.lists(st.floats(min_value=1.0, max_value=1000.0), min_size=10))
def test_price_calculation_invariants(prices):
    """Test that price calculations maintain mathematical properties."""
    result = calculate_moving_average(prices, window=5)
    assert all(isinstance(x, float) for x in result)
    assert len(result) == len(prices) - 4  # Window adjustment
```

## Testing Dependencies

All testing dependencies are managed via poetry:

```toml
[tool.poetry.group.test.dependencies]
pytest = "^8.4.1"
pytest-mock = "^3.14.1"  # Enhanced mocking capabilities
pytest-cov = "^6.2.1"     # Coverage reporting
pytest-xdist = "^3.8.0"   # Parallel execution
pytest-timeout = "^2.4.0" # Test timeouts
pytest-asyncio = "^1.1.0" # Async test support
hypothesis = "^6.137.1"   # Property-based testing
```

## Available Fixtures

### Global Fixtures (conftest.py)

- `mock_alpaca_client` - Mocked Alpaca trading client
- `mock_aws_clients` - Mocked AWS service clients (S3, Secrets Manager, CloudWatch)
- `mock_environment_variables` - Standard environment variables for testing
- `sample_portfolio_value` - Standard portfolio value (Decimal("100000.00"))
- `test_symbols` - Standard symbol list ["SPY", "QQQ", "AAPL", "TSLA", "NVDA"]

### Market Data Fixtures

- `normal_market_conditions()` - Standard market data with typical volatility
- `gap_up_scenario()` - Market data with overnight gaps
- `missing_data_scenario()` - Market data with random missing bars
- `create_flash_crash_scenario()` - Extreme market volatility simulation

### Utility Functions

- `assert_decimal_equal()` - Assert Decimal values within tolerance
- `assert_allocation_valid()` - Validate portfolio allocations sum to 1.0
- `assert_no_negative_positions()` - Ensure no negative positions/cash

## Mock Strategy

### pytest-mock Advantages

We use **pytest-mock** instead of standard unittest.mock because it provides:

1. **Automatic cleanup** - No need for context managers or manual teardown
2. **Better integration** - Works seamlessly with pytest fixtures
3. **Cleaner syntax** - `mocker.patch()` vs `@mock.patch` decorators
4. **Enhanced features** - Built-in spy functionality and better error messages

### Example Mock Patterns

```python
# Patch with return value
def test_api_call(mocker):
    mock_api = mocker.patch('module.api_call')
    mock_api.return_value = {"status": "success"}
    
# Patch with side effects
def test_api_failure(mocker):
    mock_api = mocker.patch('module.api_call')
    mock_api.side_effect = [ConnectionError(), {"status": "success"}]
    
# Spy on existing functions
def test_function_calls(mocker):
    spy = mocker.spy(module, 'existing_function')
    result = module.existing_function(42)
    spy.assert_called_once_with(42)
```

## Coverage Goals

- **Line Coverage**: >90%
- **Branch Coverage**: >85%
- **Test Execution Time**: <2 minutes for full suite
- **Test Reliability**: 95%+ bug detection rate

## Best Practices

1. **Test Isolation** - Each test should be independent
2. **Descriptive Names** - Test names should describe the scenario being tested
3. **Mock External Dependencies** - Never make real API calls in tests
4. **Use Fixtures** - Leverage pytest fixtures for common test data
5. **Property Testing** - Use hypothesis for edge case discovery
6. **Performance** - Keep unit tests fast (<100ms each)

## Contributing

When adding new features:

1. Write tests first (TDD approach)
2. Ensure all existing tests pass
3. Add appropriate fixtures if needed
4. Update documentation for new test patterns
5. Aim for >90% coverage on new code

## Current Status

**Phase 1 Complete** ✅

- Core testing infrastructure implemented
- 36 unit tests passing
- pytest-mock integration functional
- Comprehensive fixture library
- Market data generation utilities

**Next: Phase 2** 🔄

- Integration tests for component interactions
- Contract tests for external APIs
- Property-based testing expansion

---

*This testing framework transforms The Alchemiser from "hope it works" to "know it works" with mathematical certainty.*
