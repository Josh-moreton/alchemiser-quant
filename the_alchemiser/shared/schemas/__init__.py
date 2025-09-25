"""Shared schemas module.

Business Unit: shared | Status: current

Common schema definitions used across modules.
"""

# Import existing parent-level schemas (from .py files)
from .accounts import (
    AccountMetrics,
    AccountSummary,
    BuyingPowerResult,
    EnrichedAccountSummaryView,
    PortfolioAllocationResult,
    RiskMetricsResult,
    TradeEligibilityResult,
)
from .base import Result
from .common import (
    AllocationComparisonDTO,
    MultiStrategyExecutionResultDTO,
    MultiStrategySummaryDTO,
)
from .errors import (
    ErrorContextData,
    ErrorDetailInfo,
    ErrorNotificationData,
    ErrorReportSummary,
    ErrorSummaryData,
)
from .market_data import (
    MarketStatusResult,
    MultiSymbolQuotesResult,
    PriceHistoryResult,
    PriceResult,
    SpreadAnalysisResult,
)

# Import from new submodules (from subdirectories)
from .execution import *
from .market import *
from .portfolio import *  
from .strategy import *
from .system import *

__all__ = [
    # From parent-level modules
    "AccountMetrics",
    "AccountSummary",
    "AllocationComparisonDTO",
    "BuyingPowerResult",
    "EnrichedAccountSummaryView",
    "ErrorContextData",
    "ErrorDetailInfo",
    "ErrorNotificationData",
    "ErrorReportSummary",
    "ErrorSummaryData",
    "MarketStatusResult",
    "MultiStrategyExecutionResultDTO",
    "MultiStrategySummaryDTO",
    "MultiSymbolQuotesResult",
    "PortfolioAllocationResult",
    "PriceHistoryResult",
    "PriceResult",
    "Result",
    "RiskMetricsResult",
    "SpreadAnalysisResult",
    "TradeEligibilityResult",
    
    # From execution submodule  
    "ExecutedOrderDTO",
    "ExecutionReportDTO",
    "ExecutionResult",
    "ExecutionSummaryDTO",
    "MarketDataDTO",
    "OrderRequestDTO",
    "OrderResultSummaryDTO",
    "TradeRunResultDTO",
    
    # From market submodule
    "AssetInfoDTO",
    "MarketBarDTO",
    
    # From portfolio submodule
    "AssetType",
    "ConsolidatedPortfolioDTO",
    "Lot",
    "PerformanceSummary",
    "PortfolioMetricsDTO",
    "PortfolioStateDTO",
    "PositionDTO",
    "RebalancePlanDTO",
    "RebalancePlanItemDTO",
    "TradeLedgerEntry",
    "TradeLedgerQuery",
    "TradeSide",
    
    # From strategy submodule
    "IndicatorRequestDTO",
    "StrategyAllocationDTO",
    "StrategySignalDTO", 
    "TechnicalIndicatorDTO",
    
    # From system submodule
    "ASTNodeDTO",
    "LambdaEventDTO",
    "TraceDTO",
    "WebSocketResult",
    "WebSocketStatus",
]
