"""Tests for shared.logging.config module.

This module tests the application-level logging configuration functions
for different environments (production, test, development).
"""

from __future__ import annotations

import logging
import os
from unittest.mock import MagicMock, patch

from the_alchemiser.shared.logging.config import (
    configure_application_logging,
    configure_production_logging,
    configure_test_logging,
)


class TestConfigureTestLogging:
    """Test suite for configure_test_logging function."""

    @patch("the_alchemiser.shared.logging.config.configure_structlog")
    def test_configures_with_default_warning_level(self, mock_configure: MagicMock) -> None:
        """Test that configure_test_logging uses WARNING level by default."""
        configure_test_logging()

        mock_configure.assert_called_once_with(
            structured_format=False,
            console_level=logging.WARNING,
            file_level=logging.WARNING,
        )

    @patch("the_alchemiser.shared.logging.config.configure_structlog")
    def test_configures_with_custom_log_level(self, mock_configure: MagicMock) -> None:
        """Test that configure_test_logging accepts custom log level."""
        configure_test_logging(log_level=logging.DEBUG)

        mock_configure.assert_called_once_with(
            structured_format=False,
            console_level=logging.DEBUG,
            file_level=logging.DEBUG,
        )

    @patch("the_alchemiser.shared.logging.config.configure_structlog")
    def test_uses_console_format_not_json(self, mock_configure: MagicMock) -> None:
        """Test that configure_test_logging uses console format for readability."""
        configure_test_logging()

        # Verify structured_format is False (console format, not JSON)
        call_kwargs = mock_configure.call_args.kwargs
        assert call_kwargs["structured_format"] is False

    @patch("the_alchemiser.shared.logging.config.configure_structlog")
    def test_is_idempotent(self, mock_configure: MagicMock) -> None:
        """Test that multiple calls to configure_test_logging are safe."""
        configure_test_logging(log_level=logging.INFO)
        configure_test_logging(log_level=logging.DEBUG)

        # Should be called twice with different levels
        assert mock_configure.call_count == 2


class TestConfigureProductionLogging:
    """Test suite for configure_production_logging function."""

    @patch("the_alchemiser.shared.logging.config.configure_structlog")
    def test_configures_with_default_info_level(self, mock_configure: MagicMock) -> None:
        """Test that configure_production_logging uses INFO level by default."""
        configure_production_logging()

        mock_configure.assert_called_once_with(
            structured_format=True,
            console_level=logging.INFO,
            file_level=logging.INFO,
            file_path=None,
        )

    @patch("the_alchemiser.shared.logging.config.configure_structlog")
    def test_uses_json_format(self, mock_configure: MagicMock) -> None:
        """Test that configure_production_logging uses JSON format."""
        configure_production_logging()

        # Verify structured_format is True (JSON format)
        call_kwargs = mock_configure.call_args.kwargs
        assert call_kwargs["structured_format"] is True

    @patch("the_alchemiser.shared.logging.config.configure_structlog")
    def test_accepts_custom_log_level(self, mock_configure: MagicMock) -> None:
        """Test that configure_production_logging accepts custom log level."""
        configure_production_logging(log_level=logging.WARNING)

        mock_configure.assert_called_once_with(
            structured_format=True,
            console_level=logging.WARNING,
            file_level=logging.WARNING,
            file_path=None,
        )

    @patch("the_alchemiser.shared.logging.config.configure_structlog")
    def test_accepts_custom_console_level(self, mock_configure: MagicMock) -> None:
        """Test that console_level can override base log_level."""
        configure_production_logging(log_level=logging.INFO, console_level=logging.WARNING)

        call_kwargs = mock_configure.call_args.kwargs
        assert call_kwargs["console_level"] == logging.WARNING
        assert call_kwargs["file_level"] == logging.INFO

    @patch("the_alchemiser.shared.logging.config.configure_structlog")
    def test_accepts_log_file_path(self, mock_configure: MagicMock) -> None:
        """Test that log_file_path parameter is passed through."""
        configure_production_logging(log_file_path="/tmp/test.log")

        call_kwargs = mock_configure.call_args.kwargs
        assert call_kwargs["file_path"] == "/tmp/test.log"

    @patch.dict(os.environ, {"LOG_FILE_PATH": "/var/log/app.log"})
    @patch("the_alchemiser.shared.logging.config.configure_structlog")
    def test_uses_log_file_path_env_var(self, mock_configure: MagicMock) -> None:
        """Test that LOG_FILE_PATH environment variable is used when no path provided."""
        configure_production_logging()

        call_kwargs = mock_configure.call_args.kwargs
        assert call_kwargs["file_path"] == "/var/log/app.log"

    @patch.dict(os.environ, {"LOG_FILE_PATH": "/env/log.log"})
    @patch("the_alchemiser.shared.logging.config.configure_structlog")
    def test_parameter_overrides_env_var(self, mock_configure: MagicMock) -> None:
        """Test that log_file_path parameter takes precedence over env var."""
        configure_production_logging(log_file_path="/param/log.log")

        call_kwargs = mock_configure.call_args.kwargs
        assert call_kwargs["file_path"] == "/param/log.log"

    @patch("the_alchemiser.shared.logging.config.configure_structlog")
    def test_is_idempotent(self, mock_configure: MagicMock) -> None:
        """Test that multiple calls to configure_production_logging are safe."""
        configure_production_logging()
        configure_production_logging(log_level=logging.WARNING)

        # Should be called twice
        assert mock_configure.call_count == 2


class TestConfigureApplicationLogging:
    """Test suite for configure_application_logging function."""

    @patch.dict(os.environ, {"AWS_LAMBDA_FUNCTION_NAME": "my-lambda-function"})
    @patch("the_alchemiser.shared.logging.config.configure_production_logging")
    @patch("the_alchemiser.shared.logging.config.configure_structlog")
    def test_detects_lambda_environment(
        self, mock_structlog: MagicMock, mock_production: MagicMock
    ) -> None:
        """Test that Lambda environment triggers production configuration."""
        configure_application_logging()

        # Should call production logging, not structlog directly
        mock_production.assert_called_once_with(log_level=logging.INFO)
        mock_structlog.assert_not_called()

    @patch.dict(os.environ, {}, clear=True)
    @patch("the_alchemiser.shared.logging.config.configure_production_logging")
    @patch("the_alchemiser.shared.logging.config.configure_structlog")
    def test_uses_development_config_when_not_lambda(
        self, mock_structlog: MagicMock, mock_production: MagicMock
    ) -> None:
        """Test that non-Lambda environment uses development configuration."""
        configure_application_logging()

        # Should call structlog directly for development, not production
        mock_structlog.assert_called_once_with(
            structured_format=False,
            console_level=logging.INFO,
            file_level=logging.DEBUG,
            file_path="logs/trade_run.log",
        )
        mock_production.assert_not_called()

    @patch.dict(os.environ, {"AWS_LAMBDA_FUNCTION_NAME": ""})
    @patch("the_alchemiser.shared.logging.config.configure_production_logging")
    @patch("the_alchemiser.shared.logging.config.configure_structlog")
    def test_empty_lambda_env_var_triggers_production(
        self, mock_structlog: MagicMock, mock_production: MagicMock
    ) -> None:
        """Test that empty AWS_LAMBDA_FUNCTION_NAME still triggers production mode.

        This tests the fix for M1: Environment variable detection edge case.
        Even if the env var is set to empty string, it should be treated as production.
        """
        configure_application_logging()

        # With the fix (is not None), empty string should trigger production
        mock_production.assert_called_once_with(log_level=logging.INFO)
        mock_structlog.assert_not_called()

    @patch.dict(os.environ, {}, clear=True)
    @patch("the_alchemiser.shared.logging.config.configure_structlog")
    def test_development_uses_console_format(self, mock_structlog: MagicMock) -> None:
        """Test that development mode uses human-readable console format."""
        configure_application_logging()

        call_kwargs = mock_structlog.call_args.kwargs
        assert call_kwargs["structured_format"] is False

    @patch.dict(os.environ, {}, clear=True)
    @patch("the_alchemiser.shared.logging.config.configure_structlog")
    def test_development_uses_different_console_and_file_levels(
        self, mock_structlog: MagicMock
    ) -> None:
        """Test that development mode uses INFO for console, DEBUG for file."""
        configure_application_logging()

        call_kwargs = mock_structlog.call_args.kwargs
        assert call_kwargs["console_level"] == logging.INFO
        assert call_kwargs["file_level"] == logging.DEBUG

    @patch.dict(os.environ, {"AWS_LAMBDA_FUNCTION_NAME": "test-function"})
    @patch("the_alchemiser.shared.logging.config.configure_production_logging")
    def test_is_idempotent(self, mock_production: MagicMock) -> None:
        """Test that multiple calls to configure_application_logging are safe."""
        configure_application_logging()
        configure_application_logging()

        # Should be called twice
        assert mock_production.call_count == 2


class TestEdgeCases:
    """Test suite for edge cases and error conditions."""

    @patch("the_alchemiser.shared.logging.config.configure_structlog")
    def test_configure_test_logging_with_zero_log_level(self, mock_configure: MagicMock) -> None:
        """Test that log level 0 (NOTSET) is accepted."""
        configure_test_logging(log_level=logging.NOTSET)

        call_kwargs = mock_configure.call_args.kwargs
        assert call_kwargs["console_level"] == logging.NOTSET

    @patch("the_alchemiser.shared.logging.config.configure_structlog")
    def test_configure_test_logging_with_critical_level(self, mock_configure: MagicMock) -> None:
        """Test that CRITICAL log level is accepted."""
        configure_test_logging(log_level=logging.CRITICAL)

        call_kwargs = mock_configure.call_args.kwargs
        assert call_kwargs["console_level"] == logging.CRITICAL

    @patch("the_alchemiser.shared.logging.config.configure_structlog")
    def test_configure_production_logging_with_none_console_level(
        self, mock_configure: MagicMock
    ) -> None:
        """Test that None console_level defaults to log_level."""
        configure_production_logging(log_level=logging.WARNING, console_level=None)

        call_kwargs = mock_configure.call_args.kwargs
        assert call_kwargs["console_level"] == logging.WARNING

    @patch.dict(os.environ, {}, clear=True)
    @patch("the_alchemiser.shared.logging.config.configure_structlog")
    def test_configure_production_logging_without_env_var(self, mock_configure: MagicMock) -> None:
        """Test that production logging works without LOG_FILE_PATH env var."""
        configure_production_logging()

        call_kwargs = mock_configure.call_args.kwargs
        assert call_kwargs["file_path"] is None


class TestParameterNaming:
    """Test suite to verify parameter naming consistency."""

    def test_production_logging_parameter_name(self) -> None:
        """Test that configure_production_logging uses log_file_path parameter name."""
        import inspect

        sig = inspect.signature(configure_production_logging)
        # Verify the parameter is named log_file_path (not log_file)
        assert "log_file_path" in sig.parameters
        assert "log_file" not in sig.parameters
