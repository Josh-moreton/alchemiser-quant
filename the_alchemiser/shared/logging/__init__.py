"""Business Unit: shared | Status: current.

Centralized logging system for the Alchemiser trading platform.

Simple approach:
- Lambda: Emit ALL logs as JSON to CloudWatch
- Tests: Human-readable with configurable level
- Filter at read-time in CloudWatch Insights, not at write-time

CloudWatch Insights query examples:
    # View INFO+ only
    fields @timestamp, level, event, extra
    | filter level in ["info", "warning", "error"]
    | sort @timestamp desc

    # View errors only
    fields @timestamp, level, event, extra
    | filter level = "error"
"""

# Configuration functions
from .config import (
    configure_application_logging,
    configure_test_logging,
)

# Context management
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
from .structlog_config import (
    configure_structlog_lambda,
    configure_structlog_test,
    get_structlog_logger,
)

# Trading-specific helpers
from .structlog_trading import (
    bind_trading_context,
    log_data_integrity_checkpoint,
    log_order_flow,
    log_repeg_operation,
    log_trade_event,
)

__all__ = [
    "bind_trading_context",
    "configure_application_logging",
    "configure_structlog_lambda",
    "configure_structlog_test",
    "configure_test_logging",
    "generate_request_id",
    "get_causation_id",
    "get_correlation_id",
    "get_error_id",
    "get_logger",
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

# Alias for convenience
get_logger = get_structlog_logger
