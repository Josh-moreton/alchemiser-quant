from typing import Any

import pytest

from the_alchemiser.services.trading.trading_service_manager import TradingServiceManager


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


@pytest.mark.parametrize("flag, expect_typed", [(None, False), ("1", True)])
def test_get_open_orders_flag(flag: str | None, expect_typed: bool, types_flag):
    types_flag(flag)
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
    if expect_typed:
        assert "domain" in first and "summary" in first
        dom = first["domain"]
        assert dom.symbol.value in ("AAPL", "MSFT")
        assert float(dom.quantity.value) in (1.0, 2.0)
    else:
        assert isinstance(first, dict)
        assert first["symbol"] == "AAPL"
