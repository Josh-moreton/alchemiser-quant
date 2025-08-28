"""Business Unit: utilities; Status: current.

Error report template builder.

This module handles error notification email template generation.
"""

from __future__ import annotations

# ✅ Phase 14 - Error handler types enabled
from .base import BaseEmailTemplate


class ErrorReportBuilder:
    """Builds error notification email templates."""

    @staticmethod
    def build_error_report(
        title: str, error_message: str
    ) -> (
        str
    ):  # ✅ Phase 14 - Current signature compatible, could accept ErrorNotificationData in future
        """Build an error alert email."""
        header = BaseEmailTemplate.get_header("The Alchemiser")
        status_banner = BaseEmailTemplate.get_status_banner(title, "Error", "#EF4444", "❌")

        # Check if error_message is structured (contains markdown headers)
        if error_message.startswith("# Trading System Error Report"):
            # Structured error report - convert markdown to HTML
            formatted_error = error_message.replace("\n", "<br>")
            formatted_error = formatted_error.replace(
                "# ", "<h2 style='color: #1F2937; margin: 24px 0 16px 0;'>"
            )
            formatted_error = formatted_error.replace(
                "## ", "<h3 style='color: #374151; margin: 20px 0 12px 0;'>"
            )
            formatted_error = formatted_error.replace("**", "<strong>")
            formatted_error = formatted_error.replace("</strong>", "</strong>")

            error_content = f"""
            <div style="margin: 24px 0;">
                <div style="background-color: white; border-radius: 8px; padding: 20px; border-left: 4px solid #EF4444; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                    <div style="color: #374151; font-size: 14px; line-height: 1.6;">
                        {formatted_error}
                    </div>
                </div>
            </div>
            """
        else:
            # Simple error message
            formatted_error = error_message.replace("\n", "<br>")

            error_content = f"""
            <div style="margin: 24px 0;">
                <h3 style="margin: 0 0 16px 0; color: #1F2937; font-size: 18px; font-weight: 600;">🚨 Error Details</h3>
                <div style="background-color: white; border-radius: 8px; padding: 20px; border-left: 4px solid #EF4444; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                    <div style="color: #DC2626; font-family: 'Courier New', monospace; font-size: 14px; line-height: 1.5; white-space: pre-wrap;">
                        {formatted_error}
                    </div>
                </div>
            </div>
            """

        # Add troubleshooting tips
        tips_content = """
        <div style="margin: 24px 0;">
            <h3 style="margin: 0 0 16px 0; color: #1F2937; font-size: 18px; font-weight: 600;">💡 Troubleshooting Tips</h3>
            <div style="background-color: #FEF3C7; border-radius: 8px; padding: 16px; border-left: 4px solid #F59E0B;">
                <ul style="margin: 0; padding-left: 20px; color: #92400E;">
                    <li>Check system logs for additional error details</li>
                    <li>Verify API credentials and network connectivity</li>
                    <li>Ensure market hours are within trading schedule</li>
                    <li>Review configuration settings for accuracy</li>
                    <li>Contact support if the issue persists</li>
                </ul>
            </div>
        </div>
        """

        footer = BaseEmailTemplate.get_footer()

        # Combine all content
        content = f"""
        {header}
        {status_banner}
        <tr>
            <td style="padding: 32px 24px; background-color: white;">
                {error_content}
                {tips_content}
            </td>
        </tr>
        {footer}
        """

        return BaseEmailTemplate.wrap_content(content, f"The Alchemiser - {title}")
