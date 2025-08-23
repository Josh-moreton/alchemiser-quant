# Canonical Typed Contracts

Models use `dataclasses` unless validation is required, in which case `pydantic.BaseModel` is used. All models are serialisable via `.dict()` and `.json()` with `by_alias=True`.

## AccountInfo
```python
from dataclasses import dataclass
from typing import Dict

@dataclass(frozen=True)
class AccountInfo:
    id: str
    balances: Dict[str, float]
    status: str  # active, suspended
```
**Invariants**: `balances` keys are ISO currency codes.  
**Migration**: previously `Dict[str, Any]` from provider; now validated at boundary.

## OrderDetails
```python
from dataclasses import dataclass
from typing import Literal

@dataclass(frozen=True)
class OrderDetails:
    symbol: str
    side: Literal['buy', 'sell']
    qty: float
    order_type: Literal['market', 'limit']
    limit_price: float | None = None
```
**Serialisation**: `dict()` matches broker API.  
**Migration**: replaces ad‑hoc dict in smart execution.

## ExecutionResultDTO
```python
from dataclasses import dataclass
from typing import List

@dataclass(frozen=True)
class ExecutionResultDTO:
    orders: List[OrderDetails]
    success: bool
    message: str | None = None
```
**Migration**: replaces `Dict` return from execution services.

## PositionSnapshot
```python
from dataclasses import dataclass
from datetime import datetime

@dataclass(frozen=True)
class PositionSnapshot:
    timestamp: datetime
    positions: dict[str, float]
```
**Migration**: supersedes `Dict[str, Any]` portfolio metrics.

## SignalPayload
```python
from dataclasses import dataclass

@dataclass(frozen=True)
class SignalPayload:
    strategy: str
    data: dict
```
**Migration**: wraps heterogeneous strategy outputs.

## ProviderResponse
```python
from pydantic import BaseModel

class Quote(BaseModel):
    symbol: str
    bid: float
    ask: float
    ts: int

class Bar(BaseModel):
    symbol: str
    open: float
    high: float
    low: float
    close: float
    volume: int
    ts: int

class OrderAck(BaseModel):
    id: str
    status: str
    ts: int
```

## CacheEntry[T]
```python
from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar('T')

@dataclass(frozen=True)
class CacheKey:
    namespace: str
    key: str

@dataclass(frozen=True)
class CacheEntry(Generic[T]):
    key: CacheKey
    value: T
    ttl: int
```
**Migration**: replaces `Dict[str, Any]` cache values.

# Worked Examples

## 1. Order placement with `OrderDetails` and `ExecutionResultDTO`
```python
# adapter
class LegacyOrderAdapter:
    @staticmethod
    def from_dict(d: dict) -> OrderDetails:
        return OrderDetails(
            symbol=d['symbol'],
            side=d['side'],
            qty=float(d['qty']),
            order_type=d.get('type', 'market'),
            limit_price=d.get('limit_price'),
        )

# usage
order = LegacyOrderAdapter.from_dict(payload)
result = broker.place_order(order)
assert isinstance(result, ExecutionResultDTO)
```
_Test_: `tests/execution/test_smart_execution.py` updated with model assertions.

## 2. Provider cache with `CacheEntry[Quote]`
```python
key = CacheKey('quotes', symbol)
entry: CacheEntry[Quote] | None = cache.get(key)
if not entry:
    quote = provider.get_quote(symbol)
    entry = CacheEntry(key=key, value=quote, ttl=60)
    cache.set(entry)
return entry.value
```
_Test_: `tests/providers/test_quote_cache.py` ensures serialisation/deserialisation.

## 3. Email template using typed context
```python
context = TradingReportContext(account=AccountInfo(...), results=[ExecutionResultDTO(...)] )
html = render_template('trading_report.html', context)
```
_Snapshot_: `tests/email/test_trading_report_snapshot.py` captures HTML before/after.
