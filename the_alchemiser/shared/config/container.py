"""Business Unit: utilities; Status: current.

Main application container for dependency injection.
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
    
    # Execution providers (late binding to avoid circular imports)
    execution: providers.Container[Any] | None = None

    # Application layer (will be added in Phase 2)

    def initialize_execution_providers(self) -> None:
        """Initialize execution providers with late binding to avoid circular imports."""
        if self.execution is None:
            # Use importlib to avoid static import detection
            execution_config_module = importlib.import_module("the_alchemiser.execution_v2.config")
            ExecutionProviders = execution_config_module.ExecutionProviders
            
            self.execution = providers.Container(
                ExecutionProviders,
                infrastructure=self.infrastructure,
                config=self.config,
            )

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

        # Initialize execution providers with late binding
        container.initialize_execution_providers()

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
