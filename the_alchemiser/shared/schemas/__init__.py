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
    # DSL schemas
    "ASTNode",
    "ASTNodeDTO",
    # Account-related schemas
    "AccountMetrics",
    "AccountSummary",
    # Common schemas
    "AllocationComparison",
    "AllocationComparisonDTO",
    # Asset and broker schemas
    "AssetInfo",
    "AssetInfoDTO",
    "AssetType",
    "BuyingPowerResult",
    "Configuration",
    "ConfigurationDTO",
    # Portfolio schemas
    "ConsolidatedPortfolio",
    "ConsolidatedPortfolioDTO",
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
    "ExecutedOrderDTO",
    "ExecutionReport",
    "ExecutionReportDTO",
    "ExecutionResult",
    "ExecutionResultDTO",
    "ExecutionSummary",
    "ExecutionSummaryDTO",
    # Strategy schemas
    "IndicatorRequest",
    "IndicatorRequestDTO",
    # Event and infrastructure schemas
    "LambdaEvent",
    "LambdaEventDTO",
    # Trading schemas
    "Lot",
    # Market data schemas
    "MarketBar",
    "MarketBarDTO",
    "MarketData",
    "MarketDataDTO",
    "MarketStatusResult",
    "MultiStrategyExecutionResult",
    "MultiStrategyExecutionResultDTO",
    "MultiStrategySummary",
    "MultiStrategySummaryDTO",
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
    "PortfolioMetricsDTO",
    "PortfolioState",
    "PortfolioStateDTO",
    "Position",
    "PositionDTO",
    "PriceHistoryResult",
    "PriceResult",
    "RebalancePlan",
    "RebalancePlanDTO",
    "RebalancePlanItem",
    "RebalancePlanItemDTO",
    # Base schemas
    "Result",
    "RiskMetricsResult",
    "SpreadAnalysisResult",
    "StrategyAllocation",
    "StrategyAllocationDTO",
    "StrategySignal",
    "StrategySignalDTO",
    "TechnicalIndicator",
    "TechnicalIndicatorDTO",
    "Trace",
    "TraceDTO",
    "TraceEntry",
    "TraceEntryDTO",
    "TradeEligibilityResult",
    "TradeLedgerEntry",
    "TradeLedgerQuery",
    "TradeRunResult",
    "TradeRunResultDTO",
    "TradeSide",
    "WebSocketResult",
    "WebSocketStatus",
    # Factory functions
    "create_failure_result",
    "create_success_result",
]
