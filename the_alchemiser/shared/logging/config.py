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
    """Configure structlog for test environments with human-readable output."""
    configure_structlog(
        structured_format=False,  # Console format for readability in tests
        console_level=log_level,
        file_level=log_level,
    )


def configure_production_logging(
    log_level: int = logging.INFO,
    log_file: str | None = None,
    *,
    console_level: int | None = None,
) -> None:
    """Configure structlog for production environment with JSON output.

    Args:
        log_level: Base log level for handlers.
        log_file: Optional path/URI for file logging (kept for API compatibility).
        console_level: Override for console handler level (kept for API compatibility).

    """
    effective_console_level = console_level if console_level is not None else log_level
    # In Lambda, avoid file logging by default. Allow opt-in via LOG_FILE_PATH env var
    effective_log_file = log_file or os.getenv("LOG_FILE_PATH")
    configure_structlog(
        structured_format=True,  # JSON format for production
        console_level=effective_console_level,
        file_level=log_level,
        file_path=effective_log_file,
    )


def configure_application_logging() -> None:
    """Configure application logging with structlog.

    Automatically selects appropriate configuration based on environment.
    Production uses JSON format, development uses console format with clean terminal output.
    """
    # Determine if we're in production (Lambda environment)
    is_production = bool(os.getenv("AWS_LAMBDA_FUNCTION_NAME"))

    if is_production:
        configure_production_logging(log_level=logging.INFO)
    else:
        # Development environment - clean console, detailed file
        # Default to local file logging for development only
        configure_structlog(
            structured_format=False,  # Human-readable for development
            console_level=logging.INFO,  # Clean console (no debug spam)
            file_level=logging.DEBUG,  # File captures everything for debugging
            file_path="logs/trade_run.log",
        )
