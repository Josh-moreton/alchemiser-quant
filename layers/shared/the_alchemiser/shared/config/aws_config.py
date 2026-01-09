"""Business Unit: shared | Status: current.

AWS client configuration for retry policies and timeouts.

This module centralizes AWS SDK configuration to ensure consistent behavior
across all AWS clients in the system. Configuration follows AWS best practices
for handling transient failures in serverless environments.
"""

from __future__ import annotations

from botocore.config import Config

# DynamoDB retry configuration for transient failures
# - max_attempts: 5 total attempts (1 initial + 4 retries)
# - mode: adaptive uses exponential backoff with token bucket
# - connect_timeout: 10 seconds for connection
# - read_timeout: 30 seconds for response
#
# Adaptive mode automatically adjusts retry behavior based on:
# - Throttling responses (429s)
# - Transient errors (timeouts, connection errors)
# - Service availability
DYNAMODB_RETRY_CONFIG = Config(
    retries={
        "max_attempts": 5,
        "mode": "adaptive",
    },
    connect_timeout=10,
    read_timeout=30,
)

# Lambda invoke configuration for synchronous calls
# Longer timeouts for Lambda-to-Lambda invocations
LAMBDA_INVOKE_CONFIG = Config(
    retries={
        "max_attempts": 3,
        "mode": "adaptive",
    },
    connect_timeout=10,
    read_timeout=120,  # Lambda can take up to 60s, plus buffer
)

__all__ = [
    "DYNAMODB_RETRY_CONFIG",
    "LAMBDA_INVOKE_CONFIG",
]
