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
from .assets import AssetInfoDTO
from .base import Result
from .broker import WebSocketResult, WebSocketStatus
from .common import (
    AllocationComparisonDTO,
    MultiStrategyExecutionResultDTO,
    MultiStrategySummaryDTO,
)
from .dsl import ASTNodeDTO, TraceDTO, TraceEntryDTO
from .errors import (
    ErrorContextData,
    ErrorDetailInfo,
    ErrorNotificationData,
    ErrorReportSummary,
    ErrorSummaryData,
)
from .events import LambdaEventDTO
from .execution import ExecutionResult
from .indicators import TechnicalIndicatorDTO
from .market_data import (
    MarketBarDTO,
    MarketStatusResult,
    MultiSymbolQuotesResult,
    PriceHistoryResult,
    PriceResult,
    SpreadAnalysisResult,
)
from .orders import MarketDataDTO, OrderRequestDTO
from .portfolio import PortfolioMetricsDTO, PortfolioStateDTO, PositionDTO
from .strategy import StrategyAllocationDTO, StrategySignalDTO
from .trading import (
    AssetType,
    Lot,
    PerformanceSummary,
    TradeLedgerEntry,
    TradeLedgerQuery,
    TradeSide,
)

__all__ = [
    "AccountMetrics",
    "AccountSummary",
    "AllocationComparisonDTO",
    "ASTNodeDTO",
    "AssetInfoDTO",
    "AssetType",
    "BuyingPowerResult",
    "EnrichedAccountSummaryView",
    "ErrorContextData",
    "ErrorDetailInfo",
    "ErrorNotificationData",
    "ErrorReportSummary",
    "ErrorSummaryData",
    "ExecutionResult",
    "LambdaEventDTO",
    "Lot",
    "MarketBarDTO",
    "MarketDataDTO",
    "MarketStatusResult",
    "MultiStrategyExecutionResultDTO",
    "MultiStrategySummaryDTO",
    "MultiSymbolQuotesResult",
    "OrderRequestDTO",
    "PerformanceSummary",
    "PortfolioAllocationResult",
    "PortfolioMetricsDTO",
    "PortfolioStateDTO",
    "PositionDTO",
    "PriceHistoryResult",
    "PriceResult",
    "Result",
    "RiskMetricsResult",
    "SpreadAnalysisResult",
    "StrategyAllocationDTO",
    "StrategySignalDTO",
    "TechnicalIndicatorDTO",
    "TradeLedgerEntry",
    "TradeLedgerQuery",
    "TraceDTO",
    "TraceEntryDTO",
    "TradeEligibilityResult",
    "TradeSide",
    "WebSocketResult",
    "WebSocketStatus",
]
