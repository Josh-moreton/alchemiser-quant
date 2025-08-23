from datetime import UTC, datetime
from decimal import Decimal

import pytest

from the_alchemiser.application.mapping.execution import (
    account_info_to_execution_result_dto,
    create_quote_dto,
    create_trading_plan_dto,
    dict_to_execution_result_dto,
    dict_to_quote_dto,
    dict_to_trading_plan_dto,
    dict_to_websocket_result_dto,
    execution_result_dto_to_dict,
    quote_dto_to_dict,
    trading_plan_dto_to_dict,
    websocket_result_dto_to_dict,
)
from the_alchemiser.interfaces.schemas.execution import (
    TradingAction,
    WebSocketStatus,
)


def test_trading_plan_round_trip_precision():
    plan = create_trading_plan_dto("aapl", "buy", Decimal("1.23456"), Decimal("150.0199"), "reason")
    d = trading_plan_dto_to_dict(plan)
    # Quantity & price serialized as strings preserving precision policy (2dp money, 4dp qty)
    assert d["quantity"] == "1.2346"  # rounded 4 dp
    assert d["estimated_price"] == "150.02"  # rounded 2 dp
    plan2 = dict_to_trading_plan_dto(
        {
            "symbol": d["symbol"],
            "action": d["action"],
            "quantity": d["quantity"],
            "estimated_price": d["estimated_price"],
            "reasoning": d["reasoning"],
        }
    )
    assert plan2.symbol == plan.symbol
    assert plan2.action == TradingAction.BUY
    # Use decimal equality via string comparison (values are Decimals)
    assert str(plan2.quantity) == "1.2346"
    assert str(plan2.estimated_price) == "150.02"


def test_trading_plan_invalid_action():
    with pytest.raises(ValueError):
        dict_to_trading_plan_dto(
            {
                "symbol": "AAPL",
                "action": "HOLD",  # invalid for TradingPlan
                "quantity": 1,
                "estimated_price": 10,
                "reasoning": "x",
            }
        )


def test_quote_round_trip_and_timestamp_normalization():
    now = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
    quote = create_quote_dto(100, 100.05, 10.123456, 11.99999, now)
    d = quote_dto_to_dict(quote)
    assert d["bid_price"] == "100.00"
    assert d["ask_price"] == "100.05"
    assert d["bid_size"] == "10.1235"
    assert d["ask_size"] == "12.0000"
    # Round trip
    quote2 = dict_to_quote_dto(d)
    assert str(quote2.bid_price) == "100.00"
    assert quote2.timestamp.endswith("+00:00") or quote2.timestamp.endswith("Z")


def test_websocket_result_mapping():
    dto = dict_to_websocket_result_dto(
        {
            "status": WebSocketStatus.COMPLETED.value,
            "message": "done",
            "orders_completed": ["o1", "o2"],
        }
    )
    out = websocket_result_dto_to_dict(dto)
    assert out["orders_count"] == 2
    assert out["status"] == WebSocketStatus.COMPLETED.value


def test_execution_result_order_normalization():
    account = {
        "account_id": "abc",
        "equity": 1,
        "cash": 1,
        "buying_power": 1,
        "day_trades_remaining": 3,
        "portfolio_value": 1,
        "last_equity": 1,
        "daytrading_buying_power": 1,
        "regt_buying_power": 1,
        "status": "ACTIVE",
    }
    order = {
        "id": "o1",
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
    exec_dto = account_info_to_execution_result_dto([order], account, account)
    as_dict = execution_result_dto_to_dict(exec_dto)
    assert as_dict["orders_count"] == 1
    assert as_dict["orders_executed"][0]["id"] == "o1"
    # Round trip minimal
    exec_dto2 = dict_to_execution_result_dto(
        {
            "orders_executed": as_dict["orders_executed"],
            "account_info_before": account,
            "account_info_after": account,
            "execution_summary": {},
            "final_portfolio_state": None,
        }
    )
    assert len(exec_dto2.orders_executed) == 1


def test_invalid_websocket_status():
    with pytest.raises(ValueError):
        dict_to_websocket_result_dto(
            {
                "status": "finished",  # invalid
                "message": "x",
                "orders_completed": [],
            }
        )
