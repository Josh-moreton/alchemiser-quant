"""Data transfer objects.

DEPRECATED: This module is deprecated. Use `the_alchemiser.shared.schemas` instead.
This module will be removed in a future version.
"""

from __future__ import annotations

import warnings

# Re-export everything from schemas for backward compatibility
from the_alchemiser.shared.schemas import (
    AssetInfo,
    AssetInfoDTO,
    AssetType,
    Configuration,
    ConfigurationDTO,
    Error,
    ErrorDTO,
    ExecutedOrder,
    ExecutedOrderDTO,
    ExecutionReport,
    ExecutionReportDTO,
    ExecutionSummary,
    ExecutionSummaryDTO,
    LambdaEvent,
    LambdaEventDTO,
    Lot,
    MarketBar,
    MarketBarDTO,
    MarketData,
    MarketDataDTO,
    OrderRequest,
    OrderRequestDTO,
    OrderResultSummary,
    OrderResultSummaryDTO,
    PerformanceSummary,
    PortfolioMetrics,
    PortfolioMetricsDTO,
    PortfolioState,
    PortfolioStateDTO,
    Position,
    PositionDTO,
    RebalancePlan,
    RebalancePlanDTO,
    RebalancePlanItem,
    RebalancePlanItemDTO,
    StrategyAllocation,
    StrategyAllocationDTO,
    StrategySignal,
    StrategySignalDTO,
    TechnicalIndicator,
    TechnicalIndicatorDTO,
    TradeLedgerEntry,
    TradeLedgerQuery,
    TradeRunResult,
    TradeRunResultDTO,
)


class Configuration(BaseModel):
    """Placeholder for configuration data transfer.

    Proper Pydantic v2 DTO to replace placeholder class.
    Will be enhanced with specific config fields in Phase 2.
    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    config_data: dict[str, Any] = Field(
        default_factory=dict,
        description="Configuration data (flexible for Phase 1 scaffolding)",
    )


class Error(BaseModel):
    """Placeholder for error data transfer.

    Proper Pydantic v2 DTO to replace placeholder class.
    Will be enhanced with specific error fields in Phase 2.
    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    error_type: str = Field(description="Type of error")
    message: str = Field(description="Error message")
    context: dict[str, Any] = Field(
        default_factory=dict, description="Error context data"
    )


__all__ = [
    "AssetInfo",
    "AssetInfoDTO",
    "AssetType",
    "Configuration",
    "ConfigurationDTO",
    "Error",
    "ErrorDTO",
    "ExecutedOrder",
    "ExecutedOrderDTO",
    "ExecutionReport",
    "ExecutionReportDTO",
    "ExecutionSummary",
    "ExecutionSummaryDTO",
    "LambdaEvent",
    "LambdaEventDTO",
    "Lot",
    "MarketBar",
    "MarketBarDTO",
    "MarketData",
    "MarketDataDTO",
    "OrderRequest",
    "OrderRequestDTO",
    "OrderResultSummary",
    "OrderResultSummaryDTO",
    "PerformanceSummary",
    "PortfolioMetrics",
    "PortfolioMetricsDTO",
    "PortfolioState",
    "PortfolioStateDTO",
    "Position",
    "PositionDTO",
    "RebalancePlan",
    "RebalancePlanDTO",
    "RebalancePlanItem",
    "RebalancePlanItemDTO",
    "StrategyAllocation",
    "StrategyAllocationDTO",
    "StrategySignal",
    "StrategySignalDTO",
    "TechnicalIndicator",
    "TechnicalIndicatorDTO",
    "TradeLedgerEntry",
    "TradeLedgerQuery",
    "TradeRunResult",
    "TradeRunResultDTO",
    "TradeSide",
]
