"""Basic integration test for TradingEngine compatibility wrappers."""

from the_alchemiser.application.engine_service import (
    TradingEngine as RootTradingEngine,
)
from the_alchemiser.application.trading.engine_service import (
    TradingEngine as DirectTradingEngine,
)
from the_alchemiser.application.trading.trading_engine import (
    TradingEngine as LegacyTradingEngine,
)


def test_wrappers_export_same_class() -> None:
    assert RootTradingEngine is DirectTradingEngine
    assert RootTradingEngine is LegacyTradingEngine
