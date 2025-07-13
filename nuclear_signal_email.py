#!/usr/bin/env python3
"""
Nuclear Energy Daily Signal Check - Email Only
Sends an email with Nuclear Energy strategy signal status and portfolio allocation if the signal changes.
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json
import os
import warnings
warnings.filterwarnings('ignore')

# Import our Nuclear strategy components
from nuclear_trading_bot import NuclearStrategyEngine, TechnicalIndicators

def fetch_nuclear_signal():
    """Fetch the current Nuclear Energy strategy signal"""
    try:
        # Create strategy engine
        strategy = NuclearStrategyEngine()
        
        # Get market data
        market_data = strategy.get_market_data()
        if not market_data:
            raise ValueError("Failed to fetch market data")
        
        # Calculate indicators
        indicators = strategy.calculate_indicators(market_data)
        if not indicators:
            raise ValueError("Failed to calculate indicators")
        
        # Evaluate strategy
        symbol, action, reason = strategy.evaluate_nuclear_strategy(indicators, market_data)
        
        # Get current price for main signal
        current_price = strategy.data_provider.get_current_price(symbol)
        
        # Handle portfolio allocations
        portfolio = None
        portfolio_allocation = None
        
        # Check for nuclear portfolio signal
        if symbol == 'NUCLEAR_PORTFOLIO' and action == 'BUY':
            portfolio_allocation = strategy.get_nuclear_portfolio(indicators, market_data)
            if portfolio_allocation:
                portfolio = {}
                for sym, data in portfolio_allocation.items():
                    if sym in indicators:
                        portfolio[sym] = {
                            'weight': data['weight'],
                            'price': indicators[sym]['current_price'],
                            'performance': data['performance']
                        }
        
        # Check for UVXY/BTAL portfolio signal
        elif symbol == 'UVXY_BTAL_PORTFOLIO' and action == 'BUY':
            portfolio = {
                'UVXY': {
                    'weight': 0.75,
                    'price': strategy.data_provider.get_current_price('UVXY'),
                    'performance': 0.0
                },
                'BTAL': {
                    'weight': 0.25,
                    'price': strategy.data_provider.get_current_price('BTAL'),
                    'performance': 0.0
                }
            }
            
        # Check for bear market portfolio signal
        elif symbol == 'BEAR_PORTFOLIO' and action == 'BUY':
            # Extract portfolio allocation from reason string
            import re
            portfolio_match = re.findall(r'(\w+) \((\d+\.?\d*)%\)', reason)
            
            if portfolio_match:
                portfolio = {}
                for stock_symbol, allocation_str in portfolio_match:
                    allocation_weight = float(allocation_str) / 100.0
                    portfolio[stock_symbol] = {
                        'weight': allocation_weight,
                        'price': strategy.data_provider.get_current_price(stock_symbol),
                        'performance': 0.0
                    }
        
        # Check for signal change by comparing with previous signal
        signal_changed = check_signal_change(symbol, action, reason)
        
        return {
            'success': True,
            'date': datetime.now().strftime('%Y-%m-%d'),
            'symbol': symbol,
            'action': action,
            'reason': reason,
            'price': current_price,
            'portfolio': portfolio,
            'signal_changed': signal_changed,
            'market_data': {
                'spy_price': indicators.get('SPY', {}).get('current_price', 0),
                'spy_ma_200': indicators.get('SPY', {}).get('ma_200', 0),
                'spy_rsi_10': indicators.get('SPY', {}).get('rsi_10', 0),
                'market_regime': 'Bull' if indicators.get('SPY', {}).get('current_price', 0) > indicators.get('SPY', {}).get('ma_200', 0) else 'Bear'
            }
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'date': datetime.now().strftime('%Y-%m-%d')
        }

def check_signal_change(current_symbol, current_action, current_reason):
    """Check if the signal has changed from the previous day"""
    signal_file = 'nuclear_last_signal.json'
    
    # Try to load previous signal
    try:
        with open(signal_file, 'r') as f:
            prev_signal = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        prev_signal = None
    
    # Save current signal
    current_signal = {
        'symbol': current_symbol,
        'action': current_action,
        'reason': current_reason,
        'date': datetime.now().strftime('%Y-%m-%d')
    }
    
    try:
        with open(signal_file, 'w') as f:
            json.dump(current_signal, f)
    except Exception as e:
        print(f"Warning: Could not save signal to file: {e}")
    
    # Check if signal changed
    if prev_signal is None:
        return True  # First run, consider it a change
    
    # Check if key components changed
    signal_changed = (
        prev_signal.get('symbol') != current_symbol or
        prev_signal.get('action') != current_action or
        prev_signal.get('reason') != current_reason
    )
    
    return signal_changed

def format_email_body(signal_data):
    """Format the email body with signal information"""
    if not signal_data['success']:
        return f"""
Nuclear Energy Strategy Error on {signal_data['date']}

❌ Error: {signal_data['error']}

Please check the system logs for more information.
"""
    
    # Signal change indicator
    change_indicator = " 🔄 SIGNAL CHANGED!" if signal_data['signal_changed'] else ""
    
    # Market data
    market = signal_data['market_data']
    spy_vs_ma = ((market['spy_price'] / market['spy_ma_200']) - 1) * 100 if market['spy_ma_200'] > 0 else 0
    
    # Action emoji
    action_emoji = "🚨" if signal_data['action'] == 'BUY' else "⏸️" if signal_data['action'] == 'HOLD' else "🔴"
    
    # Determine subject and signal description
    signal_description = signal_data['symbol']
    if signal_data['symbol'] == 'NUCLEAR_PORTFOLIO':
        signal_description = f"Nuclear Portfolio ({len(signal_data['portfolio'])} stocks)"
    elif signal_data['symbol'] == 'UVXY_BTAL_PORTFOLIO':
        signal_description = "UVXY/BTAL Hedge Portfolio"
    elif signal_data['symbol'] == 'BEAR_PORTFOLIO':
        signal_description = f"Bear Market Portfolio ({len(signal_data['portfolio'])} positions)"
    
    body = f"""Nuclear Energy Strategy Signal - {signal_data['date']}

{action_emoji} SIGNAL: {signal_data['action']} {signal_description}{change_indicator}

📊 MARKET CONDITIONS:
• SPY Price: ${market['spy_price']:.2f}
• SPY 200-MA: ${market['spy_ma_200']:.2f}
• SPY vs MA: {spy_vs_ma:+.1f}%
• SPY RSI(10): {market['spy_rsi_10']:.1f}
• Market Regime: {market['market_regime']}

🎯 SIGNAL DETAILS:
• Symbol: {signal_data['symbol']}
• Action: {signal_data['action']}
• Reason: {signal_data['reason']}

"""
    
    # Add portfolio allocation if available
    if signal_data['portfolio']:
        if signal_data['symbol'] == 'NUCLEAR_PORTFOLIO':
            body += "💼 NUCLEAR PORTFOLIO ALLOCATION:\n"
            body += "(Top 3 nuclear stocks by 90-day MA return - Inverse Volatility Weighted)\n\n"
        elif signal_data['symbol'] == 'UVXY_BTAL_PORTFOLIO':
            body += "🛡️ VOLATILITY HEDGE ALLOCATION:\n"
            body += "(UVXY 75% / BTAL 25% allocation per original Composer strategy)\n\n"
        elif signal_data['symbol'] == 'BEAR_PORTFOLIO':
            body += "🐻 BEAR MARKET PORTFOLIO ALLOCATION:\n"
            body += "(Combined Bear1 & Bear2 strategies - 14-day Inverse Volatility Weighted)\n\n"
        else:
            body += "💼 PORTFOLIO ALLOCATION:\n\n"
        
        for symbol, data in signal_data['portfolio'].items():
            shares_10k = (10000 * data['weight']) / data['price']
            body += f"• {symbol}: {data['weight']:.1%} @ ${data['price']:.2f} ({shares_10k:.1f} shares for $10K)\n"
            if data['performance'] != 0.0:
                body += f"  90-day MA Return: {data['performance']:.2f}%\n"
            body += "\n"
    else:
        # Single stock signal
        body += f"• Price: ${signal_data['price']:.2f}\n\n"
    
    body += """
📈 TRADING GUIDANCE:
• This is a deterministic strategy with no confidence scoring
• Signals are based on RSI levels, moving averages, and market regimes
• In bull markets: Focus on nuclear energy portfolio
• In bear markets: Tech shorts and bond/volatility plays
• In overbought conditions: Volatility protection (UVXY)

⚠️ IMPORTANT: This is for educational purposes only. Not financial advice.
Always do your own research before making trading decisions.

Nuclear Energy Strategy | Based on Composer.trade Symphony
"""
    
    return body

def send_email_signal(signal_data, smtp_server, smtp_port, smtp_user, smtp_password, to_email):
    """Send email with signal information"""
    
    # Determine signal description for subject
    signal_description = signal_data['symbol']
    if signal_data['symbol'] == 'NUCLEAR_PORTFOLIO':
        signal_description = f"Nuclear Portfolio"
    elif signal_data['symbol'] == 'UVXY_BTAL_PORTFOLIO':
        signal_description = "UVXY/BTAL Hedge"
    elif signal_data['symbol'] == 'BEAR_PORTFOLIO':
        signal_description = "Bear Market Portfolio"
    
    # Determine subject based on signal change and type
    if signal_data['signal_changed']:
        subject_prefix = "🔄 SIGNAL CHANGE"
    else:
        subject_prefix = "📊 Daily Update"
    
    if signal_data['success']:
        subject = f"{subject_prefix}: Nuclear Energy - {signal_data['action']} {signal_description} ({signal_data['date']})"
    else:
        subject = f"❌ Nuclear Energy Strategy Error - {signal_data['date']}"
    
    # Format email body
    body = format_email_body(signal_data)
    
    # Create email
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
        
        print(f"Email sent successfully to {to_email}")
        return True
        
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False

def test_email_workflow():
    """Test the email sending workflow with dummy signal data"""
    print("\n=== TESTING NUCLEAR ENERGY EMAIL WORKFLOW ===")
    
    # Dummy signal data simulating a nuclear portfolio signal
    test_signal_data = {
        'success': True,
        'date': datetime.now().strftime('%Y-%m-%d'),
        'symbol': 'SMR',
        'action': 'BUY',
        'reason': 'Bull market - Nuclear portfolio: SMR (33.3%), LEU (33.3%), OKLO (33.3%)',
        'price': 37.48,
        'portfolio': {
            'SMR': {'weight': 0.333, 'price': 37.48, 'performance': 1.23},
            'LEU': {'weight': 0.333, 'price': 206.40, 'performance': 1.15},
            'OKLO': {'weight': 0.333, 'price': 56.08, 'performance': 0.99}
        },
        'signal_changed': True,
        'market_data': {
            'spy_price': 623.62,
            'spy_ma_200': 580.82,
            'spy_rsi_10': 72.1,
            'market_regime': 'Bull'
        }
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
    result = send_email_signal(test_signal_data, smtp_server, smtp_port, smtp_user, smtp_password, to_email)
    
    if result:
        print("✅ Test email sent successfully.")
    else:
        print("❌ Test email failed.")

def main():
    """Main function"""
    print("🚀 Nuclear Energy Daily Signal Check (Email Only)")
    print("=" * 50)
    
    try:
        # Fetch current signal
        signal_data = fetch_nuclear_signal()
        
        if signal_data['success']:
            print(f"✅ Signal fetched successfully: {signal_data['action']} {signal_data['symbol']}")
            print(f"   Reason: {signal_data['reason']}")
            print(f"   Signal changed: {signal_data['signal_changed']}")
            
            # Only send email if signal changed or it's an error
            if signal_data['signal_changed']:
                print("📧 Signal changed - sending email...")
                
                # Email config for Apple Mail/iCloud
                smtp_server = "smtp.mail.me.com"
                smtp_port = 587
                smtp_user = "joshuamoreton1@icloud.com"  # Replace with your iCloud email
                smtp_password = os.environ.get("SMTP_PASSWORD")
                to_email = "josh@rwxt.org"  # Replace with recipient
                
                if not smtp_password:
                    print("❌ SMTP_PASSWORD environment variable not set. Email not sent.")
                    return
                
                send_email_signal(signal_data, smtp_server, smtp_port, smtp_user, smtp_password, to_email)
            else:
                print("📊 No signal change. No email sent.")
        else:
            print(f"❌ Error fetching signal: {signal_data['error']}")
            
            # Send error email
            smtp_server = "smtp.mail.me.com"
            smtp_port = 587
            smtp_user = "joshuamoreton1@icloud.com"  # Replace with your iCloud email
            smtp_password = os.environ.get("SMTP_PASSWORD")
            to_email = "josh@rwxt.org"  # Replace with recipient
            
            if smtp_password:
                send_email_signal(signal_data, smtp_server, smtp_port, smtp_user, smtp_password, to_email)
            else:
                print("❌ SMTP_PASSWORD environment variable not set. Error email not sent.")
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()
    # Uncomment the line below to test the email workflow
    # test_email_workflow()
