#!/usr/bin/env python3
"""
Test script to generate and send a sample neutral mode multi-strategy email.

This script creates realistic mock data to demonstrate what the new email
template will look like when triggered by a live trading run.
"""

import smtplib
import sys
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Add the project root to Python path
sys.path.insert(0, "/Users/joshua.moreton/Documents/GitHub/the-alchemiser")

from the_alchemiser.core.ui.email.templates import EmailTemplates


class MockExecutionResult:
    """Mock execution result to simulate a real trading run."""

    def __init__(self):
        self.success = True

        # Mock consolidated portfolio (target allocations)
        self.consolidated_portfolio = {
            "SPY": 0.40,
            "QQQ": 0.25,
            "IWM": 0.15,
            "TLT": 0.10,
            "GLD": 0.10,
        }

        # Mock account info after execution
        self.account_info_after = {
            "status": "ACTIVE",
            "day_trade_count": 1,
            "portfolio_value": 110000.0,
            "equity": 110000.0,
            "cash": 5500.0,
            "open_positions": [
                {
                    "symbol": "SPY",
                    "qty": 200.0,
                    "market_value": 42000.0,
                    "unrealized_pl": 850.0,
                    "unrealized_plpc": 0.0206,
                },
                {
                    "symbol": "QQQ",
                    "qty": 150.0,
                    "market_value": 28500.0,
                    "unrealized_pl": -320.0,
                    "unrealized_plpc": -0.0111,
                },
                {
                    "symbol": "IWM",
                    "qty": 100.0,
                    "market_value": 16000.0,
                    "unrealized_pl": 125.0,
                    "unrealized_plpc": 0.0079,
                },
                {
                    "symbol": "TLT",
                    "qty": 120.0,
                    "market_value": 12000.0,
                    "unrealized_pl": -75.0,
                    "unrealized_plpc": -0.0062,
                },
                {
                    "symbol": "GLD",
                    "qty": 60.0,
                    "market_value": 6000.0,
                    "unrealized_pl": 45.0,
                    "unrealized_plpc": 0.0076,
                },
            ],
        }

        # Mock strategy signals
        self.strategy_signals = {
            "momentum": {
                "action": "BUY",
                "symbol": "SPY",
                "reason": "Strong momentum detected in SPY with RSI cooling from overbought levels. Price broke above resistance at $415 with high volume confirmation. Technical indicators show bullish divergence with MACD crossover.",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "technical_indicators": {
                    "SPY": {
                        "current_price": 418.50,
                        "ma_200": 405.80,
                        "rsi_10": 72.5,
                        "rsi_20": 68.2,
                    },
                    "QQQ": {
                        "current_price": 385.20,
                        "ma_200": 378.90,
                        "rsi_10": 75.1,
                        "rsi_20": 70.8,
                    },
                },
            },
            "mean_reversion": {
                "action": "SELL",
                "symbol": "TLT",
                "reason": "Bond yields showing reversal pattern after extended rally. TLT approaching resistance levels with declining momentum. Risk-off sentiment weakening as equity markets strengthen.",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "technical_indicators": {
                    "TLT": {"current_price": 98.75, "ma_200": 96.50, "rsi_10": 45.2, "rsi_20": 42.8}
                },
            },
            "risk_parity": {
                "action": "HOLD",
                "symbol": "GLD",
                "reason": "Gold maintaining stable range with balanced risk across asset classes. No immediate rebalancing needed based on current volatility patterns.",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "technical_indicators": {
                    "GLD": {
                        "current_price": 185.40,
                        "ma_200": 182.30,
                        "rsi_10": 55.7,
                        "rsi_20": 53.1,
                    }
                },
            },
        }

        # Mock orders executed
        self.orders_executed = [
            {"symbol": "SPY", "action": "BUY", "qty": 25, "price": 418.50},
            {"symbol": "QQQ", "action": "SELL", "qty": 10, "price": 385.20},
            {"symbol": "TLT", "action": "SELL", "qty": 15, "price": 98.75},
        ]


def send_email(html_content: str, recipient_email: str):
    """Send the email using Gmail SMTP."""

    # Email configuration
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    sender_email = "your-email@gmail.com"  # Replace with your email
    sender_password = "your-app-password"  # Replace with your app password

    # Create message
    message = MIMEMultipart("alternative")
    message["Subject"] = "The Alchemiser - Multi-Strategy Report Sample (Neutral Mode)"
    message["From"] = sender_email
    message["To"] = recipient_email

    # Add HTML content
    html_part = MIMEText(html_content, "html")
    message.attach(html_part)

    try:
        # Send email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipient_email, message.as_string())

        print(f"✅ Sample email sent successfully to {recipient_email}")

    except Exception as e:
        print(f"❌ Failed to send email: {str(e)}")
        print("Note: Update the email credentials in the script to enable sending")


def save_email_html(html_content: str, filename: str = "sample_email.html"):
    """Save the HTML content to a file for inspection."""
    filepath = f"/Users/joshua.moreton/Documents/GitHub/the-alchemiser/{filename}"

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"✅ Email HTML saved to: {filepath}")
    print("   You can open this file in a web browser to preview the email")


def main():
    """Generate and optionally send sample emails."""

    print("🚀 Generating sample multi-strategy emails...")

    # Create mock execution result
    mock_result = MockExecutionResult()

    # Generate both paper and live trading samples
    modes = [("paper", "PAPER"), ("live", "LIVE")]

    for mode_key, mode_display in modes:
        try:
            print(f"\n📧 Generating {mode_display} trading email sample...")

            # Generate the email HTML using the neutral template (only template we use)
            html_content = EmailTemplates.build_multi_strategy_report_neutral(
                result=mock_result, mode=mode_key
            )

            # Save to file for inspection
            filename = f"sample_{mode_key}_email.html"
            save_email_html(html_content, filename)

            print(f"✅ {mode_display} email content generated successfully")

        except Exception as e:
            print(f"❌ Error generating {mode_display} email: {str(e)}")
            import traceback

            traceback.print_exc()

    print("\n" + "=" * 60)
    print("SAMPLE EMAIL TEMPLATES GENERATED:")
    print("=" * 60)
    print("Template Architecture:")
    print("  ✅ Multi-Strategy Neutral Template (for all success cases)")
    print("  ✅ Error Templates (for failure cases)")
    print("  ❌ Single Strategy Templates (removed - not used)")
    print("  ❌ Non-Neutral Templates (removed - not used)")
    print("")
    print("Both PAPER and LIVE trading now use the same neutral template")
    print("Features demonstrated:")
    print("  • Portfolio rebalancing table with percentages")
    print("  • Account status without dollar amounts")
    print("  • Strategy signals with analysis")
    print("  • Market regime analysis")
    print("  • Trading activity summary")
    print("=" * 60)

    print("\n📁 Open the saved HTML files to see the email layouts:")
    print(
        "   Paper Trading: file:///Users/joshua.moreton/Documents/GitHub/the-alchemiser/sample_paper_email.html"
    )
    print(
        "   Live Trading:  file:///Users/joshua.moreton/Documents/GitHub/the-alchemiser/sample_live_email.html"
    )


if __name__ == "__main__":
    main()
