"""Unit tests for account utility helpers."""

import importlib.util
from pathlib import Path

# Load module directly to avoid importing heavy services package
spec = importlib.util.spec_from_file_location(
    "account_utils", Path(__file__).resolve().parents[2] / "the_alchemiser/services/account_utils.py"
)
account_utils = importlib.util.module_from_spec(spec)
spec.loader.exec_module(account_utils)  # type: ignore[attr-defined]
extract_current_position_values = account_utils.extract_current_position_values


def test_extract_current_position_values_basic():
    """It converts market value strings to floats."""
    positions = {
        "AAPL": {"market_value": "1000.50"},
        "MSFT": {"market_value": 2000},
    }
    result = extract_current_position_values(positions)
    assert result == {"AAPL": 1000.50, "MSFT": 2000.0}


def test_extract_current_position_values_handles_invalid():
    """It defaults to zero for missing or invalid values."""
    positions = {
        "TSLA": {"market_value": "invalid"},
        "GOOG": {},
    }
    result = extract_current_position_values(positions)
    assert result["TSLA"] == 0.0
    assert result["GOOG"] == 0.0
