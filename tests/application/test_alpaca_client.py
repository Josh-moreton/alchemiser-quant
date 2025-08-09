from types import SimpleNamespace

from alpaca.trading.enums import OrderSide

from the_alchemiser.application.alpaca_client import AlpacaClient
from the_alchemiser.services.exceptions import TradingClientError


class DummyTradingClient:
    def __init__(self, errors=None):
        self.errors = errors or []
        self.calls = 0

    def submit_order(self, _):
        if self.calls < len(self.errors):
            error = self.errors[self.calls]
            self.calls += 1
            raise error
        self.calls += 1
        return SimpleNamespace(id="1")


class DummyAssetHandler:
    def __init__(self):
        self.fallback_called = False

    def prepare_market_order(self, *args, **kwargs):
        return object(), ""

    def handle_fractionability_error(self, *args, **kwargs):
        self.fallback_called = True
        return object(), "converted"


class DummyPositionManager:
    def validate_buying_power(self, *args, **kwargs):
        return True, ""

    def validate_sell_position(self, *args, **kwargs):
        return True, 1, ""


class DummyOrderMonitor:
    pass


class DummyPricingHandler:
    pass


class DummyWebSocketManager:
    pass


def _client(trading_client):
    client = AlpacaClient.__new__(AlpacaClient)
    client.trading_client = trading_client
    client.asset_handler = DummyAssetHandler()
    client.position_manager = DummyPositionManager()
    client.order_monitor = DummyOrderMonitor()
    client.limit_order_handler = None
    client.pricing_handler = DummyPricingHandler()
    client.websocket_manager = DummyWebSocketManager()
    client.validate_buying_power = False
    client.cancel_all_orders = lambda symbol: None
    client.get_current_positions = lambda: {}
    return client


def test_place_market_order_insufficient_buying_power():
    trading_client = DummyTradingClient([TradingClientError("insufficient buying power")])
    client = _client(trading_client)
    result = client.place_market_order("AAPL", OrderSide.BUY, qty=1, cancel_existing=False)
    assert result is None


def test_place_market_order_fractionability():
    error = TradingClientError("not fractionable")
    trading_client = DummyTradingClient([error])
    client = _client(trading_client)
    result = client.place_market_order("AAPL", OrderSide.BUY, qty=1, cancel_existing=False)
    assert result == "1"
    assert client.asset_handler.fallback_called
