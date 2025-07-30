#!/usr/bin/env python3
"""
Demo script to show the portfolio P&L functionality in action.
"""

import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from the_alchemiser.core.ui.email_utils import _build_closed_positions_pnl_email_html

def demo_email_template():
    """Demonstrate the closed position P&L email template"""
    print("📧 Demo: Closed Position P&L Email Template")
    print("=" * 50)
    
    # Create realistic test data
    test_account_info = {
        'recent_closed_pnl': [
            {
                'symbol': 'UVXY',
                'realized_pnl': 360.71,
                'realized_pnl_pct': 15.2,
                'trade_count': 26,
                'last_trade_date': '2024-07-29T14:52:00Z'
            },
            {
                'symbol': 'TECL',
                'realized_pnl': -325.58,
                'realized_pnl_pct': -0.59,
                'trade_count': 31,
                'last_trade_date': '2024-07-29T15:03:00Z'
            },
            {
                'symbol': 'OKLO',
                'realized_pnl': -153.28,
                'realized_pnl_pct': -0.86,
                'trade_count': 7,
                'last_trade_date': '2024-07-29T15:11:00Z'
            },
            {
                'symbol': 'SMR',
                'realized_pnl': 245.83,
                'realized_pnl_pct': 2.1,
                'trade_count': 19,
                'last_trade_date': '2024-07-29T15:34:00Z'
            }
        ]
    }
    
    # Generate HTML
    html_content = _build_closed_positions_pnl_email_html(test_account_info)
    
    # Save to file for viewing
    output_file = "/tmp/portfolio_pnl_demo.html"
    with open(output_file, 'w') as f:
        # Create a complete HTML document for viewing
        f.write(f"""
<!DOCTYPE html>
<html>
<head>
    <title>Portfolio P&L Demo</title>
    <style>
        body {{ 
            font-family: 'Segoe UI', sans-serif; 
            margin: 20px; 
            background-color: #f5f5f5; 
        }}
        .progress-bar {{
            background-color: #E5E7EB;
            border-radius: 4px;
            overflow: hidden;
            height: 8px;
            margin: 4px 0;
        }}
        .progress-fill {{
            background: linear-gradient(90deg, #10B981, #059669);
            height: 100%;
            transition: width 0.3s ease;
        }}
    </style>
</head>
<body>
    <h1>🧪 The Alchemiser - Portfolio P&L Demo</h1>
    <div style="background: white; padding: 20px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
        {html_content}
    </div>
</body>
</html>
        """)
    
    print(f"✅ Demo HTML saved to: {output_file}")
    print(f"📊 Generated HTML size: {len(html_content):,} characters")
    print()
    
    # Show summary of what was generated
    print("📋 Email Template Contents:")
    print("   - Recent Closed Positions P&L section")
    print("   - Professional HTML table with gradient styling")
    print("   - Color-coded P&L values (green/red)")
    print("   - Symbol, P&L amount, P&L %, trade count, last trade date")
    print("   - Total realized P&L summary row")
    print()
    
    # Calculate summary stats
    total_realized = sum(pos['realized_pnl'] for pos in test_account_info['recent_closed_pnl'])
    winners = [pos for pos in test_account_info['recent_closed_pnl'] if pos['realized_pnl'] > 0]
    losers = [pos for pos in test_account_info['recent_closed_pnl'] if pos['realized_pnl'] < 0]
    
    print("💰 Demo P&L Summary:")
    print(f"   Total Realized P&L: ${total_realized:.2f}")
    print(f"   Winning Positions: {len(winners)}")
    print(f"   Losing Positions: {len(losers)}")
    print(f"   Best Performer: {max(test_account_info['recent_closed_pnl'], key=lambda x: x['realized_pnl'])['symbol']}")
    print(f"   Worst Performer: {min(test_account_info['recent_closed_pnl'], key=lambda x: x['realized_pnl'])['symbol']}")
    
    print(f"\n🌐 Open the demo HTML file to see the email template:")
    print(f"   open {output_file}")

if __name__ == "__main__":
    demo_email_template()
