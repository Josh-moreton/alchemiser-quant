# Type Upgrade

## **Comprehensive Strict Typing Implementation Plan**

### **Phase 1: Core Type Definitions (Foundation)**

#### **1.1 Create Core Type Definitions File**

**File**: `the_alchemiser/core/types.py` (NEW)

```python
"""Core type definitions for The Alchemiser trading system."""
from typing import TypedDict, Literal, Any
from datetime import datetime
from decimal import Decimal

# Account Information Types
class AccountInfo(TypedDict):
    account_id: str
    equity: str | float
    cash: str | float
    buying_power: str | float
    day_trades_remaining: int
    portfolio_value: str | float
    last_equity: str | float
    daytrading_buying_power: str | float
    regt_buying_power: str | float
    status: Literal["ACTIVE", "INACTIVE"]

# Position Types
class PositionInfo(TypedDict):
    symbol: str
    qty: str | float
    side: Literal["long", "short"]
    market_value: str | float
    cost_basis: str | float
    unrealized_pl: str | float
    unrealized_plpc: str | float
    current_price: str | float

class PositionsDict(TypedDict):
    positions: dict[str, PositionInfo]

# Order Types
class OrderDetails(TypedDict):
    id: str
    symbol: str
    qty: str | float
    side: Literal["buy", "sell"]
    order_type: Literal["market", "limit", "stop", "stop_limit"]
    time_in_force: Literal["day", "gtc", "ioc", "fok"]
    status: Literal["new", "partially_filled", "filled", "canceled", "expired", "rejected"]
    filled_qty: str | float
    filled_avg_price: str | float | None
    created_at: str
    updated_at: str

# Strategy Types
class StrategySignal(TypedDict):
    symbol: str
    action: Literal["BUY", "SELL", "HOLD"]
    confidence: float
    reasoning: str
    allocation_percentage: float

class StrategyPnLSummary(TypedDict):
    strategy_name: str
    total_pnl: float
    realized_pnl: float
    unrealized_pnl: float
    total_trades: int
    win_rate: float
    positions_count: int

# Trading Execution Types
class ExecutionResult(TypedDict):
    orders_executed: list[OrderDetails]
    account_info_before: AccountInfo
    account_info_after: AccountInfo
    execution_summary: dict[str, Any]  # Will be refined in Phase 2
    final_portfolio_state: dict[str, Any] | None

# Error Reporting Types
class ErrorContext(TypedDict):
    timestamp: str
    component: str
    operation: str
    additional_data: dict[str, Any]

# Email Configuration Types
class EmailCredentials(TypedDict):
    smtp_server: str
    smtp_port: int
    email_address: str
    email_password: str
    recipient_email: str
```

### **Phase 2: Fix Critical Trading Engine Types**

#### **2.1 Update Trading Engine Protocol**

**File**: `the_alchemiser/execution/trading_engine.py`

**Lines 41, 49, 73, 176, 225 etc.**

```python
# BEFORE:
def get_account_info(self) -> dict[str, Any]:
def get_positions_dict(self) -> dict[str, dict[str, Any]]:

# AFTER:
from ..core.types import AccountInfo, PositionsDict

def get_account_info(self) -> AccountInfo:
def get_positions_dict(self) -> PositionsDict:
```

**Lines 362, 411, 539, 559-561:**

```python
# BEFORE:
) -> list[dict[str, Any]]:
) -> dict[str, Any]:

# AFTER:
from ..core.types import OrderDetails, ExecutionResult, StrategyPnLSummary

) -> list[OrderDetails]:
) -> ExecutionResult:
def get_multi_strategy_performance_report(self) -> StrategyPnLSummary:
def generate_execution_report(
    self,
    account_info: AccountInfo,
    current_positions: PositionsDict,
) -> ExecutionResult:
```

#### **2.2 Update Account Service**

**File**: `the_alchemiser/execution/account_service.py`

**Lines 33, 41, 49:**

```python
# BEFORE:
def get_account_info(self) -> dict[str, Any]:
def get_positions_dict(self) -> dict[str, dict[str, Any]]:
position_dict: dict[str, dict[str, Any]] = {}

# AFTER:
from ..core.types import AccountInfo, PositionsDict, PositionInfo

def get_account_info(self) -> AccountInfo:
def get_positions_dict(self) -> PositionsDict:
position_dict: dict[str, PositionInfo] = {}
```

### **Phase 3: Fix Main Entry Points**

#### **3.1 Update Main.py**

**File**: `the_alchemiser/main.py`

**Line 70:**

```python
# BEFORE:
def generate_multi_strategy_signals(settings: Settings) -> tuple[Any, ...]:

# AFTER:
from .core.types import StrategySignal
from .core.trading.strategy_manager import MultiStrategyManager

def generate_multi_strategy_signals(
    settings: Settings
) -> tuple[MultiStrategyManager, dict[StrategyType, StrategySignal], dict[str, float]]:
```

#### **3.2 Update Lambda Handler**

**File**: `the_alchemiser/lambda_handler.py`

**Line 22:**

```python
# BEFORE:
def parse_event_mode(event: dict[str, Any]) -> list[str]:

# AFTER:
class LambdaEvent(TypedDict):
    mode: str | None
    arguments: list[str] | None

def parse_event_mode(event: LambdaEvent) -> list[str]:
```

### **Phase 4: Fix Tracking and Integration**

#### **4.1 Update Tracking Integration**

**File**: `the_alchemiser/tracking/integration.py`

**Lines 138, 144:**

```python
# BEFORE:
) -> dict[str, Any]:
def extract_order_details_from_alpaca_order(order) -> dict[str, Any]:

# AFTER:
from ..core.types import StrategyPnLSummary, OrderDetails

) -> StrategyPnLSummary:

# Create Alpaca Order Protocol
class AlpacaOrderProtocol(Protocol):
    id: str
    symbol: str
    qty: str
    side: str
    order_type: str
    time_in_force: str
    status: str
    filled_qty: str
    filled_avg_price: str | None
    created_at: str
    updated_at: str

def extract_order_details_from_alpaca_order(order: AlpacaOrderProtocol) -> OrderDetails:
```

#### **4.2 Update Strategy Order Tracker**

**File**: `the_alchemiser/tracking/strategy_order_tracker.py`

**Lines 487, 525, 530:**

```python
# BEFORE:
def _apply_order_history_limit(self, data: dict[str, Any]) -> None:
) -> dict[str, Any]:
summary: dict[str, Any] = {

# AFTER:
class OrderHistoryData(TypedDict):
    orders: list[OrderDetails]
    metadata: dict[str, Any]

class EmailSummary(TypedDict):
    total_orders: int
    recent_orders: list[OrderDetails]
    performance_metrics: dict[str, float]

def _apply_order_history_limit(self, data: OrderHistoryData) -> None:
) -> EmailSummary:
summary: EmailSummary = {
```

### **Phase 5: Fix Execution Layer**

#### **5.1 Update Portfolio Rebalancer**

**File**: `the_alchemiser/execution/portfolio_rebalancer.py`

**Lines 53, 65, 91, 233:**

```python
# BEFORE:
) -> list[dict[str, Any]]:
orders_executed: list[dict[str, Any]] = []
sell_plans: list[dict[str, Any]] = []
buy_plans: list[dict[str, Any]] = []

# AFTER:
from ..core.types import OrderDetails

class TradingPlan(TypedDict):
    symbol: str
    action: Literal["BUY", "SELL"]
    quantity: float
    estimated_price: float
    reasoning: str

) -> list[OrderDetails]:
orders_executed: list[OrderDetails] = []
sell_plans: list[TradingPlan] = []
buy_plans: list[TradingPlan] = []
```

#### **5.2 Update Smart Execution**

**File**: `the_alchemiser/execution/smart_execution.py`

**Lines 82, 297, 323:**

```python
# BEFORE:
def get_latest_quote(self, symbol: str) -> tuple[Any, ...]:
self, sell_orders: list[dict[str, Any]], max_wait_time: int = 60, poll_interval: float = 2.0
order_obj: Any = self._order_executor.trading_client.get_order_by_id(order_id)

# AFTER:
class QuoteData(TypedDict):
    bid_price: float
    ask_price: float
    bid_size: float
    ask_size: float
    timestamp: str

def get_latest_quote(self, symbol: str) -> QuoteData:
self, sell_orders: list[OrderDetails], max_wait_time: int = 60, poll_interval: float = 2.0

# Create protocol for Alpaca order object
class AlpacaOrderObject(Protocol):
    id: str
    status: str
    filled_qty: str

order_obj: AlpacaOrderObject = self._order_executor.trading_client.get_order_by_id(order_id)
```

### **Phase 6: Fix Strategy Layer**

#### **6.1 Update Strategy Manager**

**File**: `the_alchemiser/core/trading/strategy_manager.py`

**Lines 44, 54, 138, 146, 319, 393, 423, 455, 458, 460:**

```python
# BEFORE:
def to_dict(self) -> dict[str, Any]:
def from_dict(cls, data: dict[str, Any]) -> "StrategyPosition":
) -> tuple[dict[StrategyType, Any], dict[str, float], dict[str, list[StrategyType]]]:
strategy_signals: dict[StrategyType, dict[str, Any]] = {}
def _get_nuclear_portfolio_allocation(self, signal_data: dict[str, Any]) -> dict[str, float]:
self, signal_data: dict[str, Any], strategy_type: StrategyType
new_positions: dict[StrategyType, list[Any]] = {
def get_strategy_performance_summary(self) -> dict[str, Any]:
positions: dict[StrategyType, list[Any]] = {strategy: [] for strategy in StrategyType}
summary: dict[str, Any] = {

# AFTER:
from ..types import StrategySignal, StrategyPnLSummary

class StrategyPositionData(TypedDict):
    symbol: str
    quantity: float
    entry_price: float
    current_price: float
    strategy_type: str

def to_dict(self) -> StrategyPositionData:
def from_dict(cls, data: StrategyPositionData) -> "StrategyPosition":
) -> tuple[dict[StrategyType, StrategySignal], dict[str, float], dict[str, list[StrategyType]]]:
strategy_signals: dict[StrategyType, StrategySignal] = {}
def _get_nuclear_portfolio_allocation(self, signal_data: StrategySignal) -> dict[str, float]:
self, signal_data: StrategySignal, strategy_type: StrategyType
new_positions: dict[StrategyType, list[StrategyPositionData]] = {
def get_strategy_performance_summary(self) -> StrategyPnLSummary:
positions: dict[StrategyType, list[StrategyPositionData]] = {strategy: [] for strategy in StrategyType}
summary: StrategyPnLSummary = {
```

#### **6.2 Update KLM Ensemble Engine**

**File**: `the_alchemiser/core/trading/klm_ensemble_engine.py`

**Lines 180, 213-214, 285:**

```python
# BEFORE:
) -> list[tuple[BaseKLMVariant, Any, float]]:
self, variant_results: list[tuple[BaseKLMVariant, Any, float]]
) -> tuple[Any, BaseKLMVariant]:
all_variant_results: list[tuple[BaseKLMVariant, Any, float]],

# AFTER:
class KLMVariantResult(TypedDict):
    variant: BaseKLMVariant
    signal: StrategySignal
    confidence: float

) -> list[KLMVariantResult]:
self, variant_results: list[KLMVariantResult]
) -> tuple[StrategySignal, BaseKLMVariant]:
all_variant_results: list[KLMVariantResult],
```

### **Phase 7: Fix Utility Functions**

#### **7.1 Update Limit Order Handler**

**File**: `the_alchemiser/utils/limit_order_handler.py`

**Line 101:**

```python
# BEFORE:
) -> tuple[Any, ...]:

# AFTER:
from ..execution.types import LimitOrderRequest

class LimitOrderResult(TypedDict):
    order_request: LimitOrderRequest | None
    error_message: str | None

) -> LimitOrderResult:
```

#### **7.2 Update WebSocket Order Monitor**

**File**: `the_alchemiser/utils/websocket_order_monitor.py`

**Lines 240, 243:**

```python
# BEFORE:
return self._use_existing_websocket(on_update, remaining, completed, max_wait_seconds)  # type: ignore[no-any-return]
return self._create_new_websocket(  # type: ignore[no-any-return]

# AFTER:
class WebSocketResult(TypedDict):
    status: Literal["completed", "timeout", "error"]
    message: str
    orders_completed: list[str]

def _use_existing_websocket(
    self, on_update, remaining, completed, max_wait_seconds
) -> WebSocketResult:

def _create_new_websocket(
    self, on_update, remaining, completed, max_wait_seconds
) -> WebSocketResult:

# Remove type: ignore comments
return self._use_existing_websocket(on_update, remaining, completed, max_wait_seconds)
return self._create_new_websocket(
```

### **Phase 8: Fix Email and UI Layer**

#### **8.1 Update Email Config**

**File**: `the_alchemiser/core/ui/email/config.py`

**Line 28:**

```python
# BEFORE:
return self._config_cache  # type: ignore[no-any-return]

# AFTER:
from ...types import EmailCredentials

class EmailConfig:
    def __init__(self):
        self._config_cache: EmailCredentials | None = None
    
    def get_config(self) -> EmailCredentials:
        if self._config_cache is not None:
            return self._config_cache
        # ... rest of implementation
```

#### **8.2 Update Email Templates**

**File**: `the_alchemiser/core/ui/email/templates/portfolio.py`

**Lines 16, 80, 133, 166, 247, 288:**

```python
# BEFORE:
def build_positions_table(open_positions: list[dict[str, Any]]) -> str:
def build_account_summary(account_info: dict[str, Any]) -> str:
def build_portfolio_allocation(result: Any) -> str:
def build_closed_positions_pnl(account_info: dict[str, Any]) -> str:
def build_positions_table_neutral(open_positions: list[dict[str, Any]]) -> str:
def build_account_summary_neutral(account_info: dict[str, Any]) -> str:

# AFTER:
from ...types import AccountInfo, PositionInfo

def build_positions_table(open_positions: list[PositionInfo]) -> str:
def build_account_summary(account_info: AccountInfo) -> str:
def build_portfolio_allocation(result: ExecutionResult) -> str:
def build_closed_positions_pnl(account_info: AccountInfo) -> str:
def build_positions_table_neutral(open_positions: list[PositionInfo]) -> str:
def build_account_summary_neutral(account_info: AccountInfo) -> str:
```

### **Phase 9: Fix KLM Variants Type Errors**

#### **9.1 Update KLM Variants**

**Files**: `the_alchemiser/core/trading/klm_workers/variant_*.py`

**Remove all `# type: ignore[assignment]` comments and fix underlying types:**

```python
# BEFORE:
result = (  # type: ignore[assignment]
result = self._evaluate_holy_grail_pop_bot(indicators)  # type: ignore[assignment]

# AFTER:
# Create proper result type
class KLMDecision(TypedDict):
    symbol: str
    action: Literal["BUY", "SELL", "HOLD"]
    reasoning: str

# Update all variant methods to return KLMDecision instead of tuple
result: KLMDecision = {
    "symbol": "FNGU",
    "action": "BUY",
    "reasoning": "KMLM Switcher: FNGU fallback"
}
```

### **Phase 10: Fix Reporting and Dashboard**

#### **10.1 Update Reporting Functions**

**File**: `the_alchemiser/execution/reporting.py`

**Lines 11-14, 105-107:**

```python
# BEFORE:
orders_executed: list[dict[str, Any]],
account_before: dict[str, Any],
account_after: dict[str, Any],
) -> dict[str, Any]:

# AFTER:
from ..core.types import OrderDetails, AccountInfo, ExecutionResult

orders_executed: list[OrderDetails],
account_before: AccountInfo,
account_after: AccountInfo,
) -> ExecutionResult:
```

#### **10.2 Update Dashboard Utils**

**File**: `the_alchemiser/utils/dashboard_utils.py`

**Lines 15, 46, 80, 114-115, 143-144:**

```python
# BEFORE:
def build_basic_dashboard_structure(paper_trading: bool) -> dict[str, Any]:
def extract_portfolio_metrics(account_info: dict[str, Any]) -> dict[str, float]:
def extract_positions_data(open_positions: list[dict[str, Any]]) -> list[dict[str, Any]]:
strategy_signals: dict[str, Any], strategy_allocations: dict[str, Any]
) -> dict[str, dict[str, Any]]:
orders_executed: list[dict[str, Any]], limit: int = 10
) -> list[dict[str, Any]]:

# AFTER:
from ..core.types import AccountInfo, PositionInfo, OrderDetails, StrategySignal

class DashboardStructure(TypedDict):
    account_status: str
    trading_mode: Literal["paper", "live"]
    timestamp: str

def build_basic_dashboard_structure(paper_trading: bool) -> DashboardStructure:
def extract_portfolio_metrics(account_info: AccountInfo) -> dict[str, float]:
def extract_positions_data(open_positions: list[PositionInfo]) -> list[PositionInfo]:
strategy_signals: dict[str, StrategySignal], strategy_allocations: dict[str, float]
) -> dict[str, StrategySignal]:
orders_executed: list[OrderDetails], limit: int = 10
) -> list[OrderDetails]:
```

### **Phase 11: Fix Data Layer**

#### **11.1 Update Data Provider**

**File**: `the_alchemiser/core/data/data_provider.py`

**Remove unsafe `cast(TimeFrame, timeframe)` usage and implement proper validation:**

```python
# BEFORE:
cast(TimeFrame, timeframe)

# AFTER:
def validate_timeframe(timeframe: str) -> TimeFrame:
    """Safely convert string to TimeFrame enum."""
    timeframe_mapping = {
        "1Min": TimeFrame.Minute,
        "5Min": TimeFrame.FiveMin,
        "15Min": TimeFrame.FifteenMin,
        "1Hour": TimeFrame.Hour,
        "1Day": TimeFrame.Day
    }
    
    if timeframe not in timeframe_mapping:
        raise ValueError(f"Invalid timeframe: {timeframe}")
    
    return timeframe_mapping[timeframe]

# Use: validate_timeframe(timeframe) instead of cast
```

#### **11.2 Update Real-time Pricing**

**File**: `the_alchemiser/core/data/real_time_pricing.py`

**Lines 105, 211, 259, 411, 693:**

```python
# BEFORE:
self._stats: dict[str, Any] = {
async def _on_quote(self, quote: Quote | dict[str, Any]) -> None:
async def _on_trade(self, trade: Trade | dict[str, Any]) -> None:
def get_stats(self) -> dict[str, Any]:

# AFTER:
class PricingStats(TypedDict):
    quotes_received: int
    trades_received: int
    last_update: str
    symbols_tracked: list[str]

self._stats: PricingStats = {
async def _on_quote(self, quote: Quote) -> None:
async def _on_trade(self, trade: Trade) -> None:
def get_stats(self) -> PricingStats:
```

### **Phase 12: Fix Backtest Layer**

#### **12.1 Update Backtest Components**

**File**: `the_alchemiser/backtest/data_cache.py`

**Lines 54, 224, 250, 257, 270:**

```python
# BEFORE:
self._cache_metadata: dict[str, dict[str, Any]] = {}
def _process_timestamp(self, timestamp: Any, symbol: str, bar_index: int) -> dt.datetime | None:
def _extract_timestamp_from_bar(self, bar: Any) -> Any:
def _create_bar_row(self, bar: Any) -> dict[str, float] | None:
def _convert_bars_to_dataframe(self, bars: list[Any], symbol: str) -> pd.DataFrame | None:

# AFTER:
from alpaca.data.models import Bar

class CacheMetadata(TypedDict):
    last_updated: str
    symbol_count: int
    timeframe: str

self._cache_metadata: dict[str, CacheMetadata] = {}
def _process_timestamp(self, timestamp: str | datetime, symbol: str, bar_index: int) -> dt.datetime | None:
def _extract_timestamp_from_bar(self, bar: Bar) -> datetime:
def _create_bar_row(self, bar: Bar) -> dict[str, float] | None:
def _convert_bars_to_dataframe(self, bars: list[Bar], symbol: str) -> pd.DataFrame | None:
```

### **Phase 13: Fix CLI and Display**

#### **13.1 Update CLI Formatter**

**File**: `the_alchemiser/core/ui/cli_formatter.py`

**Lines 19, 190, 255, 383-384, 454-455:**

```python
# BEFORE:
all_indicators: dict[str, dict[str, Any]] = {}
orders_executed: list[dict[str, Any]], console: Console | None = None
def render_account_info(account_info: dict[str, Any], console: Console | None = None) -> None:
account_info: dict[str, Any],
current_positions: dict[str, Any],
sell_orders: list[dict[str, Any]],
buy_orders: list[dict[str, Any]],

# AFTER:
from ..types import AccountInfo, PositionInfo, OrderDetails, StrategySignal

class IndicatorData(TypedDict):
    value: float
    timestamp: str
    symbol: str

all_indicators: dict[str, IndicatorData] = {}
orders_executed: list[OrderDetails], console: Console | None = None
def render_account_info(account_info: AccountInfo, console: Console | None = None) -> None:
account_info: AccountInfo,
current_positions: PositionsDict,
sell_orders: list[OrderDetails],
buy_orders: list[OrderDetails],
```

### **Phase 14: Fix Error Handler**

#### **14.1 Update Error Handler**

**File**: `the_alchemiser/core/error_handler.py`

**Lines 49, 61, 146, 184, 285:**

```python
# BEFORE:
additional_data: dict[str, Any] | None = None,
def to_dict(self) -> dict[str, Any]:
additional_data: dict[str, Any] | None = None,
def get_error_summary(self) -> dict[str, Any]:
error: Exception, context: str, component: str, additional_data: dict[str, Any] | None = None

# AFTER:
from .types import ErrorContext

class ErrorSummary(TypedDict):
    total_errors: int
    by_category: dict[str, int]
    critical_errors: list[str]
    recent_errors: list[ErrorContext]

additional_data: ErrorContext | None = None,
def to_dict(self) -> ErrorContext:
additional_data: ErrorContext | None = None,
def get_error_summary(self) -> ErrorSummary:
error: Exception, context: str, component: str, additional_data: ErrorContext | None = None
```

### **Phase 15: Update mypy Configuration**

#### **15.1 Enhance mypy Settings**

**File**: `pyproject.toml`

```toml
[tool.mypy]
python_version = "3.12"
warn_return_any = true
warn_unused_configs = true
disallow_any_generics = true
disallow_subclassing_any = true
disallow_untyped_calls = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
disallow_untyped_decorators = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true
warn_unreachable = true
strict_equality = true
strict_concatenate = true

# Remove or minimize these as we fix types:
# [[tool.mypy.overrides]]
# module = ["alpaca.*", "boto3.*"]
# ignore_missing_imports = true
```

### **Phase 16: Testing and Validation**

#### **16.1 Create Type Validation Tests**

**File**: `tests/test_types.py` (NEW)

```python
"""Tests for type definitions and validation."""
import pytest
from typing import get_type_hints
from the_alchemiser.core.types import (
    AccountInfo, PositionInfo, OrderDetails, 
    StrategySignal, StrategyPnLSummary
)

def test_account_info_structure():
    """Test AccountInfo TypedDict structure."""
    hints = get_type_hints(AccountInfo)
    required_fields = {
        'account_id', 'equity', 'cash', 'buying_power', 
        'day_trades_remaining', 'portfolio_value', 'status'
    }
    assert all(field in hints for field in required_fields)

def test_strategy_signal_structure():
    """Test StrategySignal TypedDict structure."""
    hints = get_type_hints(StrategySignal)
    required_fields = {
        'symbol', 'action', 'confidence', 'reasoning', 'allocation_percentage'
    }
    assert all(field in hints for field in required_fields)

# Add validation tests for each major TypedDict
```

#### **16.2 Run Comprehensive Type Checking**

```bash
# Phase-by-phase validation
mypy the_alchemiser/core/types.py                    # Phase 1
mypy the_alchemiser/execution/trading_engine.py      # Phase 2  
mypy the_alchemiser/main.py                         # Phase 3
mypy the_alchemiser/tracking/                       # Phase 4
mypy the_alchemiser/execution/                      # Phase 5
mypy the_alchemiser/core/trading/                   # Phase 6
mypy the_alchemiser/utils/                          # Phase 7
mypy the_alchemiser/core/ui/email/                  # Phase 8
mypy the_alchemiser/core/trading/klm_workers/       # Phase 9
mypy the_alchemiser/                                # Full project
```

## **Implementation Priority Order:**

1. **Phase 1** (Foundation) - Create core type definitions first
2. **Phase 2** (Trading Engine) - Critical for trading operations
3. **Phase 3** (Main Entry) - Required for basic functionality
4. **Phase 4** (Tracking) - Important for historical data
5. **Phases 5-7** (Execution & Utils) - Core trading functionality
6. **Phases 8-11** (UI & Data) - User interface and data handling
7. **Phases 12-13** (Backtest & CLI) - Supporting functionality
8. **Phases 14-16** (Error Handling & Testing) - Quality assurance

## **Validation Commands:**

```bash
# After each phase
mypy --strict the_alchemiser/
ruff check the_alchemiser/
black --check the_alchemiser/

# Final validation
poetry run pytest tests/test_types.py
poetry run mypy --strict the_alchemiser/
```
