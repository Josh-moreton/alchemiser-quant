import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
#!/usr/bin/env python3
"""
LQQ3 Daily Signal Check - 150-day SMA Strategy
Daily popup with TQQQ signal status and trading guidance
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import subprocess
import sys
import shutil
import platform
import warnings
warnings.filterwarnings('ignore')

def fetch_daily_signal():
    """Fetch TQQQ data and calculate 150-day SMA signal"""
    try:
        # --- Config ---
        TICKER = "TQQQ"
        SMA_PERIOD = 150
        
        # --- Fetch Data ---
        end_date = datetime.now()
        start_date = end_date - timedelta(days=SMA_PERIOD*2)  # Extra buffer for weekends/holidays
        
        print(f"Fetching {TICKER} data...")
        data = yf.download(TICKER, start=start_date, end=end_date, progress=False)
        
        if data.empty:
            raise ValueError(f"Failed to fetch {TICKER} data from Yahoo Finance")
        
        # Handle multi-level columns that yfinance sometimes returns
        if data.columns.nlevels > 1:
            data.columns = data.columns.get_level_values(0)
        
        if 'Close' not in data.columns:
            raise ValueError("Downloaded data does not contain 'Close' prices")
        
        # --- Calculate SMA ---
        data['SMA'] = data['Close'].rolling(window=SMA_PERIOD).mean()
        
        # Drop rows where SMA cannot be calculated
        data = data.dropna(subset=['SMA'])
        
        if data.empty:
            raise ValueError(f"Not enough data to compute {SMA_PERIOD}-day SMA")
        
        # Get latest and previous day data
        latest = data.iloc[-1]
        previous = data.iloc[-2] if len(data) > 1 else latest
        
        # Extract values
        latest_close = float(latest['Close'])
        latest_sma = float(latest['SMA'])
        prev_close = float(previous['Close'])
        prev_sma = float(previous['SMA'])
        
        # --- Determine Current Signal ---
        current_signal = int(latest_close > latest_sma)
        previous_signal = int(prev_close > prev_sma)
        signal_changed = current_signal != previous_signal
        
        signal_str = "IN (Buy/Hold LQQ3)" if current_signal else "OUT (Sell 66%/Hold Cash)"
        
        # --- Generate Guidance ---
        if current_signal == 1:  # Bullish signal
            if signal_changed:
                guidance = "🟢 Signal just turned IN: BUY LQQ3 with available cash!"
            else:
                guidance = "🟢 Signal IN: Hold LQQ3 position."
        else:  # Bearish signal
            if signal_changed:
                guidance = "🔴 Signal just turned OUT: SELL 66% of LQQ3 position!"
            else:
                guidance = "🔴 Signal OUT: Hold remaining LQQ3/cash."
        
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
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def create_popup(signal_data):
    """Create macOS popup notification if running on macOS"""
    # Skip popup on non-macOS systems or if osascript is unavailable
    if platform.system() != "Darwin" or shutil.which("osascript") is None:
        print("Popup notifications require macOS with osascript. Skipping.")
        return False

    if not signal_data['success']:
        message = f"❌ Error fetching signal data:\n{signal_data['error']}"
        title = "LQQ3 Signal Error"
    else:
        price_vs_sma = signal_data['price_vs_sma_pct']
        change_indicator = " 🔄 CHANGED!" if signal_data['signal_changed'] else ""
        
        message = (
            f"TQQQ Close: ${signal_data['tqqq_close']:.2f}\n"
            f"150-SMA: ${signal_data['sma_150']:.2f}\n"
            f"Price vs SMA: {price_vs_sma:+.1f}%\n"
            f"Signal: {signal_data['signal_str']}{change_indicator}\n\n"
            f"{signal_data['guidance']}"
        )
        title = "LQQ3 Daily Signal"
    
    # Create macOS dialog (centered popup with OK button)
    # Escape double quotes for AppleScript
    message_escaped = message.replace('"', '\"')
    title_escaped = title.replace('"', '\"')
    script = f'display dialog "{message_escaped}" with title "{title_escaped}" buttons ["OK"] default button "OK"'
    cmd = ["osascript", "-e", script]
    try:
        subprocess.run(cmd, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"Failed to create popup: {e}")
        return False

def send_email_signal_change(signal_data, smtp_server, smtp_port, smtp_user, smtp_password, to_email):
    """Send an email if the signal has changed"""
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

def main():
    """Main execution function"""
    print("🚀 LQQ3 Daily Signal Check")
    print("=" * 40)
    
    # Fetch signal data
    signal_data = fetch_daily_signal()
    
    # Display results in console
    if signal_data['success']:
        data = signal_data
        print(f"Date: {data['date']}")
        print(f"TQQQ Close: ${data['tqqq_close']:.2f}")
        print(f"150-day SMA: ${data['sma_150']:.2f}")
        print(f"Price vs SMA: {data['price_vs_sma_pct']:+.1f}%")
        print(f"Signal: {data['signal_str']}")
        if data['signal_changed']:
            print("🔄 SIGNAL CHANGED!")
        print(f"Guidance: {data['guidance']}")
    else:
        print(f"❌ Error: {signal_data['error']}")
    

    # Create popup notification
    create_popup(signal_data)

    # Email config for Apple Mail/iCloud
    smtp_server = "smtp.mail.me.com"
    smtp_port = 587
    smtp_user = "joshuamoreton1@icloud.com"  # Replace with your iCloud email
    smtp_password = "hdrn-ihkv-labz-mvgp"  # Replace with your app-specific password
    to_email = "josh@rwxt.org"  # Replace with recipient

    # Only send email if signal changed
    if signal_data['success'] and signal_data['signal_changed']:
        send_email_signal_change(signal_data, smtp_server, smtp_port, smtp_user, smtp_password, to_email)

    return signal_data

def test_email_workflow():
    """Test the email sending workflow with dummy signal data."""
    print("\n=== TESTING EMAIL WORKFLOW ===")
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

    print("Sending test email...")
    result = send_email_signal_change(test_signal_data, smtp_server, smtp_port, smtp_user, smtp_password, to_email)
    if result:
        print("Test email sent successfully.")
    else:
        print("Test email failed.")

# To run the test, uncomment the following line:
# test_email_workflow()

if __name__ == "__main__":
    main()
