# Typing Architecture Rules for Alchemiser Quant

## Problem Statement

Mixed usage of data types across layers creates type confusion and protocol violations. The same logical data appears as:

- External SDK objects (`TradeAccount`, `Order`, `Position`)
- Generic data (`dict[str, Any]`)
- Various ad-hoc formats and `typing.Any` annotations

This creates maintenance issues, type safety problems, and violates the ANN401 lint rule.

## Core Architectural Rules

### 1. Layer-Specific Type Ownership

```text
┌─────────────────┬─────────────────────┬─────────────────────────┐
│ Layer           │ Type Used           │ Purpose                 │
├─────────────────┼─────────────────────┼─────────────────────────┤
│ External SDK    │ TradeAccount, Order │ Rich API objects        │
│ Execution Layer │ AccountInfoDTO      │ Domain representation   │
│ Strategy Layer  │ StrategySignalDTO   │ Strategy outputs        │
│ Portfolio Layer │ PortfolioStateDTO   │ Portfolio state         │
│ Shared/Protocol │ Domain DTOs         │ Cross-module interface  │
│ Orchestration   │ Domain DTOs         │ Business logic          │
│ Serialization   │ dict[str, Any]      │ JSON/transport only     │
└─────────────────┴─────────────────────┴─────────────────────────┘
```

### 2. Conversion Points (Pydantic v2 Compatible)

- **At SDK boundary**: External SDK → Domain DTO
- **At serialization**: Domain DTO → `dict` (via `model_dump()`)
- **At deserialization**: `dict` → Domain DTO (via `model_validate()`)
- **Never**: Raw `dict` flowing through business logic

### 3. Naming Conventions

```python
# Internal SDK access (private)
def _get_account_raw(self) -> TradeAccount:

# Primary business interface
def get_account(self) -> AccountInfoDTO | None:

# Serialization helpers (when needed)
def get_account_dict(self) -> dict[str, Any] | None:
    account = self.get_account()
    return account.model_dump() if account else None
```

## ANN401 Specific Rules

### When `Any` is Prohibited

```python
# ❌ NEVER - Business logic parameters
def process_signals(signals: Any) -> dict[str, float]:

# ❌ NEVER - Return types in domain methods
def get_account(self) -> Any:

# ❌ NEVER - DTO fields without constraints
class MyDTO(BaseModel):
    data: Any  # Should be specific type or union

# ❌ NEVER - Protocol method parameters
class Repository(Protocol):
    def save(self, data: Any) -> bool:
```

### When `Any` is Acceptable (with `# type: ignore[misc]`)

```python
# ✅ OK - External SDK objects (with comment)
@property
def trading_client(self) -> Any:  # type: ignore[misc] # Alpaca SDK TradingClient
    """External SDK client - type varies by broker."""
    return self._trading_client

# ✅ OK - Serialization metadata only
class MyDTO(BaseModel):
    metadata: dict[str, Any] | None = None  # JSON metadata only

# ✅ OK - Generic decorator internals (advanced)
P = ParamSpec('P')
def decorator(func: Callable[P, Any]) -> Callable[P, Any]:  # type: ignore[misc]
```

### Replacement Patterns

#### Pattern 1: Union Types for Flexible Input

```python
# ❌ Before
def convert_value(value: Any) -> Decimal:

# ✅ After
def convert_value(value: str | int | float | Decimal) -> Decimal:
```

#### Pattern 2: Generic TypeVars for Reusable Functions

```python
# ❌ Before
def cache_result(key: str, value: Any) -> Any:

# ✅ After
T = TypeVar('T')
def cache_result(key: str, value: T) -> T:
```

#### Pattern 3: Protocols for Interface Types

```python
# ❌ Before
def handle_result(result: Any) -> bool:

# ✅ After
class ProcessableResult(Protocol):
    def is_valid(self) -> bool: ...
    def get_data(self) -> dict[str, str]: ...

def handle_result(result: ProcessableResult) -> bool:
```

#### Pattern 4: Specific Dict Types

```python
# ❌ Before
def process_config(config: dict[str, Any]) -> None:

# ✅ After
def process_config(config: dict[str, str | int | bool]) -> None:
```

## Implementation Strategy (Pydantic v2)

### Phase 1: Create Domain DTOs

```python
# shared/dto/account_info_dto.py
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field
from typing import Literal

class AccountInfoDTO(BaseModel):
    """Account information DTO with Pydantic v2 configuration."""

    model_config = ConfigDict(
        strict=True,              # Strict validation
        frozen=True,              # Immutable after creation
        validate_assignment=True, # Validate on assignment
        str_strip_whitespace=True # Strip whitespace automatically
    )

    account_id: str = Field(..., min_length=1)
    equity: Decimal = Field(..., gt=0)
    cash: Decimal = Field(..., ge=0)
    buying_power: Decimal = Field(..., ge=0)
    portfolio_value: Decimal = Field(..., ge=0)
    day_trades_remaining: int = Field(..., ge=0)
    status: Literal["ACTIVE", "INACTIVE"]

    @classmethod
    def from_alpaca_account(cls, account: TradeAccount) -> "AccountInfoDTO":
        """Convert Alpaca account to domain DTO."""
        return cls(
            account_id=account.id,
            equity=Decimal(str(account.equity)),
            cash=Decimal(str(account.cash)),
            buying_power=Decimal(str(account.buying_power)),
            portfolio_value=Decimal(str(account.portfolio_value)),
            day_trades_remaining=account.daytrade_buying_power,
            status="ACTIVE" if account.status == "ACTIVE" else "INACTIVE"
        )
```

### Phase 2: Update Protocols

```python
# shared/protocols/repository.py
class AccountRepository(Protocol):
    def get_account(self) -> AccountInfoDTO | None:  # Not dict[str, Any]
        """Get account information as typed DTO."""
        ...
```

### Phase 3: Fix Implementation

```python
# shared/brokers/alpaca_manager.py
def get_account(self) -> AccountInfoDTO | None:
    """Get account information as domain DTO."""
    try:
        raw_account = self._trading_client.get_account()
        return AccountInfoDTO.from_alpaca_account(raw_account)
    except Exception:
        return None

# Legacy compatibility (if needed during migration)
def get_account_dict(self) -> dict[str, Any] | None:
    """Get account as dict for legacy compatibility."""
    account = self.get_account()
    return account.model_dump() if account else None
```

### Phase 4: Update Callers

```python
# orchestration/portfolio_orchestrator.py
account_info: AccountInfoDTO | None = alpaca_manager.get_account()
if account_info:
    buying_power = account_info.buying_power  # Type-safe access
    cash_available = account_info.cash       # Decimal precision
```

## Benefits of This Approach

1. **Type Safety**: MyPy catches misuse at compile time
2. **Clear Boundaries**: Each layer has well-defined types
3. **Maintainability**: Changes to external APIs isolated
4. **Documentation**: Types serve as living documentation
5. **Testability**: Easy to mock with concrete types

## Anti-Patterns to Avoid

### ❌ Generic Dicts in Business Logic

```python
def calculate_risk(account: dict[str, Any]) -> float:
    return float(account.get("buying_power", 0))  # Unsafe
```

### ❌ Mixed Return Types

```python
def get_account(self) -> TradeAccount | dict[str, Any]:  # Confusing
```

### ❌ Type Casts Everywhere

```python
account = cast(dict[str, Any], alpaca_manager.get_account())
```

### ✅ Proper Domain Types

```python
def calculate_risk(account: AccountInfoDTO) -> Decimal:
    return account.buying_power * Decimal("0.02")  # Type-safe
```

## Migration Strategy

### Step 1: Create DTOs First (Non-Breaking)

1. Create domain DTOs in `shared/dto/` following existing patterns
2. Add conversion methods (`from_alpaca_*`, `model_dump()`)
3. Do NOT change existing method signatures yet

### Step 2: Add Parallel Methods

```python
# Keep existing (temporarily)
def get_account(self) -> dict[str, Any] | None:
    """Legacy method - deprecated."""

# Add new typed method
def get_account_dto(self) -> AccountInfoDTO | None:
    """New typed method."""
    account_dict = self.get_account()
    return AccountInfoDTO.model_validate(account_dict) if account_dict else None
```

### Step 3: Migrate Callers Incrementally

```python
# Before
account = broker.get_account()
if account:
    cash = Decimal(str(account.get("cash", 0)))

# After
account = broker.get_account_dto()
if account:
    cash = account.cash  # Already Decimal
```

### Step 4: Update Protocols and Interfaces

Only after all implementations provide typed methods:

```python
class AccountRepository(Protocol):
    def get_account(self) -> AccountInfoDTO | None:  # Updated signature
        ...
```

### Step 5: Remove Legacy Methods

After all callers migrated, remove `dict[str, Any]` methods.

## Priority Order for ANN401 Fixes

### 🟢 Phase 1: Low-Hanging Fruit (Quick Wins)

- Remove unnecessary `| Any` from union types
- Fix CLI parameter types with specific imports
- Update notification templates with proper DTOs

### 🟡 Phase 2: SDK Integration Layer

- Fix Alpaca SDK wrapper methods with proper return types
- Update protocol interfaces to match implementations
- Create market data DTOs for quote/bar data

### 🟠 Phase 3: Business Logic Layer

- Fix signal orchestrator with proper strategy signal types
- Update strategy engines with specific result types
- Fix portfolio calculations with typed state

### 🔴 Phase 4: Infrastructure Layer

- Fix generic utility functions with TypeVar/ParamSpec
- Update error handlers with advanced generic typing
- Fix decorators with proper parameter specifications

This follows the modular architecture principles while providing clear type boundaries and systematic ANN401 resolution.
