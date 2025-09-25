"""Data transfer objects.

Typed DTOs for inter-module communication with correlation tracking
and serialization helpers.

NOTE: This module now provides backward compatibility re-exports.
New code should import directly from shared.schemas submodules.
"""

from __future__ import annotations

from typing import Any

# Placeholder DTO classes for future implementation (to be enhanced in Phase 2)
from pydantic import BaseModel, ConfigDict, Field

# Re-export moved DTOs from new schema locations for backward compatibility
from the_alchemiser.shared.schemas.execution import (
    ExecutedOrderDTO,
    ExecutionReportDTO,
    ExecutionResult,
    ExecutionSummaryDTO,
    MarketDataDTO,
    OrderRequestDTO,
    OrderResultSummaryDTO,
    TradeRunResultDTO,
)
from the_alchemiser.shared.schemas.market import AssetInfoDTO, MarketBarDTO
from the_alchemiser.shared.schemas.portfolio import (
    AssetType,
    ConsolidatedPortfolioDTO,
    Lot,
    PerformanceSummary,
    PortfolioMetricsDTO,
    PortfolioStateDTO,
    PositionDTO,
    RebalancePlanDTO,
    RebalancePlanItemDTO,
    TradeLedgerEntry,
    TradeLedgerQuery,
    TradeSide,
)
from the_alchemiser.shared.schemas.strategy import (
    IndicatorRequestDTO,
    StrategyAllocationDTO,
    StrategySignalDTO,
    TechnicalIndicatorDTO,
)
from the_alchemiser.shared.schemas.system import ASTNodeDTO, LambdaEventDTO, TraceDTO


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
    "AssetInfoDTO",
    # AST DTOs
    "ASTNodeDTO",
    # Trade Ledger DTOs
    "AssetType",
    # Placeholder DTOs
    "ConfigurationDTO",
    "ConsolidatedPortfolioDTO",
    "ErrorDTO",
    # Execution DTOs
    "ExecutedOrderDTO",
    "ExecutionReportDTO",
    "ExecutionResult",
    "ExecutionSummaryDTO",
    # Indicator DTOs
    "IndicatorRequestDTO",
    # Lambda DTOs
    "LambdaEventDTO",
    # Trade Ledger DTOs
    "Lot",
    # Market DTOs
    "MarketBarDTO",
    "MarketDataDTO",
    "OrderRequestDTO",
    "OrderResultSummaryDTO",
    # Trade Ledger DTOs
    "PerformanceSummary",
    "PortfolioMetricsDTO",
    "PortfolioStateDTO",
    "PositionDTO",
    "RebalancePlanDTO",
    "RebalancePlanItemDTO",
    "StrategyAllocationDTO",
    "StrategySignalDTO",
    "TechnicalIndicatorDTO",
    # Trace DTOs
    "TraceDTO",
    # Trade Ledger DTOs
    "TradeLedgerEntry",
    "TradeLedgerQuery",
    "TradeRunResultDTO",
    # Trade Ledger DTOs
    "TradeSide",
]
