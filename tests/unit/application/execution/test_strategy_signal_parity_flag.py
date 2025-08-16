from __future__ import annotations

import os
from typing import Any

import pytest

from the_alchemiser.application.execution.execution_manager import ExecutionManager
from the_alchemiser.domain.strategies.strategy_manager import StrategyType


class _FakeStrategyManager:
    def run_all_strategies(self) -> tuple[
        dict[StrategyType, dict[str, Any]],
        dict[str, float],
        dict[str, list[StrategyType]],
    ]:
        legacy_signals: dict[StrategyType, dict[str, Any]] = {
            StrategyType.NUCLEAR: {
                "symbol": "XLE",
                "action": "BUY",
                "reason": "nuclear bullish",
                "confidence": 0.8,
                "allocation_percentage": 0.5,
            },
            StrategyType.TECL: {
                # Portfolio allocation result to validate portfolio symbol handling
                "symbol": {"UVXY": 0.25, "BIL": 0.75},
                "action": "HOLD",
                "reason": "vol neutral",
                "confidence": 0.3,
                "allocation_percentage": 0.0,
            },
            StrategyType.KLM: {
                "symbol": "AAPL",
                # Lowercase to test normalization in typed path
                "action": "sell",
                "reason": "ml signal",
                "confidence": 0.6,
                "allocation_percentage": 0.2,
                "variant_name": "v1",
            },
        }
        consolidated = {"BIL": 1.0}
        attribution: dict[str, list[StrategyType]] = {}
        return legacy_signals, consolidated, attribution

    # Provide default allocations expected by reporting
    @property
    def strategy_allocations(self) -> dict[StrategyType, float]:
        return {
            StrategyType.NUCLEAR: 1.0 / 3.0,
            StrategyType.TECL: 1.0 / 3.0,
            StrategyType.KLM: 1.0 / 3.0,
        }


class _FakeEngine:
    def __init__(self) -> None:
        self.paper_trading = True
        self.strategy_manager = _FakeStrategyManager()

    def get_account_info(self) -> dict[str, Any]:
        return {
            "account_id": "test",
            "equity": 100000.0,
            "cash": 100000.0,
            "buying_power": 200000.0,
            "day_trades_remaining": 3,
            "portfolio_value": 100000.0,
            "last_equity": 100000.0,
            "daytrading_buying_power": 200000.0,
            "regt_buying_power": 200000.0,
            "status": "ACTIVE",
        }

    def rebalance_portfolio(
        self,
        consolidated_portfolio: dict[str, float],
        strategy_attribution: dict[str, list[StrategyType]] | None = None,
    ) -> list[dict[str, Any]]:
        return []

    def get_positions(self) -> dict[str, Any]:
        return {}

    def get_current_prices(self, symbols: list[str]) -> dict[str, float]:
        return dict.fromkeys(symbols, 100.0)

    def _trigger_post_trade_validation(
        self, strategy_signals: dict[StrategyType, Any], orders_executed: list[dict[str, Any]]
    ) -> None:  # noqa: D401
        return None

    def _archive_daily_strategy_pnl(self, pnl_summary: dict[str, Any]) -> None:
        return None


@pytest.fixture(autouse=True)
def _no_dashboard_save(monkeypatch: pytest.MonkeyPatch) -> None:
    # Avoid S3 writes by no-oping the save function used by ExecutionManager
    import the_alchemiser.application.execution.execution_manager as em
    import the_alchemiser.application.reporting.reporting as rep

    monkeypatch.setattr(em, "save_dashboard_data", lambda *_args, **_kwargs: None)
    # Stub reporting to avoid needing real strategy_allocations and prices
    monkeypatch.setattr(
        rep,
        "create_execution_summary",
        lambda *_args, **_kwargs: {
            "allocations": {},
            "strategy_summary": {},
            "trading_summary": {},
            "pnl_summary": {},
        },
    )
    monkeypatch.setattr(
        rep,
        "build_portfolio_state_data",
        lambda *_args, **_kwargs: {"allocations": {}},
    )


def _run_with_flag(flag_value: str | None) -> Any:
    # Set/unset feature flag and execute once
    env_name = "TYPES_V2_ENABLED"
    if flag_value is None:
        os.environ.pop(env_name, None)
    else:
        os.environ[env_name] = flag_value

    engine = _FakeEngine()
    manager = ExecutionManager(engine)
    return manager.execute_multi_strategy()


def test_strategy_signal_parity_flag_on_off() -> None:
    # OFF path (legacy dict signals)
    res_off = _run_with_flag(None)
    legacy = res_off.strategy_signals  # dict[StrategyType, dict]

    # ON path (typed StrategySignal)
    res_on = _run_with_flag("1")
    typed = res_on.strategy_signals  # dict[StrategyType, StrategySignal]

    # Nuclear: symbol should be identical, action normalized
    assert legacy[StrategyType.NUCLEAR]["symbol"] == "XLE"
    assert typed[StrategyType.NUCLEAR]["symbol"] == "XLE"
    assert typed[StrategyType.NUCLEAR]["action"] == "BUY"

    # TECL: legacy symbol is a dict allocation -> typed uses a portfolio label
    assert isinstance(legacy[StrategyType.TECL]["symbol"], dict)
    assert typed[StrategyType.TECL]["symbol"] == "PORTFOLIO"
    assert typed[StrategyType.TECL]["action"] == "HOLD"

    # KLM: lowercase action should normalize to SELL, symbol preserved
    assert legacy[StrategyType.KLM]["symbol"] == "AAPL"
    assert typed[StrategyType.KLM]["symbol"] == "AAPL"
    assert legacy[StrategyType.KLM]["action"] == "sell"
    assert typed[StrategyType.KLM]["action"] == "SELL"


def test_strategy_signal_parity_conf_alloc_reason() -> None:
    # OFF path (legacy dict signals)
    res_off = _run_with_flag(None)
    legacy = res_off.strategy_signals  # dict[StrategyType, dict]

    # ON path (typed StrategySignal)
    res_on = _run_with_flag("1")
    typed = res_on.strategy_signals  # dict[StrategyType, StrategySignal]

    # Confidence parity
    assert typed[StrategyType.NUCLEAR]["confidence"] == legacy[StrategyType.NUCLEAR]["confidence"]
    assert typed[StrategyType.TECL]["confidence"] == legacy[StrategyType.TECL]["confidence"]
    assert typed[StrategyType.KLM]["confidence"] == legacy[StrategyType.KLM]["confidence"]

    # Allocation percentage parity
    assert (
        typed[StrategyType.NUCLEAR]["allocation_percentage"]
        == legacy[StrategyType.NUCLEAR]["allocation_percentage"]
    )
    assert (
        typed[StrategyType.TECL]["allocation_percentage"]
        == legacy[StrategyType.TECL]["allocation_percentage"]
    )
    assert (
        typed[StrategyType.KLM]["allocation_percentage"]
        == legacy[StrategyType.KLM]["allocation_percentage"]
    )

    # Reason -> reasoning mapping parity
    assert typed[StrategyType.NUCLEAR]["reasoning"] == legacy[StrategyType.NUCLEAR]["reason"]
    assert typed[StrategyType.TECL]["reasoning"] == legacy[StrategyType.TECL]["reason"]
    assert typed[StrategyType.KLM]["reasoning"] == legacy[StrategyType.KLM]["reason"]
