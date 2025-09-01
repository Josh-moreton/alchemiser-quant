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
from the_alchemiser.shared.dto.rebalance_plan_dto import (
    RebalancePlanDTO,
    RebalancePlanItemDTO,
)
from the_alchemiser.shared.dto.signal_dto import StrategySignalDTO


# Placeholder DTO classes for future implementation
class PortfolioStateDTO:
    """Placeholder for portfolio state data transfer."""



class PositionDTO:
    """Placeholder for position data transfer."""



class OrderDTO:
    """Placeholder for order data transfer."""



class MarketDataDTO:
    """Placeholder for market data transfer."""



class ConfigurationDTO:
    """Placeholder for configuration data transfer."""



class ErrorDTO:
    """Placeholder for error data transfer."""



__all__ = [
    # Placeholder DTOs
    "ConfigurationDTO",
    "ErrorDTO",
    # Implemented DTOs
    "ExecutedOrderDTO",
    "ExecutionReportDTO",
    "MarketDataDTO",
    "OrderDTO",
    "PortfolioStateDTO",
    "PositionDTO",
    "RebalancePlanDTO",
    "RebalancePlanItemDTO",
    "StrategySignalDTO",
]