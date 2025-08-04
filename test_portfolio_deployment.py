#!/usr/bin/env python3
"""
Test script to verify the portfolio deployment percentage calculation
in the neutral email template.
"""

import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from the_alchemiser.core.ui.email.templates.portfolio import PortfolioBuilder


def test_portfolio_deployment():
    """Test the portfolio deployment calculation"""

    # Test case 1: 100% deployed (no cash)
    account_info_1 = {"status": "ACTIVE", "daytrade_count": 0, "cash": 0.0, "equity": 10000.0}

    html_1 = PortfolioBuilder.build_account_summary_neutral(account_info_1)
    print("Test 1 - 100% deployed:")
    print("Expected: 100.0%")
    print(f"Generated HTML contains: {html_1}")
    assert "100.0%" in html_1
    assert "🟢" in html_1  # Should be green emoji
    print("✅ Test 1 passed\n")

    # Test case 2: 80% deployed
    account_info_2 = {"status": "ACTIVE", "daytrade_count": 1, "cash": 2000.0, "equity": 10000.0}

    html_2 = PortfolioBuilder.build_account_summary_neutral(account_info_2)
    print("Test 2 - 80% deployed:")
    print("Expected: 80.0%")
    print(f"Generated HTML contains: {html_2}")
    assert "80.0%" in html_2
    assert "🟡" in html_2  # Should be yellow emoji
    print("✅ Test 2 passed\n")

    # Test case 3: 50% deployed (low deployment)
    account_info_3 = {"status": "ACTIVE", "daytrade_count": 2, "cash": 5000.0, "equity": 10000.0}

    html_3 = PortfolioBuilder.build_account_summary_neutral(account_info_3)
    print("Test 3 - 50% deployed:")
    print("Expected: 50.0%")
    print(f"Generated HTML contains: {html_3}")
    assert "50.0%" in html_3
    assert "🔴" in html_3  # Should be red emoji
    print("✅ Test 3 passed\n")

    # Test case 4: Edge case - zero equity
    account_info_4 = {"status": "ACTIVE", "daytrade_count": 0, "cash": 0.0, "equity": 0.0}

    html_4 = PortfolioBuilder.build_account_summary_neutral(account_info_4)
    print("Test 4 - Zero equity edge case:")
    print("Expected: 0.0%")
    print(f"Generated HTML contains: {html_4}")
    assert "0.0%" in html_4
    print("✅ Test 4 passed\n")

    print("🎉 All tests passed! Portfolio deployment feature is working correctly.")


if __name__ == "__main__":
    test_portfolio_deployment()
