# EventBridge Migration Guide

## Overview

This document describes the migration from the in-memory `EventBus` to Amazon EventBridge for the Alchemiser trading system. The approach is simple: build the EventBridge implementation, test it thoroughly, then switch completely with no tech debt.

## Architecture

### Before: In-Memory Event Bus

```
Lambda Invocation (15 min timeout)
  └─> In-Memory EventBus
      ├─> SignalGenerated → Portfolio Handler (sync)
      ├─> RebalancePlanned → Execution Handler (sync)
      └─> TradeExecuted → Orchestrator (sync)
```

**Limitations:**
- No durability: Events lost on timeout/crash
- No replay capability
- Synchronous blocking
- Single-process only
- No observability

### After: EventBridge Event Bus

```
Lambda Invocation
  └─> EventBridge Bus (durable, async)
      ├─> SignalGenerated → Portfolio Lambda (async)
      ├─> RebalancePlanned → Execution Lambda (async)
      └─> TradeExecuted → Orchestrator Lambda (async)
      
EventBridge Bus
  ├─> Event Archive (S3, 365-day retention)
  ├─> Dead Letter Queue (failed events)
  └─> CloudWatch Metrics (observability)
```

**Benefits:**
- **Durability**: Events persisted before processing
- **Async execution**: Non-blocking, independent Lambda timeouts
- **Replay capability**: Reprocess events from archive
- **Observability**: CloudWatch logs, metrics, X-Ray tracing
- **Scalability**: Horizontal scaling with multiple Lambda instances
- **Error handling**: Automatic retries, DLQ for failed events

## Migration Approach

### Phase 1: Infrastructure Setup ✅ (Current)

**Goal**: Deploy EventBridge infrastructure without changing code behavior.

**Changes:**
- Added `EventBridgeSettings` to configuration (simple, no feature flags)
- Created CloudFormation resources:
  - `AlchemiserEventBus`: Named event bus (standard EventBridge, not default bus)
  - `EventBusPolicy`: IAM policy for event publishing
  - `EventArchive`: S3 archive with 365-day retention
  - `EventDLQ`: Dead-letter queue for failed events
  - Event routing rules (disabled)
- Updated Lambda IAM permissions for EventBridge

**Status**: Infrastructure deployed but disabled. No runtime changes.

**Risk**: None - infrastructure only.

### Phase 2: EventBridge Implementation (Next)

**Goal**: Implement EventBridge event publishing and handling, test thoroughly.

**Planned Changes:**
1. Create `EventBridgeBus` class implementing `EventBus` interface
2. Create Lambda handler for EventBridge events
3. Enable event routing rules
4. Add comprehensive integration tests
5. Test in dev environment with real workflows

**No Dual-Publishing**: We build the complete implementation and test it, then switch cleanly.

**Validation:**
- Integration tests verify event delivery and processing
- Test event replay capability from archive
- Test DLQ behavior with intentional failures
- Monitor CloudWatch metrics during testing
- Run full trading workflow tests in dev

**Risk**: Low - thoroughly tested before production deployment.

### Phase 3: Production Switch (Future)

**Goal**: Switch production to EventBridge completely.

**Planned Changes:**
1. Deploy EventBridge implementation to production
2. Update orchestration to use `EventBridgeBus` instead of in-memory bus
3. Remove in-memory bus code (clean, no tech debt)

**Configuration:**
Simple switch in code - no environment variables or feature flags needed.
3. Split Lambda into separate functions per handler (optional)
4. Enable all event routing rules
5. Remove in-memory bus code (after 1 month buffer)

**Risk**: Medium - primary event delivery mechanism changes. Mitigated by thorough Phase 2 testing.

## Configuration

### EventBridge Settings

The `EventBridgeSettings` class provides simple configuration options:

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `event_bus_name` | str | `"alchemiser-trading-events"` | Name of the EventBridge event bus |
| `source_prefix` | str | `"alchemiser"` | Prefix for event sources |
| `max_retry_attempts` | int | `3` | Maximum retry attempts for failed events |
| `max_event_age_seconds` | int | `3600` | Max event age before retry expires |
| `archive_retention_days` | int | `365` | Event archive retention period |

### Environment Variables

Settings can be overridden using environment variables with the pattern `EVENTBRIDGE__<SETTING>`:

```bash
# Use custom event bus name
EVENTBRIDGE__EVENT_BUS_NAME=my-custom-bus

# Adjust retry behavior
EVENTBRIDGE__MAX_RETRY_ATTEMPTS=5
EVENTBRIDGE__MAX_EVENT_AGE_SECONDS=7200
```

### CloudFormation Parameters

The template creates the following resources per stage:

**Resources:**
- `AlchemiserEventBus`: `alchemiser-trading-events-${Stage}` (named event bus, not default)
- `EventArchive`: `alchemiser-event-archive-${Stage}`
- `EventDLQ`: `alchemiser-event-dlq-${Stage}`

**Event Rules:**
- `SignalGeneratedRule`: Routes `alchemiser.strategy.SignalGenerated` events
- `RebalancePlannedRule`: Routes `alchemiser.portfolio.RebalancePlanned` events
- `TradeExecutedRule`: Routes `alchemiser.execution.TradeExecuted` events
- `AllEventsToOrchestratorRule`: Routes all `alchemiser.*` events for monitoring

All rules are **DISABLED** in Phase 1 and will be enabled in Phase 2.

## Event Schema

EventBridge events follow this structure:

```json
{
  "version": "0",
  "id": "unique-event-id",
  "detail-type": "SignalGenerated",
  "source": "alchemiser.strategy",
  "account": "123456789012",
  "time": "2025-10-13T20:00:00Z",
  "region": "us-east-1",
  "resources": [
    "correlation:abc-123-def",
    "causation:xyz-789-ghi"
  ],
  "detail": {
    "event_id": "evt_abc123",
    "event_type": "SignalGenerated",
    "correlation_id": "abc-123-def",
    "causation_id": "xyz-789-ghi",
    "timestamp": "2025-10-13T20:00:00+00:00",
    "source_module": "strategy",
    "schema_version": "1.0",
    "signals_data": {...},
    "consolidated_portfolio": {...},
    "signal_count": 5
  }
}
```

**Key Fields:**
- `source`: Event source (e.g., `alchemiser.strategy`)
- `detail-type`: Event type (e.g., `SignalGenerated`)
- `resources`: Correlation/causation IDs for tracing
- `detail`: Full event payload as JSON

## Deployment

### Deploy Infrastructure (Phase 1)

```bash
# Deploy to dev
ENVIRONMENT=dev bash scripts/deploy.sh

# Deploy to prod
ENVIRONMENT=prod bash scripts/deploy.sh
```

This deploys:
- EventBridge event bus
- Event archive
- Dead-letter queue
- Event routing rules (disabled)
- IAM permissions

**Verify Deployment:**

```bash
# Check EventBridge resources
aws events list-event-buses --name-prefix alchemiser

# Check event rules
aws events list-rules --event-bus-name alchemiser-trading-events-dev

# Check DLQ
aws sqs get-queue-attributes --queue-url <queue-url>
```

### Enable Dual-Publish (Phase 2)

```bash
# Update Lambda environment variables
aws lambda update-function-configuration \
  --function-name the-alchemiser-v2-lambda-dev \
  --environment Variables='{
    "EVENTBRIDGE__ENABLE_DUAL_PUBLISH": "true",
    ...
  }'

# Enable event routing rules
aws events enable-rule \
  --event-bus-name alchemiser-trading-events-dev \
  --name alchemiser-signal-generated-dev
```

## Monitoring & Observability

### CloudWatch Metrics

EventBridge publishes metrics to CloudWatch:

- `Invocations`: Number of times targets were invoked
- `FailedInvocations`: Number of failed target invocations
- `ThrottledRules`: Number of times rules were throttled
- `MatchedEvents`: Number of events matched by rules

**View Metrics:**

```bash
# Get invocation metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/Events \
  --metric-name Invocations \
  --dimensions Name=EventBusName,Value=alchemiser-trading-events-dev \
  --start-time 2025-10-13T00:00:00Z \
  --end-time 2025-10-13T23:59:59Z \
  --period 3600 \
  --statistics Sum
```

### Dead Letter Queue Monitoring

Monitor the DLQ for failed events:

```bash
# Check DLQ depth
aws sqs get-queue-attributes \
  --queue-url <dlq-url> \
  --attribute-names ApproximateNumberOfMessages

# Retrieve failed messages
aws sqs receive-message \
  --queue-url <dlq-url> \
  --max-number-of-messages 10
```

**Alarm Setup:**

The template includes a CloudWatch Alarm (to be added in Phase 2) that triggers when:
- DLQ message count > 5
- Evaluation period: 5 minutes

### Event Replay

Replay events from the archive for debugging or reprocessing:

**Using AWS CLI:**

```bash
# Start a replay
aws events start-replay \
  --replay-name "replay-2025-10-13" \
  --event-source-arn arn:aws:events:us-east-1:123456789012:archive/alchemiser-event-archive-dev \
  --event-start-time 2025-10-13T00:00:00Z \
  --event-end-time 2025-10-13T23:59:59Z \
  --destination '{
    "Arn": "arn:aws:events:us-east-1:123456789012:event-bus/alchemiser-trading-events-dev"
  }'

# Check replay status
aws events describe-replay --replay-name "replay-2025-10-13"
```

**Using Python Script (Phase 2):**

```python
# scripts/replay_events.py
from datetime import datetime, timedelta
import boto3

def replay_events(start_time: datetime, end_time: datetime):
    events = boto3.client("events")
    
    response = events.start_replay(
        ReplayName=f"replay-{datetime.now().isoformat()}",
        EventSourceArn="arn:aws:events:us-east-1:123456789012:archive/alchemiser-event-archive-dev",
        EventStartTime=start_time,
        EventEndTime=end_time,
        Destination={
            "Arn": "arn:aws:events:us-east-1:123456789012:event-bus/alchemiser-trading-events-dev"
        },
    )
    
    print(f"Replay started: {response['ReplayArn']}")
```

## Cost Estimation

**Monthly Cost (100 events/day, 3000 events/month):**

| Service | Usage | Unit Cost | Monthly Cost |
|---------|-------|-----------|--------------|
| EventBridge | 3,000 events | $1 per 1M events | $0.003 |
| Lambda invocations | 3,000 invocations | $0.20 per 1M | $0.0006 |
| Lambda compute (3s avg) | 9,000 GB-sec | $0.0000166667 per GB-sec | $0.15 |
| S3 archive (1 GB) | 1 GB storage | $0.023 per GB | $0.023 |
| CloudWatch Logs (500 MB) | 500 MB storage | $0.50 per GB | $0.25 |
| **Total** | | | **~$0.43/month** |

**Annual Cost:** ~$5.16/year (negligible!)

## Testing

### Unit Tests (Phase 2)

Test the `EventBridgeBus` class:

```python
# tests/shared/events/test_eventbridge_bus.py
def test_publish_to_eventbridge(mock_events_client):
    bus = EventBridgeBus(event_bus_name="test-bus")
    event = SignalGenerated(...)
    
    bus.publish(event)
    
    mock_events_client.put_events.assert_called_once()
```

### Integration Tests (Phase 2)

Test the full workflow through EventBridge:

```python
# tests/integration/test_eventbridge_workflow.py
def test_full_workflow_via_eventbridge(eventbridge_bus):
    # Publish event
    signal_event = SignalGenerated(...)
    eventbridge_bus.publish(signal_event)
    
    # Wait for workflow completion
    result = wait_for_workflow_completion(
        signal_event.correlation_id,
        timeout=60
    )
    
    assert result.success
```

### Chaos Testing (Phase 3)

Test resilience:
- Simulate Lambda timeouts during execution
- Verify event replay recovers state
- Test DLQ handling for permanently failed events

## Troubleshooting

### Events Not Appearing in EventBridge

**Check:**
1. EventBridge bus exists: `aws events list-event-buses`
2. IAM permissions: Lambda has `events:PutEvents` permission
3. Event bus policy: Allows Lambda to publish
4. Configuration: `EVENTBRIDGE__ENABLE_DUAL_PUBLISH=true` or `EVENTBRIDGE__USE_EVENTBRIDGE=true`

### Events in DLQ

**Investigate:**
1. Check DLQ messages: `aws sqs receive-message --queue-url <dlq-url>`
2. Review Lambda logs: `aws logs tail /aws/lambda/the-alchemiser-v2-lambda-dev`
3. Check event pattern: Verify event source/detail-type matches rule

### Event Replay Not Working

**Verify:**
1. Archive exists and is enabled: `aws events describe-archive`
2. Time range includes events: Check archive event pattern
3. Destination bus is correct
4. Replay state: `aws events describe-replay`

## References

- [Amazon EventBridge Documentation](https://docs.aws.amazon.com/eventbridge/)
- [EventBridge Best Practices](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-best-practices.html)
- [Event-Driven Architecture Patterns](https://aws.amazon.com/event-driven-architecture/)
- [EventBridge vs SQS Comparison](https://aws.amazon.com/blogs/compute/choosing-between-messaging-services-for-serverless-applications/)

## Next Steps

### Immediate (Phase 2)

1. Implement `EventBridgeBus` class
2. Add dual-publish logic to event publishers
3. Create Lambda handler for EventBridge events
4. Enable event routing rules
5. Add integration tests
6. Deploy to dev and monitor for 1-2 weeks

### Future (Phase 3)

1. Switch to EventBridge as primary
2. Split Lambda into separate functions (optional)
3. Enable all event routing rules
4. Remove in-memory bus code
5. Deploy to production

### Optional Enhancements

1. **Schema Registry**: Define event schemas in AWS Schema Registry
2. **Content-based Routing**: Filter events based on payload values
3. **CloudWatch Dashboard**: Create custom dashboard for EventBridge metrics
4. **Alarms**: Set up alarms for high DLQ counts, failed invocations
5. **X-Ray Integration**: Enable end-to-end tracing across Lambda invocations
