"""Data transfer objects.

Typed DTOs for inter-module communication with correlation tracking
and serialization helpers.
"""

from __future__ import annotations

from typing import Any

# Placeholder DTO classes for future implementation (to be enhanced in Phase 2)
from pydantic import BaseModel, ConfigDict, Field

from the_alchemiser.shared.dto.execution_report_dto import (
    ExecutedOrderDTO,
    ExecutionReportDTO,
)
from the_alchemiser.shared.dto.lambda_event_dto import LambdaEventDTO
from the_alchemiser.shared.dto.order_request_dto import (
    MarketDataDTO,
    OrderRequestDTO,
)
from the_alchemiser.shared.dto.portfolio_state_dto import (
    PortfolioMetrics,
    PortfolioSnapshot,
    Position,
)
from the_alchemiser.shared.dto.rebalance_plan_dto import (
    RebalancePlan,
    RebalancePlanItem,
)
from the_alchemiser.shared.dto.technical_indicators_dto import TechnicalIndicatorDTO
from the_alchemiser.shared.dto.trade_ledger_dto import (
    AssetType,
    Lot,
    PerformanceSummary,
    TradeLedgerEntry,
    TradeLedgerQuery,
    TradeSide,
)
from the_alchemiser.shared.dto.trade_run_result_dto import (
    ExecutionSummaryDTO,
    OrderResultSummaryDTO,
    TradeRunResultDTO,
)

# Import implemented DTOs
from the_alchemiser.shared.schemas.assets import AssetInfo
from the_alchemiser.shared.schemas.market_data import MarketBar
from the_alchemiser.shared.schemas.signals import StrategySignal
from the_alchemiser.shared.schemas.strategy import StrategyAllocation


class ConfigurationDTO(BaseModel):
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


class ErrorDTO(BaseModel):
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
    context: dict[str, Any] = Field(default_factory=dict, description="Error context data")


__all__ = [
    # Asset DTOs
    "AssetInfo",
    # Trade Ledger DTOs
    "AssetType",
    # Placeholder DTOs
    "ConfigurationDTO",
    "ErrorDTO",
    # Implemented DTOs
    "ExecutedOrderDTO",
    "ExecutionReportDTO",
    "ExecutionSummaryDTO",
    "LambdaEventDTO",
    # Trade Ledger DTOs
    "Lot",
    "MarketBar",
    "MarketDataDTO",
    "OrderRequestDTO",
    "OrderResultSummaryDTO",
    # Trade Ledger DTOs
    "PerformanceSummary",
    "PortfolioMetrics",
    "PortfolioSnapshot",
    "Position",
    "RebalancePlan",
    "RebalancePlanItem",
    "StrategyAllocation",
    "StrategySignal",
    "TechnicalIndicatorDTO",
    # Trade Ledger DTOs
    "TradeLedgerEntry",
    "TradeLedgerQuery",
    "TradeRunResultDTO",
    # Trade Ledger DTOs
    "TradeSide",
]
