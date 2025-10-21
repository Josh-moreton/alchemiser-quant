"""Business Unit: shared; Status: current.

Multi-strategy report template builder.

This module handles the multi-strategy email template generation for
neutral-mode reports (no financial values exposed). Used by the notification
system to generate HTML email templates for multi-strategy execution reports.
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

    This class provides static methods to generate HTML email templates for
    multi-strategy execution reports. All templates follow the neutral reporting
    policy - no dollar values, P&L, or financial metrics are exposed.

    Example:
        >>> from the_alchemiser.execution_v2.models.execution_result import ExecutionResult
        >>> result = ExecutionResult(success=True, orders_executed=[...])
        >>> html = MultiStrategyReportBuilder.build_multi_strategy_report_neutral(
        ...     result, mode="PAPER"
        ... )
        >>> # Returns HTML string suitable for email delivery

    """

    @staticmethod
    def build_multi_strategy_report_neutral(result: ExecutionLike, mode: str) -> str:
        """Build a neutral multi-strategy email report without financial values.

        Generates an HTML email template showing portfolio rebalancing actions,
        strategy signals, and order execution details without exposing any
        financial values (dollar amounts, P&L, account balances).

        Args:
            result: Execution result object with attributes:
                - success (bool): Execution success status
                - strategy_signals (dict): Strategy signal data
                - orders_executed (list): List of executed orders
            mode: Trading mode, should be "PAPER" or "LIVE" (case-insensitive)

        Returns:
            str: Complete HTML email template ready for delivery

        Raises:
            ValueError: If mode is not "PAPER" or "LIVE"
            AttributeError: If result object lacks required attributes (propagated
                from builder delegates)

        Note:
            This function is deterministic and has no side effects. It delegates
            to PortfolioBuilder and SignalsBuilder for specific content sections.

        """
        # Validate mode parameter
        mode_upper = mode.upper()
        if mode_upper not in ("PAPER", "LIVE"):
            raise ValueError(f"Invalid mode '{mode}'. Must be 'PAPER' or 'LIVE'.")

        # Determine success status
        success = getattr(result, "success", True)
        status_color = "#059669" if success else "#DC2626"
        status_emoji = "✅" if success else "❌"
        status_text = "Completed Successfully" if success else "Execution Failed"

        # Build content sections
        combined_header = BaseEmailTemplate.get_combined_header_status(
            f"{mode_upper} Multi-Strategy Execution Report",
            status_text,
            status_color,
            status_emoji,
        )

        # Get strategy signals for market regime and signals
        strategy_signals = getattr(result, "strategy_signals", {})

        # Build content sections (neutral mode - no financial data)
        content_sections = []

        # Add signal summary at the top (Issue: More context in emails)
        consolidated_portfolio = getattr(result, "consolidated_portfolio", {})
        signal_summary_html = SignalsBuilder.build_signal_summary(
            strategy_signals, consolidated_portfolio
        )
        if signal_summary_html:
            content_sections.append(signal_summary_html)

        # Add execution summary box if successful
        if success:
            orders = getattr(result, "orders_executed", [])
            orders_count = len(orders) if orders else 0
            summary_html = f"""
            <div style="margin: 0 0 28px 0; padding: 18px; background-color: #ECFDF5; border-left: 4px solid #059669; border-radius: 8px;">
                <h3 style="margin: 0 0 10px 0; color: #065F46; font-size: 16px; font-weight: 600; letter-spacing: 0.3px;">
                    Execution Summary
                </h3>
                <p style="margin: 0; color: #065F46; line-height: 1.6; font-size: 14px;">
                    Portfolio rebalancing completed successfully. {orders_count} order{"s" if orders_count != 1 else ""} executed as per strategy allocation targets.
                </p>
            </div>
            """
            content_sections.append(summary_html)

        # Strategy signals (neutral mode) - MOVED UP before portfolio rebalancing
        if strategy_signals:
            neutral_signals_html = SignalsBuilder.build_strategy_signals_neutral(strategy_signals)
            content_sections.append(neutral_signals_html)

        # Portfolio rebalancing table (percentages only) - with improved header
        rebalancing_html = BaseEmailTemplate.create_section(
            "Portfolio Rebalancing Plan",
            PortfolioBuilder.build_portfolio_rebalancing_table(result),
        )
        content_sections.append(rebalancing_html)

        # Market regime analysis (no financial data)
        market_regime_html = SignalsBuilder.build_market_regime_analysis(strategy_signals)
        if market_regime_html:
            content_sections.append(market_regime_html)

        # Orders executed (detailed table, no values) - with improved header
        orders = getattr(result, "orders_executed", [])
        if orders:
            orders_table_html = PortfolioBuilder.build_orders_table_neutral(orders)
            neutral_orders_html = BaseEmailTemplate.create_section(
                "Order Execution Details", orders_table_html
            )
            content_sections.append(neutral_orders_html)
        else:
            neutral_orders_html = """
            <div style="margin: 24px 0;">
                <h3 style="margin: 0 0 14px 0; color: #1F2937; font-size: 16px; font-weight: 600; letter-spacing: 0.3px;">Order Execution Details</h3>
                <p style="margin: 0; color: #6B7280; font-size: 14px; line-height: 1.6;">No rebalancing orders required. Current portfolio allocation matches target strategy parameters.</p>
            </div>
            """
            content_sections.append(neutral_orders_html)

        # Error section if needed
        if not success:
            error_html = """
            <div style="margin: 24px 0; padding: 18px; background-color: #FEE2E2; border-left: 4px solid #DC2626; border-radius: 8px;">
                <h3 style="margin: 0 0 10px 0; color: #991B1B; font-size: 16px; font-weight: 600; letter-spacing: 0.3px;">
                    Execution Error
                </h3>
                <p style="margin: 0; color: #991B1B; line-height: 1.6; font-size: 14px;">
                    Review system logs for detailed error information and correlation ID for troubleshooting.
                </p>
            </div>
            """
            content_sections.append(error_html)

        footer = BaseEmailTemplate.get_footer()

        # Combine all content
        main_content = "".join(content_sections)
        content = f"""
        {combined_header}
        <tr>
            <td style="padding: 32px 24px; background-color: #F9FAFB;">
                {main_content}
            </td>
        </tr>
        {footer}
        """

        return BaseEmailTemplate.wrap_content(
            content, f"{APPLICATION_NAME} - {mode_upper} Multi-Strategy Execution Report"
        )
