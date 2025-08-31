"""Business Unit: portfolio assessment & management | Status: current

Portfolio context domain exceptions.
"""

from the_alchemiser.shared_kernel.exceptions.base_exceptions import AlchemiserError, DataAccessError


class PortfolioExecutionError(AlchemiserError):
    """Base exception for portfolio execution failures."""


class RebalancingError(PortfolioExecutionError):
    """Exception raised when portfolio rebalancing fails."""


class PositionCalculationError(PortfolioExecutionError):
    """Exception raised when position calculation fails."""


class ConcurrencyError(DataAccessError):
    """Exception raised when optimistic locking violations occur."""


class ProcessingError(AlchemiserError):
    """Exception raised when execution report processing fails."""


class PublishError(AlchemiserError):
    """Exception raised when plan publishing fails."""
