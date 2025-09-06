"""Business Unit: shared | Status: current.

Market data TypedDict definitions for shared use across modules.
"""

from typing import Any, TypedDict


class MarketDataPoint(TypedDict):
    timestamp: str
    open: float
    high: float
    low: float
    close: float
    volume: int
    symbol: str


class PriceData(TypedDict):
    symbol: str
    price: float
    timestamp: str
    bid: float | None
    ask: float | None
    volume: int | None


class QuoteData(TypedDict):
    bid_price: float
    ask_price: float
    bid_size: float
    ask_size: float
    timestamp: str


class DataProviderResult(TypedDict):
    success: bool
    data: dict[str, Any] | None
    error_message: str | None
    timestamp: str


class IndicatorData(TypedDict):
    symbol: str
    indicator_name: str
    value: float
    timestamp: str
    parameters: dict[str, Any]