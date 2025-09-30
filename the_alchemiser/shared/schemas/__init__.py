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
from .asset_info import AssetInfo
from .ast_node import ASTNode
from .base import Result
from .broker import OrderExecutionResult, WebSocketResult, WebSocketStatus
from .common import (
    AllocationComparison,
    Configuration,
    Error,
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
from .execution_report import (
    ExecutedOrder,
    ExecutionReport,
)
from .execution_result import ExecutionResult
from .indicator_request import IndicatorRequest
from .lambda_event import LambdaEvent
from .market_bar import MarketBar
from .market_data import (
    MarketStatusResult,
    MultiSymbolQuotesResult,
    PriceHistoryResult,
    PriceResult,
    SpreadAnalysisResult,
)
from .order_request import (
    MarketData,
    OrderRequest,
)
from .pnl import PnLData
from .portfolio_state import (
    PortfolioMetrics,
    PortfolioState,
    Position,
)
from .rebalance_plan import (
    RebalancePlan,
    RebalancePlanItem,
)
from .strategy_allocation import (
    StrategyAllocation,
)
from .strategy_signal import StrategySignal
from .technical_indicator import (
    TechnicalIndicator,
)
from .trace import Trace, TraceEntry
from .trade_result_factory import create_failure_result, create_success_result
from .trade_run_result import (
    ExecutionSummary,
    OrderResultSummary,
    TradeRunResult,
)

__all__ = [
    "ASTNode",
    "AccountMetrics",
    "AccountSummary",
    "AllocationComparison",
    "AssetInfo",
    "BuyingPowerResult",
    "Configuration",
    "ConsolidatedPortfolio",
    "EnrichedAccountSummaryView",
    "Error",
    "ErrorContextData",
    "ErrorDetailInfo",
    "ErrorNotificationData",
    "ErrorReportSummary",
    "ErrorSummaryData",
    "ExecutedOrder",
    "ExecutionReport",
    "ExecutionResult",
    "ExecutionSummary",
    "IndicatorRequest",
    "LambdaEvent",
    "MarketBar",
    "MarketData",
    "MarketStatusResult",
    "MultiStrategyExecutionResult",
    "MultiStrategySummary",
    "MultiSymbolQuotesResult",
    "OrderExecutionResult",
    "OrderRequest",
    "OrderResultSummary",
    "PnLData",
    "PortfolioAllocationResult",
    "PortfolioMetrics",
    "PortfolioState",
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
    "TradeRunResult",
    "WebSocketResult",
    "WebSocketStatus",
    "create_failure_result",
    "create_success_result",
]
