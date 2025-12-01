"""Contract compatibility checks for strategy_v2 event and schema usage."""

from the_alchemiser.shared.constants import CONTRACT_VERSION
from the_alchemiser.shared.events import (
    SignalGenerated,
    StartupEvent,
    WorkflowFailed,
    WorkflowStarted,
)
from the_alchemiser.shared.events.dsl_events import (
    FilterEvaluated,
    IndicatorComputed,
    PortfolioAllocationProduced,
    StrategyEvaluated,
    StrategyEvaluationRequested,
    TopNSelected,
)
from the_alchemiser.shared.schemas import StrategySignal
from the_alchemiser.shared.schemas.ast_node import ASTNode
from the_alchemiser.shared.schemas.consolidated_portfolio import ConsolidatedPortfolio
from the_alchemiser.shared.schemas.indicator_request import IndicatorRequest, PortfolioFragment
from the_alchemiser.shared.schemas.market_bar import MarketBar
from the_alchemiser.shared.schemas.strategy_allocation import StrategyAllocation
from the_alchemiser.shared.schemas.technical_indicator import TechnicalIndicator
from the_alchemiser.shared.schemas.trace import Trace


def test_strategy_events_are_versioned() -> None:
    events = [
        StartupEvent,
        WorkflowStarted,
        SignalGenerated,
        WorkflowFailed,
        StrategyEvaluationRequested,
        StrategyEvaluated,
        IndicatorComputed,
        PortfolioAllocationProduced,
        FilterEvaluated,
        TopNSelected,
    ]

    for event in events:
        assert getattr(event, "__event_version__", None) == CONTRACT_VERSION


def test_strategy_schemas_are_versioned() -> None:
    schemas = [
        ASTNode,
        IndicatorRequest,
        PortfolioFragment,
        TechnicalIndicator,
        Trace,
        StrategyAllocation,
        StrategySignal,
        MarketBar,
        ConsolidatedPortfolio,
    ]

    for schema in schemas:
        assert getattr(schema, "__schema_version__", None) == CONTRACT_VERSION
