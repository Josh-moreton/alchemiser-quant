# Type Hint Audit Report

### Type-hint findings

| File & line | Issue | Corrected annotation |
|-------------|-------|---------------------|
| `domain/registry/strategy_registry.py` L97 | Factory returns `Any`, losing engine type info. | `def create_strategy_engine(cls, strategy_type: StrategyType, **kwargs: Any) -> StrategyEngineProtocol:` |
| `domain/strategies/tecl_signals.py` L165 | Alert parameter typed as `Any`. | `def log_alert(self, alert: Alert) -> None:` |
| `domain/strategies/tecl_signals.py` L171 | Return type `Any`. | `def run_once(self) -> list[Alert] | None:` |
| `domain/strategies/nuclear_signals.py` L265 | Alert parameter typed as `Any`. | `def log_alert(self, alert: Alert) -> None:` |
| `domain/strategies/nuclear_signals.py` L271 | Return type `Any`. | `def run_once(self) -> list[Alert] | None:` |
| `domain/interfaces/trading_repository.py` L151 | `trading_client` property uses `Any`. | `@property def trading_client(self) -> TradingClient:` |
| `domain/interfaces/market_data_repository.py` L115 | `data_client` property uses `Any`. | `@property def data_client(self) -> StockHistoricalDataClient:` |
| `infrastructure/websocket/websocket_connection_manager.py` L122-128 | Stream/thread getters return `Any`. | `def get_websocket_stream(self) -> WebSocketApp | None:`<br>`def get_websocket_thread(self) -> threading.Thread | None:` |
| `services/repository/alpaca_manager.py` L95 | `get_account` returns `Any`. | `def get_account(self) -> Account:` |
| `services/repository/alpaca_manager.py` L156 | `get_position` returns `Any`. | `def get_position(self, symbol: str) -> Position | None:` |
| `services/repository/alpaca_manager.py` L169 | `place_order` uses `Any` for request & return. | `def place_order(self, order_request: LimitOrderRequest | MarketOrderRequest) -> Order:` |
| `services/repository/alpaca_manager.py` L251 | `place_limit_order` returns `Any`. | `def place_limit_order(... ) -> Order:` |
| `services/repository/alpaca_manager.py` L392 | Quote getter returns `Any`. | `def get_latest_quote_raw(self, symbol: str) -> StockQuote | None:` |
| `application/trading/alpaca_client.py` L441 | Order lookup returns `Any`. | `def get_order_by_id(self, order_id: str) -> Order | None:` |
| `application/tracking/integration.py` L78-86 | Context manager typed `Any`. | `def strategy_execution_context(strategy: StrategyType) -> Iterator[None]:` |
| `application/tracking/integration.py` L104-124 | Decorator uses `Any`; lacks generics. | `def create_strategy_aware_order_callback(original_order_function: Callable[P, T]) -> Callable[P, T]:` with `P = ParamSpec('P'), T = TypeVar('T')` |
| `application/tracking/integration.py` L153 | P&L summary returns `dict[str, Any]`. | `def get_strategy_pnl_summary(self, current_prices: dict[str, float] | None = None) -> StrategyPnLSummary:` |
| `application/tracking/integration.py` L160-161 | Order extraction uses `Any`. | `def extract_order_details_from_alpaca_order(order: AlpacaOrderProtocol) -> OrderDetails:` |
| `application/tracking/integration.py` L197-198 | Tracking function accepts `Any`. | `def track_alpaca_order_if_filled(order: AlpacaOrderProtocol) -> None:` |
| `services/trading/trading_service_manager.py` L246 | Portfolio value returns `Any`. | `def get_portfolio_value(self) -> float:` |
| `application/execution/execution_manager.py` L32 | Execution result typed `Any`. | `def execute_multi_strategy(self) -> MultiStrategyExecutionResult:` |
| `services/errors/error_recovery.py` L256 | Circuit-breaker call uses `Callable[..., Any]`/`Any`. | Use generics: `T = TypeVar('T'); def call(self, func: Callable[..., T], *args: Any, **kwargs: Any) -> T:` |
| `services/errors/error_recovery.py` L392-399 | Retry function returns `Any`; not generic. | `def retry_with_strategy(self, func: Callable[[], T], ...) -> T:` |
| `services/errors/error_recovery.py` L507-510 | `execute_with_resilience` and inner `protected_func` return `Any`. | `def execute_with_resilience(..., func: Callable[..., T], ...) -> T:` and `def protected_func() -> T:` |
| `infrastructure/data_providers/unified_data_provider_facade.py` L182 | Runtime mismatch: string passed where `Exception` expected. | `self._error_handler.log_and_handle(e, {"symbol": symbol})` |

### Estimated type coverage

Approx. **85–90%**. Most functions are annotated, but many still rely on `Any` or placeholder types, reducing overall precision.

### Highest-impact fixes (priority)

1. **Replace `Any` in core interfaces** – repositories, Alpaca manager, and tracking integration drive most downstream typing. Precise protocols for external clients (Alpaca, WebSocket) will greatly improve safety.
2. **Introduce Protocols/TypedDicts** for strategy engines, order details, execution results, and account summaries to remove recurring `dict[str, Any]` usage.
3. **Add generics** to resilience utilities (`error_recovery`) and decorators to propagate concrete return types.
4. **Fix runtime type mismatches** such as `log_and_handle` expecting an `Exception`.
5. **Refine domain types** (e.g., `KLMVariantResult.variant`, `LimitOrderResult.order_request`) to avoid `Any` placeholders once circular dependencies are resolved.

### Ready-to-paste updates

```python
# domain/registry/strategy_registry.py
class StrategyEngineProtocol(Protocol):
    def run_once(self) -> list[Alert] | None: ...
    # add core engine methods here

@classmethod
def create_strategy_engine(
    cls, strategy_type: StrategyType, **kwargs: Any
) -> StrategyEngineProtocol:
    ...

# domain/strategies/tecl_signals.py
def log_alert(self, alert: Alert) -> None:
    ...

def run_once(self) -> list[Alert] | None:
    ...

# domain/interfaces/trading_repository.py
from alpaca.trading.client import TradingClient
@property
def trading_client(self) -> TradingClient: ...

# infrastructure/websocket/websocket_connection_manager.py
from websocket import WebSocketApp
import threading
def get_websocket_stream(self) -> WebSocketApp | None: ...
def get_websocket_thread(self) -> threading.Thread | None: ...

# services/repository/alpaca_manager.py
from alpaca.trading.models import Account, Position, Order
from alpaca.data.models import Quote
def get_account(self) -> Account: ...
def get_position(self, symbol: str) -> Position | None: ...
def place_order(self, order_request: LimitOrderRequest | MarketOrderRequest) -> Order: ...
def place_limit_order(... ) -> Order: ...
def get_latest_quote_raw(self, symbol: str) -> Quote | None: ...

# application/tracking/integration.py
from collections.abc import Iterator, Callable
from typing import ParamSpec, TypeVar
P = ParamSpec("P")
T = TypeVar("T")

@contextmanager
def strategy_execution_context(strategy: StrategyType) -> Iterator[None]:
    ...

def create_strategy_aware_order_callback(
    original_order_function: Callable[P, T]
) -> Callable[P, T]:
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        ...

# services/errors/error_recovery.py
T = TypeVar("T")
def call(self, func: Callable[..., T], *args: Any, **kwargs: Any) -> T: ...
def retry_with_strategy(self, func: Callable[[], T], ...) -> T: ...
def execute_with_resilience(..., func: Callable[..., T], ...) -> T:
    def protected_func() -> T:
        ...
```

### Notes
- Many `Any` placeholders in `domain/types.py` (e.g., `variant`, `execution_summary`, `order_request`) should evolve into concrete `TypedDict` or protocol definitions as the data structures stabilize.
- Where Alpaca or external SDK types are not yet available, creating thin Protocols (e.g., `AlpacaOrderProtocol`) can provide immediate benefits without forcing heavy imports.

