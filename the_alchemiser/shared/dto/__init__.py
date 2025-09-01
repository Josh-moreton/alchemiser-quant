"""Business Unit: shared | Status: current.

Data transfer objects for inter-module communication.

This module provides typed DTOs that enable type-safe communication between
the four main modules (strategy, portfolio, execution, shared) while maintaining
clear boundaries and preventing direct coupling.
"""

from __future__ import annotations

from the_alchemiser.shared.dto.execution_report_dto import ExecutionReportDTO
from the_alchemiser.shared.dto.rebalance_plan_dto import RebalancePlanDTO
from the_alchemiser.shared.dto.signal_dto import StrategySignalDTO


# Legacy placeholder DTO classes (to be implemented in future phases)
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
    "ConfigurationDTO",
    "ErrorDTO",
    "ExecutionReportDTO",
    "MarketDataDTO",
    "OrderDTO",
    "PortfolioStateDTO",
    "PositionDTO",
    "RebalancePlanDTO",
    "StrategySignalDTO",
]