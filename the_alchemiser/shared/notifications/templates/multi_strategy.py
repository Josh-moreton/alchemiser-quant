"""Business Unit: strategy & signal generation; Status: current.

Multi-strategy report template builder.

This module handles the multi-strategy email template generation.
"""

from __future__ import annotations

from ...constants import APPLICATION_NAME
from .base import BaseEmailTemplate
from .portfolio import ExecutionLike, PortfolioBuilder
from .signals import SignalsBuilder


class MultiStrategyReportBuilder:
    """Builds multi-strategy email templates (neutral mode only).

    Non-neutral (financial value) variant removed - system policy mandates
    neutral reporting only. Historical build_multi_strategy_report() deleted
    to simplify maintenance and avoid accidental financial disclosure.
    """

    @staticmethod
    def build_multi_strategy_report_neutral(result: ExecutionLike, mode: str) -> str:
        """Build a neutral multi-strategy email report without financial values."""
        # Determine success status
        success = getattr(result, "success", True)
        status_color = "#10B981" if success else "#EF4444"
        status_emoji = "✅" if success else "❌"
        status_text = "Success" if success else "Failed"

        # Build content sections
        combined_header = BaseEmailTemplate.get_combined_header_status(
            f"{mode.upper()} Multi-Strategy Report",
            status_text,
            status_color,
            status_emoji,
        )

        # Get strategy signals for market regime and signals
        strategy_signals = getattr(result, "strategy_signals", {})

        # Build content sections (neutral mode - no financial data)
        content_sections = []

        # Portfolio rebalancing table (percentages only)
        rebalancing_html = BaseEmailTemplate.create_section(
            "🔄 Portfolio Rebalancing",
            PortfolioBuilder.build_portfolio_rebalancing_table(result),
        )
        content_sections.append(rebalancing_html)

        # Market regime analysis (no financial data)
        market_regime_html = SignalsBuilder.build_market_regime_analysis(strategy_signals)
        if market_regime_html:
            content_sections.append(market_regime_html)

        # Strategy signals (neutral mode)
        if strategy_signals:
            neutral_signals_html = SignalsBuilder.build_strategy_signals_neutral(strategy_signals)
            content_sections.append(neutral_signals_html)

        # Orders executed (detailed table, no values)
        orders = getattr(result, "orders_executed", [])
        if orders:
            orders_table_html = PortfolioBuilder.build_orders_table_neutral(orders)
            neutral_orders_html = BaseEmailTemplate.create_section(
                "📋 Trading Activity", orders_table_html
            )
            content_sections.append(neutral_orders_html)
        else:
            neutral_orders_html = BaseEmailTemplate.create_section(
                "📋 Trading Activity",
                "<p>No orders executed - portfolio already balanced</p>",
            )
            content_sections.append(neutral_orders_html)

        # Error section if needed
        if not success:
            error_html = BaseEmailTemplate.create_alert_box(
                "⚠️ Check logs for error details", "error"
            )
            content_sections.append(error_html)

        footer = BaseEmailTemplate.get_footer()

        # Combine all content
        main_content = "".join(content_sections)
        content = f"""
        {combined_header}
        <tr>
            <td style="padding: 32px 24px; background-color: white;">
                {main_content}
            </td>
        </tr>
        {footer}
        """

        return BaseEmailTemplate.wrap_content(
            content, f"{APPLICATION_NAME} - Multi-Strategy Report (Neutral)"
        )
