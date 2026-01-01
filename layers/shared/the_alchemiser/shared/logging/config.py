"""Business Unit: shared | Status: current.

Logging configuration for AWS Lambda environments.

Simple, correct approach:
- Lambda: Emit ALL logs as JSON to CloudWatch
- Tests: Human-readable with configurable level
- Filter at read-time in CloudWatch Insights, not at write-time
"""

from __future__ import annotations

import logging

from .structlog_config import configure_structlog_lambda, configure_structlog_test


def configure_test_logging(log_level: int = logging.WARNING) -> None:
    """Configure structlog for test environments with human-readable output.

    Args:
        log_level: Minimum log level to display (default: WARNING to reduce noise).

    """
    configure_structlog_test(log_level=log_level)


def configure_application_logging() -> None:
    """Configure logging for the application.

    In Lambda: JSON output, all levels emitted to CloudWatch.
    Outside Lambda (shouldn't happen, but fallback): same as Lambda.

    Filter logs at query time in CloudWatch Insights:
        fields @timestamp, level, event
        | filter level in ["info", "warning", "error"]
        | sort @timestamp desc

    """
    configure_structlog_lambda()
