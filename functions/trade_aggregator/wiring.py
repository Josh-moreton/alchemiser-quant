"""Business Unit: trade_aggregator | Status: current.

Dependency wiring for trade_aggregator module.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from the_alchemiser.shared.config.container import ApplicationContainer


def register_trade_aggregator(container: ApplicationContainer) -> None:
    """Register trade_aggregator dependencies.

    Args:
        container: The main ApplicationContainer instance.

    """
    # Trade aggregator uses TradeAggregatorService directly
