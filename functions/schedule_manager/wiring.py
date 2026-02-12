"""Business Unit: coordinator_v2 | Status: current.

Dependency wiring for schedule_manager module.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from the_alchemiser.shared.config.container import ApplicationContainer


def register_schedule_manager(container: ApplicationContainer) -> None:
    """Register schedule manager dependencies.

    Args:
        container: The main ApplicationContainer instance

    """
    # Schedule manager uses MarketCalendarService and boto3 directly
