#!/usr/bin/env python3
"""
Test script for the new UnifiedDataProvider class.
"""

import logging
import sys
import os

# Add the core directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core'))

from core.data_provider import UnifiedDataProvider, DataProvider, AlpacaDataProvider

def test_unified_provider():
    """Test the UnifiedDataProvider functionality."""
    print("🧪 Testing UnifiedDataProvider")
    print("=" * 50)
    
    try:
        # Initialize with paper trading (safe for testing)
        unified = UnifiedDataProvider(paper_trading=True)
        print(f"✅ UnifiedDataProvider initialized successfully")
        print(f"   Paper trading: {unified.paper_trading}")
        print(f"   Cache duration: {unified.cache_duration}s")
        
        # Test cache stats
        stats = unified.get_cache_stats()
        print(f"   Cache stats: {stats}")
        
        # Test getting data for a simple symbol
        print("\n📊 Testing data fetching...")
        test_symbol = "SPY"
        
        data = unified.get_data(test_symbol, period="1mo", interval="1d")
        if not data.empty:
            print(f"✅ Successfully fetched {len(data)} bars for {test_symbol}")
            print(f"   Columns: {list(data.columns)}")
            print(f"   Date range: {data.index[0]} to {data.index[-1]}")
            print(f"   Latest close: ${data['Close'].iloc[-1]:.2f}")
        else:
            print(f"❌ No data returned for {test_symbol}")
        
        # Test current price
        print(f"\n💰 Testing current price for {test_symbol}...")
        current_price = unified.get_current_price(test_symbol)
        if current_price:
            print(f"✅ Current price: ${current_price:.2f}")
        else:
            print(f"❌ Could not get current price for {test_symbol}")
        
        # Test cache (should be faster second time)
        print(f"\n⚡ Testing cache performance...")
        import time
        
        start_time = time.time()
        data2 = unified.get_data(test_symbol, period="1mo", interval="1d")
        cache_time = time.time() - start_time
        
        if not data2.empty:
            print(f"✅ Cached data retrieved in {cache_time:.3f}s")
            print(f"   Same data: {len(data) == len(data2) and data.equals(data2)}")
        
        # Test account info (if available)
        print(f"\n🏦 Testing account info...")
        account = unified.get_account_info()
        if account:
            print(f"✅ Account info retrieved")
            print(f"   Account status: {getattr(account, 'status', 'unknown')}")
        else:
            print(f"❌ Could not retrieve account info")
        
        print(f"\n✅ UnifiedDataProvider tests completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ UnifiedDataProvider test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def compare_providers():
    """Compare UnifiedDataProvider with existing providers."""
    print("\n🔄 Comparing Providers")
    print("=" * 50)
    
    test_symbol = "SPY"
    
    try:
        # Test DataProvider (old)
        print("Testing original DataProvider...")
        old_provider = DataProvider()
        old_data = old_provider.get_data(test_symbol, period="1mo", interval="1d")
        old_price = old_provider.get_current_price(test_symbol)
        print(f"   DataProvider: {len(old_data)} bars, price: ${old_price or 0:.2f}")
        
        # Test AlpacaDataProvider (old)
        print("Testing AlpacaDataProvider...")
        alpaca_provider = AlpacaDataProvider(paper_trading=True)
        alpaca_price = alpaca_provider.get_current_price(test_symbol)
        print(f"   AlpacaDataProvider: price: ${alpaca_price or 0:.2f}")
        
        # Test UnifiedDataProvider (new)
        print("Testing UnifiedDataProvider...")
        unified_provider = UnifiedDataProvider(paper_trading=True)
        unified_data = unified_provider.get_data(test_symbol, period="1mo", interval="1d")
        unified_price = unified_provider.get_current_price(test_symbol)
        print(f"   UnifiedDataProvider: {len(unified_data)} bars, price: ${unified_price or 0:.2f}")
        
        # Compare results
        print(f"\n📊 Comparison Results:")
        print(f"   Data consistency: {len(old_data) == len(unified_data) if not old_data.empty and not unified_data.empty else 'N/A'}")
        print(f"   Price consistency: {abs((old_price or 0) - (unified_price or 0)) < 1.0 if old_price and unified_price else 'N/A'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Provider comparison failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    print("🚀 UnifiedDataProvider Test Suite")
    print("=" * 60)
    
    # Run tests
    unified_success = test_unified_provider()
    comparison_success = compare_providers()
    
    # Summary
    print(f"\n📋 Test Summary")
    print("=" * 30)
    print(f"UnifiedDataProvider: {'✅ PASS' if unified_success else '❌ FAIL'}")
    print(f"Provider Comparison: {'✅ PASS' if comparison_success else '❌ FAIL'}")
    
    if unified_success and comparison_success:
        print(f"\n🎉 All tests passed! UnifiedDataProvider is ready for use.")
        print(f"\n💡 Next steps:")
        print(f"   1. Update strategy_manager.py to use UnifiedDataProvider")
        print(f"   2. Update other modules that use DataProvider/AlpacaDataProvider")
        print(f"   3. Test the full application")
        print(f"   4. Remove old provider classes")
    else:
        print(f"\n⚠️ Some tests failed. Please review the issues before proceeding.")
