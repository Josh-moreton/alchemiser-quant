#!/usr/bin/env python3
"""
Test Alpaca Connection
Simple script to test the Alpaca API connection and display account info
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from execution.alpaca_trader import AlpacaTradingBot

def test_connection():
    """Test Alpaca API connection"""
    try:
        print("🧪 Testing Alpaca API Connection...")
        print("="*50)
        
        # Initialize bot with paper trading
        bot = AlpacaTradingBot(paper_trading=True)
        
        # Test account info
        print("📊 Fetching Account Information...")
        account_info = bot.get_account_info()
        
        if account_info:
            print("✅ Account Connection Successful!")
            print(f"   Portfolio Value: ${account_info.get('portfolio_value', 0):,.2f}")
            print(f"   Cash: ${account_info.get('cash', 0):,.2f}")
            print(f"   Buying Power: ${account_info.get('buying_power', 0):,.2f}")
            print(f"   Status: {account_info.get('status', 'unknown')}")
        else:
            print("❌ Failed to get account information")
            return False
        
        # Test positions
        print("\n📈 Fetching Current Positions...")
        positions = bot.get_positions()
        
        if positions:
            print(f"✅ Found {len(positions)} positions:")
            for symbol, pos in positions.items():
                print(f"   {symbol}: {pos['qty']} shares @ ${pos['current_price']:.2f}")
        else:
            print("✅ No current positions (empty portfolio)")
        
        # Test price fetching
        print("\n💰 Testing Price Fetching...")
        test_symbols = ['AAPL', 'SPY', 'SMR']
        for symbol in test_symbols:
            price = bot.get_current_price(symbol)
            if price > 0:
                print(f"   {symbol}: ${price:.2f}")
            else:
                print(f"   {symbol}: ❌ Failed to get price")
        
        print("\n✅ All tests passed! Alpaca connection is working.")
        return True
        
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        return False

if __name__ == "__main__":
    test_connection()
