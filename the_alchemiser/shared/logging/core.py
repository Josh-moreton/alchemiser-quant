"""Business Unit: shared | Status: current.

Core logging infrastructure and setup.

This module provides the core logging setup functions and logger retrieval
for the centralized logging system.
"""

from __future__ import annotations

import logging

from .formatters import _create_formatter
from .handlers import (
    _create_console_handler,
    _create_file_handler_if_needed,
    _should_add_console_handler,
)
from .utils import _should_suppress_s3_logging, _suppress_third_party_loggers


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with proper configuration.

    Retrieves a logger from Python's logging system that will use the centralized
    configuration established by setup_logging(). The logger will inherit all
    formatting, levels, and handlers configured globally.

    Logger retrieval behavior:
    - Uses the standard logging hierarchy (dotted names create parent-child relationships)
    - Inherits root logger configuration (handlers, formatters, levels)
    - Supports both structured (JSON) and standard text formatting
    - Automatically includes context variables (request_id, error_id) when present

    Args:
        name: Logger name, typically __name__ for module-level logging.
              Creates hierarchical loggers (e.g., 'the_alchemiser.strategy_v2.core')

    Returns:
        Configured logger instance that uses centralized handlers and formatting.
        Output will go to console and/or file based on setup_logging() configuration.

    """
    return logging.getLogger(name)


def log_with_context(logger: logging.Logger, level: int, message: str, **context: object) -> None:
    """Log a message with additional context fields.

    Args:
        logger: Logger instance
        level: Logging level (e.g., logging.INFO)
        message: Log message
        **context: Additional context fields to include

    """
    extra: dict[str, object] = {"extra_fields": context}
    logger.log(level, message, extra=extra)


def setup_logging(
    log_level: int = logging.INFO,
    log_file: str | None = None,
    console_level: int | None = None,
    *,
    suppress_third_party: bool = True,
    structured_format: bool = False,
    enable_file_rotation: bool = False,
    max_file_size_mb: int = 100,
    respect_existing_handlers: bool = False,
) -> None:
    """Set up centralized logging for the project.

    Configures the root Python logger with consistent formatting, handlers, and levels
    across the entire application. This function should be called once at startup
    to establish the logging infrastructure.

    Logging Setup Details:

    Formats:
    - Standard format: "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
    - Structured format: JSON with timestamp, level, logger, message, module, function, line
    - All messages prefixed with "[ALCHEMISER]" and include context IDs when available

    Levels:
    - Root logger set to DEBUG to capture all messages
    - Individual handlers filter by their specific levels
    - Supports different levels for console vs file output
    - Third-party loggers suppressed to WARNING to reduce noise

    Handlers:
    - Console handler: outputs to stdout with configurable level
    - File handler: optional local file or S3 URI support (with fallback)
    - File rotation: optional RotatingFileHandler with size-based rotation
    - S3 logging: converts S3 URIs to local fallback unless explicitly enabled

    Special Features:
    - Context variable support for request_id and error_id tracking
    - AWS Lambda environment detection for production hygiene
    - AlchemiserLoggerAdapter integration for consistent message formatting
    - Automatic directory creation for log file paths

    Args:
        log_level: Default logging level for file output (DEBUG=10, INFO=20, WARNING=30, ERROR=40)
        log_file: Optional file path or S3 URI for file logging. If S3 URI provided in Lambda
                 without ENABLE_S3_LOGGING=true, falls back to console-only logging
        console_level: Optional different level for console output (defaults to log_level).
                      Useful for reducing console noise while maintaining detailed file logs
        suppress_third_party: Whether to suppress noisy third-party loggers (botocore, urllib3,
                             alpaca, boto3, etc.) to WARNING level
        structured_format: Whether to use JSON structured logging format (recommended for production)
                          vs human-readable text format (recommended for development)
        enable_file_rotation: Whether to enable file rotation for local files using RotatingFileHandler.
                             Creates backups when max_file_size_mb is exceeded
        max_file_size_mb: Maximum file size in MB before rotation triggers (default 100MB)
        respect_existing_handlers: If True, don't clear existing handlers (useful for CLI tools
                                  that may have pre-configured logging)

    """
    root_logger = logging.getLogger()

    # Handle S3 logging suppression in Lambda environments
    if _should_suppress_s3_logging(log_file):
        logger = get_logger(__name__)
        logger.warning(
            "S3 logging requested in Lambda environment but ENABLE_S3_LOGGING not set. "
            "Defaulting to CloudWatch-only logging for production hygiene."
        )
        log_file = None

    # Only clear handlers if we're not respecting existing ones
    if not respect_existing_handlers and root_logger.hasHandlers():
        root_logger.handlers.clear()

    formatter = _create_formatter(structured_format=structured_format)
    handlers: list[logging.Handler] = []

    # Add console handler if needed
    if _should_add_console_handler(
        respect_existing_handlers=respect_existing_handlers, root_logger=root_logger
    ):
        console_handler = _create_console_handler(formatter, console_level, log_level)
        handlers.append(console_handler)

    # Add file handler if specified
    file_handler = _create_file_handler_if_needed(
        log_file,
        formatter,
        log_level,
        enable_file_rotation=enable_file_rotation,
        max_file_size_mb=max_file_size_mb,
    )
    if file_handler:
        handlers.append(file_handler)

    # Configure root logger
    root_logger.setLevel(logging.DEBUG)  # Capture everything, filter at handler level
    for handler in handlers:
        root_logger.addHandler(handler)

    if suppress_third_party:
        _suppress_third_party_loggers()

    # Log initialization message
    logger = get_logger(__name__)
    logger.info(
        f"Logging initialized. Level: {logging.getLevelName(log_level)} | "
        f"Format: {'structured' if structured_format else 'standard'} | "
        f"File: {log_file or 'console only'}"
    )


def get_service_logger(service_name: str) -> logging.Logger:
    """Get a properly configured logger for a service.

    This replaces create_service_logger by using the centrally configured
    logging system instead of creating individual handlers.

    Args:
        service_name: Name of the service

    Returns:
        Logger instance using central configuration

    """
    return logging.getLogger(f"the_alchemiser.services.{service_name}")


def configure_quiet_logging() -> dict[str, int]:
    """Configure quiet logging to reduce CLI noise.

    Returns:
        Dict mapping module names to original log levels for restoration

    """
    # Store original levels for restoration
    original_levels = {}

    # Modules to quiet down (these tend to be noisy during execution)
    noisy_modules = [
        "the_alchemiser.execution_v2",
        "the_alchemiser.portfolio_v2",
        "the_alchemiser.strategy_v2",
        "the_alchemiser.orchestration",
        "the_alchemiser.orchestration.event_driven_orchestrator",
        "alpaca",
        "urllib3",
        "requests",
    ]

    for module_name in noisy_modules:
        logger = logging.getLogger(module_name)
        original_levels[module_name] = logger.level
        logger.setLevel(logging.WARNING)

    return original_levels


def restore_logging(original_levels: dict[str, int]) -> None:
    """Restore original logging levels.

    Args:
        original_levels: Dict mapping module names to original log levels

    """
    for module_name, level in original_levels.items():
        logger = logging.getLogger(module_name)
        logger.setLevel(level)
