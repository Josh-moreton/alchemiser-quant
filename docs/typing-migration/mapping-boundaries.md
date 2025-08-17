# Typed Domain V2: Mapping Boundaries Documentation

## Overview

This document provides comprehensive guidance for implementing the anti-corruption layer pattern in The Alchemiser's typed domain migration. It covers the three critical mapping boundaries that maintain domain purity while enabling integration with external systems.

## Architecture Pattern

The Typed Domain V2 system follows the **anti-corruption layer** pattern with three distinct boundaries:

```
External Systems ↔ [DTO Mapping] ↔ Domain Objects ↔ [Infra Mapping] ↔ Infrastructure
```

### Three Mapping Boundaries

1. **DTO ↔ Domain**: External API responses/requests mapped to pure domain objects
2. **Domain ↔ Infrastructure**: Domain objects adapted for persistence/caching  
3. **Cross-boundary Translation**: Legacy data structures converted to typed domain

## Boundary 1: DTO ↔ Domain Mapping

**Location**: `the_alchemiser/application/mapping/`

**Purpose**: Convert external API data (Alpaca, AWS) into pure domain objects while maintaining domain purity.

### Key Principles

- **Domain Purity**: No framework imports (no Pydantic, requests, logging) in domain layer
- **Decimal Normalization**: All financial values use `Decimal` for precision
- **Immutable Value Objects**: Use `@dataclass(frozen=True)` for value objects
- **Explicit Mapping**: Never rely on implicit conversions or duck typing

### Example: Order Mapping

```python
# the_alchemiser/application/mapping/order_mapping.py
from decimal import Decimal
from the_alchemiser.domain.trading.entities.order import Order
from the_alchemiser.domain.shared_kernel.value_objects.money import Money

def alpaca_order_to_domain(order: Any) -> Order:
    """Convert Alpaca order object/dict to domain Order entity."""
    
    # Handle both dict and object attributes
    def get_attr(name: str, default: Any = None) -> Any:
        if isinstance(order, dict):
            return order.get(name, default)
        return getattr(order, name, default)
    
    # Extract and normalize values
    raw_id = get_attr("id") or get_attr("order_id")
    symbol_raw = get_attr("symbol") or "UNKNOWN"
    qty_raw = get_attr("qty") or get_attr("quantity") or 0
    
    # Map primitives to domain value objects
    order_id = OrderId(str(raw_id))
    symbol = Symbol(symbol_raw)
    quantity = Quantity(_coerce_decimal(qty_raw))
    status = _map_status(get_attr("status"))
    
    # Handle optional limit price with Money value object
    limit_price = None
    if raw_limit := get_attr("limit_price"):
        limit_price = Money(_coerce_decimal(raw_limit), "USD")
    
    return Order(
        id=order_id,
        symbol=symbol,
        quantity=quantity,
        status=status,
        order_type=get_attr("order_type", "market"),
        limit_price=limit_price,
    )

def _coerce_decimal(value: Any) -> Decimal:
    """Safely convert any numeric value to Decimal."""
    try:
        if value is None:
            return Decimal("0")
        return Decimal(str(value))
    except Exception:
        return Decimal("0")
```

### Decimal Normalization Rules

**Financial Values**: Always use `Decimal` for money, quantities, percentages, and prices:

```python
# ✅ Correct - using Decimal
portfolio_value = Decimal("100000.00")
allocation_pct = Decimal("0.25")  # 25%
price = Money(Decimal("150.45"), "USD")

# ❌ Incorrect - using float
portfolio_value = 100000.0  # Precision loss risk
allocation_pct = 0.25       # IEEE-754 rounding errors
```

**Normalization Function**:
```python
def to_money_usd(value: str | float | int | Decimal | None) -> Money | None:
    """Convert various numeric types to Money with USD currency."""
    if value is None:
        return None
    try:
        decimal_value = Decimal(str(value))
        return Money(decimal_value, "USD")
    except Exception:
        return None
```

## Boundary 2: Domain ↔ Infrastructure Mapping  

**Location**: `the_alchemiser/infrastructure/` (adapters)

**Purpose**: Adapt domain objects for external persistence, caching, and API calls.

### Example: Domain to Infrastructure

```python
# the_alchemiser/infrastructure/alpaca_adapter.py
def domain_order_to_alpaca_request(order: Order) -> dict[str, Any]:
    """Convert domain Order to Alpaca API request format."""
    request = {
        "symbol": order.symbol.value,
        "qty": str(order.quantity.value),  # Alpaca expects string
        "side": "buy" if order.quantity.value > 0 else "sell",
        "type": order.order_type.lower(),
    }
    
    if order.limit_price:
        request["limit_price"] = str(order.limit_price.amount)
    
    return request
```

### Infrastructure Rules

- **Keep domain objects pure**: No infrastructure concerns leak into domain
- **Explicit serialization**: Always specify how domain objects convert to external formats
- **Error boundaries**: Infrastructure failures don't propagate domain exceptions

## Boundary 3: Cross-boundary Translation

**Location**: `the_alchemiser/application/mapping/`

**Purpose**: Bridge between legacy untyped systems and new typed domain.

### Legacy Signal Mapping Example

```python
# the_alchemiser/application/mapping/strategy_signal_mapping.py
def legacy_signal_to_typed(legacy: dict[str, Any]) -> StrategySignal:
    """Convert legacy strategy signal dict to typed StrategySignal."""
    
    # Handle complex symbol types (dict for portfolio)
    raw_symbol = legacy.get("symbol")
    if isinstance(raw_symbol, dict):
        symbol = "PORTFOLIO"
    else:
        symbol = str(raw_symbol) if raw_symbol is not None else "N/A"
    
    # Normalize action strings
    action: ActionLiteral = _normalize_action(legacy.get("action"))
    
    # Support both legacy 'reason' and typed 'reasoning'
    reasoning = str(legacy.get("reason", legacy.get("reasoning", "")))
    
    return StrategySignal(
        symbol=symbol,
        action=action,
        confidence=float(legacy.get("confidence", 0.0) or 0.0),
        reasoning=reasoning,
        allocation_percentage=float(legacy.get("allocation_percentage", 0.0) or 0.0),
    )
```

## Domain Purity Rules

### What's Allowed in Domain Layer

```python
# ✅ Allowed imports
from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime, UTC
from typing import Protocol

# ✅ Standard library only
from abc import ABC, abstractmethod
from enum import Enum
```

### What's Prohibited in Domain Layer

```python
# ❌ Prohibited - Framework imports
from pydantic import BaseModel
import requests
import logging
from sqlalchemy import Column

# ❌ Prohibited - Infrastructure concerns  
import boto3
from alpaca_trade_api import REST
```

### Value Object Pattern

```python
@dataclass(frozen=True)
class Symbol:
    """Stock symbol value object."""
    value: str
    
    def __post_init__(self) -> None:
        if not self.value or len(self.value) > 10:
            raise ValueError("Invalid symbol")
```

### Entity Pattern  

```python
@dataclass
class Order:
    """Order entity with business behavior."""
    id: OrderId
    symbol: Symbol
    # ... other fields
    
    def cancel(self) -> None:
        """Business logic for cancelling orders."""
        if self.status == OrderStatus.FILLED:
            raise ValueError("Cannot cancel filled order")
        self.status = OrderStatus.CANCELLED
```

## No Legacy Fallback Policy

**Critical Rule**: Never add conditional fallbacks to legacy modules in production code.

```python
# ❌ Prohibited pattern
try:
    positions = modern_service.get_positions()
except Exception:
    positions = legacy_provider.get_positions()  # NO!

# ✅ Correct pattern  
try:
    positions = modern_service.get_positions()
except Exception as e:
    raise PositionServiceError(f"Failed to get positions: {e}") from e
```

**Testing Exception**: Legacy paths may be used in tests for parity verification only.

## Mapping Module Structure

### Current Modules

1. **`order_mapping.py`** - Alpaca orders ↔ Domain Order entities
2. **`account_mapping.py`** - Account data ↔ Typed AccountSummary  
3. **`position_mapping.py`** - Position data ↔ PositionSummary
4. **`strategy_signal_mapping.py`** - Legacy signals ↔ Typed StrategySignal

### Adding New Mappers

When creating new mapping modules:

1. **Place in `application/mapping/`** - Keep separate from domain and infrastructure
2. **Follow naming convention** - `{domain}_mapping.py`
3. **Pure functions only** - No state, no side effects
4. **Comprehensive error handling** - Never fail silently
5. **Full test coverage** - Test all edge cases and conversions

### Example Template

```python
"""Mapping utilities between {External} data and domain {Entity}.

This module is part of the anti-corruption layer. It converts external
{External} representations into pure domain models so the rest of the 
application can operate with strong types.
"""

from __future__ import annotations
from decimal import Decimal
from typing import Any

from the_alchemiser.domain.{domain}.entities.{entity} import {Entity}

def {external}_to_domain(data: Any) -> {Entity}:
    """Convert {External} data to domain {Entity}."""
    # Implementation
    pass

def domain_to_{external}(entity: {Entity}) -> dict[str, Any]:
    """Convert domain {Entity} to {External} format."""
    # Implementation  
    pass

def _safe_decimal(value: Any) -> Decimal:
    """Helper for safe Decimal conversion."""
    try:
        return Decimal(str(value or "0"))
    except Exception:
        return Decimal("0")
```

## Testing Patterns

### Mapper Testing

```python
def test_alpaca_order_to_domain():
    """Test order mapping with realistic data."""
    alpaca_data = {
        "id": "12345",
        "symbol": "AAPL", 
        "qty": "10",
        "status": "filled",
        "limit_price": "150.50"
    }
    
    domain_order = alpaca_order_to_domain(alpaca_data)
    
    assert domain_order.id.value == "12345"
    assert domain_order.symbol.value == "AAPL"
    assert domain_order.quantity.value == Decimal("10")
    assert domain_order.status == OrderStatus.FILLED
    assert domain_order.limit_price.amount == Decimal("150.50")
```

### Parity Testing (Feature Flag)

```python
def test_typed_vs_legacy_parity(mock_alpaca_client):
    """Ensure typed and legacy paths produce equivalent results."""
    
    with environment_var("TYPES_V2_ENABLED", "1"):
        typed_result = service.get_positions()
    
    with environment_var("TYPES_V2_ENABLED", "0"): 
        legacy_result = service.get_positions()
    
    # Compare essential fields
    assert typed_result.total_value == legacy_result["total_value"]
    assert len(typed_result.positions) == len(legacy_result["positions"])
```

## Migration Checklist

When implementing new mapping boundaries:

- [ ] **Create mapper module** in `application/mapping/`
- [ ] **Define domain entities/value objects** with proper types
- [ ] **Implement bi-directional mapping** (to/from domain)
- [ ] **Add Decimal normalization** for all financial values  
- [ ] **Write comprehensive tests** including edge cases
- [ ] **Document mapping rules** and any special handling
- [ ] **Ensure domain purity** - no framework imports
- [ ] **Add feature flag support** if incrementally rolling out
- [ ] **Remove legacy fallbacks** once typed path is stable

## Troubleshooting

### Common Issues

**Decimal conversion errors**:
```python
# Problem: float precision loss
price = float(api_response["price"])  # 150.5000000001

# Solution: always use Decimal
price = Decimal(str(api_response["price"]))  # 150.50
```

**Value object validation failures**:
```python
# Problem: invalid data crashes system
symbol = Symbol(raw_data.get("symbol"))  # Might be None

# Solution: defensive programming
symbol_value = raw_data.get("symbol", "UNKNOWN")
symbol = Symbol(symbol_value) if symbol_value else Symbol("UNKNOWN")
```

**Domain purity violations**:
```python
# Problem: framework leak into domain
from pydantic import BaseModel  # In domain module

# Solution: keep domain pure
from dataclasses import dataclass  # Use standard library
```

## References

- [Architecture Overview](./overview.md) - Overall typed domain migration strategy
- [Typed Domain Contracts](./contracts.md) - Canonical type definitions  
- [Phase Plan](./phase-plan.md) - Migration roadmap and timeline
- [Main README](../../README.md#typed-domain-system-v2) - Quick reference and setup