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
from datetime import UTC, datetime
from pathlib import Path
from typing import cast

# Constants
_S3_PROTOCOL_PREFIX = "s3://"

# S3 logging configuration constants
# Set of string values that, when present in configuration, indicate S3 logging should be enabled.
_S3_ENABLED_VALUES = frozenset(["1", "true", "yes", "on"])
# Set of environment variable names that, if present, indicate the code is running in an AWS Lambda environment.
_LAMBDA_ENV_VARS = frozenset(["AWS_EXECUTION_ENV", "AWS_LAMBDA_RUNTIME_API", "LAMBDA_RUNTIME_DIR"])

# Context variables for request tracking
request_id_context: ContextVar[str | None] = ContextVar("request_id", default=None)
error_id_context: ContextVar[str | None] = ContextVar("error_id", default=None)


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


class AlchemiserLoggerAdapter(logging.LoggerAdapter[logging.Logger]):
    """Custom logger adapter for the Alchemiser quantitative trading system."""

    def process(
        self, msg: object, kwargs: MutableMapping[str, object]
    ) -> tuple[str, MutableMapping[str, object]]:
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
            "timestamp": datetime.now(UTC).isoformat() + "Z",
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


def generate_request_id() -> str:
    """Generate a new request ID.

    Returns:
        A unique request ID string

    """
    return str(uuid.uuid4())


def log_with_context(
    logger: logging.Logger, level: int | None, message: str, **context: object
) -> None:
    """Log a message with additional context fields.

    Args:
        logger: Logger instance
        level: Logging level (e.g., logging.INFO) or logger method
        message: Log message
        **context: Additional context fields to include

    """
    extra: dict[str, object] = {"extra_fields": context}

    # Handle case where level is a logger method (e.g., logger.info)
    if callable(level):
        level(message, extra=extra)
    else:
        # level should be an integer logging level
        if level is None:
            level = logging.INFO
        logger.log(level, message, extra=extra)


def _create_formatter(*, structured_format: bool) -> logging.Formatter:
    """Create appropriate formatter based on format setting."""
    if structured_format:
        return StructuredFormatter()
    log_format = "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
    return logging.Formatter(log_format)


def _create_console_handler(
    formatter: logging.Formatter, console_level: int | None, log_level: int
) -> logging.Handler:
    """Create console handler with appropriate level."""
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(console_level if console_level is not None else log_level)
    return console_handler


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


def _should_add_console_handler(
    *, respect_existing_handlers: bool, root_logger: logging.Logger
) -> bool:
    """Determine if console handler should be added."""
    return not respect_existing_handlers or not root_logger.hasHandlers()


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


def configure_test_logging(log_level: int = logging.WARNING) -> None:
    """Configure logging specifically for test environments."""
    setup_logging(
        log_level=log_level,
        console_level=log_level,
        suppress_third_party=True,
        structured_format=False,  # Use human-readable format for tests
    )


def configure_production_logging(
    log_level: int = logging.INFO,
    log_file: str | None = None,
    *,
    console_level: int | None = None,
) -> None:
    """Configure logging for production environment with structured format.

    In Lambda environments, defaults to CloudWatch-only logging unless S3 is explicitly enabled.

    Args:
        log_level: Base log level for handlers.
        log_file: Optional path/URI for file logging.
        console_level: Override for console handler level. When None, defaults to `log_level`.

    """
    # Production hygiene: Only allow S3 logging if explicitly enabled
    if _should_suppress_s3_logging(log_file):
        logger = get_logger(__name__)
        logger.info("Lambda production mode: defaulting to CloudWatch-only logging")
        log_file = None

    setup_logging(
        log_level=log_level,
        log_file=log_file,
        console_level=console_level if console_level is not None else log_level,
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
    module_name: str, **context: object
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


def log_trade_event(
    logger: logging.Logger, event_type: str, symbol: str, **details: object
) -> None:
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
        "timestamp": datetime.now(UTC).isoformat() + "Z",
        **details,
    }
    log_with_context(logger, logging.INFO, f"Trading event: {event_type} for {symbol}", **context)


def log_error_with_context(
    logger: logging.Logger, error: Exception, operation: str, **context: object
) -> None:
    """Log an error with full context and traceback.

    Args:
        logger: Logger instance
        error: Exception that occurred
        operation: Description of the operation that failed
        **context: Additional context information

    """
    context.update(
        {
            "operation": operation,
            "error_type": type(error).__name__,
            "error_message": str(error),
        }
    )
    log_with_context(logger, logging.ERROR, f"Error in {operation}: {error}", **context)
    logger.exception(f"Full traceback for {operation} error:")


def log_data_transfer_checkpoint(
    logger: logging.Logger,
    stage: str,
    data: dict[str, object] | None,
    context: str = "",
) -> None:
    """Log a data transfer checkpoint with integrity validation.

    This function provides standardized logging for data transfer points
    in the trade pipeline to help trace where data might be lost.

    Args:
        logger: Logger instance to use
        stage: Name of the pipeline stage (e.g., "ExecutionManager→Engine")
        data: The data being transferred (typically portfolio allocation dict)
        context: Additional context description

    """
    if data is None:
        logger.error(f"🚨 DATA_TRANSFER_CHECKPOINT[{stage}]: NULL DATA DETECTED")
        logger.error(f"🚨 Context: {context}")
        return

    # Calculate data integrity metrics
    data_count = len(data) if data else 0
    data_checksum: float = 0.0
    if data and all(isinstance(v, int | float) for v in data.values()):
        numeric_values: list[float] = []
        for v in data.values():
            numeric_values.append(float(cast(int | float, v)))
        data_checksum = sum(numeric_values)
    data_type = type(data).__name__

    # Log checkpoint info
    logger.info(f"=== DATA_TRANSFER_CHECKPOINT[{stage}] ===")
    logger.info(f"STAGE: {stage}")
    logger.info(f"CONTEXT: {context}")
    logger.info(f"DATA_TYPE: {data_type}")
    logger.info(f"DATA_COUNT: {data_count}")
    logger.info(f"DATA_CHECKSUM: {data_checksum:.6f}")

    # Log detailed content for small datasets
    if data_count <= 10:
        logger.info(f"DATA_CONTENT: {data}")
    else:
        # Log first few items for large datasets
        items = list(data.items())[:5] if hasattr(data, "items") else []
        logger.info(f"DATA_SAMPLE: {dict(items)} (showing first 5 of {data_count})")

    # Data validation warnings
    if data_count == 0:
        logger.warning(f"⚠️ CHECKPOINT[{stage}]: Empty data detected")

    if (
        isinstance(data, dict)
        and all(isinstance(v, int | float) for v in data.values())
        and abs(data_checksum - 1.0) > 0.05
    ):
        # Portfolio allocation validation
        logger.warning(
            f"⚠️ CHECKPOINT[{stage}]: Portfolio allocation sum={data_checksum:.4f}, expected~1.0"
        )

    logger.info(f"=== END_CHECKPOINT[{stage}] ===")


def _format_trade_details(trade: dict[str, object], index: int) -> str:
    """Format trade details for logging."""
    symbol = trade.get("symbol", "UNKNOWN")
    action = trade.get("action", "UNKNOWN")
    amount = trade.get("amount", 0)
    return f"  Expected_{index + 1}: {action} {symbol} ${amount:.2f}"


def _format_order_details(order: object, index: int) -> str:
    """Format order details for logging."""
    if hasattr(order, "symbol") and hasattr(order, "side") and hasattr(order, "qty"):
        return f"  Actual_{index + 1}: {order.side} {order.symbol} qty={order.qty}"
    if isinstance(order, dict):
        symbol = order.get("symbol", "UNKNOWN")
        side = order.get("side", "UNKNOWN")
        qty = order.get("qty", 0)
        return f"  Actual_{index + 1}: {side} {symbol} qty={qty}"
    return f"  Actual_{index + 1}: {order}"


def _log_trade_mismatches(
    logger: logging.Logger,
    expected_trades: list[dict[str, object]],
    expected_count: int,
    actual_count: int,
    stage: str,
) -> None:
    """Log trade count mismatches and lost trades."""
    if expected_count > 0 and actual_count == 0:
        logger.error(
            f"🚨 TRADE_LOSS_DETECTED[{stage}]: Expected {expected_count} trades but got 0 orders"
        )
        for trade in expected_trades:
            symbol = trade.get("symbol", "UNKNOWN")
            action = trade.get("action", "UNKNOWN")
            amount = trade.get("amount", 0)
            logger.error(f"🚨 LOST_TRADE: {action} {symbol} ${amount:.2f}")
    elif expected_count != actual_count:
        logger.warning(
            f"⚠️ TRADE_COUNT_MISMATCH[{stage}]: Expected {expected_count} ≠ Actual {actual_count}"
        )


def log_trade_expectation_vs_reality(
    logger: logging.Logger,
    expected_trades: list[dict[str, object]],
    actual_orders: list[object],
    stage: str = "Unknown",
) -> None:
    """Log comparison between expected trades and actual orders created.

    Args:
        logger: Logger instance
        expected_trades: List of expected trade calculations
        actual_orders: List of actual orders created
        stage: Pipeline stage where this comparison is being made

    """
    expected_count = len(expected_trades) if expected_trades else 0
    actual_count = len(actual_orders) if actual_orders else 0

    logger.info(f"=== TRADE_EXPECTATION_VS_REALITY[{stage}] ===")
    logger.info(f"EXPECTED_TRADES: {expected_count}")
    logger.info(f"ACTUAL_ORDERS: {actual_count}")
    logger.info(f"MATCH: {expected_count == actual_count}")

    if expected_count > 0:
        logger.info("EXPECTED_TRADE_DETAILS:")
        for i, trade in enumerate(expected_trades):
            logger.info(_format_trade_details(trade, i))

    if actual_count > 0:
        logger.info("ACTUAL_ORDER_DETAILS:")
        for i, order in enumerate(actual_orders):
            logger.info(_format_order_details(order, i))

    # Flag mismatches
    _log_trade_mismatches(logger, expected_trades, expected_count, actual_count, stage)

    logger.info(f"=== END_EXPECTATION_VS_REALITY[{stage}] ===")


def resolve_log_level(*, is_production: bool) -> int:
    """Resolve the desired log level from environment or settings.

    Args:
        is_production: Whether running in production environment

    Returns:
        Log level as integer

    """
    # Environment override first
    env_level = _parse_log_level(os.getenv("LOGGING__LEVEL"))
    if env_level is not None:
        return env_level

    # Then settings
    try:
        from the_alchemiser.shared.config.config import load_settings

        settings = load_settings()
        configured = _parse_log_level(getattr(settings.logging, "level", None))
        if configured is not None:
            return configured
    except (AttributeError, TypeError, ImportError):
        # Settings loading failed or invalid log level, fall back to default
        pass

    # Fallback
    return logging.INFO if is_production else logging.WARNING


def _load_application_settings() -> object | None:
    """Load application settings with error handling."""
    try:
        from the_alchemiser.shared.config.config import load_settings

        return load_settings()
    except (AttributeError, ImportError, TypeError):
        return None


def _determine_production_log_file(settings: object | None) -> str | None:
    """Determine log file for production environment."""
    if not settings:
        return None
    if (
        hasattr(settings, "logging")
        and getattr(settings.logging, "enable_s3_logging", False)
        and getattr(settings.logging, "s3_log_uri", None)
    ):
        return str(getattr(settings.logging, "s3_log_uri", None))
    return None


def _determine_production_console_level(settings: object | None) -> int | None:
    """Determine console level for production environment."""
    console_level = _parse_log_level(os.getenv("LOGGING__CONSOLE_LEVEL"))
    if console_level is not None:
        return console_level

    if not settings or not hasattr(settings, "logging"):
        return None

    settings_console_value = getattr(settings.logging, "console_level", None)
    if settings_console_value is not None:
        return _parse_log_level(str(settings_console_value))

    return None


def _configure_production_logging(resolved_level: int, settings: object | None) -> None:
    """Configure logging for production environment."""
    log_file = _determine_production_log_file(settings)
    console_level = _determine_production_console_level(settings)

    configure_production_logging(
        log_level=resolved_level,
        log_file=log_file,
        console_level=console_level,
    )


def _determine_development_console_level(default_level: int, settings: object | None) -> int:
    """Determine console level for development environment."""
    env_console = _parse_log_level(os.getenv("LOGGING__CONSOLE_LEVEL"))
    if env_console is not None:
        return env_console

    if settings and hasattr(settings, "logging"):
        configured_console = _parse_log_level(str(settings.logging.console_level))
        if configured_console is not None:
            return configured_console

    return default_level


def _determine_development_log_file(settings: object | None) -> str | None:
    """Determine log file for development environment."""
    env_path = os.getenv("LOGGING__LOCAL_LOG_FILE")
    if env_path and env_path.strip():
        return env_path

    if settings and hasattr(settings, "logging"):
        local_log_file = getattr(settings.logging, "local_log_file", None)
        if local_log_file:
            path = str(local_log_file).strip()
            return path or None

    return None


def _configure_development_logging(resolved_level: int, settings: object | None) -> None:
    """Configure logging for development environment."""
    setup_logging(
        log_level=resolved_level,
        log_file=_determine_development_log_file(settings),
        console_level=_determine_development_console_level(resolved_level, settings),
        suppress_third_party=True,
        structured_format=False,
        respect_existing_handlers=True,
    )


def _is_lambda_production_environment() -> bool:
    """Check if running in Lambda production environment."""
    return any(
        [
            os.getenv("AWS_EXECUTION_ENV"),
            os.getenv("AWS_LAMBDA_RUNTIME_API"),
            os.getenv("LAMBDA_RUNTIME_DIR"),
        ]
    )


def _should_skip_logging_setup(root_logger: logging.Logger, *, is_production: bool) -> bool:
    """Determine if logging setup should be skipped."""
    return root_logger.hasHandlers() and not is_production


def configure_application_logging() -> None:
    """Configure application logging with reduced complexity."""
    is_production = _is_lambda_production_environment()
    root_logger = logging.getLogger()

    if _should_skip_logging_setup(root_logger, is_production=is_production):
        return

    resolved_level = resolve_log_level(is_production=is_production)
    settings = _load_application_settings()

    if is_production:
        _configure_production_logging(resolved_level, settings)
    else:
        _configure_development_logging(resolved_level, settings)


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
        "the_alchemiser.orchestration.trading_orchestrator",
        "the_alchemiser.orchestration.signal_orchestrator",
        "the_alchemiser.orchestration.portfolio_orchestrator",
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
