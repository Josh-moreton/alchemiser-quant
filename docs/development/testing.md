# Testing Guide

Comprehensive guide to The Alchemiser's testing framework, coverage, and best practices.

## Test Suite Overview

The Alchemiser includes a robust test suite with 232+ tests across 12 test files, providing comprehensive coverage of trading logic, execution, and edge cases.

### Test Structure

```
tests/
├── test_alchemiser_trader_integration.py  # Main trading integration tests
├── test_alchemiser_trader.py.backup       # Legacy tests (reference)
├── test_cash_buying_power.py              # Cash management scenarios
├── test_edge_cases.py                     # Edge case handling
├── test_error_handling.py                 # Error scenarios and recovery
├── test_integration.py                    # End-to-end integration
├── test_market_conditions.py              # Various market scenarios
├── test_order_manager.py                  # Order placement and management
├── test_order_placement.py               # Order execution logic
├── test_portfolio_rebalancing.py         # Portfolio management
├── test_reporting_logging.py             # Reporting and notifications
├── test_simple_order_manager.py          # Basic order operations
├── test_strategy_engines.py              # Strategy logic testing
├── test_strategy_signals.py              # Signal generation
├── test_technical_indicators.py          # Indicator calculations
└── test_tecl_strategy_engine.py         # TECL strategy specific tests
```

## Running Tests

### Quick Test Execution

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=the_alchemiser

# Run specific test file
pytest tests/test_strategy_engines.py

# Run with verbose output
pytest -v
```

### Using Make Commands

```bash
# Run full test suite
make test

# Run tests with coverage report
make test-coverage

# Run specific category
make test-integration
make test-strategies
make test-execution
```

### Test Configuration

Tests are configured via `pytest.ini`:

```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    --strict-markers
    --disable-warnings
    --tb=short
markers =
    integration: Integration tests that require API access
    unit: Unit tests that run in isolation
    slow: Tests that take longer to execute
```

## Test Categories

### 1. Unit Tests

**Purpose**: Test individual components in isolation

**Examples**:

```python
def test_calculate_position_size():
    """Test position size calculation logic."""
    portfolio_value = 100000
    target_allocation = 0.25
    current_price = 150.00
    
    result = calculate_position_size(portfolio_value, target_allocation, current_price)
    expected_shares = int((portfolio_value * target_allocation) / current_price)
    
    assert result == expected_shares

def test_rsi_calculation():
    """Test RSI indicator calculation accuracy."""
    prices = [44, 44.34, 44.09, 44.15, 43.61, 44.33, 44.83, 45.85, 46.08, 45.89]
    
    rsi = calculate_rsi(prices, period=14)
    
    # Compare with known TradingView values
    assert abs(rsi - 70.53) < 0.1
```

### 2. Integration Tests

**Purpose**: Test component interactions and API integrations

**Examples**:

```python
@pytest.mark.integration
def test_full_trading_cycle():
    """Test complete signal generation to order execution."""
    trader = AlchemiserTradingBot(paper_trading=True)
    
    # Generate signals
    signals = trader.generate_multi_strategy_signals()
    assert signals is not None
    
    # Execute trades
    result = trader.execute_multi_strategy(signals)
    assert result.success
    assert len(result.orders) > 0

@pytest.mark.integration  
def test_alpaca_api_connectivity():
    """Verify Alpaca API credentials and connectivity."""
    client = AlpacaClient(paper_trading=True)
    
    account_info = client.get_account_info()
    assert account_info['account_id'] is not None
    assert 'portfolio_value' in account_info
```

### 3. Market Condition Tests

**Purpose**: Test behavior under various market scenarios

**Examples**:

```python
def test_bear_market_scenario():
    """Test strategy behavior during bear market conditions."""
    indicators = {
        'RSI_14': 25.0,  # Oversold
        'VIX': 35.0,     # High volatility
        'SMA_20': 150.0,
        'Current_Price': 140.0  # Below moving average
    }
    
    strategy = NuclearStrategyEngine()
    portfolio = strategy.evaluate_nuclear_strategy(indicators)
    
    # Should be defensive
    assert portfolio.get('BIL', 0) >= 0.5  # At least 50% in treasury bills
    assert portfolio.get('UVXY', 0) >= 0.2  # Volatility hedge
    
def test_bull_market_scenario():
    """Test strategy behavior during bull market conditions."""
    indicators = {
        'RSI_14': 75.0,  # Overbought but bullish
        'VIX': 12.0,     # Low volatility
        'SMA_20': 150.0,
        'Current_Price': 165.0  # Above moving average
    }
    
    strategy = NuclearStrategyEngine()
    portfolio = strategy.evaluate_nuclear_strategy(indicators)
    
    # Should be growth-oriented
    assert any(symbol in ['TQQQ', 'TECL', 'SPXL'] for symbol in portfolio.keys())
```

### 4. Error Handling Tests

**Purpose**: Verify graceful error handling and recovery

**Examples**:

```python
def test_insufficient_buying_power():
    """Test handling of insufficient buying power."""
    with patch('alpaca_client.place_order') as mock_order:
        mock_order.side_effect = InsufficientFundsError("Insufficient buying power")
        
        trader = AlchemiserTradingBot()
        result = trader.place_buy_order('AAPL', 1000000)  # Huge order
        
        assert not result.success
        assert 'insufficient' in result.error_message.lower()

def test_api_connection_failure():
    """Test behavior when API is unavailable."""
    with patch('requests.get') as mock_get:
        mock_get.side_effect = ConnectionError("API unavailable")
        
        trader = AlchemiserTradingBot()
        
        # Should handle gracefully and not crash
        with pytest.raises(ConnectionError):
            trader.get_account_info()
```

### 5. Order Execution Tests

**Purpose**: Test order placement, monitoring, and settlement

**Examples**:

```python
def test_progressive_limit_order():
    """Test progressive limit order execution strategy."""
    mock_pricing = {
        'bid': 100.00,
        'ask': 100.50,
        'mid': 100.25
    }
    
    with patch('get_realtime_pricing', return_value=mock_pricing):
        order_manager = SmartExecution()
        
        # Test progressive stepping
        prices = order_manager.calculate_progressive_prices('BUY', mock_pricing)
        
        assert prices[0] == 100.25  # Starts at midpoint
        assert prices[1] > prices[0]  # Steps toward ask
        assert prices[-1] <= 100.50  # Never exceeds ask

def test_websocket_order_monitoring():
    """Test WebSocket order status monitoring."""
    order_ids = ['order_1', 'order_2']
    
    with patch('websocket.create_connection') as mock_ws:
        # Simulate order fill notifications
        mock_ws.return_value.recv.side_effect = [
            '{"order": {"id": "order_1", "status": "filled"}}',
            '{"order": {"id": "order_2", "status": "filled"}}'
        ]
        
        monitor = OrderMonitor()
        results = monitor.wait_for_completion(order_ids, timeout=30)
        
        assert all(result.status == 'filled' for result in results)
```

## Test Data and Fixtures

### Mock Data Generation

```python
@pytest.fixture
def sample_market_data():
    """Generate realistic market data for testing."""
    return {
        'SPY': {
            'price': 450.00,
            'rsi_14': 65.3,
            'sma_20': 445.2,
            'volatility': 0.18
        },
        'VIX': {
            'price': 16.5,
            'change': -2.1
        }
    }

@pytest.fixture
def mock_alpaca_client():
    """Mock Alpaca client for isolated testing."""
    with patch('alpaca_client.AlpacaClient') as mock:
        mock.return_value.get_account_info.return_value = {
            'account_id': 'test_account',
            'portfolio_value': 100000.0,
            'cash': 50000.0
        }
        mock.return_value.get_positions.return_value = {}
        yield mock.return_value
```

### Test Scenarios

```python
# Market condition scenarios
MARKET_SCENARIOS = [
    {
        'name': 'bull_market',
        'rsi_14': 70.0,
        'vix': 12.0,
        'trend': 'up',
        'expected_allocation': 'growth'
    },
    {
        'name': 'bear_market', 
        'rsi_14': 30.0,
        'vix': 30.0,
        'trend': 'down',
        'expected_allocation': 'defensive'
    },
    {
        'name': 'sideways_market',
        'rsi_14': 50.0,
        'vix': 18.0,
        'trend': 'sideways',
        'expected_allocation': 'neutral'
    }
]

@pytest.mark.parametrize('scenario', MARKET_SCENARIOS)
def test_market_scenarios(scenario):
    """Test strategy behavior across different market conditions."""
    # Test implementation here
```

## Coverage Analysis

### Current Coverage Status

```bash
# Generate coverage report
pytest --cov=the_alchemiser --cov-report=html

# View coverage summary
pytest --cov=the_alchemiser --cov-report=term-missing
```

**Coverage by Module:**

```
Name                              Stmts   Miss  Cover   Missing
---------------------------------------------------------------
the_alchemiser/core/               145      8    94%    45-47, 123
the_alchemiser/execution/          201     12    94%    78-82, 156-159
the_alchemiser/utils/              89      5    94%    23, 67-69
the_alchemiser/strategies/         167     15    91%    Various small gaps
---------------------------------------------------------------
TOTAL                             602     40    93%
```

### Critical Test Gaps

Based on analysis, these areas need additional test coverage:

**1. Strategy Logic Unit Tests** (Missing)

```python
# Needed: Pure strategy logic testing
def test_nuclear_strategy_scenarios():
    """Test each nuclear strategy scenario independently."""
    
def test_portfolio_weighting_algorithms():
    """Test equal weight vs inverse volatility weighting."""
    
def test_regime_detection_accuracy():
    """Test market regime classification accuracy."""
```

**2. Technical Indicator Tests** (Missing)

```python
# Needed: Mathematical accuracy validation
def test_rsi_calculation_accuracy():
    """Compare RSI calculation with TradingView/TwelveData."""
    
def test_moving_average_calculations():
    """Test SMA, EMA calculations with known values."""
    
def test_volatility_calculations():
    """Test 14-day volatility calculation accuracy."""
```

**3. Configuration Management Tests** (Missing)

```python
# Needed: Configuration loading and validation
def test_config_file_loading():
    """Test YAML configuration loading with valid/invalid files."""
    
def test_environment_variable_overrides():
    """Test environment variable configuration precedence."""
```

## Test Best Practices

### 1. Test Organization

```python
class TestNuclearStrategy:
    """Group related tests together."""
    
    def setup_method(self):
        """Setup before each test method."""
        self.strategy = NuclearStrategyEngine()
        
    def test_bear_market_detection(self):
        """Test specific scenario."""
        pass
        
    def test_bull_market_detection(self):
        """Test specific scenario."""
        pass
```

### 2. Mocking External Dependencies

```python
# Mock external API calls
@patch('twelve_data_client.get_time_series')
@patch('alpaca_client.get_account')
def test_strategy_execution(mock_alpaca, mock_twelve_data):
    """Test with mocked external dependencies."""
    
    # Setup mocks
    mock_twelve_data.return_value = sample_price_data
    mock_alpaca.return_value = sample_account_data
    
    # Test logic
    result = execute_strategy()
    assert result.success
```

### 3. Parameterized Tests

```python
@pytest.mark.parametrize('rsi,vix,expected', [
    (25.0, 35.0, 'defensive'),
    (75.0, 12.0, 'growth'),
    (50.0, 18.0, 'neutral')
])
def test_regime_detection(rsi, vix, expected):
    """Test regime detection with various inputs."""
    regime = detect_market_regime(rsi=rsi, vix=vix)
    assert regime == expected
```

### 4. Error Testing

```python
def test_handles_invalid_data():
    """Test graceful handling of invalid input data."""
    
    with pytest.raises(ValueError, match="Invalid RSI value"):
        calculate_rsi([])  # Empty data
        
    with pytest.raises(ValueError, match="Negative prices"):
        calculate_rsi([-1, -2, -3])  # Negative prices
```

## Continuous Integration

### GitHub Actions Workflow

```yaml
# .github/workflows/test.yml
name: Test Suite

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
        
    - name: Install dependencies
      run: |
        pip install -e .
        pip install pytest pytest-cov
        
    - name: Run tests
      run: pytest --cov=the_alchemiser --cov-report=xml
      
    - name: Upload coverage
      uses: codecov/codecov-action@v3
```

### Pre-commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: pytest-check
        name: pytest-check
        entry: pytest
        language: system
        pass_filenames: false
        always_run: true
```

## Performance Testing

### Load Testing

```python
def test_strategy_performance():
    """Test strategy execution performance."""
    import time
    
    start = time.time()
    
    # Execute strategy 100 times
    for _ in range(100):
        strategy.evaluate_nuclear_strategy(sample_indicators)
        
    execution_time = time.time() - start
    
    # Should complete within reasonable time
    assert execution_time < 1.0  # Less than 1 second
```

### Memory Testing

```python
def test_memory_usage():
    """Test memory usage during execution."""
    import psutil
    import os
    
    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss
    
    # Execute memory-intensive operation
    large_backtest = run_backtest(years=10)
    
    final_memory = process.memory_info().rss
    memory_increase = final_memory - initial_memory
    
    # Memory increase should be reasonable
    assert memory_increase < 100 * 1024 * 1024  # Less than 100MB
```

## Next Steps

- [Contributing Guide](./contributing.md)
- [Code Style Guide](./code-style.md)
- [Debugging Guide](./debugging.md)
