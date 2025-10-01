"""Business Unit: shared | Status: current.

Handler creation and management for logging system.

This module provides functions for creating and configuring various logging handlers
including console handlers, file handlers, and S3 fallback handlers.
"""

from __future__ import annotations

import logging
import sys

from .utils import _S3_PROTOCOL_PREFIX, _create_directory_if_needed


def _create_console_handler(
    formatter: logging.Formatter, console_level: int | None, log_level: int
) -> logging.Handler:
    """Create console handler with appropriate level."""
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(console_level if console_level is not None else log_level)
    return console_handler


def _create_s3_fallback_handler(
    log_file: str, formatter: logging.Formatter, log_level: int
) -> logging.Handler:
    """Create fallback file handler for S3 logging."""
    # Convert S3 path to local file path
    fallback_file = log_file.replace(_S3_PROTOCOL_PREFIX, "").replace("/", "_")
    _create_directory_if_needed(fallback_file)

    handler = logging.FileHandler(fallback_file)
    handler.setFormatter(formatter)
    handler.setLevel(log_level)
    return handler


def _create_local_file_handler(
    log_file: str,
    formatter: logging.Formatter,
    log_level: int,
    *,
    enable_file_rotation: bool,
    max_file_size_mb: int,
) -> logging.Handler:
    """Create local file handler with optional rotation."""
    _create_directory_if_needed(log_file)

    handler: logging.Handler
    if enable_file_rotation:
        from logging.handlers import RotatingFileHandler

        max_bytes = max_file_size_mb * 1024 * 1024  # Convert MB to bytes
        handler = RotatingFileHandler(
            log_file, mode="a", maxBytes=max_bytes, backupCount=5, encoding="utf-8"
        )
    else:
        handler = logging.FileHandler(log_file, mode="a", encoding="utf-8")

    handler.setFormatter(formatter)
    handler.setLevel(log_level)
    return handler


def _create_file_handler_if_needed(
    log_file: str | None,
    formatter: logging.Formatter,
    log_level: int,
    *,
    enable_file_rotation: bool,
    max_file_size_mb: int,
) -> logging.Handler | None:
    """Create file handler if log_file is specified."""
    if not log_file:
        return None

    if log_file.startswith(_S3_PROTOCOL_PREFIX):
        logging.warning("S3 logging not available - using local file fallback")
        return _create_s3_fallback_handler(log_file, formatter, log_level)

    return _create_local_file_handler(
        log_file,
        formatter,
        log_level,
        enable_file_rotation=enable_file_rotation,
        max_file_size_mb=max_file_size_mb,
    )


def _should_add_console_handler(
    *, respect_existing_handlers: bool, root_logger: logging.Logger
) -> bool:
    """Determine if console handler should be added."""
    return not respect_existing_handlers or not root_logger.hasHandlers()
