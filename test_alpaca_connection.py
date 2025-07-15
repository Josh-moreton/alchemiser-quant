#!/usr/bin/env python3
"""
Test Alpaca Market Data API connection
"""

import os
import pandas as pd
from dotenv import load_dotenv
import traceback

# Load environment variables
load_dotenv()

def test_alpaca_connection():
    """Test basic Alpaca Market Data API connection"""
    
    print("🔍 Testing Alpaca Market Data API Connection...")
    print("=" * 50)
    
    # Check credentials
    api_key = os.getenv('ALPACA_PAPER_KEY') or os.getenv('ALPACA_KEY')
    secret_key = os.getenv('ALPACA_PAPER_SECRET') or os.getenv('ALPACA_SECRET')
    
    print(f"📋 API Key: {api_key[:8] if api_key else 'None'}...")
    print(f"📋 Secret Key: {secret_key[:8] if secret_key else 'None'}...")
    
    if not api_key or not secret_key:
        print("❌ No Alpaca credentials found!")
        return False
    
    try:
        # Import Alpaca modules
        from alpaca.data.historical import StockHistoricalDataClient
        from alpaca.data.requests import StockBarsRequest
        from alpaca.data.timeframe import TimeFrame
        
        print("✅ Alpaca modules imported successfully")
        
        # Create client
        client = StockHistoricalDataClient(api_key=api_key, secret_key=secret_key)
        print("✅ Alpaca client created successfully")
        
        # Test with a simple request for SPY
        print("\n📊 Testing data request for SPY...")
        
        request = StockBarsRequest(
            symbol_or_symbols=['SPY'],  # Try as list
            timeframe=TimeFrame.Day,  # type: ignore
            start=pd.Timestamp('2024-12-01'),
            end=pd.Timestamp('2024-12-31')
        )
        print("✅ Request object created")
        
        # Make the API call
        response = client.get_stock_bars(request)
        print(f"✅ API call successful! Response type: {type(response)}")
        
        # Inspect response
        print(f"📋 Response attributes: {[attr for attr in dir(response) if not attr.startswith('_')]}")
        
        # Check if response has data
        if hasattr(response, 'data'):
            data = getattr(response, 'data')  # type: ignore
            print(f"📊 Response data type: {type(data)}")
            print(f"📊 Data keys: {list(data.keys()) if hasattr(data, 'keys') else 'No keys'}")
            
            if 'SPY' in data:
                spy_data = data['SPY']  # type: ignore
                print(f"✅ SPY data found! {len(spy_data)} bars")
                
                # Show first few bars
                for i, bar in enumerate(spy_data[:3]):
                    print(f"Bar {i+1}: {bar.timestamp} - Close: ${bar.close}")  # type: ignore
                    
                return True
            else:
                print("❌ No SPY data in response")
                
        elif hasattr(response, 'SPY'):
            spy_data = getattr(response, 'SPY')
            print(f"✅ SPY data found as attribute! {len(spy_data)} bars")
            return True
        else:
            print("❌ Unable to find data in response")
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure alpaca-py is installed: pip install alpaca-py")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("📋 Full traceback:")
        traceback.print_exc()
        
    return False

def test_alternative_approach():
    """Test with alternative API approach"""
    print("\n🔄 Trying alternative approach...")
    
    try:
        # Try using the trading API for market data (fallback)
        from alpaca.trading.client import TradingClient
        
        api_key = os.getenv('ALPACA_PAPER_KEY') or os.getenv('ALPACA_KEY')
        secret_key = os.getenv('ALPACA_PAPER_SECRET') or os.getenv('ALPACA_SECRET')
        
        client = TradingClient(api_key=api_key, secret_key=secret_key, paper=True)
        
        # Get account info to test connection
        account = client.get_account()
        print(f"✅ Trading API connection successful! Account: {getattr(account, 'id', 'unknown')}")  # type: ignore
        
        print("ℹ️  Note: Market data access may require separate subscription")
        return True
            
    except Exception as e:
        print(f"❌ Alternative approach failed: {e}")
        
    return False

if __name__ == "__main__":
    success = test_alpaca_connection()
    
    if not success:
        test_alternative_approach()
        
    print("\n" + "=" * 50)
    print("Test completed!")
