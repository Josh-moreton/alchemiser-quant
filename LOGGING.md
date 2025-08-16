# Logging Strategy

This project emits one JSON log event per line following a subset of the Elastic Common Schema (ECS).

## Core Fields

| Field | Description |
|------|-------------|
| `@timestamp` | ISO-8601 UTC timestamp with millisecond precision |
| `log.level` | Log level (TRACE/DEBUG/INFO/WARNING/ERROR/CRITICAL) |
| `message` | Concise human message |
| `event` | Short machine label for the event |
| `trace.id` / `span.id` | OpenTelemetry trace identifiers |
| `correlation_id` | Fallback UUIDv4 when no trace is active |
| `service` | Service name |
| `env` | Deployment environment (DEV/PROD) |
| `region` | Cloud region |
| `version` | Release SHA or version string |
| `process.pid` | Process identifier |
| `host.name` | Hostname |
| `runtime` | Python runtime version |
| `error.kind` | Exception class when logging errors |
| `error.message` | Exception message |
| `error.stack` | Stack trace |

Domain specific keys (e.g. `symbol`, `order_id`, `latency_ms`) may be added as needed.

## Usage

```python
from the_alchemiser.logging import configure_logging, get_logger, context

configure_logging(env="DEV", service="alchemiser", version="dev", region="local")
logger = get_logger(__name__)

with context(request_id="req-123"):
    logger.info("Placed order", event="order.placed", extra={"symbol": "AAPL", "order_id": "42"})
```

Logs are written to stdout for collection by the runtime (CloudWatch, etc.).

## Redaction

Values matching common secret patterns (AWS keys, bearer tokens, emails, IBAN, credit card numbers) are replaced with `***REDACTED***` before emission.

## OTEL Integration

If an OpenTelemetry span is active, `trace.id` and `span.id` fields are populated automatically. Otherwise a `correlation_id` is generated and bound to subsequent log lines via contextvars.

## Local Development

Set `LOG_LEVEL=DEBUG` to see debug messages. Production environments should default to `INFO`.
