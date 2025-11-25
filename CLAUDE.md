# CLAUDE.md - AI Agent Instructions for Alchemiser

This file provides guidance for AI agents (Claude, Copilot, etc.) working with the Alchemiser quantitative trading system codebase.

## Quick Reference

```bash
# Common commands
source venv/bin/activate              # Activate virtualenv (use this, not poetry run)
python -m pytest tests/ -v            # Run all tests
python -m mypy the_alchemiser/        # Type check
make format                           # Format code
make type-check                       # Type check (via make)
make bump-patch                       # Version bump after changes (REQUIRED)
```

## Project Overview

Alchemiser is a **multi-strategy quantitative trading system** deployed on AWS Lambda. It uses an **event-driven architecture** where business modules communicate exclusively through events.

### Tech Stack
- **Language**: Python 3.12+
- **Framework**: AWS SAM (Serverless Application Model)
- **Broker**: Alpaca Markets API
- **Dependencies**: Poetry for package management
- **Testing**: pytest with Hypothesis for property tests
- **Typing**: mypy with strict mode

## Architecture

### Module Structure
```
the_alchemiser/
├── strategy_v2/      # Signal generation from market data
├── portfolio_v2/     # Converts signals to rebalance plans
├── execution_v2/     # Executes trades via Alpaca
├── orchestration/    # Workflow coordination
├── reporting/        # PDF report generation (separate Lambda)
├── notifications_v2/ # Email notifications
└── shared/           # DTOs, events, adapters, utilities
```

### Critical Architecture Rules
1. **Business modules only import from `shared/`** - no cross-module imports
2. **Event-driven communication** - modules publish/consume events via `EventBus`
3. **DTOs at boundaries** - never pass raw dicts between modules
4. **Idempotent handlers** - all event handlers must be safe under replay

### Event Flow
```
WorkflowStarted → SignalGenerated → RebalancePlanned → TradeExecuted → WorkflowCompleted
```

## Code Style & Guardrails

### Mandatory Rules

1. **Module Headers**: Every new module starts with:
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

## Testing

### Running Tests
```bash
# All tests
python -m pytest tests/ -v

# Specific module
python -m pytest tests/reporting/ -v

# With coverage
python -m pytest tests/ --cov=the_alchemiser
```

### Test Requirements
- Every public function/class needs at least one test
- Mirror source structure: `tests/test_<module>.py`
- Use Hypothesis for property-based tests on math/strategies
- Freeze time and seed RNG for determinism

## Version Management (MANDATORY)

**AI agents MUST bump version after every code change:**

```bash
# After making changes:
git add <your-changed-files>
make bump-patch   # Bug fixes, docs, tests
make bump-minor   # New features, new modules
make bump-major   # Breaking changes
```

The bump command commits both your changes AND the version bump together.

## Lambda Architecture

### Main Trading Lambda
- Handler: `the_alchemiser.lambda_handler.lambda_handler`
- Uses `ApplicationContainer` for dependency injection
- Heavy dependencies: pandas, numpy, alpaca-py

### Report Generator Lambda
- Handler: `the_alchemiser.reporting.lambda_handler.lambda_handler`
- **Avoids `ApplicationContainer`** to stay lightweight
- Creates `EventBus` directly via `_create_event_bus()`
- No pandas/numpy dependencies

**Important**: When modifying the report lambda, do NOT import `ApplicationContainer` - it pulls in heavy dependencies that break the Lambda.

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

## File Locations

| Purpose | Location |
|---------|----------|
| Main entry point | `the_alchemiser/lambda_handler.py` |
| Report Lambda | `the_alchemiser/reporting/lambda_handler.py` |
| Event schemas | `the_alchemiser/shared/events/schemas.py` |
| DTOs | `the_alchemiser/shared/schemas/` |
| DI Container | `the_alchemiser/shared/config/container.py` |
| Strategy engines | `the_alchemiser/strategy_v2/engines/` |
| Tests | `tests/` (mirrors source structure) |

## Pre-Commit Checklist

Before committing changes:
1. [ ] Run `make format` (or `python -m ruff format the_alchemiser/`)
2. [ ] Run `make type-check` (or `python -m mypy the_alchemiser/`)
3. [ ] Run relevant tests
4. [ ] Add module header if new file
5. [ ] Stage changes: `git add <files>`
6. [ ] Bump version: `make bump-patch` (or minor/major)

## Need More Context?

- **Architecture details**: See `README.md`
- **CI/CD workflow**: See `docs/DEPLOYMENT_WORKFLOW.md`
- **Ephemeral stacks**: See `docs/EPHEMERAL_DEPLOYMENTS.md`
- **Module READMEs**: Check `the_alchemiser/<module>/README.md`
