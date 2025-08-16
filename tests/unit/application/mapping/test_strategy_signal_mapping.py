import pytest

from tests._tolerances import DEFAULT_ATL
from the_alchemiser.application.mapping.strategy_signal_mapping import (
    legacy_signal_to_typed,
)


def test_legacy_to_typed_basic_buy():
    legacy = {
        "symbol": "AAPL",
        "action": "buy",
        "reason": "RSI oversold",
        "confidence": 0.75,
        "allocation_percentage": 25.0,
    }
    typed = legacy_signal_to_typed(legacy)

    assert typed["symbol"] == "AAPL"
    assert typed["action"] == "BUY"
    # Sonar rule: avoid direct float comparison (IEEE-754 rounding).
    assert typed["confidence"] == pytest.approx(0.75, rel=1e-9, abs=DEFAULT_ATL)
    assert typed["reasoning"] == "RSI oversold"
    # Sonar rule: avoid direct float comparison (IEEE-754 rounding).
    assert typed["allocation_percentage"] == pytest.approx(25.0, rel=1e-9, abs=DEFAULT_ATL)


def test_legacy_to_typed_action_enum_like():
    # Simulate ActionType enum string repr
    legacy = {"symbol": "SPY", "action": "ActionType.SELL", "reason": "Take profit"}
    typed = legacy_signal_to_typed(legacy)
    assert typed["action"] == "SELL"


def test_legacy_portfolio_symbol_maps_to_label():
    legacy = {"symbol": {"UVXY": 0.25, "BIL": 0.75}, "action": "BUY", "reason": "Hedge"}
    typed = legacy_signal_to_typed(legacy)
    assert typed["symbol"] == "PORTFOLIO"
