#!/usr/bin/env python3
"""
Simple Post-Trade Validation Test

Tests the post-trade validation module with minimal API calls to respect rate limits.
"""

import sys
import os
from datetime import datetime

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from the_alchemiser.core.post_trade_validator import PostTradeValidator

def test_module_import():
    """Test that the module imports correctly"""
    print("🔍 Testing module import...")
    try:
        validator = PostTradeValidator()
        print("✅ PostTradeValidator imported successfully")
        print(f"   Rate limit: {validator.max_requests_per_minute}/minute")
        print(f"   Nuclear indicators: {validator.nuclear_indicators}")
        print(f"   TECL indicators: {validator.tecl_indicators}")
        return True
    except Exception as e:
        print(f"❌ Module import failed: {e}")
        return False

def test_api_key_retrieval():
    """Test API key retrieval from AWS Secrets Manager"""
    print("\n🔍 Testing API key retrieval...")
    try:
        validator = PostTradeValidator()
        api_key = validator._get_api_key()
        if api_key:
            print("✅ API key retrieved successfully")
            print(f"   Key length: {len(api_key)} characters")
            return True
        else:
            print("❌ No API key found")
            return False
    except Exception as e:
        print(f"❌ API key retrieval failed: {e}")
        return False

def test_single_validation_minimal():
    """Test validation for a single symbol with minimal API calls"""
    print("\n🔍 Testing single symbol validation (SPY only)...")
    print("   This will make ~4 API calls (RSI 10/20, MA 20/200)")
    print("   Respecting rate limits...")
    
    try:
        validator = PostTradeValidator()
        result = validator.validate_symbol('SPY', 'nuclear')
        
        print(f"\n📊 Validation Result:")
        print(f"   Symbol: {result['symbol']}")
        print(f"   Strategy: {result['strategy']}")
        print(f"   Status: {result['status']}")
        print(f"   Current price: ${result.get('current_price', 0):.2f}")
        
        # Show validation results
        successful_validations = 0
        total_validations = 0
        
        for indicator, validation in result['validations'].items():
            if validation['status'] not in ['custom_indicator', 'unavailable']:
                total_validations += 1
                if validation['status'] in ['excellent', 'good']:
                    successful_validations += 1
        
        print(f"   External validations: {successful_validations}/{total_validations} successful")
        
        # Show a couple examples
        if 'rsi_10' in result['validations']:
            rsi_val = result['validations']['rsi_10']
            our_val = rsi_val['our_value']
            td_val = rsi_val.get('twelvedata_value', 'N/A')
            status = rsi_val['status']
            if td_val != 'N/A':
                diff = rsi_val.get('difference', 0)
                print(f"   RSI(10): Our={our_val:.1f} | TwelveData={td_val:.1f} | Diff={diff:.1f} | {status}")
        
        if 'ma_20' in result['validations']:
            ma_val = result['validations']['ma_20']
            our_val = ma_val['our_value']
            td_val = ma_val.get('twelvedata_value', 'N/A')
            status = ma_val['status']
            if td_val != 'N/A':
                diff = ma_val.get('difference', 0)
                pct_diff = ma_val.get('percent_difference', 0)
                print(f"   MA(20): Our={our_val:.2f} | TwelveData={td_val:.2f} | Diff={diff:.2f} ({pct_diff:.2f}%) | {status}")
        
        return result['status'] in ['success', 'partial']
        
    except Exception as e:
        print(f"❌ Validation failed: {e}")
        return False

def test_integration_function():
    """Test the main integration function"""
    print("\n🔍 Testing integration function (no API calls)...")
    try:
        from the_alchemiser.core.post_trade_validator import validate_after_live_trades
        
        # Test with async_mode=True (should return None immediately)
        result = validate_after_live_trades(
            nuclear_symbols=['SPY'],
            tecl_symbols=None,
            async_mode=True  # This won't make API calls, just starts background thread
        )
        
        if result is None:
            print("✅ Async validation function works correctly")
            print("   (Background validation started, no blocking)")
            return True
        else:
            print("❌ Async function should return None")
            return False
            
    except Exception as e:
        print(f"❌ Integration function test failed: {e}")
        return False

def main():
    """Run minimal validation tests"""
    print("🤖 POST-TRADE VALIDATION - MINIMAL TEST")
    print("=" * 50)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print("This test validates the post-trade validation system")
    print("with minimal API usage to respect rate limits.")
    print()
    
    tests = [
        ("Module Import", test_module_import),
        ("API Key Retrieval", test_api_key_retrieval),
        ("Integration Function", test_integration_function),
        ("Single Validation", test_single_validation_minimal),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"📋 Running: {test_name}")
        try:
            if test_func():
                print(f"✅ {test_name} PASSED")
                passed += 1
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} ERROR: {e}")
        
        print()
    
    print("🏁 TEST SUMMARY")
    print("=" * 30)
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed!")
        print("\n💡 The post-trade validation system is ready for live trading!")
        print("   Use 'python main.py trade --live' to enable automatic validation")
    else:
        print(f"⚠️  {total - passed} tests failed")
        print("   Check API key configuration and network connectivity")

if __name__ == "__main__":
    main()
