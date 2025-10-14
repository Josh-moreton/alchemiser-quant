"""Business Unit: shared | Status: current.

Global pytest configuration and fixtures for all test levels.

Provides common fixtures for unit, integration, functional, and end-to-end tests.
"""

import pytest
import uuid
from datetime import UTC, datetime
from unittest.mock import Mock, MagicMock
from typing import Any, Dict, Generator

# Add the project root to Python path for imports
import sys
import os

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


@pytest.fixture
def mock_alpaca_manager() -> Mock:
    """Create a mock AlpacaManager for testing."""
    mock = Mock()
    mock.is_paper_trading = True
    mock.get_account.return_value = {
        "account_id": "test_account_123",
        "equity": 100000.0,
        "cash": 10000.0,
        "buying_power": 50000.0,
        "portfolio_value": 100000.0,
    }
    mock.get_all_positions.return_value = {}
    mock.place_order.return_value = {"id": "test_order_123", "status": "filled"}
    return mock


@pytest.fixture
def mock_container() -> Mock:
    """Create a mock ApplicationContainer for testing."""
    container = Mock()
    container.config.alpaca_api_key = "test_api_key"
    container.config.alpaca_secret_key = "test_secret_key"
    container.config.paper_trading = True
    return container


@pytest.fixture
def test_correlation_id() -> str:
    """Generate a test correlation ID."""
    return f"test-correlation-{uuid.uuid4()}"


@pytest.fixture
def test_causation_id() -> str:
    """Generate a test causation ID."""
    return f"test-causation-{uuid.uuid4()}"


@pytest.fixture
def test_event_id() -> str:
    """Generate a test event ID."""
    return f"test-event-{uuid.uuid4()}"


@pytest.fixture
def test_timestamp() -> datetime:
    """Generate a test timestamp."""
    return datetime.now(UTC)


@pytest.fixture
def sample_target_allocations() -> Dict[str, float]:
    """Sample target allocations for testing."""
    return {
        "AAPL": 0.3,
        "GOOGL": 0.25, 
        "MSFT": 0.2,
        "TSLA": 0.15,
        "NVDA": 0.1
    }


@pytest.fixture
def event_bus_fixture():
    """Create an EventBus instance for testing.
    
    Note: Returns in-memory EventBus for unit tests that don't need EventBridge.
    For integration tests requiring EventBridge behavior, use eventbridge_bus_fixture.
    """
    try:
        from the_alchemiser.shared.events.bus import EventBus
        return EventBus()
    except ImportError:
        return Mock()


@pytest.fixture
def eventbridge_bus_fixture():
    """Create an EventBridgeBus instance for testing with mocked boto3 client."""
    try:
        from unittest.mock import Mock
        from the_alchemiser.shared.events.eventbridge_bus import EventBridgeBus
        
        bus = EventBridgeBus(event_bus_name="test-bus", enable_local_handlers=True)
        # Mock the boto3 client to avoid actual AWS calls
        mock_client = Mock()
        mock_client.put_events.return_value = {
            "FailedEntryCount": 0,
            "Entries": [{"EventId": "test-event-id"}]
        }
        # Use the public method for dependency injection
        bus.set_client_for_testing(mock_client)
        return bus
    except ImportError:
        return Mock()


@pytest.fixture(scope="session")
def disable_external_calls():
    """Disable external API calls during testing."""
    import os
    os.environ["TESTING"] = "true"
    os.environ["PAPER_TRADING"] = "true"
    yield
    if "TESTING" in os.environ:
        del os.environ["TESTING"]