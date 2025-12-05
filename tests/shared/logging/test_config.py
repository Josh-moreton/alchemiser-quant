"""Tests for shared.logging.config module.

This module tests the application-level logging configuration functions
for different environments (production, test, development).
"""

from __future__ import annotations

import logging
import os
from unittest.mock import MagicMock, patch

from the_alchemiser.shared.logging.config import configure_application_logging, configure_test_logging


class TestConfigureTestLogging:
    """Test suite for configure_test_logging function."""

    @patch("the_alchemiser.shared.logging.config.configure_structlog")
    def test_configures_with_default_warning_level(self, mock_configure: MagicMock) -> None:
        """Test that configure_test_logging uses WARNING level by default."""
        configure_test_logging()

        mock_configure.assert_called_once_with(
            console_level=logging.WARNING,
            file_level=logging.WARNING,
        )

    @patch("the_alchemiser.shared.logging.config.configure_structlog")
    def test_configures_with_custom_log_level(self, mock_configure: MagicMock) -> None:
        """Test that configure_test_logging accepts custom log level."""
        configure_test_logging(log_level=logging.DEBUG)

        mock_configure.assert_called_once_with(
            console_level=logging.DEBUG,
            file_level=logging.DEBUG,
        )

    @patch("the_alchemiser.shared.logging.config.configure_structlog")
    def test_uses_console_format_not_json(self, mock_configure: MagicMock) -> None:
        """Test that configure_test_logging uses console format for readability."""
        configure_test_logging()

        call_kwargs = mock_configure.call_args.kwargs
        assert call_kwargs["console_level"] == logging.WARNING

    @patch("the_alchemiser.shared.logging.config.configure_structlog")
    def test_is_idempotent(self, mock_configure: MagicMock) -> None:
        """Test that multiple calls to configure_test_logging are safe."""
        configure_test_logging(log_level=logging.INFO)
        configure_test_logging(log_level=logging.DEBUG)

        # Should be called twice with different levels
        assert mock_configure.call_count == 2

class TestConfigureApplicationLogging:
    """Test suite for configure_application_logging function."""
    @patch.dict(os.environ, {"AWS_LAMBDA_FUNCTION_NAME": "my-lambda-function"}, clear=True)
    @patch("the_alchemiser.shared.logging.config.configure_structlog")
    def test_lambda_environment_uses_console_only(self, mock_structlog: MagicMock) -> None:
        """Lambda environment should configure console handler only unless file path provided."""
        configure_application_logging()

        mock_structlog.assert_called_once_with(
            console_level=logging.INFO,
            file_level=logging.INFO,
            file_path=None,
        )

    @patch.dict(
        os.environ,
        {"AWS_LAMBDA_FUNCTION_NAME": "my-lambda-function", "LOG_FILE_PATH": "/tmp/lambda.log"},
        clear=True,
    )
    @patch("the_alchemiser.shared.logging.config.configure_structlog")
    def test_lambda_environment_respects_log_file_env(self, mock_structlog: MagicMock) -> None:
        """Lambda environment honors LOG_FILE_PATH when provided."""
        configure_application_logging()

        mock_structlog.assert_called_once_with(
            console_level=logging.INFO,
            file_level=logging.INFO,
            file_path="/tmp/lambda.log",
        )

    @patch.dict(os.environ, {}, clear=True)
    @patch("the_alchemiser.shared.logging.config.configure_structlog")
    def test_development_uses_console_and_file_logging(self, mock_structlog: MagicMock) -> None:
        """Non-Lambda environments use console INFO and file DEBUG to a local log file."""
        configure_application_logging()

        mock_structlog.assert_called_once_with(
            console_level=logging.INFO,
            file_level=logging.DEBUG,
            file_path="logs/trade_run.log",
        )

    @patch.dict(os.environ, {}, clear=True)
    @patch("the_alchemiser.shared.logging.config.configure_structlog")
    def test_console_level_override_applies(self, mock_structlog: MagicMock) -> None:
        """Console level can override base log level while file stays at DEBUG in development."""
        configure_application_logging(log_level=logging.WARNING, console_level=logging.ERROR)

        call_kwargs = mock_structlog.call_args.kwargs
        assert call_kwargs["console_level"] == logging.ERROR
        assert call_kwargs["file_level"] == logging.DEBUG
        assert call_kwargs["file_path"] == "logs/trade_run.log"

    @patch.dict(os.environ, {}, clear=True)
    @patch("the_alchemiser.shared.logging.config.configure_structlog")
    def test_is_idempotent(self, mock_structlog: MagicMock) -> None:
        """Multiple calls should remain safe."""
        configure_application_logging()
        configure_application_logging()

        assert mock_structlog.call_count == 2


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
