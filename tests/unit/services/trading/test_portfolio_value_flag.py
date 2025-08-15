from __future__ import annotations

from decimal import Decimal

import pytest

from the_alchemiser.services.trading.trading_service_manager import TradingServiceManager


@pytest.fixture(autouse=True)
def clear_flag_env(monkeypatch: pytest.MonkeyPatch):
    # Ensure a clean env for each test
    monkeypatch.delenv("TYPES_V2_ENABLED", raising=False)
    yield
    monkeypatch.delenv("TYPES_V2_ENABLED", raising=False)


class DummyAlpacaManager:
    def __init__(self, value):
        self._value = value

    def get_portfolio_value(self):
        return self._value


def make_manager(value):
    mgr = TradingServiceManager("key", "secret", paper=True)
    # Inject dummy alpaca manager to avoid real API
    mgr.alpaca_manager = DummyAlpacaManager(value)
    return mgr


def test_get_portfolio_value_legacy(monkeypatch: pytest.MonkeyPatch):
    mgr = make_manager(12345.67)
    result = mgr.get_portfolio_value()
    assert isinstance(result, float)
    assert result == 12345.67


def test_get_portfolio_value_typed(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("TYPES_V2_ENABLED", "1")
    mgr = make_manager(12345.67)
    result = mgr.get_portfolio_value()
    assert isinstance(result, dict)
    assert result["value"] == 12345.67
    money = result["money"]
    assert money is not None
    assert money.currency == "USD"
    assert money.amount == Decimal("12345.67").quantize(Decimal("0.01"))
