from __future__ import annotations

from datetime import UTC, datetime

from fastapi.testclient import TestClient

from the_alchemiser.execution_v2.api import create_app
from the_alchemiser.shared.events import EventBus, TradeExecuted


def test_executions_endpoint_emits_trade_executed() -> None:
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
