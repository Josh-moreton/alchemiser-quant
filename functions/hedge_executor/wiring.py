"""Business Unit: hedge_executor | Status: current.

Dependency wiring for hedge_executor module.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from the_alchemiser.shared.config.container import ApplicationContainer


def register_hedge_executor(container: ApplicationContainer) -> None:
    """Register hedge executor module dependencies.

    Args:
        container: The main ApplicationContainer instance

    """
    # Services are initialized in handler with credentials from env
