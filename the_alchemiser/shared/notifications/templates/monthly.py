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
            f"Monthly Summary — {summary.month_label}", "Completed", "#3B82F6", "📅"
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
            content, f"The Alchemiser — Monthly Summary ({summary.month_label})"
        )

    @staticmethod
    def _build_portfolio_section(summary: MonthlySummaryDTO) -> str:
        """Build the portfolio performance section.

        Args:
            summary: Monthly summary data

        Returns:
            HTML string for portfolio section

        """
        # Handle case where portfolio data is missing
        if summary.portfolio_first_value is None or summary.portfolio_last_value is None:
            return BaseEmailTemplate.create_alert_box(
                "<strong>⚠️ No Portfolio Data:</strong><br>"
                "No account value snapshots found for this month. "
                "Portfolio P&L cannot be calculated.",
                "warning",
            )

        # Format values for display
        first_val = summary.portfolio_first_value
        last_val = summary.portfolio_last_value
        pnl_abs = summary.portfolio_pnl_abs or Decimal("0")
        pnl_pct = summary.portfolio_pnl_pct or Decimal("0")

        # Determine color based on P&L
        pnl_color = "#10B981" if pnl_abs >= 0 else "#EF4444"
        pnl_sign = "+" if pnl_abs >= 0 else ""

        portfolio_html = f"""
        <div style="margin: 0 0 32px 0;">
            <h3 style="margin: 0 0 16px 0; color: #1F2937; font-size: 18px; font-weight: 600; letter-spacing: 0.3px;">
                Portfolio P&L
            </h3>
            <table style="width: 100%; border-collapse: collapse; background-color: white; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);">
                <tbody>
                    <tr>
                        <td style="padding: 14px 16px; border-bottom: 1px solid #E5E7EB; font-weight: 600; color: #374151; width: 50%;">
                            Start of Month
                        </td>
                        <td style="padding: 14px 16px; border-bottom: 1px solid #E5E7EB; color: #1F2937; text-align: right;">
                            ${first_val:,.2f}
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 14px 16px; border-bottom: 1px solid #E5E7EB; font-weight: 600; color: #374151;">
                            End of Month
                        </td>
                        <td style="padding: 14px 16px; border-bottom: 1px solid #E5E7EB; color: #1F2937; text-align: right;">
                            ${last_val:,.2f}
                        </td>
                    </tr>
                    <tr style="background-color: #F9FAFB;">
                        <td style="padding: 14px 16px; font-weight: 700; color: #111827; font-size: 16px;">
                            Change
                        </td>
                        <td style="padding: 14px 16px; text-align: right; font-weight: 700; color: {pnl_color}; font-size: 16px;">
                            {pnl_sign}${pnl_abs:,.2f} ({pnl_sign}{pnl_pct:.2f}%)
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>
        """

        return portfolio_html

    @staticmethod
    def _build_strategy_section(summary: MonthlySummaryDTO) -> str:
        """Build the per-strategy performance section.

        Args:
            summary: Monthly summary data

        Returns:
            HTML string for strategy section

        """
        if not summary.strategy_rows:
            return BaseEmailTemplate.create_alert_box(
                "<strong>ℹ️ No Strategy Data:</strong><br>"
                "No realized trades found for this month.",
                "info",
            )

        # Build strategy rows
        strategy_rows_html = ""
        for row in summary.strategy_rows:
            strategy_name = row.get("strategy_name", "Unknown")
            realized_pnl = row.get("realized_pnl", Decimal("0"))
            realized_trades = row.get("realized_trades", 0)

            # Determine color based on P&L
            pnl_color = "#10B981" if realized_pnl >= 0 else "#EF4444"
            pnl_sign = "+" if realized_pnl >= 0 else ""

            strategy_rows_html += f"""
            <tr>
                <td style="padding: 12px 16px; border-bottom: 1px solid #E5E7EB; font-weight: 600; color: #374151;">
                    {strategy_name}
                </td>
                <td style="padding: 12px 16px; border-bottom: 1px solid #E5E7EB; color: {pnl_color}; text-align: right; font-weight: 600;">
                    {pnl_sign}${realized_pnl:,.2f}
                </td>
                <td style="padding: 12px 16px; border-bottom: 1px solid #E5E7EB; color: #6B7280; text-align: right;">
                    {realized_trades} trades
                </td>
            </tr>
            """

        strategy_html = f"""
        <div style="margin: 0 0 32px 0;">
            <h3 style="margin: 0 0 16px 0; color: #1F2937; font-size: 18px; font-weight: 600; letter-spacing: 0.3px;">
                Realized P&L by Strategy
            </h3>
            <table style="width: 100%; border-collapse: collapse; background-color: white; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);">
                <thead>
                    <tr style="background-color: #F9FAFB;">
                        <th style="padding: 12px 16px; text-align: left; font-weight: 600; color: #374151; border-bottom: 2px solid #E5E7EB;">
                            Strategy
                        </th>
                        <th style="padding: 12px 16px; text-align: right; font-weight: 600; color: #374151; border-bottom: 2px solid #E5E7EB;">
                            Realized P&L
                        </th>
                        <th style="padding: 12px 16px; text-align: right; font-weight: 600; color: #374151; border-bottom: 2px solid #E5E7EB;">
                            Trades
                        </th>
                    </tr>
                </thead>
                <tbody>
                    {strategy_rows_html}
                </tbody>
            </table>
        </div>
        """

        return strategy_html

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
