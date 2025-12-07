"""Tests for shared.logging.config module.

Tests for the simplified Lambda-first logging configuration.
All logs go to CloudWatch; filtering happens at query time.
"""

from __future__ import annotations

import logging
from unittest.mock import MagicMock, patch

from the_alchemiser.shared.logging.config import (
    configure_application_logging,
    configure_test_logging,
)


class TestConfigureTestLogging:
    """Test suite for configure_test_logging function."""

    @patch("the_alchemiser.shared.logging.config.configure_structlog_test")
    def test_configures_with_default_warning_level(self, mock_configure: MagicMock) -> None:
        """Test that configure_test_logging uses WARNING level by default."""
        configure_test_logging()

        mock_configure.assert_called_once_with(log_level=logging.WARNING)

    @patch("the_alchemiser.shared.logging.config.configure_structlog_test")
    def test_configures_with_custom_log_level(self, mock_configure: MagicMock) -> None:
        """Test that configure_test_logging accepts custom log level."""
        configure_test_logging(log_level=logging.DEBUG)

        mock_configure.assert_called_once_with(log_level=logging.DEBUG)

    @patch("the_alchemiser.shared.logging.config.configure_structlog_test")
    def test_is_idempotent(self, mock_configure: MagicMock) -> None:
        """Test that multiple calls to configure_test_logging are safe."""
        configure_test_logging(log_level=logging.INFO)
        configure_test_logging(log_level=logging.DEBUG)

        assert mock_configure.call_count == 2


class TestConfigureApplicationLogging:
    """Test suite for configure_application_logging function."""

    @patch("the_alchemiser.shared.logging.config.configure_structlog_lambda")
    def test_configures_lambda_logging(self, mock_configure: MagicMock) -> None:
        """Test that configure_application_logging calls configure_structlog_lambda."""
        configure_application_logging()

        mock_configure.assert_called_once_with()

    @patch("the_alchemiser.shared.logging.config.configure_structlog_lambda")
    def test_is_idempotent(self, mock_configure: MagicMock) -> None:
        """Test that multiple calls to configure_application_logging are safe."""
        configure_application_logging()
        configure_application_logging()

        assert mock_configure.call_count == 2


class TestEdgeCases:
    """Test suite for edge cases."""

    @patch("the_alchemiser.shared.logging.config.configure_structlog_test")
    def test_configure_test_logging_with_notset_level(self, mock_configure: MagicMock) -> None:
        """Test that log level 0 (NOTSET) is accepted."""
        configure_test_logging(log_level=logging.NOTSET)

        mock_configure.assert_called_once_with(log_level=logging.NOTSET)

    @patch("the_alchemiser.shared.logging.config.configure_structlog_test")
    def test_configure_test_logging_with_critical_level(self, mock_configure: MagicMock) -> None:
        """Test that CRITICAL log level is accepted."""
        configure_test_logging(log_level=logging.CRITICAL)

        mock_configure.assert_called_once_with(log_level=logging.CRITICAL)
