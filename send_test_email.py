#!/usr/bin/env python3
"""
Test script to send a sample neutral mode email.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from the_alchemiser.core.ui.email.config import is_neutral_mode_enabled
from the_alchemiser.core.ui.email.templates import EmailTemplates
from the_alchemiser.core.ui.email import send_email_notification

def create_sample_data():
    """Create sample trading data for the test email."""
    
    # Sample execution result data
    mode = "PAPER"
    success = True
    
    account_before = {
        "equity": 48500.00,
        "cash": 2500.00,
        "status": "ACTIVE"
    }
    
    account_after = {
        "equity": 52750.00,
        "cash": 1250.00,
        "status": "ACTIVE",
        "daytrade_count": 2,
        "buying_power": 105000.00
    }
    
    # Sample portfolio positions
    positions = {
        "AAPL": 0.25,
        "TSLA": 0.30,
        "NVDA": 0.20,
        "MSFT": 0.15,
        "GOOGL": 0.10
    }
    
    # Sample orders executed
    orders = [
        {
            "side": "BUY",
            "symbol": "AAPL", 
            "qty": 15.5,
            "estimated_value": 2650.00,
            "order_type": "MARKET"
        },
        {
            "side": "SELL",
            "symbol": "TSLA",
            "qty": 8.0,
            "estimated_value": 1840.00,
            "order_type": "MARKET"
        },
        {
            "side": "BUY",
            "symbol": "NVDA",
            "qty": 3.25,
            "estimated_value": 1450.00,
            "order_type": "LIMIT"
        }
    ]
    
    # Sample open positions
    open_positions = [
        {
            "symbol": "AAPL",
            "qty": 25.5,
            "market_value": 4335.00,
            "unrealized_pl": 185.50,
            "unrealized_plpc": 0.0447,
            "avg_entry_price": 162.75
        },
        {
            "symbol": "TSLA", 
            "qty": 12.0,
            "market_value": 2760.00,
            "unrealized_pl": -95.25,
            "unrealized_plpc": -0.0333,
            "avg_entry_price": 237.94
        },
        {
            "symbol": "NVDA",
            "qty": 5.25,
            "market_value": 2341.25,
            "unrealized_pl": 67.80,
            "unrealized_plpc": 0.0298,
            "avg_entry_price": 433.42
        },
        {
            "symbol": "MSFT",
            "qty": 18.0,
            "market_value": 7650.00,
            "unrealized_pl": 315.75,
            "unrealized_plpc": 0.0431,
            "avg_entry_price": 407.46
        }
    ]
    
    return {
        "mode": mode,
        "success": success,
        "account_before": account_before,
        "account_after": account_after,
        "positions": positions,
        "orders": orders,
        "open_positions": open_positions
    }

def send_regular_email():
    """Send a regular email with financial data."""
    print("Generating regular email with financial data...")
    
    data = create_sample_data()
    
    # Generate regular email template
    html_content = EmailTemplates.build_trading_report(
        mode=data["mode"],
        success=data["success"],
        account_before=data["account_before"],
        account_after=data["account_after"],
        positions=data["positions"],
        orders=data["orders"],
        open_positions=data["open_positions"]
    )
    
    # Send email
    result = send_email_notification(
        subject="📈 The Alchemiser - REGULAR MODE Test Email",
        html_content=html_content,
        text_content="Test email with regular financial reporting template"
    )
    
    if result:
        print("✅ Regular email sent successfully!")
    else:
        print("❌ Failed to send regular email")
    
    return result

def send_neutral_email():
    """Send a neutral email without financial data."""
    print("Generating neutral email without financial data...")
    
    data = create_sample_data()
    
    # Generate neutral email template
    html_content = EmailTemplates.build_trading_report_neutral(
        mode=data["mode"],
        success=data["success"],
        account_before=data["account_before"],
        account_after=data["account_after"],
        positions=data["positions"],
        orders=data["orders"],
        open_positions=data["open_positions"]
    )
    
    # Send email
    result = send_email_notification(
        subject="📈 The Alchemiser - NEUTRAL MODE Test Email",
        html_content=html_content,
        text_content="Test email with neutral reporting template (no financial values)"
    )
    
    if result:
        print("✅ Neutral email sent successfully!")
    else:
        print("❌ Failed to send neutral email")
    
    return result

def main():
    """Main function to send test emails."""
    print("🧪 The Alchemiser Email Template Test\n")
    
    # Check current neutral mode setting
    neutral_mode = is_neutral_mode_enabled()
    print(f"Current neutral mode setting: {neutral_mode}\n")
    
    # Ask user which email type to send
    choice = input("Which email would you like to send?\n1. Regular email (with $ values)\n2. Neutral email (no $ values)\n3. Both\nChoice (1/2/3): ").strip()
    
    print()
    
    if choice == "1":
        send_regular_email()
    elif choice == "2":
        send_neutral_email()
    elif choice == "3":
        print("Sending both email types...\n")
        send_regular_email()
        print()
        send_neutral_email()
    else:
        print("Invalid choice. Please run again and select 1, 2, or 3.")
        return
    
    print("\n📧 Test email(s) sent! Check your inbox.")

if __name__ == "__main__":
    main()
