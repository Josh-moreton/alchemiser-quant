#!/usr/bin/env python3
"""
Simple Test Runner and Setup for Alpaca Trading Bot
Sets up testing environment and runs basic validation
"""

import sys
import os
import subprocess
import json
from pathlib import Path

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))


def install_test_dependencies():
    """Install required test dependencies"""
    print("📦 Installing test dependencies...")
    
    try:
        # Install basic testing packages
        subprocess.check_call([
            sys.executable, '-m', 'pip', 'install', 
            'pytest>=7.0.0',
            'pytest-mock>=3.10.0', 
            'pytest-cov>=4.0.0'
        ])
        print("✅ Test dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False


def run_basic_validation():
    """Run basic validation without pytest"""
    print("\n🔧 Running Basic Bot Validation...")
    
    try:
        # Test 1: Import test
        print("Testing imports...")
        from execution.alpaca_trader import AlpacaTradingBot
        print("✅ AlpacaTradingBot import successful")
        
        # Test 2: Mock initialization test
        print("Testing mock initialization...")
        from unittest.mock import patch, Mock
        
        with patch.dict(os.environ, {
            'ALPACA_PAPER_KEY': 'test_key',
            'ALPACA_PAPER_SECRET': 'test_secret'
        }):
            with patch('execution.alpaca_trader.TradingClient') as mock_trading:
                with patch('execution.alpaca_trader.StockHistoricalDataClient') as mock_data:
                    # Mock the clients
                    mock_trading.return_value = Mock()
                    mock_data.return_value = Mock()
                    
                    # Initialize bot
                    bot = AlpacaTradingBot(paper_trading=True)
                    print("✅ Mock bot initialization successful")
                    
                    # Test 3: Basic method calls
                    print("Testing basic methods...")
                    
                    # Mock get_current_price
                    mock_quote = Mock()
                    mock_quote.bid_price = 100.0
                    mock_quote.ask_price = 102.0
                    bot.data_client.get_stock_latest_quote = Mock(return_value={'AAPL': mock_quote})
                    
                    price = bot.get_current_price('AAPL')
                    assert price == 101.0, f"Expected 101.0, got {price}"
                    print("✅ Price fetching test passed")
                    
                    # Test 4: Portfolio parsing
                    print("Testing signal parsing...")
                    signals = [
                        {
                            'symbol': 'SMR',
                            'action': 'BUY',
                            'reason': 'Nuclear portfolio allocation: 31.2% (Bull market)',
                            'timestamp': '2024-01-01T12:00:00'
                        },
                        {
                            'symbol': 'LEU', 
                            'action': 'BUY',
                            'reason': 'Nuclear portfolio allocation: 39.5% (Bull market)',
                            'timestamp': '2024-01-01T12:00:00'
                        }
                    ]
                    
                    portfolio = bot.parse_portfolio_from_signals(signals)
                    expected = {'SMR': 0.312, 'LEU': 0.395}
                    
                    for symbol, weight in expected.items():
                        assert abs(portfolio[symbol] - weight) < 0.001, f"Portfolio parsing failed for {symbol}"
                    
                    print("✅ Signal parsing test passed")
                    
                    # Test 5: Error handling
                    print("Testing error handling...")
                    
                    # Test with invalid price
                    bot.data_client.get_stock_latest_quote = Mock(side_effect=Exception("API Error"))
                    price = bot.get_current_price('INVALID')
                    assert price == 0.0, f"Expected 0.0 for failed price fetch, got {price}"
                    print("✅ Error handling test passed")
        
        print("\n✅ All basic validation tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def create_sample_test():
    """Create a sample test that can be run manually"""
    sample_test = '''#!/usr/bin/env python3
"""
Sample Manual Test for Alpaca Trading Bot
Can be run without pytest for basic validation
"""

import sys
import os
from unittest.mock import Mock, patch

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_basic_functionality():
    """Test basic bot functionality manually"""
    print("🧪 Running manual bot test...")
    
    from execution.alpaca_trader import AlpacaTradingBot
    
    # Test with mocked environment
    with patch.dict(os.environ, {
        'ALPACA_PAPER_KEY': 'test_key',
        'ALPACA_PAPER_SECRET': 'test_secret'
    }):
        with patch('execution.alpaca_trader.TradingClient'):
            with patch('execution.alpaca_trader.StockHistoricalDataClient'):
                bot = AlpacaTradingBot(paper_trading=True)
                
                # Test price fetching
                mock_quote = Mock()
                mock_quote.bid_price = 40.0
                mock_quote.ask_price = 41.0
                bot.data_client.get_stock_latest_quote = Mock(return_value={'SMR': mock_quote})
                
                price = bot.get_current_price('SMR')
                print(f"SMR price: ${price}")
                assert price == 40.5
                
                # Test portfolio allocation parsing
                signals = [
                    {
                        'symbol': 'SMR',
                        'action': 'BUY',
                        'reason': 'Nuclear portfolio allocation: 50% (Bull market)',
                        'timestamp': '2024-01-01T12:00:00'
                    }
                ]
                
                portfolio = bot.parse_portfolio_from_signals(signals)
                print(f"Parsed portfolio: {portfolio}")
                assert portfolio['SMR'] == 0.5
                
                print("✅ Manual test passed!")
                return True

if __name__ == '__main__':
    try:
        test_basic_functionality()
        print("\\n🎉 All manual tests passed!")
    except Exception as e:
        print(f"\\n❌ Manual test failed: {e}")
        import traceback
        traceback.print_exc()
'''
    
    test_file = Path("tests/manual_test.py")
    test_file.parent.mkdir(exist_ok=True)
    
    with open(test_file, 'w') as f:
        f.write(sample_test)
    
    print(f"📝 Created sample test file: {test_file}")
    return test_file


def run_pytest_tests():
    """Run the full pytest suite"""
    print("\n🧪 Running Pytest Test Suite...")
    
    try:
        # Run pytest with verbose output
        result = subprocess.run([
            sys.executable, '-m', 'pytest', 'tests/', 
            '-v', '--tb=short', '--color=yes'
        ], capture_output=True, text=True)
        
        print(result.stdout)
        if result.stderr:
            print("Warnings/Errors:")
            print(result.stderr)
        
        if result.returncode == 0:
            print("✅ All pytest tests passed!")
            return True
        else:
            print(f"❌ Some tests failed (exit code: {result.returncode})")
            return False
            
    except FileNotFoundError:
        print("❌ pytest not found. Install with: pip install pytest")
        return False
    except Exception as e:
        print(f"❌ Error running pytest: {e}")
        return False


def main():
    """Main test setup and runner"""
    print("🚀 Alpaca Trading Bot Test Setup & Validation")
    print("=" * 60)
    
    # Step 1: Basic validation (no dependencies required)
    print("Step 1: Basic Validation")
    if not run_basic_validation():
        print("❌ Basic validation failed. Check your bot implementation.")
        return False
    
    # Step 2: Create sample test
    print("\\nStep 2: Creating Sample Test")
    sample_test_file = create_sample_test()
    
    # Step 3: Install dependencies if needed
    print("\\nStep 3: Test Dependencies")
    try:
        import pytest
        print("✅ pytest already installed")
    except ImportError:
        print("pytest not found. Installing...")
        if not install_test_dependencies():
            print("❌ Failed to install test dependencies")
            print("You can still run the manual test:")
            print(f"python {sample_test_file}")
            return False
    
    # Step 4: Run full test suite
    print("\\nStep 4: Full Test Suite")
    success = run_pytest_tests()
    
    # Summary
    print("\\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    if success:
        print("✅ All tests completed successfully!")
        print("\\n🎯 Your Alpaca Trading Bot is ready for all market conditions!")
        print("\\nAvailable test commands:")
        print("  python run_tests.py unit          # Unit tests only")
        print("  python run_tests.py market        # Market scenario tests")
        print("  python run_tests.py performance   # Performance tests")
        print("  python run_tests.py coverage      # Coverage report")
    else:
        print("❌ Some tests failed or couldn't run")
        print("\\n🔧 Manual testing available:")
        print(f"  python {sample_test_file}")
    
    return success


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
