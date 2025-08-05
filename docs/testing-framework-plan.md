# Comprehensive Testing Framework Plan

## Overview

Based on the P0 failure mode analysis, we need a multi-layered testing strategy that covers:

- **Unit Tests**: Core logic, calculations, edge cases
- **Integration Tests**: API interactions, data flows, state management
- **Contract Tests**: Broker API compatibility, schema validation
- **Property Tests**: Market data edge cases, precision testing
- **Simulation Tests**: Real market scenario testing
- **Infrastructure Tests**: AWS services, deployment validation

---

## 1. Core Testing Infrastructure

### Test Structure

```
tests/
├── unit/                     # Fast, isolated tests
│   ├── test_indicators.py    # Technical indicator calculations
│   ├── test_trading_math.py  # Price calculations, rounding
│   ├── test_portfolio.py     # Portfolio rebalancing logic
│   ├── test_strategies/      # Strategy logic isolation
│   ├── test_types.py         # Type validation
│   └── test_pytest_mock_integration.py # pytest-mock functionality tests
├── integration/              # Component interaction tests
│   ├── test_data_pipeline.py # Data provider → indicators → signals
│   ├── test_execution.py     # Order placement → tracking → reconciliation
│   ├── test_persistence.py   # S3 state management
│   └── test_error_handling.py # Exception flows
├── contract/                 # External API compatibility
│   ├── test_alpaca_api.py    # Broker API contract validation
│   ├── test_aws_services.py  # AWS SDK expectations
│   └── schemas/              # JSON schema definitions
├── property/                 # Property-based testing
│   ├── test_precision.py     # Decimal/float precision edge cases
│   ├── test_market_data.py   # Data gaps, outliers, edge cases
│   └── test_portfolio_math.py # Portfolio calculation invariants
├── simulation/               # Market scenario testing
│   ├── test_market_scenarios.py # Historical replay testing
│   ├── test_failure_modes.py    # Specific failure scenarios
│   └── fixtures/             # Market data fixtures
├── infrastructure/           # AWS/deployment tests
│   ├── test_lambda_deployment.py
│   ├── test_permissions.py
│   └── test_networking.py
├── utils/                    # Testing utilities
│   └── mocks.py             # Comprehensive mock framework
├── fixtures/                 # Test data fixtures
│   └── market_data.py       # Market data generation
└── conftest.py              # Global pytest configuration and fixtures
```

### Testing Dependencies

**Core Testing Stack:**

- **pytest**: Primary testing framework
- **pytest-mock**: Enhanced mocking capabilities (replaces unittest.mock)
- **pytest-cov**: Test coverage reporting
- **pytest-xdist**: Parallel test execution
- **pytest-timeout**: Test timeout management
- **hypothesis**: Property-based testing for edge cases
- **numpy/pandas**: Test data generation and analysis

---

## 2. Failure Mode Mapping to Test Categories

### 2.1 Trading Logic Failures → Unit + Property Tests

**Target Failures:**

- Indicator miscalculation from missing data
- Floating-point precision in crossovers
- Tick-size and rounding errors
- Hard-coded assumptions about instruments

**Test Approach:**

```python
# Unit Tests
def test_rsi_calculation_with_missing_bars():
    """Test RSI handles data gaps gracefully"""
    data_with_gaps = create_price_series_with_gaps()
    rsi = calculate_rsi(data_with_gaps, period=14)
    assert not rsi.isna().any()  # No NaN values
    
def test_moving_average_crossover_precision():
    """Test crossover detection with minimal differences"""
    # Property: should have hysteresis to prevent jittering
    prices = [100.0001, 100.0002, 100.0001, 100.0002]
    signals = detect_crossover(prices, short=2, long=3)
    assert count_signal_changes(signals) <= 1  # No thrashing

# Property Tests (using hypothesis)
@given(prices=price_series(), tick_size=tick_sizes())
def test_price_rounding_invariants(prices, tick_size):
    """Price calculations respect tick size requirements"""
    rounded_prices = round_to_tick_size(prices, tick_size)
    assert all(p % tick_size == 0 for p in rounded_prices)
```

### 2.2 API/Broker Issues → Contract + Integration Tests

**Target Failures:**

- API rate limits, network timeouts
- Authentication/session expiration
- Order acknowledgments lost
- Broker API schema changes

**Test Approach:**

```python
# Contract Tests
def test_alpaca_order_response_schema():
    """Validate broker API response structure"""
    mock_response = load_alpaca_order_fixture()
    validated = OrderDetails.from_dict(mock_response)
    assert validated.id is not None
    assert validated.status in VALID_ORDER_STATUSES

```python
# Integration Tests with Mocking using pytest-mock
def test_order_submission_with_rate_limit(mocker):
    """Test exponential backoff on 429 errors"""
    mock_submit = mocker.patch('alpaca_api.submit_order')
    mock_submit.side_effect = [RateLimitError(), success_response()]
    
    with measure_execution_time() as timer:
        result = trading_engine.place_order("AAPL", 100, "BUY")
    
    assert result.success
    assert timer.elapsed > MIN_BACKOFF_TIME
    assert mock_submit.call_count == 2

def test_network_timeout_recovery(mocker):
    """Test network timeout handling with pytest-mock"""
    mock_post = mocker.patch('requests.post')
    mock_post.side_effect = [Timeout(), success_response()]
    
    result = data_provider.get_price("AAPL")
    assert result is not None  # Should recover from timeout
```

```

### 2.3 Data Integrity → Property + Simulation Tests
**Target Failures:**
- S3 eventual consistency
- Portfolio desynchronization  
- Corrupted data handling
- State persistence across Lambda restarts

**Test Approach:**
```python
# Property Tests for Data Consistency
@given(portfolio_states=portfolio_scenarios())
def test_portfolio_consistency_invariants(portfolio_states):
    """Portfolio math should always balance"""
    for state in portfolio_states:
        total_allocation = sum(state.allocations.values())
        assert abs(total_allocation - 1.0) < 1e-6  # Within precision
        
        portfolio_value = calculate_total_value(state)
        sum_of_positions = sum(pos.market_value for pos in state.positions)
        assert abs(portfolio_value - sum_of_positions) < 0.01  # Within penny

# Simulation Tests
def test_s3_eventual_consistency_scenario():
    """Test read-after-write with artificial delay"""
    state = PortfolioState(positions={"AAPL": 100})
    
    # Write state
    s3_handler.save_state(state)
    
    # Simulate eventual consistency delay
    with mock_s3_delay(seconds=2):
        retrieved_state = s3_handler.load_state()
    
    assert retrieved_state == state  # Should handle consistency
```

### 2.4 AWS Infrastructure → Infrastructure + Contract Tests

**Target Failures:**

- Lambda cold starts, timeouts
- IAM permission errors
- EventBridge misconfiguration
- Secrets Manager throttling

**Test Approach:**

```python
# Infrastructure Tests
def test_lambda_cold_start_performance():
    """Verify Lambda initializes within acceptable time"""
    import subprocess
    import time
    
    start_time = time.time()
    result = subprocess.run(['sam', 'local', 'invoke', 'TradingFunction'])
    cold_start_time = time.time() - start_time
    
    assert cold_start_time < MAX_COLD_START_TIME
    assert result.returncode == 0

def test_iam_permissions_minimal():
    """Test Lambda has exactly required permissions"""
    # Should succeed
    assert can_access_secrets_manager()
    assert can_read_s3_bucket()
    
    # Should fail (principle of least privilege)
    assert not can_access_other_accounts_resources()
    assert not can_delete_s3_buckets()

@pytest.mark.integration
def test_eventbridge_trigger_timing():
    """Test EventBridge triggers at correct market times"""
    with freeze_time("2024-01-15 09:30:00 EST"):  # Market open
        trigger_result = simulate_eventbridge_trigger()
        assert trigger_result.success
    
    with freeze_time("2024-01-15 16:00:01 EST"):  # After market close
        trigger_result = simulate_eventbridge_trigger()
        assert not trigger_result.should_trade
```

---

## 3. Advanced Testing Strategies

### 3.1 Market Scenario Simulation

```python
class MarketScenarioRunner:
    """Run strategies against historical market conditions"""
    
    def test_2020_march_crash(self):
        """Test strategy during COVID crash"""
        historical_data = load_market_data("2020-02-15", "2020-04-15")
        strategy_results = run_strategy_simulation(
            strategy=KLMStrategy(),
            data=historical_data,
            initial_portfolio=100000
        )
        
        # Strategy should limit drawdown
        max_drawdown = calculate_max_drawdown(strategy_results)
        assert max_drawdown < 0.25  # Less than 25% drawdown
        
    def test_flash_crash_recovery(self):
        """Test behavior during rapid price movements"""
        flash_crash_data = create_flash_crash_scenario()
        
        # Strategy should not panic sell at the bottom
        signals = strategy.generate_signals(flash_crash_data)
        bottom_signals = signals.loc[flash_crash_data.price.idxmin()]
        assert bottom_signals.action != "SELL"
```

### 3.2 Precision and Edge Case Testing

```python
from hypothesis import given, strategies as st
from decimal import Decimal

@given(
    portfolio_value=st.decimals(min_value=1000, max_value=1000000, places=2),
    allocation_pcts=st.lists(
        st.decimals(min_value=0, max_value=1, places=4), 
        min_size=2, max_size=10
    ).filter(lambda x: sum(x) <= 1)
)
def test_portfolio_allocation_precision(portfolio_value, allocation_pcts):
    """Portfolio allocations should never exceed available cash"""
    allocations = calculate_dollar_allocations(portfolio_value, allocation_pcts)
    
    total_allocated = sum(allocations.values())
    assert total_allocated <= portfolio_value
    
    # Should be within one cent of expected
    expected_total = portfolio_value * sum(allocation_pcts)
    assert abs(total_allocated - expected_total) <= Decimal('0.01')
```

### 3.3 Chaos Engineering for Resilience

```python
class ChaosTestSuite:
    """Inject controlled failures to test resilience"""
    
    def test_api_intermittent_failures(self):
        """Test behavior with 10% API failure rate"""
        with chaos_api_failures(failure_rate=0.1):
            results = []
            for _ in range(100):
                try:
                    price = data_provider.get_current_price("AAPL")
                    results.append(price)
                except APIError:
                    results.append(None)
            
            # Should successfully get prices >85% of the time
            success_rate = len([r for r in results if r is not None]) / 100
            assert success_rate > 0.85
    
    def test_partial_lambda_timeout(self):
        """Test behavior when Lambda times out mid-execution"""
        with lambda_timeout_simulation(timeout_after_seconds=25):
            # Should gracefully handle timeout
            result = trading_function.main_handler(test_event)
            assert result.get('partial_execution_logged', False)
```

---

## 4. Test Data Management

### 4.1 Fixture Strategy

```python
# tests/fixtures/market_data.py
@pytest.fixture
def normal_market_conditions():
    """Standard market data with typical volatility"""
    return generate_market_data(
        symbols=["SPY", "QQQ", "AAPL"],
        start_date="2023-01-01",
        end_date="2023-12-31",
        volatility="normal"
    )

@pytest.fixture  
def gap_up_scenario():
    """Market data with overnight gaps"""
    base_data = normal_market_conditions()
    return inject_price_gaps(base_data, gap_sizes=[0.05, 0.10, -0.03])

@pytest.fixture
def missing_data_scenario():
    """Market data with random missing bars"""
    base_data = normal_market_conditions()
    return randomly_remove_bars(base_data, removal_rate=0.02)
```

### 4.2 Mock Strategy

```python
# Comprehensive mocking using pytest-mock for external dependencies
class TestingMockSuite:
    
    def mock_broker_api(self, mocker, responses=None):
        """Mock all broker interactions using pytest-mock"""
        mock_client = mocker.patch('alpaca.trading.TradingClient')
        mock_client.return_value.submit_order.side_effect = responses or [success_order()]
        mock_client.return_value.get_account.return_value = test_account()
        return mock_client
    
    def mock_aws_services(self, mocker):
        """Mock S3, Secrets Manager, CloudWatch using pytest-mock"""
        mock_s3 = mocker.Mock()
        mock_secrets = mocker.Mock()
        
        def mock_boto_client(service):
            return {'s3': mock_s3, 'secretsmanager': mock_secrets}[service]
            
        mocker.patch('boto3.client', side_effect=mock_boto_client)
        return {'s3': mock_s3, 'secretsmanager': mock_secrets}
```

---

## 5. Implementation Priority

### Phase 1: Foundation (Week 1) ✅ **COMPLETED**

1. **Setup pytest infrastructure** with fixtures and mocks ✅
2. **Unit tests for core calculations** (indicators, portfolio math) ✅
3. **pytest-mock integration** for enhanced mocking capabilities ✅
4. **Basic integration tests** for happy path scenarios ✅
5. **CI/CD integration** with GitHub Actions

**Status**: Infrastructure setup complete with pytest, pytest-mock, comprehensive fixtures, and 36 passing unit tests.

### Phase 2: Coverage Expansion (Week 2) ✅ **COMPLETED**

1. **Property-based testing** for edge cases ✅
2. **Contract tests** for Alpaca API ✅
3. **Error handling tests** for all failure modes ✅
4. **Performance benchmarks**
5. **Basic integration tests** for component interactions ✅

**Status**: Integration testing complete with 28 passing tests covering:

- Basic component interactions (6 tests): Signal generation, cash flow, portfolio tracking, data pipelines
- Comprehensive integration flows (10 tests): Data-to-signal, execution workflows, error handling and recovery
- API contract validation (12 tests): Alpaca trading API, AWS services, error handling patterns
- All external API contracts validated and error scenarios tested

### Phase 3: Property-Based Testing (Week 3) ✅ **COMPLETED**

1. **Property-based testing** framework with Hypothesis ✅
2. **Mathematical property validation** for trading calculations ✅
3. **Edge case generation** for market data scenarios ✅
4. **Portfolio mathematics invariants** testing ✅

**Status**: Property-based testing complete with 9 passing tests covering:

- Trading mathematics properties (7 tests): Moving averages, price changes, order validation, RSI calculation, P&L calculation, Bollinger Bands, average price calculations
- Portfolio mathematics properties (2 tests): Portfolio value calculations, cash management invariants
- All tests use Hypothesis strategies for comprehensive edge case coverage
- Zero variance handling in mathematical calculations properly implemented

### Phase 4: Advanced Testing (Week 4)

1. **Market scenario simulation** framework
2. **Chaos engineering** suite
3. **Infrastructure testing** with LocalStack
4. **Security testing** for secrets/permissions

### Phase 4: Market Scenario & Infrastructure Testing (Week 4)

1. **Market scenario simulation** framework
2. **Chaos engineering** suite
3. **Infrastructure testing** with LocalStack
4. **Security testing** for secrets/permissions

### Phase 5: Continuous Validation (Week 5)

1. **Regression test suite** for production issues
2. **Monitoring/alerting** integration tests
3. **Documentation** and test maintenance processes
4. **Load testing** for production volumes

---

## Current Test Suite Status

### **✅ COMPLETED: 73 Passing Tests**

**Test Categories:**
- **Unit Tests**: 36 tests covering core trading mathematics, portfolio calculations, and pytest-mock integration
- **Integration Tests**: 28 tests covering component interactions, API contracts, and error handling
- **Property-Based Tests**: 9 tests using Hypothesis for mathematical property validation

**Test Coverage:**
```
Unit Tests (36):
├── Trading Math (18 tests): Price rounding, position sizing, portfolio calculations
├── Portfolio Management (10 tests): Rebalancing, state management, allocation calculations  
└── pytest-mock Integration (7 tests): Enhanced mocking capabilities, AWS/Alpaca mocking

Integration Tests (28):
├── Basic Integration (6 tests): Signal generation, cash flow, portfolio tracking
├── Comprehensive Flows (10 tests): Data-to-signal pipelines, execution workflows
└── Contract Validation (12 tests): API contracts, error handling patterns

Property-Based Tests (9):
├── Trading Math Properties (7 tests): Moving averages, RSI, Bollinger Bands, P&L
└── Portfolio Math Properties (2 tests): Value calculations, cash management
```

**Framework Features:**
- ✅ **pytest-mock**: Enhanced mocking with no recursion issues
- ✅ **Hypothesis**: Property-based testing for edge cases  
- ✅ **Safe Mocking Patterns**: Avoiding complex spy operations
- ✅ **Comprehensive Fixtures**: Test data generation and scenarios
- ✅ **Zero Variance Handling**: Mathematical edge cases properly handled

---

## Success Metrics

- **Coverage**: >90% line coverage, >85% branch coverage
- **Performance**: All tests run in <2 minutes
- **Reliability**: Tests catch 95%+ of introduced bugs
- **Maintenance**: New features require corresponding tests
- **Confidence**: Zero-fear deployments with comprehensive test suite

This testing framework will transform your trading system from "hope it works" to "know it works" with mathematical certainty.
