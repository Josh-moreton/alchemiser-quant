# CLAUDE.md - AI Agent Instructions for Alchemiser

This file provides guidance for AI agents (Claude, Copilot, etc.) working with the Alchemiser quantitative trading system codebase.

## Quick Reference

```bash
# Common commands
source venv/bin/activate              # Activate virtualenv (use this, not poetry run)
python -m mypy the_alchemiser/        # Type check
make format                           # Format code
make type-check                       # Type check (via make)
make bump-patch                       # Version bump after changes (REQUIRED)
```
Note: For packaging or migration documentation changes (like CodeUri/layer updates), use `make bump-patch` for docs-only PRs.

## Project Overview

Alchemiser is a **multi-strategy quantitative trading system** deployed as **multiple AWS Lambda microservices**. It uses an **event-driven architecture** where Lambdas communicate via EventBridge, SQS, and SNS.

Note: Each Lambda's source is packaged from `functions/<name>/` (SAM `CodeUri`) and shared runtime/business code is provided by `layers/shared/` (the `SharedCodeLayer`). Avoid copying `the_alchemiser/shared/` into each function; prefer the shared layer.

### Tech Stack
- **Language**: Python 3.12+
- **Framework**: AWS SAM (Serverless Application Model)
- **Broker**: Alpaca Markets API
- **Messaging**: EventBridge (events), SQS (execution queue), SNS (notifications)
- **Storage**: DynamoDB (trade ledger), S3 (performance reports)
- **Dependencies**: Poetry for package management
- **Typing**: mypy with strict mode

## Architecture

### Multi-Lambda Microservices

The system is deployed as **AWS Lambda functions** that communicate asynchronously. The Strategy layer supports **multi-node horizontal scaling**:

```
                              MULTI-NODE STRATEGY SCALING
                              ===========================
┌─────────────────────┐
│  Strategy           │──┬──▶ Strategy Worker 1 ──┐
│  Orchestrator       │  │                         │ PartialSignalGenerated
│  (Entry Point)      │  ├──▶ Strategy Worker 2 ──┼──────────────────────────┐
└─────────────────────┘  │                         │                          │
        │                └──▶ Strategy Worker N ──┘                          ▼
        │                                                            ┌─────────────────┐
        │ Creates session                                            │  Signal         │
        ▼                                                            │  Aggregator     │
┌─────────────────┐                                                  └─────────────────┘
│  DynamoDB       │◀──────────────────────────────────────────────────────────│
│  (Sessions)     │                                                           │
└─────────────────┘                                                           │
                                                                              │ SignalGenerated
                                                                              ▼
                        ┌─────────────────┐     EventBridge      ┌─────────────────┐
                        │  Rebalance     │◀─────────────────────│                 │
                        │  Planner       │                      └─────────────────┘
                        └─────────────────┘
                                │ RebalancePlanned
                                ▼
                        ┌─────────────────┐
                        │  SQS Queue      │
                        │  (with DLQ)     │
                        └─────────────────┘
                                │
                                ▼
                        ┌─────────────────┐
                        │  Execution      │
                        │  Lambda         │
                        └─────────────────┘
                                │
          TradeExecuted / WorkflowFailed
                                ▼
                        ┌─────────────────┐
                        │  Notifications  │
                        │  Lambda         │
                        └─────────────────┘
                                │
                                ▼ SNS
                        ┌─────────────────┐
                        │  Email          │
                        │  Subscription   │
                        └─────────────────┘
```

### Module Structure
```
the_alchemiser/
├── coordinator_v2/   # Lambda: Strategy Orchestrator (entry point, fans out)
├── strategy_v2/      # Lambda: Strategy Worker (executes single DSL file)
├── aggregator_v2/    # Lambda: Signal Aggregator (merges partial signals)
├── portfolio_v2/     # Lambda: Rebalance Planner (converts signals to rebalance plans)
├── execution_v2/     # Lambda: Executes trades via Alpaca (SQS-triggered)
├── notifications_v2/ # Lambda: Sends email notifications via SNS
└── shared/           # DTOs, events, adapters, utilities
```

### Critical Architecture Rules
1. **Business modules only import from `shared/`** - no cross-module imports
2. **Event-driven communication** - Lambdas publish/consume events via EventBridge
3. **SQS Standard queue for execution** - Per-trade parallel execution (up to 10 concurrent Lambdas)
4. **Two-phase ordering via enqueue timing** - SELLs enqueued first, BUYs stored until SELLs complete
5. **SNS for notifications** - Email notifications via SNS topic subscriptions
6. **DTOs at boundaries** - never pass raw dicts between modules
7. **Idempotent handlers** - all event handlers must be safe under replay

### Event Flow (Signal Generation)
```
[EventBridge Schedule] → Strategy Orchestrator
        ↓ (Async Lambda Invoke)
    Strategy Worker 1, 2, ... N (parallel)
        ↓ (PartialSignalGenerated via EventBridge)
    Signal Aggregator (merges when all complete)
        ↓ (SignalGenerated via EventBridge)
    Rebalance Planner Lambda
```

### Event Flow (Trade Execution)
```
Rebalance Planner Lambda
        ↓ (SELL trades to SQS Standard queue, BUYs stored in DynamoDB)
    Execution Lambdas (parallel - up to 10 concurrent)
        ↓ (Last SELL triggers BUY phase, enqueues BUY trades)
    Execution Lambdas (parallel - up to 10 concurrent)
        ↓ (TradeExecuted/WorkflowFailed via EventBridge)
    Notifications Lambda → SNS → Email
```

### AWS Resources (template.yaml)

| Resource | Type | Purpose |
|----------|------|---------|
| `StrategyOrchestratorFunction` | Lambda | Entry point, dispatches parallel strategy execution |
| `StrategyFunction` | Lambda | Worker, executes single DSL strategy file |
| `StrategyAggregatorFunction` | Lambda | Merges partial signals into consolidated portfolio |
| `RebalancePlannerFunction` | Lambda | Rebalance planning |
| `ExecutionFunction` | Lambda | Trade execution (SQS-triggered) |
| `NotificationsFunction` | Lambda | Email via SNS |
| `AlchemiserEventBus` | EventBridge | Event routing between Lambdas |
| `AggregationSessionsTable` | DynamoDB | Tracks multi-node aggregation sessions |
| `ExecutionQueue` | SQS | Reliable trade execution buffer |
| `ExecutionDLQ` | SQS | Dead letter queue for failed executions |
| `TradingNotificationsTopic` | SNS | Email notification delivery |
| `DLQAlertTopic` | SNS | DLQ monitoring alerts |
| `TradeLedgerTable` | DynamoDB | Trade history persistence |
| `StrategyAnalyticsFunction` | Lambda | Daily strategy metrics computation (S3 Parquet) |
| `StrategyReportsFunction` | Lambda | Quantstats HTML tearsheet generation |
| `PerformanceReportsBucket` | S3 | Strategy analytics (Parquet/JSON) and reports (HTML tearsheets) |

## Code Style & Guardrails

### Mandatory Rules

1. **No Emojis**: Never use emojis in code, comments, commit messages, or documentation.

2. **Module Headers**: Every new module starts with:
   ```python
   """Business Unit: <name> | Status: current."""
   ```

2. **No Float Equality**: Never use `==`/`!=` on floats
   ```python
   # ❌ Bad
   if price == 100.0:
   
   # ✅ Good
   from decimal import Decimal
   if price == Decimal("100.00"):
   
   # ✅ Good for ratios
   import math
   if math.isclose(ratio, 1.0, rel_tol=1e-9):
   ```

3. **Money Always Decimal**:
   ```python
   from decimal import Decimal
   price = Decimal("99.95")  # ✅
   price = 99.95             # ❌
   ```

4. **Event Traceability**: All events include `correlation_id` and `causation_id`

5. **No Secrets in Code**: Use environment variables, never hardcode

### Size Limits
- **Module**: ≤500 lines (split at >800)
- **Function**: ≤50 lines (aim for 10-30)
- **Parameters**: ≤5 (excluding `self`)
- **Cyclomatic complexity**: ≤10 per function

### Imports
```python
# Order: stdlib → third-party → local
from __future__ import annotations

import os
from datetime import UTC, datetime

import boto3
from pydantic import BaseModel

from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.events import EventBus
```

## Version Management (MANDATORY)

**AI agents MUST bump version after every code change:**

```bash
# After making changes:
git add <your-changed-files>
make bump-patch   # Bug fixes, docs, refactoring
make bump-minor   # New features, new modules
make bump-major   # Breaking changes
```

The bump command commits both your changes AND the version bump together.

## Lambda Handlers

Each microservice has its own Lambda handler:

| Lambda | Handler Path | Trigger | Publishes |
|--------|--------------|---------|-----------|
| Strategy Orchestrator | `the_alchemiser.coordinator_v2.lambda_handler` | EventBridge Schedule (3:30 PM ET) | Invokes Strategy Workers |
| Strategy Worker | `the_alchemiser.strategy_v2.lambda_handler` | Orchestrator (async) or Schedule (legacy) | `PartialSignalGenerated` or `SignalGenerated` |
| Signal Aggregator | `the_alchemiser.aggregator_v2.lambda_handler` | EventBridge (`PartialSignalGenerated`) | `SignalGenerated` |
| Rebalance Planner | `the_alchemiser.portfolio_v2.lambda_handler` | EventBridge (`SignalGenerated`) | `RebalancePlanned` |
| Execution | `the_alchemiser.execution_v2.lambda_handler` | SQS Queue | `TradeExecuted`, `WorkflowCompleted` |
| Notifications | `the_alchemiser.notifications_v2.lambda_handler` | EventBridge (`TradeExecuted`, `WorkflowFailed`) | SNS messages |

### Publishing to EventBridge
```python
from the_alchemiser.shared.events.eventbridge_publisher import publish_to_eventbridge

# Publish event to EventBridge (routes to other Lambdas)
publish_to_eventbridge(signal_generated_event)
```

### Publishing to SNS (Notifications)
```python
from the_alchemiser.shared.notifications.sns_publisher import publish_notification

# Send email via SNS topic
publish_notification(subject="Trade Executed", message="...")
```

## Common Patterns

### Creating an Event Handler
```python
from the_alchemiser.shared.events import BaseEvent, EventHandler

class MyHandler(EventHandler):
    def can_handle(self, event_type: str) -> bool:
        return event_type == "MyEventType"
    
    def handle_event(self, event: BaseEvent) -> None:
        # Idempotent logic here
        pass
```

### Publishing Events
```python
from the_alchemiser.shared.events import EventBus
from the_alchemiser.shared.events.schemas import MyEvent

event = MyEvent(
    event_id=generate_request_id(),
    correlation_id=correlation_id,
    causation_id=causation_id,
    timestamp=datetime.now(UTC),
    source_module="my_module",
    source_component="MyComponent",
    # ... event-specific fields
)
event_bus.publish(event)
```

### DTOs with Pydantic
```python
from pydantic import BaseModel, ConfigDict

class OrderResult(BaseModel):
    model_config = ConfigDict(strict=True, frozen=True)

    order_id: str
    symbol: str
    quantity: int
    price: Decimal
```

### Writing New Scripts

All scripts that import from `the_alchemiser.*` must use the import helper:

```python
#!/usr/bin/env python3
"""Business Unit: scripts | Status: current."""

from __future__ import annotations

import argparse
from pathlib import Path

# Setup imports BEFORE the_alchemiser imports
import _setup_imports  # noqa: F401

from the_alchemiser.shared.logging import get_logger

# Use PROJECT_ROOT if needed for .env or config file paths
project_root = _setup_imports.PROJECT_ROOT
```

For scripts that need function-specific imports (e.g., `strategy_v2`):

```python
import _setup_imports  # Shared layer

# Also add strategy function code
import sys
strategy_function_path = _setup_imports.PROJECT_ROOT / "functions" / "strategy_worker"
sys.path.insert(0, str(strategy_function_path))

from the_alchemiser.shared.logging import get_logger  # From layer
from the_alchemiser.strategy_v2.lambda_handler import lambda_handler  # From function
```

## Error Handling

```python
from the_alchemiser.shared.errors import AlchemiserError

# ✅ Good - catch narrow, re-raise typed
try:
    result = risky_operation()
except SpecificError as e:
    raise AlchemiserError(f"Operation failed: {e}") from e

# ❌ Bad - silent catch
try:
    result = risky_operation()
except:
    pass
```

## Deployment

### Deploy to Dev (Beta)
```bash
make deploy-dev
# or
make release-beta
```

### Deploy to Production
```bash
make deploy-prod
```

### Ephemeral (Feature Branch) Stacks
```bash
make deploy-ephemeral TTL_HOURS=24
make list-ephemeral
make destroy-ephemeral STACK=alchemiser-ephem-...
```

## Logging

### Environment-Aware Logging

The system uses different log formats based on the deployment environment:

| Environment | Format | Colors | Timestamp | Use Case |
|-------------|--------|--------|-----------|----------|
| **Prod Lambda** (APP__STAGE=prod) | JSON | No | No (CloudWatch adds) | CloudWatch Insights queries, log aggregation |
| **Dev Lambda** (APP__STAGE=dev) | Human-readable | No | No (CloudWatch adds) | Easier debugging in CloudWatch |

All Lambda handlers must initialize logging on cold start:
```python
from the_alchemiser.shared.logging import configure_application_logging, get_logger

# Initialize logging on cold start (must be before get_logger)
configure_application_logging()

logger = get_logger(__name__)
```

### Using the Logger

Use structured logging with context:
```python
from the_alchemiser.shared.logging import get_logger

logger = get_logger(__name__)

logger.info(
    "Order placed",
    order_id=order.id,
    symbol=order.symbol,
    correlation_id=correlation_id,
)
```

**Avoid**: `event=` as a kwarg (conflicts with structlog). Use `lambda_event=` instead.

### Environment Variables

- `APP__STAGE`: Set to `prod` or `dev` (controls JSON vs human-readable format)
- `LOG_LEVEL` or `LOGGING__LEVEL`: Set log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

## File Locations

| Purpose | Location |
|---------|----------|
| Strategy Orchestrator handler | `functions/strategy_orchestrator/lambda_handler.py` |
| Strategy Worker handler | `functions/strategy_worker/lambda_handler.py` |
| Strategy Analytics handler | `functions/strategy_analytics/lambda_handler.py` |
| Strategy Reports handler | `functions/strategy_reports/lambda_handler.py` |
| Execution Lambda handler | `functions/execution/lambda_handler.py` |
| Notifications Lambda handler | `functions/notifications/lambda_handler.py` |
| Event schemas | `layers/shared/the_alchemiser/shared/events/schemas.py` |
| EventBridge publisher | `layers/shared/the_alchemiser/shared/events/eventbridge_publisher.py` |
| SES email publisher | `layers/shared/the_alchemiser/shared/notifications/ses_publisher.py` |
| DTOs | `layers/shared/the_alchemiser/shared/schemas/` |
| DI Container | `layers/shared/the_alchemiser/shared/config/container.py` |
| Strategy engines | `functions/strategy_worker/engines/` |
| Infrastructure (SAM) | `template.yaml` |
| Script import helper | `scripts/_setup_imports.py` |

## Pre-Commit Checklist

Before committing changes:
1. [ ] Run `make format` (or `python -m ruff format the_alchemiser/`)
2. [ ] Run `make type-check` (or `python -m mypy the_alchemiser/`)
3. [ ] Add module header if new file
4. [ ] Stage changes: `git add <files>`
5. [ ] Bump version: `make bump-patch` (or minor/major)

**Note**: This repo does not use pytest or unit tests. Validate changes via type-checking and manual verification.

## Need More Context?

- **Architecture details**: See `README.md`
- **CI/CD workflow**: See `docs/DEPLOYMENT_WORKFLOW.md`
- **Ephemeral stacks**: See `docs/EPHEMERAL_DEPLOYMENTS.md`
- **Module READMEs**: Check `the_alchemiser/<module>/README.md`
