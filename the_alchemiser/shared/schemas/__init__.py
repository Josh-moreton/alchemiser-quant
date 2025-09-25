"""Shared schemas module.

Business Unit: shared | Status: current

Common schema definitions used across modules.
"""

# Import from organized submodules
from .core import *
from .dsl import *
from .execution import *
from .market import *
from .portfolio import *
from .strategy import *
from .system import *

__all__ = [
    # Core schemas
    "AllocationComparison",
    "ErrorContextData",
    "ErrorDetailInfo", 
    "ErrorNotificationData",
    "ErrorReportSummary",
    "ErrorSummaryData",
    "MultiStrategyExecutionResult",
    "MultiStrategySummary",
    "Result",
    
    # Portfolio schemas
    "AccountMetrics",
    "AccountSummary",
    "BuyingPowerResult",
    "ConsolidatedPortfolio",
    "EnrichedAccountSummaryView",
    "PortfolioAllocationResult",
    "PortfolioMetrics",
    "PortfolioSnapshot",
    "Position",
    "RebalancePlan",
    "RebalancePlanItem",
    "RiskMetricsResult",
    "TradeEligibilityResult",
    
    # Execution schemas
    "ExecutedOrder",
    "ExecutionReport",
    "OperationResult",
    "OrderCancellationResult",
    "OrderResultSummary",
    "OrderStatusResult",
    "TradeExecutionSummary",
    "TradeRunResult",
    
    # Strategy schemas
    "IndicatorRequest",
    "PortfolioFragment",
    "StrategyAllocation",
    "StrategySignal",
    "TechnicalIndicator",
    
    # Market schemas
    "MarketBar",
    "MarketData", 
    "MarketStatusResult",
    "MultiSymbolQuotesResult",
    "OrderRequest",
    "PriceHistoryResult",
    "PriceResult",
    "SpreadAnalysisResult",
    
    # System schemas
    "AssetInfo",
    "Configuration",
    "EnrichedOrderView",
    "EnrichedPositionView",
    "EnrichedPositionsView",
    "Error",
    "LambdaEvent",
    "OpenOrdersView",
    
    # DSL schemas
    "ASTNode",
    "Trace",
    "TraceEntry",
]
