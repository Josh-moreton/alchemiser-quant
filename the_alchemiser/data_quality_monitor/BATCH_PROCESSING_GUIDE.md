# Data Quality Monitor - Batch Processing Guide

## Problem Solved

Your data validation Lambda was hitting Twelve Data's API rate limit of **8 API credits per minute**. Attempting to validate 188 symbols in one invocation caused:
- API rate limit errors (188 credits requested vs 8 allowed)
- Risk of hitting Lambda's 15-minute timeout for large symbol lists

## Solution Architecture

Implemented a **distributed batch processing system** using the Alchemiser's coordinator/worker pattern:

```
┌─────────────────────────────────────────────────────────────────┐
│                     BATCH PROCESSING FLOW                       │
└─────────────────────────────────────────────────────────────────┘

EventBridge Schedule (4:30 AM UTC)
        ↓
┌───────────────────────┐
│ DataQuality           │  1. Determines symbols to validate
│ Coordinator           │  2. Creates validation session in DynamoDB
│                       │  3. Splits symbols into batches of 8
│ (coordinator_handler) │  4. Enqueues first batch to SQS
└───────────────────────┘
        ↓
┌───────────────────────┐
│ SQS Queue             │  - Standard queue (not FIFO)
│                       │  - 60-second delay between batches
│ (ValidationQueue)     │  - DLQ for failed batches
└───────────────────────┘
        ↓ (triggered by SQS)
┌───────────────────────┐
│ DataQuality           │  1. Receives batch (8 symbols)
│ Batch Processor       │  2. Validates against Twelve Data API
│                       │  3. Stores results in DynamoDB
│ (batch_processor)     │  4. Enqueues next batch (60s delay)
└───────────────────────┘  5. Publishes WorkflowCompleted when done
        ↓
┌───────────────────────┐
│ DynamoDB              │  - Session metadata & batch tracking
│                       │  - Per-symbol validation results
│ (ValidationSessions)  │  - 7-day TTL for auto cleanup
└───────────────────────┘
```

## Key Components

### 1. **Coordinator Lambda** (`coordinator_handler.py`)
- **Trigger:** EventBridge Schedule (4:30 AM UTC)
- **Memory:** 512 MB
- **Timeout:** 2 minutes
- **Responsibilities:**
  - Extracts all symbols from strategy configs (or uses provided list)
  - Creates validation session in DynamoDB
  - Splits symbols into batches of 8
  - Enqueues first batch to SQS for immediate processing

### 2. **Batch Processor Lambda** (`batch_processor_handler.py`)
- **Trigger:** SQS messages from ValidationQueue
- **Memory:** 1024 MB
- **Timeout:** 15 minutes
- **Responsibilities:**
  - Processes one batch of symbols (max 8)
  - Validates against Twelve Data API
  - Stores results in DynamoDB
  - Enqueues next pending batch with 60-second delay
  - Publishes WorkflowCompleted when all batches done

### 3. **Session Manager** (`session_manager.py`)
- Manages validation session state in DynamoDB
- Tracks batch status (pending → processing → completed/failed)
- Stores per-symbol validation results
- Calculates overall workflow completion

### 4. **DynamoDB Table** (`ValidationSessionsTable`)
- **PK:** `SESSION#<session-id>`
- **SK:** `METADATA` (session info) or `RESULT#<symbol>` (results)
- **TTL:** 7 days for automatic cleanup

### 5. **SQS Queue** (`ValidationQueue`)
- Standard queue (not FIFO) - order doesn't matter
- 15-minute visibility timeout (matches Lambda timeout)
- Dead Letter Queue (DLQ) after 3 failed attempts
- Supports per-message delay (60 seconds between batches)

## How It Works

### Timeline Example (188 symbols)

```
T+0s:    Coordinator creates 24 batches (188 symbols ÷ 8 = 24 batches)
T+0s:    Batch 0 enqueued to SQS (immediate)
T+5s:    Batch 0 processing (8 symbols validated)
T+15s:   Batch 0 complete, results stored, Batch 1 enqueued (60s delay)
T+75s:   Batch 1 processing
T+85s:   Batch 1 complete, Batch 2 enqueued (60s delay)
...
T+24min: Batch 23 complete, WorkflowCompleted event published
```

**Total Duration:** ~24 minutes for 188 symbols (24 batches × 60 seconds)

### Rate Limit Compliance

- **8 API credits/minute limit** ✓
- **8 symbols per batch** ✓
- **60-second delay between batches** ✓
- **One batch processes at a time** ✓

## Deployment

### Prerequisites

Ensure you have:
- Twelve Data API key (`TWELVEDATA_API_KEY` parameter)
- AWS SAM CLI installed
- Sufficient DynamoDB and SQS quotas

### Deploy to Development

```bash
# Build and deploy data infrastructure
sam build --template data-template.yaml
sam deploy \
  --template data-template.yaml \
  --stack-name alchemiser-shared-data \
  --parameter-overrides TwelveDataApiKey=<your-api-key> \
  --capabilities CAPABILITY_NAMED_IAM \
  --resolve-s3
```

### What Gets Created

| Resource | Type | Purpose |
|----------|------|---------|
| `ValidationSessionsTable` | DynamoDB | Session and result tracking |
| `ValidationQueue` | SQS | Batch message queue |
| `ValidationQueueDLQ` | SQS | Dead letter queue |
| `DataQualityCoordinatorFunction` | Lambda | Entry point |
| `DataQualityBatchProcessorFunction` | Lambda | Worker |

## Usage

### Automatic (Recommended)

The coordinator runs daily at 4:30 AM UTC automatically via EventBridge Schedule.

### Manual Invocation

Invoke the **coordinator** (not the batch processor):

```bash
# Via AWS CLI
aws lambda invoke \
  --function-name alchemiser-shared-data-quality-coordinator \
  --payload '{"lookback_days": 5}' \
  response.json

# Via AWS Console
# Navigate to Lambda → alchemiser-shared-data-quality-coordinator → Test
# Event JSON:
{
  "lookback_days": 5
}
```

**Response:**
```json
{
  "statusCode": 200,
  "body": {
    "status": "initiated",
    "session_id": "session-abc123...",
    "total_symbols": 188,
    "total_batches": 24,
    "estimated_duration_minutes": 24
  }
}
```

### Validate Specific Symbols

```json
{
  "symbols": ["AAPL", "GOOGL", "MSFT"],
  "lookback_days": 10
}
```

### Monitor Progress

Query DynamoDB to check session progress:

```python
import boto3

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table("alchemiser-data-quality-validation-sessions")

# Get session metadata
response = table.get_item(
    Key={"PK": "SESSION#<session-id>", "SK": "METADATA"}
)
session = response["Item"]

print(f"Status: {session['status']}")
print(f"Completed: {sum(1 for b in session['batches'] if b['status'] == 'completed')}/{session['total_batches']}")

# Get symbol results
results = table.query(
    KeyConditionExpression="PK = :pk AND begins_with(SK, :sk)",
    ExpressionAttributeValues={
        ":pk": f"SESSION#{session_id}",
        ":sk": "RESULT#"
    }
)

for item in results["Items"]:
    print(f"{item['symbol']}: {'PASS' if item['passed'] else 'FAIL'}")
    if not item['passed']:
        print(f"  Issues: {item['issues']}")
```

## Monitoring

### CloudWatch Logs

- **Coordinator:** `/aws/lambda/alchemiser-shared-data-quality-coordinator`
- **Batch Processor:** `/aws/lambda/alchemiser-shared-data-quality-batch-processor`

### CloudWatch Metrics

Monitor SQS queue metrics:
- `ApproximateNumberOfMessagesVisible` - Batches waiting to process
- `ApproximateNumberOfMessagesNotVisible` - Batches currently processing
- `NumberOfMessagesReceived` - Total batches processed

### Dead Letter Queue

Monitor `alchemiser-data-quality-validation-dlq` for persistent failures:

```bash
aws sqs receive-message \
  --queue-url $(aws sqs get-queue-url --queue-name alchemiser-data-quality-validation-dlq --query QueueUrl --output text) \
  --max-number-of-messages 10
```

### EventBridge Events

The system publishes:
- `WorkflowCompleted` - All batches successfully processed
- `WorkflowFailed` - Critical error in coordinator or batch processor

## Error Handling

### Individual Symbol Failures

- Logged as warnings, don't fail the batch
- Stored in DynamoDB with `passed: false`
- Example: Symbol not found, API timeout

### Batch Failures

- Batch marked as FAILED in DynamoDB
- Next batch still processes (graceful degradation)
- After 3 retries, moves to DLQ

### Session Recovery

If a batch fails and you want to retry:

1. Identify the session ID from CloudWatch Logs
2. Query DynamoDB to find failed batches
3. Manually enqueue failed batch to SQS:

```python
import boto3
import json

sqs = boto3.client("sqs")
queue_url = "https://sqs.us-east-1.amazonaws.com/<account>/alchemiser-data-quality-validation-queue"

message = {
    "session_id": "session-abc123...",
    "correlation_id": "quality-coord-xyz...",
    "batch_number": 5,  # The failed batch
    "symbols": ["AAPL", "GOOGL", "MSFT"],
    "lookback_days": 5
}

sqs.send_message(QueueUrl=queue_url, MessageBody=json.dumps(message))
```

## Testing

Run unit tests:

```bash
source .venv/bin/activate
python -m pytest tests/data_quality_monitor/ -v
```

All 13 tests should pass:
- Session creation and batch splitting
- Batch status transitions
- Session completion detection
- DynamoDB serialization/deserialization

## Cost Estimate

For 188 symbols validated daily:

| Service | Usage | Cost/Month |
|---------|-------|------------|
| Lambda (Coordinator) | 1 invoke/day × 2s × 512MB | $0.00 |
| Lambda (Batch Processor) | 24 invokes/day × 10s × 1024MB | $0.02 |
| DynamoDB (Sessions) | 24 batches/day × 7-day TTL | $0.00 |
| SQS (Queue) | 24 messages/day | $0.00 |
| Twelve Data API | 188 symbols/day (free tier: 800/day) | $0.00 |

**Total: ~$0.02/month** (effectively free within AWS free tier)

## Troubleshooting

### Queue Not Processing

**Symptom:** Messages stuck in ValidationQueue

**Check:**
1. Lambda has correct IAM permissions for SQS
2. Lambda event source mapping is enabled
3. Check CloudWatch Logs for errors

### Session Stuck in PROCESSING

**Symptom:** Session never completes

**Resolution:**
1. Query DynamoDB to find which batch is stuck
2. Check CloudWatch Logs for that batch number
3. Look for API rate limit errors or timeouts
4. Manually retry the batch (see Error Handling above)

### Rate Limit Errors Still Occurring

**Symptom:** Still seeing "run out of API credits" errors

**Check:**
1. Verify batch size is 8 (not higher)
2. Verify 60-second delay is being used
3. Check if multiple sessions are running concurrently
4. Consider upgrading Twelve Data plan

## Future Enhancements

Potential improvements:
- Add SNS notifications for workflow completion
- Dashboard for real-time session monitoring
- Automated retry logic for failed batches
- Support for different batch sizes based on API tier
- Parallel processing for different symbol groups (if API tier supports it)
