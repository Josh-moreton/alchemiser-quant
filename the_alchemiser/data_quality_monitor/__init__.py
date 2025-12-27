"""Business Unit: data_quality_monitor | Status: current.

Data Quality Monitor microservice for validating S3 parquet market data.

This module provides Lambda-based monitoring of our S3 parquet datalake by comparing
stored data against an external data source (Twelve Data API) to detect:
- Missing data gaps
- Timestamp misalignment
- Price discrepancies
- Data freshness issues

Runs daily after the data refresh Lambda to validate data integrity using batch
processing to respect API rate limits (8 API credits/minute).

Components:
- coordinator_handler: Entry point that creates validation sessions
- batch_processor_handler: Worker that processes batches of 8 symbols
- session_manager: DynamoDB state management
- schemas: DTOs for batch processing
- quality_checker: Data validation logic (requires Lambda layer dependencies)
"""

from __future__ import annotations

__all__ = [
    "batch_processor_handler",
    "coordinator_handler",
    "schemas",
    "session_manager",
]
