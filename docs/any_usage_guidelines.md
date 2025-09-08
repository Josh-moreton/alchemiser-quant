# Any Usage Guidelines

This document provides guidelines for acceptable usage of the `typing.Any` type in the Alchemiser codebase.

## Principles

1. **Type Safety First**: Prefer concrete types, protocols, or unions over `Any`
2. **Justify Dynamic Typing**: Every `Any` should have a clear rationale  
3. **External Boundary Pattern**: `Any` is acceptable at system boundaries with external libraries
4. **Temporary Bridge**: `Any` can be used as a temporary bridge during migration, with TODOs

## Acceptable Any Usage Categories

### Category A: External SDK Objects (Justified with `# noqa: ANN401`)

Use `Any` for objects from external SDKs where we don't control the type definitions:

```python
def process_alpaca_order(order: Any) -> OrderExecutionResultDTO:  # noqa: ANN401  # Alpaca SDK order object
    """Process order from Alpaca SDK."""
    ...

def __init__(self, trading_client: Any) -> None:  # noqa: ANN401  # External SDK object (TradingClient)
    """Initialize with external trading client."""
    ...
```

**Rationale**: External SDK objects have dynamic structures we don't control.

### Category B: Decorator Passthroughs (Justified with `# noqa: ANN401`)

Use `Any` in decorators that need to handle arbitrary function signatures:

```python
def error_handler(*args: Any, **kwargs: Any) -> Any:  # noqa: ANN401  # Decorator passthrough for any function signature
    """Generic error handling decorator."""
    ...

def translate_service_errors(default_return: Any = None) -> Callable:  # noqa: ANN401  # Flexible default return for any function type
    """Decorator with flexible return type."""
    ...
```

**Rationale**: Decorators need maximum flexibility to wrap any function signature.

### Category C: Dynamic Configuration Objects (Justified with `# noqa: ANN401`)

Use `Any` for configuration objects with unknown structure:

```python
def process_strategy_config(config: Any) -> StrategyConfig:  # noqa: ANN401  # Strategy signal payloads have dynamic schema
    """Process configuration from external source."""
    ...

def lambda_handler(event: dict, context: Any) -> dict:  # noqa: ANN401  # AWS Lambda context is external object
    """AWS Lambda handler."""
    ...
```

**Rationale**: External configuration formats may vary and are not under our control.

### Category D: Value Normalization Utilities (Justified with `# noqa: ANN401`)

Use `Any` for utilities that normalize diverse input types from external sources:

```python
def safe_decimal_conversion(value: Any) -> Decimal:  # noqa: ANN401  # Handles diverse numeric types from external sources
    """Convert various numeric types to Decimal."""
    ...

def normalize_timestamp(timestamp: Any) -> str:  # noqa: ANN401  # Handles diverse timestamp formats from external sources
    """Normalize timestamp from any format."""
    ...
```

**Rationale**: These utilities need to handle unpredictable input from external data sources.

## Unacceptable Any Usage

### ❌ Domain Objects

```python
# BAD
def process_order(order: Any) -> None:
    ...

# GOOD  
def process_order(order: Order) -> None:
    ...

# BETTER
def process_order(order: OrderLikeProtocol) -> None:
    ...
```

### ❌ Internal Function Returns

```python
# BAD
def calculate_portfolio_value() -> Any:
    return some_value

# GOOD
def calculate_portfolio_value() -> Money:
    return Money(value, "USD")
```

### ❌ Repository Interfaces (when we control the data)

```python
# BAD (unless justified)
def get_positions() -> Any:
    ...

# GOOD
def get_positions() -> list[Position]:
    ...

# ACCEPTABLE (for external data)
def get_account() -> dict[str, Any] | None:  # External broker account data structure
    ...
```

## Migration Strategy

When replacing `Any` with more specific types:

1. **Use Protocols** for objects accessed via attributes by multiple functions
2. **Use Union Types** when a function handles a few known types  
3. **Use TypedDict** for structured dictionaries with known keys
4. **Keep Any** with noqa justification for truly dynamic external boundaries

## Protocol Creation Guidelines

Create a Protocol when:
- Multiple functions access the same set of attributes from `Any` objects
- The objects come from different sources but share common attributes
- You want type safety without full dataclass conversion

```python
from typing import Protocol

@runtime_checkable
class OrderLikeProtocol(Protocol):
    @property
    def id(self) -> str | None: ...
    
    @property  
    def symbol(self) -> str: ...
    
    @property
    def qty(self) -> float | str | None: ...
```

## Required Documentation

Every `Any` usage must include:

1. **Type annotation with noqa comment**: `# noqa: ANN401  # Brief justification`
2. **Docstring explanation** in the function description
3. **Classification** in the inventory document

## Examples of Good Any Usage

```python
# External SDK boundary
def alpaca_order_to_dto(order: Any) -> OrderDTO:  # noqa: ANN401  # Alpaca SDK order object
    """Convert Alpaca order to our DTO."""
    ...

# Decorator passthrough  
def retry(*args: Any, **kwargs: Any) -> Any:  # noqa: ANN401  # Decorator passthrough for any function signature
    """Retry decorator for any function."""
    ...

# Value normalization
def normalize_price(value: Any) -> Decimal:  # noqa: ANN401  # Handles diverse numeric types from external sources
    """Normalize price value from various sources."""
    ...

# External configuration
def get_account_info() -> dict[str, Any] | None:  # External broker account data with dynamic structure
    """Get account from external broker API."""
    ...
```

## Enforcement

- Use `ruff` with ANN401 rule enabled
- Every `Any` without justified `# noqa: ANN401` comment will fail CI
- Regular audits to reduce unnecessary `Any` usage
- Protocols introduced when ≥2 functions access same attributes

## Migration Checklist

When reviewing Any usage:

- [ ] Is this an external SDK object? → Keep with noqa
- [ ] Is this a decorator passthrough? → Keep with noqa  
- [ ] Is this value normalization from external source? → Keep with noqa
- [ ] Can this be replaced with a concrete type? → Replace
- [ ] Are ≥2 functions accessing same attributes? → Create Protocol
- [ ] Is this truly dynamic configuration? → Keep with noqa and justification
- [ ] Does this need a TODO for future improvement? → Add TODO comment