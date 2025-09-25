"""Business Unit: execution | Status: current.

New execution module built around DTO consumption principle.

This module provides a clean, minimal execution system that:
- Consumes RebalancePlan without recalculation
- Delegates order placement to shared AlpacaManager
- Focuses solely on order execution
- Maintains clean module boundaries
"""

from the_alchemiser.execution_v2.core.execution_manager import ExecutionManager
from the_alchemiser.execution_v2.models.execution_result import ExecutionResult

__all__ = [
    "ExecutionManager",
    "ExecutionResult",
]
