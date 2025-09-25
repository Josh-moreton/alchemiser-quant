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
from .asset_info import AssetInfo, AssetInfoDTO
from .ast_node import ASTNode, ASTNodeDTO
from .base import Result
from .broker import OrderExecutionResult, WebSocketResult, WebSocketStatus
from .common import (
    AllocationComparison,
    AllocationComparisonDTO,
    Configuration,
    ConfigurationDTO,
    Error,
    ErrorDTO,
    MultiStrategyExecutionResult,
    MultiStrategyExecutionResultDTO,
    MultiStrategySummary,
    MultiStrategySummaryDTO,
)
from .consolidated_portfolio import ConsolidatedPortfolio, ConsolidatedPortfolioDTO
from .errors import (
    ErrorContextData,
    ErrorDetailInfo,
    ErrorNotificationData,
    ErrorReportSummary,
    ErrorSummaryData,
)
from .execution_report import (
    ExecutedOrder,
    ExecutedOrderDTO,
    ExecutionReport,
    ExecutionReportDTO,
)
from .execution_result import ExecutionResult, ExecutionResultDTO
from .indicator_request import IndicatorRequest, IndicatorRequestDTO
from .lambda_event import LambdaEvent, LambdaEventDTO
from .market_bar import MarketBar, MarketBarDTO
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
    PortfolioMetricsDTO,
    PortfolioState,
    PortfolioStateDTO,
    Position,
    PositionDTO,
)
from .rebalance_plan import (
    RebalancePlan,
    RebalancePlanDTO,
    RebalancePlanItem,
    RebalancePlanItemDTO,
)
from .strategy_allocation import (
    StrategyAllocation,
    StrategyAllocationDTO,
)
from .strategy_signal import StrategySignal, StrategySignalDTO
from .technical_indicator import (
    TechnicalIndicator,
    TechnicalIndicatorDTO,
)
from .trace import Trace, TraceDTO, TraceEntry, TraceEntryDTO
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
    ExecutionSummaryDTO,
    OrderResultSummary,
    OrderResultSummaryDTO,
    TradeRunResult,
    TradeRunResultDTO,
)

__all__ = [
    # Account-related schemas
    "AccountMetrics",
    "AccountSummary",
    "BuyingPowerResult",
    "EnrichedAccountSummaryView",
    "PortfolioAllocationResult",
    "RiskMetricsResult",
    "TradeEligibilityResult",
    # Asset and broker schemas
    "AssetInfo",
    "AssetInfoDTO",
    "AssetType",
    "WebSocketResult",
    "WebSocketStatus",
    "OrderExecutionResult",
    # Base schemas
    "Result",
    # Common schemas
    "AllocationComparison",
    "AllocationComparisonDTO",
    "Configuration",
    "ConfigurationDTO",
    "Error",
    "ErrorDTO",
    "MultiStrategyExecutionResult",
    "MultiStrategyExecutionResultDTO",
    "MultiStrategySummary",
    "MultiStrategySummaryDTO",
    # Portfolio schemas
    "ConsolidatedPortfolio",
    "ConsolidatedPortfolioDTO",
    "PortfolioMetrics",
    "PortfolioMetricsDTO", 
    "PortfolioState",
    "PortfolioStateDTO",
    "Position",
    "PositionDTO",
    # Execution schemas
    "ExecutedOrder",
    "ExecutedOrderDTO",
    "ExecutionReport",
    "ExecutionReportDTO",
    "ExecutionResult",
    "ExecutionResultDTO",
    "ExecutionSummary",
    "ExecutionSummaryDTO",
    # Error schemas
    "ErrorContextData",
    "ErrorDetailInfo",
    "ErrorNotificationData",
    "ErrorReportSummary",
    "ErrorSummaryData",
    # Strategy schemas
    "IndicatorRequest",
    "IndicatorRequestDTO",
    "StrategyAllocation",
    "StrategyAllocationDTO",
    "StrategySignal",
    "StrategySignalDTO",
    "TechnicalIndicator",
    "TechnicalIndicatorDTO",
    # Market data schemas
    "MarketBar",
    "MarketBarDTO",
    "MarketData",
    "MarketDataDTO",
    "MarketStatusResult",
    "MultiSymbolQuotesResult",
    "PriceHistoryResult",
    "PriceResult",
    "SpreadAnalysisResult",
    # Event and infrastructure schemas
    "LambdaEvent",
    "LambdaEventDTO",
    # Order and trade schemas
    "OrderRequest",
    "OrderRequestDTO",
    "OrderResultSummary",
    "OrderResultSummaryDTO",
    "RebalancePlan",
    "RebalancePlanDTO",
    "RebalancePlanItem",
    "RebalancePlanItemDTO",
    "TradeRunResult",
    "TradeRunResultDTO",
    # DSL schemas
    "ASTNode",
    "ASTNodeDTO",
    "Trace",
    "TraceDTO",
    "TraceEntry",
    "TraceEntryDTO",
    # Trading schemas
    "Lot",
    "PerformanceSummary",
    "TradeLedgerEntry",
    "TradeLedgerQuery",
    "TradeSide",
    # Factory functions
    "create_failure_result",
    "create_success_result",
]
