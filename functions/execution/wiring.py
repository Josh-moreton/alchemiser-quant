"""Business Unit: execution | Status: current.

Dependency wiring for execution_v2 module.

Provides register_execution() function to wire execution module dependencies
into the main ApplicationContainer. Follows single composition root pattern.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from dependency_injector import providers

if TYPE_CHECKING:
    from the_alchemiser.shared.config.container import ApplicationContainer


def register_execution(container: ApplicationContainer) -> None:
    """Register execution module dependencies in the application container.

    This function wires up all execution module components using constructor
    injection. It accesses infrastructure dependencies from the container
    (AlpacaManager, config) and registers execution services.

    Args:
        container: The main ApplicationContainer instance

    Example:
        >>> container = ApplicationContainer()
        >>> register_execution(container)
        >>> exec_mgr = container.execution_manager()

    """
    from core.execution_manager import ExecutionManager
    from core.smart_execution_strategy import ExecutionConfig

    # Register execution manager
    container.execution_manager = providers.Factory(
        ExecutionManager,
        alpaca_manager=container.infrastructure.alpaca_manager,
        execution_config=providers.Factory(ExecutionConfig),
    )
