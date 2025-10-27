# Architecture Context for portfolio_v2/__init__.py

## Module Role in Event-Driven Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     ORCHESTRATION LAYER                         │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  EventDrivenOrchestrator                                │  │
│  │  - Initializes application container                    │  │
│  │  - Calls register_portfolio_handlers(container)         │  │
│  │  - Wires all event handlers to EventBus                 │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ calls
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              PORTFOLIO_V2 MODULE (__init__.py)                  │
│                                                                 │
│  Public API (Event-Driven):                                    │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ register_portfolio_handlers(container: Container)        │  │
│  │   1. Gets EventBus from container                        │  │
│  │   2. Creates PortfolioAnalysisHandler(container)         │  │
│  │   3. Subscribes handler to "SignalGenerated" events      │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  Legacy API (Deprecated, via __getattr__):                     │
│  - PortfolioServiceV2                                          │
│  - RebalancePlanCalculator                                     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ creates & registers
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                  PORTFOLIO ANALYSIS HANDLER                     │
│                                                                 │
│  Subscribes to: SignalGenerated (v1.0)                         │
│  Publishes: RebalancePlanned (v1.0), WorkflowFailed (v1.0)    │
│                                                                 │
│  Workflow:                                                      │
│  1. Receive SignalGenerated event                              │
│  2. Extract strategy allocations                               │
│  3. Get current portfolio state (via Alpaca)                   │
│  4. Calculate rebalance plan                                   │
│  5. Emit RebalancePlanned event                                │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ uses
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    CORE SERVICES (Internal)                     │
│                                                                 │
│  - PortfolioServiceV2: Portfolio management service            │
│  - RebalancePlanCalculator: Rebalance calculation logic        │
│  - StateReader: Read portfolio state                           │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ depends on
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                         SHARED LAYER                            │
│                                                                 │
│  Events:                  Schemas:              Infrastructure: │
│  - EventBus               - RebalancePlan       - AlpacaManager │
│  - SignalGenerated        - AllocationComp      - Container     │
│  - RebalancePlanned       - StrategyAlloc       - Logging       │
│  - WorkflowFailed         - PortfolioState                      │
└─────────────────────────────────────────────────────────────────┘
```

## Event Flow

```
Strategy Module                Portfolio Module              Execution Module
(strategy_v2)                 (portfolio_v2)                (execution_v2)
      │                             │                             │
      │ 1. Generates signals        │                             │
      ├────────────────────────────►│                             │
      │  SignalGenerated (v1.0)     │                             │
      │                             │                             │
      │                             │ 2. Analyzes portfolio       │
      │                             │    Creates rebalance plan   │
      │                             │                             │
      │                             ├────────────────────────────►│
      │                             │  RebalancePlanned (v1.0)    │
      │                             │                             │
      │                             │                             │ 3. Executes trades
      │                             │                             │
      │◄────────────────────────────┴─────────────────────────────│
                       TradeExecuted (v1.0)
```

## Module Isolation Rules

### Import Linter Contracts (All Passing ✅)

1. **Shared module isolation**: ✅
   - `shared/` cannot import from business modules
   
2. **Portfolio module isolation**: ✅
   - `portfolio_v2/` cannot import from `strategy_v2/`, `execution_v2/`, or `orchestration/`
   
3. **Event-driven layered architecture**: ✅
   ```
   Layer 3 (Top):    orchestration/
   Layer 2 (Middle): strategy_v2/ | portfolio_v2/ | execution_v2/
   Layer 1 (Bottom): shared/
   ```
   - Each layer can only import from layers below

## Dependency Injection Pattern

```python
# Container provides dependencies
container = ApplicationContainer()

# Module registers handlers
register_portfolio_handlers(container)

# Handler gets dependencies from container
class PortfolioAnalysisHandler:
    def __init__(self, container: ApplicationContainer):
        self.event_bus = container.services.event_bus()
        self.alpaca_manager = container.infrastructure.alpaca_manager()
        self.logger = get_logger(__name__)
```

## Key Design Decisions

### 1. Lazy Import Pattern
**Why:** Prevents circular imports and reduces startup time
```python
def __getattr__(name: str) -> object:
    if name == "PortfolioServiceV2":
        from .core.portfolio_service import PortfolioServiceV2
        return PortfolioServiceV2
    # ...
```

### 2. TYPE_CHECKING Guard
**Why:** ApplicationContainer only needed for type hints, not runtime
```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from the_alchemiser.shared.config.container import ApplicationContainer
```

### 3. Handler Registration Function
**Why:** Clean integration point for orchestration layer
```python
def register_portfolio_handlers(container: ApplicationContainer) -> None:
    """Primary API for event-driven architecture."""
    # Create and register handlers
```

### 4. Idempotent Registration
**Why:** Safe for multiple calls, EventBus manages lifecycle
- Multiple calls create new handler instances
- No global state mutations
- EventBus handles subscription management

## Testing Strategy

### Unit Tests (12 tests in test_module_imports.py)
- Import validation (direct and lazy)
- `__getattr__` behavior (valid and invalid)
- `__all__` export list correctness
- Event handler registration
- Handler capability verification
- Idempotency of multiple registrations

### Integration Tests (test_portfolio_analysis_handler.py)
- End-to-end event flow
- Handler event processing
- Error path validation
- State management

## Migration Status

### Current State
- ✅ Event-driven architecture fully implemented
- ✅ Primary API: `register_portfolio_handlers`
- ⚠️ Legacy APIs maintained for backward compatibility

### Deprecation Path
1. ✅ Event-driven API is primary (completed)
2. 🔄 Monitor usage of legacy APIs (ongoing)
3. ⏳ Add deprecation warnings (future)
4. ⏳ Remove legacy APIs when usage drops (future)

## Performance Characteristics

- **Startup Time**: Minimal (lazy imports)
- **Memory Footprint**: Low (container-based DI)
- **Handler Processing**: O(1) subscription lookup
- **Event Emission**: Async via EventBus

## Security Considerations

- ✅ No secrets in code
- ✅ Container-based DI prevents injection attacks
- ✅ Type system enforces input validation
- ✅ Proper error messages (no sensitive data leakage)
- ✅ All external imports guarded appropriately

---

**Document Version:** 1.0  
**Last Updated:** 2025-10-11  
**Related Files:**
- `the_alchemiser/portfolio_v2/__init__.py` (reviewed file)
- `docs/reviews/portfolio_v2_init_review.md` (detailed review)
- `docs/reviews/portfolio_v2_init_summary.md` (executive summary)
