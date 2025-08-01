"""Main email templates module.

This module provides the main template functions that combine all the 
content builders to create complete email templates.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any

from .base import BaseEmailTemplate
from .portfolio import PortfolioBuilder
from .performance import PerformanceBuilder
from .signals import SignalsBuilder


class EmailTemplates:
    """Main email template builder that combines all content builders."""
    
    @staticmethod
    def build_trading_report(
        mode: str,
        success: bool,
        account_before: dict,
        account_after: dict,
        positions: dict,
        orders: Optional[List[Dict]] = None,
        signal=None,
        portfolio_history: Optional[Dict] = None,
        open_positions: Optional[List[Dict]] = None,
    ) -> str:
        """Build a comprehensive HTML trading report email."""
        
        # Determine status styling
        status_color = "#10B981" if success else "#EF4444"
        status_emoji = "✅" if success else "❌"
        status_text = "Success" if success else "Failed"
        
        # Build content sections
        header = BaseEmailTemplate.get_header("The Alchemiser")
        status_banner = BaseEmailTemplate.get_status_banner(
            f"{mode.upper()} Trading Report",
            status_text,
            status_color,
            status_emoji
        )
        
        # Account summary
        account_summary_html = BaseEmailTemplate.create_section(
            "💰 Account Summary",
            PortfolioBuilder.build_account_summary(account_after)
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
                PortfolioBuilder.build_positions_table(open_positions)
            )
        
        # Closed positions P&L
        closed_pnl_html = ""
        if account_after and account_after.get('recent_closed_pnl'):
            closed_pnl_html = PortfolioBuilder.build_closed_positions_pnl(account_after)
        
        # Error section if needed
        error_html = ""
        if not success:
            error_html = BaseEmailTemplate.create_alert_box(
                "⚠️ Check logs for error details",
                "error"
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
    def build_multi_strategy_report(result: Any, mode: str) -> str:
        """Build a comprehensive multi-strategy email report."""
        
        # Determine success status
        success = getattr(result, 'success', True)
        status_color = "#10B981" if success else "#EF4444"
        status_emoji = "✅" if success else "❌"
        status_text = "Success" if success else "Failed"
        
        # Build content sections
        header = BaseEmailTemplate.get_header("The Alchemiser")
        status_banner = BaseEmailTemplate.get_status_banner(
            f"{mode.upper()} Multi-Strategy Report",
            status_text,
            status_color,
            status_emoji
        )
        
        # Get execution summary data
        execution_summary = getattr(result, 'execution_summary', {})
        strategy_summary = execution_summary.get('strategy_summary', {})
        trading_summary = execution_summary.get('trading_summary', {})
        account_after = execution_summary.get('account_info_after', {})
        
        # Get strategy signals if available
        strategy_signals = getattr(result, 'strategy_signals', {})
        
        # Build content sections
        content_sections = []
        
        # Account summary
        if account_after:
            account_html = BaseEmailTemplate.create_section(
                "💰 Account Summary",
                PortfolioBuilder.build_account_summary(account_after)
            )
            content_sections.append(account_html)
        
        # Market regime analysis
        market_regime_html = SignalsBuilder.build_market_regime_analysis(strategy_signals)
        if market_regime_html:
            content_sections.append(market_regime_html)
        
        # Strategy performance
        if strategy_summary:
            strategy_performance_html = PerformanceBuilder.build_strategy_performance(strategy_summary)
            content_sections.append(strategy_performance_html)
        
        # Detailed strategy signals
        if strategy_signals and strategy_summary:
            signals_html = SignalsBuilder.build_detailed_strategy_signals(strategy_signals, strategy_summary)
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
            "📈 Portfolio Allocation",
            PortfolioBuilder.build_portfolio_allocation(result)
        )
        content_sections.append(portfolio_allocation_html)
        
        # Orders executed (if available)
        orders = getattr(result, 'orders_executed', [])
        if orders:
            orders_html = PerformanceBuilder.build_trading_activity(orders)
            content_sections.append(orders_html)
        
        # Closed positions P&L
        if account_after and account_after.get('recent_closed_pnl'):
            closed_pnl_html = PortfolioBuilder.build_closed_positions_pnl(account_after)
            content_sections.append(closed_pnl_html)
        
        # Error section if needed
        if not success:
            error_html = BaseEmailTemplate.create_alert_box(
                "⚠️ Check logs for error details",
                "error"
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
    def build_error_report(title: str, error_message: str) -> str:
        """Build an error alert email."""
        
        header = BaseEmailTemplate.get_header("The Alchemiser")
        status_banner = BaseEmailTemplate.get_status_banner(
            title,
            "Error",
            "#EF4444",
            "❌"
        )
        
        # Format error message
        formatted_error = error_message.replace('\n', '<br>')
        
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
        tips_content = f"""
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


# Backward compatibility functions
def build_trading_report_html(*args, **kwargs) -> str:
    """Backward compatibility function for build_trading_report_html."""
    return EmailTemplates.build_trading_report(*args, **kwargs)

def build_multi_strategy_email_html(*args, **kwargs) -> str:
    """Backward compatibility function for build_multi_strategy_email_html."""
    return EmailTemplates.build_multi_strategy_report(*args, **kwargs)

def build_error_email_html(*args, **kwargs) -> str:
    """Backward compatibility function for build_error_email_html."""
    return EmailTemplates.build_error_report(*args, **kwargs)
