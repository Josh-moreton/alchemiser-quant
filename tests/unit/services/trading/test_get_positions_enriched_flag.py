import pytest

from tests._tolerances import DEFAULT_ATL
from the_alchemiser.services.trading.trading_service_manager import TradingServiceManager


class Obj:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


def make_manager(monkeypatch):
    # Minimal manager with fake credentials
    m = TradingServiceManager("key", "secret", paper=True)

    # Stub alpaca_manager.get_all_positions
    positions = [
        {
            "symbol": "AAPL",
            "qty": "10",
            "avg_entry_price": "150.0",
            "current_price": 155.25,
            "market_value": "1552.5",
            "unrealized_pl": "52.5",
            "unrealized_plpc": "0.0339",
        },
        Obj(
            symbol="MSFT",
            qty=5,
            avg_entry_price=310,
            current_price="315.10",
            market_value=1575.5,
            unrealized_pl=25.5,
            unrealized_plpc=0.0165,
        ),
    ]

    m.alpaca_manager.get_all_positions = lambda: positions  # type: ignore[attr-defined]
    return m


def test_get_positions_enriched_legacy(monkeypatch):
    monkeypatch.setenv("TYPES_V2_ENABLED", "0")
    mgr = make_manager(monkeypatch)

    out = mgr.get_positions_enriched()
    # Legacy path returns raw positions unchanged
    assert isinstance(out, list)
    assert out and out[0]["symbol"] == "AAPL"  # type: ignore[index]


def test_get_positions_enriched_typed(monkeypatch):
    monkeypatch.setenv("TYPES_V2_ENABLED", "1")
    mgr = make_manager(monkeypatch)

    out = mgr.get_positions_enriched()
    assert isinstance(out, list)
    first = out[0]
    assert "raw" in first and "summary" in first
    summary = first["summary"]
    assert summary["symbol"] == "AAPL"
    # Sonar rule: avoid direct float comparison (IEEE-754 rounding).
    assert summary["qty"] == pytest.approx(10.0, rel=1e-9, abs=DEFAULT_ATL)
    # Sonar rule: avoid direct float comparison (IEEE-754 rounding).
    assert summary["avg_entry_price"] == pytest.approx(150.0, rel=1e-9, abs=DEFAULT_ATL)
