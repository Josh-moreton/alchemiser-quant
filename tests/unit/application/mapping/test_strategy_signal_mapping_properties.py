from hypothesis import given, strategies as st

from the_alchemiser.application.mapping.strategy_signal_mapping import (
    _normalize_action,
    legacy_signal_to_typed,
)


@given(st.text())
def test_normalize_action_returns_valid_literal(s: str):
    assert _normalize_action(s) in {"BUY", "SELL", "HOLD"}


cases = {"buy": "BUY", "BuY": "BUY", "SELL": "SELL", "Hold": "HOLD", "HOLD": "HOLD"}


@given(st.sampled_from(list(cases.items())))
def test_normalize_action_case_insensitive(pair):
    raw, expected = pair
    assert _normalize_action(raw) == expected


@given(st.dictionaries(keys=st.text(min_size=1), values=st.one_of(st.text(), st.floats(allow_nan=False))))
def test_legacy_signal_to_typed_always_valid(data):
    sig = legacy_signal_to_typed(data)
    assert sig["action"] in {"BUY", "SELL", "HOLD"}
    assert isinstance(sig["confidence"], float)
    assert isinstance(sig["allocation_percentage"], float)
