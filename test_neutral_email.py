#!/usr/bin/env python3
"""
Test script for the neutral email mode functionality.
"""

from the_alchemiser.core.ui.email.config import is_neutral_mode_enabled
from the_alchemiser.core.ui.email.templates import EmailTemplates

def test_neutral_mode_config():
    """Test the neutral mode configuration reading."""
    print("Testing neutral mode configuration...")
    
    # Test getting the neutral mode setting
    neutral_mode = is_neutral_mode_enabled()
    print(f"Neutral mode enabled: {neutral_mode}")
    
    return neutral_mode

def test_neutral_email_template():
    """Test the neutral email template generation."""
    print("\nTesting neutral email template...")
    
    # Sample data for testing
    mode = "PAPER"
    success = True
    account_before = {"equity": 45000}
    account_after = {
        "equity": 50000,
        "cash": 5000,
        "status": "ACTIVE",
        "daytrade_count": 1
    }
    positions = {"AAPL": 0.3, "TSLA": 0.7}
    orders = [
        {"side": "BUY", "symbol": "AAPL", "qty": 10.5, "estimated_value": 1500},
        {"side": "SELL", "symbol": "TSLA", "qty": 5.0, "estimated_value": 1200}
    ]
    open_positions = [
        {"symbol": "AAPL", "qty": 10.5, "market_value": 1600, "unrealized_pl": 100, "unrealized_plpc": 0.067},
        {"symbol": "TSLA", "qty": 15.0, "market_value": 3000, "unrealized_pl": -50, "unrealized_plpc": -0.016}
    ]
    
    # Generate neutral email
    neutral_html = EmailTemplates.build_trading_report_neutral(
        mode=mode,
        success=success,
        account_before=account_before,
        account_after=account_after,
        positions=positions,
        orders=orders,
        open_positions=open_positions
    )
    
    print("Neutral email template generated successfully!")
    print(f"Template length: {len(neutral_html)} characters")
    
    # Check that dollar signs and percentages are not in the neutral template
    dollar_count = neutral_html.count('$')
    percent_count = neutral_html.count('%')
    
    print(f"Dollar signs in neutral template: {dollar_count}")
    print(f"Percent signs in neutral template: {percent_count}")
    
    # There might be some dollar signs in CSS styles, but should be minimal
    if dollar_count < 10:  # Allow for some CSS usage
        print("✅ Neutral template appears to have minimal dollar values")
    else:
        print("⚠️  Neutral template may still contain dollar values")
    
    return neutral_html

def test_regular_vs_neutral():
    """Compare regular and neutral templates."""
    print("\nComparing regular vs neutral templates...")
    
    # Test data
    mode = "PAPER"
    success = True
    account_before = {"equity": 45000}
    account_after = {
        "equity": 50000,
        "cash": 5000,
        "status": "ACTIVE",
        "daytrade_count": 1
    }
    positions = {"AAPL": 0.3, "TSLA": 0.7}
    orders = [
        {"side": "BUY", "symbol": "AAPL", "qty": 10.5, "estimated_value": 1500}
    ]
    open_positions = [
        {"symbol": "AAPL", "qty": 10.5, "market_value": 1600, "unrealized_pl": 100, "unrealized_plpc": 0.067}
    ]
    
    # Generate both templates
    regular_html = EmailTemplates.build_trading_report(
        mode=mode,
        success=success,
        account_before=account_before,
        account_after=account_after,
        positions=positions,
        orders=orders,
        open_positions=open_positions
    )
    
    neutral_html = EmailTemplates.build_trading_report_neutral(
        mode=mode,
        success=success,
        account_before=account_before,
        account_after=account_after,
        positions=positions,
        orders=orders,
        open_positions=open_positions
    )
    
    # Compare dollar usage
    regular_dollars = regular_html.count('$')
    neutral_dollars = neutral_html.count('$')
    
    print(f"Regular template dollar signs: {regular_dollars}")
    print(f"Neutral template dollar signs: {neutral_dollars}")
    print(f"Reduction in dollar signs: {regular_dollars - neutral_dollars}")
    
    if neutral_dollars < regular_dollars:
        print("✅ Neutral template successfully reduces dollar value display")
    else:
        print("⚠️  Neutral template may not be reducing dollar values as expected")

if __name__ == "__main__":
    print("🧪 Testing Neutral Email Mode\n")
    
    # Run tests
    test_neutral_mode_config()
    test_neutral_email_template()
    test_regular_vs_neutral()
    
    print("\n✅ All tests completed!")
