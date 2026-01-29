"""Business Unit: hedge_evaluator | Status: current.

Dependency wiring for hedge_evaluator module.

Provides register_hedge_evaluator() function to wire hedge evaluator
dependencies into the main ApplicationContainer.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from dependency_injector import providers

if TYPE_CHECKING:
    from the_alchemiser.shared.config.container import ApplicationContainer


def register_hedge_evaluator(container: ApplicationContainer) -> None:
    """Register hedge evaluator module dependencies in the application container.

    Args:
        container: The main ApplicationContainer instance

    """
    from core.exposure_calculator import ExposureCalculator
    from core.hedge_sizer import HedgeSizer
    from core.sector_mapper import SectorMapper

    # Register core services
    container.hedge_sector_mapper = providers.Factory(SectorMapper)
    container.hedge_exposure_calculator = providers.Factory(ExposureCalculator)
    container.hedge_sizer = providers.Factory(HedgeSizer)
