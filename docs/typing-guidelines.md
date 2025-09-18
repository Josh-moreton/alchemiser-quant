# Typing Architecture Guidelines

This guide explains the typing architecture rules enforced across the Alchemiser codebase.

## Overview

The typing architecture ensures type safety, clear boundaries, and maintainability by enforcing:

1. **Layer-specific type ownership**
2. **Prohibition of unbounded `Any` usage**
3. **Strict naming conventions**
4. **Cross-module import boundaries**

## Layer-Specific Type Ownership

Each layer has its own type family to maintain clear boundaries:

### External SDK Layer
- **Types**: SDK objects (`TradeAccount`, `Order`, `Position`)
- **Usage**: Only at adapter boundaries
- **Example**: `alpaca.trading.Account`

### Execution Layer  
- **Types**: Domain DTOs (`AccountInfoDTO`, `ExecutionResultDTO`)
- **Usage**: Business logic within execution module
- **Example**: `AccountInfoDTO` with typed Decimal fields

### Strategy Layer
- **Types**: Strategy-specific DTOs (`StrategySignalDTO`)
- **Usage**: Signal generation and analysis
- **Example**: `StrategySignalDTO` with allocation weights

### Portfolio Layer
- **Types**: Portfolio DTOs (`PortfolioStateDTO`, `RebalancePlanDTO`)
- **Usage**: Portfolio state and rebalancing logic
- **Example**: `PortfolioStateDTO` with position tracking

### Shared/Protocol Layer
- **Types**: Cross-module DTOs and Protocols
- **Usage**: Authoritative interfaces between modules
- **Example**: Common DTOs in `shared/dto/`

### Serialization Layer
- **Types**: `dict[str, ...]` for transport only
- **Usage**: IO boundaries via Pydantic `model_dump()/model_validate()`
- **Example**: JSON serialization for API responses

## Conversion Points

Use Pydantic v2 methods for type conversions:

### SDK → Domain DTO (At adapters only)
```python
# ✅ Correct: Convert at adapter boundary
def get_account(self) -> AccountInfoDTO | None:
    raw_account = self._alpaca_client.get_account()  # SDK object
    return AccountInfoDTO.from_sdk(raw_account)  # Convert to DTO
```

### Domain DTO → dict (For transport/logging)
```python
# ✅ Correct: Serialize for transport
def send_portfolio_state(state: PortfolioStateDTO) -> None:
    payload = state.model_dump()  # DTO → dict
    send_to_api(payload)
```

### dict → Domain DTO (For input)
```python
# ✅ Correct: Deserialize from input
def handle_webhook(data: dict[str, Any]) -> None:
    signal = StrategySignalDTO.model_validate(data)  # dict → DTO
    process_signal(signal)
```

### ❌ Never: Raw dicts in business logic
```python
# ❌ Wrong: Raw dict in business logic
def calculate_allocation(portfolio: dict[str, Any]) -> dict[str, Any]:
    # This violates layer boundaries
    pass

# ✅ Correct: Use DTOs in business logic
def calculate_allocation(portfolio: PortfolioStateDTO) -> RebalancePlanDTO:
    # Type-safe business logic
    pass
```

## Naming Conventions

Follow these patterns for SDK adapters:

### Private SDK Accessors
```python
# ✅ Correct: Private method returns SDK object
def _get_account_raw(self) -> Any:  # type: ignore[misc]
    """SDK boundary - returns raw Alpaca account object."""
    return self._alpaca_client.get_account()
```

### Primary Business Interface
```python
# ✅ Correct: Public method returns typed DTO
def get_account(self) -> AccountInfoDTO | None:
    """Business interface - returns typed DTO."""
    raw_account = self._get_account_raw()
    return AccountInfoDTO.from_sdk(raw_account) if raw_account else None
```

### Optional Serialization Helpers
```python
# ✅ Correct: Optional dict method for legacy compatibility
def get_account_dict(self) -> dict[str, Any] | None:
    """Serialization helper - temporary during migration."""
    account = self.get_account()
    return account.model_dump() if account else None
```

## ANN401 Policy: No Unbounded Any

### Prohibited Usage

❌ **Business logic parameters/returns**
```python
# ❌ Wrong
def process_data(input: Any) -> Any:
    pass
```

❌ **DTO fields**
```python
# ❌ Wrong  
class UserDTO(BaseModel):
    data: Any  # Use specific types instead
```

❌ **Protocol methods**
```python
# ❌ Wrong
class DataProvider(Protocol):
    def get_data(self) -> Any:  # Use concrete return types
        pass
```

### Acceptable Usage (with justification)

✅ **External SDK boundaries**
```python
# ✅ Acceptable: SDK client at adapter boundary
def _get_raw_client(self) -> Any:  # type: ignore[misc]
    """External SDK client - raw Alpaca trading client."""
    return self._alpaca_trading_client
```

✅ **DTO metadata fields for JSON passthrough**
```python
# ✅ Acceptable: Metadata for serialization
class EventDTO(BaseModel):
    event_type: str
    payload: StrategySignalDTO
    metadata: dict[str, Any] | None = None  # JSON passthrough only
```

## Replacement Patterns

### Instead of `Any` for inputs
```python
# ❌ Wrong
def process(data: Any) -> None:
    pass

# ✅ Better: Concrete union
def process(data: str | int | bool) -> None:
    pass

# ✅ Best: Specific interface
def process(data: ProcessableDTO) -> None:
    pass
```

### Instead of `Any` for generics
```python
# ❌ Wrong
def handle_data(items: list[Any]) -> None:
    pass

# ✅ Better: TypeVar for reusability
T = TypeVar('T')
def handle_data(items: list[T]) -> None:
    pass

# ✅ Best: Specific types
def handle_data(items: list[StrategySignalDTO]) -> None:
    pass
```

### Instead of `dict[str, Any]`
```python
# ❌ Wrong: Generic dict in business logic
def analyze(config: dict[str, Any]) -> None:
    pass

# ✅ Better: Specific value types
def analyze(config: dict[str, str | int | bool]) -> None:
    pass

# ✅ Best: Typed configuration DTO
def analyze(config: AnalysisConfigDTO) -> None:
    pass
```

## Cross-Module Import Rules

### Allowed Imports
```python
# ✅ All modules can import from shared
from the_alchemiser.shared.dto import PortfolioStateDTO

# ✅ Orchestration can import from business modules  
from the_alchemiser.strategy_v2.core import SingleStrategyOrchestrator
from the_alchemiser.portfolio_v2.core import PortfolioService
```

### Forbidden Imports
```python
# ❌ Business modules cannot import from each other
from the_alchemiser.strategy_v2 import SomeClass  # In portfolio_v2/
from the_alchemiser.portfolio_v2 import SomeClass  # In execution_v2/

# ❌ Shared cannot import from business modules
from the_alchemiser.strategy_v2 import SomeClass  # In shared/

# ❌ Deep imports bypass module APIs
from the_alchemiser.strategy_v2.internal.calculations import sma
```

## Migration Strategy

### Phase 1: Remove `| Any` unions
```python
# Before
def process(data: str | Any) -> None:
    pass

# After  
def process(data: str | ProcessableData) -> None:
    pass
```

### Phase 2: Create DTOs for SDK integration
```python
# Before
def get_account(self) -> dict[str, Any]:
    return self._client.get_account()

# After
def get_account(self) -> AccountInfoDTO:
    raw_account = self._client.get_account()
    return AccountInfoDTO.from_sdk(raw_account)
```

### Phase 3: Update business logic to use DTOs
```python
# Before
def rebalance(portfolio: dict[str, Any]) -> dict[str, Any]:
    pass

# After
def rebalance(portfolio: PortfolioStateDTO) -> RebalancePlanDTO:
    pass
```

### Phase 4: Generic utilities with proper typing
```python
# Before
def decorator(func: Any) -> Any:
    pass

# After
F = TypeVar('F', bound=Callable[..., Any])
def decorator(func: F) -> F:
    pass
```

## Tools and Enforcement

### Run Typing Audit
```bash
# Run comprehensive audit
python tools/typing_audit.py

# Check CI enforcement  
python tools/check_fail_on_severity.py
```

### Makefile Integration
```bash
# Run all typing checks
make migration-check

# Individual checks
make type-check    # MyPy
make lint         # Ruff 
make import-check # Module boundaries
```

### CI/CD Integration
- GitHub Actions workflow: `.github/workflows/typing-audit.yml`
- Fails on HIGH/CRITICAL violations
- Uploads detailed reports as artifacts
- Comments on PRs with audit summary

## Common Patterns

### DTO Creation Template
```python
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field

class ExampleDTO(BaseModel):
    """Example DTO with proper configuration."""
    
    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )
    
    # Use concrete types, not Any
    name: str = Field(description="Entity name")
    amount: Decimal = Field(description="Financial amount")
    status: Literal["active", "inactive"] = Field(description="Status")
    
    # Metadata allowed for JSON passthrough only
    metadata: dict[str, str | int | bool] | None = Field(
        default=None,
        description="Optional metadata for serialization"
    )
```

### SDK Adapter Template
```python
class ExampleAdapter:
    """Template for SDK adapters with proper type boundaries."""
    
    def _get_data_raw(self) -> Any:  # type: ignore[misc]
        """Private: Returns raw SDK object."""
        return self._sdk_client.get_data()
    
    def get_data(self) -> ExampleDTO | None:
        """Public: Returns typed DTO."""
        raw_data = self._get_data_raw()
        return ExampleDTO.from_sdk(raw_data) if raw_data else None
    
    def get_data_dict(self) -> dict[str, Any] | None:
        """Legacy: Serialization helper (temporary)."""
        data = self.get_data()
        return data.model_dump() if data else None
```

## Troubleshooting

### Q: When can I use `Any`?
A: Only at SDK boundaries with `# type: ignore[misc]` comment and justification.

### Q: How do I replace `dict[str, Any]` in business logic?
A: Create a proper DTO with typed fields or use specific unions like `dict[str, str | int | bool]`.

### Q: Can orchestration modules import from business modules?
A: Yes, orchestration can import from strategy_v2, portfolio_v2, and execution_v2 to coordinate workflows.

### Q: What if I need flexible metadata fields?
A: Use `dict[str, str | int | bool] | None` for structured metadata, or `dict[str, Any] | None` only for JSON passthrough with clear documentation.

### Q: How do I handle legacy code during migration?
A: Keep `*_dict()` methods temporarily for backward compatibility, but prioritize migrating callers to use DTOs.

## Additional Resources

- [.github/copilot-instructions.md](.github/copilot-instructions.md) - Complete architecture rules
- [Pydantic v2 Documentation](https://docs.pydantic.dev/latest/) - DTO implementation guide
- [MyPy Documentation](https://mypy.readthedocs.io/) - Type checking reference