# Data Quality Monitor

**Business Unit:** data_quality_monitor | **Status:** current

Lambda microservice for validating S3 parquet market data quality.

## Overview

The Data Quality Monitor runs daily after the Data Lambda to validate data integrity by comparing our S3 parquet datalake against external data sources (Yahoo Finance).

## Architecture

```
Data Lambda (4:00 AM UTC)
    ↓ fetches latest bars
S3 Parquet Datalake
    ↓ triggers
Data Quality Monitor (4:30 AM UTC)
    ↓ validates
    ├─ Freshness check (data age)
    ├─ Completeness check (missing dates)
    └─ Accuracy check (price discrepancies)
```

## Quality Checks

### 1. Freshness Check
- Validates that data is not stale (>72 hours old)
- Accounts for weekends and market holidays

### 2. Completeness Check
- Compares our data against Yahoo Finance
- Detects missing trading days
- Flags recent gaps (last 2 days)

### 3. Price Accuracy Check
- Compares close prices between sources
- Tolerance: 2% default
- Reports significant discrepancies

## Usage

### Scheduled Invocation
Runs automatically daily at 4:30 AM UTC via EventBridge Schedule.

### Manual Invocation
```python
# Validate all symbols
{
    "lookback_days": 5
}

# Validate specific symbols
{
    "symbols": ["AAPL", "GOOGL", "MSFT"],
    "lookback_days": 10
}
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `MARKET_DATA_BUCKET` | S3 bucket for market data | `alchemiser-shared-market-data` |
| `EVENT_BUS_NAME` | EventBridge bus for events | `alchemiser-shared-data-events` |
| `TWELVEDATA_API_KEY` | Twelve Data API key (required for external validation) | None |

## External Data Source

Uses **Twelve Data API** (via `twelvedata` SDK) for validation:
- Professional-grade financial data API
- Free tier: 800 requests/day
- Reliable and no IP blocking (unlike Yahoo Finance)
- Requires `TWELVEDATA_API_KEY` environment variable
- Get free API key at: https://twelvedata.com/pricing

## Outputs

### Success Response
```json
{
    "statusCode": 200,
    "body": {
        "status": "success",
        "total_symbols": 10,
        "passed": 10,
        "issues_found": 0
    }
}
```

### Issues Detected Response
```json
{
    "statusCode": 200,
    "body": {
        "status": "issues_detected",
        "total_symbols": 10,
        "passed": 8,
        "failed": 2,
        "failed_symbols": ["AAPL", "GOOGL"],
        "issues": [
            {"symbol": "AAPL", "issue": "Data is stale: latest timestamp is 2025-01-01, age is 96.5 hours"},
            {"symbol": "GOOGL", "issue": "Missing 1 recent trading day(s): [2025-01-03]"}
        ]
    }
}
```

## Events Published

### WorkflowFailed
Published when quality check encounters an exception:
```python
WorkflowFailed(
    source_module="data_quality_monitor",
    workflow_type="data_quality_check",
    failure_reason="...",
)
```

## Lambda Configuration

- **Runtime:** Python 3.12
- **Memory:** 1024 MB
- **Timeout:** 900s (15 minutes)
- **Layer:** Same as Strategy Lambda (awswrangler + dependencies)
- **Schedule:** Daily at 4:30 AM UTC (30 minutes after Data Lambda)

## Dependencies

Requires:
- `awswrangler` (S3/Parquet access)
- `twelvedata` (external data validation via Twelve Data API)
- `pandas` (data manipulation)
- `pydantic` (schemas)
- `structlog` (logging)

## Error Handling

- Individual symbol failures are logged but don't fail the entire run
- Quality issues are logged as warnings, not errors
- Publishes `WorkflowFailed` event only on critical exceptions

## Testing

See `tests/data_quality_monitor/` for unit tests.

## Monitoring

- CloudWatch Logs: `/aws/lambda/alchemiser-shared-data-quality-monitor`
- Dashboard: Included in shared data infrastructure dashboard
- Alerts: WorkflowFailed events trigger SNS notifications
