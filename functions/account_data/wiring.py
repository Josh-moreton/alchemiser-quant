"""Business Unit: account_data | Status: current.

Dependency wiring for account_data module.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from the_alchemiser.shared.config.container import ApplicationContainer


def register_account_data(container: ApplicationContainer) -> None:
    """Register account data dependencies.

    Args:
        container: The main ApplicationContainer instance

    """
    # Account data uses Alpaca clients and DynamoDB directly
