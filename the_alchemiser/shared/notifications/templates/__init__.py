"""Business Unit: shared | Status: current

Email template package initialization.

This module provides a unified interface for email template generation functions
and classes used throughout the notification system.
"""

from __future__ import annotations

from typing import Any

# Import only the base template to avoid circular import issues
from .base import BaseEmailTemplate


def build_error_email_html(title: str, message: str) -> str:
    """Build an error notification email.
    
    Args:
        title: Error title
        message: Error message
        
    Returns:
        Complete HTML email content
    """
    # Create error content
    error_content = BaseEmailTemplate.create_alert_box(
        f"<strong>{title}</strong><br>{message}",
        "error"
    )
    
    # Build header and footer
    header = BaseEmailTemplate.get_header("The Alchemiser")
    status_banner = BaseEmailTemplate.get_status_banner(
        title,
        "Error",
        "#EF4444",
        "❌"
    )
    footer = BaseEmailTemplate.get_footer()
    
    # Combine content
    content = f"""
    {header}
    {status_banner}
    <tr>
        <td style="padding: 32px 24px; background-color: white;">
            {error_content}
        </td>
    </tr>
    {footer}
    """
    
    return BaseEmailTemplate.wrap_content(content, f"The Alchemiser - {title}")


def build_multi_strategy_email_html(result: Any, mode: str = "PAPER") -> str:
    """Build a multi-strategy execution report email.
    
    Args:
        result: Execution result object
        mode: Trading mode (PAPER, LIVE, etc.)
        
    Returns:
        Complete HTML email content
    """
    # Import here to avoid circular imports
    from .multi_strategy import MultiStrategyReportBuilder
    return MultiStrategyReportBuilder.build_multi_strategy_report(result, mode)


def build_trading_report_html(
    trading_summary: dict[str, Any],
    strategy_signals: dict[str, Any] | None = None,
    account_info: dict[str, Any] | None = None
) -> str:
    """Build a general trading report email.
    
    Args:
        trading_summary: Summary of trading activity
        strategy_signals: Optional strategy signals data
        account_info: Optional account information
        
    Returns:
        Complete HTML email content
    """
    # Import here to avoid circular imports
    from .performance import PerformanceBuilder
    from .portfolio import PortfolioBuilder 
    from .signals import SignalsBuilder
    
    # Build content sections
    header = BaseEmailTemplate.get_header("The Alchemiser")
    status_banner = BaseEmailTemplate.get_status_banner(
        "Trading Report",
        "Complete", 
        "#10B981",
        "✅"
    )
    
    content_sections = []
    
    # Trading summary
    if trading_summary:
        trading_html = PerformanceBuilder.build_trading_summary(trading_summary)
        content_sections.append(trading_html)
    
    # Strategy signals if available
    if strategy_signals:
        signals_html = SignalsBuilder.build_technical_indicators(strategy_signals)
        content_sections.append(signals_html)
    
    # Account summary if available
    if account_info:
        account_html = BaseEmailTemplate.create_section(
            "💰 Account Summary",
            PortfolioBuilder.build_account_summary(account_info)
        )
        content_sections.append(account_html)
    
    footer = BaseEmailTemplate.get_footer()
    
    # Combine all content
    main_content = "".join(content_sections)
    content = f"""
    {header}
    {status_banner}
    <tr>
        <td style="padding: 32px 24px; background-color: white;">
            {main_content}
        </td>
    </tr>
    {footer}
    """
    
    return BaseEmailTemplate.wrap_content(content, "The Alchemiser - Trading Report")


class EmailTemplates:
    """Unified email template generator class.
    
    This class provides a centralized interface for generating different types
    of email templates used throughout the system.
    """
    
    @staticmethod
    def error_notification(title: str, message: str) -> str:
        """Generate an error notification email."""
        return build_error_email_html(title, message)
    
    @staticmethod
    def multi_strategy_report(result: Any, mode: str = "PAPER") -> str:
        """Generate a multi-strategy execution report."""
        return build_multi_strategy_email_html(result, mode)
    
    @staticmethod
    def trading_report(
        trading_summary: dict[str, Any],
        strategy_signals: dict[str, Any] | None = None,
        account_info: dict[str, Any] | None = None
    ) -> str:
        """Generate a general trading report."""
        return build_trading_report_html(trading_summary, strategy_signals, account_info)


# Export the main functions and classes
__all__ = [
    "EmailTemplates",
    "build_error_email_html", 
    "build_multi_strategy_email_html",
    "build_trading_report_html",
    "BaseEmailTemplate",
]