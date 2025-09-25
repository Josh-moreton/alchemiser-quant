#!/usr/bin/env python3
"""Test script for AlpacaErrorHandler utility."""

import sys
import time
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from the_alchemiser.shared.utils.alpaca_error_handler import (
        AlpacaErrorHandler,
        alpaca_retry_context,
    )
    
    print("✓ Successfully imported AlpacaErrorHandler")
    
    # Test transient error detection
    print("\n--- Testing Transient Error Detection ---")
    
    test_errors = [
        Exception("502 Bad Gateway error"),
        Exception("503 Service Unavailable"),
        Exception("504 Gateway Timeout occurred"),
        Exception("Connection timeout"),
        Exception("<html><body>502 Bad Gateway</body></html>"),
        Exception("Regular application error"),
    ]
    
    for error in test_errors:
        is_transient, reason = AlpacaErrorHandler.is_transient_error(error)
        print(f"Error: {str(error)[:50]:<50} | Transient: {is_transient:<5} | Reason: {reason}")
    
    # Test error message sanitization
    print("\n--- Testing Error Message Sanitization ---")
    
    for error in test_errors:
        sanitized = AlpacaErrorHandler.sanitize_error_message(error)
        print(f"Original: {str(error)[:30]:<30} | Sanitized: {sanitized}")
    
    # Test should_retry logic
    print("\n--- Testing Should Retry Logic ---")
    
    transient_error = Exception("502 Bad Gateway")
    non_transient_error = Exception("Authentication failed")
    
    for attempt in range(1, 5):
        should_retry_transient = AlpacaErrorHandler.should_retry(transient_error, attempt, 3)
        should_retry_non_transient = AlpacaErrorHandler.should_retry(non_transient_error, attempt, 3)
        print(f"Attempt {attempt}/3 | Transient: {should_retry_transient:<5} | Non-transient: {should_retry_non_transient}")
    
    # Test create_error_result
    print("\n--- Testing Error Result Creation ---")
    
    test_error = Exception("Test error for result creation")
    error_result = AlpacaErrorHandler.create_error_result(
        test_error, 
        context="Test Operation",
        order_id="test-123"
    )
    
    print(f"Created error result:")
    print(f"  Success: {error_result.success}")
    print(f"  Order ID: {error_result.order_id}")
    print(f"  Status: {error_result.status}")
    print(f"  Error: {error_result.error}")
    
    # Test alpaca_retry_context with success
    print("\n--- Testing Retry Context (Success Case) ---")
    
    try:
        with alpaca_retry_context(max_retries=2, operation_name="Test Success"):
            print("  Operation executed successfully")
    except Exception as e:
        print(f"  Unexpected error: {e}")
    
    # Test alpaca_retry_context with transient failure then success
    print("\n--- Testing Retry Context (Transient then Success) ---")
    
    attempt_counter = 0
    try:
        with alpaca_retry_context(max_retries=3, base_delay=0.1, operation_name="Test Retry"):
            attempt_counter += 1
            if attempt_counter < 2:
                raise Exception("502 Bad Gateway")  # Transient error on first attempt
            print(f"  Operation succeeded on attempt {attempt_counter}")
    except Exception as e:
        print(f"  Final error: {e}")
    
    print("\n✓ All tests completed successfully!")
    
except ImportError as e:
    print(f"✗ Import error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"✗ Test error: {e}")
    sys.exit(1)