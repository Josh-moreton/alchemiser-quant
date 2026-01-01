"""Business Unit: scripts | Status: current.

QuantStats report generation modules for GitHub Actions workflow.

Note: This package is named quantstats_reports (not quantstats) to avoid
shadowing the third-party quantstats library which is imported in report_generator.py.

This package provides tools to generate QuantStats tearsheet reports
from DynamoDB trade data, with SPY benchmark comparison.
"""

from __future__ import annotations

__all__ = [
    "benchmark_service",
    "report_generator",
    "returns_builder",
    "s3_uploader",
]
