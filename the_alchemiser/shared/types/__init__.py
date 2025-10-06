"""Business Unit: shared | Status: current.

Common types and value objects used across modules.

Note: TimeInForce is deprecated as of 2.10.7 and removed from exports.
Use BrokerTimeInForce instead.
"""

from __future__ import annotations

from .broker_enums import (
    BrokerOrderSide,
    BrokerTimeInForce,
    OrderSideType,
    TimeInForceType,
)
from .market_data_port import MarketDataPort
from .quantity import Quantity
from .strategy_protocol import StrategyEngine
from .strategy_value_objects import StrategySignal

# Import but don't export - deprecated as of 2.10.7, will be removed in 3.0.0
from .time_in_force import TimeInForce  # noqa: F401

__all__ = [
    "BrokerOrderSide",
    "BrokerTimeInForce",
    "MarketDataPort",
    "OrderError",
    "OrderSideType",
    "Quantity",
    "StrategyEngine",
    "StrategySignal",
    "TimeInForceType",
    # "TimeInForce",  # DEPRECATED: Removed from exports in 2.10.7, use BrokerTimeInForce
]
