"""Business Unit: hedge_roll_manager | Status: current.

Dependency wiring for hedge_roll_manager module.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from the_alchemiser.shared.config.container import ApplicationContainer


def register_hedge_roll_manager(container: ApplicationContainer) -> None:
    """Register hedge roll manager dependencies.

    Args:
        container: The main ApplicationContainer instance

    """
    # Roll manager uses handler directly - no additional services needed
