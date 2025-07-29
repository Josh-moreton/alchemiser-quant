import pytest
from unittest.mock import MagicMock
from alpaca.trading.enums import OrderSide
from the_alchemiser.execution.order_manager_adapter import OrderManagerAdapter


@pytest.fixture
def order_manager():
    from unittest.mock import MagicMock
    trading_client = MagicMock()
    trading_client.get_clock.return_value = MagicMock(is_open=True)
    trading_client.submit_order.side_effect = lambda order_data: MagicMock(id='1', status='filled')
    trading_client.get_order_by_id.side_effect = lambda order_id: MagicMock(id=order_id, status='filled')
    trading_client.cancel_order_by_id.return_value = None
    # Mock position for sell tests
    trading_client.get_all_positions.return_value = [
        MagicMock(symbol='AAPL', qty=10.0, market_value=1000.0)
    ]

    data_provider = MagicMock()
    data_provider.get_current_price.return_value = 100.0
    data_provider.get_latest_quote.return_value = (99.0, 101.0)

    config = {'alpaca': {'slippage_bps': 10}}
    return OrderManagerAdapter(trading_client, data_provider, ignore_market_hours=False, config=config)

def test_place_limit_or_market_buy(order_manager):
    order_id = order_manager.place_limit_or_market('AAPL', 1.0, OrderSide.BUY)
    assert order_id is not None

def test_place_limit_or_market_sell(order_manager):
    order_id = order_manager.place_limit_or_market('AAPL', 1.0, OrderSide.SELL)
    assert order_id is not None

def test_wait_for_settlement(order_manager):
    # Simulate a filled order
    sell_orders = [{'order_id': '1'}]
    result = order_manager.wait_for_settlement(sell_orders, max_wait_time=2, poll_interval=0.1)
    assert result is True

def test_calculate_dynamic_limit_price(order_manager):
    price = order_manager.calculate_dynamic_limit_price(OrderSide.BUY, 99.0, 101.0, step=1, tick_size=0.2, max_steps=3)
    assert price == 100.2
    price = order_manager.calculate_dynamic_limit_price(OrderSide.SELL, 99.0, 101.0, step=2, tick_size=0.5, max_steps=3)
    assert price == 99.0
