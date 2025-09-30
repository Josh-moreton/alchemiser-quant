# Testing Guide

This document provides guidance on testing the Alchemiser trading system, including execution testing with mocked signals for rapid development iteration.

## Table of Contents

- [Test Structure](#test-structure)
- [Execution Testing with Signal Mocks](#execution-testing-with-signal-mocks)
- [Running Tests](#running-tests)
- [Environment Setup](#environment-setup)
- [Test Markers](#test-markers)

## Test Structure

The test suite follows a layered architecture matching the repository structure:

```
tests/
├── unit/               # Unit tests for individual components
├── integration/        # Integration tests for module interactions
├── functional/         # Functional tests with mocked dependencies
├── e2e/               # End-to-end tests
├── execution_v2/      # Execution module tests
├── portfolio_v2/      # Portfolio module tests
├── strategy_v2/       # Strategy module tests
└── shared/            # Shared utilities tests
```

## Execution Testing with Signal Mocks

### Overview

The signal mock execution test framework enables rapid testing of execution logic changes without waiting for full strategy signal generation. This significantly speeds up the development cycle for execution-related work.

### Quick Start

#### 1. Using pytest

Run the signal mock execution tests:

```bash
# Run all signal mock tests
python -m pytest tests/execution_v2/test_signal_mock_execution.py -v

# Run specific test
python -m pytest tests/execution_v2/test_signal_mock_execution.py::TestQuickExecutionWithSignalMock::test_signal_mock_creation -v

# Run with real Paper API (requires credentials)
ALPACA_API_KEY=your_key ALPACA_SECRET_KEY=your_secret python -m pytest tests/execution_v2/test_signal_mock_execution.py::TestQuickExecutionWithSignalMock::test_execution_with_real_paper_api_basic -v
```

#### 2. Using the Standalone Script

The `scripts/quick_execution_test.py` script provides a convenient CLI for testing:

```bash
# Basic test with default allocations
python scripts/quick_execution_test.py --test-only

# Custom allocations
python scripts/quick_execution_test.py --test-only --allocations SPY:0.5,QQQ:0.3,AAPL:0.2

# Full execution with real Paper API (when integrated)
ALPACA_API_KEY=your_key ALPACA_SECRET_KEY=your_secret python scripts/quick_execution_test.py
```

### Test Cases

#### Signal Mock Creation (`test_signal_mock_creation`)

Tests the creation of realistic `SignalGenerated` events with proper metadata and correlation tracking.

**Purpose**: Validate signal event structure for execution testing.

#### Custom Allocations (`test_signal_mock_with_custom_allocations`)

Tests signal creation with custom portfolio allocations.

**Purpose**: Enable testing with various allocation scenarios.

#### Event Bus Integration (`test_signal_publishing_to_event_bus`)

Tests that signals can be published and collected via the event bus.

**Purpose**: Validate event-driven architecture integration.

#### Complete Event Chain (`test_execution_with_mock_handlers`)

Tests the complete workflow: Signal → Portfolio → Execution → Completion with mock handlers.

**Purpose**: Validate end-to-end event chain without requiring real APIs.

**Event Flow**:
1. `SignalGenerated` → Portfolio handler
2. `RebalancePlanned` → Execution handler  
3. `TradeExecuted` → Completion
4. `WorkflowCompleted`

#### Real Paper API Test (`test_execution_with_real_paper_api_basic`)

Tests execution with mocked signal but real Paper API integration.

**Purpose**: Validate actual Paper API execution flow.

**Requirements**:
- Real Paper API credentials (`ALPACA_API_KEY`, `ALPACA_SECRET_KEY`)
- `PAPER_TRADING=true` environment variable
- Full system integration (ApplicationContainer)

### Signal Mock Helper Function

The `create_execution_test_signal()` function creates realistic signals for testing:

```python
from tests.execution_v2.test_signal_mock_execution import create_execution_test_signal

# Default liquid securities (SPY, QQQ, AAPL, MSFT)
signal = create_execution_test_signal()

# Custom allocations
signal = create_execution_test_signal(
    correlation_id="test-123",
    allocations={
        "VTI": 0.50,
        "BND": 0.30,
        "GLD": 0.20,
    }
)
```

**Default Allocations** (liquid securities):
- SPY: 35% (S&P 500 ETF)
- QQQ: 25% (Nasdaq ETF)
- AAPL: 20% (Apple)
- MSFT: 20% (Microsoft)

## Running Tests

### All Tests

```bash
# Run all tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=the_alchemiser --cov-report=html
```

### By Level

```bash
# Unit tests only
python -m pytest tests/ -v -m unit

# Integration tests
python -m pytest tests/ -v -m integration

# Functional tests
python -m pytest tests/ -v -m functional

# End-to-end tests
python -m pytest tests/ -v -m e2e
```

### By Module

```bash
# Execution tests
python -m pytest tests/execution_v2/ -v

# Portfolio tests
python -m pytest tests/portfolio_v2/ -v

# Strategy tests
python -m pytest tests/strategy_v2/ -v

# Event system tests
python -m pytest tests/shared/events/ -v
```

## Environment Setup

### Required Environment Variables

For execution testing with real Paper API:

```bash
# Required
export ALPACA_API_KEY=your_paper_api_key
export ALPACA_SECRET_KEY=your_paper_secret_key
export PAPER_TRADING=true

# Optional
export TESTING=true
export ALPACA_ENDPOINT=https://paper-api.alpaca.markets
```

### Test Environment Fixtures

The test suite provides fixtures in `tests/conftest.py`:

- `event_bus_fixture`: EventBus instance
- `mock_alpaca_manager`: Mocked Alpaca client
- `mock_container`: Mocked ApplicationContainer
- `test_correlation_id`: Generated correlation ID
- `test_timestamp`: Test timestamp
- `sample_target_allocations`: Sample allocations

## Test Markers

Tests are marked for categorization:

```python
@pytest.mark.unit          # Unit tests
@pytest.mark.integration   # Integration tests
@pytest.mark.functional    # Functional tests
@pytest.mark.e2e           # End-to-end tests
@pytest.mark.property      # Property-based tests
@pytest.mark.event_driven  # Event-driven architecture tests
@pytest.mark.slow          # Slow-running tests
```

### Running Specific Markers

```bash
# Run only event-driven tests
python -m pytest -v -m event_driven

# Run all except slow tests
python -m pytest -v -m "not slow"

# Combine markers
python -m pytest -v -m "integration and event_driven"
```

## Best Practices

### 1. Test Isolation

Each test should be independent and not rely on external state:

```python
def test_execution_logic(event_bus):
    """Test with isolated event bus."""
    # Test runs in isolation
    signal = create_execution_test_signal()
    event_bus.publish(signal)
    # Assert results
```

### 2. Use Fixtures

Leverage pytest fixtures for common setup:

```python
@pytest.fixture
def execution_handler(mock_container):
    """Create execution handler for testing."""
    return TradingExecutionHandler(mock_container)
```

### 3. Validate Event Chains

For event-driven tests, validate complete event chains:

```python
def test_event_chain(event_collector):
    # Publish event
    # ...
    
    # Verify event types in order
    expected = ["SignalGenerated", "RebalancePlanned", "TradeExecuted"]
    actual = [e.event_type for e in event_collector.events_received]
    assert actual == expected
    
    # Verify correlation ID propagation
    for event in event_collector.events_received:
        assert event.correlation_id == correlation_id
```

### 4. Mock External Dependencies

Always mock external API calls in unit/integration tests:

```python
@patch('alpaca.trading.client.TradingClient')
def test_execution(mock_client):
    mock_client.place_order.return_value = Mock(id="order-123")
    # Test execution logic
```

### 5. Paper Trading Enforcement

For tests with real APIs, enforce Paper trading mode:

```python
@pytest.fixture
def enforce_paper_trading():
    assert os.environ.get("PAPER_TRADING") == "true"
    assert os.environ.get("ALPACA_API_KEY", "").startswith("PK")
```

## Troubleshooting

### Import Errors

If you see import errors for event system components:

```bash
# Install dependencies
pip install pandas numpy alpaca-py pydantic pydantic-settings pytest
```

### Test Skipped: Events Not Available

The test suite checks for event system availability. If tests are skipped:

1. Verify all dependencies are installed
2. Check `EVENTS_AVAILABLE` flag in test output
3. Review import error messages for missing modules

### Paper Trading Validation Failed

Ensure environment variables are set correctly:

```bash
export PAPER_TRADING=true
export ALPACA_API_KEY=PKxxxxx...  # Must start with 'PK'
```

## Development Workflow

### Rapid Execution Testing

1. Make execution logic changes
2. Run signal mock test:
   ```bash
   python scripts/quick_execution_test.py --test-only
   ```
3. Verify signal creation succeeds
4. Run full test suite:
   ```bash
   python -m pytest tests/execution_v2/test_signal_mock_execution.py -v
   ```
5. Test with real Paper API (optional):
   ```bash
   ALPACA_API_KEY=... ALPACA_SECRET_KEY=... python scripts/quick_execution_test.py
   ```

### Benefits

- **Fast Iteration**: Test execution changes in seconds, not minutes
- **Isolation**: Debug execution issues separately from strategy generation
- **Reproducible**: Same signal used across test runs
- **Safe**: Enforced Paper trading mode prevents accidental live trades

## Related Documentation

- [README.md](../README.md) - Main project documentation
- [Event-Driven Architecture](../README.md#event-driven-workflow) - Event system overview
- [Execution v2](../the_alchemiser/execution_v2/README.md) - Execution module details
- [Portfolio v2](../the_alchemiser/portfolio_v2/README.md) - Portfolio module details
