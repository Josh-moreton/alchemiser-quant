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
from .common import (
    AllocationComparison,
    MultiStrategyExecutionResult,
    MultiStrategySummary,
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
from .portfolio import PortfolioMetrics, PortfolioSnapshot, Position
from .rebalancing import RebalancePlan, RebalancePlanItem

__all__ = [
    "AccountMetrics",
    "AccountSummary",
    "AllocationComparison",
    "AssetInfo",
    "BuyingPowerResult",
    "EnrichedAccountSummaryView",
    "ErrorContextData",
    "ErrorDetailInfo",
    "ErrorNotificationData",
    "ErrorReportSummary",
    "ErrorSummaryData",
    "MarketStatusResult",
    "MultiStrategyExecutionResult",
    "MultiStrategySummary",
    "MultiSymbolQuotesResult",
    "PortfolioAllocationResult",
    "PortfolioMetrics",
    "PortfolioSnapshot",
    "Position",
    "PriceHistoryResult",
    "PriceResult",
    "RebalancePlan",
    "RebalancePlanItem",
    "Result",
    "RiskMetricsResult",
    "SpreadAnalysisResult",
    "TradeEligibilityResult",
]
