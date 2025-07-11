#!/usr/bin/env python3
"""
LQQ3 Daily Signal Check - 150-day SMA Strategy (Popup Only)
Shows a macOS popup with TQQQ signal status and trading guidance.
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import subprocess
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

def create_popup(signal_data):
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
    message_escaped = message.replace('"', '\"')
    title_escaped = title.replace('"', '\"')
    script = f'display dialog "{message_escaped}" with title "{title_escaped}" buttons ["OK"] default button "OK"'
    cmd = ["osascript", "-e", script]
    try:
        subprocess.run(cmd, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Failed to create popup: {e}")
        return False

def main():
    print("🚀 LQQ3 Daily Signal Check (Popup Only)")
    print("=" * 40)
    try:
        signal_data = fetch_daily_signal()
        create_popup(signal_data)
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
