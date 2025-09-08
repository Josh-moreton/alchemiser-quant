"""Business Unit: utilities; Status: current.

Logging helpers for consistent structured output.
"""

from __future__ import annotations

import json
import logging
import os
import sys
import uuid
from collections.abc import MutableMapping
from contextvars import ContextVar
from datetime import datetime
from typing import Any

from the_alchemiser.portfolio.utils.s3_utils import S3FileHandler

# Context variables for request tracking
request_id_context: ContextVar[str | None] = ContextVar("request_id", default=None)
error_id_context: ContextVar[str | None] = ContextVar("error_id", default=None)


class AlchemiserLoggerAdapter(logging.LoggerAdapter):
    """Custom logger adapter for the Alchemiser quantitative trading system."""

    def process(
        self, msg: Any, kwargs: MutableMapping[str, Any]
    ) -> tuple[str, MutableMapping[str, Any]]:
        """Prefix log messages with system identifier and add context IDs."""
        # Get context variables
        request_id = request_id_context.get()
        error_id = error_id_context.get()

        # Build context suffix
        context_parts = []
        if request_id:
            context_parts.append(f"req_id={request_id}")
        if error_id:
            context_parts.append(f"error_id={error_id}")

        context_suffix = f" [{', '.join(context_parts)}]" if context_parts else ""

        return f"[ALCHEMISER]{context_suffix} {msg}", kwargs


class StructuredFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Convert a log record into a JSON string."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add request_id and error_id from context vars if present
        request_id = request_id_context.get()
        if request_id:
            log_entry["request_id"] = request_id

        error_id = error_id_context.get()
        if error_id:
            log_entry["error_id"] = error_id

        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": self.formatException(record.exc_info),
            }

        # Add extra fields if present
        extra_fields = getattr(record, "extra_fields", None)
        if extra_fields:
            log_entry.update(extra_fields)

        return json.dumps(log_entry, default=str)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with proper configuration.

    Args:
        name: Logger name, typically __name__

    Returns:
        Configured logger instance

    """
    return logging.getLogger(name)


def set_request_id(request_id: str | None) -> None:
    """Set the request ID in the logging context.

    Args:
        request_id: The request ID to set, or None to clear

    """
    request_id_context.set(request_id)


def set_error_id(error_id: str | None) -> None:
    """Set the error ID in the logging context.

    Args:
        error_id: The error ID to set, or None to clear

    """
    error_id_context.set(error_id)


def get_request_id() -> str | None:
    """Get the current request ID from the logging context.

    Returns:
        The current request ID, or None if not set

    """
    return request_id_context.get()


def get_error_id() -> str | None:
    """Get the current error ID from the logging context.

    Returns:
        The current error ID, or None if not set

    """
    return error_id_context.get()


def generate_request_id() -> str:
    """Generate a new request ID.

    Returns:
        A unique request ID string

    """
    return str(uuid.uuid4())


def log_with_context(logger: logging.Logger, level: int, message: str, **context: Any) -> None:
    """Log a message with additional context fields.

    Args:
        logger: Logger instance
        level: Logging level (e.g., logging.INFO)
        message: Log message
        **context: Additional context fields to include

    """
    extra = {"extra_fields": context}
    logger.log(level, message, extra=extra)


def setup_logging(
    log_level: int = logging.INFO,
    log_file: str | None = None,
    console_level: int | None = None,
    suppress_third_party: bool = True,
    structured_format: bool = False,
    enable_file_rotation: bool = False,
    max_file_size_mb: int = 100,
    respect_existing_handlers: bool = False,
) -> None:
    """Set up centralized logging for the project.

    Args:
        log_level: Default logging level for file output
        log_file: Optional file path or S3 URI for file logging
        console_level: Optional different level for console output (defaults to log_level)
        suppress_third_party: Whether to suppress noisy third-party loggers
        structured_format: Whether to use JSON structured logging format
        enable_file_rotation: Whether to enable file rotation for local files
        max_file_size_mb: Maximum file size in MB before rotation
        respect_existing_handlers: If True, don't clear existing handlers (useful for CLI)

    """
    root_logger = logging.getLogger()

    # Production hygiene: Guard against S3 logging in Lambda environments
    is_lambda = any(
        [
            os.environ.get("AWS_EXECUTION_ENV"),
            os.environ.get("AWS_LAMBDA_RUNTIME_API"),
            os.environ.get("LAMBDA_RUNTIME_DIR"),
        ]
    )
    s3_logging_enabled = os.environ.get("ENABLE_S3_LOGGING", "").lower() in (
        "1",
        "true",
        "yes",
        "on",
    )

    if is_lambda and log_file and log_file.startswith("s3://") and not s3_logging_enabled:
        logger = get_logger(__name__)
        logger.warning(
            "S3 logging requested in Lambda environment but ENABLE_S3_LOGGING not set. "
            "Defaulting to CloudWatch-only logging for production hygiene."
        )
        log_file = None

    # Only clear handlers if we're not respecting existing ones
    if not respect_existing_handlers and root_logger.hasHandlers():
        root_logger.handlers.clear()

    # Choose formatter based on structured_format setting
    formatter: logging.Formatter
    if structured_format:
        formatter = StructuredFormatter()
    else:
        # Standard format for human-readable logs
        log_format = "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
        formatter = logging.Formatter(log_format)

    handlers: list[logging.Handler] = []

    # Console handler - only add if we don't have existing handlers or are not respecting them
    if not respect_existing_handlers or not root_logger.hasHandlers():
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(console_level if console_level is not None else log_level)
        handlers.append(console_handler)

    # File handler if specified
    if log_file:
        if log_file.startswith("s3://"):
            # Use S3 handler for S3 URIs
            s3_handler = S3FileHandler(log_file)
            s3_handler.setFormatter(formatter)
            s3_handler.setLevel(log_level)
            handlers.append(s3_handler)
        else:
            # Ensure directory exists for local files
            if os.path.dirname(log_file):
                os.makedirs(os.path.dirname(log_file), exist_ok=True)

            file_handler: logging.Handler
            if enable_file_rotation:
                from logging.handlers import RotatingFileHandler

                max_bytes = max_file_size_mb * 1024 * 1024  # Convert MB to bytes
                file_handler = RotatingFileHandler(
                    log_file, mode="a", maxBytes=max_bytes, backupCount=5, encoding="utf-8"
                )
            else:
                file_handler = logging.FileHandler(log_file, mode="a", encoding="utf-8")

            file_handler.setFormatter(formatter)
            file_handler.setLevel(log_level)
            handlers.append(file_handler)

    # Configure root logger
    root_logger.setLevel(logging.DEBUG)  # Capture everything, filter at handler level
    for handler in handlers:
        root_logger.addHandler(handler)

    # Suppress noisy third-party loggers
    if suppress_third_party:
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

    # Log initialization message
    logger = get_logger(__name__)
    logger.info(
        f"Logging initialized. Level: {logging.getLevelName(log_level)} | "
        f"Format: {'structured' if structured_format else 'standard'} | "
        f"File: {log_file or 'console only'}"
    )


def configure_test_logging(log_level: int = logging.WARNING) -> None:
    """Configure logging specifically for test environments."""
    setup_logging(
        log_level=log_level,
        console_level=log_level,
        suppress_third_party=True,
        structured_format=False,  # Use human-readable format for tests
    )


def configure_production_logging(
    log_level: int = logging.INFO, log_file: str | None = None
) -> None:
    """Configure logging for production environment with structured format.

    In Lambda environments, defaults to CloudWatch-only logging unless S3 is explicitly enabled.
    """
    # Production hygiene: Only allow S3 logging if explicitly enabled
    is_lambda = any(
        [
            os.environ.get("AWS_EXECUTION_ENV"),
            os.environ.get("AWS_LAMBDA_RUNTIME_API"),
            os.environ.get("LAMBDA_RUNTIME_DIR"),
        ]
    )
    s3_logging_enabled = os.environ.get("ENABLE_S3_LOGGING", "").lower() in (
        "1",
        "true",
        "yes",
        "on",
    )

    # If in Lambda and S3 logging not explicitly enabled, force log_file to None
    if is_lambda and not s3_logging_enabled:
        if log_file and log_file.startswith("s3://"):
            logger = get_logger(__name__)
            logger.info("Lambda production mode: defaulting to CloudWatch-only logging")
        log_file = None

    setup_logging(
        log_level=log_level,
        log_file=log_file,
        console_level=logging.WARNING,  # Reduce console noise in production
        suppress_third_party=True,
        structured_format=True,  # Use JSON format for production
        enable_file_rotation=True,
        respect_existing_handlers=False,  # Production always controls logging
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


def get_trading_logger(
    module_name: str, **context: Any
) -> logging.Logger | AlchemiserLoggerAdapter:
    """Get a logger specifically configured for trading operations.

    Args:
        module_name: Name of the module/component
        **context: Additional context to include in all log messages

    Returns:
        Logger instance with trading-specific configuration

    """
    logger = get_logger(module_name)
    if context:
        # Create adapter with default context
        return AlchemiserLoggerAdapter(logger, context)
    return logger


def log_trade_event(logger: logging.Logger, event_type: str, symbol: str, **details: Any) -> None:
    """Log a trading event with standardized structure.

    Args:
        logger: Logger instance
        event_type: Type of event (order_placed, order_filled, etc.)
        symbol: Trading symbol
        **details: Additional event details

    """
    context = {
        "event_type": event_type,
        "symbol": symbol,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        **details,
    }
    log_with_context(logger, logging.INFO, f"Trading event: {event_type} for {symbol}", **context)


def log_error_with_context(
    logger: logging.Logger, error: Exception, operation: str, **context: Any
) -> None:
    """Log an error with full context and traceback.

    Args:
        logger: Logger instance
        error: Exception that occurred
        operation: Description of the operation that failed
        **context: Additional context information

    """
    context.update(
        {"operation": operation, "error_type": type(error).__name__, "error_message": str(error)}
    )
    log_with_context(logger, logging.ERROR, f"Error in {operation}: {error}", **context)
    logger.exception(f"Full traceback for {operation} error:")
