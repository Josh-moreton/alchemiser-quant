from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import Mock

from fastapi.testclient import TestClient

from the_alchemiser.execution_v2.api import create_app
from the_alchemiser.shared.events import EventBus, TradeExecuted


def test_executions_endpoint_emits_trade_executed() -> None:
    """Test happy path: successful execution event publication."""
    event_bus = EventBus()
    captured: list[TradeExecuted] = []
    event_bus.subscribe("TradeExecuted", lambda event: captured.append(event))

    app = create_app(event_bus=event_bus)
    client = TestClient(app)

    timestamp = datetime.now(UTC)
    payload = {
        "correlation_id": "corr-execution",
        "causation_id": "cause-portfolio",
        "event_id": "evt-execution-1",
        "timestamp": timestamp.isoformat(),
        "source_module": "execution_v2",
        "source_component": "api",
        "execution_data": {"orders": [{"symbol": "SPY", "qty": 10}]},
        "success": True,
        "orders_placed": 1,
        "orders_succeeded": 1,
        "metadata": {"note": "contract-test"},
        "failure_reason": None,
        "failed_symbols": [],
    }

    response = client.post("/executions", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["event"]["event_type"] == "TradeExecuted"
    assert body["event"]["execution_data"] == payload["execution_data"]

    assert len(captured) == 1
    emitted_event = captured[0]
    expected_event = TradeExecuted(**{**payload, "timestamp": timestamp})
    assert emitted_event == expected_event


def test_executions_endpoint_missing_required_fields() -> None:
    """Test validation: missing required fields returns 422."""
    app = create_app()
    client = TestClient(app)

    # Missing execution_data, success, orders_placed, etc.
    invalid_payload = {"correlation_id": "test"}

    response = client.post("/executions", json=invalid_payload)

    assert response.status_code == 422
    assert "detail" in response.json()


def test_executions_endpoint_failed_execution() -> None:
    """Test failed execution scenario with failure_reason and failed_symbols."""
    event_bus = EventBus()
    captured: list[TradeExecuted] = []
    event_bus.subscribe("TradeExecuted", lambda event: captured.append(event))

    app = create_app(event_bus=event_bus)
    client = TestClient(app)

    timestamp = datetime.now(UTC)
    payload = {
        "correlation_id": "corr-execution",
        "causation_id": "cause-portfolio",
        "timestamp": timestamp.isoformat(),
        "execution_data": {"orders": [{"symbol": "AAPL", "qty": 5}]},
        "success": False,  # Failed execution
        "orders_placed": 1,
        "orders_succeeded": 0,
        "failure_reason": "Insufficient buying power",
        "failed_symbols": ["AAPL"],
    }

    response = client.post("/executions", json=payload)

    assert response.status_code == 200
    assert len(captured) == 1
    assert captured[0].success is False
    assert captured[0].failure_reason == "Insufficient buying power"
    assert captured[0].failed_symbols == ["AAPL"]


def test_executions_endpoint_event_bus_failure() -> None:
    """Test error handling: EventBus publish failure returns 500."""
    mock_bus = Mock(spec=EventBus)
    mock_bus.publish.side_effect = RuntimeError("EventBus connection failed")

    app = create_app(event_bus=mock_bus)
    client = TestClient(app)

    timestamp = datetime.now(UTC)
    payload = {
        "correlation_id": "corr-execution",
        "causation_id": "cause-portfolio",
        "timestamp": timestamp.isoformat(),
        "execution_data": {"orders": []},
        "success": True,
        "orders_placed": 0,
        "orders_succeeded": 0,
    }

    response = client.post("/executions", json=payload)

    assert response.status_code == 500
    assert "Event publication failed" in response.json()["detail"]


def test_executions_endpoint_with_defaults() -> None:
    """Test optional fields: event_id and timestamp default correctly."""
    event_bus = EventBus()
    captured: list[TradeExecuted] = []
    event_bus.subscribe("TradeExecuted", lambda event: captured.append(event))

    app = create_app(event_bus=event_bus)
    client = TestClient(app)

    # Omit optional event_id, timestamp, metadata, failure_reason, failed_symbols
    payload = {
        "correlation_id": "corr-execution",
        "causation_id": "cause-portfolio",
        "execution_data": {"orders": []},
        "success": True,
        "orders_placed": 0,
        "orders_succeeded": 0,
    }

    response = client.post("/executions", json=payload)

    assert response.status_code == 200
    assert len(captured) == 1
    # event_id should be auto-generated
    assert captured[0].event_id is not None
    # timestamp should default to now
    assert captured[0].timestamp is not None
    # Optional fields should have defaults
    assert captured[0].metadata == {}
    assert captured[0].failure_reason is None
    assert captured[0].failed_symbols == []


def test_executions_endpoint_partial_success() -> None:
    """Test partial execution success: some orders succeed, some fail."""
    event_bus = EventBus()
    captured: list[TradeExecuted] = []
    event_bus.subscribe("TradeExecuted", lambda event: captured.append(event))

    app = create_app(event_bus=event_bus)
    client = TestClient(app)

    timestamp = datetime.now(UTC)
    payload = {
        "correlation_id": "corr-execution",
        "causation_id": "cause-portfolio",
        "timestamp": timestamp.isoformat(),
        "execution_data": {
            "orders": [
                {"symbol": "SPY", "qty": 10, "status": "filled"},
                {"symbol": "AAPL", "qty": 5, "status": "rejected"},
            ]
        },
        "success": False,  # Overall failure due to partial rejection
        "orders_placed": 2,
        "orders_succeeded": 1,
        "failure_reason": "Partial execution failure",
        "failed_symbols": ["AAPL"],
    }

    response = client.post("/executions", json=payload)

    assert response.status_code == 200
    assert len(captured) == 1
    assert captured[0].orders_placed == 2
    assert captured[0].orders_succeeded == 1
    assert captured[0].failed_symbols == ["AAPL"]


def test_executions_endpoint_uses_header_correlation_id() -> None:
    """Middleware should source trace IDs from headers when payload omits them."""
    event_bus = EventBus()
    captured: list[TradeExecuted] = []
    event_bus.subscribe("TradeExecuted", lambda event: captured.append(event))

    app = create_app(event_bus=event_bus)
    client = TestClient(app)

    payload = {
        "execution_data": {"orders": [{"symbol": "SPY", "qty": 10}]},
        "success": True,
        "orders_placed": 1,
        "orders_succeeded": 1,
    }

    headers = {"X-Correlation-ID": "corr-header-exec", "X-Causation-ID": "cause-header-exec"}

    response = client.post("/executions", json=payload, headers=headers)

    assert response.status_code == 200
    assert captured[0].correlation_id == "corr-header-exec"
    assert captured[0].causation_id == "cause-header-exec"


def test_health_endpoint() -> None:
    """Test health check endpoint returns healthy status."""
    app = create_app()
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "service": "execution_v2"}


def test_contracts_endpoint_reports_versions() -> None:
    """Contract probe should surface supported events."""
    app = create_app()
    client = TestClient(app)

    response = client.get("/contracts")

    assert response.status_code == 200
    body = response.json()
    assert body["service"] == "execution_v2"
    assert body["supported_events"]["TradeExecuted"] == TradeExecuted.__event_version__
