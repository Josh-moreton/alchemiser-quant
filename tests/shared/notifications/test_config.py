#!/usr/bin/env python3
"""Test suite for shared/notifications/config.py.

Tests EmailConfig for:
- Successful configuration loading
- Missing required fields (from_email, password)
- Default fallback behavior (to_email)
- Cache behavior
- Thread safety
- Error handling with typed exceptions
- Neutral mode caching
- Backward compatibility functions
"""

from __future__ import annotations

from unittest.mock import Mock, patch

import pytest

from the_alchemiser.shared.errors import ConfigurationError
from the_alchemiser.shared.notifications.config import (
    EmailConfig,
    get_email_config,
    is_neutral_mode_enabled,
)
from the_alchemiser.shared.schemas.notifications import EmailCredentials


class TestEmailConfigGetConfig:
    """Test suite for EmailConfig.get_config() method."""

    @pytest.fixture
    def mock_settings(self):
        """Mock settings object with valid email configuration."""
        settings = Mock()
        settings.email.smtp_server = "smtp.example.com"
        settings.email.smtp_port = 587
        settings.email.from_email = "sender@example.com"
        settings.email.to_email = "recipient@example.com"
        settings.email.neutral_mode = True
        return settings

    @patch("the_alchemiser.shared.notifications.config.load_settings")
    @patch("the_alchemiser.shared.notifications.config.get_email_password")
    def test_get_config_success(self, mock_password, mock_settings_loader, mock_settings):
        """Test successful config loading with all fields present."""
        mock_settings_loader.return_value = mock_settings
        mock_password.return_value = "test_password"

        config = EmailConfig()
        result = config.get_config()

        assert isinstance(result, EmailCredentials)
        assert result.smtp_server == "smtp.example.com"
        assert result.smtp_port == 587
        assert result.email_address == "sender@example.com"
        assert result.email_password == "test_password"
        assert result.recipient_email == "recipient@example.com"

    @patch("the_alchemiser.shared.notifications.config.load_settings")
    @patch("the_alchemiser.shared.notifications.config.get_email_password")
    def test_get_config_caches_result(self, mock_password, mock_settings_loader, mock_settings):
        """Test that get_config() caches the result."""
        mock_settings_loader.return_value = mock_settings
        mock_password.return_value = "test_password"

        config = EmailConfig()
        result1 = config.get_config()
        result2 = config.get_config()

        # Should only call load_settings once due to caching
        assert mock_settings_loader.call_count == 1
        assert result1 is result2  # Same object instance

    @patch("the_alchemiser.shared.notifications.config.load_settings")
    @patch("the_alchemiser.shared.notifications.config.get_email_password")
    def test_get_config_missing_from_email_raises_error(
        self, mock_password, mock_settings_loader, mock_settings
    ):
        """Test that missing from_email raises ConfigurationError."""
        mock_settings.email.from_email = None
        mock_settings_loader.return_value = mock_settings
        mock_password.return_value = "test_password"

        config = EmailConfig()

        with pytest.raises(ConfigurationError, match="from_email is required"):
            config.get_config()

    @patch("the_alchemiser.shared.notifications.config.load_settings")
    @patch("the_alchemiser.shared.notifications.config.get_email_password")
    def test_get_config_missing_password_raises_error(
        self, mock_password, mock_settings_loader, mock_settings
    ):
        """Test that missing password raises ConfigurationError."""
        mock_settings_loader.return_value = mock_settings
        mock_password.return_value = None

        config = EmailConfig()

        with pytest.raises(ConfigurationError, match="Email password is required"):
            config.get_config()

    @patch("the_alchemiser.shared.notifications.config.load_settings")
    @patch("the_alchemiser.shared.notifications.config.get_email_password")
    def test_get_config_to_email_defaults_to_from_email(
        self, mock_password, mock_settings_loader, mock_settings
    ):
        """Test that to_email defaults to from_email when not specified."""
        mock_settings.email.to_email = None
        mock_settings_loader.return_value = mock_settings
        mock_password.return_value = "test_password"

        config = EmailConfig()
        result = config.get_config()

        assert result.recipient_email == "sender@example.com"

    @patch("the_alchemiser.shared.notifications.config.load_settings")
    @patch("the_alchemiser.shared.notifications.config.get_email_password")
    def test_get_config_caches_neutral_mode(
        self, mock_password, mock_settings_loader, mock_settings
    ):
        """Test that neutral_mode is cached alongside credentials."""
        mock_settings_loader.return_value = mock_settings
        mock_password.return_value = "test_password"

        config = EmailConfig()
        config.get_config()

        # Neutral mode should be cached
        assert config._neutral_mode_cache is True

    @patch("the_alchemiser.shared.notifications.config.load_settings")
    @patch("the_alchemiser.shared.notifications.config.get_email_password")
    def test_get_config_wraps_exceptions_as_configuration_error(
        self, mock_password, mock_settings_loader
    ):
        """Test that unexpected exceptions are wrapped as ConfigurationError."""
        mock_settings_loader.side_effect = RuntimeError("Database unavailable")

        config = EmailConfig()

        with pytest.raises(ConfigurationError, match="Failed to load email configuration"):
            config.get_config()


class TestEmailConfigClearCache:
    """Test suite for EmailConfig.clear_cache() method."""

    @pytest.fixture
    def mock_settings(self):
        """Mock settings object with valid email configuration."""
        settings = Mock()
        settings.email.smtp_server = "smtp.example.com"
        settings.email.smtp_port = 587
        settings.email.from_email = "sender@example.com"
        settings.email.to_email = "recipient@example.com"
        settings.email.neutral_mode = True
        return settings

    @patch("the_alchemiser.shared.notifications.config.load_settings")
    @patch("the_alchemiser.shared.notifications.config.get_email_password")
    def test_clear_cache_invalidates_config(
        self, mock_password, mock_settings_loader, mock_settings
    ):
        """Test that clear_cache() invalidates the cached config."""
        mock_settings_loader.return_value = mock_settings
        mock_password.return_value = "test_password"

        config = EmailConfig()
        config.get_config()
        config.clear_cache()
        config.get_config()

        # Should call load_settings twice (before and after clear_cache)
        assert mock_settings_loader.call_count == 2

    @patch("the_alchemiser.shared.notifications.config.load_settings")
    @patch("the_alchemiser.shared.notifications.config.get_email_password")
    def test_clear_cache_invalidates_neutral_mode(
        self, mock_password, mock_settings_loader, mock_settings
    ):
        """Test that clear_cache() invalidates the neutral mode cache."""
        mock_settings_loader.return_value = mock_settings
        mock_password.return_value = "test_password"

        config = EmailConfig()
        config.get_config()

        # Verify caches are set
        assert config._config_cache is not None
        assert config._neutral_mode_cache is not None

        config.clear_cache()

        # Verify caches are cleared
        assert config._config_cache is None
        assert config._neutral_mode_cache is None


class TestEmailConfigIsNeutralModeEnabled:
    """Test suite for EmailConfig.is_neutral_mode_enabled() method."""

    @pytest.fixture
    def mock_settings(self):
        """Mock settings object."""
        settings = Mock()
        settings.email.neutral_mode = True
        return settings

    @patch("the_alchemiser.shared.notifications.config.load_settings")
    def test_is_neutral_mode_enabled_returns_true(self, mock_settings_loader, mock_settings):
        """Test neutral mode returns True when enabled."""
        mock_settings_loader.return_value = mock_settings

        config = EmailConfig()
        result = config.is_neutral_mode_enabled()

        assert result is True

    @patch("the_alchemiser.shared.notifications.config.load_settings")
    def test_is_neutral_mode_enabled_returns_false(self, mock_settings_loader, mock_settings):
        """Test neutral mode returns False when disabled."""
        mock_settings.email.neutral_mode = False
        mock_settings_loader.return_value = mock_settings

        config = EmailConfig()
        result = config.is_neutral_mode_enabled()

        assert result is False

    @patch("the_alchemiser.shared.notifications.config.load_settings")
    def test_is_neutral_mode_enabled_caches_result(self, mock_settings_loader, mock_settings):
        """Test that neutral mode result is cached."""
        mock_settings_loader.return_value = mock_settings

        config = EmailConfig()
        result1 = config.is_neutral_mode_enabled()
        result2 = config.is_neutral_mode_enabled()

        # Should only call load_settings once due to caching
        assert mock_settings_loader.call_count == 1
        assert result1 is result2

    @patch("the_alchemiser.shared.notifications.config.load_settings")
    def test_is_neutral_mode_enabled_raises_on_error(self, mock_settings_loader):
        """Test that errors are raised as ConfigurationError."""
        mock_settings_loader.side_effect = RuntimeError("Settings unavailable")

        config = EmailConfig()

        with pytest.raises(ConfigurationError, match="Failed to check neutral mode"):
            config.is_neutral_mode_enabled()


class TestBackwardCompatibilityFunctions:
    """Test suite for backward compatibility functions."""

    @pytest.fixture
    def mock_settings(self):
        """Mock settings object with valid email configuration."""
        settings = Mock()
        settings.email.smtp_server = "smtp.example.com"
        settings.email.smtp_port = 587
        settings.email.from_email = "sender@example.com"
        settings.email.to_email = "recipient@example.com"
        settings.email.neutral_mode = True
        return settings

    @patch("the_alchemiser.shared.notifications.config.load_settings")
    @patch("the_alchemiser.shared.notifications.config.get_email_password")
    def test_get_email_config_returns_tuple(
        self, mock_password, mock_settings_loader, mock_settings
    ):
        """Test that get_email_config() returns a tuple."""
        mock_settings_loader.return_value = mock_settings
        mock_password.return_value = "test_password"

        with pytest.warns(DeprecationWarning, match="get_email_config.*deprecated"):
            result = get_email_config()

        assert isinstance(result, tuple)
        assert len(result) == 5
        assert result[0] == "smtp.example.com"
        assert result[1] == 587
        assert result[2] == "sender@example.com"
        assert result[3] == "test_password"
        assert result[4] == "recipient@example.com"

    @patch("the_alchemiser.shared.notifications.config.load_settings")
    @patch("the_alchemiser.shared.notifications.config.get_email_password")
    def test_get_email_config_returns_none_on_error(
        self, mock_password, mock_settings_loader, mock_settings
    ):
        """Test that get_email_config() returns None on configuration error."""
        mock_settings.email.from_email = None
        mock_settings_loader.return_value = mock_settings
        mock_password.return_value = "test_password"

        with pytest.warns(DeprecationWarning, match="get_email_config.*deprecated"):
            result = get_email_config()

        assert result is None

    @patch("the_alchemiser.shared.notifications.config.load_settings")
    def test_is_neutral_mode_enabled_standalone_returns_bool(
        self, mock_settings_loader, mock_settings
    ):
        """Test that standalone is_neutral_mode_enabled() returns bool."""
        mock_settings_loader.return_value = mock_settings

        with pytest.warns(DeprecationWarning, match="is_neutral_mode_enabled.*deprecated"):
            result = is_neutral_mode_enabled()

        assert isinstance(result, bool)
        assert result is True

    @patch("the_alchemiser.shared.notifications.config.load_settings")
    def test_is_neutral_mode_enabled_standalone_returns_false_on_error(self, mock_settings_loader):
        """Test that standalone is_neutral_mode_enabled() returns False on error."""
        mock_settings_loader.side_effect = RuntimeError("Settings unavailable")

        with pytest.warns(DeprecationWarning, match="is_neutral_mode_enabled.*deprecated"):
            result = is_neutral_mode_enabled()

        assert result is False


class TestThreadSafety:
    """Test suite for thread safety of singleton pattern."""

    @pytest.fixture
    def mock_settings(self):
        """Mock settings object with valid email configuration."""
        settings = Mock()
        settings.email.smtp_server = "smtp.example.com"
        settings.email.smtp_port = 587
        settings.email.from_email = "sender@example.com"
        settings.email.to_email = "recipient@example.com"
        settings.email.neutral_mode = True
        return settings

    @patch("the_alchemiser.shared.notifications.config.load_settings")
    @patch("the_alchemiser.shared.notifications.config.get_email_password")
    def test_singleton_returns_same_instance(
        self, mock_password, mock_settings_loader, mock_settings
    ):
        """Test that singleton pattern returns the same instance."""
        from the_alchemiser.shared.notifications.config import (
            _get_email_config_singleton,
        )

        mock_settings_loader.return_value = mock_settings
        mock_password.return_value = "test_password"

        instance1 = _get_email_config_singleton()
        instance2 = _get_email_config_singleton()

        assert instance1 is instance2

    @patch("the_alchemiser.shared.notifications.config.load_settings")
    @patch("the_alchemiser.shared.notifications.config.get_email_password")
    def test_concurrent_access_thread_safe(
        self, mock_password, mock_settings_loader, mock_settings
    ):
        """Test that concurrent access to singleton is thread-safe."""
        import threading

        from the_alchemiser.shared.notifications.config import (
            _get_email_config_singleton,
        )

        mock_settings_loader.return_value = mock_settings
        mock_password.return_value = "test_password"

        instances = []

        def get_instance():
            instances.append(_get_email_config_singleton())

        # Create multiple threads accessing singleton
        threads = [threading.Thread(target=get_instance) for _ in range(10)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        # All instances should be the same object
        assert all(instance is instances[0] for instance in instances)
