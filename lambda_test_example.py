#!/usr/bin/env python3
"""Simple Lambda Handler Test Example.

This script demonstrates how to test the enhanced Lambda handler
locally with different event configurations.
"""

import json
from the_alchemiser.lambda_handler import lambda_handler, parse_event_mode


def test_event_parsing():
    """Test the event parsing functionality."""
    print("🧪 Testing Lambda Handler Event Parsing")
    print("=" * 60)
    
    test_events = [
        ({'mode': 'trade', 'trading_mode': 'paper'}, 'Paper Trading'),
        ({'mode': 'trade', 'trading_mode': 'live'}, 'Live Trading'),
        ({'mode': 'bot'}, 'Signal Analysis'),
        ({}, 'Empty Event (Backward Compatibility)'),
        ({'mode': 'trade', 'trading_mode': 'paper', 'ignore_market_hours': True}, 'Paper + Override'),
    ]
    
    for event, description in test_events:
        args = parse_event_mode(event)
        print(f"{description:.<40} {args}")
    
    print("\n✅ Event parsing tests completed!")


def demo_lambda_responses():
    """Demonstrate different Lambda response formats."""
    print("\n📋 Lambda Response Examples")
    print("=" * 60)
    
    # Note: These won't actually execute the trading bot, just show response format
    mock_context = type('MockContext', (), {'aws_request_id': 'test-12345'})()
    
    test_events = [
        {'mode': 'trade', 'trading_mode': 'paper'},
        {'mode': 'bot'},
        {},  # Backward compatibility
    ]
    
    for event in test_events:
        print(f"\nEvent: {json.dumps(event)}")
        print("Expected Response Format:")
        print("  {")
        print(f"    \"status\": \"success|failed\",")
        print(f"    \"mode\": \"trade|bot\",")
        print(f"    \"trading_mode\": \"paper|live|n/a\",")
        print(f"    \"message\": \"Status message\",")
        print(f"    \"request_id\": \"test-12345\"")
        print("  }")


if __name__ == "__main__":
    test_event_parsing()
    demo_lambda_responses()
    
    print("\n📖 Next Steps:")
    print("1. Deploy the updated Lambda function")
    print("2. Configure CloudWatch Events with desired event payloads")
    print("3. Monitor CloudWatch Logs for execution details")
    print("4. See docs/lambda_event_configuration.md for full setup guide")
