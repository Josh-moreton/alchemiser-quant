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
from .base import Result
from .broker import WebSocketResult, WebSocketStatus
from .common import (
    AllocationComparison,
    MultiStrategyExecutionResult,
    MultiStrategySummary,
)
from .dsl import ASTNode, Trace, TraceEntry
from .errors import (
    ErrorContextData,
    ErrorDetailInfo,
    ErrorNotificationData,
    ErrorReportSummary,
    ErrorSummaryData,
)
from .events import LambdaEvent
from .execution import ExecutionResult
from .indicators import TechnicalIndicator
from .market_data import (
    MarketBar,
    MarketStatusResult,
    MultiSymbolQuotesResult,
    PriceHistoryResult,
    PriceResult,
    SpreadAnalysisResult,
)
from .orders import MarketData, OrderRequest
from .portfolio import PortfolioMetrics, PortfolioState, Position
from .strategy import StrategyAllocation, StrategySignal
from .trading import (
    AssetType,
    Lot,
    PerformanceSummary,
    TradeLedgerEntry,
    TradeLedgerQuery,
    TradeSide,
)

__all__ = [
    "ASTNode",
    "AccountMetrics",
    "AccountSummary",
    "AllocationComparison",
    "AssetInfo",
    "AssetType",
    "BuyingPowerResult",
    "EnrichedAccountSummaryView",
    "ErrorContextData",
    "ErrorDetailInfo",
    "ErrorNotificationData",
    "ErrorReportSummary",
    "ErrorSummaryData",
    "ExecutionResult",
    "LambdaEvent",
    "Lot",
    "MarketBar",
    "MarketData",
    "MarketStatusResult",
    "MultiStrategyExecutionResult",
    "MultiStrategySummary",
    "MultiSymbolQuotesResult",
    "OrderRequest",
    "PerformanceSummary",
    "PortfolioAllocationResult",
    "PortfolioMetrics",
    "PortfolioState",
    "Position",
    "PriceHistoryResult",
    "PriceResult",
    "Result",
    "RiskMetricsResult",
    "SpreadAnalysisResult",
    "StrategyAllocation",
    "StrategySignal",
    "TechnicalIndicator",
    "Trace",
    "TraceEntry",
    "TradeEligibilityResult",
    "TradeLedgerEntry",
    "TradeLedgerQuery",
    "TradeSide",
    "WebSocketResult",
    "WebSocketStatus",
]
