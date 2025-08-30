"""Business Unit: portfolio assessment & management | Status: current.

Bootstrap helper for Portfolio context Lambda handlers.

Provides dependency injection and initialization for Portfolio context use cases
while keeping AWS Lambda specifics isolated from application logic.
"""

from __future__ import annotations

import logging

from the_alchemiser.anti_corruption.serialization.signal_serializer import SignalSerializer
from the_alchemiser.infrastructure.config import Settings, load_settings
from the_alchemiser.portfolio.application.use_cases.generate_plan import GeneratePlanUseCase
from the_alchemiser.portfolio.application.use_cases.update_portfolio import UpdatePortfolioUseCase
from the_alchemiser.portfolio.infrastructure.adapters.event_bus_plan_publisher_adapter import (
    EventBusPlanPublisherAdapter,
)
from the_alchemiser.shared_kernel.exceptions.base_exceptions import ConfigurationError

logger = logging.getLogger(__name__)


class PortfolioBootstrapContext:
    """Dependency bundle for Portfolio Lambda handlers."""
    
    def __init__(
        self,
        generate_plan_use_case: GeneratePlanUseCase,
        update_portfolio_use_case: UpdatePortfolioUseCase,
        signal_serializer: SignalSerializer,
        config: Settings,
    ) -> None:
        self.generate_plan_use_case = generate_plan_use_case
        self.update_portfolio_use_case = update_portfolio_use_case
        self.signal_serializer = signal_serializer
        self.config = config


def bootstrap_portfolio_context() -> PortfolioBootstrapContext:
    """Bootstrap Portfolio context dependencies for Lambda execution.
    
    Constructs all required ports, adapters, and use cases while pulling
    configuration from environment variables.
    
    Returns:
        PortfolioBootstrapContext with initialized dependencies
        
    Raises:
        ConfigurationError: If required configuration is missing or invalid
    """
    logger.info("Bootstrapping Portfolio context for Lambda execution")
    
    try:
        # Load configuration from environment
        config = load_settings()
        
        # Create plan publisher (using EventBus)
        plan_publisher = EventBusPlanPublisherAdapter()
        
        # Create use cases
        generate_plan_use_case = GeneratePlanUseCase(plan_publisher=plan_publisher)
        update_portfolio_use_case = UpdatePortfolioUseCase()
        
        # Create serializer for contract handling
        signal_serializer = SignalSerializer()
        
        logger.info("Portfolio context bootstrap completed successfully")
        
        return PortfolioBootstrapContext(
            generate_plan_use_case=generate_plan_use_case,
            update_portfolio_use_case=update_portfolio_use_case,
            signal_serializer=signal_serializer,
            config=config,
        )
        
    except Exception as e:
        logger.error(f"Failed to bootstrap Portfolio context: {e}", exc_info=True)
        raise ConfigurationError(f"Portfolio context bootstrap failed: {e}") from e