"""Business Unit: shared | Status: current.

Configuration management for structlog-based logging system.

This module provides application-level logging configuration functions for different
environments including production, test, and development configurations.
All configurations now use structlog by default.
"""

from __future__ import annotations

import logging
import os

from .structlog_config import configure_structlog


def configure_test_logging(log_level: int = logging.WARNING) -> None:
    """Configure structlog for test environments with human-readable output.

    Args:
        log_level: Log level for both console and file output (default: WARNING).

    Example:
        >>> configure_test_logging(log_level=logging.DEBUG)

    """
    configure_structlog(
        structured_format=False,  # Console format for readability in tests
        console_level=log_level,
        file_level=log_level,
    )


def configure_production_logging(
    log_level: int = logging.INFO,
    log_file_path: str | None = None,
    *,
    console_level: int | None = None,
) -> None:
    """Configure structlog for production environment with JSON output.

    Args:
        log_level: Base log level for handlers (default: INFO).
        log_file_path: Optional path/URI for file logging. Falls back to LOG_FILE_PATH env var.
        console_level: Override for console handler level. Defaults to log_level if not provided.

    Example:
        >>> configure_production_logging(log_level=logging.INFO)
        >>> configure_production_logging(log_file_path="/tmp/app.log", console_level=logging.WARNING)

    Note:
        File logging may fail silently if the log file path is not writable.
        In AWS Lambda environments, only /tmp is writable. The underlying
        structlog_config module catches OSError and falls back to console-only logging.

    """
    effective_console_level = console_level if console_level is not None else log_level
    # In Lambda, avoid file logging by default. Allow opt-in via LOG_FILE_PATH env var
    effective_log_file = log_file_path or os.getenv("LOG_FILE_PATH")
    configure_structlog(
        structured_format=False,  # Human-readable for CloudWatch console
        console_level=effective_console_level,
        file_level=log_level,
        file_path=effective_log_file,
    )


def _get_log_level_from_env() -> int:
    """Get log level from LOGGING__LEVEL environment variable.

    Supports standard Python logging level names (case-insensitive):
    DEBUG, INFO, WARNING, ERROR, CRITICAL

    Returns:
        int: Logging level constant, defaults to INFO if not set or invalid.

    """
    level_name = os.getenv("LOGGING__LEVEL", "INFO").upper()
    level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "WARN": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }
    return level_map.get(level_name, logging.INFO)


def configure_application_logging() -> None:
    """Configure application logging with structlog.

    Automatically selects appropriate configuration based on environment.
    Production uses JSON format, development uses console format with clean terminal output.

    Environment Detection:
        - Production: AWS_LAMBDA_FUNCTION_NAME environment variable is set (not None)
        - Development: AWS_LAMBDA_FUNCTION_NAME is not set

    Log Level:
        Controlled by LOGGING__LEVEL environment variable (default: INFO).
        Supports: DEBUG, INFO, WARNING, ERROR, CRITICAL

    Example:
        >>> # In Lambda (production)
        >>> configure_application_logging()  # Uses JSON format, console-only
        >>>
        >>> # In local development
        >>> configure_application_logging()  # Uses console format, logs to logs/trade_run.log

    Note:
        In development, file logging to logs/trade_run.log may fail silently if the
        directory doesn't exist. The underlying structlog_config module catches OSError
        and falls back to console-only logging.

    """
    # Determine if we're in production (Lambda environment)
    # Use explicit None check to handle empty string case correctly
    is_production = os.getenv("AWS_LAMBDA_FUNCTION_NAME") is not None

    # Get log level from environment (respects LOGGING__LEVEL from template.yaml)
    log_level = _get_log_level_from_env()

    if is_production:
        configure_production_logging(log_level=log_level)
    else:
        # Development environment - clean console, detailed file
        # Default to local file logging for development only
        configure_structlog(
            structured_format=False,  # Human-readable for development
            console_level=log_level,  # Respect env var for console
            file_level=logging.DEBUG,  # File captures everything for debugging
            file_path="logs/trade_run.log",
        )
