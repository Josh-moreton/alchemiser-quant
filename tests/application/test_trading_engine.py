from rich.panel import Panel

from the_alchemiser.application.trading_engine import TradingEngine
from the_alchemiser.application.types import MultiStrategyExecutionResult


def _account_info() -> dict:
    return {
        "account_id": "1",
        "equity": 0.0,
        "cash": 0.0,
        "buying_power": 0.0,
        "day_trades_remaining": 0,
        "portfolio_value": 0.0,
        "last_equity": 0.0,
        "daytrading_buying_power": 0.0,
        "regt_buying_power": 0.0,
        "status": "ACTIVE",
    }


def test_display_multi_strategy_summary_prints_orders_table(monkeypatch):
    engine = TradingEngine.__new__(TradingEngine)
    engine.paper_trading = True
    engine.ignore_market_hours = False

    execution_result = MultiStrategyExecutionResult(
        success=True,
        strategy_signals={},
        consolidated_portfolio={"AAPL": 0.5},
        orders_executed=[],
        account_info_before=_account_info(),
        account_info_after=_account_info(),
        execution_summary={},
    )

    printed = []

    def fake_print(self, obj=None, *args, **kwargs):
        printed.append(obj)

    monkeypatch.setattr("rich.console.Console.print", fake_print, raising=False)

    engine.display_multi_strategy_summary(execution_result)

    assert isinstance(printed[3], Panel)
