#!/usr/bin/env python3
"""
LQQ3 Daily Signal Check - 150-day SMA Strategy (Email Only)
Sends an email with TQQQ signal status and trading guidance if the signal changes.
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import warnings
warnings.filterwarnings('ignore')

def fetch_daily_signal():
    TICKER = "TQQQ"
    SMA_PERIOD = 150
    end_date = datetime.now()
    start_date = end_date - timedelta(days=SMA_PERIOD*2)
    data = yf.download(TICKER, start=start_date, end=end_date, progress=False)
    if data.empty:
        raise ValueError(f"Failed to fetch {TICKER} data from Yahoo Finance")
    if data.columns.nlevels > 1:
        data.columns = data.columns.get_level_values(0)
    if 'Close' not in data.columns:
        raise ValueError("Downloaded data does not contain 'Close' prices")
    data['SMA'] = data['Close'].rolling(window=SMA_PERIOD).mean()
    data = data.dropna(subset=['SMA'])
    if data.empty:
        raise ValueError(f"Not enough data to compute {SMA_PERIOD}-day SMA")
    latest = data.iloc[-1]
    previous = data.iloc[-2] if len(data) > 1 else latest
    latest_close = float(latest['Close'])
    latest_sma = float(latest['SMA'])
    prev_close = float(previous['Close'])
    prev_sma = float(previous['SMA'])
    current_signal = int(latest_close > latest_sma)
    previous_signal = int(prev_close > prev_sma)
    signal_changed = current_signal != previous_signal
    signal_str = "IN (Buy/Hold LQQ3)" if current_signal else "OUT (Sell 66%/Hold Cash)"
    if current_signal == 1:
        guidance = "🟢 Signal just turned IN: BUY LQQ3 with available cash!" if signal_changed else "🟢 Signal IN: Hold LQQ3 position."
    else:
        guidance = "🔴 Signal just turned OUT: SELL 66% of LQQ3 position!" if signal_changed else "🔴 Signal OUT: Hold remaining LQQ3/cash."
    return {
        'success': True,
        'date': latest.name.strftime('%Y-%m-%d'),
        'tqqq_close': latest_close,
        'sma_150': latest_sma,
        'signal': current_signal,
        'signal_str': signal_str,
        'guidance': guidance,
        'signal_changed': signal_changed,
        'price_vs_sma_pct': ((latest_close / latest_sma) - 1) * 100
    }

def send_email_signal_change(signal_data, smtp_server, smtp_port, smtp_user, smtp_password, to_email):
    price_vs_sma = signal_data['price_vs_sma_pct']
    change_indicator = " 🔄 CHANGED!" if signal_data['signal_changed'] else ""
    subject = f"LQQ3 Signal Change: {signal_data['signal_str']} on {signal_data['date']}"
    body = (
        f"TQQQ Close: ${signal_data['tqqq_close']:.2f}\n"
        f"150-SMA: ${signal_data['sma_150']:.2f}\n"
        f"Price vs SMA: {price_vs_sma:+.1f}%\n"
        f"Signal: {signal_data['signal_str']}{change_indicator}\n\n"
        f"{signal_data['guidance']}"
    )
    msg = MIMEMultipart()
    msg['From'] = smtp_user
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))
    print(f"Connecting to SMTP server: {smtp_server}:{smtp_port} as {smtp_user}")
    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            print("EHLO...")
            server.ehlo()
            print("Starting TLS...")
            server.starttls()
            print("EHLO again...")
            server.ehlo()
            print("Logging in...")
            server.login(smtp_user, smtp_password)
            print("Sending email...")
            server.sendmail(smtp_user, to_email, msg.as_string())
        print(f"Email sent to {to_email}")
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False

def test_email_workflow():
    """Test the email sending workflow with dummy signal data."""
    print("\n=== TESTING EMAIL WORKFLOW ===")
    from datetime import datetime
    import os
    # Dummy signal data simulating a signal change
    test_signal_data = {
        'success': True,
        'date': datetime.now().strftime('%Y-%m-%d'),
        'tqqq_close': 100.0,
        'sma_150': 98.0,
        'signal': 1,
        'signal_str': 'IN (Buy/Hold LQQ3)',
        'guidance': '🟢 Signal just turned IN: BUY LQQ3 with available cash!',
        'signal_changed': True,
        'price_vs_sma_pct': 2.04
    }
    # Email config for Apple Mail/iCloud
    smtp_server = "smtp.mail.me.com"
    smtp_port = 587
    smtp_user = "joshuamoreton1@icloud.com"  # Replace with your iCloud email
    smtp_password = os.environ.get("SMTP_PASSWORD")
    to_email = "josh@rwxt.org"  # Replace with recipient

    if not smtp_password:
        print("❌ SMTP_PASSWORD environment variable not set. Test email not sent.")
        return

    print("Sending test email...")
    result = send_email_signal_change(test_signal_data, smtp_server, smtp_port, smtp_user, smtp_password, to_email)
    if result:
        print("Test email sent successfully.")
    else:
        print("Test email failed.")

def main():
    print("🚀 LQQ3 Daily Signal Check (Email Only)")
    print("=" * 40)
    import os
    try:
        signal_data = fetch_daily_signal()
        if signal_data['success'] and signal_data['signal_changed']:
            # Email config for Apple Mail/iCloud
            smtp_server = "smtp.mail.me.com"
            smtp_port = 587
            smtp_user = "joshuamoreton1@icloud.com"  # Replace with your iCloud email
            smtp_password = os.environ.get("SMTP_PASSWORD")
            to_email = "josh@rwxt.org"  # Replace with recipient
            if not smtp_password:
                print("❌ SMTP_PASSWORD environment variable not set. Email not sent.")
                return
            send_email_signal_change(signal_data, smtp_server, smtp_port, smtp_user, smtp_password, to_email)
        else:
            print("No signal change. No email sent.")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    # main()
    test_email_workflow()
