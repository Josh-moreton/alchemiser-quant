"""Business Unit: shared | Status: current.

Common types and value objects used across modules.

Note: TimeInForce is deprecated as of 2.10.7 and removed from exports.
Use Alpaca SDK enums directly (OrderSide, TimeInForce from alpaca.trading.enums).
"""

from __future__ import annotations

from .market_data_port import MarketDataPort
from .quantity import Quantity
from .strategy_protocol import StrategyEngine
from .strategy_types import StrategyType
from .strategy_value_objects import StrategySignal

# Import but don't export - deprecated as of 2.10.7, will be removed in 3.0.0
from .time_in_force import TimeInForce  # noqa: F401

__all__ = [
    "MarketDataPort",
    "OrderSideType",
    "Quantity",
    "StrategyEngine",
    "StrategySignal",
    "StrategyType",
    # "TimeInForce",  # DEPRECATED: Removed from exports in 2.10.7, use Alpaca SDK directly
]
