"""Business Unit: shared | Status: current.

Unit tests for InfrastructureProviders DI container.

This test suite validates the infrastructure layer dependency injection
configuration, ensuring proper wiring of external dependencies and services.
"""

import pytest

from the_alchemiser.shared.config.infrastructure_providers import (
    InfrastructureProviders,
)


@pytest.mark.unit
class TestInfrastructureProviders:
    """Test InfrastructureProviders DI container configuration."""

    def test_container_has_required_providers(self) -> None:
        """Test that container exposes all required providers."""
        container = InfrastructureProviders()

        # Verify all providers exist
        assert hasattr(container, "config")
        assert hasattr(container, "alpaca_manager")
        assert hasattr(container, "market_data_service")
        assert hasattr(container, "trading_repository")
        assert hasattr(container, "market_data_repository")
        assert hasattr(container, "account_repository")

    def test_alpaca_manager_is_singleton(self) -> None:
        """Test that alpaca_manager provider is configured as singleton."""
        container = InfrastructureProviders()

        # Mock the config dependencies
        container.config.alpaca_api_key.override("test_key")
        container.config.alpaca_secret_key.override("test_secret")
        container.config.paper_trading.override(True)  # noqa: FBT003

        # Get two instances
        instance1 = container.alpaca_manager()
        instance2 = container.alpaca_manager()

        # Verify they are the same instance (singleton)
        assert instance1 is instance2

    def test_market_data_service_is_singleton(self) -> None:
        """Test that market_data_service provider is configured as singleton."""
        container = InfrastructureProviders()

        # Mock the config dependencies
        container.config.alpaca_api_key.override("test_key")
        container.config.alpaca_secret_key.override("test_secret")
        container.config.paper_trading.override(True)  # noqa: FBT003

        # Get two instances
        instance1 = container.market_data_service()
        instance2 = container.market_data_service()

        # Verify they are the same instance (singleton)
        assert instance1 is instance2

    def test_alpaca_manager_receives_config_values(self) -> None:
        """Test that AlpacaManager receives configuration from config container."""
        container = InfrastructureProviders()

        # Override config with test values
        test_api_key = "test_api_key_12345"
        test_secret_key = "test_secret_key_67890"
        test_paper_mode = True

        container.config.alpaca_api_key.override(test_api_key)
        container.config.alpaca_secret_key.override(test_secret_key)
        container.config.paper_trading.override(test_paper_mode)

        # Get the alpaca_manager instance
        alpaca_manager = container.alpaca_manager()

        # Verify it received the correct configuration
        assert alpaca_manager._api_key == test_api_key
        assert alpaca_manager._secret_key == test_secret_key
        assert alpaca_manager._paper == test_paper_mode

    def test_market_data_service_receives_alpaca_manager(self) -> None:
        """Test that MarketDataService receives alpaca_manager as dependency."""
        container = InfrastructureProviders()

        # Mock the config dependencies
        container.config.alpaca_api_key.override("test_key")
        container.config.alpaca_secret_key.override("test_secret")
        container.config.paper_trading.override(True)  # noqa: FBT003

        # Get instances
        alpaca_manager = container.alpaca_manager()
        market_data_service = container.market_data_service()

        # Verify MarketDataService has the alpaca_manager (stored as _repo)
        assert market_data_service._repo is alpaca_manager

    def test_backward_compatibility_aliases_point_to_alpaca_manager(self) -> None:
        """Test that backward compatibility aliases reference alpaca_manager."""
        container = InfrastructureProviders()

        # The aliases should be the same provider as alpaca_manager
        # Note: These are provider declarations, not instances
        assert container.trading_repository is container.alpaca_manager
        assert container.market_data_repository is container.alpaca_manager
        assert container.account_repository is container.alpaca_manager

    def test_backward_compatibility_aliases_return_same_instance(self) -> None:
        """Test that aliases return the same singleton instance as alpaca_manager."""
        container = InfrastructureProviders()

        # Mock the config dependencies
        container.config.alpaca_api_key.override("test_key")
        container.config.alpaca_secret_key.override("test_secret")
        container.config.paper_trading.override(True)  # noqa: FBT003

        # Get instances via different names
        alpaca_manager = container.alpaca_manager()
        trading_repo = container.trading_repository()
        market_data_repo = container.market_data_repository()
        account_repo = container.account_repository()

        # Verify all aliases return the same instance
        assert trading_repo is alpaca_manager
        assert market_data_repo is alpaca_manager
        assert account_repo is alpaca_manager

    def test_container_can_be_instantiated_without_errors(self) -> None:
        """Test that container can be instantiated without configuration."""
        try:
            container = InfrastructureProviders()
            assert container is not None
        except Exception as e:
            pytest.fail(f"Container instantiation failed: {e}")

    def test_container_exposes_dependencies_container(self) -> None:
        """Test that config is a DependenciesContainer."""
        container = InfrastructureProviders()

        # Verify config is accessible
        assert hasattr(container, "config")
        assert container.config is not None

    def test_alpaca_manager_with_paper_trading_false(self) -> None:
        """Test AlpacaManager configuration with paper trading disabled."""
        container = InfrastructureProviders()

        # Override config with live trading mode
        container.config.alpaca_api_key.override("live_api_key")
        container.config.alpaca_secret_key.override("live_secret_key")
        container.config.paper_trading.override(False)  # noqa: FBT003

        # Get the alpaca_manager instance
        alpaca_manager = container.alpaca_manager()

        # Verify it's configured for live trading
        assert alpaca_manager._paper is False

    def test_alpaca_manager_singleton_survives_multiple_lookups(self) -> None:
        """Test that singleton pattern persists across multiple provider lookups."""
        container = InfrastructureProviders()

        # Mock the config dependencies
        container.config.alpaca_api_key.override("test_key")
        container.config.alpaca_secret_key.override("test_secret")
        container.config.paper_trading.override(True)  # noqa: FBT003

        # Get multiple instances via different paths
        instances = [
            container.alpaca_manager(),
            container.trading_repository(),
            container.market_data_repository(),
            container.account_repository(),
            container.alpaca_manager(),  # Again via primary name
        ]

        # Verify all are the same instance
        first_instance = instances[0]
        for instance in instances[1:]:
            assert instance is first_instance

    def test_container_inheritance(self) -> None:
        """Test that InfrastructureProviders inherits from DeclarativeContainer."""
        from dependency_injector import containers

        assert issubclass(InfrastructureProviders, containers.DeclarativeContainer)

    def test_container_has_correct_module_docstring(self) -> None:
        """Test that container module has correct business unit header."""
        import the_alchemiser.shared.config.infrastructure_providers as module

        assert module.__doc__ is not None
        assert "Business Unit: utilities" in module.__doc__
        assert "Status: current" in module.__doc__


@pytest.mark.unit
class TestInfrastructureProvidersIntegration:
    """Integration tests for InfrastructureProviders with dependencies."""

    def test_container_with_real_config_providers(self) -> None:
        """Test container integration with ConfigProviders."""
        from the_alchemiser.shared.config.config_providers import ConfigProviders

        # Create a real config container
        config_container = ConfigProviders()

        # Override with test credentials to avoid real API calls
        config_container.alpaca_api_key.override("test_api_key")
        config_container.alpaca_secret_key.override("test_secret_key")
        config_container.paper_trading.override(True)  # noqa: FBT003

        # Create infrastructure container with config dependency
        infrastructure_container = InfrastructureProviders()
        infrastructure_container.config.override(config_container)

        # Verify we can get instances
        alpaca_manager = infrastructure_container.alpaca_manager()
        assert alpaca_manager is not None
        assert alpaca_manager._api_key == "test_api_key"
        assert alpaca_manager._secret_key == "test_secret_key"
        assert alpaca_manager._paper is True

    def test_multiple_containers_maintain_separate_singletons(self) -> None:
        """Test that different container instances have separate singletons."""
        # Create two separate containers
        container1 = InfrastructureProviders()
        container2 = InfrastructureProviders()

        # Override with different configs
        container1.config.alpaca_api_key.override("key1")
        container1.config.alpaca_secret_key.override("secret1")
        container1.config.paper_trading.override(True)  # noqa: FBT003

        container2.config.alpaca_api_key.override("key2")
        container2.config.alpaca_secret_key.override("secret2")
        container2.config.paper_trading.override(False)  # noqa: FBT003

        # Get instances from each container
        manager1 = container1.alpaca_manager()
        manager2 = container2.alpaca_manager()

        # Verify they are different instances with different configs
        assert manager1 is not manager2
        assert manager1._api_key == "key1"
        assert manager2._api_key == "key2"
        assert manager1._paper is True
        assert manager2._paper is False


@pytest.mark.unit
class TestInfrastructureProvidersDocumentation:
    """Test that providers are properly documented."""

    def test_class_has_docstring(self) -> None:
        """Test that InfrastructureProviders class has a docstring."""
        assert InfrastructureProviders.__doc__ is not None
        assert len(InfrastructureProviders.__doc__.strip()) > 0
        assert "infrastructure layer" in InfrastructureProviders.__doc__.lower()

    def test_module_follows_naming_conventions(self) -> None:
        """Test that module name follows snake_case convention."""
        import the_alchemiser.shared.config.infrastructure_providers as module

        # Module name should be snake_case
        assert module.__name__ == "the_alchemiser.shared.config.infrastructure_providers"

    def test_class_name_follows_conventions(self) -> None:
        """Test that class name follows PascalCase convention."""
        # Class name should be PascalCase
        assert InfrastructureProviders.__name__ == "InfrastructureProviders"
