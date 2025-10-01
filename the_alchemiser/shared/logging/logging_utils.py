"""Business Unit: utilities; Status: deprecated.

DEPRECATED: This module has been decomposed into smaller, focused modules.

This file is maintained for backward compatibility only. New code should import from:
- the_alchemiser.shared.logging (preferred - public API)
- the_alchemiser.shared.logging.core (core functions)
- the_alchemiser.shared.logging.trading (trading-specific functions)
- the_alchemiser.shared.logging.config (configuration functions)
- the_alchemiser.shared.logging.context (context management)

All functions are re-exported from the new modular structure to maintain
backward compatibility with existing imports.
"""

from __future__ import annotations

# Re-export everything from new modules for backward compatibility
from .config import (
    configure_application_logging,
    configure_production_logging,
    configure_test_logging,
    resolve_log_level,
)
from .context import (
    error_id_context,
    generate_request_id,
    get_error_id,
    get_request_id,
    request_id_context,
    set_error_id,
    set_request_id,
)
from .core import (
    configure_quiet_logging,
    get_logger,
    get_service_logger,
    log_with_context,
    restore_logging,
    setup_logging,
)
from .formatters import AlchemiserLoggerAdapter, StructuredFormatter
from .trading import (
    get_trading_logger,
    log_data_transfer_checkpoint,
    log_error_with_context,
    log_trade_event,
    log_trade_expectation_vs_reality,
)

# Re-export private functions used internally (prefixed with _)
# These are needed for internal module dependencies

__all__ = [
    # Formatters and adapters
    "AlchemiserLoggerAdapter",
    "StructuredFormatter",
    "configure_application_logging",
    "configure_production_logging",
    "configure_quiet_logging",
    # Configuration functions
    "configure_test_logging",
    "error_id_context",
    "generate_request_id",
    "get_error_id",
    # Core functions
    "get_logger",
    "get_request_id",
    "get_service_logger",
    # Trading functions
    "get_trading_logger",
    "log_data_transfer_checkpoint",
    "log_error_with_context",
    "log_trade_event",
    "log_trade_expectation_vs_reality",
    "log_with_context",
    # Context variables and functions
    "request_id_context",
    "resolve_log_level",
    "restore_logging",
    "set_error_id",
    "set_request_id",
    "setup_logging",
]
