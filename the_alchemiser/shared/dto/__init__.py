"""Data transfer objects.

Typed DTOs for inter-module communication with correlation tracking
and serialization helpers.
"""

from __future__ import annotations

from typing import Any

# Placeholder DTO classes for future implementation (to be enhanced in Phase 2)
from pydantic import BaseModel, ConfigDict, Field

# Import implemented DTOs
from the_alchemiser.shared.dto.execution_report_dto import (
    ExecutedOrderDTO,
    ExecutionReportDTO,
)
from the_alchemiser.shared.dto.lambda_event_dto import LambdaEventDTO
from the_alchemiser.shared.dto.market_bar_dto import MarketBarDTO
from the_alchemiser.shared.dto.order_request_dto import (
    MarketDataDTO,
    OrderRequestDTO,
)
from the_alchemiser.shared.dto.portfolio_state_dto import (
    PortfolioMetricsDTO,
    PortfolioStateDTO,
    PositionDTO,
)
from the_alchemiser.shared.dto.rebalance_plan_dto import (
    RebalancePlanDTO,
    RebalancePlanItemDTO,
)
from the_alchemiser.shared.dto.signal_dto import StrategySignalDTO
from the_alchemiser.shared.dto.strategy_allocation_dto import StrategyAllocationDTO
from the_alchemiser.shared.dto.technical_indicators_dto import TechnicalIndicatorDTO
from the_alchemiser.shared.dto.trade_run_result_dto import (
    ExecutionSummaryDTO,
    OrderResultSummaryDTO,
    TradeRunResultDTO,
)


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
        description="Configuration data (flexible for Phase 1 scaffolding)"
    )


class ErrorDTO(BaseModel):
    """Error data transfer object for structured error handling.
    
    Standardizes error representation across the system, replacing
    error_message: str | None patterns and TypedDict structures.
    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    # Core error fields
    error_type: str = Field(description="Type/class name of the error")
    message: str = Field(description="Human-readable error message")
    
    # Optional detailed fields
    category: str | None = Field(default=None, description="Error category for grouping")
    component: str | None = Field(default=None, description="Component where error occurred")
    context: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional context data"
    )
    timestamp: str | None = Field(default=None, description="ISO timestamp when error occurred")
    traceback: str | None = Field(default=None, description="Stack trace if available")
    suggested_action: str | None = Field(default=None, description="Suggested remediation")
    
    @classmethod
    def from_exception(
        cls, 
        error: Exception, 
        category: str | None = None,
        component: str | None = None,
        additional_context: dict[str, Any] | None = None
    ) -> ErrorDTO:
        """Create ErrorDTO from an exception instance.
        
        Args:
            error: The exception to convert
            category: Optional error category
            component: Optional component name
            additional_context: Optional additional context
            
        Returns:
            ErrorDTO instance

        """
        from datetime import UTC, datetime
        
        context = additional_context or {}
        
        # Try to get context from exception if it has one
        if hasattr(error, "context") and isinstance(error.context, dict):
            context.update(error.context)
            
        # Try to get timestamp from exception if available
        timestamp = None
        if hasattr(error, "timestamp"):
            timestamp = error.timestamp.isoformat() if hasattr(error.timestamp, "isoformat") else str(error.timestamp)
        else:
            timestamp = datetime.now(UTC).isoformat()
            
        return cls(
            error_type=error.__class__.__name__,
            message=str(error),
            category=category,
            component=component,
            context=context,
            timestamp=timestamp,
            suggested_action=getattr(error, "suggested_action", None)
        )


__all__ = [
    # Placeholder DTOs
    "ConfigurationDTO",
    "ErrorDTO",
    # Implemented DTOs
    "ExecutedOrderDTO",
    "ExecutionReportDTO",
    # Trade execution result DTOs
    "ExecutionSummaryDTO",
    "LambdaEventDTO",
    "MarketBarDTO",
    "MarketDataDTO",
    "OrderRequestDTO",
    "OrderResultSummaryDTO",
    "PortfolioMetricsDTO",
    "PortfolioStateDTO",
    "PositionDTO",
    "RebalancePlanDTO",
    "RebalancePlanItemDTO",
    "StrategyAllocationDTO",
    "StrategySignalDTO",
    "TechnicalIndicatorDTO",
    "TradeRunResultDTO",
]
