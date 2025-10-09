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

        Raises:
            ValueError: If mode is not PAPER or LIVE

        """
        # Validate mode parameter
        mode_upper = mode.upper()
        if mode_upper not in ("PAPER", "LIVE"):
            raise ValueError(f"Invalid mode '{mode}'. Must be 'PAPER' or 'LIVE'.")

        # Create header with status
        header = BaseEmailTemplate.get_combined_header_status(
            f"{mode_upper} Monthly Summary — {summary.month_label}", "Completed", "#3B82F6", "📅"
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

        return BaseEmailTemplate.wrap_content(
            content, f"The Alchemiser — {mode_upper} Monthly Summary ({summary.month_label})"
        )

    @staticmethod
    def _build_portfolio_section(summary: MonthlySummaryDTO) -> str:
        """Build the portfolio P&L section.

        Args:
            summary: Monthly summary data

        Returns:
            HTML string for portfolio section

        """
        # Check if we have portfolio data
        if (
            summary.portfolio_first_value is None
            or summary.portfolio_last_value is None
            or summary.portfolio_pnl_abs is None
            or summary.portfolio_pnl_pct is None
        ):
            return BaseEmailTemplate.create_alert_box(
                "<strong>⚠️ Portfolio Data Unavailable</strong><br>"
                "Unable to calculate monthly P&L — insufficient account snapshots.",
                "warning",
            )

        # Format values
        first_val = f"${summary.portfolio_first_value:,.2f}"
        last_val = f"${summary.portfolio_last_value:,.2f}"
        pnl_abs = summary.portfolio_pnl_abs
        pnl_pct = summary.portfolio_pnl_pct

        # Determine color and sign for P&L
        if pnl_abs > 0:
            pnl_color = "#10B981"  # Green
            pnl_sign = "+"
        elif pnl_abs < 0:
            pnl_color = "#EF4444"  # Red
            pnl_sign = ""
        else:
            pnl_color = "#6B7280"  # Gray
            pnl_sign = ""

        pnl_abs_str = f"{pnl_sign}${pnl_abs:,.2f}"
        pnl_pct_str = f"({pnl_sign}{pnl_pct:.2f}%)"

        return f"""
        <div style="margin-bottom: 24px;">
            <h3 style="margin: 0 0 16px 0; color: #1F2937; font-size: 18px; font-weight: 600;">
                💰 Portfolio Summary — {summary.month_label}
            </h3>
            <table style="width: 100%; border-collapse: collapse; background-color: #F9FAFB; border-radius: 8px; overflow: hidden;">
                <tbody>
                    <tr>
                        <td style="padding: 12px 16px; border-bottom: 1px solid #E5E7EB; font-weight: 600; color: #374151;">
                            Start of Month
                        </td>
                        <td style="padding: 12px 16px; border-bottom: 1px solid #E5E7EB; text-align: right; color: #1F2937;">
                            {first_val}
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 12px 16px; border-bottom: 1px solid #E5E7EB; font-weight: 600; color: #374151;">
                            End of Month
                        </td>
                        <td style="padding: 12px 16px; border-bottom: 1px solid #E5E7EB; text-align: right; color: #1F2937;">
                            {last_val}
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 12px 16px; font-weight: 600; color: #374151;">
                            Monthly P&L
                        </td>
                        <td style="padding: 12px 16px; text-align: right; font-weight: 700; color: {pnl_color};">
                            {pnl_abs_str} {pnl_pct_str}
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>
        """

    @staticmethod
    def _build_strategy_section(summary: MonthlySummaryDTO) -> str:
        """Build the per-strategy P&L section.

        Args:
            summary: Monthly summary data

        Returns:
            HTML string for strategy section

        """
        if not summary.strategy_rows:
            return BaseEmailTemplate.create_alert_box(
                "<strong>📊 No Strategy Activity</strong><br>"
                "No closed trades recorded this month.",
                "info",
            )

        # Build table rows
        rows_html = ""
        for row in summary.strategy_rows:
            strategy_name = row.get("strategy_name", "Unknown")
            realized_pnl = row.get("realized_pnl", Decimal("0"))
            realized_trades = row.get("realized_trades", 0)

            # Determine color and sign for P&L
            if realized_pnl > 0:
                pnl_color = "#10B981"  # Green
                pnl_sign = "+"
            elif realized_pnl < 0:
                pnl_color = "#EF4444"  # Red
                pnl_sign = ""
            else:
                pnl_color = "#6B7280"  # Gray
                pnl_sign = ""

            pnl_str = f"{pnl_sign}${realized_pnl:,.2f}"

            rows_html += f"""
            <tr>
                <td style="padding: 12px 16px; border-bottom: 1px solid #E5E7EB; font-weight: 600; color: #374151;">
                    {strategy_name}
                </td>
                <td style="padding: 12px 16px; border-bottom: 1px solid #E5E7EB; text-align: center; color: #1F2937;">
                    {realized_trades}
                </td>
                <td style="padding: 12px 16px; border-bottom: 1px solid #E5E7EB; text-align: right; font-weight: 600; color: {pnl_color};">
                    {pnl_str}
                </td>
            </tr>
            """

        return f"""
        <div style="margin-bottom: 24px;">
            <h3 style="margin: 0 0 16px 0; color: #1F2937; font-size: 18px; font-weight: 600;">
                📊 Strategy Performance — {summary.month_label}
            </h3>
            <table style="width: 100%; border-collapse: collapse; background-color: #F9FAFB; border-radius: 8px; overflow: hidden;">
                <thead>
                    <tr style="background-color: #E5E7EB;">
                        <th style="padding: 12px 16px; text-align: left; font-weight: 700; color: #1F2937;">
                            Strategy
                        </th>
                        <th style="padding: 12px 16px; text-align: center; font-weight: 700; color: #1F2937;">
                            Trades
                        </th>
                        <th style="padding: 12px 16px; text-align: right; font-weight: 700; color: #1F2937;">
                            Realized P&L
                        </th>
                    </tr>
                </thead>
                <tbody>
                    {rows_html}
                </tbody>
            </table>
        </div>
        """

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
