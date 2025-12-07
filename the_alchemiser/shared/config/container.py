"""Business Unit: utilities; Status: current.

Main application container for dependency injection.

This module orchestrates the dependency injection container hierarchy for the
entire application, managing configuration, infrastructure, and service layers.

Example:
    >>> # Create container for specific environment
    >>> container = ApplicationContainer.create_for_environment("production")
    >>>
    >>> # Access services
    >>> event_bus = container.services.event_bus()
    >>> execution_manager = container.execution_manager()

"""

from __future__ import annotations

import importlib
from typing import Any

from dependency_injector import containers, providers

from the_alchemiser.shared.config.config_providers import ConfigProviders
from the_alchemiser.shared.config.infrastructure_providers import (
    InfrastructureProviders,
)
from the_alchemiser.shared.config.service_providers import ServiceProviders
from the_alchemiser.shared.logging import get_logger

logger = get_logger(__name__)

# Test credentials constants
TEST_API_KEY = "test_api_key_valid_for_testing"
TEST_SECRET_KEY = "test_secret_key_valid_for_testing"  # noqa: S105  # nosec B105


class ApplicationContainer(containers.DeclarativeContainer):
    """Main application container orchestrating all dependencies."""

    # Wire configuration
    # Note: Business modules are wired dynamically via register_* functions
    # called in create_for_environment() to avoid circular dependencies
    wiring_config = containers.WiringConfiguration(modules=[])

    # Sub-containers (logical layers)
    config = providers.Container(ConfigProviders)
    infrastructure = providers.Container(InfrastructureProviders, config=config)
    services = providers.Container(ServiceProviders, infrastructure=infrastructure, config=config)

    # Business module providers (registered by wiring functions)
    # Execution module
    execution_manager: Any = None

    # Strategy module
    strategy_registry: Any = None
    strategy_market_data_adapter: Any = None
    strategy_orchestrator: Any = None

    # Portfolio module
    portfolio_data_adapter: Any = None
    portfolio_state_reader: Any = None
    portfolio_planner: Any = None
    portfolio_service: Any = None

    @classmethod
    def create_for_environment(cls, env: str = "development") -> ApplicationContainer:
        """Create container configured for specific environment.

        Supports environment-specific configuration overrides. Valid environments:
        - "development": Default configuration from environment variables
        - "test": Test credentials and paper trading mode
        - "production": Production configuration from environment variables

        Args:
            env: Environment name (development, test, or production)

        Returns:
            Configured ApplicationContainer instance

        Example:
            >>> container = ApplicationContainer.create_for_environment("test")
            >>> container = ApplicationContainer.create_for_environment("production")

        """
        logger.info("Creating ApplicationContainer", extra={"environment": env})
        container = cls()

        # Load environment-specific configuration
        if env == "test":
            logger.debug("Applying test environment configuration")
            container.config.alpaca_api_key.override(TEST_API_KEY)
            container.config.alpaca_secret_key.override(TEST_SECRET_KEY)
            container.config.paper_trading.override(True)  # noqa: FBT003
        elif env == "production":
            # Production uses environment variables (default behavior)
            logger.debug("Using production environment configuration from environment variables")
        elif env == "development":
            # Development also uses environment variables (default behavior)
            logger.debug("Using development environment configuration from environment variables")
        else:
            # Log warning for unknown environment but continue with defaults
            logger.warning(
                "Unknown environment specified, using default configuration",
                extra={
                    "environment": env,
                    "valid_environments": ["development", "test", "production"],
                },
            )

        # Register business module dependencies using wiring functions (dynamic import)
        # Import dynamically to avoid circular dependencies and maintain architecture boundaries
        exec_wiring = importlib.import_module("the_alchemiser.execution_v2.wiring")
        strategy_wiring = importlib.import_module("the_alchemiser.strategy_v2.wiring")
        portfolio_wiring = importlib.import_module("the_alchemiser.portfolio_v2.wiring")

        exec_wiring.register_execution(container)
        strategy_wiring.register_strategy(container)
        portfolio_wiring.register_portfolio(container)

        logger.info("ApplicationContainer created successfully", extra={"environment": env})
        return container

    @classmethod
    def create_for_testing(cls) -> ApplicationContainer:
        """Create container with test doubles for testing.

        This method creates a container with mock implementations suitable for
        testing. It should only be used in test code.

        Returns:
            ApplicationContainer configured with test mocks

        Note:
            This method is provided for backward compatibility with existing tests.
            Consider using proper test fixtures or dependency injection patterns
            instead of importing unittest.mock in production code paths.

        Example:
            >>> # In test code
            >>> container = ApplicationContainer.create_for_testing()
            >>> assert container.infrastructure.alpaca_manager().is_paper_trading

        """
        logger.info("Creating ApplicationContainer for testing with mock doubles")
        container = cls.create_for_environment("test")

        # Override with mocks for testing
        # NOTE: This imports unittest.mock in production code which is not ideal.
        # Consider moving this to a test utilities module if this becomes problematic.
        from unittest.mock import Mock

        # Create a mock AlpacaManager that behaves like the real one
        mock_alpaca_manager = Mock()
        mock_alpaca_manager.is_paper_trading = True
        mock_alpaca_manager.get_account.return_value = {
            "account_id": "test_account",
            "equity": 100000.0,
            "cash": 10000.0,
            "buying_power": 50000.0,
            "portfolio_value": 100000.0,
        }
        mock_alpaca_manager.get_all_positions.return_value = {}

        # Override the entire infrastructure layer with mocks
        container.infrastructure.alpaca_manager.override(mock_alpaca_manager)

        logger.info("ApplicationContainer for testing created successfully")
        return container
