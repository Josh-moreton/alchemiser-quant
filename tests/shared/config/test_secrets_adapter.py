"""Business Unit: shared | Status: current.

Comprehensive tests for secrets_adapter module.

Tests cover:
- Alpaca credentials loading (flat and nested formats)
- Email password loading (Pydantic config and env vars)
- Input validation and sanitization
- Error handling with typed exceptions
- Logging with structured context
- Edge cases (whitespace, empty strings, invalid URLs)
"""

from __future__ import annotations

from unittest.mock import Mock, patch

import pytest

from the_alchemiser.shared.config.secrets_adapter import (
    DEFAULT_PAPER_ENDPOINT,
    MAX_KEY_LENGTH,
    get_alpaca_keys,
    get_email_password,
)
from the_alchemiser.shared.errors.exceptions import ConfigurationError


class TestGetAlpacaKeys:
    """Test Alpaca credentials loading."""

    def test_loads_flat_format_env_vars(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should load ALPACA_KEY/ALPACA_SECRET format."""
        monkeypatch.setenv("ALPACA_KEY", "test_key_123")
        monkeypatch.setenv("ALPACA_SECRET", "test_secret_456")
        monkeypatch.setenv("ALPACA_ENDPOINT", "https://api.alpaca.markets")

        api_key, secret_key, endpoint = get_alpaca_keys()

        assert api_key == "test_key_123"
        assert secret_key == "test_secret_456"
        assert endpoint == "https://api.alpaca.markets"

    def test_loads_nested_format_env_vars(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should load ALPACA__KEY/ALPACA__SECRET Pydantic format."""
        monkeypatch.setenv("ALPACA__KEY", "test_key_nested")
        monkeypatch.setenv("ALPACA__SECRET", "test_secret_nested")
        monkeypatch.setenv("ALPACA__ENDPOINT", "https://paper-api.alpaca.markets")

        api_key, secret_key, endpoint = get_alpaca_keys()

        assert api_key == "test_key_nested"
        assert secret_key == "test_secret_nested"
        assert endpoint == "https://paper-api.alpaca.markets"

    def test_prefers_flat_format_over_nested(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should prefer ALPACA_KEY over ALPACA__KEY when both present."""
        monkeypatch.setenv("ALPACA_KEY", "flat_key")
        monkeypatch.setenv("ALPACA__KEY", "nested_key")
        monkeypatch.setenv("ALPACA_SECRET", "flat_secret")
        monkeypatch.setenv("ALPACA__SECRET", "nested_secret")

        api_key, secret_key, endpoint = get_alpaca_keys()

        assert api_key == "flat_key"
        assert secret_key == "flat_secret"

    def test_returns_none_tuple_when_key_missing(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should return (None, None, None) when API key missing."""
        monkeypatch.setenv("ALPACA_SECRET", "test_secret")
        # ALPACA_KEY not set

        result = get_alpaca_keys()

        assert result == (None, None, None)

    def test_returns_none_tuple_when_secret_missing(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should return (None, None, None) when secret missing."""
        monkeypatch.setenv("ALPACA_KEY", "test_key")
        # ALPACA_SECRET not set

        result = get_alpaca_keys()

        assert result == (None, None, None)

    def test_defaults_to_paper_endpoint_when_not_set(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should default to paper trading endpoint."""
        monkeypatch.setenv("ALPACA_KEY", "test_key")
        monkeypatch.setenv("ALPACA_SECRET", "test_secret")
        # ALPACA_ENDPOINT not set

        _, _, endpoint = get_alpaca_keys()

        assert endpoint == DEFAULT_PAPER_ENDPOINT

    def test_uses_provided_endpoint(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should use ALPACA_ENDPOINT when provided."""
        monkeypatch.setenv("ALPACA_KEY", "test_key")
        monkeypatch.setenv("ALPACA_SECRET", "test_secret")
        monkeypatch.setenv("ALPACA_ENDPOINT", "https://custom.api.com")

        _, _, endpoint = get_alpaca_keys()

        assert endpoint == "https://custom.api.com"

    def test_strips_whitespace_from_values(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should strip whitespace from credentials."""
        monkeypatch.setenv("ALPACA_KEY", "  test_key  ")
        monkeypatch.setenv("ALPACA_SECRET", "\ttest_secret\n")
        monkeypatch.setenv("ALPACA_ENDPOINT", "  https://api.alpaca.markets  ")

        api_key, secret_key, endpoint = get_alpaca_keys()

        assert api_key == "test_key"
        assert secret_key == "test_secret"
        assert endpoint == "https://api.alpaca.markets"

    def test_raises_error_for_empty_key_after_strip(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should raise ConfigurationError for empty key after stripping."""
        monkeypatch.setenv("ALPACA_KEY", "   ")
        monkeypatch.setenv("ALPACA_SECRET", "test_secret")

        with pytest.raises(ConfigurationError) as exc_info:
            get_alpaca_keys()

        assert "ALPACA_KEY" in str(exc_info.value)
        assert "empty" in str(exc_info.value).lower()

    def test_raises_error_for_empty_secret_after_strip(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should raise ConfigurationError for empty secret after stripping."""
        monkeypatch.setenv("ALPACA_KEY", "test_key")
        monkeypatch.setenv("ALPACA_SECRET", "\t\n  ")

        with pytest.raises(ConfigurationError) as exc_info:
            get_alpaca_keys()

        assert "ALPACA_SECRET" in str(exc_info.value)
        assert "empty" in str(exc_info.value).lower()

    def test_raises_error_for_key_exceeding_max_length(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should raise ConfigurationError for key exceeding max length."""
        long_key = "x" * (MAX_KEY_LENGTH + 1)
        monkeypatch.setenv("ALPACA_KEY", long_key)
        monkeypatch.setenv("ALPACA_SECRET", "test_secret")

        with pytest.raises(ConfigurationError) as exc_info:
            get_alpaca_keys()

        assert "ALPACA_KEY" in str(exc_info.value)
        assert "maximum length" in str(exc_info.value).lower()

    def test_raises_error_for_invalid_endpoint_url(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should raise ConfigurationError for invalid endpoint URL format."""
        monkeypatch.setenv("ALPACA_KEY", "test_key")
        monkeypatch.setenv("ALPACA_SECRET", "test_secret")
        monkeypatch.setenv("ALPACA_ENDPOINT", "not-a-url")

        with pytest.raises(ConfigurationError) as exc_info:
            get_alpaca_keys()

        assert "ALPACA_ENDPOINT" in str(exc_info.value)
        assert "HTTP" in str(exc_info.value)

    def test_logs_error_for_missing_credentials(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Should log error when credentials missing."""
        # No credentials set
        result = get_alpaca_keys()

        assert result == (None, None, None)
        assert any("Missing required Alpaca credentials" in record.message for record in caplog.records)

    def test_logs_debug_for_successful_load(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Should log debug message on successful load."""
        monkeypatch.setenv("ALPACA_KEY", "test_key")
        monkeypatch.setenv("ALPACA_SECRET", "test_secret")

        with caplog.at_level("DEBUG"):
            get_alpaca_keys()

        assert any("Successfully loaded Alpaca credential metadata" in record.message for record in caplog.records)

    def test_logs_info_for_default_endpoint(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Should log info when defaulting to paper trading."""
        monkeypatch.setenv("ALPACA_KEY", "test_key")
        monkeypatch.setenv("ALPACA_SECRET", "test_secret")
        # No endpoint set

        get_alpaca_keys()

        assert any("defaulting to paper trading mode" in record.message for record in caplog.records)

    def test_defaults_to_paper_for_empty_endpoint_after_strip(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should default to paper endpoint if ALPACA_ENDPOINT is empty after strip."""
        monkeypatch.setenv("ALPACA_KEY", "test_key")
        monkeypatch.setenv("ALPACA_SECRET", "test_secret")
        monkeypatch.setenv("ALPACA_ENDPOINT", "   ")

        _, _, endpoint = get_alpaca_keys()

        assert endpoint == DEFAULT_PAPER_ENDPOINT


class TestGetEmailPassword:
    """Test email password loading."""

    def test_loads_from_pydantic_config_preferred(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should prefer loading via load_settings()."""
        mock_config = Mock()
        mock_config.email.password = "pydantic_password"

        with patch("the_alchemiser.shared.config.secrets_adapter.load_settings", return_value=mock_config):
            password = get_email_password()

        assert password == "pydantic_password"

    def test_strips_whitespace_from_pydantic_password(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should strip whitespace from Pydantic config password."""
        mock_config = Mock()
        mock_config.email.password = "  pydantic_password  "

        with patch("the_alchemiser.shared.config.secrets_adapter.load_settings", return_value=mock_config):
            password = get_email_password()

        assert password == "pydantic_password"

    def test_skips_empty_pydantic_password_after_strip(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should skip Pydantic password if empty after stripping."""
        mock_config = Mock()
        mock_config.email.password = "   "
        monkeypatch.setenv("EMAIL_PASSWORD", "fallback_password")

        with patch("the_alchemiser.shared.config.secrets_adapter.load_settings", return_value=mock_config):
            password = get_email_password()

        assert password == "fallback_password"

    def test_falls_back_to_env_vars_when_config_fails(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should fallback to direct env vars if Pydantic fails."""
        monkeypatch.setenv("EMAIL_PASSWORD", "fallback_password")

        with patch(
            "the_alchemiser.shared.config.secrets_adapter.load_settings",
            side_effect=Exception("Config failed"),
        ):
            password = get_email_password()

        assert password == "fallback_password"

    def test_reraises_configuration_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should re-raise ConfigurationError from load_settings."""
        with patch(
            "the_alchemiser.shared.config.secrets_adapter.load_settings",
            side_effect=ConfigurationError("Invalid config"),
        ):
            with pytest.raises(ConfigurationError, match="Invalid config"):
                get_email_password()

    def test_tries_email__password_env_var(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should try EMAIL__PASSWORD env var."""
        monkeypatch.setenv("EMAIL__PASSWORD", "email__pass")

        with patch(
            "the_alchemiser.shared.config.secrets_adapter.load_settings",
            side_effect=Exception("No config"),
        ):
            password = get_email_password()

        assert password == "email__pass"

    def test_tries_email_password_env_var(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should try EMAIL_PASSWORD env var."""
        monkeypatch.setenv("EMAIL_PASSWORD", "email_pass")

        with patch(
            "the_alchemiser.shared.config.secrets_adapter.load_settings",
            side_effect=Exception("No config"),
        ):
            password = get_email_password()

        assert password == "email_pass"

    def test_tries_email__smtp_password_env_var(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should try EMAIL__SMTP_PASSWORD env var."""
        monkeypatch.setenv("EMAIL__SMTP_PASSWORD", "smtp_pass")

        with patch(
            "the_alchemiser.shared.config.secrets_adapter.load_settings",
            side_effect=Exception("No config"),
        ):
            password = get_email_password()

        assert password == "smtp_pass"

    def test_tries_smtp_password_env_var(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should try SMTP_PASSWORD env var."""
        monkeypatch.setenv("SMTP_PASSWORD", "smtp_pass")

        with patch(
            "the_alchemiser.shared.config.secrets_adapter.load_settings",
            side_effect=Exception("No config"),
        ):
            password = get_email_password()

        assert password == "smtp_pass"

    def test_prefers_email__password_over_others(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should prefer EMAIL__PASSWORD when multiple env vars set."""
        monkeypatch.setenv("EMAIL__PASSWORD", "preferred")
        monkeypatch.setenv("EMAIL_PASSWORD", "other1")
        monkeypatch.setenv("SMTP_PASSWORD", "other2")

        with patch(
            "the_alchemiser.shared.config.secrets_adapter.load_settings",
            side_effect=Exception("No config"),
        ):
            password = get_email_password()

        assert password == "preferred"

    def test_strips_whitespace_from_env_var_password(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should strip whitespace from environment variable password."""
        monkeypatch.setenv("EMAIL_PASSWORD", "  env_password  ")

        with patch(
            "the_alchemiser.shared.config.secrets_adapter.load_settings",
            side_effect=Exception("No config"),
        ):
            password = get_email_password()

        assert password == "env_password"

    def test_returns_none_when_not_found(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should return None when password not found."""
        with patch(
            "the_alchemiser.shared.config.secrets_adapter.load_settings",
            side_effect=Exception("No config"),
        ):
            password = get_email_password()

        assert password is None

    def test_returns_none_for_empty_password_after_strip(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should return None if password is empty after stripping."""
        monkeypatch.setenv("EMAIL_PASSWORD", "   ")

        with patch(
            "the_alchemiser.shared.config.secrets_adapter.load_settings",
            side_effect=Exception("No config"),
        ):
            password = get_email_password()

        assert password is None

    def test_logs_warning_when_not_found(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Should log warning listing tried env vars."""
        with patch(
            "the_alchemiser.shared.config.secrets_adapter.load_settings",
            side_effect=Exception("No config"),
        ):
            get_email_password()

        assert any("Email password not found" in record.message for record in caplog.records)

    def test_logs_debug_for_pydantic_success(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Should log debug message on Pydantic config success."""
        mock_config = Mock()
        mock_config.email.password = "pydantic_password"

        with caplog.at_level("DEBUG"):
            with patch("the_alchemiser.shared.config.secrets_adapter.load_settings", return_value=mock_config):
                get_email_password()

        assert any("Successfully loaded email password from Pydantic config" in record.message for record in caplog.records)

    def test_logs_debug_for_env_var_success(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Should log debug message on env var success."""
        monkeypatch.setenv("EMAIL_PASSWORD", "env_password")

        with caplog.at_level("DEBUG"):
            with patch(
                "the_alchemiser.shared.config.secrets_adapter.load_settings",
                side_effect=Exception("No config"),
            ):
                get_email_password()

        assert any("Successfully loaded email password from environment variables" in record.message for record in caplog.records)

    def test_logs_debug_for_pydantic_failure(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Should log debug message when Pydantic config fails."""
        monkeypatch.setenv("EMAIL_PASSWORD", "env_password")

        with caplog.at_level("DEBUG"):
            with patch(
                "the_alchemiser.shared.config.secrets_adapter.load_settings",
                side_effect=ValueError("Test error"),
            ):
                get_email_password()

        assert any("Could not load email password from Pydantic config" in record.message for record in caplog.records)
