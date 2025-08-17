from __future__ import annotations

from typing import Any

import pytest

from the_alchemiser.services.trading.trading_service_manager import TradingServiceManager


@pytest.fixture(autouse=True)
def clear_flag_env(monkeypatch: pytest.MonkeyPatch):
    # Default legacy for tests unless explicitly enabled
    monkeypatch.setenv("TYPES_V2_ENABLED", "0")
    yield
    monkeypatch.delenv("TYPES_V2_ENABLED", raising=False)


class DummyOrderObj:
    def __init__(self, id: str, symbol: str, qty: float, status: str, order_type: str = "market"):
        self.id = id
        self.symbol = symbol
        self.qty = qty
        self.status = status
        self.order_type = order_type
        self.limit_price = None
        self.created_at = None


class DummyAlpacaManager:
    def __init__(self, orders: list[Any]):
        self._orders = orders

    def get_orders(self, status: str | None = None):
        return self._orders


def make_manager(orders: list[Any]):
    mgr = TradingServiceManager("key", "secret", paper=True)
    mgr.alpaca_manager = DummyAlpacaManager(orders)
    return mgr


def test_get_open_orders_legacy(monkeypatch: pytest.MonkeyPatch):
    orders = [
        DummyOrderObj("11111111-1111-1111-1111-111111111111", "AAPL", 1.0, "new"),
        {
            "id": "22222222-2222-2222-2222-222222222222",
            "symbol": "MSFT",
            "qty": 2.0,
            "status": "filled",
        },
    ]
    mgr = make_manager(orders)
    res = mgr.get_open_orders()
    assert isinstance(res, list)
    assert isinstance(res[0], dict)
    assert "id" in res[0]
    assert res[0]["symbol"] == "AAPL"


def test_get_open_orders_typed(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("TYPES_V2_ENABLED", "1")
    orders = [
        DummyOrderObj("11111111-1111-1111-1111-111111111111", "AAPL", 1.0, "new"),
        {
            "id": "22222222-2222-2222-2222-222222222222",
            "symbol": "MSFT",
            "qty": 2.0,
            "status": "filled",
        },
    ]
    mgr = make_manager(orders)
    res = mgr.get_open_orders()
    assert isinstance(res, list)
    first = res[0]
    assert "domain" in first and "summary" in first
    dom = first["domain"]
    # Domain object has attributes
    assert dom.symbol.value in ("AAPL", "MSFT")
    assert float(dom.quantity.value) in (1.0, 2.0)
    # Summary shape
    summary = first["summary"]
    assert {"id", "symbol", "qty", "status", "type"}.issubset(summary.keys())
