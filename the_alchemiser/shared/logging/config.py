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
    """Configure structlog for Lambda environments (dev and prod).

    Dev Lambda uses human-readable format for easier debugging.
    Prod Lambda uses JSON format for CloudWatch Insights queries and log aggregation.

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
        APP__STAGE: Deployment stage ("dev" or "prod"). Determines log format.

    """
    # Read log level from environment variable if not explicitly provided
    # Support both LOG_LEVEL (standard) and LOGGING__LEVEL (SAM template convention)
    if log_level is None:
        level_name = os.getenv("LOG_LEVEL") or os.getenv("LOGGING__LEVEL") or "INFO"
        log_level = getattr(logging, level_name.upper(), logging.INFO)

    effective_console_level = console_level if console_level is not None else log_level
    effective_log_file = log_file_path or os.getenv("LOG_FILE_PATH")

    # Detect production stage (uses JSON) vs dev stage (uses human-readable)
    stage = os.getenv("APP__STAGE", "").lower()
    is_prod_stage = stage in ("prod", "production")

    configure_structlog(
        console_level=effective_console_level,
        file_level=log_level,
        file_path=effective_log_file,
        use_colors=False,  # No colors in CloudWatch (ANSI codes don't render)
        include_timestamp=False,  # CloudWatch adds its own timestamp
        use_json=is_prod_stage,  # JSON for prod Lambda, human-readable for dev Lambda
    )


def configure_application_logging() -> None:
    """Configure application logging with structlog.

    Automatically selects appropriate configuration based on environment:
    - **Prod Lambda** (APP__STAGE=prod): JSON format for CloudWatch Insights
    - **Dev Lambda** (APP__STAGE=dev): Human-readable for easier debugging
    - **Local Development**: Human-readable with colors and file logging

    Environment Detection:
        - **Prod Lambda** (AWS_LAMBDA_FUNCTION_NAME set, APP__STAGE=prod):
          - JSON format (queryable in CloudWatch Insights)
          - No ANSI colors
          - No timestamp (CloudWatch adds its own)
          - Log level from LOG_LEVEL env var (default: INFO)

        - **Dev Lambda** (AWS_LAMBDA_FUNCTION_NAME set, APP__STAGE=dev):
          - Human-readable format (easier debugging)
          - No ANSI colors (CloudWatch doesn't render them)
          - No timestamp (CloudWatch adds its own)
          - Log level from LOG_LEVEL env var (default: INFO)

        - **Local Development** (AWS_LAMBDA_FUNCTION_NAME not set):
          - Human-readable format
          - Full ANSI colors for beautiful terminal output
          - Timestamps included
          - File logging to logs/trade_run.log

    Example:
        >>> # In prod Lambda
        >>> configure_application_logging()  # JSON output for CloudWatch Insights
        >>>
        >>> # In dev Lambda
        >>> configure_application_logging()  # Human-readable output for debugging
        >>>
        >>> # In local development
        >>> configure_application_logging()  # Colored output, file logging

    Note:
        In local development, file logging to logs/trade_run.log may fail silently if
        the directory doesn't exist. The underlying structlog_config module catches
        OSError and falls back to console-only logging.

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
