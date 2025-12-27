# Data Quality Monitor

**Business Unit:** data_quality_monitor | **Status:** current

Lambda microservice for validating S3 parquet market data quality using **batch processing** to respect API rate limits.

## Overview

The Data Quality Monitor runs daily after the Data Lambda to validate data integrity by comparing our S3 parquet datalake against external data sources (Twelve Data API).

**NEW:** Implements batch processing to respect Twelve Data's 8 API credits/minute rate limit, using multiple Lambda invocations coordinated via DynamoDB and SQS.

## Architecture

```
Data Lambda (4:00 AM UTC)
    ↓ fetches latest bars
S3 Parquet Datalake
    ↓ triggers schedule
Data Quality Coordinator (4:30 AM UTC)
    ↓ creates session, splits into batches
    ├─ DynamoDB Session Table (tracks workflow)
    └─ SQS Queue (batch messages with 60s delay)
         ↓
    Batch Processor Lambda (parallel instances)
         ↓ validates batch (max 8 symbols)
         ├─ Freshness check (data age)
         ├─ Completeness check (missing dates)
         └─ Accuracy check (price discrepancies)
         ↓
    DynamoDB (stores results)
         ↓ when all batches complete
    WorkflowCompleted Event
```

### Components

1. **DataQualityCoordinator** (`coordinator_handler.py`)
   - Entry point (scheduled at 4:30 AM UTC)
   - Determines symbols to validate
   - Creates validation session in DynamoDB
   - Splits symbols into batches of 8
   - Enqueues first batch to SQS

2. **DataQualityBatchProcessor** (`batch_processor_handler.py`)
   - Triggered by SQS messages
   - Processes one batch (max 8 symbols)
   - Validates against Twelve Data API
   - Stores results in DynamoDB
   - Enqueues next batch with 60-second delay
   - Publishes WorkflowCompleted when all batches done

3. **ValidationSessionManager** (`session_manager.py`)
   - Manages session state in DynamoDB
   - Tracks batch status (pending/processing/completed/failed)
   - Stores per-symbol results
   - Calculates overall workflow status

4. **Validation Sessions Table** (DynamoDB)
   - Stores session metadata and batch tracking
   - Stores per-symbol validation results
   - 7-day TTL for automatic cleanup

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

### Scheduled Invocation (Recommended)
The coordinator runs automatically daily at 4:30 AM UTC via EventBridge Schedule.

Workflow:
1. Coordinator creates session and enqueues first batch
2. Batch processor validates batch (8 symbols)
3. After 60 seconds, next batch is processed
4. Repeats until all symbols validated
5. WorkflowCompleted event published

**Duration:** For 188 symbols = 24 batches × 60 seconds = ~24 minutes total

### Manual Invocation

Invoke the **coordinator** (not the batch processor):

```python
# Validate all symbols (from strategy configs)
{
    "lookback_days": 5
}

# Validate specific symbols
{
    "symbols": ["AAPL", "GOOGL", "MSFT"],
    "lookback_days": 10
}
```

### Querying Session Status

Use the session ID from the response to check progress:

```python
import boto3

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table("alchemiser-data-quality-validation-sessions")

response = table.get_item(
    Key={"PK": "SESSION#<session-id>", "SK": "METADATA"}
)
session = response["Item"]
print(f"Status: {session['status']}")
print(f"Completed batches: {session['completed_batches_count']}/{session['total_batches']}")
```

## Environment Variables

### Coordinator Lambda

| Variable | Description | Default |
|----------|-------------|---------|
| `EVENT_BUS_NAME` | EventBridge bus for events | `alchemiser-shared-data-events` |
| `VALIDATION_SESSIONS_TABLE` | DynamoDB table for sessions | `alchemiser-data-quality-validation-sessions` |
| `VALIDATION_QUEUE_URL` | SQS queue URL | (set by CloudFormation) |

### Batch Processor Lambda

| Variable | Description | Default |
|----------|-------------|---------|
| `MARKET_DATA_BUCKET` | S3 bucket for market data | `alchemiser-shared-market-data` |
| `EVENT_BUS_NAME` | EventBridge bus for events | `alchemiser-shared-data-events` |
| `VALIDATION_SESSIONS_TABLE` | DynamoDB table for sessions | `alchemiser-data-quality-validation-sessions` |
| `VALIDATION_QUEUE_URL` | SQS queue URL | (set by CloudFormation) |
| `TWELVEDATA_API_KEY` | Twelve Data API key (required) | None |

## External Data Source

Uses **Twelve Data API** (via `twelvedata` SDK) for validation:
- Professional-grade financial data API
- Free tier: 800 requests/day
- Reliable and no IP blocking (unlike Yahoo Finance)
- Requires `TWELVEDATA_API_KEY` environment variable
- Get free API key at: https://twelvedata.com/pricing

## Outputs

### Coordinator Response (Immediate)
```json
{
    "statusCode": 200,
    "body": {
        "status": "initiated",
        "session_id": "session-abc123...",
        "correlation_id": "quality-coord-xyz...",
        "total_symbols": 188,
        "total_batches": 24,
        "estimated_duration_minutes": 24
    }
}
```

### Batch Processor Response (Per Batch)
```json
{
    "statusCode": 200,
    "body": {
        "status": "success",
        "session_id": "session-abc123...",
        "batch_number": 5,
        "symbols_processed": 8,
        "session_complete": false
    }
}
```

### Final Results (DynamoDB Query)
Query `RESULT#*` items for a session to get per-symbol results:
```json
{
    "symbol": "AAPL",
    "passed": false,
    "issues": [
        "Data is stale: latest timestamp is 2025-01-01, age is 96.5 hours",
        "Missing 1 recent trading day(s): [2025-01-03]"
    ],
    "rows_checked": 5,
    "external_source": "twelvedata",
    "validated_at": "2025-01-15T04:35:22Z"
}
```

## Events Published

### WorkflowCompleted
Published when all batches complete successfully:
```python
WorkflowCompleted(
    source_module="data_quality_monitor",
    workflow_type="data_quality_batch_validation",
    completion_details={
        "session_id": "...",
        "total_symbols": 188,
        "passed_count": 180,
        "failed_count": 8,
        "failed_symbols": ["AAPL", "GOOGL", ...],
    },
)
```

### WorkflowFailed
Published when coordinator or batch processing encounters a critical exception:
```python
WorkflowFailed(
    source_module="data_quality_monitor",
    workflow_type="data_quality_batch_validation",
    failure_reason="...",
    failure_step="coordination" or "batch_N",
)
```

## Lambda Configuration

### Coordinator
- **Runtime:** Python 3.12
- **Memory:** 512 MB
- **Timeout:** 120s (2 minutes)
- **Layer:** DataQualityMonitorLayer (awswrangler + twelvedata)
- **Schedule:** Daily at 4:30 AM UTC (30 minutes after Data Lambda)

### Batch Processor
- **Runtime:** Python 3.12
- **Memory:** 1024 MB
- **Timeout:** 900s (15 minutes)
- **Layer:** DataQualityMonitorLayer (awswrangler + twelvedata)
- **Trigger:** SQS (ValidationQueue) with batch size 1

## Dependencies

Requires:
- `awswrangler` (S3/Parquet access)
- `twelvedata` (external data validation via Twelve Data API)
- `pandas` (data manipulation)
- `pydantic` (schemas)
- `structlog` (logging)

## Rate Limiting

The batch processing system respects Twelve Data's API limits:

- **Batch size:** 8 symbols (matches 8 API credits/minute limit)
- **Delay between batches:** 60 seconds (ensures 1 batch/minute)
- **No parallel batch processing:** Only one batch processes at a time
- **Graceful degradation:** Failed batches marked in session, don't block others

### Why This Works

- **188 symbols** → 24 batches of 8 symbols
- **1 batch per minute** → 24 minutes total runtime
- **8 API calls per batch** → stays within 8 credits/minute limit
- **Multiple Lambda invocations** → avoids 15-minute timeout
- **DynamoDB state tracking** → workflow survives Lambda cold starts

## Error Handling

### Coordinator Failures
- Creates `WorkflowFailed` event
- Returns 500 error response
- No batches are processed

### Batch Processing Failures
- Individual symbol failures are logged but don't fail the batch
- Batch marked as FAILED in DynamoDB
- Next batch still enqueued (continues processing other symbols)
- Failed batches can be retried manually

### SQS Dead Letter Queue
- Batches that fail 3 times move to DLQ
- Monitor `alchemiser-data-quality-validation-dlq` for persistent failures
- Replay from DLQ after fixing underlying issues

### Quality Issues vs Errors
- Data quality issues (stale data, price mismatches) are **warnings**, not errors
- These are stored as validation results, not failures
- Publishes `WorkflowCompleted` even if quality issues found

## Testing

See `tests/data_quality_monitor/` for unit tests.

## Monitoring

- CloudWatch Logs: `/aws/lambda/alchemiser-shared-data-quality-monitor`
- Dashboard: Included in shared data infrastructure dashboard
- Alerts: WorkflowFailed events trigger SNS notifications
