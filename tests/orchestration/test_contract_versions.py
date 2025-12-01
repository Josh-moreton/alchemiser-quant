"""Contract compatibility checks for orchestration event and schema usage."""

from the_alchemiser.shared.constants import CONTRACT_VERSION
from the_alchemiser.shared.events import (
    ReportReady,
    StartupEvent,
    SystemNotificationRequested,
    TradingNotificationRequested,
    WorkflowCompleted,
    WorkflowFailed,
    WorkflowStarted,
)
from the_alchemiser.shared.schemas.trade_run_result import (
    ExecutionSummary,
    OrderResultSummary,
    TradeRunResult,
)


def test_orchestration_events_are_versioned() -> None:
    events = [
        StartupEvent,
        WorkflowStarted,
        WorkflowCompleted,
        WorkflowFailed,
        TradingNotificationRequested,
        SystemNotificationRequested,
        ReportReady,
    ]

    for event in events:
        assert getattr(event, "__event_version__", None) == CONTRACT_VERSION


def test_orchestration_schemas_are_versioned() -> None:
    schemas = [OrderResultSummary, ExecutionSummary, TradeRunResult]

    for schema in schemas:
        assert getattr(schema, "__schema_version__", None) == CONTRACT_VERSION
