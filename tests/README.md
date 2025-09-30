# The Alchemiser Test Suite

Comprehensive test suite for The Alchemiser Quantitative Trading System implementing unit, integration, functional, and end-to-end tests as specified in the [Event-Driven Enforcement Plan](../docs/event_driven_enforcement_plan.md).

## Test Architecture

### Test Levels

#### 🔧 Unit Tests

- **Location**: `tests/shared/`, `tests/execution_v2/`, `tests/strategy_v2/`
- **Purpose**: Test individual components and functions in isolation
- **Scope**: Single classes, functions, or modules
- **Dependencies**: None (or minimal mocking)
- **Markers**: `@pytest.mark.unit`

#### 🔗 Integration Tests

- **Location**: `tests/integration/`
- **Purpose**: Test cross-module interactions and event-driven workflows
- **Scope**: Multiple modules working together with in-memory event bus
- **Dependencies**: Mock adapters, in-memory services
- **Markers**: `@pytest.mark.integration`

#### ⚙️ Functional Tests

- **Location**: `tests/functional/`
- **Purpose**: Test complete workflows with mocked external dependencies
- **Scope**: Full business workflows (Strategy → Portfolio → Execution)
- **Dependencies**: All external services mocked (Alpaca, AWS, etc.)
- **Markers**: `@pytest.mark.functional`

#### 🚀 End-to-End Tests

- **Location**: `tests/e2e/`
- **Purpose**: Test complete system including main entry points
- **Scope**: Entire application with paper trading mode
- **Dependencies**: Paper trading APIs, test environments
- **Markers**: `@pytest.mark.e2e`

## Test Structure

```
tests/
├── conftest.py                    # Global fixtures and configuration
├── README.md                      # This documentation
├── test_suite_demo.py            # Test suite demonstration
│
├── integration/                   # Integration Tests
│   ├── __init__.py
│   ├── test_event_driven_workflow.py           # Complete event chain tests
│   └── test_event_driven_workflow_simple.py    # Basic event tests
│
├── functional/                    # Functional Tests
│   ├── __init__.py
│   └── test_trading_system_workflow.py         # Complete workflow tests
│
├── e2e/                          # End-to-End Tests
│   ├── __init__.py
│   └── test_complete_system.py                 # Full system tests
│
├── shared/                       # Existing Unit Tests
│   ├── events/
│   ├── notifications/
│   ├── services/
│   └── utils/
│
├── execution_v2/                 # Existing Unit Tests
│   └── [execution module tests]
│
└── strategy_v2/                  # Existing Unit Tests
    └── [strategy module tests]
```

## Running Tests

### All Tests

```bash
pytest tests/
```

### By Test Level

```bash
# Unit tests only
pytest -m unit

# Integration tests only
pytest -m integration

# Functional tests only
pytest -m functional

# End-to-end tests only
pytest -m e2e
```

### By Directory

```bash
# Integration tests
pytest tests/integration/

# Functional tests
pytest tests/functional/

# End-to-end tests
pytest tests/e2e/
```

### Specific Test Files

```bash
# Event-driven integration tests
pytest tests/integration/test_event_driven_workflow_simple.py -v

# Trading system functional tests
pytest tests/functional/test_trading_system_workflow.py -v

# Complete system E2E tests
pytest tests/e2e/test_complete_system.py -v
```

## Test Categories by Feature

### Event-Driven Architecture Tests

- **Integration**: Event bus, event publishing/subscribing, event handlers
- **Functional**: Complete event chains (Strategy → Portfolio → Execution)
- **E2E**: Full workflow with event correlation and causation tracking

### Trading Workflow Tests

- **Integration**: Module interactions, event sequence validation
- **Functional**: Portfolio analysis, rebalancing, order execution workflows
- **E2E**: Complete trading cycles with paper trading validation

### Error Handling and Recovery Tests

- **Integration**: Event-driven error propagation, WorkflowFailed events
- **Functional**: Module-level error handling and recovery
- **E2E**: System-level error recovery and graceful degradation

### Configuration and Environment Tests

- **Unit**: Configuration loading and validation
- **Functional**: Environment-specific configurations (dev, test, prod)
- **E2E**: Complete system with environment variables and secrets

## Test Fixtures and Utilities

### Global Fixtures (`conftest.py`)

- `mock_alpaca_manager`: Mock AlpacaManager for all test levels
- `mock_container`: Mock ApplicationContainer with test configuration
- `test_correlation_id`, `test_causation_id`, `test_event_id`: Test identifiers
- `sample_target_allocations`: Sample portfolio allocations
- `event_bus_fixture`: EventBus instance for testing
- `disable_external_calls`: Disable external API calls during testing

### Test Utilities

- `EventCollector`: Collects events for verification
- `MockPortfolioHandler`, `MockExecutionHandler`: Mock event handlers
- Environment setup and teardown utilities

## Event-Driven Testing Patterns

### Event Creation and Validation

```python
# Create events with proper schema
signal_event = SignalGenerated(
    signals_data={"strategy_name": "test_strategy"},
    consolidated_portfolio=portfolio.model_dump(),
    signal_count=5,
    correlation_id=correlation_id,
    # ... other required fields
)

# Validate event structure
assert signal_event.correlation_id == correlation_id
assert signal_event.signal_count == 5
```

### Event Chain Testing

```python
# Test complete event chains
event_bus.subscribe("SignalGenerated", portfolio_handler)
event_bus.subscribe("RebalancePlanned", execution_handler)

# Trigger workflow
event_bus.publish(signal_event)

# Verify event sequence
assert len(events_received) == 3  # Signal → Rebalance → Completion
```

### Idempotency Testing

```python
# Test event replay scenarios
event_bus.publish(same_event)
event_bus.publish(same_event)  # Replay

# Verify idempotent handling
assert handler_call_count == 1  # Should not process duplicates
```

## Safety and Compliance

### Paper Trading Enforcement

- All tests use `PAPER_TRADING=true` environment variable
- Mock external dependencies to prevent real API calls
- Test environments isolated from production

### Data Protection

- No real API keys or secrets in test code
- Mock data for all external service interactions
- Test correlation IDs for traceability without exposure

### Error Boundaries

- Tests isolated from each other
- Failed tests don't affect other test execution
- Proper setup and teardown for all test levels

## Continuous Integration

### Test Markers for CI/CD

```bash
# Fast tests for PR validation
pytest -m "not slow and not e2e"

# Full test suite for releases
pytest -m "unit or integration or functional"

# E2E tests for deployment validation
pytest -m e2e --tb=short
```

### Performance Testing

- `@pytest.mark.slow` for long-running tests
- Timeout configurations for E2E tests
- Memory and performance validation

## Contributing to Tests

### Adding New Tests

1. Choose appropriate test level (unit/integration/functional/e2e)
2. Use existing fixtures and utilities from `conftest.py`
3. Follow event-driven testing patterns
4. Add appropriate pytest markers
5. Update this documentation

### Test Writing Guidelines

- Test one thing per test function
- Use descriptive test names
- Include docstrings explaining test purpose
- Mock external dependencies appropriately
- Verify correlation ID propagation in event tests
- Test both success and failure scenarios

## Troubleshooting

### Common Issues

- **Import Errors**: Ensure all dependencies are installed (`pip install -r requirements.txt`)
- **Environment Variables**: Check test environment setup in fixtures
- **Event Schema Errors**: Verify event creation with all required fields
- **Mock Issues**: Ensure mocks implement required protocols (EventHandler, etc.)

### Debug Mode

```bash
# Run with verbose output and debug info
pytest tests/integration/ -v -s --tb=long

# Run single test with full output
pytest tests/integration/test_event_driven_workflow_simple.py::TestSimpleEventDrivenWorkflow::test_startup_event_creation_and_flow -v -s
```

## Test Coverage Goals

- **Unit Tests**: 90%+ coverage for individual modules
- **Integration Tests**: 100% coverage of event-driven workflows
- **Functional Tests**: 100% coverage of main trading workflows
- **E2E Tests**: 100% coverage of system entry points and paper trading validation

---

For more information, see:

- [Event-Driven Enforcement Plan](../docs/event_driven_enforcement_plan.md)
- [DTO Migration Plan](../docs/DTO_MIGRATION_PLAN.md)
- [Project README](../README.md)
