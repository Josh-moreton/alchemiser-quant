from __future__ import annotations

from datetime import UTC, datetime

from fastapi.testclient import TestClient

from the_alchemiser.shared.events import EventBus, SignalGenerated
from the_alchemiser.strategy_v2.api import create_app


def test_signals_endpoint_emits_signal_generated() -> None:
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
