# Email Notifications Reference

This document catalogs all email notifications sent by The Alchemiser trading system, including triggers, recipients, and content.

## Quick Reference Table

| Email Type | Trigger Event | When Sent | Subject Format | Status Color | Dedup Applied |
|------------|---------------|-----------|----------------|--------------|---------------|
| **Daily Run SUCCESS** | `AllTradesCompleted` | All trades succeeded (failed_trades = 0) | `Alchemiser Daily Run — SUCCESS — YYYY-MM-DD — {env} — run_id={id}` | 🟢 Green | No |
| **Daily Run FAILURE** | `AllTradesCompleted` | Some trades failed (failed_trades > 0) | `Alchemiser Daily Run — FAILURE — YYYY-MM-DD — {env} — run_id={id}` | 🔴 Red | No |
| **Workflow Error** | `WorkflowFailed` | System/workflow failure (pre-execution) | `Alchemiser Daily Run — FAILURE — YYYY-MM-DD — {env} — run_id={id}` | 🔴 Red | Yes (120 min quiet period) |
| **System Recovered** | `AllTradesCompleted` (success) | Success after previous failures | `Alchemiser Daily Run — RECOVERED — YYYY-MM-DD — {env} — run_id={id}` | 🔵 Blue | No |
| **System Notification** | `SystemNotificationRequested` | Manual/administrative notifications | Custom subject | ⚪️ Gray | No |

---

## Detailed Email Specifications

### 1. Daily Run SUCCESS Email

**Trigger**: `AllTradesCompleted` event with `failed_trades = 0`

**Conditions**:
- At least one trade was placed (`total_trades > 0`)
- All trades succeeded (`failed_trades = 0`)
- Skipped trades don't count as failures

**Recipients**:
- **Production**: `NOTIFICATIONS_TO_PROD` env var
- **Non-Production**: `NOTIFICATIONS_TO_NONPROD` env var (with safety banner)

**Subject**:
```
Alchemiser Daily Run — SUCCESS — 2026-01-01 — prod — run_id=abc123
```

**Content Sections** (HTML + Plain Text):

1. **Identity & Timing**
   - Environment (dev/staging/prod)
   - Trading mode (PAPER/LIVE)
   - Run ID (6-char short form)
   - Correlation ID
   - Version (Git SHA)
   - Strategy version
   - Start/end timestamps
   - Duration in seconds

2. **Outcome Summary** (green box)
   - Symbols evaluated
   - Eligible signals
   - Blocked by risk gate
   - Orders: placed, filled, cancelled, rejected

3. **Portfolio Snapshot (Post-Run)**
   - Equity (total account value)
   - Cash available
   - Gross exposure (% of equity deployed)
   - Net exposure (long - short)
   - Top 3 positions (symbol, weight %)

4. **Data Freshness**
   - Latest candle timestamp
   - Age in days
   - DATA_FRESHNESS_GATE status (PASS/FAIL)

5. **Warnings** (yellow box, if any)
   - List of non-critical warnings

6. **Links**
   - CloudWatch Logs (filtered by run_id)
   - Strategy performance report (presigned S3 URL, if available)

**Deduplication**: None (always send success emails)

**Recovery Check**: Yes - triggers recovery email if previous failures exist

---

### 2. Daily Run FAILURE Email

**Trigger**: `AllTradesCompleted` event with `failed_trades > 0`

**Conditions**:
- Trades were attempted (`total_trades > 0`)
- At least one trade failed (`failed_trades > 0`)

**Recipients**: Same as SUCCESS

**Subject**:
```
Alchemiser Daily Run — FAILURE — 2026-01-01 — prod — run_id=abc123
```

**Content Sections** (HTML + Plain Text):

1. **What Failed + Impact** (red box)
   - Failed step: `execution`
   - Impact: "Trades did not execute successfully"
   - Failed symbols list (if available)

2. **Error Signature**
   - Exception type (e.g., `TradingFailure`, `AlpacaAPIError`)
   - Error message (truncated to 500 chars)
   - Stack trace (truncated to 2000 chars)

3. **Context**
   - Environment, Run ID, Correlation ID
   - Retry attempts (currently always 0)
   - Last attempt time
   - Last successful run ID/time (if tracked)

4. **Quick Actions** (blue box)
   - Suggested troubleshooting steps:
     - Check Alpaca account status and buying power
     - Verify market is open (Mon-Fri 9:30 AM - 4:00 PM ET)
     - Check for rejected orders in trade ledger
     - Review risk controls and position limits

5. **Links**
   - CloudWatch Logs (filtered by run_id)

**Deduplication**: None (trading failures are not deduplicated)

**Note**: Trading failures represent actual execution issues, not repeated system errors, so each failure is reported.

---

### 3. Workflow Error Email

**Trigger**: `WorkflowFailed` event (from any module: strategy, portfolio, execution, etc.)

**Conditions**:
- Workflow failed before or during execution
- System-level error (not trading execution failure)

**Recipients**: Same as SUCCESS

**Subject**:
```
Alchemiser Daily Run — FAILURE — 2026-01-01 — prod — run_id=abc123
```

**Content Sections** (HTML + Plain Text):

1. **What Failed + Impact** (red box)
   - Failed step (from `failure_step` field)
   - Impact description
   - Workflow type (e.g., `daily_run`)

2. **Error Signature**
   - Exception type (from `error_details.exception_type`)
   - Error message
   - Full error details formatted as list

3. **Context**
   - Source module (e.g., `strategy_v2`, `portfolio_v2`)
   - Environment, Run ID, Correlation ID
   - Timestamp

4. **Quick Actions** (blue box)
   - Suggested troubleshooting steps:
     - Check CloudWatch Logs for detailed stack trace
     - Verify Alpaca API connectivity and credentials
     - Check market data freshness in S3
     - Review recent code changes

5. **Links**
   - CloudWatch Logs (filtered by run_id)

**Deduplication**: **YES** - 120-minute quiet period

- **First occurrence**: Email sent immediately, record created in `NotificationDedupTable`
- **Repeat within 120 min**: Email suppressed, repeat counter incremented
- **Repeat after 120 min**: Email sent, last_email_sent_time updated
- **Dedup key format**: `{component}#{env}#{failed_step}#{error_hash}`
  - Example: `Daily Run#prod#data_fetch#a3f8bc12`

**Error Normalization**: Error messages are normalized before hashing:
- Timestamps → `<TIMESTAMP>`
- UUIDs → `<UUID>`
- Run IDs → `run_id=<RUN_ID>`
- Request IDs → `request_id=<REQUEST_ID>`

**DynamoDB Record** (90-day TTL):
```json
{
  "PK": "Daily Run#prod#data_fetch#a3f8bc12",
  "status": "FAILING",
  "first_seen_time_utc": "2026-01-01T12:00:00Z",
  "last_seen_time_utc": "2026-01-01T15:30:00Z",
  "repeat_count": 5,
  "last_run_id": "abc123",
  "last_email_sent_time_utc": "2026-01-01T12:00:00Z",
  "ttl": 1748534400
}
```

---

### 4. System Recovered Email

**Trigger**: `AllTradesCompleted` event with `trading_success = true`, **AND** previous failures exist in dedup table

**Conditions**:
- Current run succeeded (`trading_success = true`)
- Recovery check finds FAILING records in `NotificationDedupTable` for this component + environment

**Recipients**: Same as SUCCESS

**Subject**:
```
Alchemiser Daily Run — RECOVERED — 2026-01-01 — prod — run_id=abc123
```

**Content** (HTML + Plain Text):

```
✅ System Recovered

Previous failures have been resolved in run abc123.

Recovered Failures:
• Daily Run#prod#data_fetch#a3f8bc12: 5 occurrences
• Daily Run#prod#api_connection#f2e9ac77: 2 occurrences

The system is now operating normally.
```

**Deduplication**: None

**Recovery Process**:
1. DynamoDB scan finds all `FAILING` records for component + env
2. Each record is marked as `RECOVERED` with `recovered_run_id` and `recovered_time_utc`
3. Single recovery email sent listing all recovered failures
4. Records remain in DynamoDB for 90 days (TTL cleanup)

---

### 5. System Notification Email

**Trigger**: `SystemNotificationRequested` event (manual/administrative)

**Conditions**: Explicitly published by admin or automation script

**Recipients**: Same as SUCCESS

**Subject**: Custom (provided in event)

**Content**: Simple HTML wrapper around plain text content

```html
<h2>System Notification</h2>
<pre>{text_content}</pre>
```

**Deduplication**: None

**Use Cases**:
- Manual administrative announcements
- Scheduled maintenance notifications
- System health alerts (custom)

---

## Environment-Safe Routing

All emails implement environment-safe routing to prevent accidental prod emails in non-prod:

### Production (`APP__STAGE=prod`)
- **Recipients**: `NOTIFICATIONS_TO_PROD` (e.g., `team@company.com`)
- **Safety Banner**: None
- **Behavior**: Send to real recipients

### Non-Production (`APP__STAGE=dev` or `staging`)
- **Default Recipients**: `NOTIFICATIONS_TO_NONPROD` (safe override address)
- **Safety Banner**: Yellow warning box prepended to email
  ```
  ⚠️ NON-PRODUCTION ENVIRONMENT
  NOTE: Recipient override active (stage=dev).
  Original recipients suppressed: team@company.com
  ```
- **Behavior**: Send to override address UNLESS:
  - `ALLOW_REAL_EMAILS=true` is explicitly set (not recommended)
  - `NOTIFICATIONS_OVERRIDE_TO` is set (custom override)

### Configuration Matrix

| Environment | `ALLOW_REAL_EMAILS` | `NOTIFICATIONS_OVERRIDE_TO` | Actual Recipients | Safety Banner |
|-------------|---------------------|----------------------------|-------------------|---------------|
| `prod` | Any | Any | `NOTIFICATIONS_TO_PROD` | No |
| `dev` | `false` (default) | Not set | `NOTIFICATIONS_TO_NONPROD` | Yes |
| `dev` | `false` | `custom@test.com` | `custom@test.com` | Yes |
| `dev` | `true` | Any | `NOTIFICATIONS_TO_PROD` | No (⚠️ dangerous) |

**Recommendation**: Always use default routing in non-prod. Never set `ALLOW_REAL_EMAILS=true` in dev/staging.

---

## Email Format Standards

### Subject Line Format (Strict)

**Pattern**:
```
Alchemiser <Component> — <STATUS> — <YYYY-MM-DD> — <env> — run_id=<run_id>
```

**Components**:
- `<Component>`: "Daily Run", "Data Lake Update", etc.
- `<STATUS>`: "SUCCESS", "SUCCESS_WITH_WARNINGS", "FAILURE", "RECOVERED"
- `<YYYY-MM-DD>`: ISO date (e.g., 2026-01-01)
- `<env>`: Environment (dev, staging, prod)
- `<run_id>`: Short 6-character run ID (e.g., `abc123`)

**Examples**:
```
Alchemiser Daily Run — SUCCESS — 2026-01-01 — prod — run_id=8f3c1a
Alchemiser Daily Run — FAILURE — 2026-01-01 — dev — run_id=f2e9ac
Alchemiser Daily Run — RECOVERED — 2026-01-01 — prod — run_id=a1b2c3
Alchemiser Data Lake Update — SUCCESS — 2026-01-01 — staging — run_id=def456
```

**Why Strict Format?**
- Easy to filter in email clients (e.g., "Daily Run FAILURE")
- Consistent sorting by date
- Quick identification of environment and run ID
- Grep-friendly for log analysis

### HTML Email Standards

1. **Inline CSS Only**: No `<style>` tags or external CSS
2. **Max Width**: 800px for desktop readability
3. **Responsive**: Mobile-friendly (uses `max-width`)
4. **Font Stack**: `-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif`
5. **Color-Coded Status**: Green/Yellow/Red/Blue for visual scanning
6. **Tables for Layout**: Use `<table>` for multi-column layouts (email client compatibility)

### Plain Text Standards

1. **Max Line Length**: 80 characters for terminal readability
2. **ASCII Borders**: Use `=` and `-` for visual separation
3. **Indentation**: Consistent 2-space or bullet indentation
4. **No Markdown**: Plain text only (no **bold** or _italic_)

---

## Notification Event Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                         EVENT SOURCES                           │
└─────────────────────────────────────────────────────────────────┘
                              │
            ┌─────────────────┼─────────────────┐
            │                 │                 │
            ▼                 ▼                 ▼
   AllTradesCompleted   WorkflowFailed   SystemNotificationRequested
   (from TradeAggregator) (any module)   (admin/script)
            │                 │                 │
            └─────────────────┼─────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │   EventBridge    │
                    │   (Event Router) │
                    └──────────────────┘
                              │
                              ▼
                ┌─────────────────────────────┐
                │  Notifications Lambda       │
                │  (lambda_handler.py)        │
                └─────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
  AllTradesCompleted    WorkflowFailed      SystemNotification
  → _handle_all_trades  → _handle_workflow  (not implemented yet)
    _completed()          _failed()
        │                     │
        ▼                     ▼
  TradingNotification    ErrorNotification
  Requested              Requested
        │                     │
        └─────────────────────┼─────────────────────┘
                              │
                              ▼
                ┌─────────────────────────────┐
                │  NotificationService        │
                │  (service.py)               │
                └─────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
  _handle_trading_     _handle_error_      _handle_system_
  notification()       notification()      notification()
        │                     │                     │
        │              ┌──────▼──────┐              │
        │              │ Dedup Check │              │
        │              │ (120 min)   │              │
        │              └──────┬──────┘              │
        │                     │                     │
        │ (success)    ┌──────▼──────┐              │
        ├─────────────►│Recovery Check│              │
        │              │ (DynamoDB)   │              │
        │              └──────┬───────┘              │
        │                     │                      │
        │                     │ (if recovered)       │
        │              ┌──────▼──────┐               │
        │              │Send Recovery│               │
        │              │    Email    │               │
        │              └─────────────┘               │
        │                                            │
        └──────────────┬─────────────────────────────┘
                       │
                       ▼
            ┌────────────────────────┐
            │  Template Rendering    │
            │  (templates.py)        │
            │  - HTML + Plain Text   │
            └────────────────────────┘
                       │
                       ▼
            ┌────────────────────────┐
            │  SES Email Publisher   │
            │  (ses_publisher.py)    │
            │  - Routing Safety      │
            │  - Safety Banner       │
            └────────────────────────┘
                       │
                       ▼
            ┌────────────────────────┐
            │    Amazon SES          │
            │    (Send Email)        │
            └────────────────────────┘
                       │
                       ▼
            📧 Email Delivered to Inbox
```

---

## Testing Notifications

### Test Success Email

```bash
aws lambda invoke \
  --function-name alchemiser-dev-notifications \
  --region us-east-1 \
  --payload file://test_success.json \
  /tmp/response.json
```

**test_success.json**:
```json
{
  "version": "0",
  "detail-type": "AllTradesCompleted",
  "source": "alchemiser.test",
  "detail": {
    "event_id": "test-001",
    "correlation_id": "test-run-123",
    "run_id": "test123",
    "total_trades": 5,
    "succeeded_trades": 5,
    "failed_trades": 0,
    "aggregated_execution_data": {
      "execution_summary": {
        "equity": 100000.00,
        "cash": 25000.00,
        "top_positions": [
          {"symbol": "AAPL", "weight": 15.5}
        ]
      }
    }
  }
}
```

### Test Failure Email

Use same format but set:
```json
{
  "succeeded_trades": 2,
  "failed_trades": 3,
  "failed_symbols": ["TSLA", "NVDA"]
}
```

### Test Workflow Error

```json
{
  "version": "0",
  "detail-type": "WorkflowFailed",
  "source": "alchemiser.strategy",
  "detail": {
    "event_id": "wf-fail-001",
    "correlation_id": "test-wf-123",
    "workflow_type": "daily_run",
    "failure_step": "data_fetch",
    "failure_reason": "API rate limit exceeded",
    "error_details": {
      "exception_type": "AlpacaAPIError",
      "exception_message": "429 Too Many Requests"
    }
  }
}
```

---

## Monitoring & Troubleshooting

### CloudWatch Logs

All email sends are logged with structured data:

```json
{
  "event": "Email sent via SES",
  "extra": {
    "message_id": "0100019b797939ad-2025ee87-893a-4566-8a5b-679dddc788eb-000000",
    "to_addresses": ["notifications@rwxt.org"],
    "subject_preview": "Alchemiser Daily Run — SUCCESS — 2026-01-01 — dev — run_id=test-r",
    "routing_override": true,
    "stage": "dev"
  }
}
```

### CloudWatch Logs Insights Queries

**Find all failure emails sent today**:
```
fields @timestamp, extra.subject_preview, extra.message_id
| filter event = "Email sent via SES" and extra.subject_preview like /FAILURE/
| sort @timestamp desc
```

**Check deduplication suppression**:
```
fields @timestamp, event, extra.dedup_key, extra.time_since_last_minutes
| filter event = "Failure within quiet period - suppressing email"
| sort @timestamp desc
```

**Track recovery emails**:
```
fields @timestamp, event, extra.recovered_count
| filter event = "Sending RECOVERED notification"
| sort @timestamp desc
```

### SES Metrics (Console)

Monitor in **AWS Console → Amazon SES → Sending statistics**:
- **Sent**: Total emails sent
- **Deliveries**: Successfully delivered
- **Bounces**: Hard bounces (keep < 5%)
- **Complaints**: Spam complaints (keep < 0.1%)

### DynamoDB Dedup Table

**Scan for current failures**:
```bash
aws dynamodb scan \
  --table-name alchemiser-prod-notification-dedup \
  --filter-expression "#status = :failing" \
  --expression-attribute-names '{"#status":"status"}' \
  --expression-attribute-values '{":failing":{"S":"FAILING"}}'
```

**Check specific dedup key**:
```bash
aws dynamodb get-item \
  --table-name alchemiser-prod-notification-dedup \
  --key '{"PK":{"S":"Daily Run#prod#data_fetch#a3f8bc12"}}'
```

---

## Cost Estimates

### Amazon SES Pricing

- **First 62,000 emails/month**: $0.10 per 1,000 emails
- **Beyond 62,000 emails/month**: $0.12 per 1,000 emails

**Daily Run Notifications** (typical):
- 1 daily run × 1 email/day = 30 emails/month
- Cost: **< $0.01/month**

**With Failures + Retries** (conservative):
- 1 daily run + 5 failures/week + 2 recoveries/week = ~70 emails/month
- Cost: **< $0.01/month**

### DynamoDB Dedup Table

- **On-demand pricing**: $1.25 per million write requests
- **Storage**: $0.25 per GB-month
- **Typical usage**: < 100 writes/month, < 1 MB storage
- Cost: **< $0.01/month**

### Total Notification Cost

**~$0.50/month** (SES + DynamoDB + Lambda invocations)

---

## Future Enhancements

### Planned Email Types

1. **Data Lake Update SUCCESS** - When data pipeline completes
2. **Data Lake Update FAILURE** - When data fetch/processing fails
3. **Data Lake RECOVERED** - When data pipeline recovers after failures
4. **Performance Report Available** - Weekly/monthly performance summary
5. **Risk Limit Breached** - Position limits or drawdown thresholds exceeded

### Planned Features

1. **Email Preferences** - Per-user notification settings (subscribe/unsubscribe)
2. **Digest Mode** - Batch multiple notifications into daily digest
3. **Slack Integration** - Alternative to email for real-time alerts
4. **SMS Alerts** - Critical failures via SNS SMS
5. **Configuration Set Tracking** - Bounce/complaint handling and metrics
6. **Attachments** - Include CSV reports inline (not just presigned URLs)

### Planned Improvements

1. **Rich Metrics** - More complete context in emails:
   - Start/end times (currently "N/A")
   - Duration (currently 0)
   - Data freshness details (currently placeholder)
   - Gate statuses (DATA_FRESHNESS_GATE, RISK_GATE)

2. **Status Enums** - Formalize `SUCCESS_WITH_WARNINGS` status

3. **GSI for Recovery Check** - Replace DynamoDB scan with query via GSI on `status` attribute

4. **Retry Logic** - Exponential backoff for SES failures (currently relies on Lambda retries)

5. **Unit Tests** - Comprehensive test coverage for all notification types

---

## References

- [SES Setup Guide](./SES_SETUP.md)
- [SNS to SES Migration Summary](./SNS_TO_SES_MIGRATION.md)
- [Template Customization Guide](./TEMPLATE_CUSTOMIZATION.md)
- [AWS SES Developer Guide](https://docs.aws.amazon.com/ses/latest/dg/)
- [Email HTML Best Practices](https://www.campaignmonitor.com/css/)

---

**Last Updated**: 2026-01-01
**Status**: Current (SES migration complete, testing in dev)
