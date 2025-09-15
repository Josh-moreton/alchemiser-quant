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

__all__ = [
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
]
