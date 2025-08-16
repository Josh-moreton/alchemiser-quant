"""Basic integration test for the TradingEngine wrapper."""
from the_alchemiser.application.engine_service import TradingEngine as NewTradingEngine
from the_alchemiser.application.trading.trading_engine import TradingEngine as LegacyTradingEngine


def test_wrapper_exports_same_class() -> None:
    assert NewTradingEngine is LegacyTradingEngine
