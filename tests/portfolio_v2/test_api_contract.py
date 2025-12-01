from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from fastapi.testclient import TestClient

from the_alchemiser.portfolio_v2.api import create_app
from the_alchemiser.shared.events import EventBus, RebalancePlanned


def test_rebalance_endpoint_emits_rebalance_planned() -> None:
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
