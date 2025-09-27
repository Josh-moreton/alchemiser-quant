"""Business Unit: utilities; Status: current.

Email utilities module - REFACTORED.

This module now imports from the new modular email system for backward compatibility.
The email functionality has been split into separate modules:

- email/config.py: Email configuration management
- email/client.py: SMTP client operations
- email/templates/: Template builders for different content types
  - base.py: Base template structure
  - portfolio.py: Portfolio content builder
  - performance.py: Performance metrics builder
  - signals.py: Strategy signals builder
  - trading_report.py: Trading report templates
  - multi_strategy.py: Multi-strategy report templates
  - error_report.py: Error notification templates

For new code, import directly from the notifications module:
    from the_alchemiser.shared.notifications import send_email_notification
    from the_alchemiser.shared.notifications.templates import EmailTemplates

This file maintains backward compatibility for existing imports.
"""

from __future__ import annotations

# Import schemas for type-safe email rendering
# Import all functions from the new modular structure
from .client import EmailClient, send_email_notification
from .config import get_email_config, is_neutral_mode_enabled
from .templates import (
    EmailTemplates,
    build_error_email_html,
    build_multi_strategy_email_html,
    build_trading_report_html,
)
from .templates.base import BaseEmailTemplate

# Import specific template builders for advanced usage
from .templates.portfolio import PortfolioBuilder
from .templates.signals import SignalsBuilder

# Export the main public API
__all__ = [
    "BaseEmailTemplate",
    "EmailClient",
    "EmailTemplates",
    "PortfolioBuilder",
    "SignalsBuilder",
    "build_error_email_html",
    "build_multi_strategy_email_html",
    "build_trading_report_html",
    "get_email_config",
    "is_neutral_mode_enabled",
    "send_email_notification",
]
