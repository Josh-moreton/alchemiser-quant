import os
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import logging
from typing import Optional, Dict, List, Any

from the_alchemiser.core.secrets.secrets_manager import SecretsManager
from the_alchemiser.core.config import get_config

# Initialize secrets manager
secrets_manager = SecretsManager()


def get_email_config():
    """Get email configuration from config.yaml and secrets manager"""
    try:
        # Get configuration instance
        config = get_config()
        
        # Get email config section from config.yaml
        email_config = config.get('email', {})
        
        # Extract values from config.yaml
        smtp_server = email_config.get('smtp_server', 'smtp.mail.me.com')
        smtp_port = int(email_config.get('smtp_port', 587))
        from_email = email_config.get('from_email')
        to_email = email_config.get('to_email')
        
        # Get secrets manager config
        secrets_config = config.get('secrets_manager', {})
        secret_name = secrets_config.get('secret_name', 'nuclear-secrets')
        
        # Get sensitive password from AWS Secrets Manager
        email_password = None
        try:
            secrets = secrets_manager.get_secret(secret_name)
            if secrets:
                # Look for email password in secrets (prioritize SMTP_PASSWORD)
                email_password = (secrets.get('SMTP_PASSWORD') or 
                                secrets.get('email_password') or 
                                secrets.get('EMAIL_PASSWORD'))
        except Exception as e:
            logging.warning(f"Could not get email password from secrets manager: {e}")
        
        # Validate required fields
        if not from_email:
            logging.error("from_email not configured in config.yaml email section")
            return None
            
        if not email_password:
            logging.error("email_password not found in AWS Secrets Manager")
            return None
            
        # Use from_email as to_email if to_email is not specified
        if not to_email:
            to_email = from_email
            
        logging.info(f"Email config loaded: SMTP={smtp_server}:{smtp_port}, from={from_email}, to={to_email}")
        
        return (smtp_server, smtp_port, from_email, email_password, to_email)
        
    except Exception as e:
        logging.error(f"Error loading email configuration: {e}")
        return None


def send_email_notification(
    subject: str,
    html_content: str,
    text_content: Optional[str] = None,
    recipient_email: Optional[str] = None
) -> bool:
    """
    Send an email notification with HTML content.
    
    Args:
        subject (str): Email subject line
        html_content (str): HTML email content
        text_content (str, optional): Plain text fallback
        recipient_email (str, optional): Override recipient email
    
    Returns:
        bool: True if sent successfully, False otherwise
    """
    email_config = get_email_config()
    if not email_config:
        logging.error("Email configuration not available")
        return False
    
    smtp_server, smtp_port, from_email, email_password, default_recipient = email_config
    
    recipient = recipient_email or default_recipient
    if not recipient:
        logging.error("No recipient email configured")
        return False
    
    try:
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = from_email
        msg['To'] = recipient
        
        # Add text version if provided
        if text_content:
            text_part = MIMEText(text_content, 'plain')
            msg.attach(text_part)
        
        # Add HTML version
        html_part = MIMEText(html_content, 'html')
        msg.attach(html_part)
        
        # Send email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(from_email, email_password)
            server.send_message(msg)
        
        logging.info(f"Email notification sent successfully to {recipient}")
        return True
        
    except Exception as e:
        logging.error(f"Failed to send email notification: {e}")
        return False


def build_trading_report_html(
    mode: str,
    success: bool,
    account_before: dict,
    account_after: dict,
    positions: dict,
    orders: Optional[List[Dict]] = None,
    signal=None,
    portfolio_state: Optional[Dict] = None,
    portfolio_history: Optional[Dict] = None,
    open_positions: Optional[List[Dict]] = None,
) -> str:
    """
    Build a beautiful HTML email template for trading reports.
    Uses Maizzle-inspired responsive design.
    """
    
    # Determine status color and emoji
    status_color = "#10B981" if success else "#EF4444"  # green or red
    status_emoji = "✅" if success else "❌"
    status_text = "Success" if success else "Failed"
    
    # Calculate P&L information
    pl_info = ""
    if account_after:
        equity = float(account_after.get('equity', 0))
        cash = float(account_after.get('cash', 0))
        pl_info = f"""
        <tr>
            <td style="padding: 8px 12px; border-bottom: 1px solid #E5E7EB;">
                <span style="font-weight: 600;">Portfolio Value:</span>
            </td>
            <td style="padding: 8px 12px; border-bottom: 1px solid #E5E7EB; text-align: right;">
                ${equity:,.2f}
            </td>
        </tr>
        <tr>
            <td style="padding: 8px 12px; border-bottom: 1px solid #E5E7EB;">
                <span style="font-weight: 600;">Cash Available:</span>
            </td>
            <td style="padding: 8px 12px; border-bottom: 1px solid #E5E7EB; text-align: right;">
                ${cash:,.2f}
            </td>
        </tr>
        """
    
    # Build positions table
    positions_html = ""
    if open_positions:
        total_unrealized_pl = 0
        positions_rows = ""
        
        for position in open_positions[:10]:  # Show top 10 positions
            symbol = position.get('symbol', 'N/A')
            market_value = float(position.get('market_value', 0))
            unrealized_pl = float(position.get('unrealized_pl', 0))
            unrealized_plpc = float(position.get('unrealized_plpc', 0))
            
            total_unrealized_pl += unrealized_pl
            
            pl_color = "#10B981" if unrealized_pl >= 0 else "#EF4444"
            pl_sign = "+" if unrealized_pl >= 0 else ""
            
            positions_rows += f"""
            <tr>
                <td style="padding: 8px 12px; border-bottom: 1px solid #E5E7EB; font-weight: 600;">
                    {symbol}
                </td>
                <td style="padding: 8px 12px; border-bottom: 1px solid #E5E7EB; text-align: right;">
                    ${market_value:,.0f}
                </td>
                <td style="padding: 8px 12px; border-bottom: 1px solid #E5E7EB; text-align: right; color: {pl_color}; font-weight: 600;">
                    {pl_sign}${unrealized_pl:.2f}
                </td>
                <td style="padding: 8px 12px; border-bottom: 1px solid #E5E7EB; text-align: right; color: {pl_color};">
                    {pl_sign}{unrealized_plpc:.2%}
                </td>
            </tr>
            """
        
        total_pl_color = "#10B981" if total_unrealized_pl >= 0 else "#EF4444"
        total_pl_sign = "+" if total_unrealized_pl >= 0 else ""
        
        positions_html = f"""
        <div style="margin: 24px 0;">
            <h3 style="margin: 0 0 16px 0; color: #1F2937; font-size: 18px; font-weight: 600;">📊 Open Positions</h3>
            <table style="width: 100%; border-collapse: collapse; background-color: white; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                <thead>
                    <tr style="background-color: #F9FAFB;">
                        <th style="padding: 12px; text-align: left; font-weight: 600; color: #374151; border-bottom: 1px solid #E5E7EB;">Symbol</th>
                        <th style="padding: 12px; text-align: right; font-weight: 600; color: #374151; border-bottom: 1px solid #E5E7EB;">Value</th>
                        <th style="padding: 12px; text-align: right; font-weight: 600; color: #374151; border-bottom: 1px solid #E5E7EB;">P&L</th>
                        <th style="padding: 12px; text-align: right; font-weight: 600; color: #374151; border-bottom: 1px solid #E5E7EB;">P&L %</th>
                    </tr>
                </thead>
                <tbody>
                    {positions_rows}
                    <tr style="background-color: #F9FAFB; font-weight: 600;">
                        <td style="padding: 12px; border-top: 2px solid #E5E7EB;">Total Unrealized</td>
                        <td style="padding: 12px; border-top: 2px solid #E5E7EB;"></td>
                        <td style="padding: 12px; text-align: right; color: {total_pl_color}; border-top: 2px solid #E5E7EB;">
                            {total_pl_sign}${total_unrealized_pl:.2f}
                        </td>
                        <td style="padding: 12px; border-top: 2px solid #E5E7EB;"></td>
                    </tr>
                </tbody>
            </table>
        </div>
        """
    
    # Build trading activity section
    trading_html = ""
    if orders and len(orders) > 0:
        orders_rows = ""
        for order in orders[:5]:  # Show last 5 orders
            side = order.get('side', 'N/A')
            symbol = order.get('symbol', 'N/A')
            qty = order.get('qty', 0)
            
            side_color = "#10B981" if side.lower() == 'buy' else "#EF4444"
            side_emoji = "🟢" if side.lower() == 'buy' else "🔴"
            
            orders_rows += f"""
            <tr>
                <td style="padding: 8px 12px; border-bottom: 1px solid #E5E7EB;">
                    <span style="color: {side_color}; font-weight: 600;">{side_emoji} {side.upper()}</span>
                </td>
                <td style="padding: 8px 12px; border-bottom: 1px solid #E5E7EB; font-weight: 600;">
                    {symbol}
                </td>
                <td style="padding: 8px 12px; border-bottom: 1px solid #E5E7EB; text-align: right;">
                    {qty}
                </td>
            </tr>
            """
        
        trading_html = f"""
        <div style="margin: 24px 0;">
            <h3 style="margin: 0 0 16px 0; color: #1F2937; font-size: 18px; font-weight: 600;">⚡ Trading Activity</h3>
            <table style="width: 100%; border-collapse: collapse; background-color: white; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                <thead>
                    <tr style="background-color: #F9FAFB;">
                        <th style="padding: 12px; text-align: left; font-weight: 600; color: #374151; border-bottom: 1px solid #E5E7EB;">Action</th>
                        <th style="padding: 12px; text-align: left; font-weight: 600; color: #374151; border-bottom: 1px solid #E5E7EB;">Symbol</th>
                        <th style="padding: 12px; text-align: right; font-weight: 600; color: #374151; border-bottom: 1px solid #E5E7EB;">Quantity</th>
                    </tr>
                </thead>
                <tbody>
                    {orders_rows}
                </tbody>
            </table>
        </div>
        """
    else:
        trading_html = f"""
        <div style="margin: 24px 0; padding: 16px; background-color: #F3F4F6; border-radius: 8px; text-align: center;">
            <span style="color: #6B7280; font-style: italic;">⚡ No trades executed</span>
        </div>
        """
    
    # Build signal information
    signal_html = ""
    if signal:
        try:
            signal_html = f"""
            <div style="margin: 24px 0; padding: 16px; background-color: #FEF3C7; border-left: 4px solid #F59E0B; border-radius: 8px;">
                <h3 style="margin: 0 0 8px 0; color: #92400E; font-size: 16px; font-weight: 600;">📈 Signal Information</h3>
                <p style="margin: 0; color: #92400E;">
                    <strong>{signal.action} {signal.symbol}</strong>
                    {f" - {signal.reason}" if hasattr(signal, "reason") and signal.reason else ""}
                </p>
            </div>
            """
        except Exception:
            signal_html = f"""
            <div style="margin: 24px 0; padding: 16px; background-color: #FEE2E2; border-left: 4px solid #EF4444; border-radius: 8px;">
                <p style="margin: 0; color: #DC2626; font-style: italic;">Error reading signal data</p>
            </div>
            """
    
    # Main HTML template
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en" xmlns:v="urn:schemas-microsoft-com:vml" xmlns:o="urn:schemas-microsoft-com:office:office">
    <head>
        <meta charset="utf-8">
        <meta name="x-apple-disable-message-reformatting">
        <meta http-equiv="x-ua-compatible" content="ie=edge">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <meta name="format-detection" content="telephone=no, date=no, address=no, email=no">
        <title>The Alchemiser - Trading Report</title>
        <!--[if mso]>
        <noscript>
            <xml>
                <o:OfficeDocumentSettings>
                    <o:PixelsPerInch>96</o:PixelsPerInch>
                </o:OfficeDocumentSettings>
            </xml>
        </noscript>
        <style>
            td,th,div,p,a,h1,h2,h3,h4,h5,h6 {{font-family: "Segoe UI", sans-serif; mso-line-height-rule: exactly;}}
        </style>
        <![endif]-->
        <style>
            @media (max-width: 600px) {{
                .sm-w-full {{ width: 100% !important; }}
                .sm-px-24 {{ padding-left: 24px !important; padding-right: 24px !important; }}
            }}
        </style>
    </head>
    <body style="margin: 0; width: 100%; padding: 0; word-break: break-word; -webkit-font-smoothing: antialiased; background-color: #F3F4F6;">
        <div style="display: none;">The Alchemiser Trading Bot - {mode} Execution Report</div>
        <div role="article" aria-roledescription="email" aria-label="The Alchemiser Trading Report" lang="en">
            <table style="width: 100%; font-family: 'Segoe UI', ui-sans-serif, system-ui, -apple-system, 'Helvetica Neue', sans-serif;" cellpadding="0" cellspacing="0" role="presentation">
                <tr>
                    <td align="center" style="background-color: #F3F4F6; padding: 24px 0;">
                        <table class="sm-w-full" style="width: 600px;" cellpadding="0" cellspacing="0" role="presentation">
                            <!-- Header -->
                            <tr>
                                <td style="padding: 32px 24px; text-align: center; background: linear-gradient(135deg, #FF6B35, #F7931E); border-radius: 12px 12px 0 0;">
                                    <h1 style="margin: 0; color: white; font-size: 28px; font-weight: 700; text-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                                        🧪 The Alchemiser
                                    </h1>
                                    <p style="margin: 8px 0 0 0; color: rgba(255,255,255,0.9); font-size: 16px;">
                                        Advanced Trading Dashboard
                                    </p>
                                </td>
                            </tr>
                            
                            <!-- Status Banner -->
                            <tr>
                                <td style="padding: 24px; background-color: {status_color}; text-align: center;">
                                    <h2 style="margin: 0; color: white; font-size: 24px; font-weight: 600;">
                                        {status_emoji} {mode.upper()} Trading Report
                                    </h2>
                                    <p style="margin: 8px 0 0 0; color: rgba(255,255,255,0.9); font-size: 16px;">
                                        Status: {status_text} • {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                                    </p>
                                </td>
                            </tr>
                            
                            <!-- Main Content -->
                            <tr>
                                <td style="padding: 32px 24px; background-color: white;">
                                    
                                    <!-- Account Summary -->
                                    <div style="margin-bottom: 24px;">
                                        <h3 style="margin: 0 0 16px 0; color: #1F2937; font-size: 18px; font-weight: 600;">💰 Account Summary</h3>
                                        <table style="width: 100%; border-collapse: collapse; background-color: #F9FAFB; border-radius: 8px; overflow: hidden;">
                                            {pl_info}
                                        </table>
                                    </div>
                                    
                                    {signal_html}
                                    
                                    {trading_html}
                                    
                                    {positions_html}
                                    
                                    {"<div style='margin: 24px 0; padding: 16px; background-color: #FEE2E2; border-left: 4px solid #EF4444; border-radius: 8px;'><p style='margin: 0; color: #DC2626; font-weight: 600;'>⚠️ Check logs for error details</p></div>" if not success else ""}
                                    
                                </td>
                            </tr>
                            
                            <!-- Footer -->
                            <tr>
                                <td style="padding: 24px; background-color: #1F2937; border-radius: 0 0 12px 12px; text-align: center;">
                                    <p style="margin: 0; color: #9CA3AF; font-size: 14px;">
                                        Generated by The Alchemiser Trading Bot
                                    </p>
                                    <p style="margin: 8px 0 0 0; color: #6B7280; font-size: 12px;">
                                        Nuclear • TECL • Multi-Strategy
                                    </p>
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
        </div>
    </body>
    </html>
    """
    
    return html_content


def _build_portfolio_display(result) -> str:
    """Build portfolio allocation display showing final actual positions"""
    try:
        # Try to get actual final portfolio state first
        if hasattr(result, 'final_portfolio_state') and result.final_portfolio_state:
            allocations = result.final_portfolio_state.get('allocations', {})
            if allocations:
                # Show actual current positions
                portfolio_lines = []
                for symbol, data in allocations.items():
                    current_percent = data.get('current_percent', 0)
                    if current_percent > 0.1:  # Only show positions > 0.1%
                        portfolio_lines.append(f"<span style='font-weight: 600;'>{symbol}:</span> {current_percent:.1f}%")
                
                if portfolio_lines:
                    return "<br>".join(portfolio_lines)
        
        # Fallback to target allocations from consolidated portfolio
        if hasattr(result, 'consolidated_portfolio') and result.consolidated_portfolio:
            return "<br>".join([
                f"<span style='font-weight: 600;'>{symbol}:</span> {weight:.1%}" 
                for symbol, weight in list(result.consolidated_portfolio.items())[:5]
            ])
        
        return "<span style='color: #6B7280; font-style: italic;'>Portfolio data unavailable</span>"
    except Exception as e:
        return f"<span style='color: #EF4444;'>Error loading portfolio: {str(e)}</span>"


def build_multi_strategy_email_html(result: Any, mode: str) -> str:
    """
    Build HTML email for multi-strategy execution results.
    """
    if not result.success:
        error_msg = result.execution_summary.get('error', 'Unknown error')
        return build_error_email_html(f"{mode} Multi-Strategy Execution FAILED", error_msg)
    
    # Extract information from result
    execution_summary = result.execution_summary
    strategy_summary = execution_summary.get('strategy_summary', {})
    trading_summary = execution_summary.get('trading_summary', {})
    account_info = execution_summary.get('account_info_after', {})
    
    # Build strategy signals section
    strategies_html = ""
    if strategy_summary:
        strategies_rows = ""
        for strategy, details in strategy_summary.items():
            allocation = details.get('allocation', 0)
            signal = details.get('signal', 'UNKNOWN')
            
            signal_color = "#10B981" if signal == "BUY" else "#EF4444" if signal == "SELL" else "#6B7280"
            
            strategies_rows += f"""
            <tr>
                <td style="padding: 8px 12px; border-bottom: 1px solid #E5E7EB; font-weight: 600;">
                    {strategy}
                </td>
                <td style="padding: 8px 12px; border-bottom: 1px solid #E5E7EB; text-align: right;">
                    {allocation:.0%}
                </td>
                <td style="padding: 8px 12px; border-bottom: 1px solid #E5E7EB; text-align: right; color: {signal_color}; font-weight: 600;">
                    {signal}
                </td>
            </tr>
            """
        
        strategies_html = f"""
        <div style="margin: 24px 0;">
            <h3 style="margin: 0 0 16px 0; color: #1F2937; font-size: 18px; font-weight: 600;">📊 Strategy Signals</h3>
            <table style="width: 100%; border-collapse: collapse; background-color: white; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                <thead>
                    <tr style="background-color: #F9FAFB;">
                        <th style="padding: 12px; text-align: left; font-weight: 600; color: #374151; border-bottom: 1px solid #E5E7EB;">Strategy</th>
                        <th style="padding: 12px; text-align: right; font-weight: 600; color: #374151; border-bottom: 1px solid #E5E7EB;">Allocation</th>
                        <th style="padding: 12px; text-align: right; font-weight: 600; color: #374151; border-bottom: 1px solid #E5E7EB;">Signal</th>
                    </tr>
                </thead>
                <tbody>
                    {strategies_rows}
                </tbody>
            </table>
        </div>
        """
    
    # Build trading summary
    trading_html = ""
    if trading_summary.get('total_trades', 0) > 0:
        total_trades = trading_summary.get('total_trades', 0)
        total_buy_value = trading_summary.get('total_buy_value', 0)
        total_sell_value = trading_summary.get('total_sell_value', 0)
        
        trading_html = f"""
        <div style="margin: 24px 0; padding: 16px; background-color: #EEF2FF; border-left: 4px solid #6366F1; border-radius: 8px;">
            <h3 style="margin: 0 0 12px 0; color: #3730A3; font-size: 16px; font-weight: 600;">⚡ Trading Summary</h3>
            <p style="margin: 0; color: #3730A3;">
                <strong>{total_trades} orders executed</strong><br>
                Buy: ${total_buy_value:,.0f} | Sell: ${total_sell_value:,.0f}
            </p>
        </div>
        """
    else:
        trading_html = f"""
        <div style="margin: 24px 0; padding: 16px; background-color: #F3F4F6; border-radius: 8px; text-align: center;">
            <span style="color: #6B7280; font-style: italic;">⚡ No trades executed</span>
        </div>
        """
    
    # Main template with multi-strategy specific content
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>The Alchemiser - Multi-Strategy Report</title>
    </head>
    <body style="margin: 0; font-family: 'Segoe UI', sans-serif; background-color: #F3F4F6;">
        <div style="max-width: 600px; margin: 0 auto; background-color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
            <!-- Header -->
            <div style="padding: 32px 24px; text-align: center; background: linear-gradient(135deg, #FF6B35, #F7931E); color: white;">
                <h1 style="margin: 0; font-size: 28px; font-weight: 700;">🧪 The Alchemiser</h1>
                <p style="margin: 8px 0 0 0; font-size: 16px; opacity: 0.9;">Multi-Strategy Trading System</p>
            </div>
            
            <!-- Status -->
            <div style="padding: 24px; background-color: #10B981; color: white; text-align: center;">
                <h2 style="margin: 0; font-size: 24px;">✅ {mode.upper()} Multi-Strategy Execution</h2>
                <p style="margin: 8px 0 0 0; opacity: 0.9;">{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            
            <!-- Content -->
            <div style="padding: 32px 24px;">
                {strategies_html}
                {trading_html}
                
                <!-- Portfolio Allocation -->
                <div style="margin: 24px 0;">
                    <h3 style="margin: 0 0 16px 0; color: #1F2937; font-size: 18px; font-weight: 600;">🎯 Portfolio Allocation</h3>
                    <div style="padding: 16px; background-color: #F9FAFB; border-radius: 8px;">
                        {_build_portfolio_display(result)}
                    </div>
                </div>
            </div>
            
            <!-- Footer -->
            <div style="padding: 24px; background-color: #1F2937; color: #9CA3AF; text-align: center; font-size: 14px;">
                Generated by The Alchemiser Trading Bot
            </div>
        </div>
    </body>
    </html>
    """
    
    return html_content


def build_error_email_html(title: str, error_message: str) -> str:
    """Build HTML email for error notifications."""
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>The Alchemiser - Error Alert</title>
    </head>
    <body style="margin: 0; font-family: 'Segoe UI', sans-serif; background-color: #F3F4F6;">
        <div style="max-width: 600px; margin: 0 auto; background-color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
            <!-- Header -->
            <div style="padding: 32px 24px; text-align: center; background: linear-gradient(135deg, #FF6B35, #F7931E); color: white;">
                <h1 style="margin: 0; font-size: 28px; font-weight: 700;">🧪 The Alchemiser</h1>
                <p style="margin: 8px 0 0 0; font-size: 16px; opacity: 0.9;">Trading Alert System</p>
            </div>
            
            <!-- Error Status -->
            <div style="padding: 24px; background-color: #EF4444; color: white; text-align: center;">
                <h2 style="margin: 0; font-size: 24px;">❌ {title}</h2>
                <p style="margin: 8px 0 0 0; opacity: 0.9;">{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            
            <!-- Error Details -->
            <div style="padding: 32px 24px;">
                <div style="padding: 16px; background-color: #FEE2E2; border-left: 4px solid #EF4444; border-radius: 8px;">
                    <h3 style="margin: 0 0 12px 0; color: #DC2626; font-size: 16px;">Error Details</h3>
                    <p style="margin: 0; color: #DC2626; font-family: monospace; font-size: 14px;">
                        {error_message}
                    </p>
                </div>
            </div>
            
            <!-- Footer -->
            <div style="padding: 24px; background-color: #1F2937; color: #9CA3AF; text-align: center; font-size: 14px;">
                Generated by The Alchemiser Trading Bot
            </div>
        </div>
    </body>
    </html>
    """
