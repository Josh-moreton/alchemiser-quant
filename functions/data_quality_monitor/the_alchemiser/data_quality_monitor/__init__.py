"""Business Unit: data_quality_monitor | Status: current.

Data Quality Monitor microservice for validating S3 parquet market data.

This module provides Lambda-based monitoring of our S3 parquet datalake by comparing
stored data against an external data source (Yahoo Finance) to detect:
- Missing data gaps
- Timestamp misalignment
- Price discrepancies
- Data freshness issues

Runs daily after the data refresh Lambda to validate data integrity.
"""

from __future__ import annotations

__all__ = [
    "lambda_handler",
]

from .lambda_handler import lambda_handler
