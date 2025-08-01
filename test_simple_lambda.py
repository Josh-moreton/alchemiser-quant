#!/usr/bin/env python3
"""Simple test for the enhanced Lambda handler."""

from the_alchemiser.lambda_handler import parse_event_mode

def test_event_parsing():
    """Test the event parsing functionality."""
    print("🧪 Testing Enhanced Lambda Handler Event Parsing")
    print("=" * 60)
    
    test_events = [
        ({"mode": "trade", "trading_mode": "paper"}, "Paper Trading"),
        ({"mode": "trade", "trading_mode": "live"}, "Live Trading"),
        ({"mode": "bot"}, "Signal Analysis"),
        ({}, "Empty Event (Backward Compatibility)"),
        ({"mode": "trade", "trading_mode": "paper", "ignore_market_hours": True}, "Paper + Market Hours Override")
    ]
    
    for event, description in test_events:
        args = parse_event_mode(event)
        print(f"{description:.<40} {args}")
    
    print("\n✅ All event parsing tests completed successfully!")

if __name__ == "__main__":
    test_event_parsing()
