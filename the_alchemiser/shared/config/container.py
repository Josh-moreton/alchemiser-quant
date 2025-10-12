"""Business Unit: utilities; Status: current.

Main application container for dependency injection.

This module orchestrates the dependency injection container hierarchy for the
entire application, managing configuration, infrastructure, and service layers.

Example:
    >>> # Create container for specific environment
    >>> container = ApplicationContainer.create_for_environment("production")
    >>>
    >>> # Initialize execution providers with late binding
    >>> ApplicationContainer.initialize_execution_providers(container)
    >>>
    >>> # Access services
    >>> event_bus = container.services.event_bus()

"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

from dependency_injector import containers, providers

from the_alchemiser.shared.config.config_providers import ConfigProviders
from the_alchemiser.shared.config.infrastructure_providers import (
    InfrastructureProviders,
)
from the_alchemiser.shared.config.service_providers import ServiceProviders
from the_alchemiser.shared.errors import ConfigurationError
from the_alchemiser.shared.logging import get_logger

if TYPE_CHECKING:
    from the_alchemiser.execution_v2.config import ExecutionProviders

logger = get_logger(__name__)

# Test credentials constants
TEST_API_KEY = "test_api_key_valid_for_testing"
TEST_SECRET_KEY = "test_secret_key_valid_for_testing"  # noqa: S105

# Avoid importing execution_v2 at module level to prevent circular imports
# (execution_v2 -> shared.utils -> shared.config.container -> execution_v2)


class ApplicationContainer(containers.DeclarativeContainer):
    """Main application container orchestrating all dependencies."""

    # Wire configuration
    wiring_config = containers.WiringConfiguration(
        modules=[
            "the_alchemiser.main",
            "the_alchemiser.lambda_handler",
        ]
    )

    # Sub-containers
    config = providers.Container(ConfigProviders)
    infrastructure = providers.Container(InfrastructureProviders, config=config)
    services = providers.Container(ServiceProviders, infrastructure=infrastructure, config=config)

    # Execution providers (initialized lazily to avoid circular imports)
    # Type hint uses TYPE_CHECKING import to avoid runtime circular dependency
    execution: ExecutionProviders | None = None

    @staticmethod
    def initialize_execution_providers(container: ApplicationContainer) -> None:
        """Attach execution providers using late binding.

        This method uses dynamic import to avoid circular dependencies between
        shared.config and execution_v2 modules. It is idempotent and safe to
        call multiple times.

        Args:
            container: The ApplicationContainer instance to initialize

        Raises:
            ConfigurationError: If execution_v2 module cannot be imported

        Example:
            >>> container = ApplicationContainer()
            >>> ApplicationContainer.initialize_execution_providers(container)

        """
        # Idempotency guard - skip if already initialized
        if getattr(container, "execution", None) is not None:
            logger.debug("Execution providers already initialized, skipping")
            return

        try:
            logger.info("Initializing execution providers with late binding")
            execution_config_module = importlib.import_module("the_alchemiser.execution_v2.config")
            execution_providers = execution_config_module.ExecutionProviders

            execution_container = execution_providers()
            execution_container.infrastructure.alpaca_manager.override(
                container.infrastructure.alpaca_manager
            )
            execution_container.config.execution.override(container.config.execution)
            container.execution = execution_container

            logger.info("Successfully initialized execution providers")
        except (ImportError, ModuleNotFoundError) as e:
            logger.error(
                "Failed to import execution_v2 module",
                extra={
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "module": "the_alchemiser.execution_v2.config",
                },
            )
            raise ConfigurationError(
                f"Failed to load execution_v2 module for late binding: {e}"
            ) from e
        except Exception as e:
            logger.error(
                "Unexpected error initializing execution providers",
                extra={
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
            )
            raise ConfigurationError(
                f"Unexpected error during execution providers initialization: {e}"
            ) from e

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

        logger.info("ApplicationContainer created successfully", extra={"environment": env})
        # Execution providers will be initialized when needed
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
