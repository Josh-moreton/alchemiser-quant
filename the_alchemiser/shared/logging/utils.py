"""Business Unit: shared | Status: current.

Utility functions for logging system.

This module provides small helper functions used across the logging infrastructure,
including log level parsing, environment detection, and directory management.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

# Constants
_S3_PROTOCOL_PREFIX = "s3://"

# S3 logging configuration constants
# Set of string values that, when present in configuration, indicate S3 logging should be enabled.
_S3_ENABLED_VALUES = frozenset(["1", "true", "yes", "on"])
# Set of environment variable names that, if present, indicate the code is running in an AWS Lambda environment.
_LAMBDA_ENV_VARS = frozenset(["AWS_EXECUTION_ENV", "AWS_LAMBDA_RUNTIME_API", "LAMBDA_RUNTIME_DIR"])


def _parse_log_level(level_str: str | None) -> int | None:
    """Convert a string log level to its numeric value."""
    if not level_str:
        return None

    lvl_upper = level_str.strip().upper()
    if not lvl_upper:
        return None

    if lvl_upper.isdigit():
        try:
            return int(lvl_upper)
        except ValueError:
            return None

    named_level = getattr(logging, lvl_upper, None)
    return named_level if isinstance(named_level, int) else None


def _is_lambda_environment() -> bool:
    """Check if running in AWS Lambda environment."""
    return any(os.environ.get(var) for var in _LAMBDA_ENV_VARS)


def _is_s3_logging_enabled() -> bool:
    """Check if S3 logging is explicitly enabled."""
    return os.environ.get("ENABLE_S3_LOGGING", "").lower() in _S3_ENABLED_VALUES


def _should_suppress_s3_logging(log_file: str | None) -> bool:
    """Determine if S3 logging should be suppressed in Lambda environment."""
    return (
        _is_lambda_environment()
        and log_file is not None
        and log_file.startswith(_S3_PROTOCOL_PREFIX)
        and not _is_s3_logging_enabled()
    )


def _create_directory_if_needed(file_path: str) -> None:
    """Create directory for log file if it doesn't exist."""
    log_path = Path(file_path)
    # Only create if parent directory is specified (not just the current directory)
    if str(log_path.parent) != ".":
        log_path.parent.mkdir(parents=True, exist_ok=True)


def _suppress_third_party_loggers() -> None:
    """Suppress noisy third-party loggers to WARNING level."""
    noisy_loggers = [
        "botocore",
        "urllib3",
        "alpaca",
        "boto3",
        "s3transfer",
        "websocket",
        "matplotlib",
        "requests",
        "urllib3.connectionpool",
        "werkzeug",
        "asyncio",
    ]
    for logger_name in noisy_loggers:
        logging.getLogger(logger_name).setLevel(logging.WARNING)


def _is_lambda_production_environment() -> bool:
    """Check if running in Lambda production environment."""
    return any(
        [
            os.getenv("AWS_EXECUTION_ENV"),
            os.getenv("AWS_LAMBDA_RUNTIME_API"),
            os.getenv("LAMBDA_RUNTIME_DIR"),
        ]
    )
