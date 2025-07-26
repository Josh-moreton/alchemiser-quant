#!/usr/bin/env python3
"""
Test email formatting and create sample emails to evaluate design quality
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from the_alchemiser.core.ui.email_utils import (
    send_email_notification, 
    build_trading_report_html,
    build_multi_strategy_email_html,
    build_error_email_html,
    get_email_config
)

def test_email_config():
    """Test email configuration"""
    print("🔧 Testing email configuration...")
    config = get_email_config()
    if config:
        smtp_server, smtp_port, from_email, _, to_email = config
        print(f"✅ Email config loaded successfully")
        print(f"   SMTP: {smtp_server}:{smtp_port}")
        print(f"   From: {from_email}")
        print(f"   To: {to_email}")
        return True
    else:
        print("❌ Email configuration failed")
        return False

def create_sample_trading_report():
    """Create a comprehensive sample trading report"""
    print("📊 Creating sample trading report...")
    
    # Sample data for a successful trading session
    account_before = {
        'equity': 95000.00,
        'cash': 45000.00
    }
    
    account_after = {
        'equity': 98500.00,
        'cash': 42000.00
    }
    
    # Sample positions (winners and losers)
    open_positions = [
        {
            'symbol': 'NVDA',
            'market_value': 25000,
            'unrealized_pl': 2500.00,
            'unrealized_plpc': 0.11
        },
        {
            'symbol': 'TSLA', 
            'market_value': 18000,
            'unrealized_pl': -800.00,
            'unrealized_plpc': -0.043
        },
        {
            'symbol': 'AAPL',
            'market_value': 15000,
            'unrealized_pl': 750.00,
            'unrealized_plpc': 0.053
        },
        {
            'symbol': 'MSFT',
            'market_value': 12000,
            'unrealized_pl': 300.00,
            'unrealized_plpc': 0.026
        },
        {
            'symbol': 'UVXY',
            'market_value': 8000,
            'unrealized_pl': 150.00,
            'unrealized_plpc': 0.019
        }
    ]
    
    # Sample orders
    orders = [
        {
            'side': 'buy',
            'symbol': 'NVDA',
            'qty': 50,
            'filled_price': 485.50
        },
        {
            'side': 'sell',
            'symbol': 'TSLA',
            'qty': 25,
            'filled_price': 195.25
        },
        {
            'side': 'buy',
            'symbol': 'AAPL',
            'qty': 100,
            'filled_price': 150.75
        }
    ]
    
    # Sample signal
    class MockSignal:
        def __init__(self):
            self.action = "BUY"
            self.symbol = "NVDA"
            self.reason = "Strong momentum breakout with high volume"
    
    signal = MockSignal()
    
    html_content = build_trading_report_html(
        mode="LIVE",
        success=True,
        account_before=account_before,
        account_after=account_after,
        positions={},
        orders=orders,
        signal=signal,
        open_positions=open_positions
    )
    
    return html_content

def create_sample_multi_strategy_report():
    """Create a sample multi-strategy report"""
    print("🎯 Creating sample multi-strategy report...")
    
    class MockResult:
        def __init__(self):
            self.success = True
            self.consolidated_portfolio = {
                'NVDA': 0.25,
                'TSLA': 0.20, 
                'AAPL': 0.15,
                'MSFT': 0.15,
                'UVXY': 0.10,
                'CASH': 0.15
            }
            self.execution_summary = {
                'strategy_summary': {
                    'Nuclear': {
                        'allocation': 0.50,
                        'signal': 'BUY'
                    },
                    'TECL': {
                        'allocation': 0.50, 
                        'signal': 'HOLD'
                    }
                },
                'trading_summary': {
                    'total_trades': 5,
                    'total_buy_value': 45000,
                    'total_sell_value': 12000
                },
                'account_info_after': {
                    'equity': 98500.00,
                    'cash': 42000.00
                }
            }
    
    result = MockResult()
    html_content = build_multi_strategy_email_html(result, "LIVE")
    return html_content

def create_sample_error_report():
    """Create a sample error report"""
    print("❌ Creating sample error report...")
    
    error_message = """API connection timeout: Failed to connect to Alpaca Trading API after 3 retries.
    
Error details:
- Connection timeout after 30 seconds
- Last successful connection: 2025-01-26 14:30:15 UTC
- Retry attempts: 3/3 failed
- Network status: Connected
    
Suggested actions:
1. Check Alpaca API status at status.alpaca.markets
2. Verify API credentials are valid
3. Check network connectivity
4. Review rate limiting settings"""
    
    html_content = build_error_email_html(
        "LIVE Trading Connection Failed",
        error_message
    )
    return html_content

def send_sample_emails():
    """Send sample emails to test formatting"""
    
    # Test 1: Successful trading report
    print("\n📧 Sending sample successful trading report...")
    trading_html = create_sample_trading_report()
    success1 = send_email_notification(
        subject="🧪 [SAMPLE] The Alchemiser - LIVE Trading Success Report",
        html_content=trading_html,
        text_content="Sample successful trading report - please view in HTML"
    )
    print(f"   {'✅ Sent' if success1 else '❌ Failed'}")
    
    # Test 2: Multi-strategy report
    print("\n📧 Sending sample multi-strategy report...")
    multi_html = create_sample_multi_strategy_report()
    success2 = send_email_notification(
        subject="🧪 [SAMPLE] The Alchemiser - Multi-Strategy Portfolio Report",
        html_content=multi_html,
        text_content="Sample multi-strategy report - please view in HTML"
    )
    print(f"   {'✅ Sent' if success2 else '❌ Failed'}")
    
    # Test 3: Error report
    print("\n📧 Sending sample error report...")
    error_html = create_sample_error_report()
    success3 = send_email_notification(
        subject="🧪 [SAMPLE] The Alchemiser - LIVE Trading Error Alert",
        html_content=error_html,
        text_content="Sample error report - critical trading system failure"
    )
    print(f"   {'✅ Sent' if success3 else '❌ Failed'}")
    
    return success1 and success2 and success3

def main():
    """Main test function"""
    print("🧪 The Alchemiser - Email Formatting Test Suite")
    print("=" * 60)
    
    # Test email configuration
    if not test_email_config():
        print("❌ Email configuration failed - cannot send test emails")
        return False
    
    print("\n" + "=" * 60)
    print("📧 SENDING SAMPLE EMAILS FOR DESIGN REVIEW")
    print("=" * 60)
    print("These emails will help us evaluate the current design quality")
    print("and identify areas for improvement to make them more enterprise-grade.")
    print()
    
    # Send sample emails
    success = send_sample_emails()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ All sample emails sent successfully!")
        print("\n📋 Please review the emails in your inbox and evaluate:")
        print("   • Overall visual design and branding")
        print("   • Data presentation and readability") 
        print("   • Mobile responsiveness")
        print("   • Professional appearance")
        print("   • Information hierarchy")
        print("   • Color scheme and typography")
    else:
        print("❌ Some emails failed to send")
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
