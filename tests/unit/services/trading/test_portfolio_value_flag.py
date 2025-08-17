from __future__ import annotations

from decimal import Decimal

import pytest

from tests._tolerances import DEFAULT_ATL
from the_alchemiser.services.trading.trading_service_manager import TradingServiceManager


@pytest.fixture(autouse=True)
def clear_flag_env(monkeypatch: pytest.MonkeyPatch):
    # Ensure legacy default explicitly for tests that assert legacy behavior
    monkeypatch.setenv("TYPES_V2_ENABLED", "0")
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
    # Sonar rule: avoid direct float comparison (IEEE-754 rounding).
    assert result == pytest.approx(12345.67, rel=1e-9, abs=DEFAULT_ATL)


def test_get_portfolio_value_typed(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("TYPES_V2_ENABLED", "1")
    mgr = make_manager(12345.67)
    result = mgr.get_portfolio_value()
    assert isinstance(result, dict)
    # Sonar rule: avoid direct float comparison (IEEE-754 rounding).
    assert result["value"] == pytest.approx(12345.67, rel=1e-9, abs=DEFAULT_ATL)
    money = result["money"]
    assert money is not None
    assert money.currency == "USD"
    assert money.amount == Decimal("12345.67").quantize(Decimal("0.01"))
