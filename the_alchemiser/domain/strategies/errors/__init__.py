"""Business Unit: strategy & signal generation; Status: current.

Strategy domain exceptions.
"""

from .strategy_errors import (
    StrategyComputationError,
    StrategyValidationError,
)

__all__ = [
    "StrategyComputationError", 
    "StrategyValidationError",
]