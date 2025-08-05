"""Email module for The Alchemiser quantitative trading system.

This module provides email notification functionality with clean separation
of concerns across configuration, client operations, and template generation.

Main components:
- config: Email configuration management
- client: SMTP client for sending emails
- templates: HTML email template builders

Usage:
    from the_alchemiser.core.ui.email import send_email_notification
    from the_alchemiser.core.ui.email.templates import EmailTemplates

    # Send a simple notification
    send_email_notification(
        subject="Test Email",
        html_content="<h1>Hello World</h1>"
    )

    # Build a trading report
    html_content = EmailTemplates.build_trading_report(
        mode="LIVE",
        success=True,
        account_before={},
        account_after={"equity": 50000},
        positions={},
        orders=[]
    )
"""

# Import main functions for backward compatibility
from typing import Any

from .client import EmailClient, send_email_notification
from .config import get_email_config, is_neutral_mode_enabled
from .templates import (
    EmailTemplates,
    build_error_email_html,
    build_multi_strategy_email_html,
    build_trading_report_html,
)

__all__ = [
    "get_email_config",
    "is_neutral_mode_enabled",
    "send_email_notification",
    "EmailClient",
    "build_trading_report_html",
    "build_multi_strategy_email_html",
    "build_error_email_html",
    "EmailTemplates",
]
