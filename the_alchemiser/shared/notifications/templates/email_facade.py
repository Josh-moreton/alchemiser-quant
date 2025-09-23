"""Business Unit: shared | Status: current.

Email template facade module.

This module provides a unified interface for email template generation functions
and classes used throughout the notification system. The functions in this module
serve as wrappers around the existing template builder classes.
"""

from __future__ import annotations

from typing import Any, cast

from the_alchemiser.shared.schemas.common import MultiStrategyExecutionResultDTO
from the_alchemiser.shared.value_objects.core_types import (
    AccountInfo,
    EnrichedAccountInfo,
)

# Import the base template and builder classes
from .base import BaseEmailTemplate


def build_error_email_html(title: str, message: str) -> str:
    """Build an error notification email.

    Args:
        title: Error title
        message: Error message

    Returns:
        Complete HTML email content

    """
    # Create error content using the existing base template functionality
    error_content = BaseEmailTemplate.create_alert_box(
        f"<strong>{title}</strong><br>{message}", "error"
    )

    # Build header and footer using existing base template methods
    header = BaseEmailTemplate.get_header()
    status_banner = BaseEmailTemplate.get_status_banner(title, "Error", "#EF4444", "❌")
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


def build_multi_strategy_email_html(
    result: MultiStrategyExecutionResultDTO, mode: str = "PAPER"
) -> str:
    """Build a multi-strategy execution report email.

    This function wraps the existing MultiStrategyReportBuilder.build_multi_strategy_report method.

    Args:
        result: Execution result object
        mode: Trading mode (PAPER, LIVE, etc.)

    Returns:
        Complete HTML email content

    """
    # Use the existing multi-strategy builder
    from .multi_strategy import MultiStrategyReportBuilder

    return MultiStrategyReportBuilder.build_multi_strategy_report(result, mode)


def build_trading_report_html(
    trading_summary: dict[str, object],
    strategy_signals: dict[str, object] | None = None,
    account_info: dict[str, object] | None = None,
) -> str:
    """Build a general trading report email.

    This function combines existing builder methods to create a comprehensive trading report.

    Args:
        trading_summary: Summary of trading activity
        strategy_signals: Optional strategy signals data
        account_info: Optional account information

    Returns:
        Complete HTML email content

    """
    # Import the existing builders
    from .performance import PerformanceBuilder
    from .portfolio import PortfolioBuilder
    from .signals import SignalsBuilder

    # Build content sections using existing template methods
    header = BaseEmailTemplate.get_header()
    status_banner = BaseEmailTemplate.get_status_banner(
        "Trading Report", "Complete", "#10B981", "✅"
    )

    content_sections = []

    # Trading summary using existing performance builder
    if trading_summary:
        trading_html = PerformanceBuilder.build_trading_summary(trading_summary)
        content_sections.append(trading_html)

    # Strategy signals using existing signals builder
    if strategy_signals:
        signals_html = SignalsBuilder.build_technical_indicators(strategy_signals)
        content_sections.append(signals_html)

    # Account summary using existing portfolio builder
    if account_info:
        account_html = BaseEmailTemplate.create_section(
            "💰 Account Summary",
            PortfolioBuilder.build_account_summary(
                cast(AccountInfo | EnrichedAccountInfo, account_info)
            ),
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
    of email templates used throughout the system. It serves as a facade over
    the existing template builder classes.
    """

    @staticmethod
    def error_notification(title: str, message: str) -> str:
        """Generate an error notification email using existing template infrastructure."""
        return build_error_email_html(title, message)

    @staticmethod
    def build_error_report(title: str, error_message: str) -> str:
        """Generate an error report email (alias for error_notification for compatibility)."""
        return build_error_email_html(title, error_message)

    @staticmethod
    def trading_report(
        trading_summary: dict[str, object],
        strategy_signals: dict[str, object] | None = None,
        account_info: dict[str, object] | None = None,
    ) -> str:
        """Generate a general trading report using existing builder classes."""
        return build_trading_report_html(trading_summary, strategy_signals, account_info)

    # ================ NEW EMAIL TEMPLATES (Issue #1038) ================

    @staticmethod
    def successful_trading_run(
        result: MultiStrategyExecutionResultDTO,
        mode: str = "PAPER",
    ) -> str:
        """Generate successful trading run email - neutral mode with no dollar values.

        This template shows portfolio rebalancing plan and trades made without exposing
        financial values, keeping the output neutral for security/privacy.

        Args:
            result: Execution result containing trading data
            mode: Trading mode (PAPER/LIVE)

        Returns:
            HTML email content for successful trading run

        """
        from .multi_strategy import MultiStrategyReportBuilder

        return MultiStrategyReportBuilder.build_multi_strategy_report_neutral(result, mode)

    @staticmethod
    def failed_trading_run(
        error_details: str,
        mode: str = "PAPER",
        context: dict[str, object] | None = None,
    ) -> str:
        """Generate failed trading run email with error summary.

        This template provides structured error reporting for failed trading runs,
        including context and actionable information.

        Args:
            error_details: Main error message or summary
            mode: Trading mode (PAPER/LIVE)
            context: Additional context information about the failure

        Returns:
            HTML email content for failed trading run

        """
        header = BaseEmailTemplate.get_header()
        status_banner = BaseEmailTemplate.get_status_banner(
            f"{mode.upper()} Trading Run Failed", "Failed", "#EF4444", "❌"
        )

        content_sections = []

        # Main error section
        error_content = BaseEmailTemplate.create_alert_box(
            f"<strong>Trading Execution Failed</strong><br>{error_details}", "error"
        )
        content_sections.append(error_content)

        # Context section if provided
        if context:
            context_rows = ""
            for key, value in context.items():
                if value is not None:
                    context_rows += f"""
                    <tr>
                        <td style="padding: 8px 12px; border-bottom: 1px solid #E5E7EB; font-weight: 600;">
                            {key.replace("_", " ").title()}:
                        </td>
                        <td style="padding: 8px 12px; border-bottom: 1px solid #E5E7EB;">
                            {value}
                        </td>
                    </tr>
                    """

            if context_rows:
                context_html = f"""
                <div style="margin-top: 24px;">
                    <h3 style="margin: 0 0 16px 0; color: #1F2937; font-size: 18px; font-weight: 600;">
                        📋 Execution Context
                    </h3>
                    <table style="width: 100%; border-collapse: collapse; background-color: white; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);">
                        <tbody>
                            {context_rows}
                        </tbody>
                    </table>
                </div>
                """
                content_sections.append(context_html)

        # Action items section
        action_html = BaseEmailTemplate.create_alert_box(
            """
            <strong>🔧 Recommended Actions:</strong><br>
            • Check application logs for detailed error information<br>
            • Verify broker connectivity and account status<br>
            • Review strategy configurations and market conditions<br>
            • Contact support if the issue persists
            """,
            "warning",
        )
        content_sections.append(action_html)

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

        return BaseEmailTemplate.wrap_content(
            content, f"The Alchemiser - {mode.upper()} Trading Failed"
        )

    @staticmethod
    def monthly_performance_summary(
        account_info: AccountInfo | EnrichedAccountInfo,
        performance_data: dict[str, Any] | None = None,
        period_label: str = "Monthly",
    ) -> str:
        """Generate monthly performance summary with full financial details.

        This template includes dollar values, P&L, and comprehensive account performance
        metrics for regular performance reporting.

        Args:
            account_info: Current account information with financial details
            performance_data: Optional performance metrics and analytics
            period_label: Label for the reporting period (e.g., "Monthly", "Quarterly")

        Returns:
            HTML email content for performance summary

        """
        from .performance import PerformanceBuilder
        from .portfolio import PortfolioBuilder

        header = BaseEmailTemplate.get_header()
        status_banner = BaseEmailTemplate.get_status_banner(
            f"{period_label} Performance Report", "Complete", "#10B981", "📊"
        )

        content_sections = []

        # Account summary with full financial details
        account_html = BaseEmailTemplate.create_section(
            "💰 Account Summary", PortfolioBuilder.build_account_summary(account_info)
        )
        content_sections.append(account_html)

        # Performance metrics if available
        if performance_data:
            # Strategy performance
            strategy_summary = performance_data.get("strategy_summary", {})
            if strategy_summary:
                strategy_html = BaseEmailTemplate.create_section(
                    "📈 Strategy Performance",
                    PerformanceBuilder.build_strategy_performance(strategy_summary),
                )
                content_sections.append(strategy_html)

            # Trading activity summary
            trading_summary = performance_data.get("trading_summary", {})
            if trading_summary:
                trading_html = BaseEmailTemplate.create_section(
                    "💼 Trading Activity",
                    PerformanceBuilder.build_trading_summary(trading_summary),
                )
                content_sections.append(trading_html)

            # Performance metrics table
            metrics = performance_data.get("metrics", {})
            if metrics:
                metrics_rows = ""
                for metric_name, metric_value in metrics.items():
                    display_name = metric_name.replace("_", " ").title()
                    if isinstance(metric_value, (int, float)):
                        if "pct" in metric_name.lower() or "percent" in metric_name.lower():
                            formatted_value = f"{metric_value:.2%}"
                        elif "ratio" in metric_name.lower():
                            formatted_value = f"{metric_value:.2f}"
                        else:
                            formatted_value = f"${metric_value:,.2f}"
                    else:
                        formatted_value = str(metric_value)

                    metrics_rows += f"""
                    <tr>
                        <td style="padding: 8px 12px; border-bottom: 1px solid #E5E7EB; font-weight: 600;">
                            {display_name}:
                        </td>
                        <td style="padding: 8px 12px; border-bottom: 1px solid #E5E7EB; text-align: right;">
                            {formatted_value}
                        </td>
                    </tr>
                    """

                if metrics_rows:
                    metrics_html = f"""
                    <div style="margin-top: 24px;">
                        <h3 style="margin: 0 0 16px 0; color: #1F2937; font-size: 18px; font-weight: 600;">
                            📊 Performance Metrics
                        </h3>
                        <table style="width: 100%; border-collapse: collapse; background-color: white; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);">
                            <tbody>
                                {metrics_rows}
                            </tbody>
                        </table>
                    </div>
                    """
                    content_sections.append(metrics_html)

        # Summary footer with key takeaways
        summary_html = BaseEmailTemplate.create_alert_box(
            f"""
            <strong>📝 {period_label} Summary:</strong><br>
            • Portfolio performance and allocation changes reviewed<br>
            • All financial metrics calculated and reported<br>
            • Review detailed breakdowns above for strategic insights
            """,
            "info",
        )
        content_sections.append(summary_html)

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

        return BaseEmailTemplate.wrap_content(
            content, f"The Alchemiser - {period_label} Performance Report"
        )
