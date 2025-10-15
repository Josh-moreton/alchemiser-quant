# EventBridge Migration Gotchas & Potential Issues

## Issues Already Fixed ✅

### 1. JSON Serialization (`Decimal`, `datetime`, `Exception`)
**Problem:** EventBridge requires JSON strings, but Python `Decimal`, `datetime`, and `Exception` objects aren't JSON-serializable.

**Solution Implemented:**
- Use `model_dump_json()` in EventBridge bus (respects `PlainSerializer` definitions)
- Use `model_dump(mode="json")` when creating event payloads
- Never pass raw exceptions - convert to `{"error_type": "...", "error_message": "..."}`

**Files Fixed:**
- `shared/events/eventbridge_bus.py` - Uses `model_dump_json()`
- `lambda_handler.py` - Uses `mode="json"` for logging
- `strategy_v2/handlers/signal_generation_handler.py` - Uses `mode="json"`
- `execution_v2/handlers/trading_execution_handler.py` - Uses `mode="json"`
- `execution_v2/core/settlement_monitor.py` - Uses `mode="json"`

---

## Potential Issues to Watch For ⚠️

### 2. EventBridge Payload Size Limit (256 KB)
**AWS Limit:** EventBridge events have a **hard limit of 256 KB** for the entire event entry (including detail, resources, etc.).

**Risk Areas:**
```python
# Large indicator data in SignalGenerated
SignalGenerated(
    signals_data=huge_dict,  # Could exceed 256KB
    consolidated_portfolio=portfolio.model_dump(mode="json"),
    metadata=big_metadata
)

# Many orders in TradeExecuted
TradeExecuted(
    execution_data={
        "orders": [order.model_dump(mode="json") for order in 500_orders]  # Too big!
    }
)
```

**Mitigation Strategies:**
1. **Store large data in S3, reference in event:**
   ```python
   # Upload to S3
   s3_key = f"signals/{correlation_id}/data.json"
   s3_client.put_object(Bucket=bucket, Key=s3_key, Body=json_data)

   # Event only contains reference
   SignalGenerated(
       signals_data_s3_key=s3_key,  # Just the key, not the data
       signal_count=len(signals)
   )
   ```

2. **Summarize data in events:**
   ```python
   # Instead of full orders
   TradeExecuted(
       execution_data={
           "summary": {"total_value": "10000", "symbols": ["AAPL", "GOOGL"]},
           "full_ledger_s3_key": s3_key  # Full data in S3
       }
   )
   ```

3. **Add size check before publishing:**
   ```python
   def publish(self, event: BaseEvent) -> None:
       detail_json = event.model_dump_json()

       # Check size (EventBridge limit is 256KB for entire entry)
       if len(detail_json.encode('utf-8')) > 200_000:  # Leave buffer
           logger.error(
               "Event payload too large for EventBridge",
               event_type=event.event_type,
               size_bytes=len(detail_json.encode('utf-8'))
           )
           # Either: raise error, truncate, or store in S3

       # Proceed with publish...
   ```

**Check Now:**
```bash
# Find largest events in logs
aws logs filter-events \
  --log-group-name /aws/lambda/the-alchemiser-v2 \
  --filter-pattern "Event published to EventBridge" \
  --query 'events[*].[message]' | \
  jq '.[] | fromjson | .event_type + ": " + (.size_estimate // "unknown")'
```

---

### 3. EventBridge Eventual Consistency
**Issue:** Events may arrive **out of order** or with slight delays (typically milliseconds, but can be seconds under load).

**Risk Scenarios:**
```python
# Scenario 1: Race condition
event_bus.publish(SignalGenerated(...))      # Event A
event_bus.publish(RebalancePlanned(...))     # Event B

# B might arrive before A! Handler for B assumes A has completed.
```

**Solution:**
- **Use causation_id chains:** Each event should reference its trigger
- **Idempotency:** Handlers must handle replays/duplicates
- **State checks:** Don't assume ordering

```python
# Good: Check state before processing
def handle_event(self, event: RebalancePlanned) -> None:
    # Verify the SignalGenerated event that caused this
    if not self._signal_exists(event.causation_id):
        logger.warning("SignalGenerated not found, event may be out of order")
        # Either: retry later, or query state from source
```

---

### 4. Lambda Cold Starts & Timeouts
**Issue:** EventBridge invokes Lambda, which has cold start times (~3-5 seconds) and timeout limits (max 15 minutes, but we use 600s).

**Risk Scenarios:**
- **Heavy signal generation:** DSL parsing 7 strategy files + 1000+ indicator calculations
- **Network delays:** Alpaca API calls during market volatility
- **Sequential processing:** Each event = new Lambda invocation

**Current Timeout:** 600 seconds (10 minutes)

**Monitoring:**
```bash
# Check Lambda durations
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Duration \
  --dimensions Name=FunctionName,Value=the-alchemiser-v2-lambda-dev \
  --start-time $(date -u -d '1 day ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 3600 \
  --statistics Average,Maximum
```

**Solution:**
- **Break up long tasks:** Don't do all indicator calcs in one handler
- **Optimize cold starts:** Keep Lambda warm with scheduled pings
- **Increase timeout if needed:** But investigate why it's slow first

---

### 5. Event Replay & Idempotency
**Issue:** EventBridge may **retry failed events** or you may **replay from archive**. Handlers must be idempotent.

**Current State:**
- ✅ `lambda_handler_eventbridge.py` has idempotency checks using DynamoDB
- ⚠️ But business logic may not handle replays correctly

**Risk Scenarios:**
```python
# Handler processes TradeExecuted event twice
# - First time: Updates portfolio state, sends notification
# - Replay: Updates again (duplicate!), sends notification again

# Non-idempotent code:
def handle_trade_executed(self, event: TradeExecuted):
    self.portfolio.apply_trades(event.execution_data)  # ❌ Applied twice!
    self.notify_user(event)  # ❌ Sent twice!
```

**Solution:**
```python
# Idempotent code:
def handle_trade_executed(self, event: TradeExecuted):
    # Check if already processed
    if self._is_already_processed(event.event_id):
        logger.info("Event already processed, skipping")
        return

    # Process
    self.portfolio.apply_trades(event.execution_data)
    self.notify_user(event)

    # Mark as processed
    self._mark_processed(event.event_id)
```

---

### 6. EventBridge Throttling & Rate Limits
**AWS Limits:**
- **PutEvents API:** 10,000 requests/second (soft limit, can be increased)
- **Invocations per second:** Varies by region, typically 2,400/second

**Risk Scenario:**
- Burst of events during signal generation (e.g., 100+ symbols)
- Multiple strategies publishing simultaneously

**Current Risk:** Low (we're not near limits)

**Future Mitigation:**
- Batch events using `put_events(Entries=[...])` (up to 10 events per call)
- Implement exponential backoff on throttling errors
- Request limit increase from AWS if needed

---

### 7. Dead Letter Queue (DLQ) Buildup
**Issue:** Failed events go to DLQ, but if not monitored, they accumulate silently.

**Current State:**
- ✅ DLQ exists: `alchemiser-trading-events-dlq-{Stage}`
- ⚠️ No CloudWatch alarms on DLQ depth

**Solution:**
```bash
# Check DLQ depth
aws sqs get-queue-attributes \
  --queue-url $(aws sqs get-queue-url --queue-name alchemiser-trading-events-dlq-dev --query 'QueueUrl' --output text) \
  --attribute-names ApproximateNumberOfMessages

# Add CloudWatch alarm
aws cloudwatch put-metric-alarm \
  --alarm-name EventBridgeDLQDepth \
  --alarm-description "Alert when DLQ has messages" \
  --metric-name ApproximateNumberOfMessagesVisible \
  --namespace AWS/SQS \
  --statistic Sum \
  --period 300 \
  --threshold 1 \
  --comparison-operator GreaterThanThreshold
```

---

### 8. Correlation ID Propagation
**Issue:** EventBridge doesn't automatically propagate correlation IDs - we must do it manually.

**Current State:** ✅ Implemented via `Resources` field
```python
resources = [
    f"correlation:{event.correlation_id}",
    f"causation:{event.causation_id}"
]
```

**But watch for:**
- Missing correlation IDs in manually created events
- Correlation ID not passed to downstream services (e.g., Alpaca API calls)

---

### 9. EventBridge Archive Storage Costs
**Current Setting:** 365-day retention for all events

**Cost:** ~$0.023/GB/month
- Estimate: 1000 events/day × 5KB/event × 365 days = ~1.8 GB/year = **$0.50/year**

**Low priority,** but monitor if event volume increases dramatically.

---

### 10. Lambda Concurrent Execution Limits
**AWS Default:** 1,000 concurrent Lambda executions (account-wide)

**Risk Scenario:**
- EventBridge fires 50 events simultaneously
- Each Lambda runs for 30 seconds
- Need 50 concurrent executions

**Current Risk:** Low (we're sequential)

**Future Mitigation:**
- Set **reserved concurrency** for critical Lambdas
- Monitor concurrent executions in CloudWatch

---

## Recommended Monitoring

### CloudWatch Alarms to Add

1. **EventBridge Throttling:**
   ```bash
   aws cloudwatch put-metric-alarm \
     --alarm-name EventBridgeThrottled \
     --metric-name ThrottledRules \
     --namespace AWS/Events \
     --statistic Sum \
     --period 300 \
     --threshold 10 \
     --comparison-operator GreaterThanThreshold
   ```

2. **Lambda Errors:**
   ```bash
   aws cloudwatch put-metric-alarm \
     --alarm-name LambdaErrors \
     --metric-name Errors \
     --namespace AWS/Lambda \
     --dimensions Name=FunctionName,Value=the-alchemiser-v2-lambda-dev \
     --statistic Sum \
     --period 300 \
     --threshold 5 \
     --comparison-operator GreaterThanThreshold
   ```

3. **DLQ Depth** (see #7 above)

### Log Insights Queries

**Find large events:**
```
fields @timestamp, event_type, @message
| filter @message like /Event published to EventBridge/
| stats count() by event_type, strlen(@message) as size
| sort size desc
```

**Find slow Lambdas:**
```
fields @timestamp, @duration, detail_type
| filter detail_type != ""
| stats avg(@duration), max(@duration), count() by detail_type
| sort max(@duration) desc
```

**Find replay/duplicate events:**
```
fields @timestamp, event_id, correlation_id
| filter @message like /already processed/
| stats count() by event_id
| sort count desc
```

---

## Testing Checklist

Before going live with EventBridge, verify:

- [ ] All events serialize without errors (run full workflow in dev)
- [ ] Check largest event payload size (must be < 200 KB)
- [ ] Test event replay from archive (ensure idempotency works)
- [ ] Verify DLQ receives intentionally failed events
- [ ] Monitor Lambda durations (all < 60 seconds ideally)
- [ ] Check correlation IDs in CloudWatch Logs (end-to-end tracing)
- [ ] Test with network delays (simulate Alpaca API slowness)
- [ ] Verify no infinite loops (especially error notifications)

---

## Quick Reference

**EventBridge Limits:**
- Max event size: **256 KB**
- PutEvents rate: **10,000 req/sec** (soft limit)
- Archive retention: **365 days** (configurable)
- Delivery retries: **24 hours** (configurable via max_event_age_seconds)

**Lambda Limits:**
- Max timeout: **15 minutes** (we use 10 min)
- Max concurrency: **1,000** (account-wide, soft limit)
- Cold start: **~3-5 seconds** (Python 3.12)

**Costs (approximate):**
- EventBridge: **$1.00/million** events
- Lambda: **$0.20/million** requests + **$0.0000166667/GB-second**
- S3 (for large payloads): **$0.023/GB/month** storage

---

## Summary

**High Priority to Monitor:**
1. ✅ JSON serialization (fixed)
2. ⚠️ Event payload size (add checks)
3. ⚠️ DLQ depth (add alarms)
4. ⚠️ Lambda timeouts (monitor durations)

**Medium Priority:**
5. Event ordering / eventual consistency
6. Idempotency on replays
7. Correlation ID propagation

**Low Priority (but watch):**
8. Throttling / rate limits
9. Archive storage costs
10. Concurrent execution limits
