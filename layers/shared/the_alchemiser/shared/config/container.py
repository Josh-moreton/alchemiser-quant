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

    # Strategy rebalancer (per-strategy books)
    strategy_rebalancer: Any = None

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
        # Only import modules that are needed to avoid pulling in unnecessary dependencies
        # (e.g., Strategy Lambda doesn't need alpaca-py from Execution module)
        exec_wiring = importlib.import_module("the_alchemiser.execution_v2.wiring")
        strategy_wiring = importlib.import_module("the_alchemiser.strategy_v2.wiring")

        exec_wiring.register_execution(container)
        strategy_wiring.register_strategy(container)

        logger.info("ApplicationContainer created successfully", extra={"environment": env})
        return container

    @classmethod
    def create_for_strategy(cls, env: str = "production") -> ApplicationContainer:
        """Create container configured for Strategy Lambda only.

        This creates a minimal container that ONLY registers strategy module
        dependencies. This avoids importing execution/portfolio modules which
        would pull in alpaca-py (not needed by Strategy Lambda).

        Args:
            env: Environment name (development, test, or production)

        Returns:
            Configured ApplicationContainer with only strategy dependencies

        """
        logger.info("Creating ApplicationContainer for Strategy Lambda", extra={"environment": env})
        container = cls()

        # Load environment-specific configuration
        if env == "test":
            container.config.alpaca_api_key.override(TEST_API_KEY)
            container.config.alpaca_secret_key.override(TEST_SECRET_KEY)
            container.config.paper_trading.override(True)  # noqa: FBT003

        # Only register strategy module (avoids alpaca-py imports from execution)
        strategy_wiring = importlib.import_module("the_alchemiser.strategy_v2.wiring")
        strategy_wiring.register_strategy(container)

        logger.info(
            "ApplicationContainer for Strategy created successfully", extra={"environment": env}
        )
        return container

    @classmethod
    def create_for_notifications(cls, env: str = "production") -> ApplicationContainer:
        """Create container configured for Notifications Lambda only.

        This creates a minimal container with NO business module dependencies.
        Notifications only needs config access (paper_trading flag) and doesn't
        need strategy/portfolio/execution modules which pull in pandas/alpaca-py.

        Args:
            env: Environment name (development, test, or production)

        Returns:
            Configured ApplicationContainer with minimal dependencies

        """
        logger.info(
            "Creating ApplicationContainer for Notifications Lambda", extra={"environment": env}
        )
        container = cls()

        # Load environment-specific configuration
        if env == "test":
            container.config.alpaca_api_key.override(TEST_API_KEY)
            container.config.alpaca_secret_key.override(TEST_SECRET_KEY)
            container.config.paper_trading.override(True)  # noqa: FBT003

        # No business module wiring needed - notifications only uses config/events/logging
        logger.info(
            "ApplicationContainer for Notifications created successfully",
            extra={"environment": env},
        )
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
