# Notifications V2 - Event-Driven SNS Notification Service

**Business Unit: notifications | Status: current**

## Overview

The `notifications_v2` module provides event-driven notification services deployed as an independent Lambda function. It consumes notification events from EventBridge and sends notifications via AWS SNS.

## Architecture

```
┌─────────────────┐    EventBridge    ┌──────────────────┐     SNS      ┌─────────────┐
│  Error Handler  │──────────────────▶│  Notifications   │─────────────▶│   Email     │
│  Orchestrator   │                   │  Lambda          │              │  Recipients │
│  Other Lambdas  │                   │                  │              │             │
└─────────────────┘                   └──────────────────┘              └─────────────┘
```

## Event Types

### ErrorNotificationRequested
Emitted when an error notification should be sent.

**Fields:**
- `error_severity`: Error severity level (CRITICAL, HIGH, MEDIUM)
- `error_priority`: Error priority (URGENT, HIGH, MEDIUM)  
- `error_title`: Error title for subject line
- `error_report`: Detailed error report content
- `error_code`: Optional error code for categorization

### TradingNotificationRequested
Emitted when a trading completion notification should be sent.

**Fields:**
- `trading_success`: Whether trading was successful
- `trading_mode`: Trading mode (LIVE, PAPER)
- `orders_placed`: Number of orders placed
- `orders_succeeded`: Number of orders that succeeded
- `total_trade_value`: Total value of trades executed
- `execution_data`: Detailed execution data
- `error_message`: Error message if trading failed
- `error_code`: Optional error code

### WorkflowFailed
Emitted when any Lambda in the workflow fails.

**Fields:**
- `error_message`: Error description
- `error_code`: Optional error code
- `source_lambda`: Lambda that failed
- `failed_at`: Failure timestamp

## Usage

### As Independent Lambda

The service is deployed as an independent Lambda function triggered by EventBridge:

```python
from the_alchemiser.notifications_v2 import NotificationService

def lambda_handler(event, context):
    service = NotificationService()
    return service.handle_event(event, context)
```

## Dependencies

### Internal Dependencies
- `shared.notifications.sns_publisher`: For SNS publishing
- `shared.logging`: For structured logging

### External Dependencies
- AWS SNS for notification delivery
- AWS EventBridge for event routing

## Deployment

Deployed via SAM template as part of the multi-Lambda architecture:

```yaml
NotificationsFunction:
  Type: AWS::Serverless::Function
  Properties:
    Handler: the_alchemiser.notifications_v2.lambda_handler.handler
    Runtime: python3.12
    Events:
      WorkflowFailed:
        Type: EventBridgeRule
        Properties:
          EventBusName: !Ref TradingEventBus
          Pattern:
            detail-type:
              - WorkflowFailed
      ErrorNotification:
        Type: EventBridgeRule
        Properties:
          EventBusName: !Ref TradingEventBus
          Pattern:
            detail-type:
              - ErrorNotificationRequested
```

## Configuration

Environment variables:
- `SNS_NOTIFICATION_TOPIC_ARN`: ARN of the SNS topic for notifications

## Error Handling

- **Isolation**: Notification failures don't break the main trading workflow
- **Logging**: All notification attempts are logged with correlation IDs
- **Retries**: EventBridge provides retry logic for failed deliveries
- **DLQ**: Failed notifications route to Dead Letter Queue

## Testing

### Unit Tests
```bash
# Run notification module tests
poetry run pytest tests/notifications_v2/ -v

# Test with coverage
poetry run pytest tests/notifications_v2/ --cov=the_alchemiser.notifications_v2
```

### Type Checking
```bash
# Verify type correctness
make type-check
```

## Module Boundaries

✅ **Follows Architecture Rules:**
- Only imports from `shared/` modules
- No cross-business-module dependencies
- Deployed independently as Lambda
- Maintains proper module isolation
- Event-driven communication only via EventBridge
