"""Business Unit: order execution/placement; Status: current.

Main trading report template builder.

This module handles the primary trading report email template generation.
"""

from typing import Any, cast

from the_alchemiser.domain.types import AccountInfo, EnrichedAccountInfo, PositionInfo

from .base import BaseEmailTemplate
from .performance import PerformanceBuilder
from .portfolio import PortfolioBuilder
from .signals import SignalsBuilder


class TradingReportBuilder:
    """Builds trading report email templates."""

    @staticmethod
    def build_regular_report(
        mode: str,
        success: bool,
        account_before: AccountInfo | EnrichedAccountInfo,
        account_after: AccountInfo | EnrichedAccountInfo,
        positions: dict[str, Any],
        orders: list[dict[str, Any]] | None = None,
        signal: Any = None,
        portfolio_history: dict[str, Any] | None = None,
        open_positions: list[dict[str, Any]] | None = None,
    ) -> str:
        """Build a comprehensive HTML trading report email."""
        # Determine status styling
        status_color = "#10B981" if success else "#EF4444"
        status_emoji = "✅" if success else "❌"
        status_text = "Success" if success else "Failed"

        # Build content sections
        header = BaseEmailTemplate.get_header("The Alchemiser")
        status_banner = BaseEmailTemplate.get_status_banner(
            f"{mode.upper()} Trading Report", status_text, status_color, status_emoji
        )

        # Account summary
        account_summary_html = BaseEmailTemplate.create_section(
            "💰 Account Summary", PortfolioBuilder.build_account_summary(account_after)
        )

        # Signal information
        signal_html = SignalsBuilder.build_signal_information(signal)

        # Trading activity
        trading_html = PerformanceBuilder.build_trading_activity(orders)

        # Open positions
        positions_html = ""
        if open_positions:
            positions_html = BaseEmailTemplate.create_section(
                "📊 Open Positions",
                PortfolioBuilder.build_positions_table(cast(list[PositionInfo], open_positions)),
            )

        # Closed positions P&L
        closed_pnl_html = ""
        if account_after and account_after.get("recent_closed_pnl"):
            closed_pnl_html = PortfolioBuilder.build_closed_positions_pnl(account_after)

        # Error section if needed
        error_html = ""
        if not success:
            error_html = BaseEmailTemplate.create_alert_box(
                "⚠️ Check logs for error details", "error"
            )

        footer = BaseEmailTemplate.get_footer()

        # Combine all content
        content = f"""
        {header}
        {status_banner}
        <tr>
            <td style="padding: 32px 24px; background-color: white;">
                {account_summary_html}
                {signal_html}
                {trading_html}
                {positions_html}
                {closed_pnl_html}
                {error_html}
            </td>
        </tr>
        {footer}
        """

        return BaseEmailTemplate.wrap_content(content, "The Alchemiser - Trading Report")

    @staticmethod
    def build_neutral_report(
        mode: str,
        success: bool,
        account_before: AccountInfo | EnrichedAccountInfo,
        account_after: AccountInfo | EnrichedAccountInfo,
        positions: dict[str, Any],
        orders: list[dict[str, Any]] | None = None,
        signal: Any = None,
        portfolio_history: dict[str, Any] | None = None,
        open_positions: list[dict[str, Any]] | None = None,
    ) -> str:
        """Build a neutral HTML trading report email without dollar values or percentages."""
        # Determine status styling
        status_color = "#10B981" if success else "#EF4444"
        status_emoji = "✅" if success else "❌"
        status_text = "Success" if success else "Failed"

        # Build content sections
        header = BaseEmailTemplate.get_header("The Alchemiser")
        status_banner = BaseEmailTemplate.get_status_banner(
            f"{mode.upper()} Trading Report - Neutral Mode", status_text, status_color, status_emoji
        )

        # Account summary (neutral mode)
        account_summary_html = BaseEmailTemplate.create_section(
            "⚙️ Account Status", PortfolioBuilder.build_account_summary_neutral(account_after)
        )

        # Signal information (same as regular, no dollar values there)
        signal_html = SignalsBuilder.build_signal_information(signal)

        # Trading activity (neutral mode)
        trading_html = PerformanceBuilder.build_trading_activity_neutral(orders)

        # Open positions (neutral mode)
        positions_html = ""
        if open_positions:
            positions_html = BaseEmailTemplate.create_section(
                "📊 Current Holdings",
                PortfolioBuilder.build_positions_table_neutral(
                    cast(list[PositionInfo], open_positions)
                ),
            )

        # Skip closed positions P&L in neutral mode

        # Error section if needed
        error_html = ""
        if not success:
            error_html = BaseEmailTemplate.create_alert_box(
                "⚠️ Check logs for error details", "error"
            )

        footer = BaseEmailTemplate.get_footer()

        # Combine all content
        content = f"""
        {header}
        {status_banner}
        <tr>
            <td style="padding: 32px 24px; background-color: white;">
                {account_summary_html}
                {signal_html}
                {trading_html}
                {positions_html}
                {error_html}
            </td>
        </tr>
        {footer}
        """

        return BaseEmailTemplate.wrap_content(content, "The Alchemiser - Trading Report (Neutral)")
