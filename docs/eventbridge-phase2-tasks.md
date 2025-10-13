# Phase 2: EventBridge Adapter Implementation

## Overview

Phase 2 implements the `EventBridgeBus` class and enables dual-publish mode for testing and validation before full migration.

## Implementation Tasks

### 1. Create EventBridge Bus Adapter

**File:** `the_alchemiser/shared/events/eventbridge_bus.py`

**Requirements:**
- Implement `EventBus` interface for compatibility
- Use `boto3` EventBridge client for event publishing
- Support dual-publish mode (publish to both in-memory and EventBridge)
- Handle errors gracefully (log and continue)
- Add correlation/causation IDs to event resources for tracing

**Key Methods:**
```python
class EventBridgeBus(EventBus):
    def __init__(
        self,
        event_bus_name: str,
        source_prefix: str,
        enable_local_handlers: bool = False,
    ) -> None:
        """Initialize EventBridge client and settings."""
        
    def publish(self, event: BaseEvent) -> None:
        """Publish event to EventBridge using boto3 client."""
        
    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        """Note: Subscriptions managed via CloudFormation EventRules."""
```

### 2. Create Lambda Handler for EventBridge Events

**File:** `the_alchemiser/lambda_handler_eventbridge.py`

**Requirements:**
- Parse EventBridge event payload structure
- Extract `detail-type` and `detail` from event
- Route to appropriate handler based on event type
- Handle errors and re-raise for Lambda retry

**Function:**
```python
def eventbridge_handler(event: dict, context: object) -> dict:
    """Handle EventBridge event by routing to appropriate handler."""
```

### 3. Update Container to Support EventBridge

**File:** `the_alchemiser/shared/config/container.py`

**Requirements:**
- Add factory method for `EventBridgeBus`
- Support dual-publish mode via configuration
- Allow switching between in-memory and EventBridge bus

### 4. Add CloudFormation Targets to Event Rules

**File:** `template.yaml`

**Updates:**
- Add Lambda targets to event rules
- Configure retry policy (3 attempts, 1 hour max age)
- Add dead-letter queue configuration
- Enable event rules (change `State: DISABLED` to `State: ENABLED`)

**Example:**
```yaml
SignalGeneratedRule:
  Type: AWS::Events::Rule
  Properties:
    Name: !Sub "alchemiser-signal-generated-${Stage}"
    EventBusName: !Ref AlchemiserEventBus
    State: ENABLED  # Change from DISABLED
    EventPattern:
      source:
        - alchemiser.strategy
      detail-type:
        - SignalGenerated
    Targets:
      - Arn: !GetAtt TradingSystemFunction.Arn
        Id: PortfolioHandler
        RetryPolicy:
          MaximumRetryAttempts: 3
          MaximumEventAge: 3600
        DeadLetterConfig:
          Arn: !GetAtt EventDLQ.Arn
```

### 5. Add Lambda Permission for EventBridge Invocation

**File:** `template.yaml`

**Resources:**
```yaml
EventBridgeInvokeLambdaPermission:
  Type: AWS::Lambda::Permission
  Properties:
    FunctionName: !Ref TradingSystemFunction
    Action: lambda:InvokeFunction
    Principal: events.amazonaws.com
    SourceArn: !GetAtt AlchemiserEventBus.Arn
```

### 6. Create Integration Tests

**File:** `tests/integration/test_eventbridge_workflow.py`

**Test Cases:**
- Event publishing to EventBridge
- Event routing to correct handlers
- Event replay from archive
- DLQ behavior with failed events
- Dual-publish comparison (in-memory vs EventBridge)

### 7. Create Helper Scripts

**Files:**
- `scripts/eventbridge/replay_events.py`: Replay events from archive
- `scripts/eventbridge/check_dlq.py`: Check and process DLQ messages
- `scripts/eventbridge/test_event_publish.py`: Manual event publishing for testing

## Deployment Steps

### 1. Deploy Code Changes

```bash
# Install dependencies
poetry install

# Run tests
make test

# Deploy to dev
ENVIRONMENT=dev bash scripts/deploy.sh
```

### 2. Enable Dual-Publish Mode

```bash
# Update Lambda environment variables
aws lambda update-function-configuration \
  --function-name the-alchemiser-v2-lambda-dev \
  --environment Variables='{
    "EVENTBRIDGE__ENABLE_DUAL_PUBLISH": "true"
  }'
```

### 3. Enable Event Rules

```bash
# Enable all event rules
for rule in signal-generated rebalance-planned trade-executed all-events-monitor; do
  aws events enable-rule \
    --event-bus-name alchemiser-trading-events-dev \
    --name alchemiser-${rule}-dev
done
```

### 4. Monitor and Validate

**Check CloudWatch Metrics:**
```bash
# View EventBridge metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/Events \
  --metric-name Invocations \
  --dimensions Name=EventBusName,Value=alchemiser-trading-events-dev \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum
```

**Check Lambda Logs:**
```bash
# Tail Lambda logs
sam logs -n TradingSystemFunction --tail

# Or use AWS CLI
aws logs tail /aws/lambda/the-alchemiser-v2-lambda-dev --follow
```

**Check DLQ:**
```bash
# Get DLQ message count
aws sqs get-queue-attributes \
  --queue-url $(aws sqs get-queue-url --queue-name alchemiser-event-dlq-dev --query 'QueueUrl' --output text) \
  --attribute-names ApproximateNumberOfMessages
```

### 5. Validation Period

**Duration:** 1-2 weeks

**Monitoring:**
- Compare event delivery between in-memory and EventBridge
- Verify no events in DLQ (except intentional test failures)
- Check Lambda execution times
- Monitor CloudWatch metrics

**Success Criteria:**
- 100% event delivery to EventBridge
- Zero production events in DLQ
- Lambda execution times within acceptable range
- No errors in logs

## Testing Checklist

### Unit Tests
- [ ] `EventBridgeBus.publish()` calls boto3 client correctly
- [ ] `EventBridgeBus.publish()` handles errors gracefully
- [ ] `eventbridge_handler()` parses EventBridge payload
- [ ] `eventbridge_handler()` routes to correct handler
- [ ] Event serialization/deserialization works correctly

### Integration Tests
- [ ] Full workflow through EventBridge (signal → execution)
- [ ] Event replay from archive
- [ ] DLQ behavior with intentional failures
- [ ] Dual-publish comparison
- [ ] Correlation/causation ID propagation

### Manual Testing
- [ ] Publish test event to EventBridge
- [ ] Verify event appears in CloudWatch Logs
- [ ] Verify event is archived
- [ ] Test event replay
- [ ] Trigger Lambda via EventBridge
- [ ] Verify DLQ receives failed events

## Rollback Plan

If issues are found during validation:

1. **Disable Dual-Publish:**
   ```bash
   aws lambda update-function-configuration \
     --function-name the-alchemiser-v2-lambda-dev \
     --environment Variables='{"EVENTBRIDGE__ENABLE_DUAL_PUBLISH": "false"}'
   ```

2. **Disable Event Rules:**
   ```bash
   for rule in signal-generated rebalance-planned trade-executed all-events-monitor; do
     aws events disable-rule \
       --event-bus-name alchemiser-trading-events-dev \
       --name alchemiser-${rule}-dev
   done
   ```

3. **Revert Code Changes:**
   ```bash
   git revert <commit-sha>
   ENVIRONMENT=dev bash scripts/deploy.sh
   ```

## Success Metrics

- **Event Delivery Rate:** 100% of events delivered to EventBridge
- **Latency Impact:** < 100ms overhead for EventBridge publish
- **Error Rate:** Zero events in DLQ (excluding test failures)
- **Replay Success:** Successfully replay events from archive
- **Dual-Publish Consistency:** 100% match between in-memory and EventBridge events

## Next Phase

After successful validation of Phase 2:

**Phase 3: Full Migration**
1. Set `EVENTBRIDGE__USE_EVENTBRIDGE=true` in production
2. Disable in-memory bus
3. Remove in-memory bus code (after 1 month buffer)
4. Consider splitting Lambda into separate functions per handler (optional)

See [eventbridge-migration.md](./eventbridge-migration.md) for full migration guide.
