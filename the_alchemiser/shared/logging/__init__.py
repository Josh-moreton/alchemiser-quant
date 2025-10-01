"""Business Unit: shared | Status: current.

Centralized logging system for the Alchemiser trading platform.

This package provides a comprehensive logging infrastructure with:
- Core logging setup and configuration
- Context management for request/error tracking
- Custom formatters including JSON structured logging
- Handler management for console, file, and S3 logging
- Trading-specific logging helpers
- Environment-specific configuration (production, test, development)
"""

# Core logging functions
from .core import (
    configure_quiet_logging,
    get_logger,
    get_service_logger,
    log_with_context,
    restore_logging,
    setup_logging,
)

# Context management
from .context import (
    generate_request_id,
    get_error_id,
    get_request_id,
    set_error_id,
    set_request_id,
)

# Configuration functions
from .config import (
    configure_application_logging,
    configure_production_logging,
    configure_test_logging,
)

# Trading-specific logging
from .trading import (
    get_trading_logger,
    log_data_transfer_checkpoint,
    log_error_with_context,
    log_trade_event,
    log_trade_expectation_vs_reality,
)

# Custom formatters and adapters (for advanced use)
from .formatters import AlchemiserLoggerAdapter, StructuredFormatter

__all__ = [
    # Core functions
    "get_logger",
    "setup_logging",
    "log_with_context",
    "get_service_logger",
    "configure_quiet_logging",
    "restore_logging",
    # Context management
    "set_request_id",
    "get_request_id",
    "set_error_id",
    "get_error_id",
    "generate_request_id",
    # Configuration
    "configure_application_logging",
    "configure_production_logging",
    "configure_test_logging",
    # Trading-specific
    "log_trade_event",
    "log_data_transfer_checkpoint",
    "log_trade_expectation_vs_reality",
    "log_error_with_context",
    "get_trading_logger",
    # Advanced
    "AlchemiserLoggerAdapter",
    "StructuredFormatter",
]
