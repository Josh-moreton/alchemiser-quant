# Final Typing Completion Plan

## Status Overview

We've made excellent progress on the strict typing migration! Here's what's left to complete the project:

**✅ COMPLETED PHASES (1-4, 6-9, 11-12, 14):**

- Core types defined in `types.py` (398 lines of comprehensive TypedDict definitions)
- Account, Position, Order, Strategy, Dashboard, Performance, Error types
- Most complex modules already migrated

**🔄 REMAINING PHASES (5, 10, 13, 15):**

- **Phase 5**: Portfolio rebalancer TradingPlan migration (2 simple changes)
- **Phase 10**: Reporting module structured types
- **Phase 13**: CLI type implementations
- **Phase 15**: Trading engine and tracking annotations

---

## Section 1: Phase 5 - Portfolio Rebalancer (5 minutes)

**Priority: HIGH - Quick wins**

### Target File: `execution/portfolio_rebalancer.py`

**Changes needed:**

1. Line 120: `sell_plans: list[dict[str, Any]]` → `sell_plans: list[TradingPlan]`
2. Line 323: `buy_plans: list[dict[str, Any]]` → `buy_plans: list[TradingPlan]`

**Import required:**

```python
from the_alchemiser.core.types import TradingPlan
```

**Validation:** The `TradingPlan` type already exists and matches the dict structure perfectly:

```python
class TradingPlan(TypedDict):
    symbol: str
    action: Literal["BUY", "SELL"]
    quantity: float
    estimated_price: float
    reasoning: str
```

---

## Section 2: Phase 10 - Reporting Module (15 minutes)

**Priority: MEDIUM - Important for production**

### Target File: `execution/reporting.py`

**Changes needed:**

1. Line 11: `engine: Any` → `engine: TradingEngine` (import from trading_engine)
2. Line 14: `orders_executed: list[dict[str, Any]]` → `orders_executed: list[OrderDetails]`
3. Line 15: `account_before: dict[str, Any]` → `account_before: AccountInfo`
4. Line 16: `account_after: dict[str, Any]` → `account_after: AccountInfo`
5. Line 17: Return type `dict[str, Any]` → `ReportingData`
6. Line 58: `engine: Any, execution_result: Any` → proper types

**Imports required:**

```python
from the_alchemiser.core.types import (
    OrderDetails, 
    AccountInfo, 
    ReportingData
)
from the_alchemiser.execution.trading_engine import TradingEngine
```

---

## Section 3: Phase 13 - CLI Implementation (10 minutes)

**Priority: MEDIUM - User experience**

### Target Files: Various CLI modules

**Note:** CLI types are already defined in `types.py`, just need implementation in:

- `cli.py` - main CLI interface
- CLI command handlers

**Types available:**

- `CLIOptions`, `CLICommandResult`, `CLISignalData`
- `CLIAccountDisplay`, `CLIPortfolioData`, `CLIOrderDisplay`

**Strategy:** Replace `dict[str, Any]` patterns with specific CLI types

---

## Section 4: Phase 15 - Trading Engine & Tracking (20 minutes)

**Priority: LOW - Final cleanup**

### Target Files

**`tracking/integration.py`:**

- Line 150: `order: Any` → `order: AlpacaOrderProtocol`
- Line 151: Return `dict[str, Any]` → `OrderDetails`
- Line 184: Use `AlpacaOrderProtocol`
- Line 213: Use `TradingEngine` type

**`execution/trading_engine.py`:**

- Line 138: `config: Any` → proper config type
- Line 682: Add return type annotation
- Line 793: Add return type

**`utils/` modules:**

- `limit_order_handler.py` Line 101: → `LimitOrderResult`
- `websocket_order_monitor.py` Lines 243, 246, 252, 288: → `WebSocketResult`

---

## Section 5: Phase 7 Cleanup - Utility Types (10 minutes)

**Priority: LOW - Final polish**

### Target Files

- `utils/limit_order_handler.py`: Migrate to `LimitOrderResult`
- `utils/websocket_order_monitor.py`: Migrate to `WebSocketResult`
- `execution/smart_execution.py`: Migrate to `QuoteData` and `OrderDetails`

---

## Execution Plan

### Step 1: Quick Wins (Phase 5) - START HERE

✅ Portfolio rebalancer TradingPlan migration

- Simple find/replace operations
- Types already exist and match
- Immediate impact, low risk

### Step 2: Core Business Logic (Phase 10)

✅ Reporting module structured types

- Critical for production reporting
- Well-defined types available
- Medium complexity

### Step 3: User Interface (Phase 13)

✅ CLI type implementations

- Important for user experience
- Types pre-defined, just need implementation
- Medium effort

### Step 4: Final Cleanup (Phase 15 & 7)

✅ Trading engine and utility annotations

- Complete the migration
- Low priority but good for completeness
- Higher complexity items

### Step 5: Validation

✅ Run type checking: `mypy --strict the_alchemiser/`
✅ Run tests: `pytest` (once test framework is ready)
✅ Update TODO documentation

---

## Success Criteria

**✅ All TODO comments with "Phase X" removed**
**✅ `mypy --strict` passes without type errors**
**✅ No `dict[str, Any]` in core business logic**
**✅ All function signatures have proper type annotations**
**✅ Import statements updated for new types**

---

## Time Estimate: **1 hour total**

- Phase 5: 5 minutes (immediate)
- Phase 10: 15 minutes
- Phase 13: 10 minutes
- Phase 15: 20 minutes
- Phase 7: 10 minutes

After completion, you'll have a fully typed codebase ready for comprehensive testing!
