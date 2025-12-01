from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime
from decimal import Decimal
import json

import httpx
from dependency_injector import providers

from the_alchemiser.orchestration.event_driven_orchestrator import (
    EventDrivenOrchestrator,
)
from the_alchemiser.shared.config.config import Settings
from the_alchemiser.shared.config.container import ApplicationContainer
from the_alchemiser.shared.events import (
    EventBus,
    RebalancePlanned,
    SignalGenerated,
    TradeExecuted,
    WorkflowStarted,
)
from the_alchemiser.shared.schemas.common import AllocationComparison
from the_alchemiser.shared.schemas.rebalance_plan import RebalancePlan, RebalancePlanItem


class _CaptureHandler:
    def __init__(self) -> None:
        self.events: list[str] = []

    def handle_event(self, event) -> None:  # pragma: no cover - test helper
        self.events.append(event.event_type)

    def can_handle(self, event_type: str) -> bool:
        return event_type in {
            "SignalGenerated",
            "RebalancePlanned",
            "TradeExecuted",
        }


def _build_rebalance_payload(correlation_id: str, causation_id: str) -> dict[str, str]:
    plan_item = RebalancePlanItem(
        symbol="AAPL",
        current_weight=Decimal("0.2"),
        target_weight=Decimal("0.3"),
        weight_diff=Decimal("0.1"),
        target_value=Decimal("300"),
        current_value=Decimal("200"),
        trade_amount=Decimal("100"),
        action="BUY",
        priority=1,
    )
    plan = RebalancePlan(
        correlation_id=correlation_id,
        causation_id=causation_id,
        timestamp=datetime.now(UTC),
        plan_id="plan-123",
        items=[plan_item],
        total_portfolio_value=Decimal("1000"),
        total_trade_value=Decimal("100"),
        max_drift_tolerance=Decimal("0.05"),
        execution_urgency="NORMAL",
        metadata={},
    )
    allocation_comparison = AllocationComparison(
        target_values={"AAPL": Decimal("0.3")},
        current_values={"AAPL": Decimal("0.2")},
        deltas={"AAPL": Decimal("0.1")},
    )
    rebalance_event = RebalancePlanned(
        correlation_id=correlation_id,
        causation_id=causation_id,
        event_id="rebalance-event",
        timestamp=datetime.now(UTC),
        source_module="portfolio_v2",
        source_component="api",
        rebalance_plan=plan,
        allocation_comparison=allocation_comparison,
        trades_required=True,
        metadata={},
    )
    return json.loads(rebalance_event.model_dump_json())


def _build_signal_payload(correlation_id: str, causation_id: str) -> dict[str, str]:
    signal_event = SignalGenerated(
        correlation_id=correlation_id,
        causation_id=causation_id,
        event_id="signal-event",
        timestamp=datetime.now(UTC),
        source_module="strategy_v2",
        source_component="api",
        signals_data={"AAPL": {"weight": 0.3}},
        consolidated_portfolio={"AAPL": 0.2},
        signal_count=1,
        metadata={},
    )
    return json.loads(signal_event.model_dump_json())


def _build_execution_payload(correlation_id: str, causation_id: str) -> dict[str, str]:
    execution_event = TradeExecuted(
        correlation_id=correlation_id,
        causation_id=causation_id,
        event_id="execution-event",
        timestamp=datetime.now(UTC),
        source_module="execution_v2",
        source_component="api",
        execution_data={"orders": [{"symbol": "AAPL", "qty": 1}]},
        success=True,
        orders_placed=1,
        orders_succeeded=1,
        metadata={},
        failure_reason=None,
        failed_symbols=[],
    )
    return json.loads(execution_event.model_dump_json())


def _transport_handler(request: httpx.Request) -> httpx.Response:  # pragma: no cover - exercised via orchestration
    body = json.loads(request.content)
    trigger_event = body.get("trigger_event", {})
    correlation_id = trigger_event.get("correlation_id")
    causation_id = trigger_event.get("event_id")

    if "signals" in request.url.path:
        return httpx.Response(200, json={"event": _build_signal_payload(correlation_id, causation_id)})
    if "rebalance" in request.url.path:
        return httpx.Response(200, json={"event": _build_rebalance_payload(correlation_id, causation_id)})
    if "executions" in request.url.path:
        return httpx.Response(200, json={"event": _build_execution_payload(correlation_id, causation_id)})

    return httpx.Response(404)


def test_full_http_workflow_emits_expected_events(monkeypatch) -> None:
    container = ApplicationContainer.create_for_testing()
    custom_settings = Settings()
    custom_settings.orchestration.use_http_domain_workflow = True
    custom_settings.orchestration.strategy_endpoint = "http://strategy.local/signals"
    custom_settings.orchestration.portfolio_endpoint = "http://portfolio.local/rebalance"
    custom_settings.orchestration.execution_endpoint = "http://execution.local/executions"
    container.config.settings.override(providers.Object(custom_settings))

    http_client = httpx.Client(transport=httpx.MockTransport(_transport_handler))
    orchestrator = EventDrivenOrchestrator(container, http_client=http_client)

    event_bus: EventBus = container.services.event_bus()
    capture_handler = _CaptureHandler()
    for event_type in ("SignalGenerated", "RebalancePlanned", "TradeExecuted"):
        event_bus.subscribe(event_type, capture_handler)

    correlation_id = "corr-http-123"
    start_event = WorkflowStarted(
        correlation_id=correlation_id,
        causation_id="system-start",
        event_id="workflow-start-event",
        timestamp=datetime.now(UTC),
        source_module="orchestration.test",
        source_component="test_full_http_workflow_emits_expected_events",
        workflow_type="trading",
        requested_by="tester",
        configuration={},
    )

    event_bus.publish(start_event)

    assert Counter(capture_handler.events) == Counter(
        ["SignalGenerated", "RebalancePlanned", "TradeExecuted"]
    )

    results = orchestrator.wait_for_workflow_completion(correlation_id, timeout_seconds=5)
    assert results["success"] is True
    assert results["correlation_id"] == correlation_id
    assert results["orders_executed"] == [{"symbol": "AAPL", "qty": 1}]
