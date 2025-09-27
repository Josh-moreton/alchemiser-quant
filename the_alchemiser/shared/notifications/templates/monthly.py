#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Monthly Summary Email Template Builder.

This module provides email template building for monthly portfolio and strategy
performance summaries, following the existing BaseEmailTemplate patterns.
"""

from __future__ import annotations

from decimal import Decimal

from ...schemas.reporting import MonthlySummaryDTO
from .base import BaseEmailTemplate


class MonthlySummaryEmailBuilder:
    """Builder for monthly summary email templates."""

    @staticmethod
    def build(summary: MonthlySummaryDTO, mode: str = "PAPER") -> str:
        """Build HTML email content for monthly summary.

        Args:
            summary: Monthly summary data
            mode: Trading mode for display (PAPER/LIVE)

        Returns:
            Complete HTML email content

        """
        # Create header with status
        header = BaseEmailTemplate.get_combined_header_status(
            f"Monthly Summary — {summary.month_label}",
            "Completed",
            "#3B82F6",
            "📅"
        )

        # Build main content sections
        portfolio_section = MonthlySummaryEmailBuilder._build_portfolio_section(summary)
        strategy_section = MonthlySummaryEmailBuilder._build_strategy_section(summary)
        footer_section = MonthlySummaryEmailBuilder._build_methodology_footer(summary.month_label)

        # Combine all sections
        content = f"""
            {header}
            <tr>
                <td style="padding: 24px; background-color: white;">
                    {portfolio_section}
                    {strategy_section}
                    {footer_section}
                </td>
            </tr>
            {BaseEmailTemplate.get_footer()}
        """

        return BaseEmailTemplate.wrap_content(content, f"The Alchemiser — Monthly Summary ({summary.month_label})")

    @staticmethod
    def _build_portfolio_section(summary: MonthlySummaryDTO) -> str:
        """Build the portfolio P&L section.

        Args:
            summary: Monthly summary data

        Returns:
            HTML string for portfolio section

        """
        if summary.portfolio_first_value is None and summary.portfolio_last_value is None:
            # No data available
            content = BaseEmailTemplate.create_alert_box(
                "No account value snapshots found for this month. Portfolio P&L cannot be calculated.",
                "warning"
            )
        elif summary.portfolio_first_value is None or summary.portfolio_last_value is None:
            # Only one snapshot
            value = summary.portfolio_first_value or summary.portfolio_last_value
            content = f"""
                <div style="display: flex; justify-content: space-between; align-items: center; margin: 16px 0;">
                    <div>
                        <p style="margin: 0; font-size: 16px; color: #6B7280;">Portfolio Value</p>
                        <p style="margin: 4px 0 0 0; font-size: 24px; font-weight: 600; color: #1F2937;">
                            ${value:,.2f}
                        </p>
                    </div>
                </div>
                {BaseEmailTemplate.create_alert_box(
                    "Only one account value snapshot found. Percentage change not calculated.",
                    "info"
                )}
            """
        else:
            # Full P&L calculation
            abs_change = summary.portfolio_pnl_abs or Decimal("0")
            pct_change = summary.portfolio_pnl_pct

            # Determine color based on P&L
            if abs_change > 0:
                pnl_color = "#10B981"  # Green
                pnl_icon = "📈"
            elif abs_change < 0:
                pnl_color = "#EF4444"  # Red
                pnl_icon = "📉"
            else:
                pnl_color = "#6B7280"  # Gray
                pnl_icon = "-"

            # Format percentage display
            pct_display = f" ({pct_change:+.2f}%)" if pct_change is not None else ""

            content = f"""
                <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 16px; margin: 16px 0;">
                    <div style="text-align: center; padding: 16px; background-color: #F9FAFB; border-radius: 8px;">
                        <p style="margin: 0; font-size: 14px; color: #6B7280;">Start of Month</p>
                        <p style="margin: 4px 0 0 0; font-size: 18px; font-weight: 600; color: #1F2937;">
                            ${summary.portfolio_first_value:,.2f}
                        </p>
                    </div>
                    <div style="text-align: center; padding: 16px; background-color: #F9FAFB; border-radius: 8px;">
                        <p style="margin: 0; font-size: 14px; color: #6B7280;">End of Month</p>
                        <p style="margin: 4px 0 0 0; font-size: 18px; font-weight: 600; color: #1F2937;">
                            ${summary.portfolio_last_value:,.2f}
                        </p>
                    </div>
                    <div style="text-align: center; padding: 16px; background-color: #F9FAFB; border-radius: 8px;">
                        <p style="margin: 0; font-size: 14px; color: #6B7280;">Change</p>
                        <p style="margin: 4px 0 0 0; font-size: 18px; font-weight: 600; color: {pnl_color};">
                            {pnl_icon} ${abs_change:+,.2f}{pct_display}
                        </p>
                    </div>
                </div>
            """

        return BaseEmailTemplate.create_section("💰 Portfolio P&L", content)

    @staticmethod
    def _build_strategy_section(summary: MonthlySummaryDTO) -> str:
        """Build the strategy performance section.

        Args:
            summary: Monthly summary data

        Returns:
            HTML string for strategy section

        """
        if not summary.strategy_rows:
            content = BaseEmailTemplate.create_alert_box(
                "No strategy trading activity found for this month.",
                "info"
            )
        else:
            # Build strategy performance table
            headers = ["Strategy", "Realized P&L ($)", "Trades"]
            rows = []

            for row in summary.strategy_rows:
                strategy_name = row["strategy_name"]
                realized_pnl = row["realized_pnl"]
                realized_trades = row["realized_trades"]

                # Format P&L with color
                if realized_pnl > 0:
                    pnl_display = f'<span style="color: #10B981; font-weight: 600;">+${realized_pnl:,.2f}</span>'
                elif realized_pnl < 0:
                    pnl_display = f'<span style="color: #EF4444; font-weight: 600;">${realized_pnl:,.2f}</span>'
                else:
                    pnl_display = '<span style="color: #6B7280;">$0.00</span>'

                rows.append([
                    strategy_name,
                    pnl_display,
                    str(realized_trades),
                ])

            content = BaseEmailTemplate.create_table(headers, rows, "strategy-performance")

        return BaseEmailTemplate.create_section("📊 Realized P&L by Strategy", content)

    @staticmethod
    def _build_methodology_footer(month_label: str) -> str:
        """Build the methodology and notes footer.

        Args:
            month_label: Month label for display

        Returns:
            HTML string for methodology footer

        """
        return BaseEmailTemplate.create_alert_box(
            f"""
            <strong>📝 {month_label} Summary Methodology:</strong><br>
            • Portfolio P&L calculated from account value snapshots (first vs last value of month)<br>
            • Strategy P&L shows realized gains/losses in dollars only<br>
            • Per-strategy percentages omitted to avoid misleading figures without clear capital base<br>
            • All calculations use UTC-based month windows and Decimal precision
            """,
            "info",
        )