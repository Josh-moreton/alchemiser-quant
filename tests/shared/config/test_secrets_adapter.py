"""Business Unit: shared | Status: current.

Comprehensive tests for secrets_adapter module.

Tests cover:
- Alpaca credentials loading (flat and nested formats)
- Input validation and sanitization
- Error handling with typed exceptions
- Logging with structured context
- Edge cases (whitespace, empty strings, invalid URLs)
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from the_alchemiser.shared.config.secrets_adapter import (
    DEFAULT_PAPER_ENDPOINT,
    MAX_KEY_LENGTH,
    get_alpaca_keys,
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

    def test_returns_none_tuple_when_secret_missing(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should return (None, None, None) when secret missing."""
        monkeypatch.setenv("ALPACA_KEY", "test_key")
        # ALPACA_SECRET not set

        result = get_alpaca_keys()

        assert result == (None, None, None)

    def test_defaults_to_paper_endpoint_when_not_set(self, monkeypatch: pytest.MonkeyPatch) -> None:
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

    def test_raises_error_for_empty_key_after_strip(self, monkeypatch: pytest.MonkeyPatch) -> None:
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

    def test_raises_error_for_invalid_endpoint_url(self, monkeypatch: pytest.MonkeyPatch) -> None:
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
        assert any(
            "Missing required Alpaca credentials" in record.message for record in caplog.records
        )

    def test_logs_debug_for_successful_load(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Should log debug message on successful load."""
        monkeypatch.setenv("ALPACA_KEY", "test_key")
        monkeypatch.setenv("ALPACA_SECRET", "test_secret")

        with caplog.at_level("DEBUG"):
            get_alpaca_keys()

        assert any(
            "Successfully loaded Alpaca credential metadata" in record.message
            for record in caplog.records
        )

    def test_logs_info_for_default_endpoint(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Should log info when defaulting to paper trading."""
        monkeypatch.setenv("ALPACA_KEY", "test_key")
        monkeypatch.setenv("ALPACA_SECRET", "test_secret")
        # No endpoint set

        get_alpaca_keys()

        assert any(
            "defaulting to paper trading mode" in record.message for record in caplog.records
        )

    def test_defaults_to_paper_for_empty_endpoint_after_strip(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should default to paper endpoint if ALPACA_ENDPOINT is empty after strip."""
        monkeypatch.setenv("ALPACA_KEY", "test_key")
        monkeypatch.setenv("ALPACA_SECRET", "test_secret")
        monkeypatch.setenv("ALPACA_ENDPOINT", "   ")

        _, _, endpoint = get_alpaca_keys()

        assert endpoint == DEFAULT_PAPER_ENDPOINT
