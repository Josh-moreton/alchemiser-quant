"""Business Unit: strategy & signal generation; Status: current.

Domain exceptions for strategy execution and validation.
"""

from __future__ import annotations


class StrategyValidationError(ValueError):
    """Raised when strategy inputs or outputs fail validation."""

    def __init__(self, message: str, strategy_name: str | None = None) -> None:
        """Initialize validation error.

        Args:
            message: Error description
            strategy_name: Name of strategy that failed validation

        """
        super().__init__(message)
        self.strategy_name = strategy_name


class StrategyComputationError(RuntimeError):
    """Raised when strategy computation fails due to data or calculation issues."""

    def __init__(self, message: str, strategy_name: str | None = None) -> None:
        """Initialize computation error.

        Args:
            message: Error description  
            strategy_name: Name of strategy that failed computation

        """
        super().__init__(message)
        self.strategy_name = strategy_name