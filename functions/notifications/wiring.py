"""Business Unit: notifications | Status: current.

Dependency wiring for notifications module.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from the_alchemiser.shared.config.container import ApplicationContainer


def register_notifications(container: ApplicationContainer) -> None:
    """Register notifications dependencies.

    Args:
        container: The main ApplicationContainer instance.

    """
    # Notifications module uses NotificationService directly
