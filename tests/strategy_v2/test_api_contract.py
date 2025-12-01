from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import Mock

from fastapi.testclient import TestClient

from the_alchemiser.shared.events import EventBus, SignalGenerated
from the_alchemiser.strategy_v2.api import create_app


def test_signals_endpoint_emits_signal_generated() -> None:
    """Test happy path: successful signal publication."""
    event_bus = EventBus()
    captured: list[SignalGenerated] = []
    event_bus.subscribe("SignalGenerated", lambda event: captured.append(event))

    app = create_app(event_bus=event_bus)
    client = TestClient(app)

    timestamp = datetime.now(UTC)
    payload = {
        "correlation_id": "corr-strategy",
        "causation_id": "cause-start",
        "event_id": "evt-signal-1",
        "timestamp": timestamp.isoformat(),
        "source_module": "strategy_v2",
        "source_component": "api",
        "signals_data": {"SPY": {"signal": "BUY", "weight": 0.6}},
        "consolidated_portfolio": {"SPY": 0.6, "QQQ": 0.4},
        "signal_count": 1,
        "metadata": {"note": "contract-test"},
    }

    response = client.post("/signals", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["event"]["event_type"] == "SignalGenerated"
    assert body["event"]["signals_data"] == payload["signals_data"]

    assert len(captured) == 1
    emitted_event = captured[0]
    expected_event = SignalGenerated(**{**payload, "timestamp": timestamp})
    assert emitted_event == expected_event


def test_signals_endpoint_missing_required_fields() -> None:
    """Test validation: missing required fields returns 422."""
    app = create_app()
    client = TestClient(app)

    # Missing correlation_id, causation_id, signals_data, etc.
    invalid_payload = {"signal_count": 1}

    response = client.post("/signals", json=invalid_payload)

    assert response.status_code == 422  # Unprocessable Entity
    assert "detail" in response.json()


def test_signals_endpoint_empty_correlation_id() -> None:
    """Test validation: empty correlation_id returns 500 due to event validation."""
    app = create_app()
    client = TestClient(app)

    timestamp = datetime.now(UTC)
    payload = {
        "correlation_id": "",  # Invalid: empty string (caught by event validation)
        "causation_id": "cause-start",
        "timestamp": timestamp.isoformat(),
        "signals_data": {"SPY": {"signal": "BUY", "weight": 0.6}},
        "consolidated_portfolio": {"SPY": 0.6, "QQQ": 0.4},
        "signal_count": 1,
    }

    response = client.post("/signals", json=payload)

    # Empty string passes Pydantic request validation but fails event validation
    assert response.status_code == 500
    assert "Event publication failed" in response.json()["detail"]


def test_signals_endpoint_invalid_timestamp() -> None:
    """Test validation: invalid timestamp format returns 422."""
    app = create_app()
    client = TestClient(app)

    payload = {
        "correlation_id": "corr-strategy",
        "causation_id": "cause-start",
        "timestamp": "not-a-valid-timestamp",
        "signals_data": {"SPY": {"signal": "BUY", "weight": 0.6}},
        "consolidated_portfolio": {"SPY": 0.6, "QQQ": 0.4},
        "signal_count": 1,
    }

    response = client.post("/signals", json=payload)

    assert response.status_code == 422


def test_signals_endpoint_event_bus_failure() -> None:
    """Test error handling: EventBus publish failure returns 500."""
    mock_bus = Mock(spec=EventBus)
    mock_bus.publish.side_effect = RuntimeError("EventBus connection failed")

    app = create_app(event_bus=mock_bus)
    client = TestClient(app)

    timestamp = datetime.now(UTC)
    payload = {
        "correlation_id": "corr-strategy",
        "causation_id": "cause-start",
        "timestamp": timestamp.isoformat(),
        "signals_data": {"SPY": {"signal": "BUY", "weight": 0.6}},
        "consolidated_portfolio": {"SPY": 0.6, "QQQ": 0.4},
        "signal_count": 1,
    }

    response = client.post("/signals", json=payload)

    assert response.status_code == 500
    assert "Event publication failed" in response.json()["detail"]


def test_signals_endpoint_with_defaults() -> None:
    """Test optional fields: event_id and timestamp default correctly."""
    event_bus = EventBus()
    captured: list[SignalGenerated] = []
    event_bus.subscribe("SignalGenerated", lambda event: captured.append(event))

    app = create_app(event_bus=event_bus)
    client = TestClient(app)

    # Omit optional event_id and timestamp
    payload = {
        "correlation_id": "corr-strategy",
        "causation_id": "cause-start",
        "signals_data": {"SPY": {"signal": "BUY", "weight": 0.6}},
        "consolidated_portfolio": {"SPY": 0.6, "QQQ": 0.4},
        "signal_count": 1,
    }

    response = client.post("/signals", json=payload)

    assert response.status_code == 200
    assert len(captured) == 1
    # event_id should be auto-generated (UUID)
    assert captured[0].event_id is not None
    # timestamp should default to now
    assert captured[0].timestamp is not None


def test_health_endpoint() -> None:
    """Test health check endpoint returns healthy status."""
    app = create_app()
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "service": "strategy_v2"}
