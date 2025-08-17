from __future__ import annotations

from types import SimpleNamespace

import pytest

from tests._tolerances import DEFAULT_ATL
from the_alchemiser.services.trading.trading_service_manager import TradingServiceManager


@pytest.fixture(autouse=True)
def clear_flag_env(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("TYPES_V2_ENABLED", raising=False)
    yield
    monkeypatch.delenv("TYPES_V2_ENABLED", raising=False)


class DummyOrderObj:
    def __init__(
        self, id: str, symbol: str, qty: float, status: str = "new", order_type: str = "market"
    ):
        self.id = id
        self.symbol = symbol
        self.qty = qty
        self.status = status
        self.order_type = order_type


class DummyAlpacaManager:
    def __init__(self):
        self.placed = []

    def place_order(self, req):
        # Simulate placing order and returning an object with id, symbol...
        self.placed.append(req)
        return DummyOrderObj(
            "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa", req.symbol, req.qty, "new", "market"
        )


class DummyOrdersService:
    def __init__(self):
        self.calls = []

    def place_market_order(
        self, symbol: str, side: str, quantity: float, validate_price: bool = True
    ) -> str:
        self.calls.append((symbol, side, quantity, validate_price))
        return "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"


def make_manager_with_doubles():
    mgr = TradingServiceManager("key", "secret", paper=True)
    mgr.alpaca_manager = DummyAlpacaManager()  # type: ignore[assignment]
    mgr.orders = DummyOrdersService()  # type: ignore[assignment]
    return mgr


def test_place_market_order_legacy(monkeypatch: pytest.MonkeyPatch):
    mgr = make_manager_with_doubles()
    out = mgr.place_market_order("AAPL", 5, "buy", validate=True)
    assert out["success"] is True
    assert out["order_id"] == "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"


def test_place_market_order_typed(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("TYPES_V2_ENABLED", "1")

    # Create a dummy MarketOrderRequest class to avoid importing alpaca in tests
    class MarketOrderRequest(SimpleNamespace):
        pass

    class OrderSide:
        BUY = "buy"
        SELL = "sell"

    class TimeInForce:
        DAY = "day"

    # Monkeypatch module import path used inside TradingServiceManager
    import builtins

    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "alpaca.trading.requests":
            mod = SimpleNamespace(MarketOrderRequest=MarketOrderRequest)
            return mod  # type: ignore[return-value]
        if name == "alpaca.trading.enums":
            mod = SimpleNamespace(OrderSide=OrderSide, TimeInForce=TimeInForce)
            return mod  # type: ignore[return-value]
        return real_import(name, *args, **kwargs)

    builtins.__import__ = fake_import  # type: ignore[assignment]
    try:
        mgr = make_manager_with_doubles()
        out = mgr.place_market_order("MSFT", 10, "sell", validate=False)
        assert out["success"] is True
        assert "order" in out
        assert out["order"]["summary"]["symbol"] == "MSFT"
        # Sonar rule: avoid direct float comparison (IEEE-754 rounding).
        assert out["order"]["summary"]["qty"] == pytest.approx(10.0, rel=1e-9, abs=DEFAULT_ATL)
    finally:
        builtins.__import__ = real_import  # type: ignore[assignment]
