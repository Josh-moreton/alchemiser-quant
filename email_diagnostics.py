#!/usr/bin/env python3
"""
Email configuration diagnostic script.
"""

import logging
from the_alchemiser.core.ui.email.config import get_email_config, is_neutral_mode_enabled

def test_email_config():
    """Test email configuration and diagnose issues."""
    print("🔍 Diagnosing email configuration...\n")
    
    # Test config loading
    try:
        config_result = get_email_config()
        
        if config_result is None:
            print("❌ Email configuration failed to load")
            return False
            
        smtp_server, smtp_port, from_email, email_password, to_email = config_result
        
        print("✅ Email configuration loaded successfully:")
        print(f"   SMTP Server: {smtp_server}")
        print(f"   SMTP Port: {smtp_port}")
        print(f"   From Email: {from_email}")
        print(f"   To Email: {to_email}")
        print(f"   Password Available: {'Yes' if email_password else 'No'}")
        
        if not email_password:
            print("\n⚠️  WARNING: No email password found in AWS Secrets Manager!")
            print("   Check that 'SMTP_PASSWORD' is set in the 'nuclear-secrets' secret")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Error loading email config: {e}")
        return False

def test_email_send():
    """Test sending a simple email with detailed error reporting."""
    print("\n📧 Testing email send with detailed logging...\n")
    
    # Enable debug logging
    logging.basicConfig(level=logging.DEBUG)
    
    try:
        from the_alchemiser.core.ui.email.client import send_email_notification
        
        result = send_email_notification(
            subject="🧪 The Alchemiser - Email Test",
            html_content="<h1>Test Email</h1><p>This is a test email to verify SMTP configuration.</p>",
            text_content="Test Email - This is a test email to verify SMTP configuration."
        )
        
        if result:
            print("✅ Email sent successfully!")
        else:
            print("❌ Email sending failed!")
            
        return result
        
    except Exception as e:
        print(f"❌ Email sending failed with error: {e}")
        return False

def check_neutral_mode():
    """Check neutral mode setting."""
    print(f"\n⚙️  Neutral mode enabled: {is_neutral_mode_enabled()}")

if __name__ == "__main__":
    print("🔧 Email Configuration Diagnostics\n")
    
    # Run diagnostics
    config_ok = test_email_config()
    check_neutral_mode()
    
    if config_ok:
        test_email_send()
    else:
        print("\n❌ Cannot test email sending due to configuration issues")
        
    print("\n🏁 Diagnostics complete!")
