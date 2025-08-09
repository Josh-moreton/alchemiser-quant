import logging
from types import SimpleNamespace

from the_alchemiser.services.enhanced.trading_service_manager import TradingServiceManager


def test_close_position_tolerance(monkeypatch):
    manager = TradingServiceManager.__new__(TradingServiceManager)
    manager.logger = logging.getLogger(__name__)
    manager.orders = SimpleNamespace(liquidate_position=lambda symbol: "abc123")

    result = manager.close_position("AAPL", percentage=100.0000000001)
    assert result == {"success": True, "order_id": "abc123"}
