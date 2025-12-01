"""Contract compatibility checks for execution_v2 event and schema usage."""

from the_alchemiser.shared.constants import CONTRACT_VERSION
from the_alchemiser.shared.events import (
    BulkSettlementCompleted,
    ExecutionPhaseCompleted,
    OrderSettlementCompleted,
    RebalancePlanned,
    TradeExecuted,
    WorkflowCompleted,
    WorkflowFailed,
)
from the_alchemiser.shared.schemas.execution_report import ExecutedOrder
from the_alchemiser.shared.schemas.rebalance_plan import RebalancePlan, RebalancePlanItem
from the_alchemiser.shared.schemas.trade_ledger import TradeLedger, TradeLedgerEntry


def test_execution_events_are_versioned() -> None:
    events = [
        RebalancePlanned,
        TradeExecuted,
        WorkflowCompleted,
        WorkflowFailed,
        BulkSettlementCompleted,
        OrderSettlementCompleted,
        ExecutionPhaseCompleted,
    ]

    for event in events:
        assert getattr(event, "__event_version__", None) == CONTRACT_VERSION


def test_execution_schemas_are_versioned() -> None:
    schemas = [
        RebalancePlan,
        RebalancePlanItem,
        ExecutedOrder,
        TradeLedger,
        TradeLedgerEntry,
    ]

    for schema in schemas:
        assert getattr(schema, "__schema_version__", None) == CONTRACT_VERSION
