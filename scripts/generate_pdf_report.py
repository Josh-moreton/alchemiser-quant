#!/usr/bin/env python3
"""Local script to trigger PDF report generation.

This script demonstrates how to trigger the PDF reporting function
that was built on the feat/dynamodb branch.
"""

import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from the_alchemiser.reporting.lambda_handler import lambda_handler


def main():
    """Trigger PDF report generation locally."""
    print("🧪 The Alchemiser - PDF Report Generation")
    print("=" * 50)

    # Example event payload
    event = {
        "account_id": "PA123456789",  # Replace with your actual account ID
        "use_latest": True,  # Use the latest snapshot
        "report_type": "account_summary",
        "correlation_id": "local-test-123"
    }

    print(f"📋 Event payload: {event}")
    print()

    try:
        # Call the Lambda handler directly
        result = lambda_handler(event, None)

        print("✅ Report generation completed!")
        print(f"📄 Report ID: {result.get('report_id')}")
        print(f"📍 S3 URI: {result.get('s3_uri')}")
        print(f"📊 File size: {result.get('file_size_bytes')} bytes")
        print(f"⏱️  Generation time: {result.get('generation_time_ms')} ms")
        print(f"📸 Snapshot ID: {result.get('snapshot_id')}")

    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
