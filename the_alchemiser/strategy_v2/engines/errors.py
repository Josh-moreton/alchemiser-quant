"""Business Unit: strategy | Status: current

Strategy errors for strategy_v2.

Exception types for strategy execution failures.
"""


class StrategyExecutionError(Exception):
    """Exception raised when strategy execution fails."""
    
    def __init__(self, message: str, strategy_type: str | None = None) -> None:
        self.strategy_type = strategy_type
        super().__init__(message)


class StrategyValidationError(StrategyExecutionError):
    """Exception raised when strategy validation fails."""
    pass