#!/usr/bin/env python3
"""Test the enhanced Orders Executed section in email"""

import sys
sys.path.insert(0, '/Users/joshua.moreton/Documents/GitHub/the-alchemiser')

from the_alchemiser.core.ui.email_utils import build_trading_report_html

def test_orders_executed_email():
    """Test the enhanced Orders Executed section"""
    
    # Sample orders data matching the CLI format  
    orders = [
        {
            'side': 'SELL',
            'symbol': 'FNGU', 
            'qty': 49.884463,
            'estimated_value': 1305.23
        },
        {
            'side': 'BUY',
            'symbol': 'TECL',
            'qty': 10.666518, 
            'estimated_value': 1129.80
        },
        {
            'side': 'BUY', 
            'symbol': 'OKLO',
            'qty': 94.660235,
            'estimated_value': 7021.88
        }
    ]
    
    # Build the email HTML
    html_content = build_trading_report_html(
        mode="LIVE",
        success=True, 
        account_before={'equity': 100000, 'cash': 5000},
        account_after={'equity': 101500, 'cash': 4800},
        positions={},
        orders=orders,
        signal=None,
        open_positions=[]
    )
    
    # Save to file for viewing
    with open('test_orders_executed_email.html', 'w') as f:
        f.write(html_content)
    
    print("✅ Email test file created: test_orders_executed_email.html")
    print("📧 Enhanced Orders Executed section includes:")
    print("   • Type (BUY/SELL with colors)")
    print("   • Symbol")
    print("   • Quantity (6 decimal precision)")
    print("   • Estimated Value")
    print("   • Summary with totals")
    print("   • Order count in title")

if __name__ == "__main__":
    test_orders_executed_email()
