"""Business Unit: shared | Status: current.

Configuration management for structlog-based logging system.

This module provides application-level logging configuration functions for human-readable
logging across environments. All configurations now use structlog by default.
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
    configure_structlog(console_level=log_level, file_level=log_level)


def configure_application_logging(
    *,
    log_level: int = logging.INFO,
    console_level: int | None = None,
    log_file_path: str | None = None,
) -> None:
    """Configure application logging with structlog (human-readable everywhere).

    Environment Detection:
        - Lambda (AWS_LAMBDA_FUNCTION_NAME set): console only unless LOG_FILE_PATH provided
        - Non-Lambda: console plus local file logging (logs/trade_run.log) by default

    Args:
        log_level: Base log level for handlers (default: INFO)
        console_level: Optional console level override (defaults to log_level)
        log_file_path: Optional explicit file path. If not provided, falls back to
            LOG_FILE_PATH env var, then to a development default when not in Lambda.

    """
    is_lambda = os.getenv("AWS_LAMBDA_FUNCTION_NAME") is not None

    effective_console_level = console_level if console_level is not None else log_level

    # Prefer explicit parameter, then env var. Only default to local file when not in Lambda.
    env_log_file = os.getenv("LOG_FILE_PATH")
    default_dev_file = None if is_lambda else "logs/trade_run.log"
    effective_log_file = log_file_path or env_log_file or default_dev_file

    effective_file_level = log_level
    if not is_lambda and effective_log_file:
        # In dev, keep detailed file logging for debugging
        effective_file_level = logging.DEBUG

    configure_structlog(
        console_level=effective_console_level,
        file_level=effective_file_level,
        file_path=effective_log_file,
    )
