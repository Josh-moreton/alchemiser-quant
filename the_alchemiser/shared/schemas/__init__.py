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
from .asset_info import AssetInfo, AssetInfo
from .ast_node import ASTNode, ASTNode
from .base import Result
from .broker import OrderExecutionResult, WebSocketResult, WebSocketStatus
from .common import (
    AllocationComparison,
    AllocationComparison,
    Configuration,
    ConfigurationDTO,
    Error,
    ErrorDTO,
    MultiStrategyExecutionResult,
    MultiStrategyExecutionResult,
    MultiStrategySummary,
    MultiStrategySummary,
)
from .consolidated_portfolio import ConsolidatedPortfolio, ConsolidatedPortfolio
from .errors import (
    ErrorContextData,
    ErrorDetailInfo,
    ErrorNotificationData,
    ErrorReportSummary,
    ErrorSummaryData,
)
from .execution_report import (
    ExecutedOrder,
    ExecutedOrder,
    ExecutionReport,
    ExecutionReportDTO,
)
from .execution_result import ExecutionResult, ExecutionResult
from .indicator_request import IndicatorRequest, IndicatorRequest
from .lambda_event import LambdaEvent, LambdaEvent
from .market_bar import MarketBar, MarketBar
from .market_data import (
    MarketStatusResult,
    MultiSymbolQuotesResult,
    PriceHistoryResult,
    PriceResult,
    SpreadAnalysisResult,
)
from .order_request import (
    MarketData,
    MarketDataDTO,
    OrderRequest,
    OrderRequestDTO,
)
from .portfolio_state import (
    PortfolioMetrics,
    PortfolioMetrics,
    PortfolioState,
    PortfolioState,
    Position,
    PositionDTO,
)
from .rebalance_plan import (
    RebalancePlan,
    RebalancePlan,
    RebalancePlanItem,
    RebalancePlanItem,
)
from .strategy_allocation import (
    StrategyAllocation,
    StrategyAllocation,
)
from .strategy_signal import StrategySignal, StrategySignalDTO
from .technical_indicator import (
    TechnicalIndicator,
    TechnicalIndicator,
)
from .trace import Trace, Trace, TraceEntry, TraceEntryDTO
from .trade_ledger import (
    AssetType,
    Lot,
    PerformanceSummary,
    TradeLedgerEntry,
    TradeLedgerQuery,
    TradeSide,
)
from .trade_result_factory import create_failure_result, create_success_result
from .trade_run_result import (
    ExecutionSummary,
    ExecutionSummary,
    OrderResultSummary,
    OrderResultSummaryDTO,
    TradeRunResult,
    TradeRunResult,
)

__all__ = [
    # DSL schemas
    "ASTNode",
    "ASTNode",
    # Account-related schemas
    "AccountMetrics",
    "AccountSummary",
    # Common schemas
    "AllocationComparison",
    "AllocationComparison",
    # Asset and broker schemas
    "AssetInfo",
    "AssetInfo",
    "AssetType",
    "BuyingPowerResult",
    "Configuration",
    "ConfigurationDTO",
    # Portfolio schemas
    "ConsolidatedPortfolio",
    "ConsolidatedPortfolio",
    "EnrichedAccountSummaryView",
    "Error",
    # Error schemas
    "ErrorContextData",
    "ErrorDTO",
    "ErrorDetailInfo",
    "ErrorNotificationData",
    "ErrorReportSummary",
    "ErrorSummaryData",
    # Execution schemas
    "ExecutedOrder",
    "ExecutedOrder",
    "ExecutionReport",
    "ExecutionReportDTO",
    "ExecutionResult",
    "ExecutionResult",
    "ExecutionSummary",
    "ExecutionSummary",
    # Strategy schemas
    "IndicatorRequest",
    "IndicatorRequest",
    # Event and infrastructure schemas
    "LambdaEvent",
    "LambdaEvent",
    # Trading schemas
    "Lot",
    # Market data schemas
    "MarketBar",
    "MarketBar",
    "MarketData",
    "MarketDataDTO",
    "MarketStatusResult",
    "MultiStrategyExecutionResult",
    "MultiStrategyExecutionResult",
    "MultiStrategySummary",
    "MultiStrategySummary",
    "MultiSymbolQuotesResult",
    "OrderExecutionResult",
    # Order and trade schemas
    "OrderRequest",
    "OrderRequestDTO",
    "OrderResultSummary",
    "OrderResultSummaryDTO",
    "PerformanceSummary",
    "PortfolioAllocationResult",
    "PortfolioMetrics",
    "PortfolioMetrics",
    "PortfolioState",
    "PortfolioState",
    "Position",
    "PositionDTO",
    "PriceHistoryResult",
    "PriceResult",
    "RebalancePlan",
    "RebalancePlan",
    "RebalancePlanItem",
    "RebalancePlanItem",
    # Base schemas
    "Result",
    "RiskMetricsResult",
    "SpreadAnalysisResult",
    "StrategyAllocation",
    "StrategyAllocation",
    "StrategySignal",
    "StrategySignalDTO",
    "TechnicalIndicator",
    "TechnicalIndicator",
    "Trace",
    "Trace",
    "TraceEntry",
    "TraceEntryDTO",
    "TradeEligibilityResult",
    "TradeLedgerEntry",
    "TradeLedgerQuery",
    "TradeRunResult",
    "TradeRunResult",
    "TradeSide",
    "WebSocketResult",
    "WebSocketStatus",
    # Factory functions
    "create_failure_result",
    "create_success_result",
]
