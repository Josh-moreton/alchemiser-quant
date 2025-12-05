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
        console_level=log_level,
        file_level=log_level,
        use_colors=True,
        include_timestamp=True,
    )


def configure_production_logging(
    log_level: int | None = None,
    log_file_path: str | None = None,
    *,
    console_level: int | None = None,
) -> None:
    """Configure structlog for production with beautiful human-readable output.

    Args:
        log_level: Base log level for handlers. If None, reads from LOG_LEVEL env var
                   (default: INFO if not set).
        log_file_path: Optional path/URI for file logging. Falls back to LOG_FILE_PATH env var.
        console_level: Override for console handler level. Defaults to log_level if not provided.

    Example:
        >>> configure_production_logging()  # Uses LOG_LEVEL env var or INFO
        >>> configure_production_logging(log_level=logging.DEBUG)  # Force DEBUG
        >>> configure_production_logging(log_file_path="/tmp/app.log")

    Note:
        File logging may fail silently if the log file path is not writable.
        In AWS Lambda environments, only /tmp is writable. The underlying
        structlog_config module catches OSError and falls back to console-only logging.

    Environment Variables:
        LOG_LEVEL: Set log level (DEBUG, INFO, WARNING, ERROR, CRITICAL). Default: INFO
        LOGGING__LEVEL: Alternative env var (used by SAM template). Falls back to LOG_LEVEL.
        LOG_FILE_PATH: Optional file path for logging output.

    """
    # Read log level from environment variable if not explicitly provided
    # Support both LOG_LEVEL (standard) and LOGGING__LEVEL (SAM template convention)
    if log_level is None:
        level_name = os.getenv("LOG_LEVEL") or os.getenv("LOGGING__LEVEL") or "INFO"
        log_level = getattr(logging, level_name.upper(), logging.INFO)

    effective_console_level = console_level if console_level is not None else log_level
    effective_log_file = log_file_path or os.getenv("LOG_FILE_PATH")

    # Detect Lambda environment for CloudWatch-friendly output
    is_lambda = os.getenv("AWS_LAMBDA_FUNCTION_NAME") is not None

    configure_structlog(
        console_level=effective_console_level,
        file_level=log_level,
        file_path=effective_log_file,
        use_colors=not is_lambda,  # No colors in CloudWatch (ANSI codes don't render)
        include_timestamp=not is_lambda,  # CloudWatch adds its own timestamp
    )


def configure_application_logging() -> None:
    """Configure application logging with structlog.

    Automatically selects appropriate configuration based on environment.
    Both production and development use beautiful human-readable output with proper
    formatting for each environment.

    Environment Detection:
        - Production (Lambda): AWS_LAMBDA_FUNCTION_NAME env var is set
          - No ANSI colors (CloudWatch doesn't render them)
          - No timestamp (CloudWatch adds its own)
          - Log level from LOG_LEVEL env var (default: INFO)
        - Development: AWS_LAMBDA_FUNCTION_NAME is not set
          - Full ANSI colors for beautiful terminal output
          - Timestamps included
          - File logging to logs/trade_run.log

    Example:
        >>> # In Lambda (production)
        >>> configure_application_logging()  # Clean output for CloudWatch
        >>>
        >>> # In local development
        >>> configure_application_logging()  # Colored output, file logging

    Note:
        In development, file logging to logs/trade_run.log may fail silently if the
        directory doesn't exist. The underlying structlog_config module catches OSError
        and falls back to console-only logging.

    """
    # Determine if we're in production (Lambda environment)
    is_lambda = os.getenv("AWS_LAMBDA_FUNCTION_NAME") is not None

    if is_lambda:
        # Production: CloudWatch-friendly output (no colors, no timestamp)
        configure_production_logging()  # Uses LOG_LEVEL env var
    else:
        # Development: Beautiful colored console output + file logging
        configure_structlog(
            console_level=logging.INFO,
            file_level=logging.DEBUG,
            file_path="logs/trade_run.log",
            use_colors=True,
            include_timestamp=True,
        )
