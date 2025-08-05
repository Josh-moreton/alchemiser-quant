#!/usr/bin/env python3
"""
Enhanced Error Handler for The Alchemiser Trading System.

This module provides comprehensive error handling, categorization, and detailed
error reporting via email notifications for autonomous trading operations.
"""

import logging
import traceback
from datetime import datetime
from typing import Any

from .exceptions import (
    AlchemiserError,
    ConfigurationError,
    DataProviderError,
    InsufficientFundsError,
    MarketDataError,
    NotificationError,
    OrderExecutionError,
    PositionValidationError,
    StrategyExecutionError,
    TradingClientError,
)


class ErrorCategory:
    """Error categories for classification and handling."""

    CRITICAL = "critical"  # System-level failures that stop all operations
    TRADING = "trading"  # Order execution, position validation issues
    DATA = "data"  # Market data, API connectivity issues
    STRATEGY = "strategy"  # Strategy calculation, signal generation issues
    CONFIGURATION = "configuration"  # Config, authentication, setup issues
    NOTIFICATION = "notification"  # Email, alert delivery issues
    WARNING = "warning"  # Non-critical issues that don't stop execution


class ErrorDetails:
    """Detailed error information for reporting."""

    def __init__(
        self,
        error: Exception,
        category: str,
        context: str,
        component: str,
        additional_data: dict[str, Any] | None = None,
        suggested_action: str | None = None,
    ):
        self.error = error
        self.category = category
        self.context = context
        self.component = component
        self.additional_data = additional_data or {}
        self.suggested_action = suggested_action
        self.timestamp = datetime.now()
        self.traceback = traceback.format_exc()

    def to_dict(self) -> dict[str, Any]:
        """Convert error details to dictionary for serialization."""
        return {
            "error_type": type(self.error).__name__,
            "error_message": str(self.error),
            "category": self.category,
            "context": self.context,
            "component": self.component,
            "timestamp": self.timestamp.isoformat(),
            "traceback": self.traceback,
            "additional_data": self.additional_data,
            "suggested_action": self.suggested_action,
        }


class TradingSystemErrorHandler:
    """Enhanced error handler for autonomous trading operations."""

    def __init__(self):
        self.errors: list[ErrorDetails] = []
        self.logger = logging.getLogger(__name__)

    def categorize_error(self, error: Exception, context: str = "") -> str:
        """Categorize error based on type and context."""
        if isinstance(
            error, InsufficientFundsError | OrderExecutionError | PositionValidationError
        ):
            return ErrorCategory.TRADING
        elif isinstance(error, MarketDataError | DataProviderError):
            return ErrorCategory.DATA
        elif isinstance(error, StrategyExecutionError):
            return ErrorCategory.STRATEGY
        elif isinstance(error, ConfigurationError):
            return ErrorCategory.CONFIGURATION
        elif isinstance(error, NotificationError):
            return ErrorCategory.NOTIFICATION
        elif isinstance(error, TradingClientError):
            # Could be trading or data depending on context
            if "order" in context.lower() or "position" in context.lower():
                return ErrorCategory.TRADING
            else:
                return ErrorCategory.DATA
        elif isinstance(error, AlchemiserError):
            return ErrorCategory.CRITICAL
        else:
            # Non-Alchemiser exceptions - categorize by context
            if "trading" in context.lower() or "order" in context.lower():
                return ErrorCategory.TRADING
            elif "data" in context.lower() or "price" in context.lower():
                return ErrorCategory.DATA
            elif "strategy" in context.lower() or "signal" in context.lower():
                return ErrorCategory.STRATEGY
            elif "config" in context.lower() or "auth" in context.lower():
                return ErrorCategory.CONFIGURATION
            else:
                return ErrorCategory.CRITICAL

    def get_suggested_action(self, error: Exception, category: str) -> str:
        """Get suggested action based on error type and category."""
        if isinstance(error, InsufficientFundsError):
            return "Check account balance and reduce position sizes or add funds"
        elif isinstance(error, OrderExecutionError):
            return "Verify market hours, check symbol validity, and ensure order parameters are correct"
        elif isinstance(error, PositionValidationError):
            return "Check current positions and ensure selling quantities don't exceed holdings"
        elif isinstance(error, MarketDataError):
            return "Check API connectivity and data provider status"
        elif isinstance(error, ConfigurationError):
            return "Verify configuration settings and API credentials"
        elif isinstance(error, StrategyExecutionError):
            return "Review strategy logic and input data for calculation errors"
        elif category == ErrorCategory.DATA:
            return "Check market data sources, API limits, and network connectivity"
        elif category == ErrorCategory.TRADING:
            return "Verify trading permissions, account status, and market hours"
        elif category == ErrorCategory.CRITICAL:
            return "Review system logs, check AWS permissions, and verify deployment configuration"
        else:
            return "Review logs for detailed error information and contact support if needed"

    def handle_error(
        self,
        error: Exception,
        context: str,
        component: str,
        additional_data: dict[str, Any] | None = None,
        should_continue: bool = True,  # noqa: ARG002
    ) -> ErrorDetails:
        """Handle an error with detailed logging and categorization."""
        category = self.categorize_error(error, context)
        suggested_action = self.get_suggested_action(error, category)

        error_details = ErrorDetails(
            error=error,
            category=category,
            context=context,
            component=component,
            additional_data=additional_data,
            suggested_action=suggested_action,
        )

        self.errors.append(error_details)

        # Log with appropriate level
        if category == ErrorCategory.CRITICAL:
            self.logger.critical(f"CRITICAL ERROR in {component}: {error}", exc_info=True)
        elif category in [ErrorCategory.TRADING, ErrorCategory.DATA, ErrorCategory.STRATEGY]:
            self.logger.error(f"{category.upper()} ERROR in {component}: {error}", exc_info=True)
        elif category == ErrorCategory.CONFIGURATION:
            self.logger.error(f"CONFIGURATION ERROR in {component}: {error}", exc_info=True)
        else:
            self.logger.warning(f"{category.upper()} in {component}: {error}")

        return error_details

    def has_critical_errors(self) -> bool:
        """Check if any critical errors occurred."""
        return any(error.category == ErrorCategory.CRITICAL for error in self.errors)

    def has_trading_errors(self) -> bool:
        """Check if any trading-related errors occurred."""
        return any(error.category == ErrorCategory.TRADING for error in self.errors)

    def get_error_summary(self) -> dict[str, Any]:
        """Get a summary of all errors by category."""
        summary = {}
        for category in [
            ErrorCategory.CRITICAL,
            ErrorCategory.TRADING,
            ErrorCategory.DATA,
            ErrorCategory.STRATEGY,
            ErrorCategory.CONFIGURATION,
            ErrorCategory.NOTIFICATION,
            ErrorCategory.WARNING,
        ]:
            category_errors = [e for e in self.errors if e.category == category]
            if category_errors:
                summary[category] = {
                    "count": len(category_errors),
                    "errors": [e.to_dict() for e in category_errors],
                }
        return summary

    def should_send_error_email(self) -> bool:
        """Determine if an error email should be sent."""
        # Send email for any errors except pure notification errors
        non_notification_errors = [
            e for e in self.errors if e.category != ErrorCategory.NOTIFICATION
        ]
        return len(non_notification_errors) > 0

    def generate_error_report(self) -> str:
        """Generate a detailed error report for email notification."""
        if not self.errors:
            return "No errors to report."

        summary = self.get_error_summary()

        # Build report
        report = "# Trading System Error Report\n\n"
        report += f"**Execution Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
        report += f"**Total Errors:** {len(self.errors)}\n\n"

        # Critical errors first
        if ErrorCategory.CRITICAL in summary:
            report += "## 🚨 CRITICAL ERRORS\n"
            report += "These errors stopped system execution and require immediate attention:\n\n"
            for error in summary[ErrorCategory.CRITICAL]["errors"]:
                report += f"**Component:** {error['component']}\n"
                report += f"**Context:** {error['context']}\n"
                report += f"**Error:** {error['error_message']}\n"
                report += f"**Action:** {error['suggested_action']}\n"
                if error["additional_data"]:
                    report += f"**Additional Data:** {error['additional_data']}\n"
                report += "\n"

        # Trading errors
        if ErrorCategory.TRADING in summary:
            report += "## 💰 TRADING ERRORS\n"
            report += "These errors affected trade execution:\n\n"
            for error in summary[ErrorCategory.TRADING]["errors"]:
                report += f"**Component:** {error['component']}\n"
                report += f"**Context:** {error['context']}\n"
                report += f"**Error:** {error['error_message']}\n"
                report += f"**Action:** {error['suggested_action']}\n"
                if error["additional_data"]:
                    report += f"**Additional Data:** {error['additional_data']}\n"
                report += "\n"

        # Other categories
        for category in [ErrorCategory.DATA, ErrorCategory.STRATEGY, ErrorCategory.CONFIGURATION]:
            if category in summary:
                icon = (
                    "📊"
                    if category == ErrorCategory.DATA
                    else "🧠" if category == ErrorCategory.STRATEGY else "⚙️"
                )
                report += f"## {icon} {category.upper()} ERRORS\n"
                for error in summary[category]["errors"]:
                    report += f"**Component:** {error['component']}\n"
                    report += f"**Context:** {error['context']}\n"
                    report += f"**Error:** {error['error_message']}\n"
                    report += f"**Action:** {error['suggested_action']}\n"
                    if error["additional_data"]:
                        report += f"**Additional Data:** {error['additional_data']}\n"
                    report += "\n"

        return report

    def clear_errors(self):
        """Clear all recorded errors."""
        self.errors.clear()


# Global error handler instance
_error_handler = TradingSystemErrorHandler()


def get_error_handler() -> TradingSystemErrorHandler:
    """Get the global error handler instance."""
    return _error_handler


def handle_trading_error(
    error: Exception, context: str, component: str, additional_data: dict[str, Any] | None = None
) -> ErrorDetails:
    """Convenience function to handle errors in trading operations."""
    return _error_handler.handle_error(error, context, component, additional_data)


def send_error_notification_if_needed():
    """Send error notification email if there are errors that warrant it."""
    if not _error_handler.should_send_error_email():
        return

    try:
        from .ui.email.client import send_email_notification
        from .ui.email.templates import EmailTemplates

        # Generate error report
        error_report = _error_handler.generate_error_report()

        # Determine severity for subject
        if _error_handler.has_critical_errors():
            severity = "🚨 CRITICAL"
            priority = "URGENT"
        elif _error_handler.has_trading_errors():
            severity = "💰 TRADING"
            priority = "HIGH"
        else:
            severity = "⚠️ SYSTEM"
            priority = "MEDIUM"

        # Build HTML email
        html_content = EmailTemplates.build_error_report(
            title=f"{severity} Alert - Trading System Errors", error_message=error_report
        )

        # Send notification
        success = send_email_notification(
            subject=f"[{priority}] The Alchemiser - {severity} Error Report",
            html_content=html_content,
            text_content=error_report,
        )

        if success:
            logging.info("Error notification email sent successfully")
        else:
            logging.error("Failed to send error notification email")

    except Exception as e:
        logging.error(f"Failed to send error notification: {e}")
