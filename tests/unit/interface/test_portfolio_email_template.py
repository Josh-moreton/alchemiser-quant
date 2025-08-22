from decimal import Decimal

from the_alchemiser.interface.email import email_utils as email_utils
from the_alchemiser.interfaces.schemas.common import MultiStrategyExecutionResultDTO
from the_alchemiser.interfaces.schemas.execution import ExecutionResultDTO


def _account() -> dict:
    return {
        "account_id": "acc1",
        "equity": 10000,
        "cash": 5000,
        "buying_power": 15000,
        "day_trades_remaining": 3,
        "portfolio_value": 10000,
        "last_equity": 10000,
        "daytrading_buying_power": 15000,
        "regt_buying_power": 15000,
        "status": "ACTIVE",
    }


def _order(order_id: str) -> dict:
    return {
        "id": order_id,
        "symbol": "AAPL",
        "qty": "1",
        "side": "buy",
        "order_type": "market",
        "time_in_force": "day",
        "status": "filled",
        "filled_qty": "1",
        "filled_avg_price": "150",
        "created_at": "2024-01-01T00:00:00+00:00",
        "updated_at": "2024-01-01T00:00:00+00:00",
    }


def test_build_portfolio_display_execution_result_dto():
    dto = ExecutionResultDTO(
        orders_executed=[_order("o1")],
        account_info_before=_account(),
        account_info_after=_account(),
        execution_summary={"orders_count": 1, "consolidated_portfolio": {"AAPL": 0.25}},
        final_portfolio_state={"cash": Decimal("5000")},
    )
    html = email_utils._build_portfolio_display(dto)  # noqa: SLF001 - internal helper acceptable
    assert "AAPL" in html


def test_build_portfolio_display_multistrategy_result_dto():
    ms = MultiStrategyExecutionResultDTO(
        success=True,
        strategy_signals={},
        consolidated_portfolio={"AAPL": 0.1},
        orders_executed=[_order("o2")],
        account_info_before=_account(),
        account_info_after=_account(),
        execution_summary={"orders_count": 1},
        final_portfolio_state={"cash": Decimal("5000")},
    )
    html = email_utils._build_portfolio_display(ms)
    assert "AAPL" in html


def test_deprecated_aliases_not_in_all():
    # ExecutionResult, WebSocketResult, QuoteData should not be exported from execution.__all__
    import the_alchemiser.interfaces.schemas.execution as exec_mod

    assert "ExecutionResult" not in exec_mod.__all__
    assert "WebSocketResult" not in exec_mod.__all__
    assert "QuoteData" not in exec_mod.__all__
