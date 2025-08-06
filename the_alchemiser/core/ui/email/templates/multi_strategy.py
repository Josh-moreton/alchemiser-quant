"""Multi-strategy report template builder.

This module handles the multi-strategy email template generation.
"""

from typing import Any

from .base import BaseEmailTemplate
from .performance import PerformanceBuilder
from .portfolio import PortfolioBuilder
from .signals import SignalsBuilder


class MultiStrategyReportBuilder:
    """Builds multi-strategy email templates."""

    @staticmethod
    def build_multi_strategy_report(result: Any, mode: str) -> str:
        """Build a comprehensive multi-strategy email report."""

        # Determine success status
        success = getattr(result, "success", True)
        status_color = "#10B981" if success else "#EF4444"
        status_emoji = "✅" if success else "❌"
        status_text = "Success" if success else "Failed"

        # Build content sections
        header = BaseEmailTemplate.get_header("The Alchemiser")
        status_banner = BaseEmailTemplate.get_status_banner(
            f"{mode.upper()} Multi-Strategy Report", status_text, status_color, status_emoji
        )

        # Get execution summary data
        execution_summary = getattr(result, "execution_summary", {})
        strategy_summary = execution_summary.get("strategy_summary", {})
        trading_summary = execution_summary.get("trading_summary", {})
        account_after = execution_summary.get("account_info_after", {})

        # Get strategy signals if available
        strategy_signals = getattr(result, "strategy_signals", {})

        # Build content sections
        content_sections = []

        # Account summary
        if account_after:
            account_html = BaseEmailTemplate.create_section(
                "💰 Account Summary", PortfolioBuilder.build_account_summary(account_after)
            )
            content_sections.append(account_html)

        # Market regime analysis
        market_regime_html = SignalsBuilder.build_market_regime_analysis(strategy_signals)
        if market_regime_html:
            content_sections.append(market_regime_html)

        # Strategy performance
        if strategy_summary:
            strategy_performance_html = PerformanceBuilder.build_strategy_performance(
                strategy_summary
            )
            content_sections.append(strategy_performance_html)

        # Detailed strategy signals
        if strategy_signals and strategy_summary:
            signals_html = SignalsBuilder.build_detailed_strategy_signals(
                strategy_signals, strategy_summary
            )
            content_sections.append(signals_html)

        # Technical indicators
        if strategy_signals:
            indicators_html = SignalsBuilder.build_technical_indicators(strategy_signals)
            content_sections.append(indicators_html)

        # Trading summary
        if trading_summary:
            trading_summary_html = PerformanceBuilder.build_trading_summary(trading_summary)
            content_sections.append(trading_summary_html)

        # Portfolio allocation
        portfolio_allocation_html = BaseEmailTemplate.create_section(
            "📈 Portfolio Allocation", PortfolioBuilder.build_portfolio_allocation(result)
        )
        content_sections.append(portfolio_allocation_html)

        # Orders executed (if available)
        orders = getattr(result, "orders_executed", [])
        if orders:
            orders_html = PerformanceBuilder.build_trading_activity(orders)
            content_sections.append(orders_html)

        # Closed positions P&L
        if account_after and account_after.get("recent_closed_pnl"):
            closed_pnl_html = PortfolioBuilder.build_closed_positions_pnl(account_after)
            content_sections.append(closed_pnl_html)

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
        {header}
        {status_banner}
        <tr>
            <td style="padding: 32px 24px; background-color: white;">
                {main_content}
            </td>
        </tr>
        {footer}
        """

        return BaseEmailTemplate.wrap_content(content, "The Alchemiser - Multi-Strategy Report")

    @staticmethod
    def build_multi_strategy_report_neutral(result: Any, mode: str) -> str:
        """Build a neutral multi-strategy email report without financial values."""

        # Determine success status
        success = getattr(result, "success", True)
        status_color = "#10B981" if success else "#EF4444"
        status_emoji = "✅" if success else "❌"
        status_text = "Success" if success else "Failed"

        # Build content sections
        combined_header = BaseEmailTemplate.get_combined_header_status(
            f"{mode.upper()} Multi-Strategy Report", status_text, status_color, status_emoji
        )

        # Get strategy signals for market regime and signals
        strategy_signals = getattr(result, "strategy_signals", {})

        # Build content sections (neutral mode - no financial data)
        content_sections = []

        # Portfolio rebalancing table (percentages only)
        rebalancing_html = BaseEmailTemplate.create_section(
            "🔄 Portfolio Rebalancing", PortfolioBuilder.build_portfolio_rebalancing_table(result)
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
                "📋 Trading Activity", "<p>No orders executed - portfolio already balanced</p>"
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
            content, "The Alchemiser - Multi-Strategy Report (Neutral)"
        )
