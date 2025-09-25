"""Shared schemas module.

Business Unit: shared | Status: current

Common schema definitions used across modules.
"""

from .accounts import (
    AccountMetrics,
    AccountSummary,
    BuyingPowerResult,
    EnrichedAccountSummaryView,
    PortfolioAllocationResult,
    RiskMetricsResult,
    TradeEligibilityResult,
)
from .assets import AssetInfo
from .ast_nodes import ASTNode
from .base import Result
from .common import (
    AllocationComparison,
    MultiStrategyExecutionResult,
    MultiStrategySummary,
)
from .consolidated_portfolio import ConsolidatedPortfolio
from .errors import (
    ErrorContextData,
    ErrorDetailInfo,
    ErrorNotificationData,
    ErrorReportSummary,
    ErrorSummaryData,
)
from .execution_reports import ExecutedOrder, ExecutionReport
from .market_bars import MarketBar
from .market_data import (
    MarketStatusResult,
    MultiSymbolQuotesResult,
    PriceHistoryResult,
    PriceResult,
    SpreadAnalysisResult,
)
from .portfolio import PortfolioMetrics, PortfolioSnapshot, Position
from .rebalancing import RebalancePlan, RebalancePlanItem
from .signals import StrategySignal
from .strategy import StrategyAllocation
from .technical_indicators import TechnicalIndicator
from .traces import Trace, TraceEntry
from .trade_results import OrderResultSummary, TradeExecutionSummary, TradeRunResult

__all__ = [
    "AccountMetrics",
    "AccountSummary",
    "AllocationComparison",
    "ASTNode",
    "AssetInfo",
    "BuyingPowerResult",
    "ConsolidatedPortfolio",
    "EnrichedAccountSummaryView",
    "ErrorContextData",
    "ErrorDetailInfo",
    "ErrorNotificationData",
    "ErrorReportSummary",
    "ErrorSummaryData",
    "ExecutedOrder",
    "ExecutionReport",
    "MarketBar",
    "MarketStatusResult",
    "MultiStrategyExecutionResult",
    "MultiStrategySummary",
    "MultiSymbolQuotesResult",
    "OrderResultSummary",
    "PortfolioAllocationResult",
    "PortfolioMetrics",
    "PortfolioSnapshot",
    "Position",
    "PriceHistoryResult",
    "PriceResult",
    "RebalancePlan",
    "RebalancePlanItem",
    "Result",
    "RiskMetricsResult",
    "SpreadAnalysisResult",
    "StrategyAllocation",
    "StrategySignal",
    "TechnicalIndicator",
    "Trace",
    "TraceEntry",
    "TradeEligibilityResult",
    "TradeExecutionSummary",
    "TradeRunResult",
]
