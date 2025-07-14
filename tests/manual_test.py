#!/usr/bin/env python3
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
                # No return value for pytest compatibility

if __name__ == '__main__':
    try:
        test_basic_functionality()
        print("\n🎉 All manual tests passed!")
    except Exception as e:
        print(f"\n❌ Manual test failed: {e}")
        import traceback
        traceback.print_exc()
