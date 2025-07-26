#!/usr/bin/env python3
"""
Email        if not email_address or not email_password:
            print("❌ Email credentials not configured!")
            print("\n📝 Please set up your email configuration:")
            print("   Option 1: config.yaml + AWS Secrets Manager")
            print("     - Add email settings to config.yaml")
            print("     - Store SMTP_PASSWORD in nuclear-secrets")
            print("   Option 2: Environment variables (EMAIL_ADDRESS, SMTP_PASSWORD, etc.)")
            print("\n📧 For iCloud users:")
            print("   - Use smtp.mail.me.com as SMTP server")
            print("   - Generate an app-specific password at appleid.apple.com")ration Test Script

This script helps you test your email notification setup for The Alchemiser.
Run this script to verify that your email configuration is working correctly
before running the actual trading bot.
"""

import sys
import os

# Add the project root to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_email_configuration():
    """Test the email notification system"""
    print("🧪 The Alchemiser - Email Configuration Test")
    print("=" * 50)
    
    try:
        from the_alchemiser.core.ui.email_utils import (
            send_email_notification, 
            build_error_email_html,
            build_trading_report_html,
            get_email_config
        )
        
        # Test 1: Check email configuration
        print("\n📋 Step 1: Checking email configuration...")
        email_config = get_email_config()
        
        if not email_config:
            print("❌ Email configuration failed to load!")
            print("\n📝 Please set up your email configuration:")
            print("   Option 1: config.yaml + AWS Secrets Manager")
            print("     - Add email settings to config.yaml")
            print("     - Store SMTP_PASSWORD in nuclear-secrets")
            print("   Option 2: Environment variables (EMAIL_ADDRESS, SMTP_PASSWORD, etc.)")
            print("\n📧 For iCloud users:")
            print("   - Use smtp.mail.me.com as SMTP server")
            print("   - Generate an app-specific password at appleid.apple.com")
            print("\n📖 See EMAIL_SETUP.md for detailed instructions")
            return False
            
        smtp_server, smtp_port, email_address, email_password, recipient_email = email_config
        
        if not email_address or not email_password:
            print("❌ Email credentials not configured!")
            print("\n📝 Please set up your email configuration:")
            print("   Option 1: AWS Secrets Manager (email-config secret)")
            print("   Option 2: Environment variables (EMAIL_ADDRESS, EMAIL_PASSWORD, etc.)")
            print("\n� For iCloud users:")
            print("   - Use smtp.mail.me.com as SMTP server")
            print("   - Generate an app-specific password at appleid.apple.com")
            print("   - Enable 2-Factor Authentication first")
            print("\n�📖 See EMAIL_SETUP.md for detailed instructions")
            return False
        
        if not recipient_email:
            print("❌ Recipient email not configured!")
            return False
        
        print(f"✅ Email configuration found:")
        print(f"   SMTP Server: {smtp_server}:{smtp_port}")
        print(f"   From: {email_address}")
        print(f"   To: {recipient_email}")
        
        # Test 2: Send test error email
        print("\n📧 Step 2: Sending test error alert email...")
        html_content = build_error_email_html(
            "Email Configuration Test", 
            "This is a test email to verify your Alchemiser email notifications are working correctly."
        )
        
        success = send_email_notification(
            subject="🧪 The Alchemiser - Email Configuration Test",
            html_content=html_content,
            text_content="Test email from The Alchemiser trading bot - Email notifications are working!"
        )
        
        if success:
            print("✅ Test error email sent successfully!")
        else:
            print("❌ Failed to send test error email")
            return False
        
        # Test 3: Send test trading report email
        print("\n📊 Step 3: Sending test trading report email...")
        
        # Mock data for testing
        mock_account = {
            'equity': 50000.00,
            'cash': 5000.00
        }
        
        mock_positions = [
            {
                'symbol': 'TECL',
                'market_value': 15000.00,
                'unrealized_pl': 1250.50,
                'unrealized_plpc': 0.091
            },
            {
                'symbol': 'SPY',
                'market_value': 12000.00,
                'unrealized_pl': -250.25,
                'unrealized_plpc': -0.020
            },
            {
                'symbol': 'BIL',
                'market_value': 8000.00,
                'unrealized_pl': 50.75,
                'unrealized_plpc': 0.006
            }
        ]
        
        mock_orders = [
            {
                'symbol': 'TECL',
                'side': 'BUY',
                'qty': 50
            },
            {
                'symbol': 'SPY',
                'side': 'SELL',
                'qty': 25
            }
        ]
        
        html_content = build_trading_report_html(
            mode="PAPER",
            success=True,
            account_before=mock_account,
            account_after=mock_account,
            positions={},
            orders=mock_orders,
            open_positions=mock_positions
        )
        
        success = send_email_notification(
            subject="📈 The Alchemiser - Test Trading Report",
            html_content=html_content,
            text_content="Test trading report email from The Alchemiser"
        )
        
        if success:
            print("✅ Test trading report email sent successfully!")
        else:
            print("❌ Failed to send test trading report email")
            return False
        
        print("\n🎉 Email configuration test completed successfully!")
        print("\n📬 Check your inbox for two test emails:")
        print("   1. Error alert email (red styling)")
        print("   2. Trading report email (with mock data)")
        print("\nIf you don't see the emails, check your spam/junk folder.")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure you're running this from the project root directory")
        return False
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main function"""
    success = test_email_configuration()
    
    if success:
        print("\n✅ Email system is ready for The Alchemiser!")
        sys.exit(0)
    else:
        print("\n❌ Email configuration needs attention")
        print("📖 Please see EMAIL_SETUP.md for configuration instructions")
        sys.exit(1)


if __name__ == "__main__":
    main()
