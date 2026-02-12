"""Business Unit: coordinator | Status: current.

Dependency wiring for strategy_orchestrator module.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from the_alchemiser.shared.config.container import ApplicationContainer


def register_strategy_orchestrator(container: ApplicationContainer) -> None:
    """Register strategy orchestrator dependencies.

    Args:
        container: The main ApplicationContainer instance

    """
    # Orchestrator uses CoordinatorSettings and StrategyInvoker directly
