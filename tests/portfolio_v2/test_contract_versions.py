"""Contract compatibility checks for portfolio_v2 event and schema usage."""

from the_alchemiser.shared.constants import CONTRACT_VERSION
from the_alchemiser.shared.events import RebalancePlanned, SignalGenerated, WorkflowFailed
from the_alchemiser.shared.schemas.consolidated_portfolio import ConsolidatedPortfolio
from the_alchemiser.shared.schemas.common import AllocationComparison
from the_alchemiser.shared.schemas.rebalance_plan import RebalancePlan, RebalancePlanItem
from the_alchemiser.shared.schemas.strategy_allocation import StrategyAllocation


def test_portfolio_events_are_versioned() -> None:
    events = [SignalGenerated, RebalancePlanned, WorkflowFailed]

    for event in events:
        assert getattr(event, "__event_version__", None) == CONTRACT_VERSION


def test_portfolio_schemas_are_versioned() -> None:
    schemas = [
        ConsolidatedPortfolio,
        AllocationComparison,
        RebalancePlan,
        RebalancePlanItem,
        StrategyAllocation,
    ]

    for schema in schemas:
        assert getattr(schema, "__schema_version__", None) == CONTRACT_VERSION
