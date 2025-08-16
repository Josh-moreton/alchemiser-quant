from hypothesis import given, strategies as st

from the_alchemiser.utils.feature_flags import _truthy


@given(st.sampled_from(["1", "true", "YES", "On", "0", "false", "n", ""]))
def test_truthy_expected_values(s):
    result = _truthy(s)
    expected = s.strip().lower() in {"1", "true", "yes", "on"}
    assert result is expected


@given(st.none())
def test_truthy_none_is_false(val):
    assert _truthy(val) is False
