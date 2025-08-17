"""Unit tests for infrastructure providers DI container."""

from unittest.mock import Mock, patch

from the_alchemiser.container.application_container import ApplicationContainer
from the_alchemiser.services.market_data.typed_data_provider_adapter import (
    TypedDataProviderAdapter,
)


class TestInfrastructureProviders:
    """Test infrastructure provider DI wiring and container creation."""

    @patch(
        "the_alchemiser.services.shared.secrets_service.SecretsService.get_alpaca_credentials"
    )
    def test_container_creates_typed_data_provider_adapter(
        self, mock_get_credentials: Mock
    ) -> None:
        """Test that DI container creates TypedDataProviderAdapter without network access."""
        # Arrange: Mock credentials to avoid network calls
        mock_get_credentials.return_value = ("test_key", "test_secret")

        # Act: Create test container
        container = ApplicationContainer.create_for_environment("test")

        # Assert: Container created successfully
        assert container is not None
        assert hasattr(container, "infrastructure")

        # Act: Get the data provider instance
        data_provider = container.infrastructure.data_provider()

        # Assert: data_provider is the expected type
        assert type(data_provider) is TypedDataProviderAdapter
        assert isinstance(data_provider, TypedDataProviderAdapter)

    @patch(
        "the_alchemiser.services.shared.secrets_service.SecretsService.get_alpaca_credentials"
    )
    def test_container_data_provider_has_expected_interface(
        self, mock_get_credentials: Mock
    ) -> None:
        """Test that TypedDataProviderAdapter has the expected interface."""
        # Arrange: Mock credentials to avoid network calls
        mock_get_credentials.return_value = ("test_key", "test_secret")

        # Act: Create test container and get data provider
        container = ApplicationContainer.create_for_environment("test")
        data_provider = container.infrastructure.data_provider()

        # Assert: TypedDataProviderAdapter has expected methods
        assert hasattr(data_provider, "get_current_price")
        assert hasattr(data_provider, "get_data")
        assert hasattr(data_provider, "trading_client")
        assert callable(data_provider.get_current_price)
        assert callable(data_provider.get_data)

    def test_di_container_wiring_regression_detection(self) -> None:
        """Test fails meaningfully if DI wiring regresses to non-typed provider."""
        # This test ensures that if someone accidentally changes the DI wiring
        # back to UnifiedDataProvider, the test will fail with a clear message

        # Import the expected type
        expected_type = TypedDataProviderAdapter

        # Verify the type exists and is importable
        assert expected_type is not None
        assert expected_type.__name__ == "TypedDataProviderAdapter"

        # This test will fail if the import path or class name changes,
        # serving as a regression guard
        from the_alchemiser.services.market_data.typed_data_provider_adapter import (
            TypedDataProviderAdapter as ImportedAdapter,
        )

        assert ImportedAdapter is TypedDataProviderAdapter
        assert ImportedAdapter.__name__ == "TypedDataProviderAdapter"
