from __future__ import annotations

from types import SimpleNamespace

import pytest

from the_alchemiser.services.trading.trading_service_manager import TradingServiceManager


@pytest.fixture(autouse=True)
def clear_flag_env(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("TYPES_V2_ENABLED", raising=False)
    yield
    monkeypatch.delenv("TYPES_V2_ENABLED", raising=False)


class DummyOrderObj:
    def __init__(
        self,
        id: str,
        symbol: str,
        qty: float,
        status: str = "new",
        order_type: str = "limit",
        limit_price: float = 0,
    ):
        self.id = id
        self.symbol = symbol
        self.qty = qty
        self.status = status
        self.order_type = order_type
        self.limit_price = limit_price


class DummyAlpacaManager:
    def __init__(self):
        self.placed = []

    def place_order(self, req):
        self.placed.append(req)
        return DummyOrderObj(
            "cccccccc-cccc-cccc-cccc-cccccccccccc",
            req.symbol,
            req.qty,
            "new",
            "limit",
            getattr(req, "limit_price", 0),
        )


class DummyOrdersService:
    def __init__(self):
        self.calls = []

    def place_limit_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        limit_price: float,
        validate_price: bool = True,
    ) -> str:
        self.calls.append((symbol, side, quantity, limit_price, validate_price))
        return "dddddddd-dddd-dddd-dddd-dddddddddddd"


def make_manager_with_doubles():
    mgr = TradingServiceManager("key", "secret", paper=True)
    mgr.alpaca_manager = DummyAlpacaManager()  # type: ignore[assignment]
    mgr.orders = DummyOrdersService()  # type: ignore[assignment]
    return mgr


def test_place_limit_order_legacy():
    mgr = make_manager_with_doubles()
    out = mgr.place_limit_order("AAPL", 5, "buy", 150.0, validate=True)
    assert out["success"] is True
    assert out["order_id"] == "dddddddd-dddd-dddd-dddd-dddddddddddd"


def test_place_limit_order_typed(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("TYPES_V2_ENABLED", "1")

    # Dummy Alpaca types
    class LimitOrderRequest(SimpleNamespace):
        pass

    class OrderSide:
        BUY = "buy"
        SELL = "sell"

    class TimeInForce:
        DAY = "day"

    import builtins

    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "alpaca.trading.requests":
            return SimpleNamespace(LimitOrderRequest=LimitOrderRequest)  # type: ignore[return-value]
        if name == "alpaca.trading.enums":
            return SimpleNamespace(OrderSide=OrderSide, TimeInForce=TimeInForce)  # type: ignore[return-value]
        return real_import(name, *args, **kwargs)

    builtins.__import__ = fake_import  # type: ignore[assignment]
    try:
        mgr = make_manager_with_doubles()
        out = mgr.place_limit_order("MSFT", 10, "sell", 310.5, validate=False)
        assert out["success"] is True
        assert "order" in out
        summary = out["order"]["summary"]
        assert summary["symbol"] == "MSFT"
        assert summary["qty"] == 10.0
        assert summary["type"].lower() == "limit"
    finally:
        builtins.__import__ = real_import  # type: ignore[assignment]
