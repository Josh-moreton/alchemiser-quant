#!/usr/bin/env python3
"""
Verification script to test CloudWatch-first logging in Lambda environment.
"""

import json
import logging
import os
import sys
from io import StringIO


def test_lambda_logging_configuration():
    """Test that Lambda environment produces CloudWatch-only JSON logs."""
    
    print("🧪 Testing Lambda logging configuration...")
    
    # Simulate Lambda environment
    os.environ['AWS_LAMBDA_FUNCTION_NAME'] = 'test-lambda'
    os.environ.pop('ENABLE_S3_LOGGING', None)  # Ensure S3 is not enabled
    
    # Capture stdout to verify JSON format
    stdout_capture = StringIO()
    
    # Clear any existing log handlers
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    
    # Import and configure logging as it would be in Lambda
    from the_alchemiser.infrastructure.logging.logging_utils import configure_production_logging
    
    configure_production_logging(log_level=logging.INFO)
    
    # Create a test logger and log a message
    test_logger = logging.getLogger('test.lambda.verification')
    
    # Redirect root logger to our capture
    for handler in root_logger.handlers:
        if isinstance(handler, logging.StreamHandler):
            handler.stream = stdout_capture
    
    # Log test messages
    test_logger.info("Lambda startup complete", extra={
        'extra_fields': {
            'component': 'lambda_handler',
            'mode': 'test',
            'trading_mode': 'paper'
        }
    })
    
    test_logger.warning("Test warning message")
    
    # Get the captured output
    log_output = stdout_capture.getvalue()
    lines = [line.strip() for line in log_output.split('\n') if line.strip()]
    
    print(f"📝 Captured {len(lines)} log lines")
    
    # Verify each line is valid JSON
    json_logs = []
    for i, line in enumerate(lines):
        try:
            log_entry = json.loads(line)
            json_logs.append(log_entry)
            print(f"✅ Line {i+1}: Valid JSON log entry")
        except json.JSONDecodeError as e:
            print(f"❌ Line {i+1}: Invalid JSON - {e}")
            print(f"   Content: {line}")
            return False
    
    # Verify log structure
    for i, log_entry in enumerate(json_logs):
        required_fields = ['timestamp', 'level', 'logger', 'message', 'module', 'function', 'line']
        missing_fields = [field for field in required_fields if field not in log_entry]
        
        if missing_fields:
            print(f"❌ Log entry {i+1} missing fields: {missing_fields}")
            return False
        else:
            print(f"✅ Log entry {i+1}: All required fields present")
            
        # Check for CloudWatch-friendly format
        if log_entry.get('level') in ['INFO', 'WARNING', 'ERROR']:
            print(f"✅ Log entry {i+1}: Valid log level ({log_entry['level']})")
        else:
            print(f"❌ Log entry {i+1}: Invalid log level ({log_entry.get('level')})")
            return False
    
    # Verify no S3 handlers were created
    from the_alchemiser.infrastructure.s3.s3_utils import S3FileHandler
    s3_handlers = [h for h in root_logger.handlers if isinstance(h, S3FileHandler)]
    
    if s3_handlers:
        print(f"❌ Found {len(s3_handlers)} S3 handlers (should be 0 in Lambda without explicit enable)")
        return False
    else:
        print("✅ No S3 handlers created (production hygiene confirmed)")
    
    # Check for console/CloudWatch handlers
    console_handlers = [h for h in root_logger.handlers if isinstance(h, logging.StreamHandler)]
    if console_handlers:
        print(f"✅ Found {len(console_handlers)} console handlers for CloudWatch")
    else:
        print("❌ No console handlers found (CloudWatch logs won't work)")
        return False
    
    print("\n📊 Sample log output:")
    for log_entry in json_logs[:2]:  # Show first 2 entries
        print(json.dumps(log_entry, indent=2))
    
    return True


def test_s3_logging_guard():
    """Test that S3 logging is blocked in Lambda without explicit enable."""
    
    print("\n🧪 Testing S3 logging guards...")
    
    # Simulate Lambda environment with S3 logging attempt
    os.environ['AWS_LAMBDA_FUNCTION_NAME'] = 'test-lambda'
    os.environ.pop('ENABLE_S3_LOGGING', None)  # Ensure S3 is not enabled
    
    # Clear any existing log handlers
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    
    # Capture log output to check for warnings
    from the_alchemiser.infrastructure.logging.logging_utils import setup_logging
    
    # Try to setup S3 logging (should be blocked)
    setup_logging(
        log_level=logging.INFO,
        log_file="s3://test-bucket/logs/test.log",
        structured_format=True,
    )
    
    # Check if S3 logging was blocked
    from the_alchemiser.infrastructure.s3.s3_utils import S3FileHandler
    s3_handlers = [h for h in root_logger.handlers if isinstance(h, S3FileHandler)]
    
    if s3_handlers:
        print("❌ S3 logging was not blocked in Lambda environment")
        return False
    else:
        print("✅ S3 logging correctly blocked in Lambda environment")
    
    return True


if __name__ == "__main__":
    print("🔍 Verifying CloudWatch-first logging configuration for Lambda deployment")
    print("=" * 80)
    
    try:
        # Test 1: Lambda logging configuration
        test1_passed = test_lambda_logging_configuration()
        
        # Test 2: S3 logging guards
        test2_passed = test_s3_logging_guard()
        
        print("\n" + "=" * 80)
        if test1_passed and test2_passed:
            print("🎉 All tests passed! Lambda will use CloudWatch-only JSON logging.")
            print("✅ Production hygiene verified: S3 logging properly guarded.")
            sys.exit(0)
        else:
            print("❌ Some tests failed. Review the output above.")
            sys.exit(1)
            
    except Exception as e:
        print(f"💥 Test execution failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)