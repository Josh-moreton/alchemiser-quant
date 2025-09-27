#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Account Value Logger Factory for persistence backend selection.

This module provides factory functions to create appropriate account value logger
instances based on environment configuration.
"""

from __future__ import annotations

import logging
import os

from .base_account_value_logger import AccountValueLoggerProtocol
from .local_account_value_logger import LocalAccountValueLogger

logger = logging.getLogger(__name__)


def create_account_value_logger() -> AccountValueLoggerProtocol:
    """Create appropriate account value logger based on environment.

    For now, only supports local file-based logging. Future versions could
    add S3 or database backend support similar to the trade ledger.

    Returns:
        Account value logger instance

    Environment Variables:
        ACCOUNT_VALUE_LOGGER_BASE_PATH: Override base path for local storage

    """
    logger.info("Creating local account value logger")
    return LocalAccountValueLogger()


def create_local_account_value_logger(base_path: str | None = None) -> LocalAccountValueLogger:
    """Create local file-based account value logger.

    Args:
        base_path: Optional override for base storage path

    Returns:
        Local account value logger instance

    """
    return LocalAccountValueLogger(base_path=base_path)


def is_account_value_logging_enabled() -> bool:
    """Check if account value logging is enabled.

    Returns:
        True if account value logging is enabled via environment variable

    """
    enabled = os.getenv("ENABLE_ACCOUNT_VALUE_LOGGING", "false").lower()
    return enabled in ("true", "1", "yes", "on")
