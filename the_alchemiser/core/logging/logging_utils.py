import json
import logging
import os
import sys
from datetime import datetime
from typing import List, Optional, Union

from the_alchemiser.core.utils.s3_utils import S3FileHandler


class AlchemiserLoggerAdapter(logging.LoggerAdapter):
    """Custom logger adapter for the Alchemiser quantitative trading system."""

    def process(self, msg, kwargs):
        return f"[ALCHEMISER] {msg}", kwargs


class StructuredFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": self.formatException(record.exc_info) if record.exc_info else None,
            }

        # Add extra fields if present
        extra_fields = getattr(record, "extra_fields", None)
        if extra_fields:
            log_entry.update(extra_fields)

        return json.dumps(log_entry, default=str)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with proper configuration.

    Args:
        name: Logger name, typically __name__

    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


def log_with_context(logger: logging.Logger, level: int, message: str, **context) -> None:
    """
    Log a message with additional context fields.

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
    log_file: Optional[str] = None,
    console_level: Optional[int] = None,
    suppress_third_party: bool = True,
    structured_format: bool = False,
    enable_file_rotation: bool = False,
    max_file_size_mb: int = 100,
) -> None:
    """
    Set up centralized logging for the project.

    Args:
        log_level: Default logging level for file output
        log_file: Optional file path or S3 URI for file logging
        console_level: Optional different level for console output (defaults to log_level)
        suppress_third_party: Whether to suppress noisy third-party loggers
        structured_format: Whether to use JSON structured logging format
        enable_file_rotation: Whether to enable file rotation for local files
        max_file_size_mb: Maximum file size in MB before rotation
    """
    # Clear any existing handlers to avoid duplicates
    root_logger = logging.getLogger()
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    # Choose formatter based on structured_format setting
    if structured_format:
        formatter = StructuredFormatter()
    else:
        # Standard format for human-readable logs
        log_format = "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
        formatter = logging.Formatter(log_format)

    # Console handler - always add one
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(console_level if console_level is not None else log_level)

    handlers: List[logging.Handler] = [console_handler]

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
    log_level: int = logging.INFO, log_file: Optional[str] = None
) -> None:
    """Configure logging for production environment with structured format."""
    setup_logging(
        log_level=log_level,
        log_file=log_file,
        console_level=logging.WARNING,  # Reduce console noise in production
        suppress_third_party=True,
        structured_format=True,  # Use JSON format for production
        enable_file_rotation=True,
    )


def get_trading_logger(
    module_name: str, **context
) -> Union[logging.Logger, AlchemiserLoggerAdapter]:
    """
    Get a logger specifically configured for trading operations.

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


def log_trade_event(logger: logging.Logger, event_type: str, symbol: str, **details) -> None:
    """
    Log a trading event with standardized structure.

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
    logger: logging.Logger, error: Exception, operation: str, **context
) -> None:
    """
    Log an error with full context and traceback.

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
