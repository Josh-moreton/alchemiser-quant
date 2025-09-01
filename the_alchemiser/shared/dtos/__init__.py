"""Business Unit: shared | Status: current.

Data transfer objects for inter-module communication.

This module provides typed objects that enable type-safe communication between
the four main modules (strategy, portfolio, execution, shared) by reusing 
existing domain objects and adding minimal correlation tracking.

Instead of duplicating existing DTOs, this module imports and wraps domain
objects to provide inter-module communication capabilities while maintaining
the existing architecture.
"""

from __future__ import annotations

# Re-export existing domain objects for inter-module communication
from the_alchemiser.domain.portfolio.rebalancing.rebalance_plan import (
    RebalancePlan,
)
from the_alchemiser.domain.strategies.value_objects.strategy_signal import (
    StrategySignal,
)

# Re-export existing interface DTOs for execution
from the_alchemiser.interfaces.schemas.execution import (
    ExecutionResult,
)

__all__ = [
    "ExecutionResult",
    "RebalancePlan",
    "StrategySignal",
]