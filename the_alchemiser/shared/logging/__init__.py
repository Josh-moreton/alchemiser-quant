"""Business Unit: shared | Status: current.

Centralized logging system for the Alchemiser trading platform.

This package provides structlog-based structured logging infrastructure with:
- Structlog configuration with Alchemiser-specific processors
- Context management for request/error tracking
- Trading-specific logging helpers (order flow, repeg operations, data integrity)
- Environment-specific configuration (production, test, development)
- Decimal serialization for precise financial data
"""

# Structlog configuration functions
from .config import (
    configure_application_logging,
    configure_production_logging,
    configure_test_logging,
)

# Context management (still using contextvars)
from .context import (
    generate_request_id,
    get_causation_id,
    get_correlation_id,
    get_error_id,
    get_request_id,
    set_causation_id,
    set_correlation_id,
    set_error_id,
    set_request_id,
)
from .structlog_config import configure_structlog, get_structlog_logger

# Structlog trading-specific helpers
from .structlog_trading import (
    bind_trading_context,
    log_data_integrity_checkpoint,
    log_order_flow,
    log_repeg_operation,
    log_trade_event,
)

__all__ = [
    # Trading-specific helpers
    "bind_trading_context",
    # Configuration functions
    "configure_application_logging",
    "configure_production_logging",
    # Structlog primary functions
    "configure_structlog",
    "configure_test_logging",
    # Context management
    "generate_request_id",
    "get_causation_id",
    "get_correlation_id",
    "get_error_id",
    "get_request_id",
    "get_structlog_logger",
    "log_data_integrity_checkpoint",
    "log_order_flow",
    "log_repeg_operation",
    "log_trade_event",
    "set_causation_id",
    "set_correlation_id",
    "set_error_id",
    "set_request_id",
]

# Alias for convenience - get_logger returns structlog logger
get_logger = get_structlog_logger
