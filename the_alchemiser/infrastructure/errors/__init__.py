"""Business Unit: utilities; Status: current.

Infrastructure error handling for The Alchemiser.

Error handlers, monitoring, reporting and other side-effect operations.
"""

from __future__ import annotations

from .handler import (
    TradingSystemErrorHandler,
    handle_trading_error,
    handle_errors_with_retry,
    send_error_notification_if_needed,
)
from .context import create_error_context, ErrorContextData
from .decorators import translate_trading_errors, translate_market_data_errors

__all__ = [
    "TradingSystemErrorHandler",
    "handle_trading_error",
    "handle_errors_with_retry", 
    "send_error_notification_if_needed",
    "create_error_context",
    "ErrorContextData", 
    "translate_trading_errors",
    "translate_market_data_errors",
]