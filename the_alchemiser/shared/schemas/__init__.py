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
    # Base schemas
    "Result",
    # Account schemas
    "AccountSummary",
    "AccountMetrics",
    "BuyingPowerResult",
    "RiskMetricsResult",
    "TradeEligibilityResult",
    "PortfolioAllocationResult",
    "EnrichedAccountSummaryView",
    # Common schemas
    "MultiStrategyExecutionResultDTO",
    "AllocationComparisonDTO",
    "MultiStrategySummaryDTO",
    # Error schemas
    "ErrorDetailInfo",
    "ErrorSummaryData",
    "ErrorReportSummary",
    "ErrorNotificationData",
    "ErrorContextData",
    # Market data schemas
    "PriceResult",
    "PriceHistoryResult",
    "SpreadAnalysisResult",
    "MarketStatusResult",
    "MultiSymbolQuotesResult",
]
