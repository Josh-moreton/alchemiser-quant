#!/usr/bin/env python3
"""
Debug script to test the neutral email template with detailed error reporting.
"""

import sys
import os
import traceback
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_neutral_template():
    """Test the neutral template generation with detailed error reporting."""
    try:
        print("Importing modules...")
        from the_alchemiser.core.ui.email.templates import EmailTemplates
        from the_alchemiser.core.ui.email.templates.portfolio import PortfolioBuilder
        from the_alchemiser.core.ui.email.templates.performance import PerformanceBuilder
        print("✅ Modules imported successfully")
        
        # Test data
        print("Creating test data...")
        data = {
            "mode": "PAPER",
            "success": True,
            "account_before": {"equity": 48500.00},
            "account_after": {
                "equity": 52750.00,
                "cash": 1250.00,
                "status": "ACTIVE",
                "daytrade_count": 2
            },
            "positions": {"AAPL": 0.25, "TSLA": 0.30},
            "orders": [
                {
                    "side": "BUY",
                    "symbol": "AAPL", 
                    "qty": 15.5,
                    "estimated_value": 2650.00
                }
            ],
            "open_positions": [
                {
                    "symbol": "AAPL",
                    "qty": 25.5,
                    "market_value": 4335.00,
                    "unrealized_pl": 185.50,
                    "unrealized_plpc": 0.0447
                }
            ]
        }
        print("✅ Test data created")
        
        # Test individual neutral functions
        print("Testing neutral functions individually...")
        
        print("  - Testing build_account_summary_neutral...")
        account_html = PortfolioBuilder.build_account_summary_neutral(data["account_after"])
        print("  ✅ Account summary works")
        
        print("  - Testing build_trading_activity_neutral...")
        trading_html = PerformanceBuilder.build_trading_activity_neutral(data["orders"])
        print("  ✅ Trading activity works")
        
        print("  - Testing build_positions_table_neutral...")
        positions_html = PortfolioBuilder.build_positions_table_neutral(data["open_positions"])
        print("  ✅ Positions table works")
        
        # Test full template
        print("Testing full neutral template...")
        html_content = EmailTemplates.build_trading_report_neutral(
            mode=data["mode"],
            success=data["success"],
            account_before=data["account_before"],
            account_after=data["account_after"],
            positions=data["positions"],
            orders=data["orders"],
            open_positions=data["open_positions"]
        )
        print("✅ Full neutral template generated successfully")
        print(f"Template length: {len(html_content)} characters")
        
        return html_content
        
    except Exception as e:
        print(f"❌ Error occurred: {e}")
        print("Full traceback:")
        traceback.print_exc()
        return None

def test_email_sending():
    """Test sending the neutral email with detailed error reporting."""
    try:
        print("\nTesting email sending...")
        from the_alchemiser.core.ui.email import send_email_notification
        
        # Generate template
        html_content = test_neutral_template()
        if not html_content:
            print("❌ Failed to generate template")
            return False
        
        print("Attempting to send email...")
        result = send_email_notification(
            subject="🧪 DEBUG - Neutral Email Test",
            html_content=html_content,
            text_content="Debug test of neutral email template"
        )
        
        if result:
            print("✅ Email sent successfully!")
        else:
            print("❌ Email sending failed")
        
        return result
        
    except Exception as e:
        print(f"❌ Email sending error: {e}")
        print("Full traceback:")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔍 Debug Test - Neutral Email Template\n")
    
    # Test template generation
    test_neutral_template()
    
    # Test email sending
    test_email_sending()
    
    print("\n🔍 Debug test completed!")
