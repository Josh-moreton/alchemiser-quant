"""Tests for ConfigService."""

from __future__ import annotations

import pytest

from the_alchemiser.shared.config.config import Settings
from the_alchemiser.shared.config.config_service import (
    CONFIG_KEY_ALPACA_ENDPOINT,
    CONFIG_KEY_ALPACA_PAPER_ENDPOINT,
    DEFAULT_CACHE_DURATION_SECONDS,
    ConfigService,
)
from the_alchemiser.shared.errors.exceptions import ConfigurationError


class TestConfigServiceInitialization:
    """Test ConfigService initialization behavior."""

    def test_init_with_explicit_config(self) -> None:
        """Test initialization with explicitly provided Settings object."""
        # Arrange
        settings = Settings()

        # Act
        service = ConfigService(config=settings)

        # Assert
        assert service.config is settings
        assert isinstance(service.config, Settings)

    def test_init_with_none_loads_settings(self) -> None:
        """Test initialization with None delegates to load_settings()."""
        # Act
        service = ConfigService(config=None)

        # Assert
        assert service.config is not None
        assert isinstance(service.config, Settings)

    def test_init_default_loads_settings(self) -> None:
        """Test initialization without argument delegates to load_settings()."""
        # Act
        service = ConfigService()

        # Assert
        assert service.config is not None
        assert isinstance(service.config, Settings)

    def test_config_immutable_after_initialization(self) -> None:
        """Test that config cannot be modified after initialization."""
        # Arrange
        service = ConfigService()

        # Act & Assert - Should not have setter
        with pytest.raises(AttributeError):
            service.config = Settings()  # type: ignore[misc]


class TestConfigServiceProperties:
    """Test ConfigService property accessors."""

    def test_config_property_returns_settings(self) -> None:
        """Test config property returns the Settings object."""
        # Arrange
        settings = Settings()
        service = ConfigService(config=settings)

        # Act
        result = service.config

        # Assert
        assert result is settings
        assert isinstance(result, Settings)

    def test_cache_duration_returns_configured_value(self) -> None:
        """Test cache_duration returns configured value when present."""
        # Arrange
        settings = Settings()
        settings.data.cache_duration = 600
        service = ConfigService(config=settings)

        # Act
        result = service.cache_duration

        # Assert
        assert result == 600
        assert isinstance(result, int)

    def test_cache_duration_returns_default_when_none(self) -> None:
        """Test cache_duration returns default 3600 when not configured."""
        # Arrange
        settings = Settings()
        settings.data.cache_duration = None  # type: ignore[assignment]
        service = ConfigService(config=settings)

        # Act
        result = service.cache_duration

        # Assert
        assert result == 3600

    def test_cache_duration_returns_default_when_zero(self) -> None:
        """Test cache_duration returns default when configured as zero."""
        # Arrange
        settings = Settings()
        settings.data.cache_duration = 0
        service = ConfigService(config=settings)

        # Act
        result = service.cache_duration

        # Assert
        assert result == 3600  # Falls back to default via `or 3600`

    def test_paper_endpoint_returns_configured_value(self) -> None:
        """Test paper_endpoint returns configured Alpaca paper endpoint."""
        # Arrange
        service = ConfigService()

        # Act
        result = service.paper_endpoint

        # Assert
        assert isinstance(result, str)
        assert "paper" in result.lower() or "alpaca" in result.lower()
        assert result.startswith("http")

    def test_live_endpoint_returns_configured_value(self) -> None:
        """Test live_endpoint returns configured Alpaca live endpoint."""
        # Arrange
        service = ConfigService()

        # Act
        result = service.live_endpoint

        # Assert
        assert isinstance(result, str)
        assert "alpaca" in result.lower()
        assert result.startswith("http")

    def test_endpoints_are_different(self) -> None:
        """Test paper and live endpoints are distinct."""
        # Arrange
        service = ConfigService()

        # Act
        paper = service.paper_endpoint
        live = service.live_endpoint

        # Assert
        assert paper != live


class TestConfigServiceGetEndpoint:
    """Test get_endpoint() helper method."""

    def test_get_endpoint_paper_trading_true(self) -> None:
        """Test get_endpoint returns paper endpoint when paper_trading=True."""
        # Arrange
        service = ConfigService()

        # Act
        result = service.get_endpoint(paper_trading=True)

        # Assert
        assert result == service.paper_endpoint
        assert "paper" in result.lower() or result == service.paper_endpoint

    def test_get_endpoint_paper_trading_false(self) -> None:
        """Test get_endpoint returns live endpoint when paper_trading=False."""
        # Arrange
        service = ConfigService()

        # Act
        result = service.get_endpoint(paper_trading=False)

        # Assert
        assert result == service.live_endpoint

    def test_get_endpoint_requires_keyword_argument(self) -> None:
        """Test get_endpoint enforces keyword-only argument."""
        # Arrange
        service = ConfigService()

        # Act & Assert - Should require keyword argument
        with pytest.raises(TypeError):
            service.get_endpoint(True)  # type: ignore[misc]


class TestConfigServiceConsistency:
    """Test ConfigService consistency across multiple calls."""

    def test_config_property_returns_same_instance(self) -> None:
        """Test config property returns same Settings instance on multiple calls."""
        # Arrange
        service = ConfigService()

        # Act
        result1 = service.config
        result2 = service.config

        # Assert
        assert result1 is result2

    def test_cache_duration_consistent_across_calls(self) -> None:
        """Test cache_duration returns consistent value on multiple calls."""
        # Arrange
        service = ConfigService()

        # Act
        result1 = service.cache_duration
        result2 = service.cache_duration

        # Assert
        assert result1 == result2

    def test_endpoints_consistent_across_calls(self) -> None:
        """Test endpoints return consistent values on multiple calls."""
        # Arrange
        service = ConfigService()

        # Act
        paper1 = service.paper_endpoint
        paper2 = service.paper_endpoint
        live1 = service.live_endpoint
        live2 = service.live_endpoint

        # Assert
        assert paper1 == paper2
        assert live1 == live2


class TestConfigServiceEdgeCases:
    """Test ConfigService edge cases and boundary conditions."""

    def test_initialization_with_custom_settings(self) -> None:
        """Test initialization with customized Settings object."""
        # Arrange
        settings = Settings()
        settings.data.cache_duration = 1800
        settings.alpaca.paper_trading = True

        # Act
        service = ConfigService(config=settings)

        # Assert
        assert service.cache_duration == 1800
        assert service.config.alpaca.paper_trading is True

    def test_service_does_not_modify_provided_config(self) -> None:
        """Test ConfigService does not modify the Settings object passed to it."""
        # Arrange
        settings = Settings()
        original_cache = settings.data.cache_duration

        # Act
        service = ConfigService(config=settings)
        _ = service.cache_duration
        _ = service.paper_endpoint

        # Assert
        assert settings.data.cache_duration == original_cache

    def test_multiple_services_with_same_config(self) -> None:
        """Test multiple ConfigService instances can share same Settings object."""
        # Arrange
        settings = Settings()

        # Act
        service1 = ConfigService(config=settings)
        service2 = ConfigService(config=settings)

        # Assert
        assert service1.config is service2.config
        assert service1.cache_duration == service2.cache_duration


class TestConfigServiceIntegration:
    """Integration tests for ConfigService with real configuration."""

    def test_load_from_environment(self) -> None:
        """Test ConfigService loads from actual environment configuration."""
        # Act
        service = ConfigService()

        # Assert - Should successfully load without errors
        assert service.config is not None
        assert service.cache_duration > 0
        assert service.paper_endpoint
        assert service.live_endpoint

    def test_all_properties_accessible(self) -> None:
        """Test all public properties are accessible without errors."""
        # Arrange
        service = ConfigService()

        # Act & Assert - Should not raise any exceptions
        _ = service.config
        _ = service.cache_duration
        _ = service.paper_endpoint
        _ = service.live_endpoint
        _ = service.get_endpoint(paper_trading=True)
        _ = service.get_endpoint(paper_trading=False)


class TestConfigServiceValidation:
    """Test ConfigService validation and error handling."""

    def test_cache_duration_validates_negative_value(self) -> None:
        """Test cache_duration raises ConfigurationError for negative values."""
        # Arrange
        settings = Settings()
        settings.data.cache_duration = -100
        service = ConfigService(config=settings)

        # Act & Assert
        with pytest.raises(ConfigurationError) as exc_info:
            _ = service.cache_duration

        assert "cache_duration must be positive" in str(exc_info.value)
        assert exc_info.value.config_key == "data.cache_duration"

    def test_cache_duration_uses_default_constant(self) -> None:
        """Test cache_duration uses DEFAULT_CACHE_DURATION_SECONDS constant."""
        # Arrange
        settings = Settings()
        settings.data.cache_duration = None  # type: ignore[assignment]
        service = ConfigService(config=settings)

        # Act
        result = service.cache_duration

        # Assert
        assert result == DEFAULT_CACHE_DURATION_SECONDS
        assert result == 3600

    def test_paper_endpoint_validates_url_format(self) -> None:
        """Test paper_endpoint raises ConfigurationError for invalid URLs."""
        # Arrange
        settings = Settings()
        settings.alpaca.paper_endpoint = "invalid-url"
        service = ConfigService(config=settings)

        # Act & Assert
        with pytest.raises(ConfigurationError) as exc_info:
            _ = service.paper_endpoint

        assert "Invalid paper endpoint URL" in str(exc_info.value)
        assert "http" in str(exc_info.value).lower()

    def test_live_endpoint_validates_url_format(self) -> None:
        """Test live_endpoint raises ConfigurationError for invalid URLs."""
        # Arrange
        settings = Settings()
        settings.alpaca.endpoint = "not-a-url"
        service = ConfigService(config=settings)

        # Act & Assert
        with pytest.raises(ConfigurationError) as exc_info:
            _ = service.live_endpoint

        assert "Invalid live endpoint URL" in str(exc_info.value)
        assert "http" in str(exc_info.value).lower()

    def test_paper_endpoint_validates_empty_string(self) -> None:
        """Test paper_endpoint raises ConfigurationError for empty string."""
        # Arrange
        settings = Settings()
        settings.alpaca.paper_endpoint = ""
        service = ConfigService(config=settings)

        # Act & Assert
        with pytest.raises(ConfigurationError) as exc_info:
            _ = service.paper_endpoint

        assert "Invalid paper endpoint URL" in str(exc_info.value)

    def test_live_endpoint_validates_empty_string(self) -> None:
        """Test live_endpoint raises ConfigurationError for empty string."""
        # Arrange
        settings = Settings()
        settings.alpaca.endpoint = ""
        service = ConfigService(config=settings)

        # Act & Assert
        with pytest.raises(ConfigurationError) as exc_info:
            _ = service.live_endpoint

        assert "Invalid live endpoint URL" in str(exc_info.value)

    def test_paper_endpoint_accepts_valid_http_url(self) -> None:
        """Test paper_endpoint accepts valid HTTP URL."""
        # Arrange
        settings = Settings()
        settings.alpaca.paper_endpoint = "http://paper-api.alpaca.markets"
        service = ConfigService(config=settings)

        # Act
        result = service.paper_endpoint

        # Assert
        assert result == "http://paper-api.alpaca.markets"

    def test_live_endpoint_accepts_valid_https_url(self) -> None:
        """Test live_endpoint accepts valid HTTPS URL."""
        # Arrange
        settings = Settings()
        settings.alpaca.endpoint = "https://api.alpaca.markets"
        service = ConfigService(config=settings)

        # Act
        result = service.live_endpoint

        # Assert
        assert result == "https://api.alpaca.markets"


class TestConfigServiceConstants:
    """Test ConfigService constants are properly defined."""

    def test_default_cache_duration_constant_exists(self) -> None:
        """Test DEFAULT_CACHE_DURATION_SECONDS constant is defined."""
        assert DEFAULT_CACHE_DURATION_SECONDS == 3600

    def test_default_cache_duration_is_positive(self) -> None:
        """Test DEFAULT_CACHE_DURATION_SECONDS is a positive value."""
        assert DEFAULT_CACHE_DURATION_SECONDS > 0

    def test_config_key_alpaca_paper_endpoint_constant(self) -> None:
        """Test CONFIG_KEY_ALPACA_PAPER_ENDPOINT constant is defined correctly."""
        assert CONFIG_KEY_ALPACA_PAPER_ENDPOINT == "alpaca.paper_endpoint"
        assert isinstance(CONFIG_KEY_ALPACA_PAPER_ENDPOINT, str)

    def test_config_key_alpaca_endpoint_constant(self) -> None:
        """Test CONFIG_KEY_ALPACA_ENDPOINT constant is defined correctly."""
        assert CONFIG_KEY_ALPACA_ENDPOINT == "alpaca.endpoint"
        assert isinstance(CONFIG_KEY_ALPACA_ENDPOINT, str)
