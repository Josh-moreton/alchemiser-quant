"""Tests for lightweight utilities in trading engine."""

import pytest

trading_engine = pytest.importorskip("the_alchemiser.application.trading_engine")
_create_default_account_info = trading_engine._create_default_account_info


def test_create_default_account_info_defaults():
    info = _create_default_account_info()
    assert info["account_id"] == "unknown"
    assert info["equity"] == 0.0
    assert info["status"] == "INACTIVE"


def test_create_default_account_info_custom_id():
    info = _create_default_account_info("abc123")
    assert info["account_id"] == "abc123"
