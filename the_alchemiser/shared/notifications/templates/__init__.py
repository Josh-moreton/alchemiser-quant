"""Business Unit: shared/notifications | Status: current.

Email template package initialization.

This module provides a unified facade interface for email template generation
functions and classes used throughout the notification system. All email templates
follow the neutral reporting policy (no financial values exposed).

Public API:
    - BaseEmailTemplate: Base HTML structure and common styling
    - EmailTemplates: Unified facade for all template types
    - PortfolioBuilder: Portfolio content builder (neutral)
    - SignalsBuilder: Strategy signals and indicators
    - MultiStrategyReportBuilder: Multi-strategy execution reports
    - build_*_html: Convenience functions for common email types

Usage:
    from the_alchemiser.shared.notifications.templates import EmailTemplates
    html = EmailTemplates.error_notification("Title", "Message")
"""

# Import base template infrastructure
from .base import BaseEmailTemplate

# Import high-level facade
from .email_facade import (
    EmailTemplates,
    build_error_email_html,
    build_multi_strategy_email_html,
    build_trading_report_html,
)

# Import specialized builder classes
from .multi_strategy import MultiStrategyReportBuilder
from .portfolio import PortfolioBuilder
from .signals import SignalsBuilder

# Export the main functions and classes (alphabetically sorted)
__all__ = [
    "BaseEmailTemplate",
    "EmailTemplates",
    "MultiStrategyReportBuilder",
    "PortfolioBuilder",
    "SignalsBuilder",
    "build_error_email_html",
    "build_multi_strategy_email_html",
    "build_trading_report_html",
]
