"""Smoke tests for FastAPI surfaces emitting events."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from the_alchemiser.execution_v2.api import create_app as create_execution_app
from the_alchemiser.portfolio_v2.api import create_app as create_portfolio_app
from the_alchemiser.shared.events import EventBus, RebalancePlanned, SignalGenerated, TradeExecuted
from the_alchemiser.strategy_v2.api import create_app as create_strategy_app


pytestmark = pytest.mark.e2e


def _headers(prefix: str) -> dict[str, str]:
    return {"X-Correlation-ID": f"{prefix}-corr", "X-Causation-ID": f"{prefix}-cause"}


def test_strategy_smoke_round_trip() -> None:
    bus = EventBus()
    captured: list[SignalGenerated] = []
    bus.subscribe("SignalGenerated", lambda event: captured.append(event))

    client = TestClient(create_strategy_app(event_bus=bus))

    payload = {
        "signals_data": {"SPY": {"signal": "BUY", "weight": 0.6}},
        "consolidated_portfolio": {"SPY": 0.6, "QQQ": 0.4},
        "signal_count": 1,
    }

    response = client.post("/signals", json=payload, headers=_headers("strategy"))

    assert response.status_code == 200
    assert len(captured) == 1
    assert captured[0].correlation_id == "strategy-corr"
    assert captured[0].causation_id == "strategy-cause"

    contract = client.get("/contracts").json()
    assert contract["supported_events"]["SignalGenerated"] == SignalGenerated.__event_version__


def test_execution_smoke_round_trip() -> None:
    bus = EventBus()
    captured: list[TradeExecuted] = []
    bus.subscribe("TradeExecuted", lambda event: captured.append(event))

    client = TestClient(create_execution_app(event_bus=bus))

    payload = {
        "execution_data": {"orders": [{"symbol": "SPY", "qty": 10}]},
        "success": True,
        "orders_placed": 1,
        "orders_succeeded": 1,
    }

    response = client.post("/executions", json=payload, headers=_headers("execution"))

    assert response.status_code == 200
    assert len(captured) == 1
    assert captured[0].correlation_id == "execution-corr"
    assert captured[0].causation_id == "execution-cause"

    contract = client.get("/contracts").json()
    assert contract["supported_events"]["TradeExecuted"] == TradeExecuted.__event_version__


def test_portfolio_smoke_round_trip() -> None:
    bus = EventBus()
    captured: list[RebalancePlanned] = []
    bus.subscribe("RebalancePlanned", lambda event: captured.append(event))

    client = TestClient(create_portfolio_app(event_bus=bus))

    payload = {
        "rebalance_plan": {
            "plan_id": "plan-smoke",
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

    response = client.post("/rebalance", json=payload, headers=_headers("portfolio"))

    assert response.status_code == 200
    assert len(captured) == 1
    assert captured[0].correlation_id == "portfolio-corr"
    assert captured[0].causation_id == "portfolio-cause"

    contract = client.get("/contracts").json()
    assert contract["supported_events"]["RebalancePlanned"] == RebalancePlanned.__event_version__
