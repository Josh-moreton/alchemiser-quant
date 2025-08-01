#!/usr/bin/env python3
"""Test script for the enhanced Lambda handler.

This script demonstrates how to test the new event-driven Lambda handler
locally before deploying to AWS.
"""

import json
import sys
import os
from typing import Dict, Any

# Add the project root to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from the_alchemiser.lambda_handler import lambda_handler


def test_lambda_event(event: Dict[str, Any], description: str) -> None:
    """Test a Lambda event and display the results.
    
    Args:
        event: The event payload to test
        description: Human-readable description of the test
    """
    print(f"\n{'='*60}")
    print(f"Testing: {description}")
    print(f"Event: {json.dumps(event, indent=2)}")
    print(f"{'='*60}")
    
    try:
        result = lambda_handler(event)
        print(f"✅ Result: {json.dumps(result, indent=2)}")
    except Exception as e:
        print(f"❌ Error: {e}")


def main():
    """Run comprehensive tests of the Lambda handler."""
    print("🧪 Testing Enhanced Lambda Handler for The Alchemiser")
    print("=" * 60)
    
    # Test cases
    test_cases = [
        # Paper trading tests
        (
            {"mode": "trade", "trading_mode": "paper"},
            "Paper Trading Mode"
        ),
        (
            {"mode": "trade", "trading_mode": "paper", "ignore_market_hours": True},
            "Paper Trading with Market Hours Override"
        ),
        
        # Live trading tests  
        (
            {"mode": "trade", "trading_mode": "live"},
            "Live Trading Mode"
        ),
        (
            {"mode": "trade", "trading_mode": "live", "ignore_market_hours": True},
            "Live Trading with Market Hours Override"
        ),
        
        # Signal analysis tests
        (
            {"mode": "bot"},
            "Signal Analysis Mode"
        ),
        
        # Backward compatibility tests
        (
            {},
            "Empty Event (Backward Compatibility)"
        ),
        (
            None,
            "None Event (Backward Compatibility)"
        ),
        
        # Error handling tests
        (
            {"mode": "invalid_mode"},
            "Invalid Mode (Error Handling)"
        ),
        (
            {"mode": "trade", "trading_mode": "invalid_trading_mode"},
            "Invalid Trading Mode (Error Handling)"
        ),
        (
            {"mode": "trade", "trading_mode": "paper", "invalid_field": "test"},
            "Extra Fields (Should be ignored)"
        ),
    ]
    
    # Run all test cases
    for event, description in test_cases:
        test_lambda_event(event, description)
    
    print(f"\n{'='*60}")
    print("🎉 All tests completed!")
    print("=" * 60)
    
    # Usage examples
    print("\n📚 Usage Examples:")
    print("=" * 60)
    print("To deploy to AWS Lambda, use these event configurations:")
    print()
    
    examples = [
        ("Paper Trading Schedule", {"mode": "trade", "trading_mode": "paper"}),
        ("Live Trading Schedule", {"mode": "trade", "trading_mode": "live"}),
        ("Signal Analysis Schedule", {"mode": "bot"}),
    ]
    
    for name, event in examples:
        print(f"{name}:")
        print(f"  Event: {json.dumps(event)}")
        print()


if __name__ == "__main__":
    main()
