#!/usr/bin/env python3
"""
Simple Alpaca Connection Debug
Test basic Alpaca connection with minimal dependencies
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_env_variables():
    """Test if environment variables are loaded correctly"""
    print("🔍 Testing Environment Variables...")
    print("-" * 40)
    
    # Check if .env is loaded
    api_key = os.getenv('ALPACA_PAPER_KEY')
    secret_key = os.getenv('ALPACA_PAPER_SECRET')
    endpoint = os.getenv('ALPACA_PAPER_ENDPOINT')
    
    print(f"ALPACA_PAPER_KEY: {'✅ Found' if api_key else '❌ Missing'}")
    if api_key:
        print(f"  Key (masked): {api_key[:8]}...")
    
    print(f"ALPACA_PAPER_SECRET: {'✅ Found' if secret_key else '❌ Missing'}")
    if secret_key:
        print(f"  Secret (masked): {secret_key[:8]}...")
    
    print(f"ALPACA_PAPER_ENDPOINT: {'✅ Found' if endpoint else '❌ Missing'}")
    if endpoint:
        print(f"  Endpoint: {endpoint}")
    
    return api_key and secret_key

def test_alpaca_import():
    """Test if Alpaca SDK can be imported"""
    print("\n📦 Testing Alpaca SDK Import...")
    print("-" * 40)
    
    try:
        from alpaca.trading.client import TradingClient
        print("✅ TradingClient imported successfully")
        
        from alpaca.trading.requests import MarketOrderRequest
        print("✅ MarketOrderRequest imported successfully")
        
        from alpaca.trading.enums import OrderSide, TimeInForce
        print("✅ Trading enums imported successfully")
        
        from alpaca.data.historical import StockHistoricalDataClient
        print("✅ StockHistoricalDataClient imported successfully")
        
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_basic_connection():
    """Test basic Alpaca connection"""
    print("\n🔌 Testing Basic Alpaca Connection...")
    print("-" * 40)
    
    try:
        from alpaca.trading.client import TradingClient
        
        api_key = os.getenv('ALPACA_PAPER_KEY')
        secret_key = os.getenv('ALPACA_PAPER_SECRET')
        
        if not api_key or not secret_key:
            print("❌ Cannot test connection - missing credentials")
            return False
        
        # Initialize client
        trading_client = TradingClient(
            api_key=api_key,
            secret_key=secret_key,
            paper=True
        )
        print("✅ TradingClient initialized")
        
        # Try to get account info
        account = trading_client.get_account()
        print("✅ Account info retrieved successfully")
        
        # Try to access account attributes safely
        account_status = getattr(account, 'status', 'unknown')
        portfolio_value = getattr(account, 'portfolio_value', 'unknown')
        
        print(f"  Status: {account_status}")
        print(f"  Portfolio Value: {portfolio_value}")
        
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print(f"   Error type: {type(e).__name__}")
        return False

def main():
    """Run all tests"""
    print("🧪 ALPACA CONNECTION DEBUG")
    print("=" * 50)
    
    # Test 1: Environment variables
    env_ok = test_env_variables()
    
    # Test 2: SDK import
    import_ok = test_alpaca_import()
    
    # Test 3: Basic connection (only if previous tests pass)
    connection_ok = False
    if env_ok and import_ok:
        connection_ok = test_basic_connection()
    
    # Summary
    print("\n📊 TEST SUMMARY")
    print("=" * 50)
    print(f"Environment Variables: {'✅ Pass' if env_ok else '❌ Fail'}")
    print(f"SDK Import: {'✅ Pass' if import_ok else '❌ Fail'}")
    print(f"Connection: {'✅ Pass' if connection_ok else '❌ Fail'}")
    
    if env_ok and import_ok and connection_ok:
        print("\n🎉 All tests passed! Alpaca is ready to use.")
    else:
        print("\n🔧 Some tests failed. Check the issues above.")

if __name__ == "__main__":
    main()
