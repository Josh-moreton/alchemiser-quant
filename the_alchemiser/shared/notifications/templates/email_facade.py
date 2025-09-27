"""Business Unit: shared | Status: current.

Email template facade module.

This module provides a unified interface for email template generation functions
and classes used throughout the notification system. The functions in this module
serve as wrappers around the existing template builder classes.
"""

from __future__ import annotations

from typing import Any

from the_alchemiser.shared.schemas.common import MultiStrategyExecutionResultDTO
from the_alchemiser.shared.value_objects.core_types import (
    AccountInfo,
    EnrichedAccountInfo,
)

from ...constants import APPLICATION_NAME

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
    header = BaseEmailTemplate.get_header(APPLICATION_NAME)
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
    """Build a multi-strategy execution report email (neutral only).

    Legacy financial variant removed; this delegates to the neutral builder.
    """
    from .multi_strategy import MultiStrategyReportBuilder

    return MultiStrategyReportBuilder.build_multi_strategy_report_neutral(result, mode)


def build_trading_report_html(*_args: object, **_kwargs: object) -> str:  # Deprecated shim
    """Return deprecation notice for removed trading report (neutral mode only)."""
    return BaseEmailTemplate.wrap_content(
        BaseEmailTemplate.create_alert_box(
            "Trading report template deprecated - neutral mode only.", "warning"
        ),
        "The Alchemiser - Trading Report (Deprecated)",
    )


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
    def trading_report(*_args: object, **_kwargs: object) -> str:  # Deprecated
        """Return deprecated trading report notice (financial view removed)."""
        return build_trading_report_html()

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
        header = BaseEmailTemplate.get_header(APPLICATION_NAME)
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
    def _format_metric_value(metric_name: str, metric_value: int | float | str) -> str:
        """Format a metric value based on its name and type.

        Args:
            metric_name: Name of the metric for determining format
            metric_value: Value to format

        Returns:
            Formatted string representation of the value

        """
        if isinstance(metric_value, (int, float)):
            if "pct" in metric_name.lower() or "percent" in metric_name.lower():
                return f"{metric_value:.2%}"
            if "ratio" in metric_name.lower():
                return f"{metric_value:.2f}"
            return f"${metric_value:,.2f}"
        return str(metric_value)

    @staticmethod
    def _build_metrics_table(metrics: dict[str, int | float | str]) -> str:
        """Build the performance metrics table HTML.

        Args:
            metrics: Dictionary of metric names and values

        Returns:
            HTML string for the metrics table, or empty string if no metrics

        """
        if not metrics:
            return ""

        metrics_rows = ""
        for metric_name, metric_value in metrics.items():
            display_name = metric_name.replace("_", " ").title()
            formatted_value = EmailTemplates._format_metric_value(metric_name, metric_value)

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

        return f"""
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

    @staticmethod
    def _build_account_section(account_info: AccountInfo | EnrichedAccountInfo) -> str:
        """Build the account summary section.

        Args:
            account_info: Account information to display

        Returns:
            HTML string for the account section

        """
        from .portfolio import PortfolioBuilder

        return BaseEmailTemplate.create_section(
            "💰 Account Summary",
            PortfolioBuilder.build_account_summary_neutral(account_info),
        )

    @staticmethod
    def _build_strategy_performance_section(
        _strategy_summary: dict[str, Any],
    ) -> str:  # Deprecated
        return ""

    @staticmethod
    def _build_trading_activity_section(
        _trading_summary: dict[str, Any],
    ) -> str:  # Deprecated
        return ""

    @staticmethod
    def _build_summary_footer(period_label: str) -> str:
        """Build the summary footer section.

        Args:
            period_label: Label for the reporting period

        Returns:
            HTML string for the summary footer

        """
        return BaseEmailTemplate.create_alert_box(
            f"""
            <strong>📝 {period_label} Summary:</strong><br>
            • Portfolio performance and allocation changes reviewed<br>
            • All financial metrics calculated and reported<br>
            • Review detailed breakdowns above for strategic insights
            """,
            "info",
        )

    @staticmethod
    def monthly_performance_summary(*_args: object, **_kwargs: object) -> str:  # Deprecated
        """Return deprecated performance summary notice (neutral mode only)."""
        return BaseEmailTemplate.wrap_content(
            BaseEmailTemplate.create_alert_box(
                "Monthly performance summary deprecated - neutral mode only.", "info"
            ),
            "The Alchemiser - Performance Report (Deprecated)",
        )

    @staticmethod
    def monthly_financial_summary(summary: object, mode: str = "PAPER") -> str:
        """Generate monthly financial summary email.

        Args:
            summary: MonthlySummaryDTO with monthly performance data
            mode: Trading mode for display (PAPER/LIVE)

        Returns:
            Complete HTML email content

        """
        from .monthly import MonthlySummaryEmailBuilder

        return MonthlySummaryEmailBuilder.build(summary, mode)
