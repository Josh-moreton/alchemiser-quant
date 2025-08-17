from __future__ import annotations

import pytest

from tests._tolerances import DEFAULT_ATL
from the_alchemiser.services.trading.trading_service_manager import TradingServiceManager


@pytest.fixture(autouse=True)
def clear_flag_env(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("TYPES_V2_ENABLED", raising=False)
    yield
    monkeypatch.delenv("TYPES_V2_ENABLED", raising=False)


def make_manager(summary: dict):
    mgr = TradingServiceManager("key", "secret", paper=True)
    # Stub account.get_account_summary to avoid touching repository
    mgr.account.get_account_summary = lambda: summary  # type: ignore[method-assign]
    return mgr


def sample_summary() -> dict:
    return {
        "account_id": "ABC-123",
        "equity": 100000.0,
        "cash": 25000.0,
        "market_value": 75000.0,
        "buying_power": 50000.0,
        "day_trade_count": 1,
        "pattern_day_trader": False,
        "trading_blocked": False,
        "transfers_blocked": False,
        "account_blocked": False,
        "last_equity": 99000.0,
        "calculated_metrics": {
            "cash_ratio": 0.25,
            "market_exposure": 0.75,
            "leverage_ratio": 1.3333,
            "available_buying_power_ratio": 0.5,
        },
    }


def test_account_summary_enriched_legacy(monkeypatch: pytest.MonkeyPatch):
    mgr = make_manager(sample_summary())
    out = mgr.get_account_summary_enriched()
    # Without flag, returns legacy dict directly
    assert isinstance(out, dict)
    # Sonar rule: avoid direct float comparison (IEEE-754 rounding).
    assert out["equity"] == pytest.approx(100000.0, rel=1e-9, abs=DEFAULT_ATL)
    assert "summary" not in out


def test_account_summary_enriched_typed(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("TYPES_V2_ENABLED", "1")
    mgr = make_manager(sample_summary())
    out = mgr.get_account_summary_enriched()
    assert isinstance(out, dict)
    assert "raw" in out and "summary" in out
    summary = out["summary"]
    # Sonar rule: avoid direct float comparison (IEEE-754 rounding).
    assert summary["equity"] == pytest.approx(100000.0, rel=1e-9, abs=DEFAULT_ATL)
    # Sonar rule: avoid direct float comparison (IEEE-754 rounding).
    assert summary["cash"] == pytest.approx(25000.0, rel=1e-9, abs=DEFAULT_ATL)
    # Sonar rule: avoid direct float comparison (IEEE-754 rounding).
    assert summary["calculated_metrics"]["cash_ratio"] == pytest.approx(
        0.25, rel=1e-9, abs=DEFAULT_ATL
    )
