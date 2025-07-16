#!/usr/bin/env python3
"""
Nuclear Trading Strategy - Main Entry Point
Unified launcher for all nuclear trading operations
"""

# Standard library imports
import sys
import os
import argparse
from datetime import datetime
import traceback

# Add src directory to Python path for local imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def run_trading_bot():
    """Run the main nuclear trading bot for live signals"""
    print("🚀 NUCLEAR TRADING BOT - LIVE MODE")
    print("=" * 60)
    print(f"Running live trading analysis at {datetime.now()}")
    print()
    
    try:
        from core.nuclear_trading_bot import NuclearTradingBot
        
        # Create and run the bot
        bot = NuclearTradingBot()
        print("Fetching live market data and generating signal...")
        print()
        
        signal = bot.run_once()
        
        if signal:
            print()
            print("✅ Signal generated successfully!")
            print(f"📁 Alert logged to: data/logs/nuclear_alerts.json")
        else:
            print()
            print("⚠️  No clear signal generated")
        
        return True
        
    except Exception as e:
        print(f"❌ Error running trading bot: {e}")
        traceback.print_exc()
        return False


def run_alpaca_bot():
    """Run the nuclear trading bot with Alpaca execution"""
    print("🚀 NUCLEAR TRADING BOT - ALPACA EXECUTION MODE")
    print("=" * 60)
    print(f"Running live trading analysis with Alpaca paper trading at {datetime.now()}")
    print()
    
    try:
        # Import and run the core nuclear trading bot first to generate signals
        from core.nuclear_trading_bot import NuclearTradingBot
        
        print("📊 STEP 1: Generating Nuclear Trading Signals...")
        print("-" * 50)
        
        # Generate nuclear signals
        bot = NuclearTradingBot()
        print("Fetching live market data and generating signal...")
        print()
        
        signal = bot.run_once()
        
        if not signal:
            print("❌ Failed to generate nuclear signals")
            return False
        
        print("✅ Nuclear trading signals generated successfully!")
        print()
        
        # Import and initialize Alpaca trading bot
        print("🏦 STEP 2: Connecting to Alpaca Paper Trading...")
        print("-" * 50)
        
        from execution.alpaca_trader import AlpacaTradingBot
        
        # Initialize bot with paper trading
        alpaca_bot = AlpacaTradingBot(paper_trading=True)
        
        # Get account info before trading
        account_info_before = alpaca_bot.get_account_info()
        
        # Display account summary before trading
        print("📋 Account Status Before Trading:")
        alpaca_bot.display_account_summary()
        
        print("⚡ STEP 3: Executing Trades Based on Nuclear Signals...")
        print("-" * 50)
        
        # Execute nuclear strategy with Alpaca
        success = alpaca_bot.execute_nuclear_strategy()
        
        if success:
            print("✅ Trade execution completed successfully!")
        else:
            print("❌ Trade execution failed!")
        
        print()
        print("📊 STEP 4: Final Account Status...")
        print("-" * 50)
        
        # Get account info after trading
        account_info_after = alpaca_bot.get_account_info()
        
        # Display updated account summary
        alpaca_bot.display_account_summary()
        
        print()
        print("=" * 70)
        print("🎯 NUCLEAR ALPACA BOT EXECUTION COMPLETE")
        print("=" * 70)
        print()
        
        # Send email notification about the execution
        print("📧 STEP 5: Sending Email Notification...")
        print("-" * 50)
        
        send_alpaca_email_notification(success, account_info_before, account_info_after, alpaca_bot)
        
        return success
        
    except Exception as e:
        print(f"❌ Error running Alpaca bot: {e}")
        traceback.print_exc()
        return False


def send_alpaca_email_notification(success, account_before, account_after, alpaca_bot):
    """Send email notification about Alpaca bot execution"""
    try:
        from src.core.email_utils import send_email
        
        # Get current positions for portfolio summary
        positions = alpaca_bot.get_positions()
        
        # Calculate portfolio changes
        portfolio_value_before = account_before.get('portfolio_value', 0.0)
        portfolio_value_after = account_after.get('portfolio_value', 0.0)
        cash_before = account_before.get('cash', 0.0)
        cash_after = account_after.get('cash', 0.0)
        
        # Email configuration
        smtp_server = "smtp.mail.me.com"
        smtp_port = 587
        smtp_user = "joshuamoreton1@icloud.com"
        smtp_password = os.environ.get("SMTP_PASSWORD")
        to_email = "josh@rwxt.org"
        
        if not smtp_password:
            print("⚠️ SMTP_PASSWORD environment variable not set. Email notification skipped.")
            return
        
        # Format subject and body
        status_icon = "✅" if success else "❌"
        subject = f"{status_icon} Nuclear Alpaca Bot Execution - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        portfolio_change = portfolio_value_after - portfolio_value_before
        portfolio_change_pct = (portfolio_change / portfolio_value_before * 100) if portfolio_value_before > 0 else 0
        
        # Create positions summary
        if positions:
            positions_text = "\n📊 CURRENT POSITIONS:\n"
            for symbol, position in positions.items():
                qty = position.get('qty', 0)
                market_value = position.get('market_value', 0)
                current_price = position.get('current_price', 0)
                positions_text += f"   {symbol}: {qty} shares @ ${current_price:.2f} = ${market_value:.2f}\n"
        else:
            positions_text = "\n💰 CURRENT POSITIONS: 100% Cash\n"
        
        body = f"""Nuclear Alpaca Bot Execution Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

{status_icon} EXECUTION STATUS: {'SUCCESS' if success else 'FAILED'}

📈 ACCOUNT SUMMARY:
   Portfolio Value Before: ${portfolio_value_before:,.2f}
   Portfolio Value After:  ${portfolio_value_after:,.2f}
   Portfolio Change:       ${portfolio_change:+,.2f} ({portfolio_change_pct:+.2f}%)
   
   Cash Before: ${cash_before:,.2f}
   Cash After:  ${cash_after:,.2f}
   Cash Change: ${cash_after - cash_before:+,.2f}

{positions_text}

🤖 EXECUTION DETAILS:
   Strategy: Nuclear Energy Portfolio Rebalancing
   Trading Mode: Paper Trading (Alpaca)
   Execution Time: {datetime.now().strftime('%H:%M:%S')}
   
📋 LOGS:
   Check data/logs/alpaca_trader.log for detailed execution logs
   Check data/logs/nuclear_alerts.json for nuclear strategy signals
"""
        
        # Send email
        email_sent = send_email(subject, body, smtp_server, smtp_port, smtp_user, smtp_password, to_email)
        
        if email_sent:
            print("✅ Email notification sent successfully!")
        else:
            print("❌ Failed to send email notification.")
            
    except Exception as e:
        print(f"⚠️ Error sending email notification: {e}")
        traceback.print_exc()








def run_email_bot():
    """Run the nuclear trading bot with email notifications"""
    print("🚀 NUCLEAR TRADING BOT - EMAIL MODE")
    print("=" * 60)
    print(f"Running live trading analysis with email notifications at {datetime.now()}")
    print()
    
    try:
        from src.core.nuclear_signal_email import main as email_main
        
        # Run the email bot
        print("📧 Starting email-enabled nuclear trading bot...")
        email_main()
        
        return True
        
    except Exception as e:
        print(f"❌ Error running email bot: {e}")
        traceback.print_exc()
        return False

def main():
    parser = argparse.ArgumentParser(description="Nuclear Trading Strategy - Unified Entry Point")
    parser.add_argument('mode', choices=['bot', 'email', 'alpaca'], 
                       help='Operation mode to run')

    args = parser.parse_args()

    print("🚀 NUCLEAR TRADING STRATEGY")
    print("=" * 60)
    print(f"Mode: {args.mode}")
    print(f"Timestamp: {datetime.now()}")
    success = False
    try:
        if args.mode == 'bot':
            success = run_trading_bot()
        elif args.mode == 'email':
            success = run_email_bot()
        elif args.mode == 'alpaca':
            success = run_alpaca_bot()
    except Exception as e:
        print(f"\n💥 Operation failed due to error: {e}")
        traceback.print_exc()
        success = False
    if success:
        print("\n🎉 Operation completed successfully!")
        sys.exit(0)
    else:
        print("\n💥 Operation failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
