# Email Notification Architecture Fix - Complete

**Date:** 2025-01-XX
**Version:** v2.27.2
**Status:** ✅ IMPLEMENTED

## Problem Summary

Email notifications were not being sent despite trading completing successfully and TradingNotificationRequested events being published by the orchestrator. The notification architecture was incomplete - events were published but had no routing or handler registration.

## Root Cause

Three architectural gaps prevented email notifications:

1. **Missing Event Mapping**: `TradingNotificationRequested` was not registered in `lambda_handler_eventbridge.py` event map
2. **Missing Handler Registration**: `NotificationService` was not registered in the handler map
3. **Missing EventBridge Rule**: No EventBridge Rule existed to route TradingNotificationRequested events from EventBridge to Lambda

## Implementation

### 1. Event Map Registration
**File:** `the_alchemiser/lambda_handler_eventbridge.py`

Added `TradingNotificationRequested` to event imports and event map:
```python
from the_alchemiser.shared.events import (
    # ... other imports
    TradingNotificationRequested,  # Added
)

event_map: dict[str, type[BaseEvent]] = {
    # ... other mappings
    "TradingNotificationRequested": TradingNotificationRequested,  # Added
}
```

**Purpose:** Allows EventBridge handler to deserialize incoming TradingNotificationRequested events.

### 2. Handler Registration
**File:** `the_alchemiser/lambda_handler_eventbridge.py`

Added `NotificationService` import and handler mapping:
```python
from the_alchemiser.notifications_v2.service import NotificationService  # Added

handler_map: dict[str, Callable[[], EventHandler]] = {
    # ... other handlers
    "TradingNotificationRequested": lambda: NotificationService(container),  # Added
}
```

**Purpose:** Routes TradingNotificationRequested events to NotificationService for email sending.

### 3. EventBridge Rule Creation
**File:** `template.yaml`

Added `TradingNotificationRule` and `TradingNotificationPermission`:
```yaml
TradingNotificationRule:
  Type: AWS::Events::Rule
  Properties:
    Name: !Sub "alchemiser-trading-notification-${Stage}"
    Description: Route TradingNotificationRequested events to notification handler
    EventBusName: !Ref AlchemiserEventBus
    State: ENABLED
    EventPattern:
      source:
        - alchemiser.orchestration
      detail-type:
        - TradingNotificationRequested
    Targets:
      - Arn: !GetAtt TradingSystemFunction.Arn
        Id: NotificationHandler
        RetryPolicy:
          MaximumRetryAttempts: 3
          MaximumEventAgeInSeconds: 3600
        DeadLetterConfig:
          Arn: !GetAtt EventDLQ.Arn

TradingNotificationPermission:
  Type: AWS::Lambda::Permission
  Properties:
    FunctionName: !Ref TradingSystemFunction
    Action: lambda:InvokeFunction
    Principal: events.amazonaws.com
    SourceArn: !GetAtt TradingNotificationRule.Arn
```

**Purpose:** Routes events from orchestration EventBridge source to Lambda, with retry policy and DLQ support.

## Email Notification Flow (Complete)

```
┌─────────────────────────────────────────────────────────────────────────┐
│ COMPLETE EMAIL NOTIFICATION ARCHITECTURE                                 │
└─────────────────────────────────────────────────────────────────────────┘

1. Trade Executes
   └─> TradeExecuted event published to EventBridge
       └─> TradeExecutedRule routes to Lambda
           └─> Orchestrator processes TradeExecuted
               └─> Orchestrator publishes TradingNotificationRequested
                   └─> EventBridge receives event
                       └─> TradingNotificationRule routes to Lambda ✅ NEW
                           └─> lambda_handler routes to lambda_handler_eventbridge
                               └─> Event map deserializes event ✅ NEW
                                   └─> Handler map routes to NotificationService ✅ NEW
                                       └─> NotificationService sends email via EmailClient
                                           └─> SMTP delivery to josh@rwxt.org
```

## Validation

### Type Check
```bash
poetry run mypy --config-file=pyproject.toml the_alchemiser/lambda_handler_eventbridge.py
# Result: Success - no issues found
```

### Template Validation
```bash
sam validate --lint
# Result: template.yaml is a valid SAM Template
```

### Import Formatting
```bash
poetry run ruff check --fix the_alchemiser/lambda_handler_eventbridge.py
# Result: Fixed 1 error (import ordering)
```

## Deployment Checklist

- [x] Code changes committed (v2.27.2)
- [x] Type checking passed
- [x] Template validation passed
- [x] Import formatting fixed
- [ ] Deploy to dev: `./scripts/deploy.sh dev`
- [ ] Test email notifications
- [ ] Monitor CloudWatch logs for email delivery confirmation
- [ ] Deploy to prod: `./scripts/deploy.sh prod`

## Testing Plan

### Local Testing (SAM)
```bash
# Create test event
cat > test-events/trading-notification.json << 'EOF'
{
  "version": "0",
  "id": "test-notification-1",
  "detail-type": "TradingNotificationRequested",
  "source": "alchemiser.orchestration",
  "account": "123456789012",
  "time": "2025-01-20T10:00:00Z",
  "region": "us-west-2",
  "resources": [],
  "detail": {
    "schema_version": "1.0",
    "event_id": "notif-123",
    "correlation_id": "corr-123",
    "causation_id": "cause-123",
    "timestamp": "2025-01-20T10:00:00+00:00",
    "notification_type": "trading_summary",
    "success": true,
    "message": "Test trading notification",
    "metadata": {"test": true}
  }
}
EOF

# Test notification routing
sam local invoke TradingSystemFunction -e test-events/trading-notification.json

# Expected: Email sent via SMTP (or neutral mode log if enabled)
```

### AWS Testing
```bash
# Deploy
./scripts/deploy.sh dev

# Trigger trading workflow (scheduled or manual)
# Wait for TradeExecuted event
# Check CloudWatch logs for email delivery

# Search logs
aws logs filter-pattern "Email sent successfully" \
  --log-group-name /aws/lambda/the-alchemiser-v2-lambda-dev \
  --start-time $(date -u -d '5 minutes ago' +%s)000

# Or check for failures
aws logs filter-pattern "Failed to send email" \
  --log-group-name /aws/lambda/the-alchemiser-v2-lambda-dev \
  --start-time $(date -u -d '5 minutes ago' +%s)000
```

## Configuration Verification

### Environment Variables (template.yaml)
```yaml
EMAIL__SMTP_SERVER: smtp.mail.me.com
EMAIL__SMTP_PORT: 587
EMAIL__FROM_EMAIL: josh@rwxt.org
EMAIL__TO_EMAIL: josh@rwxt.org
EMAIL__NEUTRAL_MODE: true  # Set to false for real emails
EMAIL__PASSWORD: !If [IsDev, !Ref EmailPassword, !Ref ProdEmailPassword]
```

### GitHub Secrets (Required)
- `EMAIL__PASSWORD`: SMTP password for josh@rwxt.org
- Located: Settings → Secrets and variables → Actions → Repository secrets

## Expected Behavior

### Email Sent After Every Trade
- **Success trades**: Email with summary, orders, P&L
- **Failed trades**: Email with error details, partial execution info
- **No trades**: Email confirming 0 orders executed

### Email Content
- Subject: "Alchemiser Trading Summary - [SUCCESS/FAILURE]"
- Body includes:
  - Workflow correlation ID
  - Strategy signals
  - Rebalance plan
  - Orders executed
  - Final portfolio state
  - Execution metrics
  - Timestamps

### Neutral Mode Behavior
- `EMAIL__NEUTRAL_MODE: true` → Logs email content, doesn't send via SMTP
- `EMAIL__NEUTRAL_MODE: false` → Sends real emails via smtp.mail.me.com

## Troubleshooting

### No Email Received
1. Check CloudWatch logs for "Email sent successfully" or errors
2. Verify `EMAIL__PASSWORD` secret exists in GitHub
3. Check `EMAIL__NEUTRAL_MODE` is `false` for real emails
4. Verify SMTP server accessible from Lambda (VPC/security groups)
5. Check spam folder

### EventBridge Rule Not Triggering
```bash
# Check rule is enabled
aws events describe-rule \
  --name alchemiser-trading-notification-dev \
  --event-bus-name alchemiser-dev

# Check rule targets
aws events list-targets-by-rule \
  --rule alchemiser-trading-notification-dev \
  --event-bus-name alchemiser-dev
```

### Handler Not Found
```bash
# Check Lambda logs for routing
aws logs filter-pattern "Routing TradingNotificationRequested" \
  --log-group-name /aws/lambda/the-alchemiser-v2-lambda-dev
```

## Related Documentation

- `docs/EMAIL_NOTIFICATION_TROUBLESHOOTING.md` - Comprehensive troubleshooting guide
- `docs/EVENTBRIDGE_QUICK_REFERENCE.md` - EventBridge architecture overview
- `the_alchemiser/notifications_v2/README.md` - NotificationService implementation
- `template.yaml` - EventBridge Rules and Lambda permissions

## Summary

Email notification architecture is now **complete and wired end-to-end**. The missing pieces (event mapping, handler registration, EventBridge Rule) have been implemented. After deployment, emails will be sent after every trade execution (success or failure).

**Status:** ✅ Ready for deployment and testing
