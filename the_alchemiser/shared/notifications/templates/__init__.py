"""Business Unit: shared | Status: current.

Email template package initialization.

This module provides a unified interface for email template generation functions
and classes used throughout the notification system.
"""

# Import template builders for direct access
from .base import BaseEmailTemplate

# Import template facade functions and classes
from .email_facade import (
    EmailTemplates,
    build_error_email_html,
    build_multi_strategy_email_html,
    build_trading_report_html,
)

# Export the main functions and classes
__all__ = [
    "BaseEmailTemplate",
    "EmailTemplates",
    "build_error_email_html",
    "build_multi_strategy_email_html",
    "build_trading_report_html",
]
