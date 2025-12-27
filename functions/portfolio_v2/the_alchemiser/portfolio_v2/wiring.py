"""Business Unit: portfolio | Status: current.

Dependency wiring for portfolio_v2 module.

Provides register_portfolio() function to wire portfolio module dependencies
into the main ApplicationContainer. Follows single composition root pattern.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from dependency_injector import providers

if TYPE_CHECKING:
    from the_alchemiser.shared.config.container import ApplicationContainer


def register_portfolio(container: ApplicationContainer) -> None:
    """Register portfolio module dependencies in the application container.

    This function wires up all portfolio module components using constructor
    injection. It accesses infrastructure dependencies from the container
    (AlpacaManager) and registers portfolio services.

    Args:
        container: The main ApplicationContainer instance

    Example:
        >>> container = ApplicationContainer()
        >>> register_portfolio(container)
        >>> portfolio_service = container.portfolio_service()
        >>> planner = container.portfolio_planner()

    """
    from the_alchemiser.portfolio_v2.adapters.alpaca_data_adapter import (
        AlpacaDataAdapter,
    )
    from the_alchemiser.portfolio_v2.core.planner import RebalancePlanCalculator
    from the_alchemiser.portfolio_v2.core.portfolio_service import PortfolioServiceV2
    from the_alchemiser.portfolio_v2.core.state_reader import PortfolioStateReader

    # Register data adapter (uses AlpacaManager from infrastructure)
    container.portfolio_data_adapter = providers.Factory(
        AlpacaDataAdapter,
        alpaca_manager=container.infrastructure.alpaca_manager,
    )

    # Register state reader (uses data adapter)
    container.portfolio_state_reader = providers.Factory(
        PortfolioStateReader,
        data_adapter=container.portfolio_data_adapter,
    )

    # Register planner (stateless calculator)
    container.portfolio_planner = providers.Factory(RebalancePlanCalculator)

    # Register portfolio service (main facade)
    container.portfolio_service = providers.Factory(
        PortfolioServiceV2,
        alpaca_manager=container.infrastructure.alpaca_manager,
    )
