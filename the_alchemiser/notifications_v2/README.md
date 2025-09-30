# Notifications V2 - Event-Driven Email Service

**Business Unit: notifications | Status: current**

## Overview

The `notifications_v2` module provides event-driven email notification services that can be deployed independently as a Lambda function. It consumes notification events from the event bus and sends appropriate emails using the existing email infrastructure.

## Architecture

```
┌─────────────────┐    Events    ┌──────────────────┐    SMTP    ┌─────────────┐
│  Error Handler  │─────────────▶│  Notifications   │───────────▶│   Email     │
│  Orchestrator   │              │  Service         │            │  Recipients │
│  Other Modules  │              │                  │            │             │
└─────────────────┘              └──────────────────┘            └─────────────┘
```

## Event Types

### ErrorNotificationRequested
Emitted when an error notification email should be sent.

**Fields:**
- `error_severity`: Error severity level (CRITICAL, HIGH, MEDIUM)
- `error_priority`: Error priority (URGENT, HIGH, MEDIUM)  
- `error_title`: Error title for subject line
- `error_report`: Detailed error report content
- `error_code`: Optional error code for categorization
- `recipient_override`: Optional recipient email override

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
- `recipient_override`: Optional recipient email override

### SystemNotificationRequested
Emitted when a general system notification should be sent.

**Fields:**
- `notification_type`: Type of notification (INFO, WARNING, ALERT)
- `subject`: Email subject line
- `html_content`: HTML email content
- `text_content`: Optional plain text content
- `recipient_override`: Optional recipient email override

## Usage

### As Part of Main System

The notification service is automatically registered with the event bus when the system starts:

```python
from the_alchemiser.notifications_v2 import register_notification_handlers
from the_alchemiser.shared.config.container import ApplicationContainer

container = ApplicationContainer()
register_notification_handlers(container)
```

### As Independent Lambda

The service can be deployed as an independent Lambda function:

```python
from the_alchemiser.notifications_v2 import NotificationService
from the_alchemiser.shared.config.container import ApplicationContainer

def lambda_handler(event, context):
    container = ApplicationContainer()
    service = NotificationService(container)
    service.register_handlers()
    
    # Process events from SQS, EventBridge, etc.
    for notification_event in event['Records']:
        service.handle_event(notification_event)
    
    return {"statusCode": 200}
```

## Integration Points

### Error Handler Integration

The error handler emits notification events instead of sending emails directly:

```python
from the_alchemiser.shared.errors.error_handler import send_error_notification_if_needed

# Event-driven (preferred)
event_bus = container.services.event_bus()
send_error_notification_if_needed(event_bus)

# Direct fallback (backward compatibility)
send_error_notification_if_needed()  # Falls back to direct email
```

### Orchestrator Integration

The trading orchestrator emits trading notification events:

```python
from the_alchemiser.shared.events.schemas import TradingNotificationRequested

trading_event = TradingNotificationRequested(
    correlation_id=correlation_id,
    causation_id=causation_id,
    # ... other fields
)
event_bus.publish(trading_event)
```

## Dependencies

### Internal Dependencies
- `shared.events`: For event base classes and schemas
- `shared.notifications`: For email templates and SMTP client
- `shared.logging`: For structured logging
- `shared.config`: For container and dependency injection

### External Dependencies
- Uses existing email infrastructure from `shared.notifications`
- Compatible with existing email templates and configuration
- Maintains backward compatibility with direct email sending

## Deployment

### As Separate Lambda

1. Package the `notifications_v2` module with its dependencies
2. Deploy as independent Lambda function
3. Configure event sources (SQS, EventBridge, etc.)
4. Set up email configuration environment variables

### With Main System

The module is automatically loaded when the main system starts and registers its handlers with the event bus.

## Configuration

Uses the same email configuration as the existing system:

- `EMAIL_SMTP_SERVER`: SMTP server hostname
- `EMAIL_SMTP_PORT`: SMTP port (default: 587)
- `EMAIL_FROM_EMAIL`: From email address
- `EMAIL_TO_EMAIL`: Default recipient email address
- Email password from AWS Secrets Manager or environment variables

## Error Handling

- **Graceful Degradation**: If event-driven notifications fail, falls back to direct email
- **Isolation**: Notification failures don't break the main trading workflow
- **Logging**: All notification attempts are logged with correlation IDs
- **Retries**: Inherits retry logic from underlying email infrastructure

## Testing and Validation

### Unit Tests
```bash
# Run notification module tests
poetry run pytest tests/notifications_v2/ -v

# Test with coverage
poetry run pytest tests/notifications_v2/ --cov=the_alchemiser.notifications_v2
```

### Integration Testing
```bash
# Run integration test to verify functionality
poetry run python /tmp/integration_test.py
```

The integration test verifies:
- Event processing capabilities
- Email template generation
- Independent deployment readiness
- Module boundary compliance

### Manual Testing
```python
# Test notification event handling
from the_alchemiser.notifications_v2 import NotificationService
from the_alchemiser.shared.config.container import ApplicationContainer
from the_alchemiser.shared.events.schemas import ErrorNotificationRequested

container = ApplicationContainer()
service = NotificationService(container)
service.register_handlers()

# Create and publish test event
event = ErrorNotificationRequested(
    correlation_id="test-123",
    causation_id="manual-test",
    error_severity="MEDIUM",
    error_priority="MEDIUM",
    error_title="Test Notification",
    error_report="This is a test notification email",
)

# Event bus will route to notification handler
container.services.event_bus().publish(event)
```

### Type Checking
```bash
# Verify type correctness
make type-check
```

## Performance

### Execution Characteristics
- **Async email sending**: Non-blocking SMTP operations
- **Event-driven**: Decoupled from main trading workflow
- **Independent scaling**: Can be deployed as separate Lambda for isolation
- **Graceful degradation**: Falls back to direct email if event bus unavailable

### Resource Usage
- **Memory**: O(1) per notification event
- **Network**: SMTP connection + email transmission
- **CPU**: Minimal (template rendering and SMTP I/O)

### Timing Considerations
- **Email delivery**: 1-5 seconds typical via SMTP
- **Event processing**: Near-instant event handling
- **Non-blocking**: Does not delay trading workflows
- **Retry logic**: Built into underlying email infrastructure

## Future Enhancements

1. **Multiple Recipients**: Support for different recipient lists per notification type
2. **Template Customization**: Per-event custom email templates
3. **Delivery Tracking**: Email delivery status tracking
4. **Rate Limiting**: Built-in rate limiting for email sending
5. **Webhook Support**: Alternative notification channels (Slack, Discord, etc.)

## Module Boundaries

✅ **Follows Architecture Rules:**
- Only imports from `shared/` modules
- No cross-business-module dependencies
- Can be deployed independently
- Maintains proper module isolation
- Event-driven communication only