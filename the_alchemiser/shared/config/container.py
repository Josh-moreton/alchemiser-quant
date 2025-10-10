"""Business Unit: utilities; Status: current.

Main application container for dependency injection.
"""

from __future__ import annotations

from dependency_injector import containers, providers

from the_alchemiser.shared.config.config_providers import ConfigProviders
from the_alchemiser.shared.config.infrastructure_providers import (
    InfrastructureProviders,
)
from the_alchemiser.shared.config.service_providers import ServiceProviders

# Avoid importing execution types at module level to prevent circular imports


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
    execution: object | None = None

    # Application layer (will be added in Phase 2)

    @staticmethod
    def initialize_execution_providers(container: ApplicationContainer) -> None:
        """Attach execution providers using late binding."""
        if getattr(container, "execution", None) is not None:
            return

        import importlib

        execution_config_module = importlib.import_module("the_alchemiser.execution_v2.config")
        execution_providers = execution_config_module.ExecutionProviders

        execution_container = execution_providers()
        execution_container.infrastructure.alpaca_manager.override(
            container.infrastructure.alpaca_manager
        )
        execution_container.config.execution.override(container.config.execution)
        container.execution = execution_container

    @classmethod
    def create_for_environment(cls, env: str = "development") -> ApplicationContainer:
        """Create container configured for specific environment."""
        container = cls()

        # Load environment-specific configuration
        if env == "test":
            container.config.alpaca_api_key.override("test_api_key_valid_for_testing")
            container.config.alpaca_secret_key.override("test_secret_key_valid_for_testing")
            container.config.paper_trading.override(True)  # noqa: FBT003
        elif env == "production":
            # Production uses environment variables (default behavior)
            pass

        # Execution providers will be initialized when needed
        return container

    @classmethod
    def create_for_testing(cls) -> ApplicationContainer:
        """Create container with test doubles."""
        container = cls.create_for_environment("test")

        # Override with mocks for testing
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

        return container
