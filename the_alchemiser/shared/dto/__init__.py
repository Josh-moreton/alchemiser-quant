"""Data transfer objects.

Typed DTOs for inter-module communication with correlation tracking
and serialization helpers.

NOTE: This module now provides backward compatibility re-exports.
New code should import directly from shared.schemas submodules.
The DTOs have been moved using git mv to preserve history and eliminate duplication.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

# Re-export moved DTOs from new schema locations for backward compatibility
from the_alchemiser.shared.schemas.assets import AssetInfo
from the_alchemiser.shared.schemas.broker import WebSocketResult, WebSocketStatus
from the_alchemiser.shared.schemas.dsl import ASTNode, Trace
from the_alchemiser.shared.schemas.events import LambdaEvent
from the_alchemiser.shared.schemas.execution import ExecutionResult
from the_alchemiser.shared.schemas.indicators import TechnicalIndicator
from the_alchemiser.shared.schemas.market_data import MarketBar
from the_alchemiser.shared.schemas.orders import MarketData, OrderRequest
from the_alchemiser.shared.schemas.portfolio import (
    PortfolioMetrics,
    PortfolioState,
    Position,
)
from the_alchemiser.shared.schemas.strategy import StrategyAllocation, StrategySignal
from the_alchemiser.shared.schemas.trading import (
    AssetType,
    Lot,
    PerformanceSummary,
    TradeLedgerEntry,
    TradeLedgerQuery,
    TradeSide,
)

# Import remaining DTOs that haven't been fully consolidated yet
# These will be handled in subsequent consolidation steps
try:
    from the_alchemiser.shared.dto.consolidated_portfolio_dto import ConsolidatedPortfolio
    from the_alchemiser.shared.dto.execution_report_dto import (
        ExecutedOrder,
        ExecutionReport,
    )
    from the_alchemiser.shared.dto.indicator_request_dto import IndicatorRequest
    from the_alchemiser.shared.dto.rebalance_plan_dto import (
        RebalancePlan,
        RebalancePlanItem,
    )
    from the_alchemiser.shared.dto.trade_run_result_dto import (
        ExecutionSummary,
        OrderResultSummary,
        TradeRunResult,
    )
except ImportError:
    # Handle gracefully if files have been moved/consolidated
    pass


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
    context: dict[str, Any] = Field(default_factory=dict, description="Error context data")


__all__ = [
    # Moved DTOs (now re-exported from schema locations)
    "ASTNode",
    "AssetInfo",
    "AssetType",
    # Placeholder DTOs
    "Configuration",
    # DTOs not yet fully consolidated (temporary)
    "ConsolidatedPortfolio",
    "Error",
    "ExecutedOrder",
    "ExecutionReport",
    "ExecutionResult",
    "ExecutionSummary",
    "IndicatorRequest",
    "LambdaEvent",
    "Lot",
    "MarketBar",
    "MarketData",
    "OrderRequest",
    "OrderResultSummary",
    "PerformanceSummary",
    "PortfolioMetrics",
    "PortfolioState",
    "Position",
    "RebalancePlan",
    "RebalancePlanItem",
    "StrategyAllocation",
    "StrategySignal",
    "TechnicalIndicator",
    "Trace",
    "TradeLedgerEntry",
    "TradeLedgerQuery",
    "TradeRunResult",
    "TradeSide",
    "WebSocketResult",
    "WebSocketStatus",
]
