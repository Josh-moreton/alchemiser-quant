from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import Mock

from fastapi.testclient import TestClient

from the_alchemiser.portfolio_v2.api import create_app
from the_alchemiser.shared.events import EventBus, RebalancePlanned


def test_rebalance_endpoint_emits_rebalance_planned() -> None:
    """Test happy path: successful rebalance event publication."""
    event_bus = EventBus()
    captured: list[RebalancePlanned] = []
    event_bus.subscribe("RebalancePlanned", lambda event: captured.append(event))

    app = create_app(event_bus=event_bus)
    client = TestClient(app)

    now = datetime.now(UTC)
    now_iso = now.isoformat()
    payload = {
        "correlation_id": "corr-portfolio",
        "causation_id": "cause-signal",
        "event_id": "evt-rebalance-1",
        "timestamp": now_iso,
        "source_module": "portfolio_v2",
        "source_component": "api",
        "rebalance_plan": {
            "correlation_id": "corr-portfolio",
            "causation_id": "cause-signal",
            "timestamp": now_iso,
            "plan_id": "plan-1",
            "items": [
                {
                    "symbol": "SPY",
                    "current_weight": "0.50",
                    "target_weight": "0.60",
                    "weight_diff": "0.10",
                    "target_value": "6000",
                    "current_value": "5000",
                    "trade_amount": "1000",
                    "action": "BUY",
                    "priority": 1,
                }
            ],
            "total_portfolio_value": "10000",
            "total_trade_value": "1000",
            "max_drift_tolerance": "0.05",
            "execution_urgency": "HIGH",
            "estimated_duration_minutes": 30,
            "metadata": {"note": "contract-test"},
        },
        "allocation_comparison": {
            "target_values": {"SPY": "6000", "QQQ": "4000"},
            "current_values": {"SPY": "5000", "QQQ": "5000"},
            "deltas": {"SPY": "1000", "QQQ": "-1000"},
        },
        "trades_required": True,
        "metadata": {"note": "rebalance-contract"},
    }

    response = client.post("/rebalance", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["event"]["event_type"] == "RebalancePlanned"
    assert body["event"]["rebalance_plan"]["plan_id"] == payload["rebalance_plan"]["plan_id"]

    assert len(captured) == 1
    emitted_event = captured[0]
    assert emitted_event.rebalance_plan.plan_id == payload["rebalance_plan"]["plan_id"]
    assert emitted_event.rebalance_plan.total_trade_value == Decimal("1000")
    assert emitted_event.allocation_comparison.target_values["SPY"] == Decimal("6000")
    assert emitted_event.timestamp == now


def test_rebalance_endpoint_missing_required_fields() -> None:
    """Test validation: missing required fields returns 422."""
    app = create_app()
    client = TestClient(app)

    # Missing rebalance_plan, allocation_comparison, etc.
    invalid_payload = {"correlation_id": "test", "trades_required": True}

    response = client.post("/rebalance", json=invalid_payload)

    assert response.status_code == 422
    assert "detail" in response.json()


def test_rebalance_endpoint_invalid_decimal_conversion() -> None:
    """Test validation: invalid decimal string returns 500 with proper error."""
    app = create_app()
    client = TestClient(app)

    now_iso = datetime.now(UTC).isoformat()
    payload = {
        "correlation_id": "corr-portfolio",
        "causation_id": "cause-signal",
        "timestamp": now_iso,
        "rebalance_plan": {
            "correlation_id": "corr-portfolio",
            "causation_id": "cause-signal",
            "timestamp": now_iso,
            "plan_id": "plan-1",
            "items": [],
            "total_portfolio_value": "not-a-number",  # Invalid decimal
            "total_trade_value": "1000",
            "max_drift_tolerance": "0.05",
            "execution_urgency": "HIGH",
            "estimated_duration_minutes": 30,
        },
        "allocation_comparison": {
            "target_values": {"SPY": "6000"},
            "current_values": {"SPY": "5000"},
            "deltas": {"SPY": "1000"},
        },
        "trades_required": True,
    }

    response = client.post("/rebalance", json=payload)

    assert response.status_code == 500
    assert "Event publication failed" in response.json()["detail"]


def test_rebalance_endpoint_event_bus_failure() -> None:
    """Test error handling: EventBus publish failure returns 500."""
    mock_bus = Mock(spec=EventBus)
    mock_bus.publish.side_effect = RuntimeError("EventBus connection failed")

    app = create_app(event_bus=mock_bus)
    client = TestClient(app)

    now_iso = datetime.now(UTC).isoformat()
    payload = {
        "correlation_id": "corr-portfolio",
        "causation_id": "cause-signal",
        "timestamp": now_iso,
        "rebalance_plan": {
            "correlation_id": "corr-portfolio",
            "causation_id": "cause-signal",
            "timestamp": now_iso,
            "plan_id": "plan-1",
            "items": [],
            "total_portfolio_value": "10000",
            "total_trade_value": "1000",
            "max_drift_tolerance": "0.05",
            "execution_urgency": "HIGH",
            "estimated_duration_minutes": 30,
        },
        "allocation_comparison": {
            "target_values": {"SPY": "6000"},
            "current_values": {"SPY": "5000"},
            "deltas": {"SPY": "1000"},
        },
        "trades_required": True,
    }

    response = client.post("/rebalance", json=payload)

    assert response.status_code == 500
    assert "Event publication failed" in response.json()["detail"]


def test_rebalance_endpoint_with_defaults() -> None:
    """Test optional fields: event_id and timestamp default correctly."""
    event_bus = EventBus()
    captured: list[RebalancePlanned] = []
    event_bus.subscribe("RebalancePlanned", lambda event: captured.append(event))

    app = create_app(event_bus=event_bus)
    client = TestClient(app)

    now_iso = datetime.now(UTC).isoformat()
    # Omit optional event_id and timestamp, but include at least one item
    payload = {
        "correlation_id": "corr-portfolio",
        "causation_id": "cause-signal",
        "rebalance_plan": {
            "correlation_id": "corr-portfolio",
            "causation_id": "cause-signal",
            "timestamp": now_iso,
            "plan_id": "plan-1",
            "items": [
                {
                    "symbol": "SPY",
                    "current_weight": "1.0",
                    "target_weight": "1.0",
                    "weight_diff": "0.0",
                    "target_value": "10000",
                    "current_value": "10000",
                    "trade_amount": "0",
                    "action": "HOLD",
                    "priority": 1,
                }
            ],
            "total_portfolio_value": "10000",
            "total_trade_value": "0",
            "max_drift_tolerance": "0.05",
            "execution_urgency": "LOW",
            "estimated_duration_minutes": 30,
        },
        "allocation_comparison": {
            "target_values": {"SPY": "10000"},
            "current_values": {"SPY": "10000"},
            "deltas": {"SPY": "0"},
        },
        "trades_required": False,
    }

    response = client.post("/rebalance", json=payload)

    assert response.status_code == 200
    assert len(captured) == 1
    # event_id should be auto-generated
    assert captured[0].event_id is not None
    # timestamp should default to now
    assert captured[0].timestamp is not None


def test_rebalance_endpoint_uses_header_correlation_id() -> None:
    """Middleware should source trace IDs from headers when payload omits them."""
    event_bus = EventBus()
    captured: list[RebalancePlanned] = []
    event_bus.subscribe("RebalancePlanned", lambda event: captured.append(event))

    app = create_app(event_bus=event_bus)
    client = TestClient(app)

    payload = {
        "rebalance_plan": {
            "plan_id": "plan-123",
            "items": [
                {
                    "symbol": "SPY",
                    "current_weight": "0",
                    "target_weight": "1",
                    "weight_diff": "1",
                    "target_value": "0",
                    "current_value": "0",
                    "trade_amount": "0",
                    "action": "BUY",
                    "priority": 1,
                }
            ],
            "timestamp": datetime.now(UTC).isoformat(),
            "total_portfolio_value": "0",
            "total_trade_value": "0",
            "max_drift_tolerance": "0.05",
        },
        "allocation_comparison": {
            "target_values": {},
            "current_values": {},
            "deltas": {},
        },
        "trades_required": False,
    }

    headers = {
        "X-Correlation-ID": "corr-header-portfolio",
        "X-Causation-ID": "cause-header-portfolio",
    }

    response = client.post("/rebalance", json=payload, headers=headers)

    assert response.status_code == 200
    assert captured[0].correlation_id == "corr-header-portfolio"
    assert captured[0].causation_id == "cause-header-portfolio"


def test_health_endpoint() -> None:
    """Test health check endpoint returns healthy status."""
    app = create_app()
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "service": "portfolio_v2"}


def test_contracts_endpoint_reports_versions() -> None:
    """Contract probe should surface supported events."""
    app = create_app()
    client = TestClient(app)

    response = client.get("/contracts")

    assert response.status_code == 200
    body = response.json()
    assert body["service"] == "portfolio_v2"
    assert body["supported_events"]["RebalancePlanned"] == RebalancePlanned.__event_version__
