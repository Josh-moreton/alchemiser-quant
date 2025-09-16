"""Data transfer objects.

Typed DTOs for inter-module communication with correlation tracking
and serialization helpers.
"""

from __future__ import annotations

# Import implemented DTOs
from the_alchemiser.shared.dto.execution_report_dto import (
    ExecutedOrderDTO,
    ExecutionReportDTO,
)
from the_alchemiser.shared.dto.lambda_event_dto import LambdaEventDTO
from the_alchemiser.shared.dto.order_request_dto import (
    MarketDataDTO,
    OrderRequestDTO,
)
from the_alchemiser.shared.dto.portfolio_analysis_dto import (
    AccountInfoDTO,
    ComprehensiveAccountDataDTO,
    OrderDataDTO,
    PortfolioAnalysisDTO,
    PositionDataDTO,
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
from the_alchemiser.shared.dto.signal_analysis_dto import (
    RebalancingPlanResultDTO,
    SignalAnalysisResultDTO,
    StrategySignalResultDTO,
)
from the_alchemiser.shared.dto.signal_dto import StrategySignalDTO
from the_alchemiser.shared.dto.strategy_allocation_dto import StrategyAllocationDTO
from the_alchemiser.shared.dto.trading_workflow_dto import (
    NotificationDataDTO,
    TradingWorkflowResultDTO,
)


# Placeholder DTO classes for future implementation
class ConfigurationDTO:
    """Placeholder for configuration data transfer."""


class ErrorDTO:
    """Placeholder for error data transfer."""


__all__ = [
    # Placeholder DTOs
    "ConfigurationDTO",
    "ErrorDTO",
    # Implemented DTOs
    "AccountInfoDTO",
    "ComprehensiveAccountDataDTO",
    "ExecutedOrderDTO",
    "ExecutionReportDTO",
    "LambdaEventDTO",
    "MarketDataDTO",
    "NotificationDataDTO",
    "OrderDataDTO",
    "OrderRequestDTO",
    "PortfolioAnalysisDTO",
    "PortfolioMetricsDTO",
    "PortfolioStateDTO",
    "PositionDataDTO",
    "PositionDTO",
    "RebalancePlanDTO",
    "RebalancePlanItemDTO",
    "RebalancingPlanResultDTO",
    "SignalAnalysisResultDTO",
    "StrategyAllocationDTO",
    "StrategySignalDTO",
    "StrategySignalResultDTO",
    "TradingWorkflowResultDTO",
]
