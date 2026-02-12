"""Business Unit: strategy_performance | Status: current.

Dependency wiring for strategy_performance module.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from the_alchemiser.shared.config.container import ApplicationContainer


def register_strategy_performance(container: ApplicationContainer) -> None:
    """Register strategy performance dependencies.

    Args:
        container: The main ApplicationContainer instance

    """
    # Strategy performance uses DynamoDBMetricsPublisher directly - no additional services needed
