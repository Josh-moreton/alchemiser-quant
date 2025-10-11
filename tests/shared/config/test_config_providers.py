"""Tests for ConfigProviders dependency injection configuration.

Business Unit: shared/config | Status: current.
"""

from __future__ import annotations

from unittest.mock import Mock

import pytest

from the_alchemiser.shared.config.config import Settings
from the_alchemiser.shared.config.config_providers import ConfigProviders


class TestConfigProviders:
    """Test suite for ConfigProviders container."""

    def test_settings_is_singleton(self) -> None:
        """Verify settings provider returns same instance on multiple calls."""
        container = ConfigProviders()

        settings1 = container.settings()
        settings2 = container.settings()

        assert settings1 is settings2, "Settings should be a singleton"

    def test_paper_trading_detection_with_paper_endpoint(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test paper trading flag is True when endpoint contains 'paper'."""
        monkeypatch.setenv("ALPACA_KEY", "test_key")
        monkeypatch.setenv("ALPACA_SECRET", "test_secret")
        monkeypatch.setenv("ALPACA_ENDPOINT", "https://paper-api.alpaca.markets")

        container = ConfigProviders()
        paper_trading = container.paper_trading()

        assert paper_trading is True, "Should detect paper trading from endpoint URL"

    def test_paper_trading_detection_with_live_endpoint(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test paper trading flag is False when endpoint is live."""
        monkeypatch.setenv("ALPACA_KEY", "test_key")
        monkeypatch.setenv("ALPACA_SECRET", "test_secret")
        monkeypatch.setenv("ALPACA_ENDPOINT", "https://api.alpaca.markets")

        container = ConfigProviders()
        paper_trading = container.paper_trading()

        assert paper_trading is False, "Should detect live trading from endpoint URL"

    def test_paper_trading_defaults_to_true_when_no_endpoint(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test paper trading flag defaults to True when endpoint is None."""
        monkeypatch.setenv("ALPACA_KEY", "test_key")
        monkeypatch.setenv("ALPACA_SECRET", "test_secret")
        # Don't set ALPACA_ENDPOINT - it should default
        monkeypatch.delenv("ALPACA_ENDPOINT", raising=False)

        container = ConfigProviders()
        paper_trading = container.paper_trading()

        assert paper_trading is True, "Should default to paper trading when endpoint is None"

    def test_alpaca_api_key_provider(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test API key is correctly extracted from credentials tuple."""
        monkeypatch.setenv("ALPACA_KEY", "test_api_key")
        monkeypatch.setenv("ALPACA_SECRET", "test_secret")
        monkeypatch.setenv("ALPACA_ENDPOINT", "https://paper-api.alpaca.markets")

        container = ConfigProviders()
        api_key = container.alpaca_api_key()

        assert api_key == "test_api_key", "Should extract API key from credentials"

    def test_alpaca_secret_key_provider(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test secret key is correctly extracted from credentials tuple."""
        monkeypatch.setenv("ALPACA_KEY", "test_api_key")
        monkeypatch.setenv("ALPACA_SECRET", "test_secret_key")
        monkeypatch.setenv("ALPACA_ENDPOINT", "https://paper-api.alpaca.markets")

        container = ConfigProviders()
        secret_key = container.alpaca_secret_key()

        assert (
            secret_key == "test_secret_key"
        ), "Should extract secret key from credentials"

    def test_alpaca_endpoint_provider(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test endpoint is correctly extracted from credentials tuple."""
        test_endpoint = "https://paper-api.alpaca.markets"
        monkeypatch.setenv("ALPACA_KEY", "test_api_key")
        monkeypatch.setenv("ALPACA_SECRET", "test_secret")
        monkeypatch.setenv("ALPACA_ENDPOINT", test_endpoint)

        container = ConfigProviders()
        endpoint = container.alpaca_endpoint()

        assert endpoint == test_endpoint, "Should extract endpoint from credentials"

    def test_credentials_provider_when_credentials_missing(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test behavior when credentials are not in environment (returns None tuple)."""
        # Clear all Alpaca credentials from environment
        monkeypatch.delenv("ALPACA_KEY", raising=False)
        monkeypatch.delenv("ALPACA__KEY", raising=False)
        monkeypatch.delenv("ALPACA_SECRET", raising=False)
        monkeypatch.delenv("ALPACA__SECRET", raising=False)
        monkeypatch.delenv("ALPACA_ENDPOINT", raising=False)
        monkeypatch.delenv("ALPACA__ENDPOINT", raising=False)

        container = ConfigProviders()
        api_key = container.alpaca_api_key()
        secret_key = container.alpaca_secret_key()
        endpoint = container.alpaca_endpoint()

        assert api_key is None, "API key should be None when credentials not found"
        assert secret_key is None, "Secret key should be None when credentials not found"
        assert endpoint is None, "Endpoint should be None when credentials not found"

    def test_email_recipient_provider(self) -> None:
        """Test email recipient is extracted from settings."""
        container = ConfigProviders()

        # Create a mock settings object with nested email attribute
        mock_email = Mock()
        mock_email.to_email = "test@example.com"

        mock_settings = Mock(spec=Settings)
        mock_settings.email = mock_email

        container.settings.override(mock_settings)

        recipient = container.email_recipient()

        assert recipient == "test@example.com", "Should extract email from settings"

    def test_execution_provider(self) -> None:
        """Test execution settings are extracted from settings."""
        container = ConfigProviders()

        mock_settings = Mock(spec=Settings)
        mock_execution = Mock()
        mock_settings.execution = mock_execution

        container.settings.override(mock_settings)

        execution = container.execution()

        assert execution is mock_execution, "Should extract execution settings from settings"

    def test_paper_trading_case_insensitive(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test paper trading detection is case-insensitive."""
        test_cases = [
            "https://PAPER-api.alpaca.markets",
            "https://Paper-API.alpaca.markets",
            "https://PaPeR-api.alpaca.markets",
        ]

        for endpoint in test_cases:
            monkeypatch.setenv("ALPACA_KEY", "test_key")
            monkeypatch.setenv("ALPACA_SECRET", "test_secret")
            monkeypatch.setenv("ALPACA_ENDPOINT", endpoint)

            container = ConfigProviders()
            paper_trading = container.paper_trading()

            assert (
                paper_trading is True
            ), f"Should detect paper trading for endpoint: {endpoint}"


class TestConfigProvidersIntegration:
    """Integration tests for ConfigProviders with real configuration."""

    @pytest.mark.integration
    def test_real_settings_load(self) -> None:
        """Test that settings can be loaded from real environment (if configured)."""
        container = ConfigProviders()

        # This should not raise an exception even if .env is missing
        # (Pydantic will use defaults)
        settings = container.settings()

        assert settings is not None, "Settings should be loaded"
        assert hasattr(settings, "alpaca"), "Settings should have alpaca configuration"
        assert hasattr(settings, "email"), "Settings should have email configuration"
        assert hasattr(settings, "execution"), "Settings should have execution configuration"

    @pytest.mark.integration
    def test_credentials_provider_with_real_env(self) -> None:
        """Test credentials provider with real environment (may return None if not configured)."""
        container = ConfigProviders()

        # This should not raise an exception, even if credentials are missing
        api_key = container.alpaca_api_key()
        secret_key = container.alpaca_secret_key()
        endpoint = container.alpaca_endpoint()
        paper_trading = container.paper_trading()

        # Credentials may be None if not configured, but should be consistent
        if api_key is None:
            assert secret_key is None, "If API key is None, secret should also be None"
            assert endpoint is None, "If API key is None, endpoint should also be None"
            assert (
                paper_trading is True
            ), "Paper trading should default to True when no endpoint"
        else:
            assert isinstance(api_key, str), "API key should be string if present"
            assert isinstance(secret_key, str), "Secret key should be string if present"
            # endpoint may be None (defaults to paper), but paper_trading should be bool
            assert isinstance(paper_trading, bool), "Paper trading flag should be boolean"
