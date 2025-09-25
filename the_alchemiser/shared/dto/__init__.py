"""Data transfer objects.

Typed DTOs for inter-module communication with correlation tracking
and serialization helpers.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

# Import implemented DTOs
from the_alchemiser.shared.dto.asset_info_dto import AssetInfo, AssetInfoDTO
from the_alchemiser.shared.dto.execution_report_dto import (
    ExecutedOrder,
    ExecutedOrderDTO,
    ExecutionReport,
    ExecutionReportDTO,
)
from the_alchemiser.shared.dto.lambda_event_dto import LambdaEvent, LambdaEventDTO
from the_alchemiser.shared.dto.market_bar_dto import MarketBar, MarketBarDTO
from the_alchemiser.shared.dto.order_request_dto import (
    MarketData,
    MarketDataDTO,
    OrderRequest,
    OrderRequestDTO,
)
from the_alchemiser.shared.dto.portfolio_state_dto import (
    PortfolioMetrics,
    PortfolioMetricsDTO,
    PortfolioState,
    PortfolioStateDTO,
    Position,
    PositionDTO,
)
from the_alchemiser.shared.dto.rebalance_plan_dto import (
    RebalancePlan,
    RebalancePlanDTO,
    RebalancePlanItem,
    RebalancePlanItemDTO,
)
from the_alchemiser.shared.dto.signal_dto import StrategySignal, StrategySignalDTO
from the_alchemiser.shared.dto.strategy_allocation_dto import (
    StrategyAllocation,
    StrategyAllocationDTO,
)
from the_alchemiser.shared.dto.technical_indicators_dto import (
    TechnicalIndicator,
    TechnicalIndicatorDTO,
)
from the_alchemiser.shared.dto.trade_ledger_dto import (
    AssetType,
    Lot,
    PerformanceSummary,
    TradeLedgerEntry,
    TradeLedgerQuery,
    TradeSide,
)
from the_alchemiser.shared.dto.trade_run_result_dto import (
    ExecutionSummary,
    ExecutionSummaryDTO,
    OrderResultSummary,
    OrderResultSummaryDTO,
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


# TODO: Remove in Phase 3 - Temporary backward compatibility aliases
ConfigurationDTO = Configuration
ErrorDTO = Error
