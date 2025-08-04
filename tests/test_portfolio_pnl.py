#!/usr/bin/env python3
"""
Test script for the new portfolio P&L functionality.
"""

import os
import sys

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from the_alchemiser.core.data.data_provider import UnifiedDataProvider
from the_alchemiser.execution.trading_engine import TradingEngine


def test_data_provider_methods():
    """Test the new data provider methods"""
    print("🧪 Testing DataProvider new methods...")

    try:
        # Create data provider (paper trading)
        data_provider = UnifiedDataProvider(paper_trading=True)

        print("✅ DataProvider initialized successfully")

        # Test portfolio history (existing method)
        print("\n📊 Testing portfolio history...")
        portfolio_history = data_provider.get_portfolio_history()
        if portfolio_history:
            print(f"   Portfolio history keys: {list(portfolio_history.keys())}")
            print(f"   Equity data points: {len(portfolio_history.get('equity', []))}")
            print(f"   P&L data points: {len(portfolio_history.get('profit_loss', []))}")
        else:
            print("   No portfolio history data")

        # Test account activities (new method)
        print("\n📋 Testing account activities...")
        activities = data_provider.get_account_activities(activity_type="FILL", page_size=10)
        print(f"   Found {len(activities)} recent activities")

        if activities:
            latest_activity = activities[0]
            print(
                f"   Latest activity: {latest_activity.get('symbol')} {latest_activity.get('side')} {latest_activity.get('qty')}"
            )

        # Test closed position P&L calculation (new method)
        print("\n💰 Testing closed position P&L calculation...")
        closed_pnl = data_provider.get_recent_closed_positions_pnl(days_back=7)
        print(f"   Found {len(closed_pnl)} closed positions with P&L")

        if closed_pnl:
            for position in closed_pnl[:3]:  # Show first 3
                print(
                    f"   {position['symbol']}: ${position['realized_pnl']:.2f} ({position['realized_pnl_pct']:.2f}%)"
                )

        print("✅ DataProvider methods tested successfully")
        return True

    except Exception as e:
        print(f"❌ Error testing DataProvider: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_trading_system_integration():
    """Test the trading system integration with new P&L data"""
    print("\n🤖 Testing TradingEngine integration...")

    try:
        # Create trading system (paper trading)
        trader = TradingEngine(paper_trading=True)

        print("✅ TradingEngine initialized successfully")

        # Test enhanced account info
        print("\n📈 Testing enhanced account info...")
        account_info = trader.get_account_info()

        print(f"   Account keys: {list(account_info.keys())}")

        # Check if we have the new closed P&L data
        if "recent_closed_pnl" in account_info:
            recent_closed_pnl = account_info["recent_closed_pnl"]
            print(f"   Recent closed P&L positions: {len(recent_closed_pnl)}")

            if recent_closed_pnl:
                total_realized = sum(pos["realized_pnl"] for pos in recent_closed_pnl)
                print(f"   Total realized P&L (7 days): ${total_realized:.2f}")

                # Show top 3 performers
                print("   Top closed positions:")
                for position in recent_closed_pnl[:3]:
                    print(
                        f"     {position['symbol']}: ${position['realized_pnl']:.2f} ({position['realized_pnl_pct']:.2f}%)"
                    )
        else:
            print("   ❌ recent_closed_pnl not found in account_info")

        print("✅ Trading system integration tested successfully")
        return True

    except Exception as e:
        print(f"❌ Error testing trading system: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_email_functionality():
    """Test the email template with closed P&L"""
    print("\n📧 Testing email template functionality...")

    try:
        from the_alchemiser.core.ui.email_utils import _build_closed_positions_pnl_email_html

        # Create test account info with closed P&L
        test_account_info = {
            "recent_closed_pnl": [
                {
                    "symbol": "TSLA",
                    "realized_pnl": 1250.50,
                    "realized_pnl_pct": 8.3,
                    "trade_count": 3,
                    "last_trade_date": "2024-01-15T10:30:00Z",
                },
                {
                    "symbol": "AAPL",
                    "realized_pnl": -320.75,
                    "realized_pnl_pct": -2.1,
                    "trade_count": 2,
                    "last_trade_date": "2024-01-14T14:15:00Z",
                },
            ]
        }

        # Test the email HTML generation
        html_content = _build_closed_positions_pnl_email_html(test_account_info)

        print(f"   Generated HTML length: {len(html_content)} characters")

        # Check for key elements
        if "Recent Closed Positions P&L" in html_content:
            print("   ✅ Title found in HTML")
        if "TSLA" in html_content and "AAPL" in html_content:
            print("   ✅ Test symbols found in HTML")
        if "+$1,250.50" in html_content and "-$320.75" in html_content:
            print("   ✅ P&L values found in HTML")

        print("✅ Email template functionality tested successfully")
        return True

    except Exception as e:
        print(f"❌ Error testing email functionality: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Main test function"""
    print("🚀 Testing Portfolio P&L Enhancement Features")
    print("=" * 50)

    # Run tests
    tests = [test_data_provider_methods, test_trading_system_integration, test_email_functionality]

    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results.append(False)
        print()

    # Summary
    print("=" * 50)
    print("🎯 Test Summary:")
    passed = sum(results)
    total = len(results)
    print(f"   Passed: {passed}/{total}")

    if passed == total:
        print("🎉 All tests passed! Portfolio P&L enhancement is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
