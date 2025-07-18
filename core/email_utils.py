import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from datetime import datetime
from .config import Config

def send_email(subject, body, smtp_server, smtp_port, smtp_user, smtp_password, to_email):
    """Send a plain text email using SMTP."""
    msg = MIMEMultipart()
    msg['From'] = smtp_user
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(smtp_user, smtp_password)
            server.sendmail(smtp_user, to_email, msg.as_string())
        print(f"Email sent successfully to {to_email}")
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False

def format_alpaca_email_body(success, account_before, account_after, positions, execution_time):
    """Format the email body for Alpaca bot execution notification."""
    status_icon = "✅" if success else "❌"
    portfolio_value_before = account_before.get('portfolio_value', 0.0)
    portfolio_value_after = account_after.get('portfolio_value', 0.0)
    cash_before = account_before.get('cash', 0.0)
    cash_after = account_after.get('cash', 0.0)
    portfolio_change = portfolio_value_after - portfolio_value_before
    portfolio_change_pct = (portfolio_change / portfolio_value_before * 100) if portfolio_value_before > 0 else 0
    # Create positions summary
    if positions:
        positions_text = "\n📊 CURRENT POSITIONS:\n"
        for symbol, position in positions.items():
            qty = position.get('qty', 0)
            market_value = position.get('market_value', 0)
            current_price = position.get('current_price', 0)
            positions_text += f"   {symbol}: {qty} shares @ ${current_price:.2f} = ${market_value:.2f}\n"
    else:
        positions_text = "\n💰 CURRENT POSITIONS: 100% Cash\n"
    body = f"""Nuclear Alpaca Bot Execution Report - {execution_time}\n\n{status_icon} EXECUTION STATUS: {'SUCCESS' if success else 'FAILED'}\n\n📈 ACCOUNT SUMMARY:\n   Portfolio Value Before: ${portfolio_value_before:,.2f}\n   Portfolio Value After:  ${portfolio_value_after:,.2f}\n   Portfolio Change:       ${portfolio_change:+,.2f} ({portfolio_change_pct:+.2f}%)\n   \n   Cash Before: ${cash_before:,.2f}\n   Cash After:  ${cash_after:,.2f}\n   Cash Change: ${cash_after - cash_before:+,.2f}\n\n{positions_text}\n🤖 EXECUTION DETAILS:\n   Strategy: Nuclear Energy Portfolio Rebalancing\n   Trading Mode: Paper Trading (Alpaca)\n   Execution Time: {execution_time}\n   \n📋 LOGS:\n   Check /tmp/alpaca_trader.log for detailed execution logs\n   Check /tmp/nuclear_alerts.json for nuclear strategy signals\n"""
    return body

def format_signal_email_body(signal):
    """Format the email body for a signal alert."""
    body = f"""
Nuclear Trading Signal - {getattr(signal, 'date', '') or ''}

Signal: {getattr(signal, 'action', 'N/A')} {getattr(signal, 'symbol', '')}
Reason: {getattr(signal, 'reason', '')}
Price: {getattr(signal, 'price', 'N/A')}

"""
    portfolio = getattr(signal, 'portfolio', None)
    if portfolio:
        body += "Portfolio Allocation:\n"
        for sym, data in portfolio.items():
            weight = data.get('weight', 0)
            price = data.get('price', 0)
            body += f"- {sym}: {weight:.1%} @ ${price:.2f}\n"
    return body

def send_alpaca_notification(success, account_before, account_after, positions):
    """Send email notification about Alpaca bot execution with all formatting and configuration handled."""
    try:
        # Load email configuration from config.yaml
        config = Config()
        email_config = config['email']
        
        smtp_server = email_config['smtp_server']
        smtp_port = email_config['smtp_port']
        smtp_user = email_config['username']
        smtp_password = os.environ.get("SMTP_PASSWORD")
        to_email = email_config['recipients'][0]  # Use first recipient
        
        if not smtp_password:
            print("⚠️ SMTP_PASSWORD environment variable not set. Email notification skipped.")
            return False
        
        # Format subject and body
        status_icon = "✅" if success else "❌"
        execution_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        subject = f"{status_icon} Nuclear Alpaca Bot Execution - {execution_time}"
        body = format_alpaca_email_body(success, account_before, account_after, positions, execution_time)
        
        # Send email
        email_sent = send_email(subject, body, smtp_server, smtp_port, smtp_user, smtp_password, to_email)
        
        if email_sent:
            print("✅ Email notification sent successfully!")
        else:
            print("❌ Failed to send email notification.")
            
        return email_sent
        
    except Exception as e:
        print(f"⚠️ Error sending email notification: {e}")
        return False

def send_signal_notification(signal, test_mode=False):
    """Send email notification about trading signal with all formatting and configuration handled."""
    try:
        # Load email configuration from config.yaml
        config = Config()
        email_config = config['email']
        
        smtp_server = email_config['smtp_server']
        smtp_port = email_config['smtp_port']
        smtp_user = email_config['username']
        smtp_password = os.environ.get("SMTP_PASSWORD")
        to_email = email_config['recipients'][0]  # Use first recipient
        
        if not smtp_password:
            print("❌ SMTP_PASSWORD environment variable not set. Email not sent.")
            return False
        
        # Format subject and body
        subject = f"Nuclear Trading Signal: {getattr(signal, 'action', 'N/A')} {getattr(signal, 'symbol', '')} ({datetime.now().strftime('%Y-%m-%d')})"
        body = format_signal_email_body(signal)
        
        # Only send email if test_mode is True or signal.signal_changed is True (if present)
        should_send = test_mode or getattr(signal, 'signal_changed', True)
        
        if should_send:
            print("📧 Sending email notification...")
            email_sent = send_email(subject, body, smtp_server, smtp_port, smtp_user, smtp_password, to_email)
            
            if email_sent:
                print("✅ Email notification sent successfully!")
            else:
                print("❌ Failed to send email notification.")
                
            return email_sent
        else:
            print("No signal change detected. Email not sent.")
            return True  # Return True since this is expected behavior
            
    except Exception as e:
        print(f"❌ Error sending signal notification: {e}")
        return False
