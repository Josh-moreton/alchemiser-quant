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
    ConfigurationDTO,
    Error,
    ErrorDTO,
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
    ExecutionReportDTO,
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
    MarketDataDTO,
    OrderRequest,
    OrderRequestDTO,
)
from .portfolio_state import (
    PortfolioMetrics,
    PortfolioState,
    Position,
    PositionDTO,
)
from .rebalance_plan import (
    RebalancePlan,
    RebalancePlanItem,
)
from .strategy_allocation import (
    StrategyAllocation,
)
from .strategy_signal import StrategySignal, StrategySignalDTO
from .technical_indicator import (
    TechnicalIndicator,
)
from .trace import Trace, TraceEntry, TraceEntryDTO
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
    OrderResultSummary,
    OrderResultSummaryDTO,
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
