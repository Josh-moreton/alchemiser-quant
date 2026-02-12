"""Business Unit: data | Status: current.

Dependency wiring for data module.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from the_alchemiser.shared.config.container import ApplicationContainer


def register_data(container: ApplicationContainer) -> None:
    """Register data module dependencies.

    Args:
        container: The main ApplicationContainer instance

    """
    # Data module uses DataRefreshService and FetchRequestService directly
